# Plan: community-partner referral profile ("warm handoff packet")

**Status: decisions made November 26, 2026 for the November 30 demo (Option A, templates only).** Builds on the working
SharePoint dashboard (`src/jvsg_triage/m365/sharepoint_demo`). The
`excel_python` cells exist with offline tests but have not yet been run inside Excel. Repository work stays synthetic; real
veteran data stays in the JVSG SharePoint site ([PII protocol](../data/pii_protocol.md)).
Referral decisions stay with qualified staff; any generated text is a draft.

## 1. Framing

The dashboard answers "who is in the hardest-to-place cohort". The next
question (Hank's) is "what do we do for them". Decided answer: every veteran
in the cohort gets, at minimum, a staff-reviewed referral to a community
partner that can stabilize barriers.

A warm handoff needs two different documents:

| Document | Audience | Content | Release |
|---|---|---|---|
| **Staff referral brief** | JVSG staff / DVOP | Last-known-good profile, data freshness, suggested partner categories | Internal, SharePoint only |
| **Partner referral sheet** | Community partner | Minimum necessary subset (name, contact, stated need, requested service, staff contact) | Only with the veteran's documented consent / release |

Confirm with agency privacy/legal: release-of-information requirements for
sharing with non-agency partners, and any restriction on reusing data from
state systems. Generate the partner sheet only after consent is recorded.

## 2. Structured "last known good" profile instead of note scanning

Recommended for v1. Reasons: deterministic and auditable, no model risk, fits
337 veterans, avoids the unvalidated scrubber on real notes, and does not
depend on a governance approval for note-level AI.

Profile fields, each carried with **value, as-of date, source table.column**
so staleness is visible (exact columns to be mapped from `docs/AW_table_schema.txt`;
State ID is `dbo.indstaff.stateid`, per existing notes):

- Identity and contact: name, phone/email/address, date contact info last
  updated, county and local office, assigned staff.
- Last employment: employer, occupation, wage, separation date.
- Last positive outcome: last completed training, credential, placement, or
  successful service.
- Last service/activity and its date; last staff contact date (date only,
  not note text); days since contact.
- Structured barrier indicators: homelessness, disability, SBE designation,
  justice involvement, limited English, and similar flags that exist as
  fields.
- Case status: enrollment, plan, closure/exit state.
- Barrier domain mapping to the existing closed vocabulary (TRN, HSG, MED,
  LEG) where a structured field supports it; otherwise `UNK`.

Output per veteran: one wide row (for Excel) plus a rendered one-page brief.
Case notes stay optional: later, staff may open the notes for a single veteran
themselves; bulk note mining waits on the Phase 2 governance gate in the
[TOON/SLM plan](./toon_and_slm_barrier_dx_plan.md).

## 3. Stored procedures: probably not the right tool

- The MIS query window allows SELECT only: no EXEC, no `sp_`. A procedure
  could not be created or run from there.
- Creating objects in the vendor database needs the vendor/DBA, may be
  unsupported, and creates a maintenance and change-control burden.

Recommended: the same pattern as the existing reports (`sql/04`-`21`): a
**read-only SELECT** keyed to the cohort's State IDs (or joined to the cohort
logic), run in the query window, exported to the JVSG SharePoint library. If
IT later offers a supported view or scheduled export, the same SELECT moves
there unchanged. Keep the SQL in the restricted location chosen under
[sql_publication_strategy.md](../sql_publication_strategy.md), not the public repo.

Query design: one query per source area (employment, services, contact,
flags) returning long format `(stateid, field, value, as_of_date, source)`;
pivot to wide in Power Query or Python. This keeps each query simple enough
for the query-window limits and makes provenance explicit.

## 4. Decision tree: generating the brief

Constraint: Excel on SharePoint (web) runs in Microsoft's cloud and cannot
reach `localhost` or a staff PC. Decisions, in order:

| Option | Decision | Reason |
|---|---|---|
| **A. Templates only (no model)** in Office Script or formulas | **Chosen for the Nov 30 demo** | Works under current licenses and permissions; no installs, no new data flow. |
| B. Local Python/SLM on a staff laptop, via the synced SharePoint folder | Deferred | Needs IT approval of per-user Python and a named model (the laptop has no admin rights; application control may block it), disk-encryption and synced-PII confirmation, and model governance sign-off. Wording polish only. |
| C. VBA in a desktop `.xlsm` calling a local model | Fallback only | Desktop Excel only; macro-enabled files need IT approval. |
| D. In-tenant Azure Function called by an Office Script | Post-pilot | Needs IT hosting, managed identity and app registration; `azure_functions/` is reserved but not implemented. |
| E. Modal, GitHub-hosted or other third-party service | Rejected for identified data | Veteran PII may not leave the JVSG SharePoint/tenant. De-identified payloads only, with written approval and a data-processing agreement; not worth the risk for wording polish. |
| F. Power Automate / Copilot Studio / `=COPILOT` | Not available | Not licensed. Python in Excel has no network access, so it cannot call any model either. |

No model is used in the demo. Any later SLM only rewrites a fixed, validated
template into plain language from closed inputs, runs inside approved
boundaries, and is labeled "draft - staff review required".

## 5. Demo scope (Nov 30) and work breakdown

Demo claim: "Every veteran in the cohort gets a staff-reviewed referral brief
built from structured data with visible freshness." Show with **synthetic data
only** in the repo; the live workbook stays in SharePoint.

| # | Task | Output | Where |
|---|---|---|---|
| 1 | Confirm with Hank: referral workflow, partner categories, and who owns the partner directory | Short decision note | SharePoint, not this repo |
| 2 | Map profile fields to schema columns; mark gaps and stale-data risk | Field mapping table | Restricted storage |
| 3 | Draft read-only profile SELECTs (long format `stateid, field, value, as_of_date, source`); validate on known veterans | SQL files | Restricted storage, per the SQL publication strategy |
| 4 | Synthetic profile fixture (invented rows) matching the field list in section 2 | `data/synthetic/` CSV and schema note | This repo |
| 5 | Brief template (Office Script or formulas): fixed sections, "as of" dates, "unknown" where a field is missing, partner-category suggestions from the closed barrier vocabulary | `BuildReferralBrief` script and tests | `src/jvsg_triage/m365/sharepoint_demo/` |
| 6 | "Referral status" column (not started / consent obtained / referred / accepted / declined) and a status count on the Overview tab | Workbook change | SharePoint |
| 7 | Demo script update: show brief, freshness flags, consent gate; state clearly that no model is used and no referral is automatic | Demo talking points | `docs/operations/` |

Out of scope for Nov 30: any model, bulk note mining, automatic partner
transmission, write-back to the state system.

## 6. After the demo

- IT request: per-user Python and a named local model (Option B), synced-PII
  rules, and whether a supported scheduled export or view exists.
- Pilot with a small subset, then all 337; record aggregate referral counts
  for the NASWA nomination (publication needs approval).
- Decide where referral status is recorded long term (state system service
  codes preferred over the workbook).

## 7. Open questions

- Is there a partner directory, or do we build a minimal one (category,
  county, contact, intake method)?
- Is the cohort definition (steps 17/21) validated? Per the restricted SQL
  status it is not yet validated against MIS records; the referral list
  inherits that risk.
