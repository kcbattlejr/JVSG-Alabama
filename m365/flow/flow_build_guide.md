# Power Automate flow: barrier findings (draft)

Build this in the JVSG SharePoint site's Power Automate environment. It is a
build guide, not an importable package: flows are tied to your tenant's
connections, so create it from the template **"Run script on Excel file added
to a SharePoint library"** and edit it as below. All names are placeholders.

Everything here handles live case notes inside the tenant. Do not copy run
history, screenshots or outputs into the repository, chat or e-mail.

## Before you build

1. Upload `m365/office-scripts/BarrierFindings.ts` as an Office Script
   (Excel on the web > Automate > New script > paste > Save as
   `BarrierFindings`). The script has no model dependency.
2. Make a **working copy** of the FY2026 case-notes report as `.xlsx` in a
   restricted `Intake` folder (the report layout: 3 title rows, header on
   row 4, `Case Notes` column). Never point the flow at the original CSV or
   the dashboard workbook.
3. Run the script once by hand from Excel with `mode = extract`,
   `startRow = 1`, `maxRows = 20` and confirm the "Barrier Findings (Draft)"
   sheet appears with `Unverified` rows.
4. Create the flow from a service or shared account, not a personal one.

## Flow: manual, batched, rules-based (use this for the demo)

| # | Action | Settings |
|---|---|---|
| 1 | Trigger **Manually trigger a flow** | Inputs: `Workbook` (file) is optional; hard-code the working copy in step 3 so a run cannot target another file. |
| 2 | **Initialize variable** `nextRow` | Integer, `1` |
| 3 | **Initialize variable** `done` | Boolean, `false` |
| 4 | **Do until** `done` is equal to `true` | Count `200`, timeout `PT2H` |
| 4a | Inside: **Run script** (Excel Online (Business)) | Location: the JVSG site; Document library; File: the working copy; Script: `BarrierFindings`; `mode` = `extract`; `startRow` = `@{variables('nextRow')}`; `maxRows` = `50`; `sourceSheet` = *(blank = first sheet)*; `findingsJson` = *(blank)* |
| 4b | Inside: **Set variable** `nextRow` | `@{outputs('Run_script')?['body/result']?['nextRow']}` |
| 4c | Inside: **Set variable** `done` | `@{outputs('Run_script')?['body/result']?['done']}` |
| 4d | Inside: **Condition** | If `status` is not equal to `ok`: **Terminate** (Failed) with the `message` field only. |
| 5 | **Send an e-mail / Teams message** to the owner team (optional) | Say that a draft is ready for review and link the workbook. Never include note text or counts by person. |

If the connector returns the script result under a different property name,
open a test run and use the dynamic-content picker for `nextRow`, `done`,
`status` and `message`; the script returns exactly those fields.

### Security settings for every action that touches note text

- Action > Settings > **Secure inputs** and **Secure outputs**: on.
- Share the flow only with the processor group; restrict who can read run
  history.
- Confirm the Excel Online (Business) and SharePoint connectors sit in the
  same DLP group (business), and that no step calls a connector outside the
  tenant.

## Flow with a model (only after IT/privacy approval)

Use the same trigger and loop, with the model step between two script calls.
The model never sees raw notes: the first call returns scrubbed text only.

| # | Action | Settings |
|---|---|---|
| a | **Run script** | `mode` = `scrub`, same `startRow` / `maxRows` |
| b | **Parse JSON** | Content: `result/notesJson`; schema: array of `{note_row: integer, text: string}` |
| c | **Apply to each** note | Call the approved tenant model (AI Builder prompt, Copilot Studio, or Azure OpenAI in the tenant) with the prompt below |
| d | **Run script** | `mode` = `append`, **identical** `startRow` / `maxRows`, `findingsJson` = array built from step c |
| e | **Set variable** `nextRow`, `done` | From step a's result, not step d |

Model prompt (fixed; vary only the note text):

> You label barriers to employment in a scrubbed veteran case note. Reply with
> a JSON array only. Each item: `{"note_row": <number>, "domain": one of
> TRN|HSG|MED|LEG, "state": one of CRT|ACT|MIT|RES|UNK, "evidence_quote": an
> exact sentence copied from the note, "source": "model"}`. Use at most one
> item per domain. If the note does not clearly state a barrier, or the
> sentence is negated or about another person, return no item for it. Never
> add names, numbers or text that is not in the note.

The `append` mode re-scrubs the batch and **rejects** any item whose domain
or state is outside the vocabulary, whose quote is not an exact substring of
the scrubbed note, or whose quote contains an identifier. Rejected counts come
back in `rejected`; investigate if it is not close to zero.

## Review step (required, human)

On the "Barrier Findings (Draft)" sheet the reviewer sets `reviewer_action`
to Confirm, Correct or Reject, fills `corrected_domain` / `corrected_state`
for Correct, and adds `reviewer_role` and `reviewed_on`. The verification
status of a row stays `Unverified` until the reviewer's action is recorded;
the dashboard may count only Confirm/Correct rows (use the corrected values
for Correct). Reruns never overwrite or duplicate an existing finding
(`finding_id` = `note_row|domain`).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `case notes header row not found` | Not the native report layout; header must contain `Userid` and `Case Notes`. |
| Script times out or payload too large | Lower `maxRows` (try 25); keep sheets free of unused formatted rows. |
| Flow loops forever | `done` not mapped; check the Set variable steps and the Do until count/timeout. |
| `rejected` high in model mode | Model paraphrased quotes; tighten the prompt or lower temperature. |
