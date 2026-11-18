# JVSG MVP scope and approval checklist

**Status: November 18, 2026.** The current deliverable is an offline
demonstration using invented data. The next decision is whether to authorize
the design of a limited pilot, not whether to deploy the current demo.

## What exists today

| Capability | Current evidence and limit |
|---|---|
| Paired report intake | Validates native-layout, synthetic anti-join CSV and case-notes XLSX. Matches notes to the supplied cohort and scrubs locally. Does not recompute the 203/205 anti-join or infer the meaning of MIS date fields. |
| Staff review and follow-up | Separate synthetic workbook supplies office, assessment/contact dates, four support-area states, and review status. Follow-up bands are calculated deterministically; the 15/30-day cutoffs are examples, not policy. |
| Excel/HTML and standard TOON | Two reproducible snapshots with reconciliation and exact TOON round trips. The TOON grammar is standard; the profile schema is not an approved federal interface. |
| Optional AI wording | A draft may describe invented aggregate changes only; a person reviews it before it can be displayed. No case notes, row data, referrals, or live inference are involved. |

See the [runbook](./management_demo_runbook.md) for reproduction and the
[stakeholder briefing](./management_presentation_briefing.md) for the value
proposition, November 19 decisions, and December 4 NASWA submission gates.

## Scope the smallest pilot

Start with one authorized JVSG team. Prefer a manual paired upload and an Excel
snapshot over new services, dashboards, or app permissions. GeoSol remains the
system of record. Require matching report periods, a recorded receipt and
operator, sanitized failure messages, a visible status and report date, and
preservation of the last good output if the new pair fails. Retries must not
repeat staff work or overwrite reviewed information.

Keep the intake library and staff working data separate from any approved
management aggregates. SharePoint can store files; it does not run this Python
pipeline. Validate Excel viewing and permissions in the intended tenant before
choosing a delivery method. HTML page publishing, Power BI, Power Automate or
Azure hosting each need their own tenant, licensing and access review. Hidden
sheets, filters, and audience targeting are not access controls.

## Decisions and evidence required

| Owner to confirm | Approval or evidence needed |
|---|---|
| JVSG business owner and qualified reviewers | Approved source for office, assessment/contact dates, recorded support states and staff review. Define what counts as contact, missing-date handling, aging cutoffs, ownership of corrections, case interpretation, and referral authority. |
| MIS/report owner | Confirm report period, freshness, join key, note scope, duplicates, amended/deleted notes and receipt requirements. Only if independent cohort calculation is needed, approve the separate 203/205 extract contracts, time/office/role scope, active IEP rules, and carryovers. Use synthetic examples in this workspace. |
| IT/security and site owner | Approve the tenant, site/libraries, runtime, assigned identities, least-privilege processor/staff/reader groups, secrets, access auditing, incident handling, and safe recovery. No broad tenant-admin or Graph access is required for a manual design. |
| Privacy, records and legal | Approve the data flow, retention/deletion for originals, redacted outputs, backups and logs, disclosure and accessibility review, and any material shared outside the team. Scrubbing and pseudonyms are not anonymization. |
| Agency source-control owner | Confirm approved repository ownership, visibility, individually attributable access, offboarding, branch/CI controls, and audit-log retention. Agency ownership does not permit putting live records in GitHub or Codespaces. Licensing and historical-disclosure gates remain in [SECURITY.md](../SECURITY.md). |
| Sponsor and pilot operator | Approve cohort/scope, exception owner, rollback and training. Rehearse on generated data, then measure preparation time, data corrections, and timely follow-up against the current process only in an authorized pilot. |

Record each decision, approving role, date and supporting evidence in the
agency-approved governance location. Do not paste live examples, secrets or
named internal assignments into this repository.

## Explicitly outside the current MVP

No live ingestion, scheduled sends, staff write-back, case-note AI,
automated referrals, statewide access, or VOMA delivery is implemented or
approved. Explore each only after the manual pilot demonstrates value.
Any model or external recipient needs its own approved purpose, minimum
schema, privacy review, acceptance checks, and authorization. A NASWA
nomination is separate from all live-data, licensing, or release decisions.
