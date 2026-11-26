# From Case Notes to Follow-Up Visibility: Auditable ETL, SQL, and SharePoint Engineering for the Alabama JVSG Program

**Technical White Paper | Supporting the 2027 NASWA Merrill Baumgardner Innovation in Information Technology Award Nomination**

* **Author:** Keith Battle, Workforce Specialist – Veteran Services (Lead Architect & Developer)
* **Contributors:** See [Stakeholder Biographies](stakeholder_biographies_naswa_submission.md)
* **Publication Posture:** Written for public release; pending final sanitization review and approvals. This document contains zero PII, veteran records, live staff names, or proprietary database schemas. All database objects, privilege groups, and title patterns use generic abstractions (see [SQL Publication Strategy](../sql/sql_publication_strategy.md)), and all metrics derive from a deterministic synthetic demonstration dataset.

---

## Abstract

Jobs for Veterans State Grant (JVSG) specialists routinely document outreach and barrier-resolution work as free-text case notes inside state Management Information Systems (MIS). Because native MIS reporting typically anchors on formal service enrollments rather than narrative note activity, frontline staff and managers lack visibility into which veterans have gone too long without follow-up contact. We present a low-cost, auditable data-engineering pipeline built entirely within existing enterprise constraints: read-only, single-statement SQL access, no external automation orchestrator, and strict Personally Identifiable Information (PII) boundaries. The pipeline (1) defines the active veteran population via note authorship using constrained Common Table Expressions (CTEs), (2) routes typed CSV exports into permission-isolated SharePoint libraries, (3) validates and transforms schemas deterministically via Power Query, and (4) delivers dual-tier dashboards in Excel Online powered by Office Scripts and non-volatile worksheet formulas. A rule-based barrier classifier and fixed-template community referral brief assist qualified staff while enforcing strict human-in-the-loop governance. We detail the architectural trade-offs, privacy controls, automated testing harness, and explicit validation boundaries of the prototype.

---

## 1. Operational Problem and Engineering Constraints

### 1.1 Reframing Population Visibility Around Note Activity
In state workforce case-management platforms, narrative case notes serve as the primary record of frontline veteran engagement. However, standard operational reports query formal service tables—rendering veterans invisible when staff document intake triage, employer outreach, or barrier stabilization solely through notes. To answer the fundamental operational question—*"Which veterans in my caseload have exceeded contact-timeliness thresholds?"*—this architecture shifts the population anchor from **service enrollment** to **note authorship**: a veteran enters the active follow-up cohort when an authorized JVSG staff member authors a case note within the current fiscal year.

### 1.2 Field Origins
The engineering design emerged directly from frontline operations in Mobile, Alabama, where a two-person JVSG team (a Workforce Specialist and a Local Veterans' Employment Representative) identified three recurring failure modes:
1. **Intake Attrition:** Veterans assessed at initial contact but not yet enrolled in intensive case management lacked automated tracking and were easily lost between manual spreadsheet reviews.
2. **Unstructured Stability Risks:** Operational employment barriers—such as transit schedules, transitional housing curfews, legal obligations, and shift compatibility—resided solely in narrative notes. Matching a veteran to an employer based solely on occupational codes risked day-one placement failure if underlying stability barriers were overlooked.

3. **Case-Management-to-Business-Services Handoff:** The Workforce Specialist (veteran case management) and the Workforce Outreach Specialist (business development) lacked a shared, quickly readable view of the same veterans, so employer outreach could not easily target veterans ready for placement. Making case-management data accessible to both roles is an explicit design goal.

These practitioner insights—first shared at statewide JVSG training in October 2026—motivated the deterministic four-domain barrier model (Section 6) and structured referral brief (Section 8). They represent field-informed design hypotheses rather than empirically evaluated outcomes.

### 1.3 Architectural Constraints
Every technical decision was shaped by six non-negotiable institutional boundaries:

| Institutional Constraint | Architectural Consequence |
|---|---|
| **Single-`SELECT` Query Window** | No stored procedures, temporary tables, local variables, or `INFORMATION_SCHEMA` queries; all logic is encapsulated in standard CTEs and joins. |
| **Read-Only MIS Access** | Zero write-back to the state database; integration occurs strictly via structured file exports. |
| **No Enterprise Orchestrator** | Power Automate and Copilot Studio were unavailable; refreshes rely on deterministic file drops and user-triggered Power Query execution. |
| **Strict PII Residency Tiers** | Live PII is restricted exclusively to access-controlled SharePoint libraries; Git repositories and public artifacts use synthetic data only. |
| **Small-Cell Disclosure Risk** | Manager-facing aggregates enforce small-cell suppression ($n < 10$) to prevent indirect re-identification. |
| **Absent Org-Chart Metadata** | The MIS lacks hierarchical supervisor tables; JVSG staff scope is resolved via explicit privilege-group and title rules. |

### 1.4 Scope and Non-Claims
To maintain rigorous technical transparency, this paper claims **no** measured staff time savings, **no** formal accuracy validation of classification thresholds, **no** causal impact on veteran employment outcomes, and **no** production scheduling approval. Section 13 defines the formal validation protocol required prior to operational scaling.

---

## 2. Data Governance and Three-Tier Residency Model

Data security is enforced structurally across three isolated storage tiers (governed by [SECURITY.md](../../SECURITY.md) and the [PII Protocol](../data/pii_protocol.md)):

1. **Tier 1 — Public / Source Control:** Contains application code, Power Query scripts, Office Scripts, schema contracts, documentation, and synthetic data generators. Zero live data or third-party PDFs are permitted.
2. **Tier 2 — Restricted Operational SharePoint:** Houses live CSV exports and the production Excel workbook inside a dedicated `/restricted` folder with broken permission inheritance restricted strictly to authorized JVSG personnel. Worksheet hiding is treated as a UI convenience, never a security boundary.
3. **Tier 3 — Manager Aggregate Layer:** Exposes de-identified, cell-suppressed summary counts (`step 21`) to leadership without row-level veteran access.

**Core Privacy Invariants:** State IDs are treated as direct identifiers; free-text case notes are never exported by follow-up queries; and rule-based outputs serve strictly as advisory drafts requiring human verification.

---

## 3. System Architecture

```text
+-------------------------------------------------------------------+
| State MIS (Read-Only Single-SELECT SQL Window)                    |
|   -> Exports typed, MIS-named CSV snapshots                       |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| Access-Controlled SharePoint Document Library                     |
|   |-- /manager/    (Suppressed aggregate counts: Step 21)         |
|   +-- /restricted/ (Broken permission inheritance)                |
|         |-- /worklist/ (Veteran follow-up cohort: Step 17)        |
|         +-- /profile/  (Structured barrier fields: Step 29)       |
+---------------------------------+---------------------------------+
                                  |  Power Query (Newest file per
                                  |  folder, strict schema typing)
                                  v
+-------------------------------------------------------------------+
| Excel Online Presentation Layer                                   |
|   [Overview] [Offices & Age] [Drilldown] [Watchlist]              |
|   [Worklist] [Profile]                                            |
|   -> Office Scripts construct tabs; non-volatile formulas rank,   |
|      filter, and assemble template referral briefs                |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| Human-in-the-Loop Case Manager Review                             |
|   -> Staff verify MIS records, edit brief, and execute outreach   |
+-------------------------------------------------------------------+
```

A companion Python package (`src/jvsg_triage/`) provides offline schema validation, PII classification, and deterministic synthetic dataset generation (`demo/naswa_demo/`) for CI testing and public demonstrations.

---

## 4. Read-Only SQL Extraction Method

### 4.1 Note-Anchored Cohort Definition
Legacy queries (`Steps 16/20`) initiated joins from service-enrollment tables, systematically omitting veterans whose interactions existed solely as case notes. The redesigned queries (`Steps 17/21`) invert this logic:
1. **Window Filtering:** Extract case notes dated between the fiscal-year start and the report as-of date.
2. **Author Scoping:** Retain notes authored by designated JVSG staff (Section 4.2).
3. **Veteran Deduplication:** Collapse note events to one record per veteran, computing `FIRST_JVSG_NOTE_DATE`, `LAST_JVSG_NOTE_DATE`, `LAST_CONTACT_DATE`, `DAYS_SINCE_CONTACT`, assigned staff, office, and Local Workforce Investment Area (LWIA).
4. **Fail-Safe Exclusion Logic:** Veterans with confirmed exclusionary enrollments are filtered out, whereas records with undated or ambiguous enrollment statuses are **flagged rather than excluded**—ensuring data ambiguity never silently drops a veteran from follow-up.
5. **Timeliness Banding:** Assign deterministic follow-up bands (`Current`, `Due soon` at $\ge 15$ days, `Overdue` at $\ge 30$ days, aligned to program thresholds).

### 4.2 Resolving Staff Scope Without Org-Chart Tables
Because the MIS exposes no supervisor hierarchy or historical group-membership table, JVSG staff identification combines privilege-group codes with job-title pattern matching. Recognizing that title changes can silently alter cohort boundaries, the logic is isolated inside a single CTE, documented as an explicit assumption, and scheduled for quarterly reconciliation against human-resources rosters.

### 4.3 Identifier Preservation
State IDs reside as integers in individual demographic tables and join to staff records via usernames. Queries explicitly cast State IDs to character strings upon export, and Power Query enforces `type text` throughout ingestion—preventing spreadsheet auto-formatting from stripping leading zeros and ensuring exact text-to-text worksheet lookups.

### 4.4 Offline SQL Window Enforcement
Because the MIS query interface rejects non-compliant SQL only at runtime, an automated Pytest suite (`tests/test_sql_window_rules.py`) validates every query statically before deployment: enforcing a single `SELECT` statement, prohibiting `EXEC`, `DECLARE`, temporary tables, `SELECT *`, and `INFORMATION_SCHEMA`, and requiring bracketed column aliases.

### 4.5 Small-Cell Suppression and Differencing Protection
Manager summaries (`Step 21`) aggregate counts by office group and age band, suppressing cells where $n < 10$. To mitigate **differencing attacks**—where a hidden cell value can be deduced by subtracting visible rows from a grand total—the pipeline renders `"Suppressed"` string literals rather than zeros, isolates row-level worklists (`Step 17`) inside restricted folders, and enforces internal total reconciliation without co-publishing granular and aggregate tables to the same audience.

### 4.6 Structured Barrier Extraction (`Steps 28–29`)
Exploratory query `Step 28` audits structured demographic and intake fields across four barrier domains (training, housing, medical, legal), while `Step 29` exports only validated non-narrative columns. Where upstream structured fields are unpopulated, the classifier explicitly assigns `UNK` (*no structured evidence*) rather than falsely implying the absence of a barrier.

---

## 5. Deterministic ETL and Schema Contracts

### 5.1 Drop-Folder Ingestion Pattern
Preserving native MIS export filenames (`<step>_FreeFormSql_<yyyymmdd>.csv`), each report lands in a dedicated SharePoint subfolder. Power Query programmatically selects the **newest file** per folder based on timestamp metadata—reducing operational refreshes to a single file upload. Background refresh is disabled to prevent race conditions against partially uploaded files.

### 5.2 Strict Power Query Typing
Every Power Query script validates required column headers upon ingestion—failing loudly on schema drift rather than propagating silent `null` errors—and applies explicit type casts:
* **Identifiers:** `type text` (`STATE_ID`, `INDIVIDUAL_USERNAME`)
* **Timestamps:** `type datetime` parsed explicitly from MIS `MM/DD/YYYY h:mm:ss AM` strings
* **Metrics:** `Int64.Type` for day deltas and counts
* **Tri-State Flags:** Source `0`/`1`/blank values mapped cleanly to nullable booleans without coercing missing values to `false`.

### 5.3 Python Intake & TOON Interchange Format
For offline validation and future extensibility, `src/jvsg_triage/etl` validates exports against `data/schemas/mis_reports.v1.json`, tagging every field with a PII classification (`projected`, `lexicon`, `discarded`, `blank`). A compact, line-oriented interchange format (**TOON**: `[N]{fields}:` header plus synthetic-keyed rows `P0001` stripped of names and State IDs) provides a token-efficient, privacy-preserving payload for structured review tools.

---

## 6. Deterministic Classification Rules

The rule engine (`profile-rules-v1`) evaluates four barrier domains (**Training, Housing, Medical, Legal**) across five mutually exclusive states:
* `CRT` (Critical)
* `ACT` (Active)
* `MIT` (Mitigated)
* `RES` (Resolved)
* `UNK` (Unknown / No structured evidence)

A 180-day staleness threshold automatically downgrades aging structured evidence so outdated records are never treated as current. All classifications are deterministic, version-controlled, unit-tested, and stamped `"Unverified"` until reviewed by a case manager.

---

## 7. Excel Online Presentation Layer

To ensure maintainability by agency analysts without requiring proprietary BI licenses, the presentation layer follows a **formulas-over-macros** architecture:
* **Office Scripts:** Stored externally in version control and attached to the workbook to construct layout tabs, apply conditional formatting, and repair formula ranges after rebuilds.
* **Non-Volatile Ranking & Filtering:** Hidden helper columns utilize `AGGREGATE(14, 6, ...)` and `AGGREGATE(15, 6, ...)` to rank overdue veterans and filter up to 100 drilldown records across three parameters (Office, Follow-Up Band, Staff) without fragile legacy CSE array formulas or Excel version spill conflicts.
* **Dynamic Referral Assembly:** `XLOOKUP`, `SWITCH`, and `TEXTJOIN` dynamically assemble standardized partner-referral language from the veteran's structured barrier states.

---

## 8. Human-in-the-Loop Referral Brief

The referral panel maps structured barrier states to standardized partner-referral **templates**. By design, the output reports only what structured intake fields indicate—never diagnosing clinical needs or prescribing services. Qualified JVSG staff review the draft against live MIS case notes, edit the text as appropriate, and manually initiate partner contact.

---

## 9. Privacy, Security, and Operational Resilience

Defense in depth is maintained through broken SharePoint permission inheritance, small-cell suppression, text-typed identifiers, PII-free public repositories, and documented disaster-recovery procedures (validated during development when an accidental workbook deletion was cleanly restored via SharePoint version history and externalized Office Scripts).

---

## 10. Automated Testing and Quality Assurance

* **Pytest Suite:** Enforces SQL window compliance, Power Query column contracts, deterministic classification logic, and dashboard fixture parity.
* **Node.js Harness:** Executes Office Scripts logic against a stubbed Excel API in Continuous Integration (CI).
* **Static Analysis:** Enforces strict `mypy` type checking and `ruff` linting across the Python codebase.
* **Deterministic Fixtures:** CI verifies byte-for-byte parity between synthetic generator outputs and committed test fixtures.

---

## 11. SharePoint Engineering Lessons Learned

1. **Connector Root Discipline:** `SharePoint.Files` requires the exact site-root URL; passing `/_layouts/` or personal OneDrive paths causes authentication failures.
2. **M Literal Escaping:** Power Query M strings lack backslash escape sequences, requiring explicit `Text.Replace(path, "\", "/")` normalization.
3. **HTML Rendering Constraints:** SharePoint document libraries force `.html` downloads rather than inline rendering; Excel Online web parts provide native browser interactivity.
4. **Externalized Scripts:** Because Office Scripts reside in user OneDrive storage rather than inside `.xlsx` containers, storing scripts in Git is essential for team continuity.
5. **Permission Verification:** Always validate broken permission inheritance using a secondary non-admin test account.

---

## 12. Reproducible Demonstration Kit

The repository ships a self-contained demonstration kit (`demo/naswa_demo/`) that generates three synthetic CSV exports (`seed=3042`, yielding 240 synthetic veteran rows with `99`-prefixed IDs, `demo.personNNN` usernames, and fictional offices) alongside Power Query and Office Script files—enabling full end-to-end training, screenshots, and video capture with zero exposure of live veteran data.

---

## 13. Limitations and Validation Roadmap

| Current Limitation | Validation / Engineering Action Required |
|---|---|
| **Unvalidated Cohort Boundaries** | Audit a stratified sample of `Step 17` rows against live MIS screens to verify inclusion/exclusion edge cases. |
| **Heuristic Staff Identification** | Reconcile privilege-group/title CTE rules quarterly against official JVSG personnel rosters. |
| **Manual File Exports** | Partner with agency IT/MIS to transition from manual uploads to scheduled, encrypted file drops. |
| **Unconfirmed Staleness Thresholds** | Obtain formal sign-off from the State JVSG Coordinator on 15/30-day contact and 180-day barrier thresholds. |
| **Unmeasured Operational Outcomes** | Conduct a time-boxed pilot measuring prep-time reduction and follow-up timeliness before claiming impact. |

---

## 14. Future Roadmap

1. **Formal Validation & Scheduled Ingestion:** Complete the MIS screen audit and seek IT authorization for automated read-only exports.
2. **Enterprise BI Scaling:** Evaluate migration of aggregate manager views to Power BI with Row-Level Security (RLS) if licensing expands.
3. **Privacy-Gated NLP Exploration:** Evaluate local/private Small Language Models (SLMs) for structured barrier extraction using the de-identified TOON contract—strictly deferred until formal privacy review and mandatory human sign-off ([TOON & SLM Plan](../planning/toon_and_slm_barrier_dx_plan.md)).
4. **Cross-State Transfer Package:** Publish parameterized SQL templates and an implementation guide for fellow NASWA member agencies.

---

## Appendix A. Glossary

* **CTE:** Common Table Expression (modular SQL subquery block).
* **JVSG:** Jobs for Veterans State Grants (U.S. Department of Labor VETS program).
* **LVER:** Local Veterans' Employment Representative.
* **MIS:** State Management Information System (GeoSol).
* **TOON:** Token-Oriented Object Notation (compact, de-identified tabular interchange format).
* **UNK:** Unknown state (indicates no structured evidence in source fields).

## Appendix B. Synthetic Data Dictionary (`demo/naswa_demo/`)

| Column Name | Data Type | Description |
|---|---|---|
| `STATE_ID` | `text` | Synthetic 7-digit identifier prefixed with `99` |
| `INDIVIDUAL_USERNAME` | `text` | Synthetic handle (`demo.personNNN`) |
| `OFFICE_NAME` / `LWIA` | `text` | Fictional office and workforce area labels |
| `FIRST_JVSG_NOTE_DATE` | `datetime` | Timestamp of initial JVSG note in fiscal year |
| `LAST_JVSG_NOTE_DATE` | `datetime` | Timestamp of most recent JVSG note |
| `LAST_CONTACT_DATE` | `datetime` | Timestamp of most recent qualifying veteran contact |
| `DAYS_SINCE_CONTACT` | `integer` | Elapsed calendar days from `LAST_CONTACT_DATE` to report date |
| `FOLLOW_UP_BAND` | `text` | Deterministic timeliness tier (`Current`, `Due soon`, `Overdue`) |
| `INDIVIDUALS` *(Step 21)* | `integer` | Aggregate cohort count; groups with $n < 10$ suppressed |