# Daily briefing: November 20, 2026

Status and to-do only. No veteran identifiers, staff details, or query results
belong here. Keep all MIS outputs in approved SharePoint/OneDrive storage.

**Historical only:** The service-based reports and commit instructions below
are superseded. Do not follow them; SQL and its operational documentation are
restricted and excluded from this repository.

## Where we are

- **Constraint today:** No direct database connection from inside the firewall.
  Work is done by pasting the saved SQL into the MIS free-form SQL tool and
  exporting grid/CSV results manually. No schedule, email, or Power Automate
  delivery is verified.
- **Settled:** The FY2026 WP 203/205 candidate definition (steps 15, 16, 20).
  Do not reopen it during testing.
- **Step 16 (watchlist):** Grid/CSV counts agreed and selected field checks
  passed. Manual-test only; not an approved roster.
- **Step 20 (manager view):** Not closed. The earlier `ready` result cannot be
  tied to the current query text, and the revised blank-LWIA grouping is
  unconfirmed.
- **Rule 2 path:** Step 05 full CSV still exports header-only (blocked). Step
  05a is manual-test only. Step 06 passed spot checks but needs privacy/records
  approval before sharing.
- **Repository:** `sql/`, SQL docs and `tests/test_sql_window_rules.py` are
  still untracked, and several docs are modified or deleted but uncommitted.
  Latest commit is the synthetic demo dashboard chart labels.

## Essential today (in order)

1. **Run step 20 in the MIS free-form tool.** Paste the current text of
   `sql/20_fy2026_wp_noncm_manager.sql`, replace the login placeholder in MIS
   only, and run it. Record only the `result_status`.
   - `ready`: at least one group is visible.
   - `no_visible_groups`: suppression hid every group. This is not an empty
     cohort.
   - An invalid-input, missing-anchor or missing-group status is not an empty
     result.
2. **Export a fresh step 16 file with the same as-of date.** Check both grid
   and CSV.
3. **Compare in approved storage.** Group the step 16 export by individual
   LWIA and follow-up band, apply the same suppression, and compare each
   visible group with step 20. Confirm missing, NULL and blank LWIA values fall
   into the single combined group, and that unmatched nonblank codes stay
   separate.
4. **Log completion.** Write pass/fail only in the private location. Add a
   non-sensitive status line to `docs/sql_reporting_status.md` if it passes.
5. **Demo readiness.** Decide which output you will show: step 20 aggregates
   are the safest. Show step 16 only to authorized viewers, because it
   carries identifiers. Keep the synthetic demo (`python -m jvsg_triage.demo
   rehearse`) as the backup.
6. **Protect the work.** Review and commit the untracked SQL, docs and test
   after confirming they contain no identifiers or exports. Check `git status`
   first.

## Open, but not for today

- Privacy/records approval for suppression threshold, overlapping reports,
  repeat releases and audience.
- Step 05 header-only CSV diagnosis (staged, per the runbook), if still needed.
- Ask MIS/IT about supported scheduling, attachments, or an approved read-only
  connection. Today's firewall issue is worth raising with them.
- Power Automate/Outlook delivery: only after a report is approved.

## Guardrails for the demo

- Label outputs as candidates for qualified human review, not eligibility,
  assignment or referral decisions.
- `staffadd` is the record creator, and the group code is current, not
  historical. Say so if asked.
- Do not paste results into chat or commit them.
