# SharePoint-first management demonstration runbook

Target recording: Friday, November 20, 2026. Synthetic-only discussion prototype
for management, IT and legal; not a production deployment or approval request
to process real records in this repository.

## What actually works

```text
Simulated SharePoint Excel file drop (baseline / refreshed XLSX)
  -> strict workbook schema and closed synthetic vocabulary
  -> Polars date transformation and aging
  -> lossless @TOON demo-1 serialization and parsing
  -> verified immutable batch
  -> real Excel charts, filterable watchlist, standalone HTML
```

The cloud SharePoint workbook is the intended MVP source of operational state.
The demonstration represents its delivery using local workbook snapshots.
It does not authenticate to Microsoft 365 or download a tenant file. An
authorized operator could later supply an approved downloaded workbook through
the same file boundary, after a separate production contract and permissions
review. This demo schema is **not** a schema for an existing agency workbook.

The Gemini references are visual inspiration only. No reference workbook data,
embedded logos, baseline figures, infrastructure details or claimed validation
results are redistributed in the implementation. All distributions are invented.

## Install and run

From the repository root, in an activated Python 3.11 virtual environment:

```bash
python -m pip install -r requirements-demo.txt
python -m jvsg_triage.demo rehearse --output temp/management-demo
```

Open `temp/management-demo/index.html` in a browser. It links to baseline and
refreshed HTML dashboards, the refreshed Excel workbook, TOON and verification
evidence. The HTML has no remote dependencies, fonts, assets, requests or backend.
The prominent **Demo files - open or download here** section on the landing page
and each report links directly to the Excel report, source workbook and TOON file.
Each report shows its actual folder and file locations from the page address.
For local files this is the filesystem path; when served over HTTP it is the URL
path. On disk, expand `temp/management-demo/batches/` in VS Code and select the
matching report folder. Excel links may download; check the browser Downloads list.
Open the Excel workbook in desktop Excel or an approved Excel browser viewer;
there is no requirement to host a web application.

If a remote VS Code browser cannot open the local file, either download the
generated folder to your recording computer or serve **only this synthetic
output directory**, on loopback, while rehearsing:

```bash
python -m http.server 8765 --bind 127.0.0.1 --directory temp/management-demo
```

Open `http://127.0.0.1:8765/`; stop the server with Ctrl+C afterward. Do not serve
the repository root or expose a development port publicly.

For code validation, install the development extra and run:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

### Separate the intake and refresh steps on camera

```bash
python -m jvsg_triage.demo prepare --output temp/management-demo/simulated_sharepoint
python -m jvsg_triage.demo run \
  --source temp/management-demo/simulated_sharepoint/baseline.xlsx \
  --as-of 2026-11-20 --output temp/management-demo
python -m jvsg_triage.demo run \
  --source temp/management-demo/simulated_sharepoint/refreshed.xlsx \
  --as-of 2026-11-20 --output temp/management-demo
```

`latest.json` identifies the last successfully verified batch. For explicit
verification, substitute the printed batch ID (no angle brackets):

```bash
python -m jvsg_triage.demo verify --batch temp/management-demo/batches/BATCH_ID
```

The `rehearse` command creates the convenient landing page and change report;
individual `run` commands create batches and status files, not that landing page.
No secret, HMAC key, model download, network service or cloud account is needed.

## Expected results

| Metric | Baseline | Refreshed |
|---|---:|---:|
| Invented participants | 18 | 19 |
| Recent contact: 0-14 days | 6 | 8 |
| Follow-up due: 15-29 days | 6 | 6 |
| Extended gap in contact: 30 or more days | 6 | 5 |
| Awaiting staff review | 16 | 17 |

- `DEMO-0005`: contact date changes to November 20; days since contact change from
  30 to 0; the housing barrier changes from critical to partly addressed.
  Other barriers may still need review.
- `DEMO-0019`: added to the South demonstration office.
- Existing source review values remain unchanged, including Reviewed records.
- `rehearsal.json` records both snapshots and the exact changed/added IDs.
- Nothing is sent to Teams, GeoSol, SharePoint, a partner or a model.

## Workbook contract and demo assumptions

The source contains exactly one worksheet, `Demo Intake`. Row 1 is
`JVSG_SYNTHETIC_DEMO_V1`; row 2 contains these human-readable column headings:

```text
Demonstration participant, Demonstration office, Assessment date,
Last recorded contact, Transportation, Housing, Health, Legal, Staff review status
```

Participant numbers are `DEMO-` plus four digits, not real identifiers. Office
names are North, Central and South demonstration office. Dates appear as
"Nov 20, 2026" in reports and date-formatted Excel cells; the loader also accepts
YYYY-MM-DD text. Source dropdowns use full descriptions, not codes.
Earlier code-based workbook headers and values remain accepted for compatibility;
the normalized JSON and compact TOON keep their stable machine-readable fields.
Contact may be empty; assessment is required. Reject duplicates, missing/extra
columns, unknown state/office/review values, formula cells, empty batches,
contact before assessment, future dates, additional sheets and oversized files.

Aging uses calendar days since last contact, or assessment if contact is absent.
The 15/30 boundaries are presentation assumptions, not approved follow-up policy.
The explicit `--as-of` date avoids a dashboard changing with the recording date.
Never infer the meaning of native MIS `Date1`-style fields from this demo.

Transportation, housing, health and legal needs are displayed as Critical barrier,
Needs support, Partly addressed, Resolved or Not yet assessed. The "Most pressing
recorded need" summary selects critical, needs support, not assessed, partly
addressed, then resolved, and names the relevant support area(s).
It is an explanatory demo rollup, not an eligibility,
clinical or referral score. Barrier states are supplied synthetic input, not AI
classification. Source review state is passed through; it is not independently
verified authorization. A refresh never writes back to the source workbook.
Make operational edits in the synthetic source, not a generated dashboard.

## TOON and reproducibility

`profiles.toon` uses the reference-inspired **custom @TOON demo-1 dialect**,
not the general Token-Oriented Object Notation standard or an approved federal
VOMA contract. Its fixed fields preserve every normalized profile attribute:
identity, office, assessment/contact/as-of dates, four independent domain states,
review status, idle days and alert. `~` encodes a missing contact date. The parser
rejects unknown versions, reordered/extra fields and noncanonical values.
Round-trip equality is verified for every record before publication.

Each immutable `batches/<SHA-256>/` directory contains:

| File | Purpose |
|---|---|
| `source.xlsx` | Exact synthetic input snapshot |
| `profiles.json` / `profiles.toon` | Equivalent normalized profiles |
| `summary.json` | Reconciled aggregate counts |
| `dashboard.xlsx` | Plain-language charts/list and definitions; technical sheets hidden |
| `dashboard.html` | Plain-language filters, contact counts, support details and overview |
| `manifest.json` | Source/output hashes, execution date, version and dependency versions |

`verify` checks hashes, source-to-profile reconciliation, all TOON round trips,
summary and HTML equivalence, row counts and serialized byte counts. Hashes
detect accidental alteration; they are not signatures or authorization controls.
The manifest reports UTF-8 bytes against equivalent compact JSON, **not tokens,
real-data accuracy or a promised compression percentage**.

The normal presentation does not require reading machine codes or a glossary.
The HTML has explanations next to the measures and a plain-language support
breakdown for each person. Technical encodings and fingerprints are tucked into
closed "for IT review" sections. In Excel, TOON and Provenance are hidden sheets
(a presentation choice, not a security control); Dashboard, Watchlist and
Definitions remain visible. Contact frequency and support needs are deliberately
separate: recent contact does not imply a person's barriers are resolved.

Repeated rehearsals in separate output roots produce byte-identical artifacts
with the same inputs, date, code and pinned runtime set. Workbook ZIP metadata
and timestamps are normalized. Tests explicitly change the writer clock.
Dependency upgrades can change output bytes; runtime versions are included in
batch identity. This is not a claim of byte stability across every Python,
operating-system or library release.

The publisher stages and verifies a batch before advancing `latest.json`.
Failed refreshes exit nonzero, leave the prior batch/pointer intact, and write
`status.json` with `state: failed`. A previously opened static dashboard does
not poll status: an operator must check status before presenting it as current.
Runs are single-operator; concurrent writers and a managed scheduler are not
implemented. Rerunning `prepare`/`rehearse` resets their generated source fixtures;
use a separately named copy for manual experiments.

## Public-review and production boundary

Use only generated fixtures. The marker and schema are not an anonymizer or
proof that a user-supplied workbook has no personal information in metadata,
comments or other embedded content. Never feed live exports or agency workbooks
to this demo. All generated outputs stay under Git-ignored `temp/`,
`data/private/` or an explicitly chosen external directory. Review recordings
and artifacts before sharing; do not capture terminals with secrets, file lists
outside the demo, real Teams chats or browser account information.

The existing native MIS intake/scrubber remains a separate workflow; it is not
bypassed, reinterpreted or a dependency of this closed-vocabulary workbook demo.
Unstructured production case notes still require the privacy protocol and
qualified review before any inference. No real-world scrubber efficacy is
claimed here.

Before any live pilot, IT/legal/domain owners must approve the actual workbook
contract and ownership, refresh/receipt/version rules, least-privilege site/file
access, identity and secret management, appropriate hosting, retention, access
separation, audit/error handling and operational definitions. Direct Graph
ingestion, production schema mapping, access control, durable staff edits,
automated triggers, notifications, inference and VOMA integration remain future
work. SharePoint does not execute this Python by storing it in a document library;
HTML hosting/embedding also requires tenant-specific review.

See [SECURITY.md](../SECURITY.md), the
[SharePoint proposal](./sharepoint_data_visualization_proposal.md) and
[recording script](./management_demo_script.md). Public review is not licensing,
deployment, security-settings or live-data approval.
