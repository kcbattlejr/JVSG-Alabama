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
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.marker import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

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
from jvsg_triage.toon.demo import encode

FIXED_TIME = datetime(2026, 1, 1)
PRESENTATION_VERSION = "paired-report-review-excel-4"
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
    state_colors = {
        State.CRT: red,
        State.ACT: amber,
        State.MIT: blue,
        State.RES: green,
        State.UNK: "8999A6",
    }

    workbook = Workbook()
    dashboard = workbook.create_sheet("Dashboard", 0)
    workbook.remove(workbook["Sheet"])
    dashboard.sheet_view.showGridLines = False
    dashboard.sheet_view.zoomScale = 85
    for column in range(1, 13):
        dashboard.column_dimensions[get_column_letter(column)].width = 13

    dashboard.merge_cells("A1:L1")
    dashboard["A1"] = "Veteran follow-up and support needs"
    dashboard["A1"].font = Font(name="Aptos Display", size=22, bold=True, color=white)
    dashboard["A1"].fill = PatternFill("solid", fgColor=navy)
    dashboard["A1"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[1].height = 42

    dashboard.merge_cells("A2:L2")
    dashboard["A2"] = (
        "SYNTHETIC DEMONSTRATION  |  Offline snapshot  |  No live SharePoint connection"
    )
    dashboard["A2"].font = Font(name="Aptos", size=10, bold=True, color=muted)
    dashboard["A2"].fill = PatternFill("solid", fgColor=pale)
    dashboard["A2"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[2].height = 24

    counts = Counter(profile.alert for profile in profiles)
    cards = (
        ("A4:C4", "A5:C6", "PEOPLE IN SNAPSHOT", len(profiles), navy),
        ("D4:F4", "D5:F6", ALERT_LABELS[Alert.GREEN].upper(), counts[Alert.GREEN], green),
        ("G4:I4", "G5:I6", ALERT_LABELS[Alert.YELLOW].upper(), counts[Alert.YELLOW], amber),
        ("J4:L4", "J5:L6", ALERT_LABELS[Alert.RED].upper(), counts[Alert.RED], red),
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
    dashboard.merge_cells("A7:L7")
    dashboard["A7"] = (
        f"Staff review status: {pending} awaiting review  |  {reviewed} reviewed"
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
    for alert in Alert:
        row = 2 + list(Alert).index(alert)
        watchlist.cell(row, 16, ALERT_LABELS[alert])
        watchlist.cell(row, 17, counts[alert])
    watchlist["P6"] = "Area of support"
    for column, state in enumerate(State, start=17):
        watchlist.cell(6, column, STATE_LABELS[state])
    for row, domain in enumerate(DOMAINS, start=7):
        watchlist.cell(row, 16, DOMAIN_LABELS[domain])
        for column, state in enumerate(State, start=17):
            watchlist.cell(
                row, column,
                sum(getattr(profile, domain) == state for profile in profiles),
            )
    for column in range(16, 22):
        watchlist.column_dimensions[get_column_letter(column)].hidden = True

    chart = BarChart()
    chart.type = "bar"
    chart.style = 10
    chart.title = "Time since last contact"
    chart.y_axis.title = "Contact status"
    chart.x_axis.title = "Number of people"
    chart.add_data(Reference(watchlist, min_col=17, min_row=1, max_row=4), titles_from_data=True)
    chart.set_categories(Reference(watchlist, min_col=16, min_row=2, max_row=4))
    chart.series[0].data_points = [
        DataPoint(idx=index, spPr=GraphicalProperties(solidFill=color))
        for index, color in enumerate((green, amber, red))
    ]
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showVal = True
    chart.legend = None
    chart.width = 14
    chart.height = 8
    chart.visible_cells_only = False
    dashboard.add_chart(chart, "A9")

    barrier_chart = BarChart()
    barrier_chart.type = "bar"
    barrier_chart.grouping = "stacked"
    barrier_chart.overlap = 100
    barrier_chart.style = 10
    barrier_chart.title = "Recorded support needs by area"
    barrier_chart.x_axis.title = "Number of people"
    barrier_chart.y_axis.title = "Area of support"
    barrier_chart.add_data(
        Reference(watchlist, min_col=17, max_col=21, min_row=6, max_row=10),
        titles_from_data=True,
    )
    barrier_chart.set_categories(Reference(watchlist, min_col=16, min_row=7, max_row=10))
    for series, state in zip(barrier_chart.series, State, strict=True):
        series.graphicalProperties.solidFill = state_colors[state]
        series.graphicalProperties.line.solidFill = state_colors[state]
    barrier_chart.legend.position = "b"
    barrier_chart.width = 16
    barrier_chart.height = 8
    barrier_chart.visible_cells_only = False
    dashboard.add_chart(barrier_chart, "G9")

    dashboard.merge_cells("A25:L25")
    dashboard["A25"] = "HOW TO READ THIS SNAPSHOT"
    dashboard["A25"].font = Font(name="Aptos", size=11, bold=True, color=white)
    dashboard["A25"].fill = PatternFill("solid", fgColor=navy)
    dashboard["A25"].alignment = Alignment(vertical="center", indent=1)
    dashboard.row_dimensions[25].height = 24
    for alert in Alert:
        row = dashboard.max_row + 1
        dashboard.merge_cells(start_row=row, start_column=2, end_row=row, end_column=12)
        dashboard.cell(row, 1, ALERT_LABELS[alert])
        dashboard.cell(row, 2, ALERT_MEANINGS[alert])
    notes = (
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
    for label, meaning in notes:
        row = dashboard.max_row + 1
        dashboard.merge_cells(start_row=row, start_column=2, end_row=row, end_column=12)
        dashboard.cell(row, 1, label)
        dashboard.cell(row, 2, meaning)
    for row in range(26, dashboard.max_row + 1):
        dashboard.cell(row, 1).font = Font(name="Aptos", size=10, bold=True, color=blue)
        dashboard.cell(row, 2).font = Font(name="Aptos", size=10, color=ink)
        dashboard.cell(row, 1).alignment = Alignment(vertical="top", wrap_text=True)
        dashboard.cell(row, 2).alignment = Alignment(vertical="top", wrap_text=True)
        dashboard.row_dimensions[row].height = 30
        for cell in dashboard[row][:12]:
            cell.fill = PatternFill("solid", fgColor="F4F7F9" if row % 2 == 0 else white)
            cell.border = Border(bottom=Side(style="hair", color=line))
    dashboard.freeze_panes = "A4"
    dashboard.print_area = f"A1:L{dashboard.max_row}"
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
    for row in watchlist.iter_rows(min_row=2):
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
    toon.append(["Demonstration participant", "Technical encoding (custom TOON demo format)"])
    for profile in profiles:
        toon.append([profile.demo_id, encode(profile)])
    definitions = workbook.create_sheet("Definitions")
    for row in (
        ("Label", "What it means"),
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
        inspector = escape(encode(profile))
        support = "".join(
            f"<dt>{label}</dt><dd>{STATE_LABELS[getattr(profile, field)]}</dd>"
            for field, label in DOMAIN_LABELS.items()
        )
        rows.append(
            f'<tr data-office="{profile.office.value}" data-alert="{profile.alert.value}">'
            f'{td}<td><details><summary>View support needs</summary><dl>{support}</dl>'
            '<p>Qualified staff decide next steps. No automatic referral.</p>'
            '<details class="technical"><summary>Technical data (for IT review)</summary>'
            f'<p>Custom TOON demo format; not an approved interface.</p><pre>{inspector}</pre>'
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
        f"{contact_counts[Alert.RED]} have gone 30 or more days without recorded contact; "
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
<div class="guide"><strong>What this report helps you understand</strong>
<ul><li>Who may need follow-up because time has passed since the last contact?</li>
<li>What transportation, housing, health or legal needs are recorded?</li>
<li>Which records are still awaiting staff review?</li></ul>
<strong>How it works:</strong> Receive an Excel workbook &rarr; check its contents &rarr;
calculate follow-up information &rarr; create this report and an Excel dashboard.</div>
<h2>How long since the last recorded contact?</h2>
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
<p>Custom TOON demo-1 serialization, not standard TOON or an approved federal interface.
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
