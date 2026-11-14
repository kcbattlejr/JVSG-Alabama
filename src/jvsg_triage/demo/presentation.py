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

from jvsg_triage.demo.models import DOMAINS, Alert, Profile, Review, State
from jvsg_triage.toon.demo import encode

FIXED_TIME = datetime(2026, 1, 1)
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
    for columns, choices in (
        (("E", "F", "G", "H"), ",".join(state.value for state in State)),
        (("I",), "Pending,Reviewed"),
        (("B",), "DEMO-NORTH,DEMO-CENTRAL,DEMO-SOUTH"),
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
    dashboard.append(["JVSG | SYNTHETIC MANAGEMENT DEMO"])
    dashboard.append(["Offline snapshot - not connected to SharePoint; no live case decisions"])
    dashboard.append(["As of", profiles[0].as_of.isoformat()])
    dashboard.append(["Participants", len(profiles)])
    dashboard.append(["Pending human review", sum(p.review == Review.PENDING for p in profiles)])
    dashboard.append([])
    dashboard.append(["Aging alert", "Participants"])
    counts = Counter(p.alert for p in profiles)
    for alert in Alert:
        dashboard.append([alert.value, counts[alert]])
    chart = BarChart()
    chart.title = "Follow-up aging (invented data)"
    chart.y_axis.title = "Participants"
    chart.add_data(Reference(dashboard, min_col=2, min_row=7, max_row=10), titles_from_data=True)
    chart.set_categories(Reference(dashboard, min_col=1, min_row=8, max_row=10))
    dashboard.add_chart(chart, "D4")
    dashboard.append([])
    dashboard.append(["Domain", *(state.value for state in State)])
    for domain in DOMAINS:
        dashboard.append([
            domain, *(sum(getattr(p, domain) == state for p in profiles) for state in State),
        ])
    barrier_chart = BarChart()
    barrier_chart.type = "bar"
    barrier_chart.grouping = "stacked"
    barrier_chart.overlap = 100
    barrier_chart.title = "Barrier states - simulated, not inferred"
    barrier_chart.add_data(
        Reference(dashboard, min_col=2, max_col=6, min_row=12, max_row=16),
        titles_from_data=True,
    )
    barrier_chart.set_categories(Reference(dashboard, min_col=1, min_row=13, max_row=16))
    dashboard.add_chart(barrier_chart, "D20")

    watchlist = workbook.create_sheet("Watchlist")
    watchlist.append([*PROFILE_FIELDS, "priority", "next_action"])
    for profile in profiles:
        values = profile.model_dump(mode="json")
        watchlist.append([
            *(values[field] for field in PROFILE_FIELDS), profile.priority.value,
            "Qualified staff review; no automatic referral",
        ])
    watchlist.freeze_panes = "C2"
    table = Table(displayName="SyntheticWatchlist", ref=f"A1:N{len(profiles) + 1}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    watchlist.add_table(table)
    colors = {"GREEN": "D3F9D8", "YELLOW": "FFF3BF", "RED": "FFE3E3"}
    for row in watchlist.iter_rows(min_row=2):
        row[11].fill = PatternFill("solid", fgColor=colors[str(row[11].value)])

    toon = workbook.create_sheet("TOON")
    toon.append(["demo_id", "@TOON demo-1 (lossless demo dialect)"])
    for profile in profiles:
        toon.append([profile.demo_id, encode(profile)])
    definitions = workbook.create_sheet("Definitions")
    for row in (
        ("Boundary", "Synthetic-only, offline, not production-approved"),
        ("SharePoint", "Simulated file drop; no Graph calls, authentication or write-back"),
        ("Aging", "Calendar days since last contact, or assessment when no contact exists"),
        ("Thresholds", "Demo assumptions: GREEN <15; YELLOW 15-29; RED >=30"),
        ("Domains", "TRN transit; HSG housing; MED health; LEG legal"),
        ("States", "CRT critical; ACT active; MIT mitigated; RES resolved; UNK unknown"),
        ("Priority", "First present: CRT, ACT, UNK, MIT, RES; not a referral score"),
        ("Review", "Source review values preserved; Reviewed is not referral authorization"),
        ("Interpretation", "Barrier states are invented input, not AI classification"),
        ("Privacy", "No names, raw SIDs, contacts or narrative text allowed by demo schema"),
        ("TOON", "Versioned custom demo dialect, not standard TOON or an approved VOMA contract"),
        ("Metrics", "Invented distribution; no real-world accuracy or compression target claim"),
    ):
        definitions.append(row)
    provenance = workbook.create_sheet("Provenance")
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
        f'<article><h2>{alert.value}</h2><strong id="count-{alert.value}">'
        f'{sum(p.alert == alert for p in profiles)}</strong></article>'
        for alert in Alert
    )
    rows = []
    for profile in profiles:
        values = profile.model_dump(mode="json")
        cells = (
            profile.demo_id, profile.office.value, str(values["assessment_date"]),
            str(values["last_contact_date"] or "No contact"), str(profile.idle_days),
            profile.alert.value, profile.priority.value, profile.review.value,
        )
        td = "".join(f"<td>{escape(value)}</td>" for value in cells)
        inspector = escape(encode(profile))
        rows.append(
            f'<tr data-office="{profile.office.value}" data-alert="{profile.alert.value}">'
            f'{td}<td><details><summary>Inspect TOON</summary><pre>{inspector}</pre>'
            '<p>Qualified human review required. No automated referral.</p></details></td></tr>'
        )
    options = "".join(
        f'<option>{escape(office)}</option>'
        for office in sorted({p.office.value for p in profiles})
    )
    barrier_rows = "".join(
        f"<tr><th>{domain}</th>"
        + "".join(
            f"<td>{sum(getattr(p, domain) == state for p in profiles)}</td>" for state in State
        ) + "</tr>" for domain in DOMAINS
    )
    barrier_bars = ""
    for domain in DOMAINS:
        segments = "".join(
            f'<span class="segment {state.value}" '
            f'style="width:{100 * count / len(profiles):.4f}%" '
            f'title="{domain} {state.value}: {count}">{state.value} {count}</span>'
            for state in State
            if (count := sum(getattr(p, domain) == state for p in profiles))
        )
        barrier_bars += f'<p><strong>{domain}</strong></p><div class="bar">{segments}</div>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy"
content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';
connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'">
<title>JVSG Synthetic Watchlist Demo</title>
<style>
:root{{color-scheme:dark;font-family:Segoe UI,Arial,sans-serif;background:#06182c;color:#f8fafc}}
body{{max-width:1400px;margin:auto;padding:28px}} h1,h2{{color:#52d19c}}
.notice{{padding:16px;border:2px solid #52d19c;background:#0c2340}}
.cards{{display:flex;gap:18px;margin:20px 0;flex-wrap:wrap}}
article{{background:#122d52;border:1px solid #7496d2;padding:18px;min-width:170px}}
article strong{{font-size:36px}} label{{display:inline-block;margin:12px 20px 12px 0}}
.bar{{display:flex;min-height:36px;background:#122d52;border:1px solid #7496d2}}
.segment{{padding:8px 0;text-align:center;color:#06182c;font-weight:bold;overflow:hidden}}
.CRT{{background:#ff8787}} .ACT{{background:#ffd43b}} .MIT{{background:#69db7c}}
.RES{{background:#91a7ff}} .UNK{{background:#ced4da}}
select,input{{padding:10px;background:#122d52;color:white;border:1px solid #7496d2}}
table{{border-collapse:collapse;width:100%;margin:16px 0;background:#0c2340}}
th,td{{padding:12px;text-align:left;border-bottom:1px solid #345988}}
tr:nth-child(even){{background:#122d52}} pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
summary{{cursor:pointer;color:#52d19c}} .scroll{{overflow-x:auto}}
[hidden]{{display:none}} footer{{color:#cbd5e1;overflow-wrap:anywhere}}
</style></head><body>
<p>ADOW / JVSG discussion prototype - no official branding or endorsement implied</p>
<h1>M365 Excel Watchlist / Managerial Barrier Removal</h1>
<p class="notice"><strong>SYNTHETIC DATA ONLY | OFFLINE SNAPSHOT</strong><br>
As of {profiles[0].as_of.isoformat()}. SharePoint delivery is simulated.
No live connection, model inference, notifications or automatic referral.</p>
<p>Workbook intake &rarr; validated ETL &rarr; @TOON &rarr; Excel / HTML snapshot</p>
<section class="cards">{cards}</section>
<h2>Active demonstration roster</h2>
<label>Office <select id="office"><option value="">All offices</option>{options}</select></label>
<label>Aging <select id="alert"><option value="">All alerts</option>
<option>GREEN</option><option>YELLOW</option><option>RED</option></select></label>
<label>Demo ID <input id="search" type="search" placeholder="DEMO-0001"></label>
<p id="count" aria-live="polite">Showing {len(profiles)} of {len(profiles)}</p>
<div class="scroll"><table id="roster"><thead><tr>
<th>Demo ID</th><th>Office</th><th>Assessment</th><th>Last contact</th>
<th>Idle days</th><th>Aging</th><th>Priority</th><th>Human review</th><th>ETL inspector</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>Managerial barrier overview (entire batch, not affected by roster filters)</h2>
<p>Simulated input states, not AI findings. A person can appear in multiple domains.</p>
{barrier_bars}
<table id="barriers"><thead><tr><th>Domain</th>
{''.join(f'<th>{state.value}</th>' for state in State)}
</tr></thead><tbody>{barrier_rows}</tbody></table>
<h2>Rules and guardrails</h2>
<p>Demo aging: GREEN &lt;15 days; YELLOW 15-29; RED 30+.
Calendar days since last contact, falling back to assessment. These are demo assumptions.</p>
<p>TRN: transit; HSG: housing; MED: health; LEG: legal.
CRT: critical; ACT: active; MIT: mitigated; RES: resolved; UNK: unknown.
Priority order: CRT, ACT, UNK, MIT, RES. This is not a referral/eligibility score.</p>
<p>Barrier interpretation and referrals remain with qualified staff.
Reviewed is a carried-through source value, not authorization for a referral.
TOON here is a custom demo-1 dialect, not standard TOON or an approved VOMA interface.</p>
<footer>Source SHA-256: {source_hash}<br>Static snapshot; rerun Python ETL for a new refresh.
Public code review is not production or licensing approval.</footer>
<script>
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
  document.getElementById('count').textContent = `Showing ${{visible}} of ${{rows.length}}`;
  for (const key of Object.keys(counts)) {{
    document.getElementById('count-' + key).textContent = counts[key];
  }}
}}
for (const control of [office, alertFilter, search]) {{
  control.addEventListener('input', filterRows);
}}
</script></body></html>
"""
