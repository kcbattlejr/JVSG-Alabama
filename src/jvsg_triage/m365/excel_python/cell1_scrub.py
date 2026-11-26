# Cell 1 of 3 - scrub. Paste into the FIRST Python cell (Formulas > Insert Python).
# Stdlib only: Python in Excel has no network and cannot import jvsg_triage.
# Mirrors src/jvsg_triage/privacy/scrubber.py plus the Office Script referral-name guard.
# Scrubbing is pseudonymization, not anonymization; reviewers must still read each quote.
import re

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sept?\.?|Oct\.?|Nov\.?|Dec\.?"
)
_STREET = (
    "Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Court|Ct|Highway|Hwy|"
    "Way|Parkway|Pkwy|Circle|Cir|Place|Pl|Terrace|Trail|Loop|Plaza"
)
_HONORIFIC = r"\b(?:Mr|Mrs|Ms|Miss|Mx|Dr|Sgt|SGT|SSgt|SFC|MSG|CPT|Capt|LT|Lt|Col|COL|Maj|MAJ)\.?"
_LABELS = ("EMAIL", "URL", "SSN", "PHONE", "DATE", "ADDRESS", "ZIP", "ID", "NAME", "STAFF")
_RANK = {label: rank for rank, label in enumerate(_LABELS)}
_STOPWORDS = frozenset(
    w.casefold() for w in (
        "January February March April May June July August September October November "
        "December Monday Tuesday Wednesday Thursday Friday Saturday Sunday "
        "Will Can Hope Job Case Mark Bill Grant Chase Major Mobile Alabama Veteran "
        "Veterans Army Navy Marine Marines Air Force Good Thank Thanks Please Dear Hello "
        "Best Regards Sincerely Career Center Services Service Fair Employment Training "
        "Contact Office Specialist Program Jr Sr II III IV"
    ).split()
)
_PATTERNS = (
    ("EMAIL", re.compile(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+")),
    ("URL", re.compile(r"\b(?:https?://|www\.)\S+", re.I)),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", re.compile(
        r"(?:(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\b\d{3}[\s.-])\d{3}[\s.-]\d{4}\b"
        r"|\b\d{10}\b|\b\d{3}-\d{4}\b)(?:\s*(?:x|ext\.?)\s*\d{1,5})?", re.I)),
    ("DATE", re.compile(
        r"\b\d{1,2}[/-]\d{1,2}[/-](?:\d{4}|\d{2})\b|\b\d{4}-\d{2}-\d{2}\b"
        rf"|\b(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?\b"
        rf"|\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})(?:,?\s+\d{{4}})?\b")),
    ("ADDRESS", re.compile(
        rf"\b(?:P\.?\s?O\.?\s+Box\s+\d+|\d{{1,6}}(?:\s+[A-Z0-9][\w.'-]*){{1,4}}\s+(?:{_STREET})"
        r"\b\.?(?:,?\s+(?:Apt|Apartment|Unit|Suite|Ste|Lot|#)\.?\s*[\w-]+)?)")),
    ("ZIP", re.compile(
        r"(?:(?<=\b[A-Z]{2}\s)|(?<=\b[A-Z]{2},\s)|(?<=\bAl\s)|(?<=Alabama\s))"
        r"\d{5}(?:-\d{4})?\b")),
    ("ID", re.compile(r"\b\d{5,}\b")),
)
_HONORIFIC_NAME = re.compile(rf"{_HONORIFIC}\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)")
_REFERRAL_NAME = re.compile(
    r"\b(?:[Rr]eferred to|[Ss]poke with|[Cc]ontacted|[Cc]all(?:ed)?|[Mm]et with)\s+"
    r"([A-Z][a-z'-]+\s+[A-Z][a-z'-]+)(?=[,.;\s])")
_PLACEHOLDER = re.compile(r"\[(?:" + "|".join(_LABELS) + r")\]")


def norm(value):
    """Collapse whitespace; None and NaN become an empty string."""
    return "" if value is None or value != value else " ".join(str(value).split())


def _tokens(names, minimum=3):
    found = set()
    for name in names:
        for part in re.split(r"[^A-Za-z'\-]+", norm(name)):
            for token in {part, *part.split("-")}:
                token = token.strip("'-")
                if len(token) >= minimum:
                    found.add(token)
    return found


def _alternation(tokens):
    ordered = sorted({t.casefold() for t in tokens}, key=lambda t: (-len(t), t))
    if not ordered:
        return None
    return re.compile(r"(?<![\w'])(?:" + "|".join(map(re.escape, ordered)) + r")(?![\w])", re.I)


def build_lexicon(people, staff):
    """Whole-report name lists, built once and reused for every note."""
    persons = {t for t in _tokens(people) if t.casefold() not in _STOPWORDS}
    staffers = {t for t in _tokens(staff) if t.casefold() not in _STOPWORDS} - persons
    return {"people": _alternation(persons), "staff": _alternation(staffers)}


def scrub(text, lexicon, own_names=(), ids=()):
    """Replace PII with typed placeholders; `own_names` and `ids` come from the note's row."""
    text = "" if text is None or text != text else str(text)
    spans = []

    def add(pattern, label, capitalized=False):
        if pattern is None:
            return
        for m in pattern.finditer(text):
            if capitalized and not m.group(0)[0].isupper():
                continue
            spans.append((m.start(), m.end(), label))

    for label, pattern in _PATTERNS:
        add(pattern, label)
    known = sorted({i for i in map(norm, ids) if len(i) >= 4}, key=lambda i: (-len(i), i))
    if known:
        add(re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, known)) + r")(?!\w)"), "ID")
    add(_alternation(_tokens(own_names, minimum=2)), "NAME")
    add(lexicon["people"], "NAME", capitalized=True)
    add(lexicon["staff"], "STAFF", capitalized=True)
    for pattern in (_HONORIFIC_NAME, _REFERRAL_NAME):
        spans.extend((m.start(1), m.end(1), "NAME") for m in pattern.finditer(text))
    merged = []
    for start, end, label in sorted(spans, key=lambda s: (s[0], -s[1])):
        if merged and start <= merged[-1][1]:
            s0, e0, l0 = merged[-1]
            merged[-1] = (s0, max(e0, end), min(l0, label, key=_RANK.__getitem__))
        else:
            merged.append((start, end, label))
    out, cursor = [], 0
    for start, end, label in merged:
        out.extend((text[cursor:start], f"[{label}]"))
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def has_residual_pii(scrubbed):
    """True if structured detectors still find identifiers outside placeholders."""
    bare = _PLACEHOLDER.sub(lambda m: " " * len(m.group(0)), scrubbed)
    return any(pattern.search(bare) for _, pattern in _PATTERNS)
