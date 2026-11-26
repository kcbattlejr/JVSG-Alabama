# NASWA demo kit (synthetic)

A portable copy of the JVSG dashboard's folder layout, invented data, Power Query
files and Office Scripts, for recording the NASWA screenshots and video. Copy this
whole folder anywhere. **All data is invented**; no veteran, staff, office or
cohort figure from the live system is used, and nothing here connects to MIS or
SharePoint. Keep it separate from the restricted live workbook so a capture can
never show live data (see the capture rules in
[the video script](../../docs/naswa/video_script_and_screenshots.md)).

```text
naswa_demo/
  build_demo_data.py          regenerate the CSVs (Python 3.11+, standard library only)
  Demo/                       same layout as the SharePoint library
    csv/manager/21_FreeFormSql_20261126.csv            step 21 style (no identifiers)
    restricted/csv/worklist/17_FreeFormSql_20261126.csv step 17 style
    restricted/csv/profile/29_FreeFormSql_20261126.csv  step 29 style
  power-query/                Manager, ManagerMatrix, Worklist, WorklistByOffice, Profile, Classification
  office-scripts/             BuildOverview.ts, BuildDetailTabs.ts, RepairDetailFormulas.ts
  python-in-excel/            cell3_toon.py, cell4_profile_toon.py (optional TOON step)
```

## Build the demo workbook

The workbook itself is not shipped: it is built from the queries and scripts, the
same way as the real one ([rebuild walkthrough](../../docs/operations/sharepoint_demo_site.md#rebuild-from-scratch-live-demo-workbook-was-deleted)).

1. Copy the folder to the capture machine, for example `C:\JVSG\NaswaDemo`.
2. Create `Demo\restricted\JVSG_Dashboard_Overview.xlsx` in desktop Excel; add
   sheets `Overview`, `Python`, `Data`.
3. **Data > Get Data > Launch Power Query Editor > Manage Parameters > New**:
   `DemoFolder`, Text, value = the full path of the `Demo` folder
   (for example `C:\JVSG\NaswaDemo\Demo`).
4. Add each file in `power-query/` as a blank query (Advanced Editor), in this
   order, named as the file: `Manager`, `ManagerMatrix`, `Worklist`,
   `WorklistByOffice`, `Profile`, `Classification`. `Manager`, `Worklist` and
   `Profile` are local-folder variants of the SharePoint queries; the other three
   are unchanged. Close & Load each to a table with the same name; untick
   background refresh.
5. Run `BuildOverview.ts`, then `BuildDetailTabs.ts` from **Automate > New
   Script**. If the Drilldown or Watchlist count updates but rows stay blank,
   run `RepairDetailFormulas.ts`.
6. Optional: paste the two Python-in-Excel cells (see the runbook section
   "Referral profile, classification and TOON").

Expected results for the shipped data (seed 3042, as of 11/26/2026):

| Check | Value |
|---|---|
| `Worklist` / `Profile` rows | 240 / 240 |
| `Classification` rows | 960 (4 per profile) |
| `WorklistByOffice` rows | 12 offices |
| Worklist bands | Overdue 148, Due soon 28, Current 64 |
| `Manager` rows | 7 visible groups; Due soon is suppressed in every area, so the Overview tile shows **Suppressed** |
| TRN | RES 36, MIT 22, ACT 159, UNK 23 |
| HSG | CRT 20, ACT 34, UNK 186 |
| MED | MIT 18, ACT 64, UNK 158 |
| LEG | ACT 29, UNK 211 |

The profile CSV fills the outcome and medical-service columns as if the
service-code mapping had been completed. In the live system those columns stay
blank until the program owner confirms the codes
([referral profile setup](../../docs/operations/referral_profile_setup.md)).
The query logic is the repository's tested logic; the local-folder source
change (`Folder.Files`) has not been run in Excel by this repository.

## Refresh for a new take

```bash
python build_demo_data.py --as-of 2026-11-30       # new files, same seed
python build_demo_data.py --seed 7 --count 300     # different invented cohort
```

Delete the older CSV in each folder (the newest file wins), then **Data >
Refresh All**. Output defaults to `./Demo`; use `--output` for another folder.

## What the data imitates

Only the export format: column names, `MM/DD/YYYY h:mm:ss AM` note stamps, MIS
file names, CRLF line endings, quoted `"Last, First"`-style staff names, 0/1/blank
flags, 15/30-day bands and suppression of groups below 10. Offices are "Demo
Office ...", areas are "Demo Area ...", State IDs start with `99`, and
distributions are chosen for a readable demo, not drawn from any real cohort.

## Capture checklist

Follow the shot list in
[video_script_and_screenshots.md](../../docs/naswa/video_script_and_screenshots.md):
Overview, Offices and Age, Drilldown with the referral panel (pick a State ID in
`M4`), Watchlist, a validation failure (drop a wrong CSV into a folder and
refresh to show the "expected columns are missing" check). Hide the ribbon's
account name, file paths and notifications before recording.
