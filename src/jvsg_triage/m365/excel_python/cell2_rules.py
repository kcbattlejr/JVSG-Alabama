# Cell 2 of 3 - rules baseline and contract check. Paste into the SECOND Python cell.
# Depends on cell 1 (scrub, norm, build_lexicon, has_residual_pii). Stdlib only; no model.
# Rules mirror the Office Script rules-v1 baseline. Every finding is an UNVERIFIED
# suggestion for qualified staff; this baseline is not an accuracy claim.
import re

DOMAINS = ("TRN", "HSG", "MED", "LEG")
STATES = ("CRT", "ACT", "MIT", "RES", "UNK")
EXTRACTOR = "rules-v1"
MAX_QUOTE = 400
_I = re.I
_RULES = (
    ("TRN", re.compile(r"lacks? (?:reliable )?transportation|no (?:reliable )?(?:transportation"
                       r"|vehicle|ride)|without (?:a )?(?:car|vehicle|ride)|transportation "
                       r"(?:barrier|issue|problem)", _I), None,
     re.compile(r"referred|voucher|bus pass|arranged|provided", _I)),
    ("HSG", re.compile(r"unstable housing|homeless|eviction|unsheltered|couch.?surf|at risk of "
                       r"losing (?:housing|home)|HUD-VASH|SSVF", _I),
     re.compile(r"homeless|eviction|unsheltered|no place to (?:stay|live)", _I),
     re.compile(r"referred|assessment|case manager|placed|enrolled", _I)),
    ("MED", re.compile(r"service-connected|disability rating|medical (?:condition|barrier"
                       r"|appointment)|health (?:condition|issue|care)|PTSD|treatment|VA "
                       r"(?:claim|Medical Center)|injur", _I),
     re.compile(r"suicid|crisis|hospitali[sz]ed", _I),
     re.compile(r"enrolled|scheduled|appointment|receiving|approved", _I)),
    ("LEG", re.compile(r"justice involvement|record.?sealing|fair-chance|legal services|probation"
                       r"|parole|felony|expunge|warrant", _I),
     re.compile(r"\bwarrant\b|incarcerat", _I),
     re.compile(r"legal services|referred|will contact|scheduled", _I)),
)
_RESOLVED = re.compile(r"no longer|resolved|has (?:obtained|secured)|now (?:has|have|living)"
                       r"|problem solved", _I)
_NEGATED = re.compile(r"\b(?:denies|denied|does not (?:have|report)|doesn't have"
                      r"|no (?:current )?(?:barrier|need)s?)\b", _I)
_COLUMNS = {"individual": "individual", "created by": "created_by",
            "last edited by": "last_edited_by", "state id": "state_id", "userid": "userid",
            "case notes": "notes"}


def _classify(sentence, critical, mitigated):
    if _RESOLVED.search(sentence):
        return "RES"
    if critical and critical.search(sentence):
        return "CRT"
    if mitigated and mitigated.search(sentence):
        return "MIT"
    return "ACT"


def extract(note_row, scrubbed):
    """At most one finding per domain, quoting the first matching scrubbed sentence."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", scrubbed) if s.strip()]
    findings = []
    for domain, test, critical, mitigated in _RULES:
        for sentence in sentences:
            if test.search(sentence) and not _NEGATED.search(sentence) \
                    and len(sentence) <= MAX_QUOTE:
                findings.append({
                    "note_row": note_row, "domain": domain,
                    "state": _classify(sentence, critical, mitigated),
                    "evidence_quote": sentence, "source": EXTRACTOR,
                })
                break
    return findings


def violation(finding, scrubbed):
    """Contract check. Returns a reason string, or '' when the finding is acceptable."""
    if finding.get("domain") not in DOMAINS:
        return "domain outside vocabulary"
    if finding.get("state") not in STATES:
        return "state outside vocabulary"
    quote = finding.get("evidence_quote")
    if not isinstance(quote, str) or not quote or len(quote) > MAX_QUOTE:
        return "evidence quote missing or too long"
    if quote not in scrubbed:
        return "evidence quote not found in scrubbed note"
    if has_residual_pii(quote):
        return "evidence quote contains unscrubbed identifiers"
    return ""


def scrub_notes(df):
    """Scrub every note in a case-notes DataFrame. Returns [(note_row, scrubbed_text)].

    `note_row` is the 1-based position in the table. Rows with no note are skipped.
    """
    cols = {}
    for name in df.columns:
        key = _COLUMNS.get(norm(name).lower())
        if key:
            cols[key] = name
    if "notes" not in cols:
        raise ValueError("Case Notes column not found")

    def cell(row, key):
        return norm(row[cols[key]]) if key in cols else ""

    rows = [df.iloc[i] for i in range(len(df))]
    lexicon = build_lexicon(
        [cell(r, "individual") for r in rows],
        [cell(r, k) for r in rows for k in ("created_by", "last_edited_by")],
    )
    out = []
    for position, row in enumerate(rows, start=1):
        raw = row[cols["notes"]]
        if not norm(raw) or norm(row.iloc[0]).lower().startswith("total rows:"):
            continue
        own = [cell(row, "individual"), cell(row, "created_by"), cell(row, "last_edited_by")]
        ids = [cell(row, "state_id"), cell(row, "userid")]
        out.append((position, scrub(raw, lexicon, own, ids)))
    return out


def find_barriers(df):
    """Scrub, extract with the rules baseline, validate. Returns (findings, rejected_count)."""
    findings, rejected = [], 0
    for note_row, scrubbed in scrub_notes(df):
        for finding in extract(note_row, scrubbed):
            if violation(finding, scrubbed):
                rejected += 1
            else:
                findings.append(finding)
    return findings, rejected
