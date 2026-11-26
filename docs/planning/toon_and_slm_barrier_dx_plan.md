# Plan: TOON export and SLM barrier-diagnosis notes parsing

**Status: draft, November 21, 2026; demo November 30.** Builds on the live SharePoint Excel
dashboard and the existing synthetic Python package. Repository work uses
synthetic data only; veteran data stays in the JVSG SharePoint site (see
[PII protocol](../data/pii_protocol.md) and [SECURITY.md](../../SECURITY.md)).
Model output is a draft for qualified staff review, never a decision.

## Where we are

| Area | State |
|---|---|
| Live Excel dashboard (SharePoint) | Core data pull works. Some drill-down tabs are blank even with filters set. Office 365 rewrote the workbook on open. |
| `jvsg_triage.toon` | Exact tabular encode/decode for the closed synthetic `Profile` schema (`toon/demo.py`). Not a general TOON parser. |
| `jvsg_triage.slm` | Empty placeholder package. |
| `jvsg_triage.privacy.scrubber` | Local note scrubbing exists; effectiveness on real notes is unvalidated. |
| Barrier vocabulary | Closed: four domains (TRN, HSG, MED, LEG) x five states (CRT, ACT, MIT, RES, UNK). |
| Out of scope today | Case-note AI, live ingestion, write-back, automatic referrals (see [scope](./deliverables_and_required_inputs.md)). Staff-reviewed referral briefs from structured data are planned for the Nov 30 demo: [referral profile plan](./community_partner_referral_profile_plan.md). |

## Phase 0 - Stabilize the dashboard (do first, Nov 21-23)

Do not layer new features on a workbook that is partly blank.

1. **Freeze a baseline.** Save the current SharePoint version history entry,
   then make a copy named with the date. Work only on the copy.
2. **Diagnose blank drill-down tabs.** Check in this order, in desktop Excel
   (not Excel for the web):
   - Data > Queries & Connections: any query erroring or set to "load to
     connection only"? Refresh All and read the error.
   - PivotTables/slicers: Analyze > Refresh; confirm each slicer's Report
     Connections still point at the drill-down pivots/tables. A rewrite on
     upgrade often drops slicer links or leaves stale pivot caches.
   - Filter source: drill-down tables referencing a filter cell or slicer
     that now resolves to a different table/name (Formulas > Name Manager,
     look for `#REF!` or duplicated names with `_xlfn`/`_xlpm` prefixes).
   - Formulas rewritten as dynamic arrays (`@` inserted, spill `#SPILL!`) or
     `FILTER`/`XLOOKUP` results now blocked by adjacent cells.
   - Data types: join keys (State ID is `dbo.indstaff.stateid`, bigint) coming
     through as text in one place and number in another produce empty matches.
3. **Fix and document** each cause in a short change log kept in SharePoint.
4. **Add a smoke check tab** ("Checks"): row counts per source query vs. each
   drill-down, report date, and a red/green status. This is the same
   reconciliation idea the Python demo already uses.
5. **Exit criteria:** every drill-down shows data for at least three filter
   combinations; workbook opens without a repair prompt in desktop and web.

## Phase 1 - TOON as the stable interchange format (about 1 week)

Purpose: a compact, deterministic, lossless table format between the SQL
reports, the Python processors and the dashboard, and later the SLM input.

1. **Generalize the schema layer.** Keep `toon/demo.py` for the demo; add a
   schema-driven `toon/codec.py` (typed, deterministic) that encodes/decodes
   any declared flat table with proper quoting of commas, newlines and
   `null`. Reject unknown fields and noncanonical text, as today.
2. **Define two schemas** in `data/schemas/`: `profile` (existing) and
   `barrier_findings` (Phase 2 output): `demo_id, domain, state,
   evidence_id, evidence_quote, confidence, verification_status,
   reviewer_action, reviewer_role, reviewed_on`.
3. **Tests (synthetic):** round trip, quoting edge cases, empty table, row
   count mismatch, noncanonical input, column order.
4. **Dashboard hook, no new services:** Python writes `profiles.toon` and
   `barrier_findings.toon` plus an `.xlsx` snapshot; the operator uploads the
   `.xlsx` to the SharePoint library and the dashboard reads it via Power
   Query (Excel's built-in connector). TOON is the audit/exchange artifact;
   Excel stays the display layer until a pilot is approved.
5. **Exit criteria:** `ruff`, `mypy src`, `pytest` green; the same input
   always yields byte-identical output.

## Phase 2 - SLM parsing of notes for barrier diagnoses (about 2-3 weeks)

Treat as a draft-suggestion pipeline: **scrub locally, extract, validate,
queue for human review.**

1. **Governance gate (blocking, start now in parallel).** Per the scope
   checklist, obtain approval for purpose, model/host, minimum schema,
   retention, and logging. Use a private, in-tenant or on-device SLM; no
   public API for case notes. Record approvals in the agency governance
   location, not in this repo.
2. **Closed output contract.** The model may only emit JSON/TOON rows using
   the existing vocabulary (domain in TRN/HSG/MED/LEG, state in
   CRT/ACT/MIT/RES/UNK) plus a note-span reference. No free text, names or
   identifiers in output. Anything outside the contract is rejected, not
   repaired.

   **Verification contract (mandatory).** Every SLM output is a *claim to
   verify*, not a recorded barrier. The model may misread a note (negation,
   past vs. current, another person mentioned, ambiguous wording) and
   mislabel a barrier, so:
   - Each finding must carry a verbatim evidence quote and its location in
     the scrubbed note, so the reviewer can check it against the source in
     one step. Findings without checkable evidence are rejected.
   - Findings enter as `Unverified`. No dashboard count, follow-up band,
     referral or profile field uses a finding until a qualified human sets
     it to `Confirmed`. Reviewers may `Confirm`, `Correct` (change domain or
     state) or `Reject`; the original model claim, the reviewer's action,
     role and date are kept for audit.
   - Verification cannot be skipped by configuration, batch action or
     confidence score. High confidence never bypasses review; `CRT` findings
     are surfaced first.
   - Reruns never overwrite a Confirmed, Corrected or Rejected finding.
   - Track the reviewer reject/correct rate as the operational accuracy
     measure; a rising rate pauses use of the extractor.
3. **Pipeline in `jvsg_triage.slm`:**
   - `prompt.py`: fixed instructions and few-shot examples built from
     synthetic notes only (`data/synthetic/fy2026_case_notes.*`).
   - `client.py`: an optional adapter behind a protocol; no network at
     import or in tests; a deterministic fake client for tests.
   - `extract.py`: scrubbed note in, validated `barrier_findings` rows out;
     default to `UNK` when unsure; every finding keeps an evidence pointer.
   - `review.py`: findings start as `Unverified`; only a human action moves
     them to `Confirmed`, `Corrected` or `Rejected`. Reviewed values are
     never overwritten by reruns, and unverified findings are excluded from
     all official outputs.
4. **Baseline first.** Build a rules/keyword extractor over the same
   contract as the comparison baseline; the SLM must beat it on the
   synthetic labels (`fy2026_case_notes.pii_labels.jsonl` pattern) before any
   pilot use.
5. **Evaluation.** Per-domain precision/recall and a confusion matrix on
   synthetic data; high-severity (CRT) misses are tracked separately. Real
   validation happens only inside SharePoint/approved storage under an
   authorized pilot; metrics from real cohorts stay out of the repo.
6. **Tests:** unverified findings excluded from counts, no path to Confirmed without a human action, evidence quote must match the scrubbed note, contract rejection of malformed/out-of-vocabulary output,
   scrub-before-model ordering, no-network guarantee, idempotent reruns,
   reviewed rows preserved, empty/very long notes.
7. **Dashboard integration:** a "Barrier findings (draft)" drill-down tab
   fed by `barrier_findings`, labelled "AI-suggested, awaiting staff
   review", with filters for domain, state and review status. Never mix
   suggestions into the official profile counts until reviewed.

## Phase 3 - Pilot readiness (after Phases 1-2 and approvals)

- Single authorized team, manual paired upload, receipt and operator log.
- Measure: prep time, corrections made by staff, share of findings accepted,
  missed CRT barriers, timeliness of follow-up.
- Only then consider Azure Functions (`azure_functions/` is reserved) or
  Power Automate, each with its own security review.

## Sequencing for the November 30 demo (9 days)

Only Phase 0 and a synthetic-data slice of Phases 1-2 fit. The live SLM
adapter and pilot work do not, and should be shown as roadmap, not capability.

| Dates | Work | Demo outcome |
|---|---|---|
| Nov 21-23 | Phase 0: diagnose and repair blank drill-down tabs; add "Checks" tab. Open SLM governance requests. | Dashboard drills down reliably. |
| Nov 24-25 | Phase 1 slice: generic TOON codec for `profile` and `barrier_findings`, round-trip tests, snapshot export. | TOON export shown on synthetic data. |
| Nov 26-27 | Phase 2 slice: closed output contract, rules-based baseline extractor, deterministic fake client, synthetic evaluation. | "Draft barrier findings" tab on synthetic notes, labelled awaiting staff review. |
| Nov 28 | Freeze. Full `ruff`, `mypy src`, `pytest`; rehearse per the runbook; keep a verified offline copy. | Rehearsed, reproducible demo. |
| Nov 29-30 | Buffer and final rehearsal only; no new features. | |

**Cut order if time slips:** (1) SLM dashboard tab, (2) generic codec
(keep the existing profile TOON), (3) never cut Phase 0.

**Demo framing:** the Nov 30 demo is planned on the live FY2026 CSV in the
JVSG SharePoint site. Live data stays inside that site and the Microsoft 365
tenant; nothing is committed to this repo, and tests stay synthetic. Show
barrier findings only as `Unverified` suggestions with quoted evidence (see
the verification contract), and do not claim accuracy figures.

## Running a function against the live data (tenant-only options)

> **Superseded Nov 25-26, 2026:** `=COPILOT`, Power Automate and Copilot Studio
> are not licensed, and third-party hosts are rejected for identified data. The
> Nov 30 demo uses the rules baseline and templates only, with no model. The
> table below is kept as the options analysis; current decisions are in the
> [referral profile plan](./community_partner_referral_profile_plan.md).

Which "Copilot" matters. **GitHub Copilot Enterprise** is a coding assistant;
it is not a hosted service to call from a workbook, and sending live notes to
it or to GitHub Models is outside the tenant boundary. Use **Microsoft 365
Copilot** or a tenant-hosted model instead.

| Option | How it is called | Fit |
|---|---|---|
| Excel `=COPILOT(prompt, range)` (M365 Copilot license) | Worksheet function over note cells, e.g. returning a domain/state/quote per row | Fastest demo path. Non-deterministic, rate-limited and not suited to bulk rows; use on a small reviewed sample. Confirm availability on your Excel channel. |
| Office Script (TypeScript) + Power Automate | Script reads/writes the SharePoint workbook; the flow calls an approved tenant model (e.g. AI Builder or Azure OpenAI in the tenant) and writes `Unverified` rows | Repeatable and auditable; best for the full file. Needs flow/connector approval. |
| Python pipeline in this repo | Run locally on the CSV, scrub, extract | Only where IT/security permits live data on that machine; Codespaces must never hold live records (SECURITY.md). |

Recommended for Nov 30: keep the same output columns as `barrier_findings`
(`evidence_quote`, `verification_status = Unverified`, reviewer columns) on a
"Barrier findings (draft)" sheet. Run a limited sample of notes through
`=COPILOT` or the Office Script flow, keep every row unverified, and have a
qualified reviewer Confirm/Correct/Reject in the sheet during the demo. A
SharePoint-side scrub (strip names, SIDs, phones) must run before any note
reaches a model; the Python scrubber does not run in Excel, so port its rules
to the Office Script or confirm M365 Copilot's tenant data handling is
approved for case notes. Get written approval from the privacy/IT owners
before the demo; the scope checklist still lists case-note AI as unapproved.

Implementation: the Office Script, offline tests and flow build guide are in
[`m365/`](../../src/jvsg_triage/m365/README.md).

## Python in Excel (web) strategy - approved Nov 25, implemented, not yet run in Excel

**Status: approved Nov 25, 2026 (Python guard rails only).** Approved: Python for scrub/validate/TOON; Python in Excel cloud container acceptable for note text. `=COPILOT` is not available, so **no model step**: rules baseline only, SLM shown as roadmap. Implemented in [`m365/excel_python/`](../../src/jvsg_triage/m365/excel_python/README.md) (tests: `tests/test_excel_python_cells.py`). Not yet run inside Excel.

**Original proposal:** Applies to Formulas > Insert
Python in Excel for the web.

### Findings

- **Python in Excel cannot call Copilot or any model.** It runs in an isolated
  Microsoft cloud container with no internet or network access, no local files
  and no secrets/credentials, and only the preinstalled Anaconda package set
  (no `pip install`). `requests`, GitHub Models and Azure OpenAI calls all fail
  by design. There is no `=PY()` bridge to Copilot.
- **`=COPILOT()` is a separate worksheet function** and runs outside Python.
  The two combine only through cells: `=COPILOT(...)` writes cells, then a
  `=PY(xl("Table[col]"))` cell reads those cells (and vice versa).
- Python in Excel sends the referenced data to Microsoft's cloud container.
  This is inside the M365 tenant, but it still needs the same privacy/IT
  approval as `=COPILOT` before it touches live notes.
- The repo package `jvsg_triage` cannot be imported there. Code must be
  self-contained, pasted into cells (stdlib + pandas only; Polars is not in
  the Excel Python set).

### Recommended split

| Step | Where | Tool |
|---|---|---|
| 1. Scrub notes (names, SIDs, phones) | Excel Python cell | Small pasted regex function ported from `privacy/scrubber`; deterministic. |
| 2. Suggest domain/state/quote | Worksheet | `=COPILOT(prompt, scrubbed_range)` on a small sample (M365 Copilot licence), or the Office Script/Power Automate flow in `m365/` for bulk. |
| 3. Validate against the closed contract | Excel Python cell | Reject anything outside TRN/HSG/MED/LEG x CRT/ACT/MIT/RES/UNK, or whose `evidence_quote` is not a verbatim substring of the scrubbed note. Rejected, never repaired. Mark rest `Unverified`. |
| 4. TOON output | Excel Python cell | Pasted deterministic encoder for `barrier_findings` (header, row count, quoted fields) returned as one text cell; the operator saves it to the SharePoint library as the audit artifact. |
| 5. Human review | Sheet | Confirm/Correct/Reject columns per the verification contract. |

Python is the deterministic guard rails (scrub, validate, TOON); the model call
stays in `=COPILOT` or the flow. A rules/keyword baseline can also run in
Python in Excel with no model at all, which is the safest fallback demo.

### Alternative SLM strategy

If `=COPILOT` is unavailable or not approved for case notes: run only the
rules baseline in Python in Excel, and show the SLM as roadmap using an
approved in-tenant model (Azure OpenAI/AI Builder via Power Automate).

### Proposed next steps (on approval)

1. Add `src/jvsg_triage/m365/excel_python/` with single-file, stdlib-only
   cells (`scrub.py`, `validate.py`, `toon_encode.py`) plus offline tests that
   exec them against synthetic notes only, so the pasted code is tested.
2. Provide paste-ready cell instructions and a synthetic sample sheet.
3. Confirm availability of Python in Excel and `=COPILOT` on your tenant, and
   get written privacy/IT approval before any live note is used.

### Decisions (resolved Nov 25)

1. Python = scrub/validate/TOON: approved.
2. `=COPILOT`: not available; rules baseline only.
3. Python in Excel cloud container for note text: acceptable.

## Risks

| Risk | Mitigation |
|---|---|
| Upgrade rewrites break the workbook again | Dated copies, "Checks" tab, desktop Excel for edits. |
| Scrubber misses identifiers before the model | Local scrub plus approved in-tenant model only; pilot validation before use. |
| Model suggestions treated as decisions | Mandatory verification contract: Unverified until a human confirms against quoted evidence; labelled UI; CRT never auto-actioned. |
| Schema drift across SQL, TOON and Excel | Versioned schemas and round-trip tests in CI. |

## Open questions

1. Which SLM host is approvable (in-tenant Azure, on-device, other)?
2. Who are the qualified reviewers for AI-suggested barrier findings?
3. Do barrier diagnoses extend beyond the four current domains?
