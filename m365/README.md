# Microsoft 365 assets (Office Scripts and flow)

Assets for the SharePoint/Excel barrier-findings workflow. They are written
against the synthetic notes in `data/synthetic/` and run on live data only
inside the JVSG SharePoint site and Microsoft 365 tenant. Never commit
exports, run history or screenshots of live data.

| Path | Purpose |
|---|---|
| `office-scripts/BarrierFindings.ts` | Excel Office Script: scrub notes, rules-based barrier extraction, model-output validation, `Unverified` findings sheet |
| `flow/flow_build_guide.md` | Step-by-step Power Automate build (manual, batched) and optional model step |
| `tests/harness.mjs` | Offline Node harness with a fake Office Scripts API, used by `tests/test_office_script.py` |

## Design rules

- Findings are suggestions. Every row is written as `Unverified` with a
  verbatim evidence quote from the **scrubbed** note; a qualified person must
  Confirm, Correct or Reject it before it counts anywhere.
- Closed vocabulary: domain `TRN|HSG|MED|LEG`, state `CRT|ACT|MIT|RES|UNK`.
  Anything else, a quote not found in the scrubbed note, or a quote with
  residual identifiers is rejected, not repaired.
- Idempotent: a finding id is `note_row|domain`; reruns never overwrite or
  duplicate a row a reviewer may have edited.
- The scrub rules mirror `src/jvsg_triage/privacy/scrubber.py` (names from the
  whole report, honorific names, structured identifiers) plus a referral-name
  guard. Scrubbing is pseudonymization, not anonymization, and is unvalidated
  on live notes: reviewers must still read the quote.
- The rules-based extractor (`rules-v1`) is a deliberately simple baseline
  and is not an accuracy claim.

## Test

```bash
python -m pytest tests/test_office_script.py
```

Requires Node 22.13+ (the harness strips TypeScript types); the tests skip if
Node is missing. Paste the `.ts` file into Excel on the web to deploy it.
