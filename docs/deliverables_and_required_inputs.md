# JVSG Non-CM Pipeline: Deliverables and Required Inputs

## Purpose and current assumptions

This document defines the proposed end-to-end deliverables and the decisions
and sample inputs needed to build them. It is intended to support management
discussion and turn the current architecture into an implementable, testable
plan.

The desired outcome is a reliable, low-maintenance workflow that uses existing
203/205 assessments and case notes without asking staff to re-enter information
already recorded in the management information system (MIS). The JVSG team will
have a ready-to-use, access-controlled SharePoint experience for non-case
managed (Non-CM) veterans. A separate TOON workflow will prepare and, only when
authorized, transmit the approved information to the U.S. Department of Labor
(DOL)/VOMA.

**Confirmed initial downloads (November 6, 2026):** the project owner supplies
the MIS's precomputed **203/205 anti-join as CSV** and **case notes as XLSX**.
Keep these formats unchanged, including report title rows and wrapped headers.
The [native intake contract](./mis_intake_contract.md) records header-only
discovery and the synthetic-tested ETL foundation. Separate 203/205 inputs
remain a future requirement for independently recomputing the cohort. The
presentation also describes a Python batch extraction and M365 workbook; verify
what is currently operating and whether that extraction can consume these
specific reports before reusing or extending it. ADOW analyst accounts may
provide access to custom reports or BI features, but that access is not
confirmed for this project. Ask management/MIS administrators to assess it as
a possible future improvement, not as a prerequisite for the native-download pilot.
Keep the ingestion contract independent of source method so an authorized
managed export or integration can replace the manual step without changing
downstream processing.

This repository has an intake foundation, not a deployed system. The deliverables
below are targets; they are not claims of existing production functionality.
Live veteran data must not be added to this repository, tests, prompts, or
development artifacts. Use synthetic fixtures here. Real-data discovery and
validation must use an ADOW-approved secure environment and transfer method.

## Target workflow

```text
Manual native MIS exports (initial path)
  ├─ Precomputed 203/205 anti-join CSV
  └─ Case notes XLSX
          |
          v
Secure intake -> validation/quarantine -> normalize and deduplicate
          |
          v
Use supplied cohort -> retrieve matching notes
  (independent 203/205 join requires separate reports and approved rules)
          |
          v
Privacy boundary -> structured, evidence-linked barrier extraction
          |
          +------------------------------+
          |                              |
          v                              v
JVSG SharePoint experience        TOON validation/export
review and operational use        separately authorized DOL/VOMA path
```

Future source options, subject to approval and access, include a managed
scheduled export, MIS integration, or analyst-enabled custom report/BI
workflow. None is assumed available for the initial pilot.

The exact hosting, storage, identity, inference, and DOL connection choices
remain subject to management, IT/security, privacy, and program approval. A
manual export is an ingestion method, not permission to store exports in
unapproved locations.

## Presentation and award context

The [presentation delivered at the 2026 statewide JVSG training in
Montgomery](./Services_for_Non_CM_Veterans_Best_Practices.pdf) describes the
project's demonstrated direction and baseline:

- It reports a Mobile FY 2026 baseline of 138 assessed veterans, including 90
  active case-management records and a 48-person Non-CM triage cohort; 40 of
  those 48 were assessed in Q4. Treat these as presentation-reported figures
  until the source reports and counting rules are reconciled.
- It describes a 14- to 30-day stabilization period in the cohort summary and
  a 14- to 60-day window in the partner follow-up section. Confirm the intended
  operational window before encoding time-based rules.
- It describes an automated 203/205 anti-join, contact-velocity tracking,
  office-level SharePoint workbook/slicers, and M365 synchronization. The
  presentation calls the interactive cloud workbook deployed; confirm current
  operation, ownership, access, refresh process, and supported report types
  before deciding to rebuild or extend it.
- It describes a case-note-to-constraint workflow, managerial barrier
  diagnostics, and DVOP/LVER handoffs. The target here is to make the case-note
  extraction reviewable, traceable to approved source evidence, and integrated
  with the 203/205 cohort without duplicate entry.
- It presents local SLM and TOON integration as an approach and cites a 55%
  token-overhead reduction. Do not treat that figure as an independently
  measured result until the corpus, tokenizer, comparison method, and output
  are validated.

The Mobile team received a JVSG incentive award for its FY 2026 performance.
That award recognizes the team's performance; it was not awarded to this new
project. The project is being brought to management as a proposal for the
2027 NASWA Winter Workforce Innovation Awards, to discuss whether and how
Alabama should submit a nomination. The prior NASWA announcement provided a
December 4, 2026 nomination deadline; confirm the current requirements and
timing. The management discussion is planned for Friday, November 13, 2026.
Hank Lahti (Alabama JVSG Coordinator) and Kevin Kidd (ES Director) are the
management stakeholders for that discussion. No award or nomination outcome
for this project is assumed.

The presentation is project context, not a substitute for current-state
verification. This repository still contains a development scaffold; claims in
the presentation do not by themselves establish that production integrations,
security approvals, automated scheduling, or live-data controls are implemented
in this codebase.

## Deliverables

| ID | Deliverable | Expected result and acceptance evidence |
|---|---|---|
| D1 | **Source report contract** | Documented field mappings, data types, row granularity, report filters, and validation rules for the 203, 205, and case-notes reports. Report changes fail visibly with an actionable, sanitized error rather than silently dropping data. |
| D2 | **Secure, repeatable native-download intake** | Accept the precomputed anti-join CSV and case-notes XLSX unchanged, discover headers after titles, and validate ordered layouts. Complete an authorized intake procedure, naming/version convention, receipt record and quarantine path before live processing. Preserve the source contract if approved automation replaces manual intake. |
| D3 | **Deterministic ETL pipeline** | Typed, tested steps to load and normalize each report; deduplicate according to approved rules; join the 203 and 205 populations; identify the Non-CM cohort; match applicable case notes; and produce validation/reconciliation counts. Re-running the same inputs does not create duplicate cases or notes. |
| D4 | **Barrier extraction and review workflow** | Convert unstructured case-note evidence into a versioned, structured barrier profile with source-note provenance and uncertainty/status. Model-generated content is an `AI_Draft`; qualified JVSG staff retain authority to review and correct it. No model output independently decides eligibility, referral, or case closure. |
| D5 | **JVSG SharePoint experience** | Verify and, where approved, extend the workbook demonstrated in the presentation rather than create a competing tracker. Provide the authorized JVSG team with the cohort/action view, approved barrier summaries, review status, source/refresh timestamps, and visible exception or stale-data state. Confirm access, retention, ownership, and record-level permissions before live data is published. |
| D6 | **Parallel TOON pipeline** | A separately testable branch that serializes only approved fields using a validated, versioned TOON contract. It has its own output validation, audit trail, and idempotency controls. DOL/VOMA transmission remains disabled until the receiving contract, authorization, security review, and operational owner are confirmed. |
| D7 | **Scheduling and run operations** | A configurable schedule for intake checks and/or processing, with run IDs, input fingerprints, safe retries, duplicate-send protection, failure notification, and a restart/recovery procedure. Schedule and timing are selected with management and IT; no schedule is assumed to exist before the approved hosting mechanism is known. |
| D8 | **Security, privacy, and governance package** | Approved data-flow and access model; least-privilege roles; identity handling and de-identification rules; secure secret management; retention/deletion; audit/event handling; human-review responsibilities; and explicit approval gates for live inference and external transmission. |
| D9 | **Test and operational handoff** | Synthetic end-to-end fixtures, boundary and malformed-input tests, reconciliation checks, a concise runbook, support/escalation path, and training for the staff who export, monitor, review, and administer the solution. |
| D10 | **NASWA innovation-award proposal and evidence** | Prepare a management-ready discussion package for the upcoming NASWA Workforce Innovation Awards: candidate category/categories, project scope, presentation/demo evidence, implementation status, verified outcomes, privacy/security controls, limitations, and evidence still needed. Management decides whether to proceed and the state administrator approves any nomination. Clearly distinguish the Mobile team's FY 2026 performance award from this new project; do not imply this project has won an award or disclose veteran-level data. |
| D11 | **Agency repository ownership and audit** | Move source-code stewardship to an ADOW-approved organization or agency-managed source platform, with individually attributable accounts, least-privilege team membership, documented review rules, and an audit-log retention/export owner. Keep the repository source-only: agency hosting does not authorize veteran records or case notes in GitHub. |

### Repository ownership and audit decision

As of November 6, 2026, `kcbattlejr/JVSG-Alabama` is a private repository
owned by a personal GitHub account, not an ADOW organization. That makes its
current visibility private, but does not give ADOW organizational control of
membership, ownership continuity, or organization-level audit settings.

**Recommendation:** ask ADOW IT/security whether it already has an approved
GitHub organization or whether this project must be hosted in another managed
source-control service. If GitHub is approved, have the agency own the
organization and repository; do not rely on adding a workforce email to a
personal account as the governance solution. A verified work email can help
attribute commits, but it does not transfer repository ownership, establish
agency control, or provide organization audit logs.

Before any transfer or migration, agree with ADOW on:

- The approved platform, organization/enterprise owner, repository visibility,
  and whether this project may use GitHub-hosted CI and Codespaces.
- Agency-managed member identity requirements: existing GitHub accounts
  authenticated through ADOW SSO, or enterprise-managed accounts if required.
  SAML SSO for GitHub organizations requires GitHub Enterprise Cloud; confirm
  licensing and identity-provider support with IT.
- At least two agency-designated organization owners for continuity, plus
  named teams with least-privilege repository roles. Avoid shared accounts.
- Required two-factor authentication, outside-collaborator policy, approved
  app/OAuth integrations, secret handling, and member offboarding.
- Protected default branch or ruleset, required pull-request review and CI
  checks, who may merge, and a process for emergency changes.
- Who can review/export the organization audit log, what events must be
  reviewed, retention period, and whether logs must be streamed to ADOW's
  central monitoring system. GitHub's organization audit log covers the prior
  180 days and is available to organization owners; confirm that this meets
  ADOW's evidence-retention requirements.
- A migration/transfer owner and plan for repository permissions, Actions
  secrets and variables, environments, branch protections, webhooks/apps,
  Codespaces, package/artifact settings, remote URLs, and CI after ownership
  changes. Revalidate access and protections after the move.

**Proposed account owners for management discussion:** Hank Lahti, as Alabama
JVSG Coordinator, and Kevin Kidd, as ES Director. If both accept and ADOW
policy permits, designate them as the two accountable, individual organization
owners for continuity, with Mr. Lahti as the JVSG business/product owner and
Mr. Kidd as the executive sponsor. Confirm the least-privilege model with IT:
organization-owner access is highly privileged, so an ADOW-managed platform
administrator may instead hold the technical owner role while Hank and Kevin
serve as business owners with appropriate repository permissions. Use each
person's own approved account; never share credentials. This is a proposal,
not an assignment or confirmation that either currently has an account.

GitHub's documentation explains [repository transfers](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository),
[organization audit logs](https://docs.github.com/en/organizations/keeping-your-organization-secure/reviewing-the-audit-log-for-your-organization),
and [SAML SSO](https://docs.github.com/en/organizations/managing-saml-single-sign-on-for-your-organization/about-identity-and-access-management-with-saml-single-sign-on).
Use these as platform references, not as a substitute for ADOW security or
records-retention approval.

## Required inputs from the project owner

### 1. Sample reports for format discovery

Header-only discovery of the anti-join CSV and case-notes XLSX is complete; see
[the contract](./mis_intake_contract.md). Do not resubmit live samples. To
independently verify the underlying cohort, obtain approved synthetic samples
of the separate reports:

1. **203 report** — Comprehensive Assessments used to define the candidate
   population.
2. **205 report** — IEP/case-management records used to distinguish veterans
   already in case management from the Non-CM cohort.
3. **Case notes report** — unstructured notes associated with veterans in the
   203/205 analysis, including enough information to determine how notes link
   to an individual and how note chronology is represented.

For each report, include:

- The original export format (for example, XLSX or CSV), with headers and
  representative date and null formats preserved. Retain native formats:
  anti-join CSV and case-notes XLSX, including title rows and original headers.
- A data dictionary or explanation for each field, coded values, and report
  filters, if available.
- The report-generation steps and the date/time the report was run.
- Whether a standard user can export the report or whether it requires an
  analyst account, custom-report permission, or BI feature.
- Whether a row is a person, assessment, IEP, note, or another record type.
- A synthetic example of duplicates, missing values, and any known edge cases
  that matter to the report.
- The stable field(s) that link 203, 205, and notes. Do not assume names or
  SSNs are appropriate join keys.

**Protect the samples:** do not commit real reports or paste live names, SSNs,
raw SIDs, contact details, or case notes into GitHub, this repository, or this
chat. If representative structure cannot be reproduced synthetically, first
confirm an ADOW-approved secure transfer and review location. Do not send
unredacted reports until the agency confirms that location and the recipients
are authorized.

### 2. Business rules and interpretation

Provide or identify an owner who can approve:

- The definition of a qualifying 203 assessment, the applicable reporting
  window, and the office/role scope.
- Which 205 records count as active/open case management, including status and
  date rules.
- Deduplication rules for multiple assessments, IEPs, or notes, and how
  carryovers are handled.
- Which notes are in scope: all notes, only notes after a qualifying 203, or a
  defined time period; how amended/deleted notes should be handled.
- The required recency/freshness of exports and acceptable delay from entry in
  the MIS to display in SharePoint.
- Which barrier categories and structured fields are useful to JVSG staff, and
  what evidence, confidence, abstention, and human-review statuses should be
  shown.
- Which staff roles may see which offices/records, who approves corrections,
  and who handles exceptions.
- What information is useful for DOL/VOMA, what must never be transmitted, and
  who approves each version of the external data contract.

Where these rules are not yet settled, record the question and approver rather
than embedding a guessed rule in the pipeline.

### 3. Management and IT decisions

Confirm, or identify the decision-makers for:

- The approved storage and processing environment for live reports and notes.
- Whether a secure managed export, API, or scheduled delivery can be supported
  by the MIS/ADOW team, and what assistance or approvals would be required.
- Whether an ADOW analyst account can be provisioned or delegated for approved
  custom reports/BI, what reports or exports that access enables, who can
  authorize it, and whether it could later support a managed refresh. Do not
  share accounts or credentials; do not make the pilot depend on this access.
- SharePoint site owner, membership group, audience, tenant/environment,
  information classification, and permitted list/library or data-source
  approach.
- The approved scheduling/orchestration mechanism, run frequency, operating
  window, holiday behavior, failure notification recipient, and support owner.
- The current state and owner of the presented Python extraction, M365
  synchronization, SharePoint workbook, barrier summary, and management
  dashboard; identify which components can be reused and which are only
  demonstrations.
- Identity and secret management, logging/auditing, data retention and deletion,
  and incident/escalation procedures.
- DOL/VOMA endpoint, schema, transport, credentials/identity, test environment,
  approval process, and whether initial delivery is export-only or connected.
- Whether management wants to advance this project for the upcoming NASWA
  Workforce Innovation Awards, which category best fits, what evidence is
  needed, and who will obtain state-administrator approval.
- Whether ADOW approves GitHub for this source code, the agency-owned
  organization/platform to use, required identity/SSO and repository controls,
  and the audit-log owner/retention destination.
- Whether Hank Lahti and Kevin Kidd accept the proposed business-owner and
  repository-owner/sponsor roles, and whether ADOW policy supports granting
  organization-owner privileges to them or requires IT to retain technical
  ownership.

## Operating model: no double-entry and safe retries

1. Staff continue recording assessments and case notes in the approved MIS.
   The pipeline reads authorized exports; it does not ask staff to retype
   veteran identity, assessment details, or narrative notes into a second
   application.
2. Initially, the only manual step is exporting the three source reports as
   CSV and placing them in the approved intake location. Investigate an
   approved managed export or analyst-enabled reporting path separately; adopt
   it only after authorization and validation, without creating a second
   data-entry workflow.
3. The pipeline uses a stable source key for matching, preserves source
   provenance, and uses an approved protected identifier for downstream
   correlation. Raw identifiers and note text remain within the approved
   processing boundary; only the minimum approved fields cross to SharePoint
   or the TOON export.
4. Each run records its input version/fingerprint and outcome. Reprocessing an
   unchanged input is safe: it updates the same logical records, preserves
   authorized staff review/actions, and does not create duplicate SharePoint
   items or DOL transmissions.
5. Invalid, incomplete, stale, or mismatched reports stop or quarantine the
   affected run, show an actionable error to the operator, and do not publish
   a success-shaped partial refresh.
6. The SharePoint and TOON paths consume the same validated cohort/profile
   outputs but have separate permissions, review gates, delivery status, and
   error handling. Failure in one path must not silently mark the other as
   successful.

## Recommended implementation sequence

1. **Discover and contract:** receive safe report samples, profile schemas and
   join keys, and approve cohort/note rules.
2. **Prove ETL offline:** build synthetic fixtures matching the confirmed
   formats; implement load, validation, join, notes association, and
   reconciliation before connecting live data.
3. **Establish secure operations:** approve where live CSV exports are stored
   and processed, who can access them, and how manual intake is monitored.
   Separately ask MIS/IT whether analyst-enabled custom reports or BI can
   reduce the manual export burden in a later phase.
4. **Extend SharePoint delivery:** reuse the presented workbook where suitable;
   validate access restrictions, refresh behavior, review workflow, and
   recovery for the added notes-derived data.
5. **Build TOON in parallel:** finalize the DOL/VOMA contract, validate
   serialization independently, and test with synthetic data. Keep outbound
   transmission disabled until authorized.
6. **Schedule and pilot:** add the approved scheduler, idempotent retries,
   notifications, and operator runbook; conduct an authorized, limited pilot
   with human review.
7. **Prepare the NASWA award discussion:** present the proposed category,
   verified current-state evidence, planned work, privacy controls, and open
   decisions to management. Advance a nomination only if management and the
   state administrator approve.

## Initial review checklist

- [ ] Safe sample 203 report and field definitions received.
- [ ] Safe sample 205 report and active/open status definitions received.
- [ ] Safe sample case-notes report and person/note linkage explained.
- [ ] Initial CSV export procedure, report filters, and operator confirmed.
- [ ] Join key and duplicate/overlap rules approved.
- [ ] Live-data intake/storage/processing boundary approved.
- [ ] SharePoint owner, JVSG audience, access model, and refresh expectations
  identified.
- [ ] Schedule, failure notification, retry, and operational support owners
  identified.
- [ ] TOON fields and DOL/VOMA transmission authorization identified.
- [ ] ADOW-approved source-control owner/platform and repository visibility
  confirmed.
- [ ] Named repository administrators, access groups, branch/PR rules, and
  audit-log owner/retention confirmed.
- [ ] Human review, retention, and audit requirements approved.
- [ ] Current status and ownership of the presented workbook, extraction, and
  M365 sync confirmed.
- [ ] MIS/IT has assessed whether analyst access, custom reports, or BI is
  available and appropriate for a later phase.
- [ ] Management has decided whether to pursue a NASWA Workforce Innovation
  Award nomination for this project and identified the candidate category.
- [ ] Any nomination has state-administrator approval; the Mobile team's FY
  2026 performance award is described separately and accurately.
- [ ] Hank Lahti and Kevin Kidd have discussed and accepted (or declined) the
  proposed business-owner and repository-governance roles.

## Related project documents

- [Enterprise technical specification](./executive_summary_enterprise_technical_specification_jvsg_non_cm_triage_azure_architecture.md)
- [Implementation plan](./implementation_plan.md)
- [Implementation sprint TODO](./sprint_todo.md)
