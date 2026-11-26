# Cell 3 of 3 - deterministic TOON encoder/decoder and review table.
# Paste into the THIRD Python cell. Depends on cell 2 (DOMAINS, find_barriers). Stdlib only.
# Matches the table form of jvsg_triage.toon.demo: "[N]{fields}:" then 2-space rows,
# "[0]:" for an empty table. Reviewer fields stay null until a human acts; no State ID,
# name or other identifier is ever written to the TOON text.
import re

FIELDS = ("finding_id", "note_row", "domain", "state", "evidence_quote", "source",
          "verification_status", "reviewer_action", "reviewer_role", "reviewed_on")
# Excel cells hold at most 32,767 characters, so output is split into valid tables.
CHUNK_LIMIT = 30000
_NUMERIC = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_UNESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}


def _needs_quotes(value):
    return (value == "" or value != value.strip() or value in ("true", "false", "null")
            or bool(_NUMERIC.match(value)) or value.startswith("-")
            or any(c in value for c in ',:"\\[]{}') or any(ord(c) < 32 for c in value))


def _cell(value):
    if value is None:
        return "null"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    value = str(value)
    if _needs_quotes(value):
        return '"' + "".join(_ESCAPES.get(c, c) for c in value) + '"'
    return value


def review_rows(findings):
    """Add the Unverified review columns; order is deterministic (note, domain)."""
    ordered = sorted(findings, key=lambda f: (f["note_row"], DOMAINS.index(f["domain"])))
    return [{
        "finding_id": f"{f['note_row']}|{f['domain']}", "note_row": f["note_row"],
        "domain": f["domain"], "state": f["state"], "evidence_quote": f["evidence_quote"],
        "source": f["source"], "verification_status": "Unverified", "reviewer_action": None,
        "reviewer_role": None, "reviewed_on": None,
    } for f in ordered]


def toon_encode(rows):
    """Encode review rows as one TOON table."""
    if not rows:
        return "[0]:\n"
    lines = [f"[{len(rows)}]{{{','.join(FIELDS)}}}:"]
    lines.extend("  " + ",".join(_cell(row[field]) for field in FIELDS) for row in rows)
    return "\n".join(lines) + "\n"


def toon_chunks(rows):
    """Split rows into valid TOON tables that each fit in one Excel cell."""
    chunks, current, size = [], [], 0
    for row in rows:
        length = len(toon_encode([row]))
        if current and size + length > CHUNK_LIMIT:
            chunks.append(toon_encode(current))
            current, size = [], 0
        current.append(row)
        size += length
    chunks.append(toon_encode(current))
    return chunks


def _split(line):
    cells, buf, quoted, was_quoted = [], [], False, False
    i = 0
    while i < len(line):
        c = line[i]
        if quoted:
            if c == "\\":
                i += 1
                if i >= len(line) or line[i] not in _UNESCAPES:
                    raise ValueError("TOON: invalid escape")
                buf.append(_UNESCAPES[line[i]])
            elif c == '"':
                quoted = False
            else:
                buf.append(c)
        elif c == '"' and not buf and not was_quoted:
            quoted = was_quoted = True
        elif c == ",":
            cells.append(("".join(buf), was_quoted))
            buf, was_quoted = [], False
        else:
            if was_quoted:
                raise ValueError("TOON: text after closing quote")
            buf.append(c)
        i += 1
    if quoted:
        raise ValueError("TOON: unterminated quote")
    cells.append(("".join(buf), was_quoted))
    return cells


def toon_decode(text):
    """Read back the exact form toon_encode writes; raises ValueError otherwise."""
    if text == "[0]:\n":
        return []
    lines = text.splitlines()
    if len(lines) < 2 or lines[0] != f"[{len(lines) - 1}]{{{','.join(FIELDS)}}}:":
        raise ValueError("TOON: invalid header or row count")
    rows = []
    for line in lines[1:]:
        if not line.startswith("  "):
            raise ValueError("TOON: invalid row")
        cells = _split(line[2:])
        if len(cells) != len(FIELDS):
            raise ValueError("TOON: invalid row width")
        row = {}
        for field, (raw, quoted) in zip(FIELDS, cells, strict=True):
            if quoted:
                row[field] = raw
            elif raw == "null":
                row[field] = None
            elif field == "note_row":
                row[field] = int(raw)
            else:
                row[field] = raw
        rows.append(row)
    if toon_encode(rows) != text:
        raise ValueError("TOON: noncanonical encoding")
    return rows


def run_pipeline(df):
    """One call for the sheet: returns (review_rows, rejected_count, toon_chunks)."""
    findings, rejected = find_barriers(df)
    rows = review_rows(findings)
    return rows, rejected, toon_chunks(rows)
