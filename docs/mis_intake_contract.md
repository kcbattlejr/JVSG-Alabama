# Native MIS intake contract (v1.1)

> v1.1 adds per-column PII classes, the native XLSX footer rule, a transient
> redaction lexicon, the scrubber, private extraction and synthetic data. The
> governing privacy rules are in [pii_protocol.md](pii_protocol.md).

## Confirmed source structure

The supported report contract uses a 203/205 **anti-join in CSV** and
**case notes in XLSX**. Public fixtures demonstrate headers and layout
coordinates using invented records. Private source-discovery and validation
evidence must remain in approved private storage. This contract does not
validate FY filters or underlying MIS logic.

| Download | Observed header | Width | Structural details |
|---|---|---|---|
| Anti-join CSV | Row 1 | 46 columns | UTF-8/BOM, comma-delimited; native SSRS-style field names |
| Case-notes XLSX | Row 4 | 12 columns | One worksheet; three preceding title rows; column B has no header; footer of blank row, repeated header, `Total Rows: N` |

The full ordered headers and field handling are in
[mis_reports.v1.json](../data/schemas/mis_reports.v1.json), generated from
[contracts.py](../src/jvsg_triage/etl/contracts.py).
Header discovery scans at most 50 logical CSV records or XLSX rows. Header row
positions are discovered, not hardcoded. Case, whitespace and line wrapping
are normalized; missing, reordered, duplicate, added or renamed fields fail.
Unknown labels and title contents are never included in errors.

The blank XLSX column B remains part of the positional contract. Nonempty data
in that column fails rather than shifting subsequent columns. Multiple
worksheets are rejected rather than silently choosing one. Blank rows are
skipped, but partially populated invalid rows fail. The XLSX footer is required:
`Total Rows: N` must equal the rows read, and nothing may follow it. A missing or
mismatched footer signals a truncated download and fails the run. The CSV has no
footer. Malformed records and corrupt files fail.

## Structured model and explicit limits

The protected in-memory models are in
[models.py](../src/jvsg_triage/etl/models.py):

- **AntiJoinRecord:** source coordinates and HMAC participant token only.
- **CaseNoteRecord:** source coordinates, HMAC participant token, the
  unstructured note, and the row's own participant/staff names (`SecretStr`,
  used only to scrub that note).
- **RedactionLexicon:** names and identifiers read transiently from `lexicon`
  columns; excluded from serialization and never written.
- **IntakeBatch:** layouts, private cohort and matching notes, lexicon, and
  aggregate reconciliation counts, including the footer's declared total.
- **RedactedNote (T2)** and **ExtractionManifest (T3):** scrubbed output and
  counts-only run record.

`StateID` / `State ID` is the only join key. Text IDs retain leading zeros.
Nonnegative Excel integer IDs are converted to decimal text; no zero-padding,
name matching, SSN matching or case-folding is applied. Boolean, float and
missing IDs fail. The owner must confirm whether Excel numeric IDs have already
lost meaningful leading zeros. HMAC-SHA256 requires an explicit locally supplied
key of at least 32 UTF-8 bytes; no default key is generated or persisted.

Per the owner's streamlined scope, the only projected CSV field is `StateID`;
the only projected XLSX fields are `State ID` and `Case Notes`. Name, staff and
account-number columns are read only into the transient redaction lexicon. Dates,
subject, contact type, demographics and all other fields are discarded.
Full source headers are retained solely for download layout validation.

All source-derived fields are private and excluded from ordinary model
serialization and representations. Raw SID, names, SSN, user/staff identifiers,
contact details and unmapped fields are not retained in the normalized models.
Note text uses `SecretStr` and **remains unsanitized private evidence in T1**.
Pass the batch through the scrubber (`jvsg_triage.privacy.redact_batch`) or the
`extract` command before any use; scrubbed output is still pseudonymous.
Masking and HMAC are not anonymization, access control or encryption at rest.
Do not send these objects to inference services.
Only layouts and counts appear in the batch's ordinary JSON output.

All fields other than SID, note text and lexicon columns are represented in the
contract but **discarded** during projection. No field is assumed to be an assessment date,
service code, role, fiscal bound or active-IEP indicator without a dictionary.

Dates are not parsed or validated because they are outside this intake scope.
Notes must be nonblank text and are preserved exactly, including whitespace and
line breaks. No timezone, contact verification, latest-touch or FY policy is inferred.

## Pipeline behavior

[ingest_reports](../src/jvsg_triage/etl/ingest.py) provides the offline API:

```python
from pathlib import Path
from pydantic import SecretStr
from jvsg_triage.etl.ingest import ingest_reports

# Synthetic practice files only; inject a real key from approved local settings.
batch = ingest_reports(
    Path("data") / "synthetic" / "fy2026_203_205_anti_join.synthetic.csv",
    Path("data") / "synthetic" / "fy2026_case_notes.synthetic.xlsx",
    secret=SecretStr("synthetic-only-development-key-0001"),
)
print(batch.summary.model_dump_json())
```

1. Validate both layouts and project only mapped columns.
2. Replace source StateID with a keyed participant token immediately.
3. Validate every note row, including notes outside the supplied cohort.
4. Match notes to the **already anti-joined MIS population** by token.
5. Retain duplicate cohort rows and multiple note rows; report repeated
   participant rows, matching/unmatched notes and coverage counts.

Matching does not expand the supplied cohort. Unique participant counts do not
alter row-level evidence. Repeated notes are not deduplicated because the
download exposes no confirmed stable note ID. Inputs have no side effects;
repeated runs with identical files/key return identical batches. There is no
database upsert or cross-refresh note identity yet.

This intake does **not** recompute the 203/205 anti-join, verify Non-CM
eligibility, apply fiscal/office/role rules, calculate aging, classify notes,
persist to a database, send messages or call a network service. It does not
implement quarantine or atomic refresh. Those planned stages remain subject to the
documented operational and security decisions.

## Operator commands

From the repository root in PowerShell after installing `.[dev]`:

```powershell
.\.venv\Scripts\python.exe -m jvsg_triage.etl schema
.\.venv\Scripts\python.exe -m jvsg_triage.etl inspect `
  --anti-join 'temp\anti_join.csv' --case-notes 'temp\case_notes.xlsx'
.\.venv\Scripts\python.exe -m jvsg_triage.etl extract `
  --anti-join 'temp\anti_join.csv' --case-notes 'temp\case_notes.xlsx' `
  --output temp\private
.\.venv\Scripts\python.exe -m jvsg_triage.etl synthesize --output data\synthetic --seed 42
.\.venv\Scripts\python.exe -m jvsg_triage.etl evaluate `
  --anti-join data\synthetic\fy2026_203_205_anti_join.synthetic.csv `
  --case-notes data\synthetic\fy2026_case_notes.synthetic.xlsx `
  --labels data\synthetic\fy2026_case_notes.pii_labels.jsonl
```

`inspect` stops at the header and emits only layout coordinates. `extract`
requires `SID_HMAC_SECRET`, writes T2 notes only to `temp/`, `data/private/` or
outside the repository, and prints only the T3 manifest. `evaluate` exits nonzero
if required recall falls below 100%. Errors are sanitized and exit nonzero.

`temp/`, private/raw/processed data and XLSX files are ignored by Git. This is
only an accidental-commit safeguard: Git ignore rules are not privacy controls,
and cannot remove previously tracked files or prevent OneDrive synchronization.
Keep native downloads in an approved secure intake location outside development
and cloud-sync locations under the agency's access/retention policy.
Do not copy, rename or convert the source files for this implementation.

## Verification and remaining inputs

[test_mis_intake.py](../tests/test_mis_intake.py) constructs synthetic CSV/XLSX
fixtures for layouts, header drift, title rows, footer validation, malformed rows,
leading zeros, multiple notes, ignored metadata, exact note preservation, HMAC
determinism and output/error privacy.
[test_privacy_scrubber.py](../tests/test_privacy_scrubber.py) covers each
detector, and [test_synthetic_pipeline.py](../tests/test_synthetic_pipeline.py)
covers generator determinism, label alignment, extraction destinations and
end-to-end recall. A further test checks that the committed synthetic dataset
matches the generator output.
The checked-in contract is compared to its code model to prevent schema drift.

Remaining inputs for later stages: 203/205 filters and FY rules if independent
cohort verification is wanted, stable note identity/version semantics if
cross-refresh persistence is wanted, and authorized intake, retention and
production data handling. Other MIS fields are not needed for SID-to-note
matching and are not prerequisites for this streamlined foundation. Header discovery
is complete; the broader S1/S2 and privacy/inference release gates remain open.
