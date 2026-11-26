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

**Selected Criterion: Innovative Initiative** — *A technology-enabled operational workflow addressing a critical frontline service delivery gap in veteran case management.*

*(Note for approvers: Confirm criterion alignment with the agency administrator. Because this initiative is an operational prototype, no measured customer outcomes are claimed.)*

---

## 4. Significant Contribution in Information Technology

> State workforce agencies routinely capture rich frontline veteran interactions inside narrative case notes, yet legacy Management Information Systems (MIS) rarely translate that activity into actionable follow-up queues. In Alabama, existing service-based reports missed veterans whose outreach was documented solely through narrative notes—creating a critical visibility gap for veterans assessed but not yet enrolled in formal case management.
>
> To close this gap without costly infrastructure procurement or invasive database modifications, Alabama's Jobs for Veterans State Grant (JVSG) team engineered a lightweight, auditable Extract, Transform, Load (ETL) and visualization pipeline built entirely on existing enterprise tools. Operating within strict read-only database constraints, the workflow extracts structured metadata from note activity via single-statement SQL queries, enforces schema validation and strict role-based data segregation inside SharePoint, transforms records deterministically via Power Query, and delivers dual-tier dashboards in Excel Online.
>
> A second goal is to improve communication between the two roles on the Mobile team: the Workforce Specialist, who focuses on veteran case management, and the Workforce Outreach Specialist, who focuses on business development. The tool makes case-management data easier for both to access, so employer outreach can be matched to veterans who are ready for placement without opening multiple MIS windows.
>
> The architecture separates operational needs from executive oversight: frontline staff access an action-oriented follow-up worklist with data-freshness indicators and a rule-based referral brief, while managers view suppressed, aggregate cohort metrics that protect individual privacy. By designing around deterministic rules, automated schema checks, and human-in-the-loop governance, the system leaves GeoSol intact as the authoritative system of record. The current implementation uses no large language models, performs no free-text mining of case notes, and triggers no automated external referrals—demonstrating how state agencies can achieve high-impact operational visibility safely, transparently, and at near-zero marginal cost.

---

## 5. Implementation Timeline and Accomplishments

> **2026 — Frontline Discovery and Program Recognition:**
> The initiative originated from frontline service delivery by the Mobile JVSG team—Keith Battle and Workforce Outreach Specialist for Veteran Services Robert Stratton—during their first year of service to the state. In October 2026, the team received the JVSG Team Incentive Award `[Confirm exact award title, date, and presenter]` and presented their intake-triage methodology at statewide JVSG training in Montgomery `[Confirm exact date and audience]`. Through daily outreach, the team identified a systemic bottleneck: veterans assessed at intake but not yet enrolled in formal case management risked falling through the cracks when contact tracking relied on manual spreadsheet preparation.
>
> *Baseline Operational Context (Pre-Initiative Team Performance):* Prior to deploying the dashboard, the Mobile JVSG team's frontline outreach generated approximately $2.24 million in combined annualized wages for veterans entering employment across the first three quarters of 2026 (self-reported MIS Entered Employment data; hourly, weekly, and annual wages standardized to annual equivalents):
>
> | 2026 Reporting Period | Veterans Placed | Combined Annualized Wages |
> |---|---|---|
> | Q1 (Jan–Mar) | 21 | $988,794.80 |
> | Q2 (Apr–Jun) | `[confirm]` | $474,801 |
> | Q3 (Jul–Sep) | 13 | $777,886 |
> | Q4 (Oct–Dec) | Pending close | Pending close |
> | **Q1–Q3 Subtotal** | **`[confirm]`** | **$2,241,481.80 (~$2.24M)** |
>
> *(Governance Note: Confirm fiscal vs. calendar quarter alignment and the Q2 placement count. Q2 was manually tabulated from the Veteran Status and Case Management reports and supersedes the figure in the submitted Quarterly Manager's Report; Q3 reflects 13 successful case closures. These supersede the September newsletter's preliminary "> $700,000" Q3 estimate. These metrics contain no veteran identifiers, predate the software tool, and are presented strictly as baseline operational context rather than measured software outcomes.)*
>
> **November 2026 — Architecture, Engineering, and Safeguard Validation:**
> Designed and built the end-to-end ingestion, validation, and visualization pipeline. Key technical milestones included:
> * Developing read-only, single-`SELECT` SQL queries to define the active veteran cohort via note authorship rather than service enrollment.
> * Implementing strict schema-validation contracts in Power Query and an offline automated test suite (Pytest and Node.js) to prevent silent data drift or query failures.
> * Engineering an Excel Online presentation layer powered by Office Scripts and dynamic formulas (`AGGREGATE`, `XLOOKUP`, `SWITCH`) to deliver ranked watchlists, multi-filter drilldowns, and fixed-template community referral briefs.
> * Building a synthetic data generator (`demo/naswa_demo/`) to enable full end-to-end testing, training, and public demonstration without exposing Personally Identifiable Information (PII).
>
> **November 30, 2026 — Leadership Demonstration and Review:**
> `[Post-demo update: Record exact demonstration date, confirmed scope, and stakeholder sign-off.]`
>
> **Data Governance and Production Posture:**
> All software development, automated testing, and public demonstration artifacts rely exclusively on synthetic data. While the pipeline currently operates on live veteran exports inside Alabama's access-controlled JVSG SharePoint environment, no live veteran records exist in source control or public materials. Operating on live exports demonstrates technical feasibility; formal accuracy validation, production scheduling approval, and measured service outcomes are scoped for a subsequent evaluation phase and are not claimed here.

---

## 6. Contribution to the Workforce Development Community and State

> **Direct Operational Value to Alabama:**
> For JVSG specialists and LVERs, the dashboard replaces ad-hoc, error-prone spreadsheet manipulation with a standardized, repeatable daily workflow. Freshness indicators immediately alert staff to the currency of underlying MIS exports, while deterministic follow-up bands (Current, Due Soon, Overdue) prioritize outreach so no veteran is inadvertently overlooked. Additionally, the integrated referral brief translates structured profile fields into standardized partner-referral language—helping qualified staff connect veterans with community organizations to resolve housing, medical, legal, or training barriers before job placement. Crucially, human judgment remains central: staff review, edit, and approve every referral brief manually.
>
> **Bridging Case Management and Business Services:**
> The dashboard gives case managers and business-services staff a shared, plain view of the same follow-up data. The Workforce Specialist can surface veterans who are ready for employer referral, and the Workforce Outreach Specialist can see who is available when engaging employers, replacing ad-hoc handoffs. Staff still review every referral and placement decision.
>
> **A Replicable Blueprint for State Workforce Agencies:**
> Many state workforce agencies operate under identical architectural constraints: legacy MIS platforms with read-only reporting windows, strict PII boundaries, limited IT budgets, and restricted access to cloud automation suites. Rather than offering a proprietary black-box product, Alabama's initiative provides a transparent, vendor-neutral engineering pattern that any state can replicate using existing Microsoft 365 and SQL tools:
> 1. **Validate inputs rigorously** using schema contracts before transformation.
> 2. **Apply transparent, deterministic rules** decoupled from presentation layers.
> 3. **Enforce privacy by design** by separating row-level operational queues from cell-suppressed executive summaries.
> 4. **Keep humans in the loop** for all case interpretation and partner outreach.
>
> *(Scope Note: A separately authorized pilot will evaluate preparation time savings, data-hygiene improvements, and contact timeliness against legacy workflows. No cross-state adoption or measured outcome gains are claimed at this stage.)*

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