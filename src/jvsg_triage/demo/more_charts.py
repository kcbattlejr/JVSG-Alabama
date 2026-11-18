"""Excel 'More Charts' tab: office and support-need views with their numbers beside each chart."""

from collections.abc import Sequence

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrData, StrRef, StrVal
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.legend import Legend
from openpyxl.chart.text import RichText
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from openpyxl.drawing.text import CharacterProperties, Paragraph, ParagraphProperties
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from jvsg_triage.demo.insights import (
    ALERT_SERIES,
    STATE_SERIES,
    Row,
    most_common_areas,
    office_follow_up,
    office_review,
    people_by_area_count,
    review_first,
    support_by_area,
)
from jvsg_triage.demo.labels import OFFICE_LABELS, REVIEW_LABELS, barrier_summary
from jvsg_triage.demo.models import Alert, Profile, Review

NAVY = "16324F"
INK = "243746"
MUTED = "587080"
PALE = "EAF1F6"
LINE = "D7E1E8"
ALERT_COLORS = ("2E8B57", "B8730A", "C94C4C")
REVIEW_COLORS = ("B8730A", "2E8B57")
STATE_COLORS = ("C94C4C", "B8730A", "2F6EA5", "2E8B57", "6B7A88")
BLOCK_ROWS = 17


def white_labels() -> DataLabelList:
    properties = CharacterProperties(b=True, sz=1200, solidFill="FFFFFF")
    labels = DataLabelList(
        showVal=True, showSerName=False, showCatName=False, showLegendKey=False,
        showPercent=False, dLblPos="ctr",
    )
    labels.numFmt = "0;;;"
    labels.txPr = RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=properties))])
    return labels


def readable_text(size: int = 1200, color: str = "1F2937") -> RichText:
    properties = CharacterProperties(sz=size, solidFill=color)
    return RichText(p=[Paragraph(pPr=ParagraphProperties(defRPr=properties))])


def make_readable(chart: BarChart) -> None:
    """Give axis and legend text a legible size so long category names wrap, not shrink."""
    chart.x_axis.txPr = readable_text()
    if chart.y_axis.delete is not True:
        chart.y_axis.txPr = readable_text()
    if chart.legend is not None:
        chart.legend.txPr = readable_text()


def stacked_chart(
    ws: Worksheet, title: str, header_row: int, last_row: int, last_col: int,
    series: Sequence[str], colors: Sequence[str], labels: Sequence[str],
) -> BarChart:
    chart = BarChart()
    chart.type = "bar"
    chart.grouping = "stacked"
    chart.overlap = 100
    chart.gapWidth = 60
    chart.style = 10
    chart.title = title
    chart.add_data(
        Reference(ws, min_col=2, max_col=last_col, min_row=header_row, max_row=last_row),
        titles_from_data=True,
    )
    categories = Reference(ws, min_col=1, min_row=header_row + 1, max_row=last_row)
    for item, color in zip(chart.series, colors, strict=True):
        item.graphicalProperties.solidFill = color
        item.graphicalProperties.line.solidFill = "FFFFFF"
        item.cat = AxDataSource(strRef=StrRef(
            f=str(categories),
            strCache=StrData(ptCount=len(labels), pt=[
                StrVal(idx=index, v=label) for index, label in enumerate(labels)
            ]),
        ))
    chart.dataLabels = white_labels()
    chart.x_axis.scaling.orientation = "maxMin"
    chart.x_axis.delete = False
    chart.y_axis.delete = True
    chart.y_axis.majorGridlines = None
    if len(series) > 1:
        chart.legend = Legend(legendPos="b")
    else:
        chart.legend = None
    chart.visible_cells_only = False
    make_readable(chart)
    return chart


def add_block(
    ws: Worksheet, top: int, heading: str, note: str, first_header: str,
    series: Sequence[str], colors: Sequence[str], rows: Sequence[Row], title: str,
) -> None:
    ws.merge_cells(start_row=top, start_column=1, end_row=top, end_column=17)
    ws.cell(top, 1, heading).font = Font(name="Aptos", size=14, bold=True, color="FFFFFF")
    for column in range(1, 18):
        ws.cell(top, column).fill = PatternFill("solid", fgColor=NAVY)
    ws.cell(top, 1).alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[top].height = 28
    ws.merge_cells(start_row=top + 1, start_column=1, end_row=top + 2, end_column=5)
    ws.cell(top + 1, 1, note).font = Font(name="Aptos", size=11, color=INK)
    ws.cell(top + 1, 1).alignment = Alignment(wrap_text=True, vertical="top", indent=1)

    header_row = top + 4
    border = Border(bottom=Side(style="thin", color=LINE))
    for column, name in enumerate((first_header, *series), start=1):
        cell = ws.cell(header_row, column, name)
        cell.font = Font(name="Aptos", size=11, bold=True, color=NAVY)
        cell.fill = PatternFill("solid", fgColor=PALE)
        cell.alignment = Alignment(
            horizontal="left" if column == 1 else "center", vertical="center", wrap_text=True,
        )
    ws.row_dimensions[header_row].height = 34
    for offset, (label, values) in enumerate(rows, start=1):
        ws.cell(header_row + offset, 1, label).font = Font(name="Aptos", size=11, color=INK)
        ws.row_dimensions[header_row + offset].height = 22
        for column, value in enumerate(values, start=2):
            cell = ws.cell(header_row + offset, column, value)
            cell.font = Font(name="Aptos", size=11, bold=True, color=INK)
            cell.alignment = Alignment(horizontal="center")
        for column in range(1, len(series) + 2):
            ws.cell(header_row + offset, column).border = border

    last_row = header_row + len(rows)
    chart = stacked_chart(
        ws, title, header_row, last_row, len(series) + 1, series, colors,
        [label for label, _ in rows],
    )
    chart.anchor = TwoCellAnchor(  # type: ignore[assignment]
        editAs="twoCell",
        _from=AnchorMarker(col=6, row=top),
        to=AnchorMarker(col=17, row=top + BLOCK_ROWS - 2),
    )
    ws.add_chart(chart)


def add_more_charts(workbook: Workbook, profiles: Sequence[Profile]) -> None:
    sheet = workbook.create_sheet("More Charts", 1)
    sheet.sheet_view.showGridLines = False
    sheet.sheet_view.zoomScale = 85
    widths = {1: 32, 2: 14, 3: 14, 4: 14, 5: 14, 6: 14, 7: 14}
    for column in range(1, 18):
        sheet.column_dimensions[get_column_letter(column)].width = widths.get(column, 11)
    sheet.merge_cells("A1:Q1")
    sheet["A1"] = "Where staff attention may be needed"
    sheet["A1"].font = Font(name="Aptos Display", size=22, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor=NAVY)
    sheet["A1"].alignment = Alignment(vertical="center", indent=1)
    sheet.row_dimensions[1].height = 42
    sheet.merge_cells("A2:Q2")
    sheet["A2"] = (
        "SYNTHETIC DEMONSTRATION  |  Every number counts people across the whole report, "
        "not referrals. Staff decide next steps."
    )
    sheet["A2"].font = Font(name="Aptos", size=10, bold=True, color=MUTED)
    sheet["A2"].fill = PatternFill("solid", fgColor=PALE)
    sheet["A2"].alignment = Alignment(vertical="center", indent=1)
    sheet.row_dimensions[2].height = 24

    blocks = (
        ("Which offices have people waiting longest?",
         "Days since recorded contact, or since assessment if no contact is recorded.",
         "Demonstration office", ALERT_SERIES, ALERT_COLORS, office_follow_up(profiles),
         "People by days since contact or assessment"),
        ("How far along is staff review?",
         "\u201cAwaiting staff review\u201d means no staff review is recorded yet.",
         "Demonstration office", [REVIEW_LABELS[r] for r in Review], REVIEW_COLORS,
         office_review(profiles), "People by staff review status"),
        ("What kinds of support are recorded?",
         "The recorded status for everyone in the report, in each area of support.",
         "Area of support", STATE_SERIES, STATE_COLORS, support_by_area(profiles),
         "People by recorded support status"),
        ("How many areas of support does each person have?",
         "Counts areas marked critical or needing support. People with several areas may "
         "benefit from coordinated follow-up.",
         "Areas marked critical or needing support", ["People"], ("2F6EA5",),
         people_by_area_count(profiles), "People by number of areas"),
    )
    top = 4
    for heading, note, first_header, series, colors, rows, title in blocks:
        add_block(sheet, top, heading, note, first_header, series, colors, rows, title)
        top += BLOCK_ROWS + 1

    sheet.merge_cells(start_row=top, start_column=1, end_row=top, end_column=17)
    sheet.cell(top, 1, "Staff may want to look here first").font = Font(
        name="Aptos", size=14, bold=True, color="FFFFFF")
    for column in range(1, 18):
        sheet.cell(top, column).fill = PatternFill("solid", fgColor=NAVY)
    sheet.cell(top, 1).alignment = Alignment(vertical="center", indent=1)
    sheet.row_dimensions[top].height = 28
    sheet.merge_cells(start_row=top + 1, start_column=1, end_row=top + 2, end_column=17)
    sheet.cell(top + 1, 1, (
        "People in the 30+ day band who also have a critical barrier recorded, longest wait "
        "first. This is a sorting aid only; qualified staff decide who to contact and what "
        "support to offer."
    )).font = Font(name="Aptos", size=11, color=INK)
    sheet.cell(top + 1, 1).alignment = Alignment(wrap_text=True, vertical="top", indent=1)
    header_row = top + 4
    for column, name in ((1, "Demonstration participant"), (2, "Days since contact or assessment"),
                         (4, "Demonstration office"), (7, "Most pressing recorded need"),
                         (11, "Staff review status")):
        cell = sheet.cell(header_row, column, name)
        cell.font = Font(name="Aptos", size=11, bold=True, color=NAVY)
    for column in range(1, 18):
        sheet.cell(header_row, column).fill = PatternFill("solid", fgColor=PALE)
        sheet.cell(header_row, column).alignment = Alignment(vertical="center", wrap_text=True)
    sheet.row_dimensions[header_row].height = 34
    people = review_first(profiles)
    if not people:
        sheet.cell(header_row + 1, 1, "No one is in the 30+ day band with a critical barrier.")
    for row, profile in enumerate(people, start=header_row + 1):
        for column, value in (
            (1, profile.demo_id), (2, profile.idle_days), (4, OFFICE_LABELS[profile.office]),
            (7, barrier_summary(profile)), (11, REVIEW_LABELS[profile.review]),
        ):
            sheet.cell(row, column, value).font = Font(name="Aptos", size=11, color=INK)
        sheet.cell(row, 2).alignment = Alignment(horizontal="left")
        for column in range(1, 18):
            sheet.cell(row, column).border = Border(bottom=Side(style="hair", color=LINE))
    last = header_row + max(len(people), 1)
    areas, count = most_common_areas(profiles)
    sheet.cell(last + 2, 1, (
        f"Most often marked critical or needing support: {' and '.join(areas)} "
        f"({count} people each)."
    )).font = Font(name="Aptos", size=11, bold=True, color=INK)
    waiting = sum(p.alert == Alert.RED for p in profiles)
    sheet.cell(last + 3, 1, (
        f"{waiting} of {len(profiles)} people are in the 30+ day band; "
        f"{len(people)} of them have a critical barrier recorded."
    )).font = Font(name="Aptos", size=11, color=INK)

    sheet.print_area = f"A1:Q{last + 3}"
    sheet.page_setup.orientation = "portrait"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
