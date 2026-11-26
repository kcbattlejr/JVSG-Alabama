# JVSG-Alabama

Tools for helping Alabama Jobs for Veterans State Grant (JVSG) staff find
veterans who may be falling through the cracks, so none are left behind. This
public repository contains **code, scripts, documentation and invented data
only**. It is **not approved for production use or external release**, and
live veteran data never belongs here.

## What exists today

The working deliverable is the **SharePoint Excel dashboard**. Its code lives
in [`src/jvsg_triage/m365/sharepoint_demo/`](src/jvsg_triage/m365/sharepoint_demo/):

| Piece | What it does |
|---|---|
| `power-query/` | Four queries that read the newest MIS CSV from SharePoint folders (manager summary, office matrix, worklist, worklist by office); Refresh All updates the dashboard. |
| `office-scripts/` | `BuildOverview.ts` (overview tiles and charts), `ImportJvsgCsv.ts` and `RepairDetailFormulas.ts` (detail-tab repair). Small groups show "Suppressed", not 0. |
| `sample_csv/` | Tiny invented CSVs used by the Node tests. A fuller 160-row set is in `data/synthetic/sharepoint_dashboard/`. |
| `tests/` | Offline Node tests with a simulated workbook API. |

The dashboard shows the follow-up cohort by office and age, a top-50 overdue
watchlist and a drill-down by office, band and days. The workbook, CSVs and
site address are identifier-bearing: they stay in the restricted JVSG
SharePoint site and never enter this repository. Setup, refresh and access
rules are in the
[SharePoint Excel runbook](docs/operations/sharepoint_demo_site.md).

### Run the dashboard on synthetic data

```bash
python -m pip install -r requirements-demo.txt
python -m jvsg_triage.dashboard_demo --output temp/dashboard-demo
```

This writes synthetic step 17 and step 21 style CSVs into the same folder layout
SharePoint uses, plus `temp/dashboard-demo/JVSG_Dashboard_Demo.xlsx` (Overview
tiles and chart with the "Suppressed" rule, a top-50 Watchlist, and the `Manager`
and `Worklist` tables). Open it in Excel. To rehearse the real Power Query
workbook, copy the CSVs from
[`data/synthetic/sharepoint_dashboard/`](data/synthetic/sharepoint_dashboard/README.md)
into the SharePoint test folders. The columns match the restricted MIS SQL
(steps 17 and 21) and the Power Query files; tests enforce this.

Also in the repo:

- [`m365/excel_python/`](src/jvsg_triage/m365/excel_python/README.md): Python
  in Excel cells (scrub, rules baseline, contract check, TOON). Tested offline;
  not yet run inside Excel.
- [`m365/office-scripts/BarrierFindings.ts`](src/jvsg_triage/m365/README.md):
  Office Script that proposes barrier findings, always `Unverified`.
- Restricted MIS SQL, vendor schema and operational notes are kept in approved
  private storage, not here.

## Next: November 30 demo

A staff-reviewed **community-partner referral brief** for each veteran in the
cohort, built from structured data with visible data freshness. Templates only:
**no model is used**, nothing is sent automatically, and referrals need
consent and qualified staff review. See the
[referral profile plan](docs/planning/community_partner_referral_profile_plan.md)
for the decision tree and work breakdown.

## Decisions in force

- Veteran PII is allowed only in the JVSG SharePoint site; this repo stays synthetic.
- Not available: Power Automate, Copilot Studio, `=COPILOT`. Python in Excel has no network access.
- No third-party hosting (for example Modal) for identified data. A local SLM
  or in-tenant Azure Function needs IT and governance approval and is deferred.
- Model output is a draft; case interpretation and referral decisions stay with qualified staff.

## Synthetic rehearsal (separate Python demo)

A self-contained offline rehearsal, built on invented reports, predates the
SharePoint dashboard and remains useful for practice and CI. It is not the
current deliverable.

```bash
python -m pip install -r requirements-demo.txt
python -m jvsg_triage.demo rehearse
```

Open `temp/management-demo/index.html` locally (no web server, model or cloud
account needed). It produces HTML and Excel dashboards and a lossless
`profiles.toon` from invented data. Details, Codespaces and Teams steps are in the
[demo runbook](docs/operations/management_demo_runbook.md). It does not connect to
SharePoint or MIS, infer fields from notes, or send data anywhere.

## Documentation

See the [documentation guide](docs/README.md) for runbooks, privacy rules, plans,
briefings, and the historical archive.

## Development

Repository layout:

- `src/jvsg_triage/`: Python modules and Microsoft 365 integration assets.
- `tests/`: Python tests; integration-specific synthetic harnesses live with their assets.
- `src/jvsg_triage/dashboard_demo/`: generator and local workbook for the dashboard demo.
- `data/synthetic/`: invented fixtures; `config/`: project configuration.
- `docs/`: runbooks and project documentation; `docs/archive/`: historical material.
- `azure_functions/`: optional Azure integration notes.

The Microsoft 365 assets, including the SharePoint dashboard, are under
`src/jvsg_triage/m365/`. Generated files under `temp/` stay local and ignored;
restricted SQL and live data must remain in approved private storage.

Use the provided VS Code dev container or a local Python 3.11+ virtual
environment. In the container, activate with
`source /home/vscode/.venvs/jvsg/bin/activate`.

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m mypy src
```

The Office Script tests need Node.js 22.13+ and skip without it; SQL window tests
need `sqlglot` and the restricted SQL files, and skip without them. Run the
dashboard script tests directly with
`node --test src/jvsg_triage/m365/sharepoint_demo/tests/importer.test.mjs`.

The code for the rehearsal is under `src/jvsg_triage/demo/`. The underlying
intake and scrubber are under `etl/` and `privacy/`; generated test data and
evaluation tools are documented under [data/synthetic/](data/synthetic/README.md).
Azure Functions, live Microsoft 365 synchronization, model-based case-note
inference, and VOMA remain unimplemented. The optional settings in `.env.example` do
not grant access or authorization.

Use only generated fixtures in development, demos, prompts, and CI. Do not copy
live reports into the workspace or use Git ignore rules as a privacy control.
Package metadata remains proprietary pending agency ownership and licensing
approval; repository visibility is not a license.
