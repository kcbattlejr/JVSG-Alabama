# Synthetic data for the SharePoint dashboard

**Every value is invented**: 160 fictional candidates (`demo.personNNN`, State IDs in
the `99` band), invented offices and areas, and an invented follow-up distribution.
Nothing reflects a real cohort size, profile or office.

The layout mirrors the SharePoint folders the Power Query files read:

| File | Mirrors | Contract |
|---|---|---|
| `restricted/csv/worklist/synthetic_worklist_report.csv` | Step 17 note-based watchlist | Same 21 output columns as the restricted SQL; read by `Worklist.pq` |
| `csv/manager/synthetic_manager_report.csv` | Step 21 manager view | Same 9 output columns; groups below 10 omitted; read by `Manager.pq` |
| `restricted/csv/profile/synthetic_profile_report.csv` | Planned profile query (wide, after pivot) | Structured flags and dated fields; no names or contact details |
| `toon/profiles.toon`, `toon/barrier_classifications.toon` | TOON export of the profile and its rule-based classification | No names or State IDs; row key `P0001`... |

The restricted SQL (steps 17 and 21) is kept outside this repository. The generator
reproduces its output columns, the 15/30-day follow-up bands and its small-group
suppression. `tests/test_dashboard_demo.py` checks the columns against the Power
Query `Required` lists, and against the SQL aliases when the restricted `sql/`
folder is present locally.

`barrier_classifications.toon` holds one row per profile and domain (TRN, HSG, MED,
LEG) with a state from the closed vocabulary (CRT, ACT, MIT, RES, UNK), the rule id
(`profile-rules-v1`), the structured evidence field and value, its date and
freshness, a suggested partner category for CRT/ACT only, and `Unverified` review
columns. Classification reads structured fields only, never notes. No structured
indicator maps to `UNK` (unknown), not to "no barrier". The row key is a profile
number; the crosswalk to a veteran stays in the restricted workbook.

Default data intentionally has suppressed groups (one area is absent and two
bands are hidden) so the "Suppressed" wording can be demonstrated.

Regenerate (deterministic; the committed CSVs must match):

```bash
python -m jvsg_triage.dashboard_demo --output data/synthetic/sharepoint_dashboard --csv-only
```
