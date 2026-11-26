# SharePoint demo site: Excel dashboard connected to MIS CSV dumps

**Status: November 26, 2026. The live workbook was deleted; see
"Rebuild from scratch".** As of November 22, 2026, The owner reports that the consolidated
SharePoint workbook and its detail filters are working. The saved workbook
contains the four query tables and repaired detail formulas; independent Excel
recalculation, refresh, permissions, and MIS record validation have not been
established by this repository. Real CSVs, workbooks, and the site address
stay in approved restricted storage and never enter this repository. Output is
a candidate list for qualified human review, not a decision.

The saved workbook's cached Watchlist order, current Drilldown selection and
count, displayed detail values, and 203 indicator were compared with its source
table in memory without recording individual records or validation metrics.
The saved helper formulas were checked across both result ranges. These checks
cover only the saved state and do not verify subsequent filters, refreshes,
SharePoint permissions, or the underlying MIS cohort.

## Approach

Power Automate is not available on the owner's licence, so the dashboard uses
Excel **Power Query** connections instead of flows:

- The restricted workbook holds queries that read the **newest CSV** in each
   SharePoint subfolder. Dump new CSVs, click **Data > Refresh All**, save.
- A **SharePoint page** embeds the workbook with the **Excel web part**, which
  shows the saved dashboard sheet or chart.
- SharePoint serves `.html` from libraries as downloads, so a custom HTML/JS
  page does not run there; Excel plus the web part does.

Queries are in [sharepoint_demo/power-query](../../src/jvsg_triage/m365/sharepoint_demo/power-query/).
The earlier Office Script
([ImportJvsgCsv.ts](../../src/jvsg_triage/m365/sharepoint_demo/office-scripts/ImportJvsgCsv.ts)) needs
Power Automate to read files, so it is parked unless that becomes available.

## Restricted folder layout

```text
Demo/
  csv/manager/                 dump step 21 CSVs here (no identifiers)
  restricted/                  separate permissions: named reviewers only
      JVSG_Dashboard_Overview.xlsx  overview and identifier-bearing detail
    csv/worklist/              dump step 17 CSVs here
    csv/profile/               dump step 29 CSVs here (referral profile)
```

The manager query reads only `csv/manager/`; the worklist query reads only
`restricted/csv/worklist/`; the profile query reads only
`restricted/csv/profile/`. The consolidated workbook contains identifiers
and unsuppressed counts and must remain restricted in its entirety. Showing
only `Overview` on a page or hiding other sheets does not restrict access to
the underlying workbook. A separately built aggregate-only workbook is needed
for any broader audience, subject to privacy approval: releasing step 17
counts alongside suppressed step 21 counts can reveal groups by subtraction.

## Rebuild from scratch (live demo workbook was deleted)

Use this when the workbook is gone. Do it first with the synthetic files, then
swap in real CSVs. Total time is about an hour. Check the SharePoint recycle bin
first: a deleted workbook can usually be restored, which is faster than
rebuilding (site contents > Recycle bin).

**What is in git and what is not.** In git: the Power Query files, Office
Scripts, Python cells and synthetic CSVs. Not in git (never commit): real CSVs,
the workbook, the site URL, the restricted SQL. **Detail tabs** (`Offices and
Age`, `Watchlist`, `Drilldown`, `Definitions`) have no builder in the repo; only
the column K repair formulas exist (see below). Rebuild them by hand, or ask for
a script to be written.

### 1. Folders and CSVs

1. In the JVSG SharePoint site library, create the layout from "Restricted folder
   layout" above: `Demo/csv/manager/`, `Demo/restricted/csv/worklist/`,
   `Demo/restricted/csv/profile/`. Give `restricted/` its own permissions
   (named reviewers only; break inheritance).
2. **Rehearsal:** upload the synthetic files from
   [data/synthetic/sharepoint_dashboard](../../data/synthetic/sharepoint_dashboard/README.md):
   `csv/manager/synthetic_manager_report.csv` to `csv/manager/`,
   `restricted/csv/worklist/synthetic_worklist_report.csv` to `restricted/csv/worklist/`,
   `restricted/csv/profile/synthetic_profile_report.csv` to `restricted/csv/profile/`.
3. **Real data:** run steps 21 (manager), 17 (worklist) and 29 (profile) in MIS,
   export CSV, and upload to the same three folders. Delete the synthetic files
   first, because the newest file in each folder wins. Run steps 17, 21 and 29
   from the same day so the as-of dates agree.

### 2. New workbook

1. In `Demo/restricted/`, create a new Excel workbook named
   `JVSG_Dashboard_Overview.xlsx`. Open it in **desktop Excel** (Power Query
   editing needs it).
2. Rename Sheet1 to `Overview`. Add sheets named `Python`, `Data`, and later the
   detail tabs.

### 3. Connect the Power Query queries

1. **Data > Get Data > Launch Power Query Editor > Manage Parameters > New**:
   `SharePointSiteUrl`, type Text, current value = site root only
   (`https://<tenant>.sharepoint.com/sites/<SiteName>`). No `/_layouts/` or
   `/onedrive`.
2. For each file below: **New Source > Other Sources > Blank Query > Advanced
   Editor**, replace everything with the file's contents, click Done, rename the
   query to the name shown, and sign in with your organizational account when
   asked (choose **Organizational account** and apply to the site root).

   | Order | File in `src/jvsg_triage/m365/sharepoint_demo/power-query/` | Query name |
   |---|---|---|
   | 1 | `Manager.pq` | `Manager` |
   | 2 | `ManagerMatrix.pq` | `ManagerMatrix` |
   | 3 | `Worklist.pq` | `Worklist` |
   | 4 | `WorklistByOffice.pq` | `WorklistByOffice` |
   | 5 | `Profile.pq` | `Profile` |
   | 6 | `Classification.pq` | `Classification` (reads `Profile`; add after it) |

3. **Close & Load To... > Table**, existing worksheet `Data`, placed in separate
   areas, or one sheet per table. Table names must equal the query names. Keep
   them off `Overview`.
4. For each query, **Properties**: untick "Enable background refresh".
5. **Check:** the synthetic set gives `Worklist` 160 rows, `Profile` 160 rows and
   `Classification` 640 rows. If a query says "expected columns are missing", the
   wrong CSV is in that folder. If it says "No CSV found", the path or folder
   name is wrong.

### 4. Overview sheet

1. With `Manager` and `ManagerMatrix` loaded and refreshed, open **Automate >
   New Script**, paste
   [BuildOverview.ts](../../src/jvsg_triage/m365/sharepoint_demo/office-scripts/BuildOverview.ts)
   and **Run**. It creates the banner, four tiles, two charts and the "how to
   read" block. On a brand new workbook there is nothing to lose; it deletes and
   replaces any existing `Overview`, so do not run it on a workbook you have
   edited. If the Automate tab is missing, build the tiles and charts by hand
   over the two tables.
2. Chart ranges are fixed to the current `ManagerMatrix` rows; extend them if more
   LWIAs appear.

### 5. Detail tabs (restricted)

Build over the `Worklist` and `WorklistByOffice` tables (see "Detail tabs"
below for what each does): `Offices and Age` (office by band, charts),
`Watchlist` (top 50 overdue, longest wait first, formulas in column K rows
5 to 54), `Drilldown` (filter by office, band and minimum days; up to 100 rows,
column K rows 10 to 109) and `Definitions`. After building Watchlist and
Drilldown, if the counts update but rows do not appear, run
[RepairDetailFormulas.ts](../../src/jvsg_triage/m365/sharepoint_demo/office-scripts/RepairDetailFormulas.ts)
(**Automate > New Script**). It rewrites only those two K ranges.

### 6. Referral profile and TOON

Follow "Referral profile, classification and TOON" below. The `Profile` and
`Classification` queries are already loaded from step 3, so go straight to the
Python sheet: paste `cell3_toon.py` into A1, `cell4_profile_toon.py` into A2, and
the A3 to A5 formulas given there. The older `cell1` and `cell2` cells are only
for case-note scrubbing and are not needed. Python cells run in order, so keep the
`Python` sheet before the data sheets.

### 7. Save, check, publish

1. **Data > Refresh All**, wait for it to finish, then save to SharePoint.
2. Close and reopen the workbook, refresh again, and confirm the numbers match.
3. Add the Excel web part to a restricted page (see "SharePoint page").
4. For the real run: delete the synthetic CSVs, upload the real ones, refresh,
   save. This makes the whole workbook identifier-bearing, so keep it restricted.
5. Keep a copy of the finished workbook in approved storage and use SharePoint
   version history; do not delete the live copy again without a backup.

## Reference: build or recover the workbook (desktop Excel)

1. Open the restricted workbook. **Data > Get Data > Launch Power Query Editor.**
2. **Manage Parameters > New**: name `SharePointSiteUrl`, type Text, current
   value = the site address (for example the Mobile JVSG site's root URL).
   Use the site root only (`https://<tenant>.sharepoint.com/sites/<SiteName>`).
   A browser address containing `/_layouts/` or `/onedrive` fails with
   "URL neither points to an OData service or a feed". The folder must be in
   the site's library, not a personal OneDrive.
3. **New Source > Blank Query**, **Advanced Editor**, paste
   [Manager.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/Manager.pq), name it `Manager`.
   Sign in with your organizational account when prompted.
4. Repeat with [ManagerMatrix.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/ManagerMatrix.pq),
   named `ManagerMatrix`.
5. Add [Worklist.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/Worklist.pq) as `Worklist`
   and [WorklistByOffice.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/WorklistByOffice.pq)
   as `WorklistByOffice`. **Close & Load To... > Table** for all four queries.
   Table names must match the query names; keep data tables off presentation
   sheets. These queries make the workbook identifier-bearing and restricted.
6. The `Overview` sheet (banner, four tiles, status line, two charts, "how to
   read" block) uses only live formulas and charts over the `Manager` and
   `ManagerMatrix` tables, so **Refresh All** updates it. If the Automate tab
   is unavailable, the sheet is added to the workbook file directly (kept in
   the private SharePoint folder, not in git).
   [BuildOverview.ts](../../src/jvsg_triage/m365/sharepoint_demo/office-scripts/BuildOverview.ts) can
   build an Overview, but **deletes and replaces** that sheet; do not run it on
   the working workbook without reviewing and backing up the layout. Chart
   ranges are fixed to the current `ManagerMatrix` rows; if more LWIAs appear,
   extend them.
7. Keep the query tables and show `Overview` first. The detail sheets in the
   current workbook are not created by `BuildOverview.ts`; preserve the working
   workbook in approved storage rather than assuming this script rebuilds them.
8. In each query's **Properties**, untick "Enable background refresh" so
   **Refresh All** finishes before you save.
9. Save the workbook back to SharePoint.

### Detail tabs (restricted)

`Offices and Age` (office-by-band, days-since-contact and note-count charts),
`Watchlist` (top 50 overdue, longest wait first), `Drilldown` (filter the
worklist by office, band and minimum days; up to 100 rows) and `Definitions`
are formula-driven over the `Worklist` and `WorklistByOffice` tables. They list
veterans and unsuppressed office counts, so they belong only in the restricted
workbook. No sheet in that workbook should be shared widely by itself. The
original demo's support-area and staff-review charts are not rebuilt because
those fields are not in the MIS reports. TOON is deferred.

In the current detail layout, "Veterans with a 203 this fiscal year" counts
numeric `LATEST_FY_203_DATE` values in `Worklist`: it is the number of rows in
the note-based candidate cohort with an active FY 203, not all veterans with
a 203 or the number of 203 services. The office chart uses the unsuppressed
`WorklistByOffice` counts. Its current source covers rows 2 through 32; extend
the chart source if more offices are present.

If the Watchlist or Drilldown count updates but the results do not appear,
Excel may have converted the hidden column K formulas to single-row references.
On a restricted copy of this specific workbook, use **Automate > New Script**,
paste and run [RepairDetailFormulas.ts](../../src/jvsg_triage/m365/sharepoint_demo/office-scripts/RepairDetailFormulas.ts).
It replaces only `Watchlist!K5:K54` and `Drilldown!K10:K109` and recalculates;
it does not rebuild sheets or modify queries. In Excel, verify several filters,
including no matches and more than one match, against the Worklist table. Check
that the Watchlist is ordered by descending days and shows no more than 50 rows,
and Drilldown shows up to 100 matches in report order. Verify after refresh and
reopening before applying the repair to the live workbook. The Office Script
test is synthetic and does not run Excel's formula engine.

Office Scripts are stored separately from the workbook. To associate an owned
script, open the workbook, choose **Automate > View Scripts**, select the
script and turn on **Associate with workbook**. Do not move existing scripts
without checking for dependent links or flows.

Run the synthetic script and fixture tests with Node.js 22.13 or newer:

```bash
node --test src/jvsg_triage/m365/sharepoint_demo/tests/importer.test.mjs
```

These tests simulate workbook APIs; they do not compile against the Office
Scripts runtime or replace testing in Excel.

## Referral profile, classification and TOON (add to the workbook)

Python does not run in SharePoint. Everything below runs inside the restricted
workbook with Power Query and Python in Excel; no model, flow or script host is
used. Rehearse the whole sequence on the synthetic files first.

1. **Profile CSV.** Put the profile query output (restricted SQL, kept outside this
   repo) in `restricted/csv/profile/`. Rehearsal file:
   [synthetic_profile_report.csv](../../data/synthetic/sharepoint_dashboard/restricted/csv/profile/synthetic_profile_report.csv).
2. **Queries.** In Power Query add
   [Profile.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/Profile.pq) as `Profile`, then
   [Classification.pq](../../src/jvsg_triage/m365/sharepoint_demo/power-query/Classification.pq) as
   `Classification` (it reads `Profile`). Load both to tables with those names, untick
   background refresh, and use **Refresh All**. Both tables hold identifiers or
   classifications of veterans: restricted workbook only.
3. **Check the result (synthetic set).** `Classification` has 4 rows per profile
   (640 for 160 profiles). Expected state counts: TRN ACT 99, MIT 12, RES 25, UNK 24;
   HSG CRT 17, ACT 26, UNK 117; MED ACT 40, MIT 17, UNK 103; LEG ACT 33, UNK 127.
   For live data, spot-check several veterans by hand against the rules. The
   rules and thresholds are examples pending program-owner confirmation.
4. **TOON.** Add a sheet named `Python` placed before the data sheets. Paste
   [cell3_toon.py](../../src/jvsg_triage/m365/excel_python/cell3_toon.py) into A1 and
   [cell4_profile_toon.py](../../src/jvsg_triage/m365/excel_python/cell4_profile_toon.py) into
   A2 (**Formulas > Insert Python**), then in A3
   `class_chunks, summary_chunks = profile_toon(xl("Profile[#All]", headers=True), xl("Classification[#All]", headers=True))`
   (Python object), A4 `pd.Series(class_chunks)` and A5 `pd.Series(summary_chunks)`
   (Excel values). Each cell is a valid TOON table. Save them as
   `barrier_classifications.toon` and `profiles.toon` in the restricted library if an
   audit artifact is needed. TOON holds a row key (`P0001`), never names or State IDs;
   the `Profile` table row order is the crosswalk, so do not re-sort it between
   export and review. Python in Excel sends the table data to Microsoft's cloud
   container inside the tenant (approved for this use by the program owner).
5. **Use.** Count by state with formulas, for example
   `=COUNTIFS(Classification[state],"CRT")`. Every row is `Unverified` until staff
   confirm, correct or reject it; nothing is a referral decision.

If Python in Excel is unavailable, steps 1-3 and the counts still work; TOON can be
generated later from the same CSV with `python -m jvsg_triage.dashboard_demo` logic
on an approved machine.

## SharePoint page

1. On a restricted site page, add the **Excel** web part and choose the
   restricted consolidated workbook and intended sheet or chart.
2. Share the page and workbook only with approved reviewers. The viewer needs
   read access to the workbook, including all its sheets.
3. After each refresh and save, reload the page. Test once whether the web
   part's own refresh works with SharePoint-folder queries; if not, refresh in
   desktop Excel before the demo.

## Demo-day use

1. Run steps 21 and 17 in MIS and export CSV.
2. Drop the step 21 CSV in `csv/manager/` and the step 17 CSV in
   `restricted/csv/worklist/`. File names do not matter; the newest file wins,
   so delete or move old CSVs per retention policy.
3. Open the restricted workbook in desktop Excel, **Refresh All**, save.
4. Rehearse first with the 160-row synthetic set in
   [data/synthetic/sharepoint_dashboard](../../data/synthetic/sharepoint_dashboard/README.md)
   (or `python -m jvsg_triage.dashboard_demo` for a local workbook with no
   SharePoint), or the tiny files in
   [sharepoint_demo/sample_csv](../../src/jvsg_triage/m365/sharepoint_demo/sample_csv/) (copy them into
   the folders, then remove them before real data).

If a query errors with "expected columns are missing", the newest file is the
wrong report or the MIS columns changed; fix the file, not the query.

## Alternatives

- **Synced folder:** if the OneDrive-synced folder path is stable, replace the
  first lines of a query with `Folder.Files("C:\...\Demo\csv\manager")` (same
  filter and sort). Desktop Excel only.
- **Paste-in script:** an Office Script can run manually without Power
  Automate, but cannot read files. It could rebuild the dashboard from CSV
  rows pasted into a sheet; not built yet.

## Before using real data

- Independently verify refresh, credentials, saved results, and page behavior.
- Confirm the audience and permissions on the workbook, folders, and page, and the
  retention rule for dumped CSVs.
- Confirm follow-up band thresholds with the program owner.
- Confirm the privacy decision for releasing step 21 and review the restricted
   SQL reporting status before sharing or scheduling.
