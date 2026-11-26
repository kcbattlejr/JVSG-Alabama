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
| 2 | Run `sql/28` and choose service codes | Not run |
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
3. Choose, with the program owner, the codes that mean:
   `medical` (medical referral or service), `training_enrolled`, `credential`,
   `training_completion`. Leave `'N/A'` for any you cannot identify; that field
   stays unknown (NULL), which the rules treat as "no data", not "no barrier".
4. Edit the `svc_map` block at the top of **step 29**
   (`29_fy2026_referral_profile.sql`). A category can list several codes by
   adding rows with the same category name.
5. Run **step 29** and export the CSV to `restricted/csv/profile/`. The
   header must match the synthetic CSV exactly (the repo test checks it).

## 2. Field mapping used by step 29

| Profile column | Source | Notes |
|---|---|---|
| INDIVIDUAL_USERNAME, STATE_ID | `users.username`, `indstaff.stateid` | Same as step 17. Keep State ID as text. |
| OFFICE_NAME | `onestopoffice_lu.onestopname` via `indstaff.office` | Same as step 17. |
| LAST_CONTACT_DATE, DAYS_SINCE_CONTACT | Latest valid case note, any staff | Same as step 17. |
| CONTACT_INFO_UPDATED_DATE | `ind.col_edit_date` | Proxy: last edit of the whole record, not proof the phone or address is current. |
| HOMELESS_FLAG | `indveteran.col_vethomeless` = 1 or `col_homelessreintegration` = 1 | 0 only when `col_vethomeless` = 0; otherwise NULL. |
| HOUSING_UNSTABLE_FLAG | None known | Always NULL. Open question 1. |
| DISABILITY_FLAG | `indveteran.vetdisability` 1 or 2 (0 = no) | |
| JUSTICE_FLAG | `indveteran.col_incarceration` | Meaning: released from incarceration in the past 12 months. |
| LAST_MEDICAL_SERVICE_DATE | `serviceplan.actualdate` for the `medical` codes | Needs `svc_map`. |
| TRAINING_ENROLLED_FLAG | `serviceplan` rows for `training_enrolled` codes in the last 365 days | Needs `svc_map`; NULL until set. |
| LAST_OUTCOME_TYPE, LAST_OUTCOME_DATE | Latest `credential` or `training_completion` service | Needs `svc_map`. |
| LAST_EMPLOYMENT_END_DATE | None known | Always NULL. Open question 2. |

## 3. Open questions to settle before relying on the output

1. **Housing instability** has no known field. Options: leave unknown, or
   derive it from a service code or note convention staff agree on.
2. **Employment end date** has no known source. With it empty, rule TRN-3
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
  have not been run.
