# NASWA Nomination: Demonstration Video Script & Visual Assets Plan

**Submission Companion | Target Runtime: ~2:45 | Paired with [2027_naswa_it_innovation_award_nomination.md](2027_naswa_it_innovation_award_nomination.md)**

---

## Pre-Recording Security & Privacy Checklist

Because NASWA publishes nomination materials publicly, strict visual hygiene is mandatory:
* **Synthetic Data Exclusively:** Record and capture screenshots **only** from the synthetic demonstration workbook (`demo/naswa_demo/`, `seed=3042`). Never display live SharePoint sites, real veteran names, State IDs, live staff usernames, or internal tenant URLs.
* **Screen Hygiene:** Close all extraneous browser tabs, hide bookmarks bars, silence desktop notifications, and verify local file paths contain no PII before recording.
* **Governance Guardrails:** Ensure narration and captions claim **no** measured time savings, formal rule validation, employment outcome gains, production approval, or cross-state adoption.
* **Final Sign-Off:** Obtain leadership review of the final video cut and still images prior to submission.

---

## Storyboard & Narration Script (~2:45)

| Timestamp | Visual / Screen Capture | Voiceover Narration |
|---|---|---|
| **0:00–0:15** | **Title Card:** *"JVSG Follow-Up Visibility: No Veteran Left Behind"* — Alabama Department of Workforce, Employment Services Division | "Alabama's Jobs for Veterans State Grant team—led by Employment Services Director Kevin Kidd, State JVSG Coordinator Hank Lahti, and Mobile Workforce Specialist Keith Battle—is turning case-note visibility into a statewide campaign to leave no veteran behind." |
| **0:15–0:40** | **Problem & Opportunity Graphic:** Enrolled JVSG placements vs. non-case-managed veterans in narrative case notes | "JVSG works—delivering strong employment outcomes for eligible veterans in formal case management. Yet veterans assessed at intake who do not qualify for formal case management often disappear from standard reports, creating an opportunity to identify trends and serve those facing high challenges." |
| **0:40–1:05** | **Architecture Diagram:** Read-only MIS export $\rightarrow$ schema validation $\rightarrow$ deterministic ETL $\rightarrow$ Excel dashboard $\rightarrow$ staff review | "Working within strict read-only database rules, our pipeline anchors on note authorship rather than enrollment, validates each export, applies transparent rules, and surfaces actionable queues in Excel—while keeping GeoSol intact as the system of record." |
| **1:05–1:35** | **Demo Screen 1 (Synthetic):** Management *Overview* & *Offices and Age* tabs showing suppressed aggregate counts and cohort distributions | "Using synthetic demonstration data, leadership gains immediate visibility into non-case-managed cohort trends across offices and age bands—protected by automatic small-cell suppression to safeguard veteran privacy." |
| **1:35–2:00** | **Demo Screen 2 (Synthetic):** *Drilldown* & *Watchlist* views with freshness badges and overdue bands | "Frontline specialists filter directly into overdue follow-up queues, while built-in freshness indicators confirm exactly how current the underlying data export is." |
| **2:00–2:20** | **Demo Screen 3 (Synthetic):** Structured barrier profile (`Training`, `Housing`, `Medical`, `Legal`) and fixed-template referral brief | "Deep-diving structured barrier profiles surfaces housing, medical, legal, or training obstacles—powering a statewide campaign to connect veterans with community partners and execute timely follow-ups. The tool uses no AI models, mines no free-text notes, and never sends referrals automatically." |
| **2:20–2:40** | **Governance Slide:** Synthetic testing vs. access-controlled SharePoint; human decision-making | "All development and testing used synthetic data. Inside operations, live exports remain isolated within Alabama's access-controlled JVSG SharePoint environment—where human case managers interpret every record and guide every referral." |
| **2:40–2:55** | **Closing Card:** Alabama Department of Workforce logo & nomination contact `[to be added]` | "A transparent, low-cost blueprint any state workforce agency can deploy immediately: validate inputs, surface cohort trends, mobilize community referrals, and keep people in charge." |

---

## Required Still Screenshots (Synthetic Dataset Only)

1. **Management Overview (`Overview` & `Offices & Age` tabs)**
   * *Focus:* High-level cohort distribution, age/office trend breakdown, and `"Suppressed"` cells for groups where $n < 10$.
   * *Caption:* "Figure 1: Management summary dashboard illustrating non-case-managed cohort trends and small-cell privacy suppression (synthetic demonstration data)."
2. **Staff Follow-Up Drilldown (`Drilldown` / `Watchlist` tabs)**
   * *Focus:* Multi-filter queue (`Office`, `Follow-Up Band`, `Staff`) alongside prominent data-freshness timestamps.
   * *Caption:* "Figure 2: Actionable staff follow-up queue with data-freshness indicators and deterministic timeliness bands (synthetic demonstration data)."
3. **Human-in-the-Loop Referral Brief (`Profile` tab)**
   * *Focus:* Four-domain barrier summary (`Training`, `Housing`, `Medical`, `Legal`) paired with the unverified draft referral template.
   * *Caption:* "Figure 3: Structured barrier profile and fixed-template community partner referral brief supporting statewide outreach (synthetic demonstration data)."
4. **End-to-End Architecture & Privacy Diagram**
   * *Focus:* Clean vector diagram illustrating `MIS Read-Only SQL` $\rightarrow$ `Schema Validation` $\rightarrow$ `Tiered SharePoint (/manager vs. /restricted)` $\rightarrow$ `Excel Online` $\rightarrow$ `Human Reviewer`.
   * *Caption:* "Figure 4: Three-tier data governance architecture preserving GeoSol as the authoritative system of record."
5. **Schema Validation Guardrail**
   * *Focus:* Power Query validation check confirming required column headers or halting cleanly on malformed input.
   * *Caption:* "Figure 5: Automated schema contract validation preventing silent data drift during refresh."

---

## Pre-Submission Action Items

* `[ ]` Insert approved nomination contact name, email, and phone number on the closing video card.
* `[ ]` Verify synthetic workbook (`seed=3042`) contains zero stray live labels before screen capture.
* `[ ]` Secure formal approval and public-posting consent (`2027_naswa_it_innovation_award_nomination.md` §§ 8–9) for final video and image files.