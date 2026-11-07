# Synthetic FY2026 MIS practice data

**Every value in this folder is invented.** No record, name, ID, address or note
text comes from MIS data. Regenerate it with:

```powershell
python -m jvsg_triage.etl synthesize --output data\synthetic --seed 42
```

| File | Purpose |
|---|---|
| `fy2026_203_205_anti_join.synthetic.csv` | Native-layout anti-join: 46 columns, header on row 1, 64 SIDs / 66 rows (2 repeated) |
| `fy2026_case_notes.synthetic.xlsx` | Native-layout case notes: 3 title rows, wrapped header on row 4, blank column B, `Total Rows` footer; 794 notes for 204 SIDs (399 belong to the cohort) |
| `fy2026_case_notes.pii_labels.jsonl` | Ground truth, one line per note row: `row`, `state_id`, and character spans (`label`, `start`, `end`, `value`) of every injected PII value |
| `manifest.json` | Seed, generator/contract versions, the profile used, counts and file hashes |

The volumes, notes-per-SID bins, contact-type mix and date-fill rates are rounded
aggregates from a local profile of the real downloads. Note genres include staff
e-mails with signature blocks, a mass hiring-event invitation, phone contacts,
203 objective assessments and referrals. They cover the employment, VA/medical,
training, contact, legal, transportation and housing themes.

Fictional conventions:

- Phones use `555-01xx`. Emails use `example.org` and `example.gov`.
- SIDs and account numbers fall in the 99/98/97 and 96/95 bands.
- Fields the MIS masks remain `****`.

Label types: `NAME`, `STAFF`, `HONORIFIC_NAME`, `THIRD_PARTY`, `EMAIL`, `URL`,
`PHONE`, `DATE`, `ADDRESS`, `ZIP`, `ID`. `THIRD_PARTY` names have no honorific and
are the scrubber's documented gap. CI requires 100% recall on all other labels:

```powershell
python -m jvsg_triage.etl evaluate `
  --anti-join data\synthetic\fy2026_203_205_anti_join.synthetic.csv `
  --case-notes data\synthetic\fy2026_case_notes.synthetic.xlsx `
  --labels data\synthetic\fy2026_case_notes.pii_labels.jsonl
```

If the generator changes, regenerate this folder. A test fails when the committed
files fall out of sync.
