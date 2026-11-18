"""Deterministic case-note scrubber: lexicon names/IDs plus structured-PII patterns.

Every detector runs on the original text and reports character spans; the union of
all spans is replaced once. Span output lets the synthetic ground truth measure
recall exactly. Design limits are documented in docs/pii_protocol.md: names are
removed when they appear in the reports' own identity columns or follow an
honorific, so third-party names outside both can survive. Output is pseudonymous
(tier T2), never anonymous.
"""

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from jvsg_triage.etl.models import CaseNoteRecord, IntakeBatch, RedactedNote, RedactionLexicon

PROTOCOL_VERSION = "1.0"

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sept?\.?|Oct\.?|Nov\.?|Dec\.?"
)
_STREET = (
    "Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Highway|Hwy|"
    "Way|Parkway|Pkwy|Circle|Cir|Place|Pl|Terrace|Trail|Loop|Plaza"
)
_HONORIFIC = r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Sgt|SGT|SSgt|SFC|MSG|CPT|Capt|LT|Lt|Col|COL|Maj|MAJ)\.?"

# Capitalized common words never taken from the global name lexicon. They are still
# redacted when they belong to the participant or staff on the note's own row.
NAME_STOPWORDS = frozenset(
    word.casefold() for word in (
        "January February March April May June July August September October November "
        "December Monday Tuesday Wednesday Thursday Friday Saturday Sunday "
        "Will Can Hope Job Case Mark Bill Grant Chase Major Mobile Alabama Veteran "
        "Veterans Army Navy Marine Marines Air Force Good Thank Thanks Please Dear Hello "
        "Best Regards Sincerely Career Center Services Service Fair Employment Training "
        "Contact Office Specialist Program Jr Sr II III IV"
    ).split()
)

PLACEHOLDERS = {
    "EMAIL": "[EMAIL]", "URL": "[URL]", "SSN": "[SSN]", "PHONE": "[PHONE]",
    "DATE": "[DATE]", "ADDRESS": "[ADDRESS]", "ZIP": "[ZIP]", "ID": "[ID]",
    "NAME": "[NAME]", "STAFF": "[STAFF]",
}
# Earlier labels win when overlapping spans are merged (e.g. a name inside an email).
_PRIORITY = {label: rank for rank, label in enumerate(PLACEHOLDERS)}

_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+")),
    ("URL", re.compile(r"\b(?:https?://|www\.)\S+", re.I)),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", re.compile(
        r"(?:(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\b\d{3}[\s.-])\d{3}[\s.-]\d{4}\b"
        r"|\b\d{10}\b|\b\d{3}-\d{4}\b)"
        r"(?:\s*(?:x|ext\.?)\s*\d{1,5})?",
        re.I,
    )),
    ("DATE", re.compile(
        r"\b\d{1,2}[/-]\d{1,2}[/-](?:\d{4}|\d{2})\b|\b\d{4}-\d{2}-\d{2}\b"
        rf"|\b(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?\b"
        rf"|\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})(?:,?\s+\d{{4}})?\b",
    )),
    ("ADDRESS", re.compile(
        rf"\b(?:P\.?\s?O\.?\s+Box\s+\d+|\d{{1,6}}(?:\s+[A-Z0-9][\w.'-]*){{1,4}}\s+(?:{_STREET})"
        r"\b\.?(?:,?\s+(?:Apt|Apartment|Unit|Suite|Ste|Lot|#)\.?\s*[\w-]+)?)",
    )),
    # Python lookbehinds must be fixed-width, so each state form gets its own.
    ("ZIP", re.compile(
        r"(?:(?<=\b[A-Z]{2}\s)|(?<=\b[A-Z]{2},\s)|(?<=\bAl\s)|(?<=Alabama\s))"
        r"\d{5}(?:-\d{4})?\b"
    )),
    ("ID", re.compile(r"\b\d{5,}\b")),
)
_HONORIFIC_NAME = re.compile(
    rf"{_HONORIFIC}\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)"
)
_PLACEHOLDER = re.compile(r"\[(?:" + "|".join(PLACEHOLDERS) + r")\]")


@dataclass(frozen=True, slots=True)
class Span:
    """Half-open character interval in the original note text."""

    start: int
    end: int
    label: str


def _name_tokens(names: Iterable[str], *, minimum: int) -> set[str]:
    tokens: set[str] = set()
    for name in names:
        for part in re.split(r"[^A-Za-z'\-]+", name):
            for token in {part, *part.split("-")}:
                token = token.strip("'-")
                if len(token) >= minimum:
                    tokens.add(token)
    return tokens


def _alternation(tokens: Iterable[str]) -> re.Pattern[str] | None:
    ordered = sorted({token.casefold() for token in tokens}, key=lambda t: (-len(t), t))
    if not ordered:
        return None
    body = "|".join(re.escape(token) for token in ordered)
    return re.compile(rf"(?<![\w'])(?:{body})(?![\w])", re.I)


def merge_spans(spans: Iterable[Span]) -> list[Span]:
    """Union overlapping or touching spans; keep the highest-priority label."""
    merged: list[Span] = []
    for span in sorted(spans, key=lambda s: (s.start, -s.end)):
        if merged and span.start <= merged[-1].end:
            last = merged[-1]
            label = min(last.label, span.label, key=_PRIORITY.__getitem__)
            merged[-1] = Span(last.start, max(last.end, span.end), label)
        else:
            merged.append(span)
    return merged


class Redactor:
    """Build once per batch from the transient lexicon; reuse for every note."""

    def __init__(self, lexicon: RedactionLexicon) -> None:
        persons = _name_tokens(lexicon.person_names, minimum=3)
        staff = _name_tokens(lexicon.staff_names, minimum=3) - persons
        self._persons = _alternation(t for t in persons if t.casefold() not in NAME_STOPWORDS)
        self._staff = _alternation(t for t in staff if t.casefold() not in NAME_STOPWORDS)
        self._known_names = _alternation(
            t for t in persons | staff if t.casefold() not in NAME_STOPWORDS
        )
        ids = sorted(lexicon.identifiers, key=lambda value: (-len(value), value))
        self._ids = (
            re.compile(rf"(?<!\w)(?:{'|'.join(re.escape(v) for v in ids)})(?!\w)")
            if ids else None
        )

    def detect(self, text: str, context_names: Iterable[str] = ()) -> list[Span]:
        """Return merged PII spans found in the original text."""
        spans: list[Span] = []

        def add(pattern: re.Pattern[str] | None, label: str, *, capitalized: bool = False) -> None:
            if pattern is None:
                return
            for match in pattern.finditer(text):
                if capitalized and not match.group(0)[0].isupper():
                    continue
                spans.append(Span(match.start(), match.end(), label))

        for label, pattern in _PATTERNS:
            add(pattern, label)
        add(self._ids, "ID")
        # The row's own participant and staff names: any case, no stoplist.
        add(_alternation(_name_tokens(context_names, minimum=2)), "NAME")
        # Global lexicon: only Title/UPPER case, so lowercase common words survive.
        add(self._persons, "NAME", capitalized=True)
        add(self._staff, "STAFF", capitalized=True)
        spans.extend(
            Span(match.start(1), match.end(1), "NAME")
            for match in _HONORIFIC_NAME.finditer(text)
        )
        return merge_spans(spans)

    def redact(self, text: str, context_names: Iterable[str] = ()) -> tuple[str, Counter[str]]:
        """Replace each detected span with its typed placeholder."""
        counts: Counter[str] = Counter()
        pieces: list[str] = []
        cursor = 0
        for span in self.detect(text, context_names):
            pieces.extend((text[cursor:span.start], PLACEHOLDERS[span.label]))
            counts[span.label] += 1
            cursor = span.end
        pieces.append(text[cursor:])
        return "".join(pieces), counts

    def residual(self, redacted: str) -> Counter[str]:
        """Re-scan scrubbed text. Hits are defects to review; zero hits is not proof
        of safety because unknown third-party names are invisible to this scan."""
        masked = _PLACEHOLDER.sub(lambda match: " " * len(match.group(0)), redacted)
        findings: Counter[str] = Counter()
        for label, pattern in _PATTERNS:
            findings[label] += sum(1 for _ in pattern.finditer(masked))
        findings["HONORIFIC_NAME"] += sum(1 for _ in _HONORIFIC_NAME.finditer(masked))
        if self._known_names is not None:
            findings["LEXICON_NAME"] += sum(
                1 for match in self._known_names.finditer(masked) if match.group(0)[0].isupper()
            )
        return +findings


def redact_note(note: CaseNoteRecord, redactor: Redactor) -> RedactedNote:
    """Scrub one T1 note into a T2 record."""
    text, counts = redactor.redact(
        note.text.get_secret_value(), (name.get_secret_value() for name in note.context_names),
    )
    return RedactedNote(
        participant_token=note.participant_token,
        source_row=note.source.row_number,
        text=text,
        redactions=dict(sorted(counts.items())),
    )


def redact_batch(batch: IntakeBatch) -> tuple[RedactedNote, ...]:
    """Scrub every matched note in an intake batch."""
    redactor = Redactor(batch.lexicon)
    return tuple(redact_note(note, redactor) for note in batch.matched_notes)
