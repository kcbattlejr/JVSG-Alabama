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
from openpyxl.styles import Font, PatternFill
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
PRESENTATION_VERSION = "plain-language-files-1"
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
    workbook = Workbook()
    dashboard = workbook.create_sheet("Dashboard", 0)
    workbook.remove(workbook["Sheet"])
    dashboard.append(["Veteran follow-up and support needs | Fictional demonstration"])
    dashboard.append(["Offline snapshot - not connected to SharePoint; no live case decisions"])
    dashboard.append(["Report date", display_date(profiles[0].as_of)])
    dashboard.append(["People in this demonstration", len(profiles)])
    dashboard.append(["Awaiting staff review", sum(p.review == Review.PENDING for p in profiles)])
    dashboard.append([])
    dashboard.append(["Time since last contact", "Number of people"])
    counts = Counter(p.alert for p in profiles)
    for alert in Alert:
        dashboard.append([ALERT_LABELS[alert], counts[alert]])
    chart = BarChart()
    chart.title = "How long since the last contact?"
    chart.y_axis.title = "Number of people"
    chart.add_data(Reference(dashboard, min_col=2, min_row=7, max_row=10), titles_from_data=True)
    chart.set_categories(Reference(dashboard, min_col=1, min_row=8, max_row=10))
    dashboard.add_chart(chart, "H3")
    dashboard.append([])
    dashboard.append(["Area of support", *STATE_LABELS.values()])
    for domain in DOMAINS:
        dashboard.append([
            DOMAIN_LABELS[domain],
            *(sum(getattr(p, domain) == state for p in profiles) for state in State),
        ])
    barrier_chart = BarChart()
    barrier_chart.type = "bar"
    barrier_chart.grouping = "stacked"
    barrier_chart.overlap = 100
    barrier_chart.title = "What support needs are recorded?"
    barrier_chart.add_data(
        Reference(dashboard, min_col=2, max_col=6, min_row=12, max_row=16),
        titles_from_data=True,
    )
    barrier_chart.set_categories(Reference(dashboard, min_col=1, min_row=13, max_row=16))
    dashboard.add_chart(barrier_chart, "H20")
    dashboard.append([])
    dashboard.append(["How to read this report", "All people and situations are fictional."])
    for alert in Alert:
        dashboard.append([ALERT_LABELS[alert], ALERT_MEANINGS[alert]])
    dashboard.append([
        "When no contact is recorded",
        "Days are counted from assessment instead. These thresholds are demo assumptions.",
    ])
    dashboard.append([
        "Contact is not a service outcome",
        "Recent contact does not mean a person's support needs are resolved.",
    ])
    dashboard.append([
        "Who makes decisions?",
        "Qualified staff interpret needs and approve referrals. Nothing is sent automatically.",
    ])

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
    watchlist.freeze_panes = "C2"
    table = Table(displayName="SyntheticWatchlist", ref=f"A1:N{len(profiles) + 1}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    watchlist.add_table(table)
    colors = {
        ALERT_LABELS[Alert.GREEN]: "D3F9D8",
        ALERT_LABELS[Alert.YELLOW]: "FFF3BF",
        ALERT_LABELS[Alert.RED]: "FFE3E3",
    }
    for row in watchlist.iter_rows(min_row=2):
        row[11].fill = PatternFill("solid", fgColor=colors[str(row[11].value)])
        for index in (2, 3, 9):
            row[index].number_format = "mmm d, yyyy"
        if row[3].value is None:
            watchlist.cell(row[3].row, 4, "No contact recorded; counted from assessment")

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
    provenance = workbook.create_sheet("Provenance")
    provenance.sheet_state = "hidden"
    provenance.append(["Source SHA-256", source_hash])
    provenance.append(["As of", profiles[0].as_of.isoformat()])
    provenance.append(["Refresh", "Static snapshot; rerun ETL to refresh"])
    provenance.append(["Record count", len(profiles)])
    for sheet in workbook:
        sheet.sheet_view.showGridLines = False
        for cell in sheet[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="122D52")
        for index, column in enumerate(sheet.columns, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = min(
                75, max(16, max(len(str(cell.value or "")) for cell in column) + 2),
            )
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
<li><a href="source.xlsx" download>Download the source Excel workbook</a>
 - the fictional input used to create this report.
<small>File: <code data-demo-file="source.xlsx">source.xlsx</code></small></li>
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
The source workbook and calculated records are checked before this report is created.</p>
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
