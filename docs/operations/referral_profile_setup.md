# Referral profile setup (living document)

Where the instructions live for building the community partner referral
profile on the SharePoint dashboard (Option A: structured data, fixed
templates, no model). Update the status table as each step is done. Real SQL
output stays in the JVSG SharePoint site; nothing identified goes in this repo.

Plan and rationale: [community_partner_referral_profile_plan.md](../planning/community_partner_referral_profile_plan.md).
Workbook steps: [sharepoint_demo_site.md](sharepoint_demo_site.md), section
"Referral profile, classification and TOON".

## Status

| Step | What | State |
|---|---|---|
| 1 | Re-run steps 17 and 21, refresh the dashboard | Per batch |
| 2 | Run `sql/28` (service codes); find housing and employment history columns (step 30 is blocked) | Not done |
| 3 | Put codes in `svc_map` in `sql/29`, run it, save the CSV | Not run |
| 4 | Add `Profile` and `Classification` queries to the workbook | Not done |
| 5 | Check counts and spot-check veterans with staff | Not done |
| 6 | Python in Excel TOON cells (`cell3` + `cell4`) | Not done |
| 7 | Brief sheet, `Referrals` table, Overview counts | Not built |

## 1. Run the batch (MIS query window)

`sql/` is gitignored. Paste each file as is; each is one SELECT.

1. **Step 17** then **step 21**: export to the dashboard folders as usual
   (`csv/manager/`, `restricted/csv/worklist/`).
2. **Step 28** (`28_referral_profile_service_inventory.sql`): counts of service
   codes the candidates used in the last 365 days. No identifiers.
3. **Step 30 cannot run in the query window**: MIS reports restricted tables for
   `INFORMATION_SCHEMA` (metadata is blocked, as with the earlier step 08). Find
   the two missing sources another way, then fill the two `SLOT` notes in the
   step 29 header:
   - Ask the vendor or IT for the full data dictionary for `tbl_case`,
     `tbl_caseveteran` (the Wagner-Peyser application tables) and the employment
     history table.
   - Or open a veteran's Wagner-Peyser application and employment history screen
     in MIS, note the field labels for housing stability and the employment
     history grid, and send me the labels and any page or table names shown;
     I'll map them to columns.
   - Then test one guess at a time: `SELECT TOP 5 k.<column> AS [x] FROM
     dbo.tbl_case AS k` fails with "invalid column" if the name is wrong.
4. Choose, with the program owner, the codes that mean:
   `medical` (medical referral or service), `training_enrolled`, `credential`,
   `training_completion`. Leave `'N/A'` for any you cannot identify; that field
   stays unknown (NULL), which the rules treat as "no data", not "no barrier".
5. Edit the `svc_map` block at the top of **step 29**
   (`29_fy2026_referral_profile.sql`). A category can list several codes by
   adding rows with the same category name.
6. Run **step 29** and export the CSV to `restricted/csv/profile/`. The
   header must match the synthetic CSV exactly (the repo test checks it).

## 2. Field mapping used by step 29

| Profile column | Source | Notes |
|---|---|---|
| INDIVIDUAL_USERNAME, STATE_ID | `users.username`, `indstaff.stateid` | Same as step 17. Keep State ID as text. |
| OFFICE_NAME | `onestopoffice_lu.onestopname` via `indstaff.office` | Same as step 17. |
| LAST_CONTACT_DATE, DAYS_SINCE_CONTACT | Latest valid case note, any staff | Same as step 17. |
| CONTACT_INFO_UPDATED_DATE | `ind.col_edit_date` | Proxy: last edit of the whole record, not proof the phone or address is current. |
| HOMELESS_FLAG | `indveteran.col_vethomeless` or `col_homelessreintegration` = 1, or the latest WP application's `tbl_caseveteran.col_vethomeless` = 1 | 0 only when `col_vethomeless` = 0; otherwise NULL. |
| HOUSING_UNSTABLE_FLAG | Housing stability on the veteran's most recent Wagner-Peyser application (`tbl_case`, `col_programid` = 3, latest `col_appdate`, not a partial save), documented at registration | Column not yet identified (step 30 is blocked; see section 1). NULL until the slot is filled. The application date shows how old the answer is. |
| DISABILITY_FLAG | `indveteran.vetdisability` 1 or 2 (0 = no) | |
| JUSTICE_FLAG | `indveteran.col_incarceration` | Meaning: released from incarceration in the past 12 months. |
| LAST_MEDICAL_SERVICE_DATE | `serviceplan.actualdate` for the `medical` codes | Needs `svc_map`. |
| TRAINING_ENROLLED_FLAG | `serviceplan` rows for `training_enrolled` codes in the last 365 days | Needs `svc_map`; NULL until set. |
| LAST_OUTCOME_TYPE, LAST_OUTCOME_DATE | Latest `credential` or `training_completion` service | Needs `svc_map`. |
| LAST_EMPLOYMENT_END_DATE | Employment history table | Table not in the schema document; find it via the vendor dictionary or the MIS screen. NULL until the slot is filled. |

## 3. Open questions to settle before relying on the output

1. **Housing instability**: identify the column on the Wagner-Peyser application and
   which values mean unstable versus stable. The answer is a point-in-time
   registration answer, so the rules should treat an old application as stale
   (the 180-day freshness rule needs the application date; add a column to the
   profile contract if you want that, updating the CSV, Power Query, Python,
   and tests together).
2. **Employment end date**: find the history table and decide how a row with no
   end date (current job) is handled. Until filled, rule TRN-3
   ("no recent employment") fires for every veteran without a recent outcome or
   enrolment, so the training and employment domain over-flags. Options: find a
   source, or change TRN-3 to require a known date (then update
   `dashboard_demo/profile.py`, `Classification.pq`, `cell4_profile_toon.py`,
   and the parity tests together).
3. **Service codes** for medical, training, credential and completion (step 28).
4. **Thresholds** (180 and 365 days) are invented defaults; confirm them.
5. **Field values**: confirm what `vetdisability`, `col_vethomeless` and
   `col_incarceration` actually contain in MIS (step 02 style value counts)
   before trusting the flags.
6. Whether a community partner directory exists to match categories to named
   organizations.

## 4. Add to the workbook

Follow "Referral profile, classification and TOON (add to the workbook)" in
[sharepoint_demo_site.md](sharepoint_demo_site.md). In short: add `Profile.pq`
and `Classification.pq` as blank queries (Data, Get Data, Blank Query,
Advanced Editor, paste, rename to the file name), Close and Load as tables,
Refresh All, then paste `cell3_toon.py` and `cell4_profile_toon.py` into a
Python sheet. Verify counts against staff judgement, not against the synthetic
expected counts, once real data is loaded.

## 5. Rules for everything produced

- All classification and TOON output is an `Unverified` draft for qualified
  staff review; it is not a referral or eligibility decision.
- Keep the profile CSV, workbook and TOON files in the restricted SharePoint
  library only.
- Validate the SQL against MIS records before any wider use. Steps 28 and 29
  have not been run; step 30 is blocked.
