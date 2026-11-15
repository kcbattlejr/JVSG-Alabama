# Proposal: JVSG SharePoint Data Visualization and Reporting Workflow

**Date:** November 13, 2026  
**Proposed lead:** Alabama JVSG Veteran Services team  
**For discussion with:** ES Director; JVSG State Coordinator
**Status:** Management proposal; not an approved or deployed production workflow.

## Recommendation

Use an ADOW-approved modern SharePoint site as the internal front door for
JVSG reporting. Start with restricted report intake, an authorized ETL
operator, and an aggregate Excel dashboard. Evaluate SharePoint HTML pages
for custom presentation and Power BI for richer interactive reporting only
after confirming tenant availability, licensing, and approvals.

First verify the ownership, operation, and refresh process of the SharePoint
workbook described in the statewide presentation. Extend that experience
where practical rather than introduce a competing tracker. See
[deliverables and required inputs](deliverables_and_required_inputs.md).

This approach requires project-scoped permissions, not tenant administrator
access for the project developer.

## Business value

Management reports that ADOW's current GeoSol configuration does not include
the veterans-specific package. This initiative explores complementary,
agency-controlled visualization and workflows around existing reports.
GeoSol remains the system of record; the proposal does not assume a supported
GeoSol plugin interface, write-back access, or replacement of the MIS.

- **Veterans:** Intended to support timely follow-up for veterans receiving
  services outside formal case management, while keeping service decisions
  with qualified staff.
- **ADOW:** A potential path to incremental modernization using existing
  reports and approved Microsoft 365 resources.
- **JVSG:** Better visibility and coordination without asking specialists to
  re-enter information already recorded in the MIS.
- **National relevance:** A potentially replicable approach to extending
  existing systems and preparing for responsible AI adoption.

Cost savings, improved service outcomes, and statewide impact are hypotheses
to measure, not established results.

## Current capability and boundaries

The repository implements intake validation for the native 203/205 anti-join
CSV and case-notes XLSX, matching notes to cohort SIDs, privacy scrubbing, and
synthetic practice data. The anti-join report supplies the cohort; the current
pipeline does not independently recompute it from separate 203 and 205 reports.

The [synthetic management demo](./management_demo_runbook.md) now implements a
separate, closed-vocabulary Excel input contract, deterministic ETL, lossless
custom TOON demo serialization, simulated file arrival/refresh, and real
Excel/HTML snapshots with integrity verification. The intended MVP driver is
the cloud SharePoint workbook; its delivery is simulated locally in this demo.
This does not establish a mapping to the existing agency workbook or approved
production aging/barrier rules.

Live SharePoint ingestion/publishing, scheduled report collection, operational
lists, automatic cloud dashboard refresh, AI classification, and DOL/VOMA
integration remain unimplemented. A SharePoint library stores files; uploading
Python code or reports does not make SharePoint execute the ETL.

Live reports require an approved processing environment. Keep GitHub,
Codespaces, CI, demonstrations, and development artifacts synthetic-only
unless separately authorized under agency policy. Repository ownership and
Codespaces approval remain separate governance decisions.

## Proposed end-to-end workflow

```text
GeoSol native weekly reports
  - 203/205 anti-join CSV
  - Case notes XLSX
             |
             v
Approved manual upload or authorized mailbox delivery
             |
             v
Restricted SharePoint intake library
             |
             v
Approved ETL execution environment
  - Validate report layouts and reporting period
  - Match notes to the supplied cohort
  - Apply privacy controls and reconcile counts
  - Record batch status; quarantine invalid inputs
             |
       +-----+-------------------+
       |                         |
       v                         v
Restricted JVSG workspace    Approved aggregate dataset
Authorized staff only            |
                                 v
                        Internal statewide dashboard
```

### Intake and processing

1. An authorized official arranges weekly delivery of both
   reports to an approved mailbox, if supported and approved. Otherwise,
   designated staff upload the native reports manually. The developer does
   not need personal permission to email reports.
2. A designated operator or approved Power Automate flow saves the reports
   into the restricted intake library without changing the CSV/XLSX layouts.
3. Before processing, confirm both reports belong to the same agreed batch
   and reporting period. Do not mix a new report with an older counterpart.
4. An authorized operator initially runs the existing ETL in an approved
   environment. Additional dashboard transformations must be implemented and
   validated before publishing their outputs.
5. Record a batch ID, source receipt times, reconciliation counts, processing
   result, and last successful refresh without recording case-note content
   in logs. Reject or quarantine malformed batches and notify an owner.
6. Publish only validated outputs. Retries must not duplicate records or
   notifications. Preserve the last successful dashboard on failure, but
   visibly mark it stale and display its reporting period.

Power Automate can coordinate intake and notifications, subject to licensing,
connector policies, and mailbox permissions. It does not natively run this
Python package. Managed execution, such as an approved Azure service, is a
later IT-supported option with its own identity, cost, and approval decisions.

## Proposed SharePoint structure

| Component | Purpose | Intended access |
|---|---|---|
| Overview and dashboard | Approved aggregate charts, definitions, reporting period, last successful refresh, limitations | Authorized statewide internal readers |
| Restricted intake library | Original report pairs, receipt metadata, controlled quarantine | Designated processors and administrators |
| JVSG operations workspace | Approved cohort/action data and staff review workflow, once implemented | Staff with a documented business need |
| Processing status list | Sanitized batch status, missing-report indicators, owner and resolution status | Appropriate operators; aggregate refresh status may be shown more broadly |
| Guidance page | Runbook, definitions, ownership, support and escalation | Relevant site users |

Use a separate restricted site if it makes the sensitive-data boundary easier
to administer. Dashboard readers must not inherit access to raw reports.
Filtered views, hidden pages, audience targeting, and dashboard filters are
not authorization controls.

## Visualization choices

| Option | Suitable use | Requirements and limitations |
|---|---|---|
| Excel charts in SharePoint | Lowest-complexity aggregate pilot with periodic updates | Confirm browser display/embedding and refresh behavior. Workbook access must be appropriate for every sheet and underlying record, not just visible charts. |
| SharePoint HTML page | Custom, periodically regenerated aggregate dashboard | Confirm feature availability, site settings, publication permissions, and supported scripts. Not a general-purpose application host. |
| Power BI web part | Interactive analysis and governed row-level security | Requires separate Power BI access and suitable licenses/capacity; SharePoint membership alone is insufficient. |
| SharePoint Framework web part | Future custom interface reading approved data interactively | Requires development and administrator-approved app catalog deployment; unnecessary for the first pilot. |

### Can an HTML site be dropped into a SharePoint folder?

Do not assume an ordinary document library will serve an uploaded HTML
application as a website. Microsoft now documents an HTML publishing feature
in the **Site Pages** library, but rollout and availability must be confirmed
in ADOW's actual tenant/cloud.

Microsoft's current guidance states that uploading existing HTML through
Site Pages does not require a Microsoft 365 Copilot license; Copilot-assisted
creation/editing has separate requirements. A site owner may need to allow
HTML files.

The documented feature does not support arbitrary fetch requests or outbound
API calls and limits external script libraries to specified Microsoft-managed
libraries. Therefore, evaluate it for a generated snapshot with approved
aggregate data, not a live application querying GeoSol or SharePoint APIs.
Validate the upload, update, and publication process using synthetic data.
Do not weaken custom-script settings to bypass restrictions.

Any data embedded in HTML is available to people who can access that file,
even if the interface hides it. Do not embed veteran-level rows and rely on
JavaScript filters for protection.

### Power BI licensing decision

For the SharePoint embedding scenario, Microsoft documents Pro/PPU authoring
requirements and Pro viewer licensing unless qualifying capacity supports
free-user consumption, such as Fabric F64 or higher or Power BI Premium
capacity. PPU content has additional viewer requirements. Confirm the exact
workspace, report, semantic-model, and user entitlements with IT.

Use the secure SharePoint integration, never **Publish to web** for internal
veteran information. Embedding bypasses neither access controls nor licensing.

## Minimum permissions and support to request

| Request | Scope and responsible party |
|---|---|
| Project SharePoint access | Site owner grants page/library/list authoring appropriate to the role; retain access administration with designated owners. No tenant-admin role requested. |
| Access groups | Owners establish separate readers, operational staff, and processors groups using agency identities. Include backup ownership and offboarding. |
| Report delivery | Authorized MIS administrators confirm report scheduling, recipient authorization, reporting period, and supported delivery format. |
| Mailbox connection | IT grants only the mailbox access needed by the approved operator or automation identity. Report-send authority and mailbox-read authority are separate. |
| Power Automate | Confirm maker rights, environment, standard connector entitlements, data policies, connection ownership, and an agency-approved owner plus backup. Premium/custom connectors require separate review. |
| ETL runtime | IT/security approves the live-data execution and storage location; later approve scoped application access if automation is warranted. |
| Visualization | Confirm Excel capabilities, HTML availability and Power BI licenses/capacity before choosing a dependency. |
| Governance | Confirm retention, audit, privacy, accessibility, source ownership, Codespaces policy, and support responsibilities. |

Outlook, SharePoint, and Excel connectors may be usable under existing
entitlements, but "Microsoft 365 enterprise" alone does not establish exact
rights, regional availability, or permission to use a connector.

## Security and operating controls

- "Statewide" means authorized internal users signing in with work accounts,
  not public or anonymous links. Use agency-approved sharing and conditional
  access policies.
- Keep original reports, case notes, and operational data separate from broad
  aggregate reporting. Apply least privilege to both site and underlying data.
- Privacy scrubbing is not a guarantee of anonymity. Review residual
  identifiers and small-group disclosure risks before broader publication.
- Define retention and deletion for inputs, outputs, versions, quarantine,
  backups, and logs with agency records/security staff.
- Restrict sensitive flow inputs/outputs and run-history access; do not expose
  case notes in notifications or error messages.
- Document ownership, recovery, access review, and escalation. Do not make
  production operation dependent on one employee's personal account.
- Keep case interpretation and referrals under qualified human review.

## Phased rollout and acceptance

| Phase | Deliverable | Exit evidence |
|---|---|---|
| 1: Confirm and demonstrate | Inventory the existing workbook; select the approved site, owners, report route, and runtime; demonstrate with synthetic data | Management/IT decisions recorded; reader and processor access tested, including denial of raw-report access for dashboard readers |
| 2: Authorized manual pilot | Process approved report pairs and publish validated aggregate charts | Reconciled counts, documented refresh procedure, stale/failure display, privacy review, and named support owner |
| 3: Automate intake and refresh | Approved mailbox collection and managed processing/publication as justified | Missing-pair and malformed-input handling, safe retries, owner notifications, and recovery demonstrated |
| 4: Extend based on evidence | Evaluate Power BI, custom interfaces, and separately authorized DOL/VOMA work | Defined requirements, appropriate licenses, receiving contracts, security approval, and measured pilot benefit |

Before calling the pilot successful, agree on measures such as processing
time per batch, reconciliation exceptions, refresh reliability, and staff
usability. Any claim about improved follow-up or veteran outcomes needs a
defined baseline and evidence; dashboard activity alone is not that evidence.

## Management decisions requested

Approve or identify owners to resolve:

1. The existing workbook's current status and whether to extend it.
2. The pilot audience, SharePoint location, and sensitive-data boundary.
3. Weekly report delivery, paired-report rules, and operational ownership.
4. The authorized ETL runtime and minimum project permissions.
5. The initial visualization option and tenant/license checks.
6. Pilot scope, acceptance measures, and approval gates for wider rollout.

## Award and future integration alignment

Frame the work as a collaborative Alabama JVSG Veteran Services team
initiative involving the state workforce agency, with management confirming
the eligible nominee wording. **Innovative Initiative** is the proposed
primary focus for the 2027 Merrill Baumgardner Innovation in Information
Technology Award.

The nomination deadline provided for the meeting is **December 4, 2026,
11:59 p.m. ET**. Coordinate the state's single nomination and agency
administrator approval. Report current implementation, demonstrated results,
and future plans separately; use only approved public material.

This project can establish useful data and governance foundations for future
DOL AI-tool integration, but no interoperability or external transmission is
assumed. Any such integration requires a confirmed receiving specification,
authorization, privacy review, and human oversight.

## Microsoft references

Guidance reviewed for this proposal on November 13, 2026; tenant availability,
licensing, and policies still require ADOW confirmation.

- [Create, upload, edit, and publish HTML pages in SharePoint](https://support.microsoft.com/en-us/sharepoint/create-edit-publish-html-pages)
- [Use SharePoint and Power Automate to build workflows](https://learn.microsoft.com/en-us/power-automate/sharepoint-overview)
- [Embed a report web part in SharePoint Online](https://learn.microsoft.com/en-us/power-bi/collaborate-share/office-integration/service-embed-report-spo)
- [Power Automate licensing FAQ](https://learn.microsoft.com/en-us/power-platform/admin/power-automate-licensing/faqs)
- [Excel Online (Business) connector](https://learn.microsoft.com/en-us/connectors/excelonlinebusiness/)
