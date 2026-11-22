"""Microsoft 365 Office Script behavior on synthetic notes.

The script runs under Node against an in-memory fake of the Office Scripts API.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from openpyxl import load_workbook

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "src" / "jvsg_triage" / "m365" / "tests" / "harness.mjs"
NOTES = REPO / "data" / "synthetic" / "fy2026_case_notes.synthetic.xlsx"
LABELS = REPO / "data" / "synthetic" / "fy2026_case_notes.pii_labels.jsonl"
SHEET = "Barrier Findings (Draft)"
# The script adds a referral-name guard, so THIRD_PARTY names are checked as well.
LEAK_LABELS = {
    "NAME", "STAFF", "HONORIFIC_NAME", "THIRD_PARTY", "EMAIL", "PHONE", "ID", "ADDRESS", "URL",
}

pytestmark = pytest.mark.skipif(shutil.which(
    "node") is None, reason="Node.js not installed")


def _rows() -> list[list[str]]:
    sheet = load_workbook(NOTES, read_only=True).worksheets[0]
    return [["" if c is None else str(c) for c in row] for row in sheet.iter_rows(values_only=True)]


def _run(calls: list[dict[str, Any]], rows: list[list[str]] | None = None) -> dict[str, Any]:
    payload = {"sheets": {"Case Notes": rows or _rows()}, "calls": calls}
    done = subprocess.run(
        ["node", str(HARNESS)], input=json.dumps(payload), capture_output=True, text=True,
        check=True,
    )
    return json.loads(done.stdout)  # type: ignore[no-any-return]


def _extract_all() -> dict[str, Any]:
    return _run([{"mode": "extract", "startRow": 1, "maxRows": 100}] * 1 + [
        {"mode": "extract", "startRow": 105 + 100 * i, "maxRows": 100} for i in range(6)
    ])


def test_extract_writes_only_unverified_findings_with_closed_vocabulary() -> None:
    out = _extract_all()
    header, *findings = out["findings"]
    assert header[9] == "verification_status"
    assert len(findings) > 100
    for row in findings:
        assert row[9] == "Unverified"
        assert row[5] in {"TRN", "HSG", "MED", "LEG"}
        assert row[6] in {"CRT", "ACT", "MIT", "RES", "UNK"}
        assert row[7]
        assert row[10:] == [""] * 5  # no reviewer fields pre-filled


def test_findings_contain_no_injected_identifiers() -> None:
    out = _extract_all()
    values = {
        row: [s["value"] for s in spans if s["label"]
              in LEAK_LABELS and len(s["value"]) >= 4]
        for line in LABELS.read_text().splitlines()
        for row, spans in [(json.loads(line)["row"], json.loads(line)["spans"])]
    }
    for finding in out["findings"][1:]:
        text = " ".join(str(cell) for cell in finding)
        for value in values.get(finding[1], []):
            assert value not in text


def test_rerun_is_idempotent() -> None:
    call = {"mode": "extract", "startRow": 1, "maxRows": 100}
    out = _run([call, call])
    first, second = out["results"]
    assert first["added"] > 0
    assert (second["added"], second["skipped"]) == (0, first["added"])
    assert len(out["findings"]) == first["added"] + 1


def test_batching_reports_progress_and_completion() -> None:
    out = _extract_all()
    first, last = out["results"][0], out["results"][-1]
    assert (first["nextRow"], first["done"]) == (105, False)
    assert last["done"] is True


def test_scrub_mode_returns_scrubbed_text_only() -> None:
    out = _run([{"mode": "scrub", "startRow": 1, "maxRows": 20}])
    notes = json.loads(out["results"][0]["notesJson"])
    assert notes and out["findings"] is None
    records = [json.loads(line) for line in LABELS.read_text().splitlines()]
    labels = {record["row"]: record["spans"] for record in records}
    for note in notes:
        for span in labels.get(note["note_row"], []):
            if span["label"] in LEAK_LABELS and len(span["value"]) >= 4:
                assert span["value"] not in note["text"]


def test_append_rejects_findings_that_break_the_contract() -> None:
    scrubbed = json.loads(
        _run([{"mode": "scrub", "startRow": 1, "maxRows": 5}])[
            "results"][0]["notesJson"]
    )[0]
    quote = scrubbed["text"].split(".")[0] + "."
    good = {"note_row": scrubbed["note_row"], "domain": "TRN", "state": "ACT",
            "evidence_quote": quote, "source": "model"}
    bad = [
        {**good, "domain": "EMP"},
        {**good, "state": "SEVERE"},
        {**good, "evidence_quote": "A sentence the note never contained."},
        {**good, "evidence_quote": ""},
        {**good, "note_row": 99999},
        {**good, "evidence_quote": "Call 251-555-0123"},
    ]
    out = _run([{
        "mode": "append", "startRow": 1, "maxRows": 5,
        "findingsJson": json.dumps([good, *bad]),
    }])
    result = out["results"][0]
    assert (result["added"], result["rejected"]) == (1, len(bad))
    assert out["findings"][1][9] == "Unverified"


def test_missing_header_or_bad_mode_fails_closed() -> None:
    out = _run([{"mode": "extract", "startRow": 1, "maxRows": 5}],
               rows=[["x"], ["y"]])
    assert out["results"][0]["status"] == "error"
    assert out["findings"] is None
    out = _run([{"mode": "delete", "startRow": 1, "maxRows": 5}])
    assert out["results"][0]["status"] == "error"
