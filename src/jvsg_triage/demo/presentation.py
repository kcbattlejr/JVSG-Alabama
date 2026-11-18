"""Excel and standalone HTML snapshots, generated from the same validated profiles."""

import io
import json
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrData, StrRef, StrVal
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

from jvsg_triage.demo.insights import (
    ALERT_SERIES,
    REVIEW_SERIES,
    STATE_SERIES,
    most_common_areas,
    office_follow_up,
    office_review,
    people_by_area_count,
    review_first,
    support_by_area,
)
from jvsg_triage.demo.labels import (
    ALERT_LABELS,
    ALERT_MEANINGS,
    DOMAIN_LABELS,
    FIELD_LABELS,
    OFFICE_LABELS,
    REVIEW_LABELS,
    STATE_LABELS,
    STATE_MEANINGS,
    barrier_summary,
    display_date,
    profile_values,
)
from jvsg_triage.demo.models import DOMAINS, Alert, Office, Profile, Review, State
from jvsg_triage.demo.more_charts import add_more_charts, make_readable
from jvsg_triage.demo.svg_charts import legend, number_table, stacked_bars
from jvsg_triage.toon.demo import encode

FIXED_TIME = datetime(2026, 1, 1)
PRESENTATION_VERSION = "paired-report-review-excel-9"
PROFILE_FIELDS = (
    "demo_id", "office", "assessment_date", "last_contact_date",
    "TRN", "HSG", "MED", "LEG", "review", "as_of", "idle_days", "alert",
)


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def summary(profiles: list[Profile]) -> dict[str, object]:
    alerts = Counter(profile.alert.value for profile in profiles)
    offices = Counter(profile.office.value for profile in profiles)
    return {
        "synthetic_only": True,
        "as_of": profiles[0].as_of.isoformat(),
        "participants": len(profiles),
        "alerts": {alert.value: alerts[alert.value] for alert in Alert},
        "offices": dict(sorted(offices.items())),
        "pending_review": sum(profile.review == Review.PENDING for profile in profiles),
        "barriers": {
            domain: {
                state.value: sum(getattr(profile, domain) == state for profile in profiles)
                for state in State
            }
            for domain in DOMAINS
        },
    }


def save_workbook(workbook: Workbook, path: Path) -> None:
    """Canonical ZIP metadata and core timestamps make same-input XLSX bytes stable."""
    workbook.properties.creator = "JVSG synthetic demo"
    workbook.properties.lastModifiedBy = "JVSG synthetic demo"
    workbook.properties.created = FIXED_TIME
    workbook.properties.modified = FIXED_TIME
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    with ZipFile(stream) as source, ZipFile(path, "w", compression=ZIP_DEFLATED) as target:
        for name in sorted(source.namelist()):
            content = source.read(name)
            if name == "docProps/core.xml":
                # openpyxl overwrites modified on save; replace only that element's text.
                from xml.etree import ElementTree

                root = ElementTree.fromstring(content)
                modified = root.find("{http://purl.org/dc/terms/}modified")
                assert modified is not None
                modified.text = "2026-01-01T00:00:00Z"
                content = ElementTree.tostring(root, encoding="utf-8")
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            target.writestr(info, content)


def add_source_validation(workbook: Workbook) -> None:
    sheet = workbook["Demo Intake"]
    sheet.row_dimensions[1].hidden = True
    for cell in sheet[2]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="122D52")
    for columns, choices in (
        (("E", "F", "G", "H"), ",".join(STATE_LABELS.values())),
        (("I",), ",".join(REVIEW_LABELS.values())),
        (("B",), ",".join(OFFICE_LABELS.values())),
    ):
        validation = DataValidation(type="list", formula1=f'"{choices}"', allow_blank=False)
        validation.errorTitle = "Synthetic demo vocabulary only"
        validation.error = "Select a listed value. Do not enter personal information."
        validation.showErrorMessage = True
        validation.errorStyle = "stop"
        sheet.add_data_validation(validation)
        for column in columns:
            validation.add(f"{column}3:{column}10002")


def label_categories(chart: BarChart, source: Reference, labels: tuple[str, ...]) -> None:
    chart.series[0].cat = AxDataSource(strRef=StrRef(
        f=str(source),
        strCache=StrData(ptCount=len(labels), pt=[
            StrVal(idx=index, v=label) for index, label in enumerate(labels)
        ]),
    ))


def excel_dashboard(profiles: list[Profile], source_hash: str) -> Workbook:
    navy = "16324F"
    blue = "245B7A"
    green = "2E8B57"
    amber = "D28B16"
    red = "C94C4C"
    ink = "243746"
    muted = "587080"
    pale = "EAF1F6"
    line = "D7E1E8"
    white = "FFFFFF"
    workbook = Workbook()
    dashboard = workbook.create_sheet("Dashboard", 0)
    workbook.remove(workbook["Sheet"])
    dashboard.sheet_view.showGridLines = False
    dashboard.sheet_view.zoomScale = 85
    for column in range(1, 18):
        dashboard.column_dimensions[get_column_letter(column)].width = 4 if column == 9 else 13

    dashboard.merge_cells("A1:Q1")
    dashboard["A1"] = "Veteran follow-up and support needs"
    dashboard["A1"].font = Font(name="Aptos Display", size=22, bold=True, color=white)
    dashboard["A1"].fill = PatternFill("solid", fgColor=navy)
    dashboard["A1"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[1].height = 42

    dashboard.merge_cells("A2:Q2")
    dashboard["A2"] = (
        "SYNTHETIC DEMONSTRATION  |  Offline snapshot  |  No live SharePoint connection"
    )
    dashboard["A2"].font = Font(name="Aptos", size=10, bold=True, color=muted)
    dashboard["A2"].fill = PatternFill("solid", fgColor=pale)
    dashboard["A2"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[2].height = 24

    counts = Counter(profile.alert for profile in profiles)
    cards = (
        ("A4:D4", "A5:D6", "PEOPLE IN SNAPSHOT", len(profiles), navy),
        ("E4:H4", "E5:H6", ALERT_LABELS[Alert.GREEN].upper(), counts[Alert.GREEN], green),
        ("J4:M4", "J5:M6", ALERT_LABELS[Alert.YELLOW].upper(), counts[Alert.YELLOW], amber),
        ("N4:Q4", "N5:Q6", ALERT_LABELS[Alert.RED].upper(), counts[Alert.RED], red),
    )
    card_border = Border(
        left=Side(style="thin", color=line),
        right=Side(style="thin", color=line),
        top=Side(style="thin", color=line),
        bottom=Side(style="thin", color=line),
    )
    for label_range, value_range, label, value, accent in cards:
        dashboard.merge_cells(label_range)
        dashboard.merge_cells(value_range)
        label_cell = dashboard[label_range.split(":")[0]]
        value_cell = dashboard[value_range.split(":")[0]]
        label_cell.value = label
        value_cell.value = value
        label_cell.font = Font(name="Aptos", size=9, bold=True, color=muted)
        label_cell.alignment = Alignment(horizontal="center", vertical="center")
        value_cell.font = Font(name="Aptos Display", size=26, bold=True, color=accent)
        value_cell.alignment = Alignment(horizontal="center", vertical="center")
        for cell_range, fill in ((label_range, pale), (value_range, white)):
            for row in dashboard[cell_range]:
                for cell in row:
                    cell.fill = PatternFill("solid", fgColor=fill)
                    cell.border = card_border
    dashboard.row_dimensions[4].height = 22
    dashboard.row_dimensions[5].height = 25
    dashboard.row_dimensions[6].height = 25

    pending = sum(profile.review == Review.PENDING for profile in profiles)
    reviewed = len(profiles) - pending
    dashboard.merge_cells("A7:Q7")
    dashboard["A7"] = (
        f"Staff review status: {pending} awaiting review  |  {reviewed} reviewed"
        "  |  More charts by office and support area: see the More Charts tab"
    )
    dashboard["A7"].font = Font(name="Aptos", size=10, color=ink)
    dashboard["A7"].fill = PatternFill("solid", fgColor="F4F7F9")
    dashboard["A7"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[7].height = 24

    watchlist = workbook.create_sheet("Watchlist")
    watchlist.append([
        *(FIELD_LABELS[field] for field in PROFILE_FIELDS),
        "Most pressing recorded need", "Who decides the next step?",
    ])
    for profile in profiles:
        values = profile_values(profile)
        watchlist.append([
            *(values[field] for field in PROFILE_FIELDS), barrier_summary(profile),
            "Qualified staff review; no automatic referral",
        ])
    watchlist["P1"] = "Contact status"
    watchlist["Q1"] = "Number of people"
    contact_labels = tuple(ALERT_LABELS[alert] for alert in Alert)
    for row, (alert, label) in enumerate(zip(Alert, contact_labels, strict=True), start=2):
        watchlist.cell(row, 16, label)
        watchlist.cell(row, 17, counts[alert])
    watchlist["P6"] = "Area of support"
    watchlist["Q6"] = "People marked critical or needing support"
    for row, domain in enumerate(DOMAINS, start=7):
        watchlist.cell(row, 16, DOMAIN_LABELS[domain])
        watchlist.cell(row, 17, sum(getattr(p, domain) in (State.CRT, State.ACT) for p in profiles))
    for column in (16, 17):
        watchlist.column_dimensions[get_column_letter(column)].hidden = True

    chart = BarChart()
    chart.type = "bar"
    chart.style = 10
    chart.title = "Days since contact or assessment"
    chart.add_data(Reference(watchlist, min_col=17, min_row=1, max_row=4), titles_from_data=True)
    label_categories(chart, Reference(watchlist, min_col=16, min_row=2, max_row=4), contact_labels)
    chart.series[0].data_points = [
        DataPoint(idx=index, spPr=GraphicalProperties(solidFill=color))
        for index, color in enumerate((green, amber, red))
    ]

    barrier_chart = BarChart()
    barrier_chart.type = "col"
    barrier_chart.style = 10
    barrier_chart.title = "Critical or needs support"
    barrier_chart.add_data(
        Reference(watchlist, min_col=17, min_row=6, max_row=10), titles_from_data=True,
    )
    label_categories(
        barrier_chart, Reference(watchlist, min_col=16, min_row=7, max_row=10),
        tuple(DOMAIN_LABELS[domain] for domain in DOMAINS),
    )
    barrier_chart.x_axis.axPos = "b"
    barrier_chart.y_axis.axPos = "l"
    barrier_chart.series[0].graphicalProperties.solidFill = blue
    barrier_chart.series[0].graphicalProperties.line.solidFill = blue
    for figure, first_col, end_col in ((chart, 0, 8), (barrier_chart, 9, 17)):
        figure.dataLabels = DataLabelList(
            showVal=True, showSerName=False, showCatName=False, showLegendKey=False,
            showPercent=False, dLblPos="outEnd",
        )
        figure.legend = None
        figure.visible_cells_only = False
        make_readable(figure)
        anchor = TwoCellAnchor(
            editAs="twoCell",
            _from=AnchorMarker(col=first_col, row=8),
            to=AnchorMarker(col=end_col, row=26),
        )
        # openpyxl accepts drawing anchors; the installed stub only declares str.
        figure.anchor = anchor  # type: ignore[assignment]
        dashboard.add_chart(figure)

    dashboard.row_dimensions[28].height = 36
    for start, end, caption in (
        ("A28", "H28", "Each person is counted once. If no contact is recorded, use assessment."),
        ("J28", "Q28", "Each column counts people. A person can appear in more than one area."),
    ):
        dashboard.merge_cells(f"{start}:{end}")
        dashboard[start] = caption
        dashboard[start].font = Font(name="Aptos", size=10, color=ink)
        dashboard[start].alignment = Alignment(vertical="center", wrap_text=True, indent=1)

    dashboard.merge_cells("A29:Q29")
    dashboard["A29"] = "HOW TO READ THIS SNAPSHOT"
    dashboard["A29"].font = Font(name="Aptos", size=11, bold=True, color=white)
    dashboard["A29"].fill = PatternFill("solid", fgColor=navy)
    dashboard["A29"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[29].height = 24
    notes = (
        *((ALERT_LABELS[alert], ALERT_MEANINGS[alert]) for alert in Alert),
        (
            "Support chart",
            "Shows critical and needs-support records only. See Watchlist for all recorded states.",
        ),
        (
            "When no contact is recorded",
            "Days are counted from assessment instead. These thresholds are demo assumptions.",
        ),
        (
            "Contact is not a service outcome",
            "Recent contact does not mean a person's support needs are resolved.",
        ),
        (
            "Who makes decisions?",
            "Qualified staff interpret needs and approve referrals. Nothing is sent automatically.",
        ),
    )
    for row, (label, meaning) in enumerate(notes, start=30):
        dashboard.merge_cells(f"A{row}:D{row}")
        dashboard.merge_cells(f"E{row}:Q{row}")
        dashboard.cell(row, 1, label)
        dashboard.cell(row, 5, meaning)
        dashboard.cell(row, 1).font = Font(name="Aptos", size=10, bold=True, color=blue)
        dashboard.cell(row, 5).font = Font(name="Aptos", size=10, color=ink)
        dashboard.cell(row, 1).alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        dashboard.cell(row, 5).alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        dashboard.row_dimensions[row].height = 30
        for cell in dashboard[row]:
            cell.fill = PatternFill("solid", fgColor="F4F7F9" if row % 2 == 0 else white)
            cell.border = Border(bottom=Side(style="hair", color=line))
    dashboard.freeze_panes = "A4"
    dashboard.print_area = f"A1:Q{dashboard.max_row}"
    dashboard.page_setup.orientation = "landscape"
    dashboard.page_setup.fitToWidth = 1
    dashboard.page_setup.fitToHeight = 1
    dashboard.sheet_properties.pageSetUpPr.fitToPage = True
    dashboard.page_margins.left = 0.25
    dashboard.page_margins.right = 0.25
    dashboard.page_margins.top = 0.4
    dashboard.page_margins.bottom = 0.4

    watchlist.freeze_panes = "C2"
    table = Table(displayName="SyntheticWatchlist", ref=f"A1:N{len(profiles) + 1}")
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showFirstColumn=False, showLastColumn=False,
        showRowStripes=True, showColumnStripes=False,
    )
    watchlist.add_table(table)
    colors = {
        ALERT_LABELS[Alert.GREEN]: "DDF2E5",
        ALERT_LABELS[Alert.YELLOW]: "FFF0CC",
        ALERT_LABELS[Alert.RED]: "FCE1E1",
    }
    watchlist.sheet_view.showGridLines = False
    watchlist.sheet_view.zoomScale = 80
    watchlist.row_dimensions[1].height = 38
    for cell in watchlist[1]:
        cell.font = Font(name="Aptos", size=10, bold=True, color=white)
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in watchlist.iter_rows(min_row=2, max_row=len(profiles) + 1, max_col=14):
        row[11].fill = PatternFill("solid", fgColor=colors[str(row[11].value)])
        row[8].fill = PatternFill(
            "solid", fgColor="FFF0CC" if row[8].value == REVIEW_LABELS[Review.PENDING]
            else "DDF2E5",
        )
        for index in (2, 3, 9):
            row[index].number_format = "mmm d, yyyy;@"
        for cell in row:
            cell.font = Font(name="Aptos", size=10, color=ink)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        if row[3].value is None:
            watchlist.cell(row[3].row, 4, "No contact recorded; counted from assessment")
    watchlist_widths = (
        15, 26, 18, 30, 21, 21, 21, 21, 24, 18, 13, 26, 40, 42,
    )
    for index, width in enumerate(watchlist_widths, start=1):
        watchlist.column_dimensions[get_column_letter(index)].width = width
    for row_index in range(2, len(profiles) + 2):
        watchlist.row_dimensions[row_index].height = 42
    watchlist.print_title_rows = "1:1"
    watchlist.page_setup.orientation = "landscape"
    watchlist.page_setup.fitToWidth = 1
    watchlist.page_setup.fitToHeight = 0
    watchlist.sheet_properties.pageSetUpPr.fitToPage = True

    toon = workbook.create_sheet("TOON")
    toon.sheet_state = "hidden"
    toon.append(["Demonstration participant", "Standard TOON (one record per cell)"])
    for profile in profiles:
        toon.append([profile.demo_id, encode([profile]).rstrip("\n")])
    definitions = workbook.create_sheet("Definitions")
    for row in (
        ("Label", "What it means"),
        ("More Charts tab",
         "Office, review and support-area charts with their numbers beside them."),
        ("Staff may want to look here first",
         "People in the 30+ day band with a critical barrier, longest wait first. A sorting aid, "
         "not a referral or eligibility decision."),
        ("Fictional demonstration", "All people and situations are invented. Not a live system."),
        ("SharePoint", "Workbook delivery is simulated. No cloud account is connected."),
        ("Days since contact or assessment", "Calendar days; use assessment if contact is absent."),
        *((ALERT_LABELS[alert], ALERT_MEANINGS[alert]) for alert in Alert),
        *((STATE_LABELS[state], STATE_MEANINGS[state]) for state in State),
        ("Most pressing recorded need",
         "Critical, needs support, not assessed, partly addressed, then resolved; not a score."),
        ("Staff review status", "Copied from the source; does not authorize a referral."),
        ("Who decides?", "Qualified staff interpret needs and approve referrals."),
        ("Technical details", "Hidden TOON and Provenance sheets are for technical review only."),
    ):
        definitions.append(row)
    definitions.sheet_view.showGridLines = False
    definitions.sheet_view.zoomScale = 95
    definitions.row_dimensions[1].height = 28
    definitions.column_dimensions["A"].width = 34
    definitions.column_dimensions["B"].width = 100
    for cell in definitions[1]:
        cell.font = Font(name="Aptos", size=11, bold=True, color=white)
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for row in definitions.iter_rows(min_row=2):
        definitions.row_dimensions[row[0].row].height = 32
        for cell in row:
            cell.font = Font(name="Aptos", size=10, color=ink)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if cell.row % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F4F7F9")

    add_more_charts(workbook, profiles)
    provenance = workbook.create_sheet("Provenance")
    provenance.sheet_state = "hidden"
    provenance.append(["Source SHA-256", source_hash])
    provenance.append(["As of", profiles[0].as_of.isoformat()])
    provenance.append(["Refresh", "Static snapshot; rerun ETL to refresh"])
    provenance.append(["Record count", len(profiles)])
    provenance.sheet_view.showGridLines = False
    for sheet in workbook:
        sheet.sheet_view.showGridLines = False
    return workbook


HTML_ALERT_COLORS = ("#52d19c", "#f5b942", "#ff7b7b")
HTML_REVIEW_COLORS = ("#f5b942", "#52d19c")
HTML_STATE_COLORS = ("#ff7b7b", "#f5b942", "#7ab8ff", "#52d19c", "#a8b3c2")


def chart_figure(
    title: str, question: str, rows: list[tuple[str, list[int]]], series: list[str],
    colors: tuple[str, ...], first_column: str, unit: str = "people",
) -> str:
    key = legend(series, colors) if len(series) > 1 else ""
    return (
        f'<figure class="chart"><h3>{escape(title)}</h3><p>{escape(question)}</p>{key}'
        f'{stacked_bars(rows, series, colors, title, unit)}'
        '<details><summary>Show these numbers as a table</summary>'
        f'<div class="scroll">{number_table(rows, first_column, series)}</div></details>'
        '</figure>'
    )


def at_a_glance(profiles: list[Profile]) -> str:
    waiting = sum(p.alert == Alert.RED for p in profiles)
    first = len(review_first(profiles))
    pending = sum(p.review == Review.PENDING for p in profiles)
    areas, count = most_common_areas(profiles)
    return (
        '<section class="glance" aria-labelledby="glance-title">'
        '<h2 id="glance-title">At a glance</h2><ul>'
        f"<li><strong>{waiting}</strong> of {len(profiles)} people are in the 30+ day band.</li>"
        f"<li><strong>{first}</strong> of them also have a critical barrier recorded.</li>"
        f"<li><strong>{pending}</strong> people are still awaiting staff review.</li>"
        f"<li>Most often marked critical or needing support: <strong>{' and '.join(areas)}"
        f"</strong> ({count} people each).</li></ul></section>"
    )


def chart_section(profiles: list[Profile]) -> str:
    first = review_first(profiles)
    if first:
        body = "".join(
            f"<tr><th>{p.demo_id}</th><td>{OFFICE_LABELS[p.office]}</td><td>{p.idle_days}</td>"
            f"<td>{barrier_summary(p)}</td><td>{REVIEW_LABELS[p.review]}</td></tr>"
            for p in first
        )
        priority = (
            '<div class="scroll"><table id="review-first"><thead><tr>'
            "<th>Demonstration participant</th><th>Demonstration office</th>"
            "<th>Days since contact or assessment</th><th>Most pressing recorded need</th>"
            f"<th>Staff review status</th></tr></thead><tbody>{body}</tbody></table></div>"
        )
    else:
        priority = "<p>No one in this report is in the 30+ day band with a critical barrier.</p>"
    return (
        '<section aria-labelledby="charts-title"><h2 id="charts-title">Where staff attention '
        "may be needed</h2>"
        "<p>These charts count people across the whole report. The filters further down "
        "change only the participant list. Every number counts people, not referrals.</p>"
        '<div class="charts">'
        + chart_figure(
            "Which offices have people waiting longest?",
            "Each bar is one office. Colors show days since recorded contact, "
            "or since assessment if no contact is recorded.",
            office_follow_up(profiles), ALERT_SERIES, HTML_ALERT_COLORS, "Demonstration office",
        )
        + chart_figure(
            "How far along is staff review?",
            "\u201cAwaiting staff review\u201d means no staff review is recorded yet.",
            office_review(profiles), REVIEW_SERIES, HTML_REVIEW_COLORS, "Demonstration office",
        )
        + chart_figure(
            "What kinds of support are recorded?",
            "Each bar is one area of support. Colors show the recorded status "
            "for everyone in the report.",
            support_by_area(profiles), STATE_SERIES, HTML_STATE_COLORS, "Area of support",
        )
        + chart_figure(
            "How many areas of support does each person have?",
            "Counts areas marked critical or needing support. "
            "People with several areas may benefit from coordinated follow-up.",
            people_by_area_count(profiles), ["People"], ("#7ab8ff",), "Areas marked", "people",
        )
        + "</div>"
        '<h2>Staff may want to look here first</h2>'
        "<p>This list only sorts people who are in the 30+ day band <em>and</em> have a "
        "critical barrier recorded, longest wait first. It is a sorting aid. Qualified "
        "staff decide who to contact and what support to offer.</p>"
        f"{priority}</section>"
    )


def html_dashboard(profiles: list[Profile], source_hash: str) -> str:
    cards = "".join(
        f'<article><h2>{ALERT_LABELS[alert]}</h2><strong id="count-{alert.value}">'
        f'{sum(p.alert == alert for p in profiles)}</strong> people'
        f'<p>{ALERT_MEANINGS[alert]}</p></article>'
        for alert in Alert
    )
    rows = []
    for profile in profiles:
        contact = display_date(profile.last_contact_date)
        if profile.last_contact_date is None:
            contact += "; counted from assessment"
        cells = (
            profile.demo_id, OFFICE_LABELS[profile.office],
            display_date(profile.assessment_date), contact, str(profile.idle_days),
            ALERT_LABELS[profile.alert], barrier_summary(profile), REVIEW_LABELS[profile.review],
        )
        td = "".join(f"<td>{escape(value)}</td>" for value in cells)
        inspector = escape(encode([profile]).rstrip("\n"))
        support = "".join(
            f"<dt>{label}</dt><dd>{STATE_LABELS[getattr(profile, field)]}</dd>"
            for field, label in DOMAIN_LABELS.items()
        )
        rows.append(
            f'<tr data-office="{profile.office.value}" data-alert="{profile.alert.value}">'
            f'{td}<td><details><summary>View support needs</summary><dl>{support}</dl>'
            '<p>Qualified staff decide next steps. No automatic referral.</p>'
            '<details class="technical"><summary>Technical data (for IT review)</summary>'
            f'<p>Standard TOON syntax; not an approved federal interface.</p><pre>{inspector}</pre>'
            '</details></details></td></tr>'
        )
    options = "".join(
        f'<option value="{office}">{OFFICE_LABELS[Office(office)]}</option>'
        for office in sorted({p.office.value for p in profiles})
    )
    alert_options = "".join(
        f'<option value="{alert.value}">{ALERT_LABELS[alert]}</option>' for alert in Alert
    )
    barrier_rows = "".join(
        f"<tr><th>{DOMAIN_LABELS[domain]}</th>"
        + "".join(
            f"<td>{sum(getattr(p, domain) == state for p in profiles)}</td>" for state in State
        ) + "</tr>" for domain in DOMAINS
    )
    glossary = "".join(
        f"<dt>{STATE_LABELS[state]}</dt><dd>{STATE_MEANINGS[state]}</dd>" for state in State
    )
    contact_counts = Counter(profile.alert for profile in profiles)
    overview = (
        f"{len(profiles)} fictional people are in this report. "
        f"{contact_counts[Alert.RED]} are in the 30+ day band "
        "(since contact, or assessment if no contact was recorded); "
        f"{sum(p.review == Review.PENDING for p in profiles)} are awaiting staff review."
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy"
content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';
connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'">
<title>Veteran follow-up and support needs | Fictional demonstration</title>
<style>
:root{{color-scheme:dark;font-family:Segoe UI,Arial,sans-serif;background:#06182c;color:#f8fafc}}
body{{max-width:1400px;margin:auto;padding:28px}} h1,h2{{color:#52d19c}}
.notice{{padding:16px;border:2px solid #52d19c;background:#0c2340}}
.cards{{display:flex;gap:18px;margin:20px 0;flex-wrap:wrap}}
article{{background:#122d52;border:1px solid #7496d2;padding:18px;min-width:170px}}
article strong{{font-size:36px}} label{{display:inline-block;margin:12px 20px 12px 0}}
article{{flex:1;min-width:220px}} article h2{{font-size:20px}}
.guide{{background:#122d52;padding:20px;margin:20px 0;line-height:1.6}}
.files{{border:2px solid #52d19c;padding:20px;background:#122d52;margin:20px 0}}
.files a{{color:#8ce9bf;font-weight:bold}} .files code{{overflow-wrap:anywhere}}
.files li{{margin:14px 0}} .files small{{display:block;margin-top:4px}}
dt{{font-weight:bold;margin-top:12px}} dd{{margin:4px 0 12px}}
.technical{{margin-top:20px;color:#cbd5e1}} .intro{{font-size:20px;line-height:1.6}}
select,input{{padding:10px;background:#122d52;color:white;border:1px solid #7496d2}}
table{{border-collapse:collapse;width:100%;margin:16px 0;background:#0c2340}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #345988;vertical-align:top}}
#roster{{min-width:1350px}} #barriers{{min-width:850px}} td{{min-width:100px}}
tr:nth-child(even){{background:#122d52}} pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
summary{{cursor:pointer;color:#52d19c}} .scroll{{overflow-x:auto}}
.glance{{background:#122d52;border-left:6px solid #52d19c;padding:8px 24px;margin:20px 0}}
.glance li{{font-size:20px;line-height:1.7}} .glance strong{{font-size:26px;color:#8ce9bf}}
.charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:28px;
margin:24px 0}} .chart{{margin:0;background:#122d52;border:1px solid #7496d2;padding:22px}}
.chart h3{{margin:0 0 8px;font-size:22px;color:#f8fafc}} .chart p{{margin:0 0 14px;
font-size:17px;line-height:1.5;color:#cbd5e1}} .chart svg{{width:100%;height:auto;
display:block;margin:12px 0}} .legend{{list-style:none;display:flex;flex-wrap:wrap;gap:8px 22px;
padding:0;margin:0 0 6px;font-size:16px}} .swatch{{display:inline-block;width:16px;
height:16px;margin-right:8px;vertical-align:-2px;border-radius:3px}}
.chart table{{margin:8px 0;min-width:0}} .chart details{{margin-top:8px}}
#review-first{{min-width:900px}}
@media (max-width:640px){{.charts{{grid-template-columns:1fr}}}}
[hidden]{{display:none}} footer{{color:#cbd5e1;overflow-wrap:anywhere}}
</style></head><body>
<p>Alabama Department of Workforce discussion prototype - not an approved agency system</p>
<h1>Veteran follow-up and support needs</h1>
<p class="notice"><strong>FICTIONAL DEMONSTRATION - NO REAL PERSONAL DATA</strong><br>
Report date: {display_date(profiles[0].as_of)}. SharePoint delivery is simulated.
No live connection. Nothing is sent to staff, partners or an AI service.</p>
<section class="files" aria-labelledby="demo-files-title">
<h2 id="demo-files-title">Demo files - open or download here</h2>
<p>These are real generated files, not Python code. Each link belongs to the report
you are viewing.</p>
<ul>
<li><a href="dashboard.xlsx" download>Download the Excel report</a>
 - charts and the readable participant list.
<small>File: <code data-demo-file="dashboard.xlsx">dashboard.xlsx</code></small></li>
<li><a href="reviewed_profiles.xlsx" download>Download the synthetic review input</a>
 - fictional profile fields supplied for this demonstration, not extracted from case notes.
<small>File: <code data-demo-file="reviewed_profiles.xlsx">
reviewed_profiles.xlsx</code></small></li>
<li><a href="profiles.toon" download>Download the TOON data file</a>
 - the compact machine-readable version for technical review.
<small>File: <code data-demo-file="profiles.toon">profiles.toon</code></small></li>
<li><a href="profiles.json" download>Download the readable structured data</a>
 - the same calculated records in JSON format.
<small>File: <code data-demo-file="profiles.json">profiles.json</code></small></li>
</ul>
<p><strong>Where are these on disk?</strong> They are in the same folder as this page:
<code id="demo-folder">the report's batch folder</code>.
For the standard demo, start in <code>temp/management-demo/</code> in the VS Code
file explorer, then open <code>batches/</code> and the report folder shown here.
The source file is a saved copy, not a live SharePoint link.</p>
<p>Your browser may download Excel instead of opening it. Look in your browser's
Downloads list, then open the downloaded workbook in Excel.</p>
</section>
<p class="intro">{overview}</p>
{at_a_glance(profiles)}
{chart_section(profiles)}
<div class="guide"><strong>What this report helps you understand</strong>
<ul><li>Who may need follow-up based on time since contact or assessment?</li>
<li>What transportation, housing, health or legal needs are recorded?</li>
<li>Which records are still awaiting staff review?</li></ul>
<strong>How it works:</strong> Receive an Excel workbook &rarr; check its contents &rarr;
calculate follow-up information &rarr; create this report and an Excel dashboard.</div>
<h2>How long since recorded contact, or assessment if none?</h2>
<p>These cards count the people shown in the list below. Changing a filter updates them.</p>
<section class="cards">{cards}</section>
<h2>People who may need follow-up</h2>
<p>Every participant number is made up. Open &quot;View support needs&quot; for a
plain-language breakdown. Scroll the table sideways on smaller screens.</p>
<label for="office">Demonstration office</label><select id="office">
<option value="">All demonstration offices</option>{options}</select>
<label for="alert">Follow-up status</label><select id="alert">
<option value="">All follow-up statuses</option>{alert_options}</select>
<label for="search">Find a demonstration participant</label>
<input id="search" type="search" placeholder="Example: DEMO-0005">
<p id="count" aria-live="polite">Showing {len(profiles)} of {len(profiles)} people</p>
<div class="scroll"><table id="roster"><thead><tr>
<th>Demonstration participant</th><th>Demonstration office</th><th>Assessment date</th>
<th>Last recorded contact</th><th>Days since contact or assessment</th>
<th>Follow-up status</th><th>Most pressing recorded need</th>
<th>Staff review status</th><th>Support details</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p id="empty" hidden>No people match these filters. Clear the search or choose all statuses.</p>
<h2>What support needs are recorded across all {len(profiles)} people?</h2>
<p>This table always covers the entire report, even when you filter the list above.
Each number counts people, not referrals. A person appears once in each support area.</p>
<div class="scroll"><table id="barriers"><thead><tr><th>Area of support</th>
{''.join(f'<th>{label}</th>' for label in STATE_LABELS.values())}
</tr></thead><tbody>{barrier_rows}</tbody></table></div>
<div class="guide"><h2>What do the support descriptions mean?</h2><dl>{glossary}</dl></div>
<h2>Important limits</h2>
<ul><li>The example follow-up thresholds are not approved agency policy.</li>
<li>If no contact is recorded, days are counted from assessment instead.</li>
<li>Recent contact does not mean support needs are resolved.</li>
<li>&quot;Most pressing recorded need&quot; summarizes the supplied support descriptions;
it is not a referral or eligibility score.</li>
<li>Staff review information is copied from the workbook, not independently verified.</li>
<li>Qualified staff interpret needs and approve referrals. This report does not make decisions.</li>
<li>All support descriptions are invented input, not AI findings.</li></ul>
<details class="technical"><summary>Technical processing and verification (for IT review)</summary>
<p>Standard TOON serialization; the demo profile is not an approved federal interface.
The synthetic review-profile workbook and calculated records are checked before this
report is created.
The profile fields are not extracted or classified from native case notes.</p>
<p>Source file fingerprint (SHA-256): {source_hash}</p></details>
<footer><p>This is a saved report, not a live system. Rerun processing to update it.
Public review does not authorize production use.</p></footer>
<script>
const folderPath = decodeURIComponent(new URL('.', location.href).pathname);
document.getElementById('demo-folder').textContent = folderPath;
for (const label of document.querySelectorAll('[data-demo-file]')) {{
  label.textContent = folderPath + label.dataset.demoFile;
}}
const office = document.getElementById('office');
const alertFilter = document.getElementById('alert');
const search = document.getElementById('search');
const rows = [...document.querySelectorAll('#roster tbody tr')];
function filterRows() {{
  const counts = {{GREEN:0, YELLOW:0, RED:0}};
  let visible = 0;
  for (const row of rows) {{
    row.hidden = !!((office.value && row.dataset.office !== office.value) ||
      (alertFilter.value && row.dataset.alert !== alertFilter.value) ||
      !row.cells[0].textContent.toLowerCase().includes(search.value.trim().toLowerCase()));
    if (!row.hidden) {{ visible++; counts[row.dataset.alert]++; }}
  }}
  document.getElementById('count').textContent = `Showing ${{visible}} of ${{rows.length}} people`;
  document.getElementById('empty').hidden = visible !== 0;
  for (const key of Object.keys(counts)) {{
    document.getElementById('count-' + key).textContent = counts[key];
  }}
}}
for (const control of [office, alertFilter, search]) {{
  control.addEventListener('input', filterRows);
}}
</script></body></html>
"""
