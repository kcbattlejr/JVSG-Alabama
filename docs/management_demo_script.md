# Management / IT / legal recording script

**Target:** Friday, November 20, 2026. **Length:** approximately 8 minutes.
**Format:** recorded screen demonstration for a Teams meeting.
Use the [runbook](./management_demo_runbook.md) for all commands and definitions.

## Before recording

- Activate the environment and run the complete `rehearse` command.
- Confirm the verification message and the 18/19 expected participant counts.
- Open the generated landing page, both dashboards and refreshed Excel workbook.
  Keep the technical data and verification report available only for IT questions.
- Enlarge the browser to 125% or a readable recording resolution. Collapse
  unrelated windows, notifications, account menus and file explorers.
- Keep only generated synthetic files on screen. Do not open the Gemini
  references: they contain statements and figures not used in this demo.
- Do not display `.env`, private data, native live reports, tenant addresses,
  personal messages or infrastructure/account assignments.
- Rehearse once without recording. This is not a live tenant connectivity demo.

## 0:00-0:45 | Purpose and honest boundaries

**Show:** first report, fictional-demonstration banner and plain-language summary.

**Say:**

> This is a working synthetic prototype of a SharePoint-first Excel workflow.
> Our intended MVP starts with an approved cloud workbook as the main driver,
> not a new web application. Today I am simulating delivery of that workbook
> locally so the demonstration is repeatable and contains no live veteran data.
> We are demonstrating real data processing and generated Excel and HTML outputs,
> not claiming a deployed agency system.

## 0:45-1:45 | The workbook drives the pipeline

**Show:** generated `simulated_sharepoint/baseline.xlsx`, `Demo Intake` sheet.
Zoom to the column headers and first few invented IDs.

**Say:**

> This is the stand-in for a snapshot of the SharePoint Excel source. Each row
> has a made-up participant number and office, assessment and last-contact dates,
> transportation, housing, health and legal support needs, and a staff-review
> status. The columns and values are written out in full. There are no names,
> real participant identifiers,
> contact details or case narratives. These are invented examples, not real
> caseload proportions.
>
> The input contract is deliberately strict. Unknown values, duplicate IDs,
> formulas, future dates and malformed workbooks fail visibly rather than
> generating a plausible-looking dashboard. A real agency workbook needs its
> own approved mapping; we have not assumed this is its existing layout.

## 1:45-2:40 | Run the workbook processing

**Show:** terminal with only the baseline `run` command from the runbook.
Run it, then show `latest.json` and the successful `status.json`.

**Say:**

> This is the actual processing, not a slideshow. It checks the workbook,
> calculates days since contact for the report date, and creates a checked report.
> We use calendar days since contact, falling back to assessment
> when there is no contact. The 15- and 30-day thresholds are demo assumptions,
> not a new approved operational policy.
>
> There are no cloud credentials or model calls in this execution. A successful
> output is a real workbook, dashboard, normalized data and verification evidence.

## 2:40-3:30 | Explain one person's recorded needs

**Show:** find DEMO-0005 and expand "View support needs".
Leave the nested technical section closed unless IT requests it.

**Say:**

> This example has a critical housing barrier and still needs health support.
> Transportation has not yet been assessed, and the legal barrier is partly
> addressed. Those are different situations; we show them separately rather
> than hiding them behind one unexplained code.
>
> The system also creates a compact machine-readable version for future
> integration. We call that the TOON demonstration format. It is checked against
> the original calculated record so no information is lost. Management does not
> need to read that technical format to understand this report.

## 3:30-4:35 | Staff and managerial views

**Show:** first report. Select "North demonstration office", then
"Extended gap in contact"; clear filters. Scroll to the support-needs overview.

**Say:**

> Staff can filter by office, follow-up status and participant number.
> The three cards say recent contact, follow-up due, and extended gap in contact.
> Each explains the number of days it represents. They count the people in the
> filtered list. The support-needs overview always counts everyone in the report.
>
> For each area, needs are described as critical, needing support, partly
> addressed, resolved, or not yet assessed. "Partly addressed" does not mean
> resolved. "Not yet assessed" does not mean no problem exists.
> These descriptions were supplied by the fictional workbook, not inferred by AI.
> "Most pressing recorded need" is a summary, not an eligibility or referral score.
> Qualified staff remain responsible for interpretation and referrals.

**Show:** Excel Dashboard charts, then Watchlist filter dropdown.

> The same processed data also produces actual Excel charts and a filterable
> table. We can start with Excel in the approved workflow without requiring
> custom web hosting.

## 4:35-5:45 | Simulate the next workbook arrival

**Show:** run the refreshed `run` command, then switch to refreshed HTML.

**Say:**

> This second file simulates a new SharePoint workbook snapshot. DEMO-0005 has
> a new contact date and a supplied housing-state update. DEMO-0019 is new.
> The pipeline is rerun; this is not a timed animation or a fake sync button.
>
> The number of people changes from 18 to 19. Recent contact goes from 6 to 8,
> follow-up due stays at 6, and extended gaps in contact go from 6 to 5.
> The housing barrier for our example is now partly addressed, not resolved.
> Existing staff-review information is carried through
> from the source. A recent contact does not imply every barrier is resolved
> and does not authorize a referral.

**Show:** `rehearsal.json` added/updated IDs and preserved-review result.

## 5:45-6:35 | Reproducibility and failure behavior

**Show:** run `verify` against the refreshed batch using its actual batch ID.
Show the verification result, not a long opaque path.

**Say:**

> This command checks file integrity, counts, source reconciliation and the TOON
> round trip independently. Repeated runs with the same code, inputs, execution
> date and pinned runtime produce byte-identical artifacts, including Excel.
>
> A failed refresh returns an error and does not replace the last successful
> batch. Operators must check the status file; an already-open static dashboard
> is not a live health monitor. Automated scheduling and stale-status delivery
> are production work, not something we claim is implemented here.

## 6:35-7:35 | IT and legal review

**Show:** dashboard guardrails or runbook production-boundary section.

**Say:**

> The public repository and this recording use synthetic material only. Public
> visibility is not an open-source license, security approval or authority to
> upload real records. A synthetic marker does not sanitize an arbitrary workbook.
>
> The next review should establish who owns the cloud workbook, its approved
> schema, who may read or update it, how a processing identity receives a versioned
> snapshot, where Python executes, and how retention, access and failures are
> handled. Direct Microsoft 365 ingestion is not connected today.
>
> GeoSol remains the system of record. There is no write-back, partner messaging,
> autonomous referral, medical judgment or AI classification in this demo.

## 7:35-8:00 | Close with the decision requested

**Show:** refreshed Excel Dashboard or HTML overview.

**Say:**

> The proposed first step is a limited, approved SharePoint Excel pilot with a
> reproducible processing pipeline and Excel reporting. We are asking for review
> of the data contract, ownership, permissions and operating boundary, not broad
> tenant access or approval of autonomous decisions. The prototype lets us test
> the workflow safely before connecting any live source.

## If something fails during recording

Stop and inspect the sanitized error and `status.json`. Do not describe the old
dashboard as newly refreshed. Correct the synthetic input or permissions, rerun
the documented commands, and rerecord the segment. Never substitute a live
workbook or use an unverified screenshot to imply successful execution.
