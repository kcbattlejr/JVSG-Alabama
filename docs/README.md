# Documentation Guide

Start here to find the current runbook, project plans, and data-handling rules.
The Python demo is synthetic; the separate SharePoint workbook contains
restricted information and is not approved for general release.

## Operations

- [Management demo runbook](operations/management_demo_runbook.md): run and
  troubleshoot the synthetic rehearsal.
- [SharePoint Excel runbook](operations/sharepoint_demo_site.md): restricted
  workbook, refresh, formulas, and access boundaries.
- [Referral profile setup](operations/referral_profile_setup.md): living
  checklist for SQL steps 28/29, field mapping, open questions, and workbook setup.

## Data And Privacy

- [MIS intake contract](data/mis_intake_contract.md): report formats, validation,
  and typed intake.
- [PII protocol](data/pii_protocol.md): data tiers, scrubbing, and limitations.
- [Security requirements](../SECURITY.md): publication, privacy, and release gates.

## Planning And Briefings

- [MVP scope and approvals](planning/deliverables_and_required_inputs.md):
  deliverables, required inputs, and pilot gates.
- [Engineering process and MVP sprint](planning/engineering_process_and_mvp_sprint.md):
  development and scalability plans.
- [Management briefing](planning/management_presentation_briefing.md): dated
  presentation and decision context.
- [TOON and barrier-diagnosis plan](planning/toon_and_slm_barrier_dx_plan.md):
  proposed export and reviewed findings workflow.

- [Community-partner referral profile plan](planning/community_partner_referral_profile_plan.md):
  decisions and work breakdown for the Nov 30 demo (templates only, no model).

## NASWA Award Submission

- [Nomination draft](naswa/nomination_draft.md): draft award material, not an
  approved submission.
- [Technical paper](naswa/technical_paper.md): ETL, SQL, SharePoint lessons and
  future direction (sanitized, draft).
- [Stakeholder bios](naswa/bios.md): drafts and approval tracker.
- [Video script and screenshots](naswa/video_script_and_screenshots.md).
- [Demo kit](../demo/naswa_demo/README.md): synthetic data and scripts for
  recording screenshots and video elsewhere.

## History And Restricted Material

- [Archive](archive/README.md): historical briefing and recording script.
- MIS SQL, its operational documents, and vendor schema (`docs/sql/`, git-ignored)
  are maintained in restricted private storage and excluded from this repository. Do not copy
  live exports or identifiers into the documentation.
- `docs/source_pdfs/` (git-ignored): third-party and personal source PDFs such as
  LinkedIn exports. Never commit; they contain personal contact details.
