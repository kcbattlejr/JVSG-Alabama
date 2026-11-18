"""Dependency-free inline SVG bar charts for the offline HTML dashboard."""

from collections.abc import Sequence
from html import escape
from textwrap import wrap

from jvsg_triage.demo.insights import Row

BAR_LEFT = 270
BAR_MAX = 330
ROW_HEIGHT = 60
BAR_HEIGHT = 34
WIDTH = 760
LABEL_CHARS = 22
LINE_HEIGHT = 22


def label_text(label: str, middle: float) -> str:
    """Wrap long row labels onto lines centred on the bar instead of overrunning it."""
    lines = wrap(label, LABEL_CHARS, break_long_words=False) or [label]
    first = middle - LINE_HEIGHT * (len(lines) - 1) / 2
    spans = "".join(
        f'<tspan x="0" y="{first + i * LINE_HEIGHT:.1f}">{escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return f'<text font-size="20" fill="#f8fafc">{spans}</text>'


def legend(series: Sequence[str], colors: Sequence[str]) -> str:
    items = "".join(
        f'<li><span class="swatch" style="background:{color}"></span>{escape(name)}</li>'
        for name, color in zip(series, colors, strict=True)
    )
    return f'<ul class="legend">{items}</ul>'


def stacked_bars(
    rows: Sequence[Row], series: Sequence[str], colors: Sequence[str], summary: str,
    unit: str = "people",
) -> str:
    """Horizontal stacked bars with every count written on the bar; no axis to decode."""
    largest = max((sum(values) for _, values in rows), default=0) or 1
    height = ROW_HEIGHT * len(rows) + 6
    parts = [
        f'<svg viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(summary)}" '
        'font-family="Segoe UI, Arial, sans-serif">'
    ]
    for index, (label, values) in enumerate(rows):
        top = index * ROW_HEIGHT + 6
        middle = top + BAR_HEIGHT / 2 + 7
        parts.append(label_text(label, middle))
        left = float(BAR_LEFT)
        for value, name, color in zip(values, series, colors, strict=True):
            if not value:
                continue
            width = BAR_MAX * value / largest
            parts.append(
                f'<rect x="{left:.1f}" y="{top}" width="{width:.1f}" height="{BAR_HEIGHT}" '
                f'fill="{color}" stroke="#06182c" stroke-width="2">'
                f'<title>{escape(label)}: {value} {unit} - {escape(name)}</title></rect>'
            )
            if width >= 26:
                parts.append(
                    f'<text x="{left + width / 2:.1f}" y="{middle}" font-size="20" '
                    f'font-weight="700" text-anchor="middle" fill="#06182c">{value}</text>'
                )
            left += width
        total = sum(values)
        if len(values) > 1 or not total:
            note = f"{total} total" if len(values) > 1 else "0"
            parts.append(
                f'<text x="{left + 10:.1f}" y="{middle}" font-size="18" fill="#cbd5e1">'
                f'{note}</text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def number_table(rows: Sequence[Row], first_column: str, series: Sequence[str]) -> str:
    head = "".join(f"<th>{escape(name)}</th>" for name in (first_column, *series))
    body = "".join(
        f"<tr><th>{escape(label)}</th>" + "".join(f"<td>{value}</td>" for value in values)
        + "</tr>"
        for label, values in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
