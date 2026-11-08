# PII protocol v1.0 — native MIS case-note extraction

This protocol governs how the FY2026 203/205 anti-join CSV and the case-notes XLSX
move from native MIS downloads into data this project can use. It is implemented by
[contracts.py](../src/jvsg_triage/etl/contracts.py) (column classification),
[ingest.py](../src/jvsg_triage/etl/ingest.py) (protected intake),
[scrubber.py](../src/jvsg_triage/privacy/scrubber.py) (redaction) and
[pipeline.py](../src/jvsg_triage/etl/pipeline.py) (private extraction).

Scrubbed output is **pseudonymous, not anonymous**. Read the known limits in
section 6 before using T2 data anywhere other than a private local folder.

## 1. Data tiers

| Tier | Contents | Where it may live | May leave the workstation? |
|---|---|---|---|
| T0 | Native downloads, unmodified | Approved intake location; `temp/` (Git-ignored) for development | No |
| T1 | In-memory records: HMAC participant token, raw note (`SecretStr`), row-local names, transient lexicon | Process memory only; never serialized | No |
| T2 | `RedactedNote`: HMAC token, source row, scrubbed text, redaction counts | `temp/` or `data/private/` (Git-ignored) or outside the repo | No, unless separately approved |
| T3 | `ExtractionManifest`: contract/protocol versions, reconciliation and redaction counts | Console and local logs | Yes (counts only) |
| T4 | Seeded synthetic data with PII labels | `data/synthetic/` (versioned) | Yes |

Git-ignore rules prevent accidental commits; they are not access control.
OneDrive still syncs ignored folders, so keep T0 and T2 in an agency-approved location.

## 2. Column classification

Every source column in both downloads has a `PiiClass` and a handling rule in the
contract. The checked-in [schema](../data/schemas/mis_reports.v1.json) is generated
from it.

| Handling | Meaning | Columns |
|---|---|---|
| `projected` | Kept in the T1 model | `StateID` / `State ID` (HMAC-tokenized on read), `Case Notes` |
| `lexicon` | Read transiently to build the redaction dictionary; never stored | Names (`FirstName`, `LastName`, `Individual`), staff (`StaffCreated`, `EditStaff`, `CaseManager`, `Created By`, `Last Edited By`), identifiers (`Username`, `AppID`, `Userid`, all SIDs) |
| `discarded` | Width-checked, never read | All other columns, including dates, demographics, `Hispanic`, `col_offender`, masked contact fields and `Case Subject` |
| `blank` | Must stay empty | XLSX column B |

The SID is the only join key. It is replaced with HMAC-SHA256 under a key of at
least 32 bytes supplied through the `SID_HMAC_SECRET` environment variable. No key
is generated or stored. The same key gives stable tokens across runs. Rotating the
key unlinks earlier T2 outputs.

## 3. Structural validation

- **Header discovery:** title rows are skipped, scanning at most 50 rows.
- **Exact layout:** columns must match the contract in order. Case, spacing and
  line wraps are normalized.
- **XLSX footer:** after the data comes a blank row, a repeated header and
  `Total Rows: N`. N must equal the number of rows read. A missing footer, a
  mismatched total, or any content after the footer fails the run, because each
  of these indicates a truncated or altered download.
- **Errors:** messages carry only the report kind, row and column numbers, and
  field labels. They never contain values or file paths.

## 4. Redaction rules (protocol 1.0)

The detectors run on the original text. All detected spans are merged into one
union and replaced once with typed placeholders. Where spans overlap, the
higher-priority label wins (for example, a name inside an email becomes `[EMAIL]`).

| Placeholder | Detector |
|---|---|
| `[EMAIL]` | Any `local@domain.tld` |
| `[URL]` | `http(s)://…` or `www.…` |
| `[SSN]` | `NNN-NN-NNNN` |
| `[PHONE]` | 10-digit NANP in common formats, 7-digit `NNN-NNNN`, optional extension |
| `[DATE]` | Numeric dates (`m/d/yy`, `m/d/yyyy`, ISO) and month-name dates with or without year |
| `[ADDRESS]` | House number + 1–4 capitalized words + street type, optional unit; PO boxes |
| `[ZIP]` | 5- or 9-digit ZIP following a state abbreviation or `Alabama` |
| `[ID]` | Exact lexicon identifiers (SID, Userid, AppID, Username) and any other run of 5+ digits |
| `[NAME]` | (a) the note row's own participant and staff names, in any case, including 2-letter parts; (b) any participant name token (3+ letters) from either report, Title or UPPER case only, minus a common-word stoplist; (c) a capitalized word or two following an honorific (`Mr.`, `Ms.`, `Dr.`, `Sgt`, …) |
| `[STAFF]` | Staff name tokens from either report, Title or UPPER case only, minus the stoplist |

After scrubbing, a residual scan reruns every pattern plus the lexicon on the
output, ignoring placeholders. The manifest records per-type redaction counts,
residual counts, and the number of notes with residual findings. A residual hit is
a defect. Zero hits is not proof of safety.

## 5. Running an extraction

```powershell
$env:SID_HMAC_SECRET = '<32+ byte key from the approved secret store>'
.\.venv\Scripts\python.exe -m jvsg_triage.etl extract `
  --anti-join temp\<anti-join>.csv --case-notes temp\<case-notes>.xlsx `
  --output temp\private
```

Output goes to `redacted_notes.jsonl` (T2) and `manifest.json` (T3); only the
manifest is printed. Any in-repo destination other than `temp/` or
`data/private/` is refused.

**FY2026 baseline (local run, counts only):** 66 anti-join rows / 64 SIDs; 3,339
note rows, matching the declared footer total; 431 cohort notes covering 64/64
SIDs. Redactions: NAME 1,330, DATE 256, EMAIL 220, PHONE 197, ZIP 121, ADDRESS
98, ID 93, URL 87, STAFF 27. Residual findings: 0.

## 6. Known limits and residual risk

1. **Third-party names.** Names of family members, employers' contacts or agency
   staff are caught only if they follow an honorific or appear in the report's
   own name columns. Synthetic recall for third-party names without an honorific
   is 0% by design. A heuristic count on the FY2026 notes found many surviving
   capitalized word pairs; most are organization and program names, but some are
   likely people.
2. **Over-redaction is accepted.** A participant name that is also a common word
   is removed wherever it is capitalized. On FY2026 data, 4 such tokens account
   for 68 of 293 global-lexicon hits. Losing those words was judged a smaller cost
   than letting a real name through in other participants' notes.
3. **Quasi-identifiers in free text** (employer names, units of service, rare
   conditions, city names, narrative details) are not removed. Together they can
   re-identify a veteran.
4. **Regex coverage is English- and US-format-specific.** Spelled-out numbers,
   unusual phone formats, and dates such as "the 3rd" are not detected.
5. **Synthetic recall is not real-world recall.** The 100% required recall on
   synthetic data shows the detectors match the formats they were designed for.
   The templates were written with those formats in mind.

Therefore T2 output must not be sent to any external or cloud inference service
without a separate approval and a stronger de-identification step, such as a
local NER model plus human review.

## 7. Synthetic practice data (T4)

`python -m jvsg_triage.etl synthesize --output data/synthetic --seed 42` writes:

- Native-format copies of both downloads.
- A character-offset PII label file.
- A manifest.

Generation draws only on rounded aggregate shares from the local profile
(cohort size, notes-per-SID bins, contact-type mix, date-fill rates, theme mix).
Names, IDs, streets, employers and note templates are invented. Phones use the
fictional `555-01xx` range; emails use `example.org` and `example.gov`.

A local check against the FY2026 files found:

- No overlap in IDs (0 of 472).
- No overlap in full names (0 of 204) or name tokens (0 of 126).
- No overlap in note text: 0 of 427,397 sampled 40-character windows of real
  note text appear in the synthetic notes.

`python -m jvsg_triage.etl evaluate --labels …` scores scrubber recall per label.
CI requires 100% recall for every label except `THIRD_PARTY`.

## 8. Change control

Any change to detectors, the stoplist, or the column handling rules must:

- Bump `PROTOCOL_VERSION` (scrubber) or `CONTRACT_VERSION` (contract).
- Keep the synthetic recall test passing.
- Be followed by a real-data re-run whose new manifest counts are reviewed before
  the T2 output is used.
