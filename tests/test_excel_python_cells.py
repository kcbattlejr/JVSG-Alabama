"""Paste-ready Python in Excel cells, run in one shared namespace on synthetic notes."""

import json
from pathlib import Path
from typing import Any

import pytest

pd = pytest.importorskip("pandas")

REPO = Path(__file__).resolve().parents[1]
CELLS = REPO / "src" / "jvsg_triage" / "m365" / "excel_python"
NOTES = REPO / "data" / "synthetic" / "fy2026_case_notes.synthetic.xlsx"
LABELS = REPO / "data" / "synthetic" / "fy2026_case_notes.pii_labels.jsonl"
LEAK_LABELS = {"NAME", "STAFF", "HONORIFIC_NAME", "EMAIL", "PHONE", "ID", "ADDRESS", "URL"}


@pytest.fixture(scope="module")
def ns() -> dict[str, Any]:
    scope: dict[str, Any] = {}
    for name in ("cell1_scrub", "cell2_rules", "cell3_toon"):
        exec((CELLS / f"{name}.py").read_text(), scope)  # noqa: S102 - repo-owned cells
    return scope


@pytest.fixture(scope="module")
def frame() -> Any:
    return pd.read_excel(NOTES, header=3)


@pytest.fixture(scope="module")
def result(ns: dict[str, Any], frame: Any) -> Any:
    return ns["run_pipeline"](frame)


def test_findings_are_unverified_closed_vocabulary_and_quoted(
    ns: dict[str, Any], result: Any, frame: Any
) -> None:
    rows, _, _ = result
    scrubbed = dict(ns["scrub_notes"](frame))
    assert len(rows) > 100
    for row in rows:
        assert row["verification_status"] == "Unverified"
        assert row["domain"] in ns["DOMAINS"] and row["state"] in ns["STATES"]
        assert row["evidence_quote"] in scrubbed[row["note_row"]]
        assert (row["reviewer_action"], row["reviewer_role"], row["reviewed_on"]) == (None,) * 3


def test_scrubbed_notes_and_findings_leak_no_labelled_identifiers(
    ns: dict[str, Any], result: Any, frame: Any
) -> None:
    labels = {}
    for line in LABELS.read_text().splitlines():
        record = json.loads(line)
        labels[record["row"]] = [
            s["value"]
            for s in record["spans"]
            if s["label"] in LEAK_LABELS and len(s["value"]) >= 4
        ]
    # Labels use 1-based sheet rows; table position 1 is sheet row 5 (4 title/header rows).
    for position, text in ns["scrub_notes"](frame):
        for value in labels.get(position + 4, []):
            assert value not in text
    rows, _, chunks = result
    toon = "".join(chunks)
    for row in rows:
        for value in labels.get(row["note_row"] + 4, []):
            assert value not in toon


def test_output_is_deterministic_and_toon_round_trips(ns: dict[str, Any], result: Any) -> None:
    rows, _, chunks = result
    assert ns["run_pipeline"].__name__ == "run_pipeline"
    assert all(len(chunk) <= ns["CHUNK_LIMIT"] + 2000 for chunk in chunks)
    assert [r for chunk in chunks for r in ns["toon_decode"](chunk)] == rows
    assert chunks == ns["toon_chunks"](rows)


def test_toon_quoting_edge_cases_and_empty_table(ns: dict[str, Any]) -> None:
    quote = 'He said "no", then: [x]\nnew line\\ ok'
    row = {
        "finding_id": "1|TRN", "note_row": 1, "domain": "TRN", "state": "ACT",
        "evidence_quote": quote, "source": "rules-v1", "verification_status": "Unverified",
        "reviewer_action": None, "reviewer_role": "null", "reviewed_on": "",
    }
    text = ns["toon_encode"]([row])
    assert ns["toon_decode"](text) == [row]
    assert ns["toon_encode"]([]) == "[0]:\n" and ns["toon_decode"]("[0]:\n") == []
    for bad in (text.replace("[1]", "[2]"), text.rstrip("\n"), text.replace("  1|", "1|", 1),
                text + "  x\n"):
        with pytest.raises(ValueError):
            ns["toon_decode"](bad)


def test_contract_rejects_out_of_contract_findings(ns: dict[str, Any]) -> None:
    scrubbed = "Veteran lacks transportation. Call [PHONE] today."
    good = {"domain": "TRN", "state": "ACT", "evidence_quote": "Veteran lacks transportation."}
    assert ns["violation"](good, scrubbed) == ""
    for bad in (
        {**good, "domain": "EMP"}, {**good, "state": "SEVERE"}, {**good, "evidence_quote": ""},
        {**good, "evidence_quote": "Never in the note."}, {**good, "evidence_quote": None},
        {**good, "evidence_quote": "x" * 401},
    ):
        assert ns["violation"](bad, scrubbed)
    leaky = {**good, "evidence_quote": "Call 251-555-0123"}
    assert "unscrubbed" in ns["violation"](leaky, "Call 251-555-0123")


def test_negated_and_resolved_sentences(ns: dict[str, Any]) -> None:
    assert ns["extract"](1, "Veteran denies homeless status.") == []
    (finding,) = ns["extract"](1, "Veteran is no longer homeless.")
    assert (finding["domain"], finding["state"]) == ("HSG", "RES")


def test_missing_notes_column_fails_closed(ns: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        ns["find_barriers"](pd.DataFrame({"Individual": ["x"]}))
