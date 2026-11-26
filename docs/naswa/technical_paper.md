# From Case Notes to Follow-Up Visibility: ETL, SQL and SharePoint Engineering for the Alabama JVSG Program

Technical paper supporting the 2027 NASWA Merrill Baumgardner Innovation in
Information Technology Award nomination. DRAFT for review.

Authors: Keith Battle (lead developer). Contributors: see
[bios](bios.md).

Publication posture: this paper is written to be posted publicly. It contains
no veteran, staff or case information, and it deliberately uses **generic names**
for database objects, privilege groups and title patterns (see
[SQL publication strategy](../sql/sql_publication_strategy.md)). All figures shown are
from a synthetic demonstration kit, never from live data.

## Abstract

Jobs for Veterans State Grant (JVSG) staff document their work as free-text
case notes in a state management information system (MIS). Managers have no
native view of which veterans have gone too long without contact. We describe a
low-cost, auditable pipeline that (1) identifies the population of interest
from note activity with read-only SQL, (2) exports small typed CSV files to a
restricted SharePoint library, (3) transforms them with Power Query, and
(4) presents them in an Excel workbook with Office Scripts and worksheet
formulas, split into a restricted worklist for staff and a suppressed summary
for managers. A deterministic, rule-based barrier profile and a community
partner referral brief are layered on, always as drafts for human review. The
design is shaped by constraints: no write access, a single-statement query
window, no automation platform, and strict privacy tiers. We report the
engineering lessons and the explicit limits of what has been validated.

## 1. Problem and context

### 1.1 The visibility gap
Case notes record contact, but the MIS offers no report answering "which
veterans in my caseload were last contacted more than N days ago?". Existing
service-based reports start from services, so staff whose work is documented
only as notes are invisible. The initiative reframes the population around
**notes**: a veteran is in scope when a designated staff member authored a note
in the fiscal year.

### 1.1a Field origin
The work began in Mobile, where the two-person JVSG team (a specialist and a
Local Veterans' Employment Representative) observed that veterans assessed but
not yet in case management are the easiest to lose. Operational stability
factors, such as transport schedules, housing curfews and shift compatibility,
live only in narrative notes, so occupational matching alone can recommend a
placement that fails on day one. The approach was first presented as a best
practice at statewide JVSG training in October 2026. Those observations
motivate the four barrier states in section 6 and the structured profile in
section 8; they are practitioner experience, not evaluated findings.

### 1.2 Constraints that drove the design
| Constraint | Consequence |
|---|---|
| Query window accepts one `SELECT` | No stored procedures, temp tables, variables or `INFORMATION_SCHEMA`; everything is CTEs and joins |
| No write access to the MIS | Output is exported files only |
| No approved automation platform | Manual or scheduled export; refresh in Excel |
| PII allowed only in the restricted SharePoint site | Git and public artifacts are synthetic-only |
| Small groups in manager views | Cell suppression below 10 |
| No staff hierarchy in the data | Staff identification by rule, not lookup |

### 1.3 Claims this paper does not make
No measured time savings, no accuracy validation of the rules, no service or
employment outcomes, no production approval, and no evidence of adoption beyond
Alabama. The query set is unvalidated and not approved for scheduling. Section 13
lists what validation would be required.

## 2. Governance and data residency

Three tiers govern every artifact (see [PII protocol](../data/pii_protocol.md)):

1. **Public/repository:** code, templates, synthetic fixtures, documentation.
2. **Restricted SharePoint:** real exports and the live workbook; a
   `restricted` folder with broken permission inheritance. Hiding a worksheet is
   not access control.
3. **Manager-visible:** aggregates only, with small-cell suppression.

Rules: State IDs are treated as direct identifiers; case-note text is never
exported by the follow-up queries; model or rule output is never an
authoritative decision. These come from [SECURITY.md](../../SECURITY.md).

## 3. Architecture

```
 MIS (read-only SQL window)
        |  single-SELECT exports, MIS-named CSV files
        v
 SharePoint library
   /manager      (suppressed summary, step 21)
   /restricted
       /worklist (veteran-level, step 17)
       /profile  (structured fields for referral brief, step 29)
        |  Power Query: newest CSV per folder, typed, validated
        v
 Excel workbook (web)
   Overview | Offices and Age | Drilldown | Watchlist | Worklist | Profile
   Office Scripts build tabs; formulas filter and rank
        |
        v
 Human reviewer: referral brief as a draft, never a decision
```

A parallel Python package performs typed intake and PII classification
([MIS intake contract](../data/mis_intake_contract.md)) and a synthetic
rehearsal dashboard ([management demo runbook](../operations/management_demo_runbook.md)).

## 4. SQL method

### 4.1 Note-based population
The population is defined by note authorship within the fiscal-year window, not
by service enrollment. The earlier service-based approach (steps 16/20)
under-counted because it started from a services table. Replacing it with a
note-based approach (steps 17/21) brought in staff who document only notes.

Population logic, in generic terms:

1. Collect notes dated inside the window (fiscal-year start to as-of date).
2. Keep notes authored by designated JVSG staff (section 4.2).
3. Reduce to one row per veteran: first note, last note, last contact, days
   since contact, assigned staff, office and area.
4. Exclude veterans with an active exclusionary enrollment in the window.
   Undated or uncertain enrollment records are **flagged, not excluded**, so
   uncertainty never silently removes someone from follow-up.
5. Derive a follow-up band (current, due soon at 15-day, overdue at 30-day
   thresholds, with the program's agreed cut points).

### 4.2 The staff-identification problem
The MIS exposes no supervisor link, no group lookup and no historical
membership. The pragmatic solution combines privilege-group membership with
job-title patterns. It is brittle: new titles or group changes silently change
the population. Mitigations: keep the rule in one CTE, reconcile against a
known roster each quarter, and document it as an assumption. The real group
codes and patterns are deliberately omitted from this paper.

### 4.3 Identifier handling
The State ID lives in a staff-independent individual table as an integer type
and is joined to the user table by username. It is cast to text in the export
and kept as text through Power Query so leading zeros survive. Worksheet
lookups compare text to text.

### 4.4 Query-window rules and offline enforcement
Because the window rejects non-conforming SQL only at run time, an offline test
suite (`tests/test_sql_window_rules.py`) enforces: one statement; no `EXEC` or
system procedures; no `*`; every output column aliased in brackets; no
`DECLARE` or temp tables; no `INFORMATION_SCHEMA`. This turned a slow
copy-paste-fail loop into a fast local check.

### 4.5 Suppression and differencing
Step 21 produces manager-level counts by office group and age band and
suppresses any group below 10. Suppression alone is defeated by differencing:
if a total and all but one group are published, the hidden cell is derivable.
Mitigations: show "Suppressed" rather than zero, keep the row-level step 17
restricted, and reconcile 17 and 21 internally (their totals must agree) without
publishing both views to the same audience.

### 4.6 Reconciliation and validation plan
Step 21 totals must equal the step 17 row counts by group. The full validation
protocol (sampled veterans reviewed by staff against the MIS screen, boundary
dates at fiscal-year start and the as-of date, exclusion edge cases) is written
but **not yet executed**. See [SQL reporting status](../sql/sql_reporting_status.md)
and [SQL runbook](../sql/sql_runbook.md).

### 4.7 Lessons from the legacy anti-join path
An earlier "veterans with no recent note" anti-join over the full export
produced header-only files because the join keys did not exist for the target
group; a minimal manual-test export (05a) confirmed the format while the full
export failed. Lesson: always ship a minimal known-good query beside the full
one, to separate format problems from logic problems.

### 4.8 Profile steps 28 and 29
Step 28 explores which structured fields exist for barriers (training,
housing, medical, legal); step 29 exports only those fields. In the first live
run the service-mapped outcome and medical columns were blank, which is why the
classifier reports **UNK** ("no structured evidence") rather than "no barrier".

## 5. ETL

### 5.1 Landing zone
MIS-style file names (`<step>_FreeFormSql_<yyyymmdd>.csv`) are preserved. One
folder per report; the query selects the **newest** file in its folder, so a
refresh is "drop a new file". Background refresh is disabled so a half-written
file is never read.

### 5.2 Power Query contracts
Each query declares its required columns and fails loudly when a header is
missing, then types every column explicitly:

- text for identifiers (State ID, username);
- datetime for first/last note and contact (the MIS emits
  `MM/DD/YYYY h:mm:ss AM`), date for other stamps;
- whole numbers for counts and day deltas;
- flags as 0/1/blank, mapped to booleans without coercing blank to false.

`SharePoint.Files` requires the **site root** URL as a parameter (no
`/_layouts/` or personal-OneDrive suffix). M text literals have no backslash
escape, so path normalization uses `Text.Replace(path, "\", "/")`.

### 5.3 Python intake
`src/jvsg_triage/etl` validates native downloads against
`data/schemas/mis_reports.v1.json`: every source column carries a PII class
and handling rule (projected, lexicon, discarded, blank), and the contract
stores layout only, never example values. Redaction removes known names from
free text before any downstream use; residual risk is documented in the PII
protocol.

### 5.4 TOON export
A compact, line-oriented export (`[N]{fields}:` header plus rows) with synthetic
row keys (`P0001`), no names or State IDs, and reviewer columns null by default.
It gives a stable, token-efficient interchange for review tools and any future
language-model step.

## 6. Classification rules

Rule set `profile-rules-v1`: four domains (training, housing, medical, legal)
by five states (CRT critical, ACT active, MIT mitigated, RES resolved, UNK
unknown). A 180-day stale threshold downgrades old evidence. The rules are
deterministic, versioned and unit-tested. Every output carries "Unverified"
until a reviewer acts. Thresholds (180/365 days) are open questions for the
program coordinator.

## 7. Excel presentation layer

- **Office Scripts** build the Overview, detail tabs and repair formulas.
  Scripts are stored outside the workbook, so they are version-controlled in
  the repository and re-attached after any rebuild.
- **Watchlist:** an `AGGREGATE(14,6,...)` helper column (hidden) ranks the
  oldest items without array entry; errors are ignored via option 6.
- **Drilldown:** `AGGREGATE(15,6,...)` returns up to 100 matching rows with
  three filters (office, band, staff) without spill dependencies.
- **Referral panel:** `XLOOKUP`, `SWITCH` and `TEXTJOIN` assemble template
  language from the structured profile.
- **Python in Excel** (cloud-executed, no network) builds the TOON text.

Design rule: formulas over macros wherever possible, so the workbook remains
inspectable by non-developers.

## 8. Referral profile

The brief maps domain states to partner-referral language **templates**. It
states what the structured data show, never what the veteran needs; a case
manager reviews and edits. Open items: whether a referral counts as training
enrollment (program owner), partner directory, and housing-instability fields.
See [referral plan](../planning/community_partner_referral_profile_plan.md) and
[setup](../operations/referral_profile_setup.md).

## 9. Privacy and security

Defense in depth: restricted folder permissions; suppression in manager views;
State ID as text; no names in exports used for rules; public artifacts
synthetic only; security review gates in SECURITY.md; third-party PDFs and
personal documents excluded from version control. Backups of the live workbook
are kept after a rebuild incident (the live workbook was once deleted and
rebuilt; the recycle bin and version history were essential).

## 10. Testing and quality assurance

- Pytest suite covering SQL window rules, Power Query required columns,
  classification rules, the dashboard demo and the demo kit generator.
- Node tests exercise the Office Scripts logic with a stubbed Excel API
  (run in CI; skipped where Node is unavailable).
- Ruff and mypy (strict) on the package; CI per
  [engineering process](../planning/engineering_process_and_mvp_sprint.md).
- Synthetic fixtures compared byte-for-byte with the generator output, so
  drift fails CI.

## 11. SharePoint development lessons

1. Site-root URLs only for Power Query connectors.
2. `.html` files in libraries download instead of rendering; use the Excel web
   part or Excel Online instead of hosting pages.
3. Newest-file-wins per folder makes refresh trivial but demands naming
   discipline.
4. Office Scripts live in the user's OneDrive, not the workbook; document and
   store them in source control.
5. Broken inheritance is the only real restriction; test with a second account.
6. Power Automate and Copilot Studio were not available; design for manual
   refresh and treat automation as an upgrade.
7. Keep a rebuild runbook ([SharePoint runbook](../operations/sharepoint_demo_site.md)).

## 12. Demonstration kit

`demo/naswa_demo/` regenerates three synthetic CSVs in the exact export shape
(invented offices, staff, usernames and `99`-prefixed IDs), ships the Power
Query and Office Script files, and documents wiring and expected counts, so
screenshots and video can be recorded without touching live data. See its
README. Default seed 3042 yields 240 worklist rows.

## 13. Limitations and validation required

| Gap | What closes it |
|---|---|
| Unvalidated population | Staff-reviewed sample against MIS screens |
| Brittle staff rule | Roster reconciliation each quarter |
| Manual delivery | IT-approved export or file transfer |
| Thresholds unconfirmed | Program owner decision |
| No outcomes data | Pilot evaluation with agreed measures |

## 14. Future direction

1. Execute the validation plan, then request approval for scheduled export.
2. Delivery options to evaluate (unverified): scheduled MIS export,
   IT-managed file transfer, read-only reporting connection.
3. Power BI for manager dashboards with row-level security, if licensed.
4. Optional serverless function for intake, kept off the critical path.
5. Language-model barrier parsing of notes: deferred until privacy review, with
   TOON as the contract and reviewer sign-off mandatory
   ([plan](../planning/toon_and_slm_barrier_dx_plan.md)).
6. Community-partner directory and closed-loop referral tracking.
7. Pilot evaluation with pre-agreed measures (contact timeliness, not
   outcomes) before any impact claim.
8. Sanitized, parameterized SQL templates and a transfer guide so other states
   can adapt the method to their own case-management systems.

## 15. Cross-reference to project documentation and deliverables

| Topic | Document or deliverable |
|---|---|
| Nomination text | [Nomination draft](nomination_draft.md) |
| Bios | [Stakeholder bios](bios.md) |
| Video and screenshots | [Script](video_script_and_screenshots.md); demo kit |
| Demo kit | `demo/naswa_demo/README.md` |
| SQL status, runbook, automation | [Status](../sql/sql_reporting_status.md), [runbook](../sql/sql_runbook.md), [automation](../sql/sql_automation_plan.md) |
| SQL publication posture | [Strategy](../sql/sql_publication_strategy.md) |
| SharePoint workbook | [Runbook](../operations/sharepoint_demo_site.md) |
| Referral profile | [Setup](../operations/referral_profile_setup.md), [plan](../planning/community_partner_referral_profile_plan.md) |
| Intake and PII | [Contract](../data/mis_intake_contract.md), [protocol](../data/pii_protocol.md) |
| Scope and approvals | [MVP scope](../planning/deliverables_and_required_inputs.md) |
| Engineering process | [Process](../planning/engineering_process_and_mvp_sprint.md) |
| TOON and SLM | [Plan](../planning/toon_and_slm_barrier_dx_plan.md) |
| Field context and recognition | Statewide JVSG training presentation (Oct 2026), agency newsletter submission and quarterly manager's report: kept in restricted `docs/source_pdfs/`; the report contains veteran names and State IDs and is never published |
| Management context | [Briefing](../planning/management_presentation_briefing.md), [demo runbook](../operations/management_demo_runbook.md) |
| Security gates | [SECURITY.md](../../SECURITY.md) |

## Appendix A. Glossary

- **JVSG:** Jobs for Veterans State Grants. **MIS:** the state case-management system.
- **TOON:** compact tabular text export. **UNK:** no structured evidence.
- **Suppression:** hiding counts below the disclosure threshold.

## Appendix B. Synthetic data dictionary (demo kit)

| Column | Type | Meaning |
|---|---|---|
| STATE_ID | text | Invented 7-digit ID starting with 99 |
| INDIVIDUAL_USERNAME | text | `demo.personNNN` |
| OFFICE_NAME / LWIA | text | Invented "Demo Office"/"Demo Area" |
| FIRST_NOTE_DATE / LAST_NOTE_DATE / LAST_CONTACT_DATE | datetime | MIS-format stamps |
| DAYS_SINCE_CONTACT | integer | Days from last contact to as-of date |
| FOLLOW_UP_BAND | text | Current, Due soon, Overdue |
| INDIVIDUALS (manager file) | integer | Group count; groups below 10 omitted |
