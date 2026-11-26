"""Build a local Excel workbook equivalent to the SharePoint dashboard from the CSVs.

Power Query is replaced by reading the same CSV files in Python; the table names,
columns and suppression wording match the SharePoint workbook. Synthetic input only.
"""

import csv
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet

from jvsg_triage.dashboard_demo.generate import BANDS

NAVY = "1F3A5F"
INT_COLUMNS = {"JVSG_NOTE_COUNT", "DAYS_SINCE_CONTACT", "INDIVIDUALS"}
DATE_COLUMNS = {
    "FY_START", "FY_END", "AS_OF_DATE", "FIRST_JVSG_NOTE_DATE", "LAST_JVSG_NOTE_DATE",
    "LATEST_FY_203_DATE", "LAST_CONTACT_DATE",
}  # fmt: skip


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _typed(column: str, value: str) -> object:
    if value == "":
        return None
    if column in INT_COLUMNS:
        return int(value)
    if column in DATE_COLUMNS:
        return datetime.strptime(value, "%m/%d/%Y").date()
    return value  # State ID, office and LWIA stay text to keep leading zeros


def _add_table(sheet: Worksheet, name: str, header: list[str], rows: list[list[object]]) -> None:
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    for number, title in enumerate(header, start=1):
        sheet.column_dimensions[get_column_letter(number)].width = max(12, len(title) + 2)
        if title in DATE_COLUMNS:
            for cell in sheet[get_column_letter(number)][1:]:
                cell.number_format = "mm/dd/yyyy"
    last = f"{get_column_letter(len(header))}{max(len(rows) + 1, 2)}"
    table = Table(displayName=name, ref=f"A1:{last}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    sheet.add_table(table)


def build_workbook(
    manager: list[dict[str, str]], worklist: list[dict[str, str]], output: Path
) -> Path:
    wb = Workbook()
    default = wb.active
    if default is not None:
        wb.remove(default)
    overview = wb.create_sheet("Overview")
    detail = wb.create_sheet("Watchlist")
    mgr_sheet = wb.create_sheet("Manager_Data")
    work_sheet = wb.create_sheet("Worklist")

    manager = [row for row in manager if row["INDIVIDUALS"] != ""]
    mgr_cols = list(manager[0].keys()) if manager else ["INDIVIDUALS", "FOLLOW_UP_BAND"]
    _add_table(
        mgr_sheet, "Manager", mgr_cols, [[_typed(c, r[c]) for c in mgr_cols] for r in manager]
    )
    work_cols = list(worklist[0].keys())
    _add_table(
        work_sheet, "Worklist", work_cols, [[_typed(c, r[c]) for c in work_cols] for r in worklist]
    )

    # Overview: matrix (Power Query ManagerMatrix equivalent), tiles as live formulas.
    lwias = sorted({r["LWIA_NAME"] or r["INDIVIDUAL_RECORD_LWIA"] for r in manager})
    overview["A1"] = "JVSG follow-up candidates - SYNTHETIC DEMO DATA"
    overview["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    for col in "ABCDEFGH":
        overview[f"{col}1"].fill = PatternFill("solid", fgColor=NAVY)
    counts = "Manager[INDIVIDUALS]"
    band = "Manager[FOLLOW_UP_BAND]"
    overview["A3"], overview["B3"] = "Veterans in report (visible groups)", f"=SUM({counts})"
    for row, name in enumerate(BANDS, start=4):
        overview[f"A{row}"] = name
        overview[f"B{row}"] = (
            f'=IF(COUNTIFS({band},"{name}")=0,"Suppressed",SUMIFS({counts},{band},"{name}"))'
        )
    overview["A8"] = (
        "Groups below 10 are omitted, so totals cover visible groups only. 'Suppressed' "
        "means no visible group, not a confirmed zero."
    )
    overview.append([])
    start = 10
    overview.cell(row=start, column=1, value="LWIA")
    for offset, name in enumerate(BANDS, start=2):
        overview.cell(row=start, column=offset, value=name)
    index = {
        (r["LWIA_NAME"] or r["INDIVIDUAL_RECORD_LWIA"], r["FOLLOW_UP_BAND"]): int(r["INDIVIDUALS"])
        for r in manager
    }
    for i, lwia in enumerate(lwias, start=start + 1):
        overview.cell(row=i, column=1, value=lwia)
        for offset, name in enumerate(BANDS, start=2):
            overview.cell(row=i, column=offset, value=index.get((lwia, name), 0))
    if lwias:
        chart = BarChart()
        chart.type, chart.grouping, chart.overlap = "col", "stacked", 100
        chart.title = "Veterans by LWIA and follow-up band"
        chart.y_axis.title, chart.x_axis.title = "Number of veterans", "LWIA"
        end = start + len(lwias)
        chart.add_data(
            Reference(overview, min_col=2, max_col=4, min_row=start, max_row=end),
            titles_from_data=True,
        )
        chart.set_categories(Reference(overview, min_col=1, min_row=start + 1, max_row=end))
        chart.width, chart.height = 22, 9
        overview.add_chart(chart, f"A{end + 3}")
    overview.column_dimensions["A"].width = 38

    # Watchlist: top 50 overdue by days since contact (identifier-bearing, so restricted).
    overdue = sorted(
        (r for r in worklist if r["FOLLOW_UP_BAND"] == "Overdue"),
        key=lambda r: -int(r["DAYS_SINCE_CONTACT"]),
    )[:50]
    keep = [
        "INDIVIDUAL_USERNAME",
        "STATE_ID",
        "OFFICE_NAME",
        "LAST_CONTACT_DATE",
        "DAYS_SINCE_CONTACT",
        "FOLLOW_UP_BAND",
        "LAST_CONTACT_STAFF_NAME",
    ]
    detail.append(["Top 50 overdue, longest wait first (synthetic)"])
    detail.append(keep)
    for r in overdue:
        detail.append([_typed(c, r[c]) for c in keep])
    for number in range(1, len(keep) + 1):
        detail.column_dimensions[get_column_letter(number)].width = 24

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    return output
