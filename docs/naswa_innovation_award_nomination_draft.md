# NASWA 2027 Merrill Baumgardner Innovation in Information Technology Award: draft answers

**Status: DRAFT for review, November 19, 2026.** Proposed text only. Nothing here is
approved for submission or external release. Deadline: **Fri Dec 4, 2026, 11:59 p.m.
ET**; internal plan is submission Dec 3 after administrator approval Dec 2 (see the
[stakeholder briefing](./management_presentation_briefing.md#path-to-submission)).

## Gates before use

1. **Eligibility.** The project is a synthetic-data prototype. The nomination lead must
   confirm with NASWA that a pre-operational initiative qualifies. If the form requires
   operational results, **defer** rather than present rehearsal results as live impact.
2. **Roles and names.** The people and roles below are assumptions to confirm. Titles
   are Kevin Kidd (Director – Employment Services) and Hank Lahti (JVSG Coordinator – Alabama);
   confirm each approves being named.
3. **Claims.** Every statement must match a source in this repository. No savings,
   outcome, or award claims are made. The Mobile team's FY 2026 recognition is a
   separate matter and is not cited.
4. **Public posting.** Question 8 allows NASWA to publish the nomination. Clear all text and
   attachments with communications, privacy and legal review first ([SECURITY.md](../SECURITY.md)).
   Use only synthetic material: no veteran names, SIDs, SSNs, case notes, GeoSol exports,
   or internal infrastructure details.

## 1. Contact information

| Field | Proposed entry |
|---|---|
| First / Last name | *Nomination lead or authorized submitter (to be assigned by the executive sponsor)* |
| Email | *Submitter's agency email* |
| Full agency name | Alabama Department of Workforce (ADOW) |

Confirm the agency's legal name and the Alabama single-entry coordination for this category.

## 2. Name of initiative

**JVSG Follow-Up Visibility Initiative: a staff-owned, privacy-first watchlist for Alabama's
Jobs for Veterans State Grant**

Short form: *JVSG Follow-Up Watchlist*. Alternate: *Clear Follow-Up for Alabama's Veterans*.

## 3. Significant contributions in information technology (limit 200 words)

> ADOW's Jobs for Veterans State Grant (JVSG) program is piloting a repeatable, auditable way to turn existing report deliveries into a staff-owned follow-up workflow. The initiative, led by Kevin Kidd, Director – Employment Services, and Hank Lahti, JVSG Coordinator – Alabama, and developed by Keith Battle, Workforce Specialist – Veteran Services, validates paired MIS reports, matches case notes to the supplied roster, and scrubs notes locally. Deterministic rules then produce an Excel watchlist, an HTML dashboard with plain-language charts, and a lossless TOON data export. Each refresh shows what changed while preserving staff review statuses.
>
> The design choices are what peer states can reuse: familiar Excel tools, typed and deterministic Python, no network calls in tests, continuous-integration gates, and synthetic data only. An optional AI step drafts wording from invented aggregate totals only; a person reviews it before display, and the tool works without it. AI never reads notes, determines eligibility or makes referrals. GeoSol remains the system of record, and staff make every case decision.
>
> The prototype runs entirely on fictional data. Live use awaits IT, privacy and legal approval.

*(about 175 words)*

## 4. Implementation timeline and accomplishments (limit 200 words)

> **Nov 6–8, 2026:** Privacy-preserving intake of paired MIS reports; PII protocol, scrubbing pipeline and synthetic MIS data; protected native tooling and a reproducible Codespaces/WSL environment.
>
> **Nov 14:** Reproducible management demonstration: follow-up bands, Excel and HTML dashboards, and a TOON export verified by exact round trip.
>
> **Nov 18:** Accessible charts (labeled counts, table alternatives); safeguards that preserve the last verified output if a refresh fails; presentation materials and runbook.
>
> **Quality controls:** Every change runs lint, strict type checking and about 79 automated tests on a clean runner with no secrets or network access.
>
> **Nov 19:** Presented to agency management, IT and legal for sponsor decisions.
>
> **Demonstrated on fictional data:** a refresh from 18 to 19 participants, with one record added, one changed and review statuses preserved.
>
> **Next:** an authorized one-team pilot measuring preparation time, data corrections and timely follow-up against the current process. SharePoint automation, case-note AI and external interfaces are separate future decisions. No live results are reported yet.

*(about 150 words; adjust dates if the form's cutoff differs)*

## 5. Contribution to the workforce development community and the state (limit 200 words)

> Within Alabama, the initiative gives JVSG staff a faster, consistent view of which veterans may need follow-up and which support needs (transportation, housing, health, legal) are already recorded, and which records still need review. It is designed to reduce manual watchlist preparation and missed or duplicated review steps. These are expected benefits that the pilot will test, not measured outcomes.
>
> For the wider community, the project offers a transferable pattern rather than a product: a privacy-first intake, deterministic and explainable follow-up rules, standard open formats, and a clear boundary between automation and human judgment. The documentation covers data tiers, a PII protocol, an intake contract, a security and publication policy, and a demonstration runbook. ADOW is prepared to share the cleared synthetic demonstration and these practices with peer agencies, whether or not they use AI.
>
> The effort also builds internal capacity: a program specialist developing data-science skills as part of a Master's thesis (Western Governors University, expected January 2027), working with IT, privacy and legal reviewers.

*(about 170 words. Check the thesis reference with Keith before publishing, because the form is posted publicly.)*

## 6. Samples of work (max 10 files, 10 MB each)

All files must be synthetic, reviewed and exported as PDF, MP4, PNG or XLSX.

| # | Proposed file | Source / how to produce | Purpose |
|---|---|---|---|
| 1 | One-page initiative summary (PDF) | Condense the [stakeholder briefing](./management_presentation_briefing.md) | Overview |
| 2 | Plain-language data-flow diagram (PNG/PDF) | New; paired reports → local scrub → staff review → Excel/HTML; mark GeoSol as system of record | Shows design and privacy boundary |
| 3 | Demo video, 2–3 min (MP4) | Follow the [recording script](./management_demo_script.md); synthetic data only | Shows the workflow |
| 4 | Dashboard screenshots (PNG or PDF) | `python -m jvsg_triage.demo rehearse` → `temp/management-demo/` | Charts by office, review status and support area |
| 5 | Sample Excel watchlist (XLSX) | Same output, synthetic only | Shows the staff-facing product |
| 6 | Before/after refresh comparison (PDF) | 18 → 19 participants; 30+ day band 6 → 5 | Shows change tracking and preserved statuses |
| 7 | Limitations and governance note (PDF) | [Deliverables checklist](./deliverables_and_required_inputs.md) | Shows responsible scoping and human review |
| 8 | Privacy design summary (PDF) | Excerpt from the [PII protocol](./pii_protocol.md) with internal details removed | Shows data protection |
| 9 | Engineering process summary (PDF) | [Engineering process](./engineering_process_and_mvp_sprint.md): CI gates, tests, environment | Shows quality and repeatability |
| 10 | Pilot plan (PDF) | One-page plan from the briefing's "Next step" | Shows the path to measured results |

Optional: a time comparison of a manual versus prototype refresh on the same invented
inputs, labeled "rehearsal result, not service-delivery savings," only if completed by Nov 25.

Pre-upload check for each file: no real data, no tenant/account/infrastructure names, no
private cohort profiles or validation metrics, accessible formatting, and review sign-off.

## 7. State agency administrator approval (max 2 files)

- Email or signed memo from the ADOW state agency administrator approving this nomination
  (file 1). Request it by Nov 30, with the decision on Dec 2.
- Optional (file 2): a short sponsor/privacy/legal clearance email covering the attachments.

The approval must reference the initiative name, the category and the attached packet.

## 8. Consent

Check **"I understand and consent"** only after the administrator and communications have
cleared the text and attachments for public posting.

## Submission checklist

- [ ] NASWA confirms prototype eligibility (or the nomination is deferred)
- [ ] Names, titles and thesis reference approved by each person named
- [ ] Each claim traced to a repository source; no outcome claims
- [ ] Files 1–10 cleared and under size limits; file count within limits
- [ ] Administrator approval saved; submitted Dec 3; portal confirmation saved
