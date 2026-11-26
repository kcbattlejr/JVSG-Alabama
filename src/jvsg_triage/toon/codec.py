"""Schema-driven TOON encoder/decoder for flat tables of text, integers and null.

Same table form as ``jvsg_triage.toon.demo``: ``[N]{fields}:`` then one two-space
indented row per record, and ``[0]:`` for an empty table. Output is deterministic
and decoding rejects anything the encoder would not have written.
"""

import re
from collections.abc import Mapping, Sequence

Cell = str | int | None
Row = Mapping[str, Cell]

_NUMERIC = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_UNESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}


class ToonError(ValueError):
    """Raised for malformed or noncanonical TOON input."""


def _needs_quotes(value: str) -> bool:
    return (
        value == ""
        or value != value.strip()
        or value in ("true", "false", "null")
        or bool(_NUMERIC.match(value))
        or value.startswith("-")
        or any(c in value for c in ',:"\\[]{}')
        or any(ord(c) < 32 for c in value)
    )


def _cell(value: Cell) -> str:
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    if _needs_quotes(value):
        return '"' + "".join(_ESCAPES.get(c, c) for c in value) + '"'
    return value


def encode_table(fields: Sequence[str], rows: Sequence[Row]) -> str:
    if not rows:
        return "[0]:\n"
    for row in rows:
        if set(row) != set(fields):
            raise ToonError("TOON: row fields do not match the schema")
    lines = [f"[{len(rows)}]{{{','.join(fields)}}}:"]
    lines.extend("  " + ",".join(_cell(row[f]) for f in fields) for row in rows)
    return "\n".join(lines) + "\n"


def _split(line: str) -> list[Cell]:
    cells: list[Cell] = []
    buf: list[str] = []
    quoted = was_quoted = False
    i = 0
    while i < len(line):
        c = line[i]
        if quoted:
            if c == "\\":
                i += 1
                if i >= len(line) or line[i] not in _UNESCAPES:
                    raise ToonError("TOON: invalid escape")
                buf.append(_UNESCAPES[line[i]])
            elif c == '"':
                quoted = False
            else:
                buf.append(c)
        elif c == '"' and not buf and not was_quoted:
            quoted = was_quoted = True
        elif c == ",":
            cells.append(_finish("".join(buf), was_quoted))
            buf, was_quoted = [], False
        elif was_quoted:
            raise ToonError("TOON: text after closing quote")
        else:
            buf.append(c)
        i += 1
    if quoted:
        raise ToonError("TOON: unterminated quote")
    cells.append(_finish("".join(buf), was_quoted))
    return cells


def _finish(text: str, was_quoted: bool) -> Cell:
    if was_quoted:
        return text
    if text == "null":
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def decode_table(text: str, fields: Sequence[str]) -> list[dict[str, Cell]]:
    lines = text.splitlines()
    if lines == ["[0]:"]:
        return []
    header = f"[{len(lines) - 1}]{{{','.join(fields)}}}:"
    if not lines or lines[0] != header:
        raise ToonError("TOON: invalid header or row count")
    rows: list[dict[str, Cell]] = []
    for line in lines[1:]:
        if not line.startswith("  "):
            raise ToonError("TOON: invalid row")
        cells = _split(line[2:])
        if len(cells) != len(fields):
            raise ToonError("TOON: wrong number of cells")
        rows.append(dict(zip(fields, cells, strict=True)))
    if encode_table(fields, rows) != text:
        raise ToonError("TOON: noncanonical encoding")
    return rows
