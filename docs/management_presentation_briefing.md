# A clearer follow-up picture for Alabama's veterans

**Management, IT and legal briefing | Thursday, November 19, 2026**

**Decision requested:** Name an executive sponsor, a nomination lead and a JVSG
review lead. Authorize them to prepare a NASWA nomination for review and define
a limited pilot. This is not approval to process live records, deploy the tool,
or submit a nomination without state agency administrator approval.

## What this would improve

Staff need a quick way to see which veterans may need follow-up, what support
needs are already recorded, and which records still need review. The proposal
turns a report delivery into a consistent, filterable Excel watchlist and gives
managers an easy way to see what changed between deliveries. Staff still interpret
the records and decide what to do. GeoSol remains the system of record.

The value to test is **less time preparing the watchlist, clearer follow-up
visibility, and fewer missed or duplicated review steps**. These are expected
benefits, not measured outcomes.

## What we can show today

| Show | What it proves | What it does not prove |
|---|---|---|
| Two fictional reports arrive in a simulated SharePoint folder. The tool checks their format, matches notes to the supplied roster and scrubs the notes locally. | The prototype can repeat the intake and privacy-processing steps on invented files. | Live SharePoint access, approved live-data handling or demonstrated scrubber effectiveness on real notes. |
| A separate fictional staff-review workbook supplies office, assessment and contact dates, and recorded needs in transportation, housing, health and legal support. | The tool calculates follow-up bands, publishes Excel and HTML with plain-language charts by office, review status and support area (counts written on each bar, long labels wrapped, table alternative for every HTML chart), and verifies that the standard TOON export preserves the profile data. | The native reports do not supply those dashboard profile fields. There is no case-note classification or approved federal interface. |
| The refresh goes from **18 to 19** fictional participants; the 30-or-more-day band goes from **6 to 5**. One record is added and one changes; existing review statuses are preserved. | The refresh picks up known changes in the synthetic inputs. | No real veteran outcome or time saving is implied. |
| Optional AI-assisted briefing on the demo landing page. | An AI model can draft plain-language wording from invented totals only. A person checks it before display; the demo runs offline with or without the wording. | The AI does not read notes, see individual records, calculate the figures, or determine eligibility, referrals or services. |

**Meeting sequence:** Show the paired files and the separate review input; open the
refreshed dashboard and point to the changed counts; show the briefing only if it
has been reviewed; close with the decisions and dates below. If the draft has not
been reviewed, use the standard snapshot comparison and say that no AI copy is
being displayed. See the [recording script](./management_demo_script.md).

## Why consider the NASWA IT innovation award?

The proposed category is the **Merrill Baumgardner Innovation in Information
Technology Award**, presented by NASWA's Technology Committee. The case is
not “we added AI.” It is that a state workforce agency is testing a repeatable,
auditable way to convert existing report deliveries into a staff-owned
follow-up workflow. The use of familiar Excel tools, clear source boundaries,
and optional AI wording could make the approach useful to peer agencies even
if they choose never to use AI.

NASWA's [official awards page](https://www.naswa.org/naswa-awards) confirms
**Friday, December 4, 2026, at 11:59 p.m. Eastern (10:59 p.m. Central)**.
It also states that a state can apply once per award and that a state agency
administrator must approve the nomination. The
[nomination form](https://www.naswa.org/node/159265) requirements were not
independently verified; the nomination lead must check the current form and
confirm whether a prototype at this stage qualifies. The Mobile team's FY 2026
performance recognition is separate and is not evidence that this project won
an award or improved services.

## Path to submission

| By | Proposed owner | What must be ready |
|---|---|---|
| **Thu Nov 19** | Executive sponsor | Assign the nomination lead, JVSG review lead, IT/privacy reviewers and authorized submitter. Reserve a Dec 2 administrator decision slot. |
| **Mon Nov 23** | Nomination lead | Open the current form; confirm prototype eligibility, required evidence, questions, limits, attachments and portal access. Coordinate Alabama's single entry in this category. If eligibility or evidence requirements are unclear, ask NASWA before proceeding. |
| **Wed Nov 25** | JVSG and engineering leads | Assemble approved-for-review synthetic evidence: a short demo clip or screenshots, verified before/after counts, a plain-language data-flow diagram, and a one-page limitations note. Time a like-for-like manual versus prototype refresh on the same invented inputs, including the staff review step. Record the method and actual results if ready; label them rehearsal results, not savings in service delivery. |
| **Mon Nov 30** | Nomination lead; JVSG, IT/privacy and communications reviewers | Complete the form draft and evidence packet. Check each claim against its source; remove unsupported outcome claims and clear every attachment and disclosure for external release. |
| **Wed Dec 2** | State agency administrator | Make the submit-or-defer decision. Proceed only if the form permits the project at its current stage, required evidence is available, claims and attachments are cleared, and approval is recorded. |
| **Thu Dec 3** | Authorized submitter | Submit the approved packet one day early and save the portal confirmation. If the portal fails, contact NASWA promptly and resolve before the Dec 4 cutoff. |

If the form requires operational results the state does not have, **defer the
nomination rather than presenting rehearsal results as live impact**. With
communications approval, retain the cleared synthetic demo for a future
nomination or peer-learning opportunity. Neither a nomination nor an award is
assumed.

For the CI and unit-test process, the Codespaces setup, the SharePoint/Azure
scalability path and the engineering sprint to MVP, see
[Engineering process, scalability path and MVP sprint](./engineering_process_and_mvp_sprint.md).

## Next step for the project, even if the award is deferred

JVSG confirms who supplies the profile fields and which follow-up rules staff
should use. IT and legal confirm approved access, storage, permissions and
retention before any live data is considered. Then a small, authorized pilot can
compare preparation time, data corrections, and timely follow-up against the
current process. Use those results to decide whether to expand; case-note AI,
live SharePoint automation and external interfaces are separate decisions.
