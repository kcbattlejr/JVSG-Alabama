# Management / IT / legal recording script

<<<<<<< HEAD
**Target:** Friday, November 20, 2026. **Length:** approximately 8 minutes.
**Format:** recorded screen demonstration for a Teams meeting.
Use the [runbook](./management_demo_runbook.md) for commands and definitions.
=======
**Target:** Thursday, November 19, 2026. **Length:** approximately 8 minutes.
**Format:** recorded screen demonstration for a Teams meeting.
Use the [runbook](./management_demo_runbook.md) for commands and definitions.
Use the [stakeholder briefing](./management_presentation_briefing.md) for
the decision request and nomination schedule.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

## Before recording

- Activate the environment and run `python -m jvsg_triage.demo rehearse
  --output temp/management-demo`.
- Confirm the verification message, the paired-report counts and the 18/19
  reviewed-profile results.
<<<<<<< HEAD
=======
- If showing the optional AI-assisted briefing, review and load it using the
  runbook. Otherwise use the standard snapshot comparison.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
- Open the landing page, the raw baseline anti-join CSV, its paired case-notes
  workbook, the polished Excel Dashboard, and the refreshed TOON file.
- Keep the restricted scrubbed-note outputs closed. Do not display their contents.
- Enlarge the browser to 125% or a readable recording resolution. Collapse
  unrelated windows, notifications, account menus and file explorers.
<<<<<<< HEAD
- Keep only generated synthetic files on screen. Do not open the Gemini
  references: they contain statements and figures not used in this demo.
=======
- Keep only generated synthetic files on screen. Do not open reference
  workbooks or older demo folders.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
- Do not display `.env`, private data, native live reports, tenant addresses,
  personal messages or infrastructure/account assignments.
- Rehearse once without recording. This is not a live tenant connectivity demo.

## 0:00-0:45 | Purpose and honest boundaries

**Show:** landing page and the four-step workflow.

**Say:**

> This is a synthetic rehearsal of the MVP workflow we want to evaluate:
> upload the native anti-join and case-notes report pair, validate and privacy-
> process it, then populate a reviewed dashboard and package a TOON output.
> Delivery is simulated with local files. There is no live SharePoint connection,
> production deployment, or use of real veteran data.

## 0:45-1:45 | Start with the raw anti-join upload

**Show:** `temp/management-demo/simulated_sharepoint/` and open
`baseline_203_205_anti_join.synthetic.csv` as a table. Briefly show the paired
`baseline_case_notes.synthetic.xlsx` file without exposing individual note text.

**Say:**

> These are the two synthetic files at the simulated SharePoint intake boundary.
> The anti-join supplies the cohort; the case-notes workbook supplies notes to
> match against that cohort. These files use the native report layouts, but every
> value is invented. In production, the upload location and access controls would
> need agency approval; this local folder is not SharePoint.

## 1:45-2:50 | Validate, match and privacy-process

**Show:** run the `rehearse` command from the runbook. Then show only the
aggregate `native_intake` section in `rehearsal.json`.

**Say:**

> The actual pipeline checks the report headers and case-notes footer, matches
> notes to the supplied cohort, and HMAC-tokenizes the join key. It scrubs matched
> notes and writes them to a restricted local folder. We show counts and hashes
> here—not note text, names, or raw identifiers.
>
> The synthetic baseline has 18 cohort members; the refresh has 19. The
> anti-join defines membership; this process does not recompute the 203/205
> anti-join from separate reports. The demo HMAC key is public and synthetic-only.

## 2:50-3:40 | Make the human-review boundary explicit

**Show:** `reviewed_profiles/baseline.xlsx`, `Demo Intake` sheet.

**Say:**

> The native report pair does not contain the office, aging, or four support-
> domain fields shown in our dashboard. These separate profile inputs are
> fictional human-review examples. They are not extracted from the case notes
> and are not AI classifications. A real pilot needs an approved profile source,
> definitions, and qualified review workflow before those fields can be populated.

## 3:40-5:10 | Automatically populate the Excel visualization

**Show:** refreshed `dashboard.xlsx`, first on Dashboard, then Watchlist.
Point out the headline cards, the contact-status chart, support-needs chart,
and filterable rows.

**Say:**

> After the synthetic reviewed profiles are supplied, the run deterministically
> calculates the demo aging bands and generates this Excel workbook. The cards
> and charts summarize the same profile rows shown in the filterable Watchlist.
> The colors and 15/30-day boundaries are presentation assumptions—not approved
> agency policy.
>
> The support descriptions are independent. Recent contact does not mean a
<<<<<<< HEAD
> barrier is resolved. “Most pressing recorded need” is an explanatory summary,
> not an eligibility or referral score. Qualified staff remain responsible for
> interpretation and next steps.
=======
> barrier is resolved. The right chart counts people marked critical or needing
> support in each area. A person can appear in more than one column; the
> Watchlist shows the full status for each person. “Most pressing recorded need”
> is an explanatory summary, not an eligibility or referral score. Qualified
> staff remain responsible for interpretation and next steps.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

## 5:10-6:00 | Package and verify TOON

**Show:** refreshed `profiles.toon`, then the actual batch verification result.
Leave hidden technical workbook sheets closed unless IT asks to see them.

**Say:**

<<<<<<< HEAD
> The same reviewed profiles produce a compact, lossless custom TOON demo file.
> The verifier checks its round trip against the normalized profile records and
> verifies the report artifacts. This `@TOON demo-1` format is illustrative; it
> is not an approved federal or VOMA contract, and no data is transmitted.

## 6:00-6:50 | Simulate a refreshed report pair

**Show:** refreshed raw synthetic pair and refreshed Dashboard. Then show
`rehearsal.json` for the added and updated demo IDs.
=======
> The same reviewed profiles produce a standard TOON file, with column names
> listed once and one row per profile. The verifier checks that decoding it
> gives back the same records. The syntax is standard, but the demo's fields
> are not an approved federal or VOMA contract. No data is transmitted.

## 6:00-6:50 | Simulate a refreshed report pair and explain the change

**Show:** refreshed Dashboard and the landing page comparison.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

**Say:**

> The refreshed pair simulates a new delivery. The profile review fixture also
> includes one added and one updated fictional record, with existing review
> values preserved. The report is regenerated from the reviewed inputs; it is
> not a live sync or a write-back to SharePoint.

<<<<<<< HEAD
=======
**If the reviewed briefing is on screen, add:**

> AI drafted this wording from invented totals, and a person checked it against
> the figures. The AI saw no notes or individual records, made no decisions,
> and is not running during the presentation.

>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
## 6:50-7:35 | IT and legal review

**Show:** dashboard guardrails or the runbook production-boundary section.

**Say:**

> This demo uses generated data only. A synthetic marker does not sanitize an
> arbitrary workbook, and public visibility is not security approval or authority
> to upload live records. Before a pilot, owners must approve the actual source
> and profile contracts, permissions, processing environment, retention, support,
> and operational definitions.
>
> GeoSol remains the system of record. Direct SharePoint ingestion, automated
> scheduling, AI classification, notifications, referrals, and VOMA integration
> are not implemented here.

## 7:35-8:00 | Close with the decision requested

**Show:** refreshed Excel Dashboard.

**Say:**

<<<<<<< HEAD
> The MVP to review is a controlled paired-report intake, validated privacy-
> processing, a qualified human-review step, and generated Excel visualization
> plus a separately governed TOON package. We are asking for agreement on the
> data contracts, ownership, permissions, review process, and operating boundary—
> not broad tenant access or approval of autonomous decisions.
=======
> Today we are asking for a sponsor and named leads to scope a pilot and prepare
> a NASWA IT innovation nomination for review. We will confirm eligibility
> first, target an administrator decision on December 2, and submit on December 3
> only if the evidence and approvals are ready. We are not asking to use live
> data or claiming service results from this demo.
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88

## If something fails during recording

Stop and inspect the sanitized error and `status.json`. Do not describe the old
dashboard as newly refreshed. Correct the synthetic input, rerun the documented
commands, and rerecord the segment. Never substitute a live workbook or use an
unverified screenshot to imply successful execution.
