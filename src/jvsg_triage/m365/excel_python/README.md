# Python in Excel cells (Excel on the web)

Paste-ready cells for **Formulas > Insert Python** that scrub case notes, run the
`rules-v1` baseline, enforce the closed contract and emit TOON. Approved strategy:
Python is the deterministic guard rail; **no model is called** (`=COPILOT` is not
available, and Python in Excel has no network access by design). The SLM stays
roadmap. Every finding is an `Unverified` suggestion for qualified staff review.

## Cells

Python cells share one namespace and run in row-major order, sheet by sheet. Put
all of them on a sheet placed **before** the data sheets (for example "Python").

| Cell | Paste | Defines |
|---|---|---|
| A1 | `cell1_scrub.py` | `scrub`, `build_lexicon`, `has_residual_pii` |
| A2 | `cell2_rules.py` | `extract`, `violation`, `scrub_notes`, `find_barriers` |
| A3 | `cell3_toon.py` | `toon_encode`, `toon_decode`, `toon_chunks`, `run_pipeline` |
| A4 | `rows, rejected, chunks = run_pipeline(xl("CaseNotes[#All]", headers=True))` | Run (output: Python object) |
| A5 | `pd.DataFrame(rows)` | Review table (output: Excel value) |
| A6 | `pd.Series(chunks)` | TOON text, one valid table per cell (Excel value) |
| A7 | `rejected` | Count rejected by the contract |

Setup: the case-notes report needs its title rows removed so row 1 is the header
(`Userid ... Case Notes`), converted to a table named `CaseNotes`. Header line
breaks are fine. `note_row` is the 1-based table row, not the sheet row.

Output carries no State ID, names or other identifiers: only the scrubbed
evidence sentence, domain, state and review columns. Add Confirm/Correct/Reject
columns beside the review table; nothing counts until a human sets `Confirmed`.

## Limits

- Stdlib only (no `jvsg_triage`, no `pip`). Code must stay in step with
  `privacy/scrubber.py` and `office-scripts/BarrierFindings.ts` by hand.
- Cells hold at most 32,767 characters, so TOON is split into chunks.
- Python in Excel sends referenced data to Microsoft's cloud container
  (approved for note text by the program owner; keep it in the JVSG SharePoint site).
- Scrubbing is pseudonymization and unvalidated on live notes; the baseline is not an
  accuracy claim. Not yet run in Excel itself: verify on the synthetic workbook first.

## Test

```bash
python -m pytest tests/test_excel_python_cells.py
```

Needs `pandas` (`pip install -e ".[data]"`); the tests skip without it.
