# 2027 NASWA Merrill Baumgardner Innovation in Information Technology Award

**Submission-Ready Draft | Alabama Department of Workforce**

> **Pre-Submission Governance Note:** NASWA publishes winning and nominated entries publicly to promote cross-state replication. Verify that every name, metric, and attachment is formally approved for public release before final submission. The nominee must be the state workforce agency (or an agency-led initiative), and a single primary evaluation criterion must be selected.

---

## 1. Nominee and Contact Information

* **State Workforce Agency / Nominee:** Alabama Department of Workforce, Employment Services Division
* **Initiative / Program:** Alabama Jobs for Veterans State Grant (JVSG)
* **Project Leads:**
  * Kevin Kidd, Director, Employment Services Division (Executive Sponsor)
  * Henry "Hank" Lahti, State JVSG Coordinator, Alabama JVSG (Program Owner)
  * Keith Battle, Workforce Specialist – Veteran Services, Mobile Veterans Employment Team (Lead Architect & Developer)
* **Nomination Contact:** `[Name and title — to be added]`
* **Email / Phone:** `[Agency contact info — to be added]`
* **State Agency Administrator:** Kevin Kidd, Director, Employment Services Division `[Unconfirmed placeholder: Greg Reed, Secretary of Workforce, State of Alabama, may be the required signatory. Confirm agency approval protocol.]`

---

## 2. Initiative Name

**JVSG Follow-Up Visibility: No Veteran Left Behind Through Auditable ETL and Data Visualization**

*(Alternative short title: "No Veteran Left Behind: JVSG Follow-Up Visibility")*

---

## 3. Primary Evaluation Criterion

**Selected Criterion: Innovative Initiative** — *A technology-enabled operational workflow turning passive case-note records into an active statewide re-engagement, partner-referral, and cohort-profiling system to ensure no veteran is left behind.*

*(Note for approvers: Confirm criterion alignment with the agency administrator. Because this initiative is an operational prototype deploying into a statewide outreach campaign, no measured customer outcome gains are claimed.)*

---

## 4. Significant Contribution in Information Technology

> Alabama's Jobs for Veterans State Grant (JVSG) program consistently delivers strong employment outcomes for eligible veterans enrolled in formal case management. However, under federal statutory eligibility rules (38 U.S.C. § 4103A and U.S. Department of Labor VETS guidance), intensive JVSG case management is strictly reserved for veterans who attest to qualifying Significant Barriers to Employment (SBEs) or belong to designated priority populations. Consequently, veterans who engage with JVSG staff during initial triage—and have their interactions documented in narrative case notes—but are ineligible for or not yet enrolled in formal case management disappear from standard service-based operational reports.
>
> Rather than treating that statutory boundary as an operational blind spot, Alabama's JVSG team turned it into an opportunity to leave no veteran behind and better serve those facing high challenges. Without costly infrastructure procurement or invasive database modifications, the team engineered a lightweight, auditable Extract, Transform, Load (ETL) and visualization pipeline built entirely on existing enterprise tools. Operating within strict read-only database constraints, the workflow extracts structured metadata from note activity via single-statement SQL queries (`Step 17`), pairs that cohort with structured demographic and intake barrier fields (`Step 29`), enforces schema validation and strict role-based data segregation inside SharePoint, transforms records deterministically via Power Query, and delivers dual-tier dashboards in Excel Online.
>
> This architecture accomplishes three immediate operational goals:
> 1. **Statewide Re-Engagement & Community Partner Referrals:** By surfacing non-case-managed veterans who still face real-world stability challenges—across housing, medical, legal, and training domains—the tool enables regional JVSG specialists and Local Veterans' Employment Representatives (LVERs) to execute a coordinated statewide campaign of warm community-partner referrals and structured follow-ups.
> 2. **Descriptive Profile Trend Analysis:** Aggregating structured intake and barrier indicators across this previously invisible cohort gives state leadership a clear lens into regional service gaps, co-occurring barrier clusters, and age or office attrition patterns—without mining free-text case notes or exposing individual Personally Identifiable Information (PII).
> 3. **Case-Management-to-Business-Services Alignment:** The dashboard gives case managers and business-services outreach specialists a shared, quickly readable view of the same veterans, allowing employer outreach to target placement-ready veterans without navigating multiple Management Information System (MIS) screens.
>
> The architecture separates operational execution from executive oversight: frontline staff access an action-oriented follow-up worklist with data-freshness indicators and a fixed-template referral brief, while managers view cell-suppressed, aggregate cohort metrics that protect individual privacy. By designing around deterministic rules, automated schema checks, and human-in-the-loop governance, the system leaves GeoSol intact as the authoritative system of record. The current implementation uses no large language models, performs no free-text mining of case notes, and triggers no automated external referrals—demonstrating how state agencies can mobilize high-impact veteran outreach safely, transparently, and at near-zero marginal cost.

---

## 5. Implementation Timeline and Accomplishments

> **2026 — Proven Frontline Performance and Discovery of the Non-Case-Managed Opportunity:**
> The initiative originated from frontline service delivery by the Mobile JVSG team—Keith Battle and Workforce Outreach Specialist for Veteran Services Robert Stratton—during their first year of service to the state. In October 2026, the team received the JVSG Team Incentive Award `[Confirm exact award title, date, and presenter]` and presented their intake-triage methodology at statewide JVSG training in Montgomery `[Confirm exact date and audience]`.
>
> *Baseline Operational Context (Pre-Initiative Team Performance):* Alabama's JVSG model works well for enrolled veterans. Prior to deploying the dashboard, the Mobile JVSG team's frontline outreach generated approximately $2.24 million in combined annualized wages for veterans entering employment across the first three quarters of 2026 (self-reported MIS Entered Employment data; hourly, weekly, and annual wages standardized to annual equivalents):
>
> | 2026 Reporting Period | Veterans Placed | Combined Annualized Wages |
> |---|---|---|
> | Q1 (Jan–Mar) | 21 | $988,794.80 |
> | Q2 (Apr–Jun) | `[confirm]` | $474,801 |
> | Q3 (Jul–Sep) | 13 | $777,886 |
> | Q4 (Oct–Dec) | Pending close | Pending close |
> | **Q1–Q3 Subtotal** | **`[confirm]`** | **$2,241,481.80 (~$2.24M)** |
>
> *(Governance Note: Confirm fiscal vs. calendar quarter alignment and the Q2 placement count. Q2 was manually tabulated from the Veteran Status and Case Management reports and supersedes the figure in the submitted Quarterly Manager's Report; Q3 reflects 13 successful case closures. These supersede the September newsletter's preliminary "> $700,000" Q3 estimate. These metrics contain no veteran identifiers, predate the software tool, and are presented strictly as baseline operational context demonstrating core JVSG performance rather than measured software outcomes.)*
>
> Through daily operations, the Mobile team recognized that while enrolled veterans were achieving strong placement outcomes, veterans who were assessed at intake but were ineligible for—or not yet enrolled in—formal JVSG case management lacked automated follow-up tracking and risked slipping through the cracks between manual spreadsheet reviews.
>
> **November 2026 — Architecture, Engineering, and Safeguard Validation:**
> Designed and built the end-to-end ingestion, validation, and visualization pipeline. Key technical milestones included:
> * Developing read-only, single-`SELECT` SQL queries (`Steps 17, 21, 28, 29`) to define the active veteran cohort via note authorship rather than service enrollment and extract structured intake barrier fields.
> * Implementing strict schema-validation contracts in Power Query and an offline automated test suite (Pytest and Node.js) to prevent silent data drift or query failures.
> * Engineering an Excel Online presentation layer powered by Office Scripts and dynamic formulas (`AGGREGATE`, `XLOOKUP`, `SWITCH`) to deliver ranked watchlists, multi-filter drilldowns, aggregate age/office matrices, and fixed-template community referral briefs.
> * Building a synthetic data generator (`demo/naswa_demo/`) to enable full end-to-end testing, training, and public demonstration without exposing PII.
>
> **December 2026 — Statewide Outreach Campaign and Profile Trend Deep-Dive:**
> `[Post-demo update: Record exact leadership demonstration date and sign-off.]`
> Because the architecture relies entirely on existing enterprise tools, Alabama moved directly from prototype validation into an immediate statewide operational campaign led by State JVSG Coordinator Henry "Hank" Lahti:
> * **Cohort Discovery & Profile Analysis:** Running `Step 17` and `Step 29` statewide to surface non-case-managed veterans with overdue follow-up intervals and deep-dive their structured barrier profiles (housing, medical, legal, and training) across offices and age bands to identify regional trends and high-challenge cohorts.
> * **Coordinated Community Partner Referrals:** Equipping JVSG specialists and LVERs statewide with standardized, human-reviewed referral briefs (`Profile` tab) to connect identified veterans with community partners, Veteran Service Organizations (VSOs), and American Job Center (AJC) programs.
> * **Structured Follow-Up Execution:** Utilizing the `Watchlist` and `Drilldown` queues to conduct targeted follow-up outreach and document re-engagement directly inside GeoSol.
>
> **Data Governance and Production Posture:**
> All software development, automated testing, and public demonstration artifacts rely exclusively on synthetic data. While the pipeline currently operates on live veteran exports inside Alabama's access-controlled JVSG SharePoint environment to support the statewide outreach campaign, no live veteran records exist in source control or public materials. Operating on live exports demonstrates immediate operational utility and technical feasibility; formal accuracy validation, production scheduling approval, and measured service outcomes are scoped for a subsequent evaluation phase and are not claimed here.

---

## 6. Contribution to the Workforce Development Community and State

> **Direct Operational Value to Alabama — Leaving No Veteran Behind:**
> Alabama's JVSG specialists already achieve strong employment results for eligible veterans in case management. This initiative extends that standard of care to veterans outside formal case management who still face substantial life and employment barriers. For JVSG specialists and LVERs, the dashboard replaces ad-hoc, error-prone spreadsheet manipulation with a standardized, repeatable daily workflow. Freshness indicators immediately alert staff to the currency of underlying MIS exports, while deterministic follow-up bands (`Current`, `Due soon`, `Overdue`) prioritize outreach so no veteran is inadvertently overlooked. Simultaneously, the integrated referral brief translates structured profile fields into standardized partner-referral language—helping qualified staff connect high-challenge veterans with community organizations to resolve housing, medical, legal, or training barriers. Crucially, human judgment remains central: staff review, edit, and approve every referral brief manually.
>
> **Cohort Trend Intelligence & Business-Services Alignment:**
> Deep-diving the structured profiles of non-case-managed veterans gives state leadership actionable visibility into who is seeking services outside traditional case-management pipelines—highlighting recurring barrier clusters, demographic patterns, and regional follow-up bottlenecks so community partnerships can be targeted where need is greatest. At the local office level, the dashboard also gives case managers and business-services staff a shared, plain view of the same follow-up data, ensuring employer outreach is aligned with placement-ready veterans without ad-hoc handoffs.
>
> **A Replicable "Day-One" Blueprint for State Workforce Agencies:**
> Every state JVSG program operates under the same federal statutory eligibility boundaries (38 U.S.C. § 4103A) and similar legacy MIS constraints: read-only reporting windows, strict PII boundaries, limited IT budgets, and restricted access to cloud automation suites. Rather than offering a proprietary black-box product or waiting years for a core MIS rewrite, Alabama's initiative provides a transparent, vendor-neutral engineering pattern that any state can deploy immediately using existing Microsoft 365 and SQL tools:
> 1. **Anchor on note activity (`Step 17`)** to capture veterans who fall outside formal case-management enrollment reports.
> 2. **Validate inputs rigorously** using schema contracts before transformation.
> 3. **Profile structured barriers deterministically (`Step 29`)** to spot cohort trends and power standardized community referrals without free-text note mining.
> 4. **Enforce privacy by design** by separating row-level operational queues from cell-suppressed executive summaries, keeping humans in the loop for every outreach and referral decision.
>
> *(Scope Note: A separately authorized evaluation phase will measure preparation time savings, data-hygiene improvements, and contact timeliness against legacy workflows. No cross-state adoption or measured outcome gains are claimed at this stage.)*

---

## 7. Samples of Work

**Submission Attachments (Public-Safe / Synthetic Data Only):**
*Confirm NASWA file-count, format, and size limits prior to upload. Never attach files from local working folders (`temp/Demo/`).*

| Deliverable | Status / Reference |
|---|---|
| **1. Management Overview Screenshot** | `[Attach approved synthetic screenshot: Cohort & office summary with small-cell suppression]` |
| **2. Staff Follow-Up Drilldown Screenshot** | `[Attach approved synthetic screenshot: Filtered follow-up queue & freshness indicators]` |
| **3. Demonstration Video (2–3 min)** | `[Attach approved MP4 & transcript recorded from synthetic demo kit]` (Script: `video_script_and_visual_assets_plan.md`) |
| **4. Technical Architecture Paper** | `technical_paper_jvsg_follow_up_visibility.md` (Export to PDF after final sanitization review) |
| **5. Data-Flow & Governance Diagram** | `[Attach diagram: MIS Read-Only Export → Validation → Tiered SharePoint → Excel → Staff Review]` |
| **6. Stakeholder Biographies** | `stakeholder_biographies_naswa_submission.md` (Include only approved bios) |
| **7. Reproducible Synthetic Demo Kit** | `demo/naswa_demo/README.md` (Synthetic generator scripts, Power Query & Office Scripts) |

---

## 8. State Agency Administrator Approval

**Approval Statement:**
`[Insert signed approval statement from the State Agency Administrator confirming nomination endorsement, selected award category (Innovative Initiative), and initiative title.]`

---

## 9. Public-Posting Consent

`[Confirm formal consent only after the agency administrator and all named stakeholders have reviewed and approved the final narrative, biographies, and visual attachments for public posting on NASWA's website.]`