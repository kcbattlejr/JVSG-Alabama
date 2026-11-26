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
| 2 | Run `sql/28` (service codes); optionally `sql/31` (application value counts) | Not run |
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
3. Optional: **step 31** (`31_referral_profile_wp_application_values.sql`) shows
   value counts for the latest Wagner-Peyser application fields (housing plan,
   homeless, employment status, currently or self employed, layoff date
   recorded) for comparison with the barrier and work history answers. Step 30
   (metadata discovery) cannot run here: MIS blocks `INFORMATION_SCHEMA`.
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
| HOMELESS_FLAG | `indveteran.col_vethomeless` or `col_homelessreintegration`, the latest WP application's `tbl_caseveteran.col_vethomeless`, or the latest `indbarrier_history.homeless` | Any 1 means homeless; 0 only when a source says 0; otherwise NULL. |
| HOUSING_UNSTABLE_FLAG | Latest `indbarrier_history.col_housingassist` (needs housing assistance) | Barrier history is the audit table of the barrier screen; the latest non-deleted row per veteran is used. Confirm this is where registration housing answers land. |
| DISABILITY_FLAG | `indveteran.vetdisability` 1 or 2 (0 = no), or latest barrier `phymtldis` = 1 | |
| JUSTICE_FLAG | `indveteran.col_incarceration`, or latest barrier `offender` or `col_currentlyonparole` = 1 | |
| LAST_MEDICAL_SERVICE_DATE | `serviceplan.actualdate` for the `medical` codes | Needs `svc_map`. |
| TRAINING_ENROLLED_FLAG | `serviceplan` rows for `training_enrolled` codes in the last 365 days | Needs `svc_map`; NULL until set. |
| LAST_OUTCOME_TYPE, LAST_OUTCOME_DATE | Latest `credential` or `training_completion` service | Needs `svc_map`. |
| LAST_EMPLOYMENT_END_DATE | `indemphistory` (veteran work history, not inactive rows) | The as-of date when any entry is marked currently employed; otherwise the latest `enddate`; otherwise `tbl_wpapp.col_layoffdate`; otherwise NULL (TRN-3 then fires). |

## 3. Open questions to settle before relying on the output

1. **Housing instability** (decision 2026-11-26): `housingplan` is the
   Transition Assistance Program (TAP) housing-plan assessment done by TAP
   officers, not JVSG staff, so it is not used. **Housing instability** now comes from the barrier history "needs housing
   assistance" answer. Confirm with staff that this is the answer captured at
   registration and how current it is (step 31 shows the Wagner-Peyser
   application answers for comparison). A barrier answer has no date in the
   profile; adding one means changing the CSV, Power Query, Python, and tests
   together.
2. **Employment end date** (decision 2026-11-26) falls back to the
   Wagner-Peyser application employment status (`col_empstatusid`) when there is
   no work history or layoff date: status 1 (employed) or 2 (employed, notice
   of termination) is treated as currently employed (end date = as-of date);
   status 3 (not employed) or blank stays NULL. The status is as of the
   application date, so it can be stale; confirm with staff. Uses work history entries. Check that a veteran
   with only an undated or "currently employed" entry is treated correctly,
   and that a veteran with no work history at all (NULL, so TRN-3 fires) is
   what staff expect.
3. **Service codes** (step 28). Interim choice: `training_enrolled` uses the
   referral codes 209, 210, 211 and 206, so a referral to training counts as
   enrolled for now. **Question for the state coordinator (Hank):** should a
   referral count as enrolment, or only a confirmed start? Medical, credential
   and completion have no matching code and stay `'N/A'` (NULL, unknown).
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
