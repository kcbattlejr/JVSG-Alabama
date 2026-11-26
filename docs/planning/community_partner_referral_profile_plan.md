# Plan: community-partner referral brief (templates only)

**Status: decided November 26, 2026, for the November 30 demo.** Route: **Option A,
fixed templates with no model.** Other routes are listed under
[Next steps](#7-next-steps-not-part-of-the-demo). Builds on the working SharePoint
dashboard (`src/jvsg_triage/m365/sharepoint_demo/`). Repository work uses synthetic
data only; veteran data stays in the JVSG SharePoint site
([PII protocol](../data/pii_protocol.md)). Referral decisions stay with qualified
staff; the brief is a draft for their review.

## 1. Goal and claim

The dashboard shows which veterans are in the hardest-to-place follow-up cohort.
Hank's question was what to do with them. Answer: every veteran in the cohort
gets, at minimum, a **staff-reviewed referral to a community partner** that can
help stabilize barriers, delivered as a warm handoff.

Demo claim: *each cohort veteran has a one-page referral brief built from
structured data, with visible data freshness, a consent gate, and tracked
referral status.* No model is used, nothing is sent automatically, and staff make
every decision.

Two documents, kept separate:

| Document | Audience | Content | Release |
|---|---|---|---|
| **Staff referral brief** (demo) | JVSG staff | Last-known-good profile, freshness flags, suggested partner categories | Restricted SharePoint workbook only |
| **Partner referral sheet** (later) | Community partner | Minimum necessary subset | Only with the veteran's documented consent or release |

Confirm with agency privacy/legal: release-of-information rules for non-agency
partners and any limit on reusing state-system data.

## 2. Why structured data, not case notes

Deterministic, auditable, no model risk, no dependence on the unvalidated note
scrubber, and no governance approval for note-level AI. Notes stay with staff:
they may read one veteran's notes themselves. Bulk note mining is a later phase
(see the [TOON/SLM plan](./toon_and_slm_barrier_dx_plan.md)).

## 3. Design

```text
Read-only SELECT queries (MIS query window, restricted SQL)
  -> CSV into the restricted SharePoint folder   (restricted/csv/profile/)
  -> Power Query: Profile table (newest CSV, like Worklist.pq)
  -> Brief sheet: pick a veteran, template formulas fill the brief
  -> Referrals table: staff record consent and status (manual input)
  -> Overview: referral status counts
```

**Profile fields.** Each carries value, **as-of date** and source, so staleness is
visible. Exact columns are mapped from the vendor schema (restricted storage).

- Identity, contact and its last-updated date; county and local office; staff.
- Last employment: employer, occupation, wage, separation date.
- Last positive outcome: training, credential, placement or successful service.
- Last service and date; last contact date (never note text); days since contact.
- Structured barrier flags that exist as fields (housing, disability, SBE,
  justice involvement, limited English, and similar).
- Case status: enrollment, plan, closure.
- Barrier domain from the closed vocabulary (TRN, HSG, MED, LEG) where a field
  supports it, otherwise `UNK`.

**Queries.** The MIS query window is SELECT-only (no EXEC or `sp_`), so stored
procedures are not an option. Use read-only SELECTs like steps 17 and 21: one per
source area, long format `(stateid, field, value, as_of_date, source)`, pivoted in
Power Query. State ID is `dbo.indstaff.stateid` (bigint); keep it text in Excel.
Keep SQL in restricted storage per
[sql_publication_strategy.md](../sql/sql_publication_strategy.md).

**Brief sheet, formulas first.** Office Scripts depend on the Automate tab, which
may be unavailable, so the brief is built from worksheet formulas (`INDEX/MATCH`,
`TEXTJOIN`, `IF`) driven by a veteran selector cell. An Office Script is optional,
only to build the sheet layout. Fixed sections:

1. Header: "Draft for staff review. Not a referral decision."
2. Who and where: name, office, assigned staff, preferred contact and its
   as-of date.
3. Last known good: employment, outcome, last service, each with its date; fields
   older than a set cutoff show "Stale - verify" and missing fields show
   "Unknown", never blank or guessed.
4. Barrier indicators found in structured data, by domain.
5. Suggested partner categories, from a fixed mapping table (domain to category,
   for example HSG to housing assistance) that staff can edit; a suggestion, not
   an assignment.
6. Consent and status: filled from the `Referrals` table.

**Referrals table (manual).** Columns: `STATE_ID` (text), `STATUS` (not started,
consent obtained, referred, accepted, declined), `CONSENT_DATE`, `PARTNER_CATEGORY`,
`REVIEWED_BY`, `REVIEWED_ON`. It is separate from the query tables, so Refresh
All never overwrites staff entries. The partner sheet area stays locked until
status is at least "consent obtained".

**TOON export and classification (decided Nov 26).** From the same profile we
still generate TOON, and classify barriers by deterministic rules over structured
fields only (`profile-rules-v1`, in `src/jvsg_triage/dashboard_demo/profile.py`):

- Per profile and domain (TRN, HSG, MED, LEG): a state from the closed
  vocabulary (CRT, ACT, MIT, RES, UNK), the rule id, the evidence field, value and
  date, and freshness (`current`, `stale` after 180 days, `unknown` for undated
  flags). A missing indicator is `UNK`, never "no barrier".
- Examples: homeless flag gives HSG `CRT`; unstable housing gives HSG `ACT`;
  disability without a medical service in 365 days gives MED `ACT`, with one gives
  `MIT`; a credential or training completion in 365 days gives TRN `RES`; justice
  flag gives LEG `ACT`.
- Suggested partner category (from the fixed domain mapping) only for `CRT`/`ACT`.
- Output tables `profiles.toon` and `barrier_classifications.toon` use the
  schema-driven codec `jvsg_triage.toon.codec`; every row is `Unverified` with null
  reviewer columns. TOON carries no names or State IDs, only a profile row key; the
  crosswalk stays in the workbook. TOON is the audit and exchange artifact, and the
  Brief sheet reads the `Classification` table. In the workbook the rules run in
  Power Query (`Classification.pq`) and TOON is produced by Python in Excel
  (`cell4_profile_toon.py`); steps are in the
  [SharePoint runbook](../operations/sharepoint_demo_site.md#referral-profile-classification-and-toon-add-to-the-workbook).
- Synthetic examples are in `data/synthetic/sharepoint_dashboard/toon/`. The live
  rule thresholds and flag-to-field mapping need staff confirmation before use;
  the mapping, SQL steps and open questions are tracked in
  [referral_profile_setup.md](../operations/referral_profile_setup.md).

## 4. Demo scope

In: staff brief from structured data, freshness flags, consent gate, referral
status counts, synthetic walk-through, plain statement that no model is used.

Out: any model, bulk note mining, automatic transmission to partners, write-back
to the state system, the partner-facing sheet.

## 5. Work breakdown (Nov 26-30)

| # | Task | Output | Where |
|---|---|---|---|
| 1 | Confirm workflow, partner categories and partner-directory owner with Hank | Decision note | SharePoint |
| 2 | Map profile fields to schema columns; note gaps and stale-data risk | Mapping table | Restricted storage |
| 3 | Draft and validate profile SELECTs on known veterans (as done for query A) | SQL | Restricted storage |
| 4 | Synthetic profile CSV, rule-based classification and TOON export (done) | `data/synthetic/sharepoint_dashboard/`, `dashboard_demo/profile.py`, tests | This repo |
| 5 | `Profile.pq` query and Brief sheet formulas; domain-to-category mapping table | Power Query, layout notes | `sharepoint_demo/`, workbook in SharePoint |
| 6 | `Referrals` table and Overview status counts | Workbook change | SharePoint |
| 7 | Rehearse on synthetic data, then the live workbook; update the runbook and demo talking points | Script | `docs/operations/` |

Prioritize 1-3 and 5; if the live profile queries slip, demo the Brief on
synthetic data and say so.

## 6. Acceptance checks

- Every brief field shows a value with an as-of date, "Stale - verify" or
  "Unknown"; none is blank.
- Refresh All keeps `Referrals` entries intact.
- No model, network call or external transmission anywhere in the flow.
- Brief and `Referrals` exist only in the restricted workbook; the repo holds
  synthetic fixtures and code only.
- Offline tests pass for the profile generator, classification rules and TOON round trip.
- TOON output contains no names or State IDs and every row is `Unverified`.

## 7. Next steps (not part of the demo)

| Route | Status | What it needs |
|---|---|---|
| **B. Local Python/SLM** on a staff laptop via the synced SharePoint folder, for plain-language wording | Next | IT approval of per-user Python and a named model (the laptop has no admin rights; application control may block it), disk-encryption and synced-PII confirmation, model governance sign-off. Model only rewrites the fixed template from closed inputs, output labeled "draft - staff review required". About 2-3 hours of CPU time per full run. |
| **C. VBA in a desktop `.xlsm`** calling a local model | Fallback | Desktop Excel only; macro files need IT approval. |
| **D. In-tenant Azure Function** called by an Office Script | After pilot | IT hosting, managed identity, app registration; `azure_functions/` is reserved, not implemented. |
| **E. Third-party host (Modal, GitHub)** | Rejected for identified data | Veteran PII may not leave the JVSG SharePoint or tenant. Only de-identified payloads, with written approval and a data-processing agreement. |
| **F. Power Automate, Copilot Studio, `=COPILOT`** | Not available | Not licensed. Python in Excel has no network access, so it cannot call a model. |

Also after the demo: partner-facing referral sheet gated on consent; a supported
view or scheduled export from IT; a minimal partner directory (category, county,
contact, intake method); long-term home for referral status (state-system service
codes preferred over the workbook); pilot on a small subset, then the full
cohort, with aggregate referral counts for the NASWA nomination (publication
needs approval).

## 8. Open questions

- Does a partner directory exist, and who owns it?
- Is the cohort definition (steps 17 and 21) validated against MIS records? Per
  the restricted SQL status it is not yet; the referral list inherits that risk.
- What staleness cutoff per field should trigger "Stale - verify"?
