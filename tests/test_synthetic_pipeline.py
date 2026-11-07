"""Synthetic dataset, private extraction pipeline and end-to-end recall tests."""

import hashlib
import json
from pathlib import Path

import pytest
from openpyxl import load_workbook
from pydantic import SecretStr

from jvsg_triage.etl.contracts import ReportKind
from jvsg_triage.etl.ingest import IngestionError, inspect_layout
from jvsg_triage.etl.pipeline import MANIFEST_FILE, NOTES_FILE, run_extraction
from jvsg_triage.synthetic import generate_dataset
from jvsg_triage.synthetic import generator as gen
from jvsg_triage.synthetic.evaluate import evaluate_recall
from jvsg_triage.synthetic.notes import REQUIRED_RECALL

REPO = Path(__file__).resolve().parents[1]
COMMITTED = REPO / "data" / "synthetic"
KEY = SecretStr("synthetic-only-development-key-0001")


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("synthetic")
    generate_dataset(output, seed=42)
    return output


def _cells(path: Path) -> list[tuple[object, ...]]:
    workbook = load_workbook(path, read_only=True)
    try:
        return list(workbook.worksheets[0].iter_rows(values_only=True))
    finally:
        workbook.close()


def test_synthetic_files_match_native_layouts(dataset: Path) -> None:
    anti = inspect_layout(dataset / gen.ANTI_JOIN_FILE, ReportKind.ANTI_JOIN)
    notes = inspect_layout(dataset / gen.CASE_NOTES_FILE, ReportKind.CASE_NOTES)
    assert (anti.header_row, anti.column_count) == (1, 46)
    assert (notes.header_row, notes.column_count) == (4, 12)
    rows = _cells(dataset / gen.CASE_NOTES_FILE)
    assert str(rows[-1][0]).startswith("Total Rows:")


def test_generation_is_deterministic(dataset: Path, tmp_path: Path) -> None:
    generate_dataset(tmp_path, seed=42)
    for name in (gen.ANTI_JOIN_FILE, gen.LABELS_FILE, gen.MANIFEST_FILE):
        assert (tmp_path / name).read_bytes() == (dataset / name).read_bytes()
    assert _cells(tmp_path / gen.CASE_NOTES_FILE) == _cells(dataset / gen.CASE_NOTES_FILE)
    generate_dataset(tmp_path / "other", seed=7)
    assert (tmp_path / "other" / gen.ANTI_JOIN_FILE).read_bytes() != (
        dataset / gen.ANTI_JOIN_FILE
    ).read_bytes()


def test_committed_dataset_is_current(dataset: Path) -> None:
    """Regenerate with `python -m jvsg_triage.etl synthesize` if this fails."""
    for name in (gen.ANTI_JOIN_FILE, gen.LABELS_FILE, gen.MANIFEST_FILE):
        committed = hashlib.sha256((COMMITTED / name).read_bytes()).hexdigest()
        assert committed == hashlib.sha256((dataset / name).read_bytes()).hexdigest(), name
    assert _cells(COMMITTED / gen.CASE_NOTES_FILE) == _cells(dataset / gen.CASE_NOTES_FILE)


def test_labels_align_with_note_text(dataset: Path) -> None:
    rows = _cells(dataset / gen.CASE_NOTES_FILE)
    for line in (dataset / gen.LABELS_FILE).read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        cells = rows[record["row"] - 1]
        assert str(cells[9]) == record["state_id"]
        text = str(cells[11])
        for span in record["spans"]:
            assert text[span["start"]:span["end"]] == span["value"]


def test_required_recall_is_complete(dataset: Path) -> None:
    result = evaluate_recall(
        dataset / gen.ANTI_JOIN_FILE, dataset / gen.CASE_NOTES_FILE, dataset / gen.LABELS_FILE,
    )
    assert result["required_recall_met"] is True
    recall = result["recall"]
    assert isinstance(recall, dict)
    for label in REQUIRED_RECALL:
        assert recall[label]["labelled"] > 0, label


def test_extraction_writes_scrubbed_notes_and_aggregate_manifest(
    dataset: Path, tmp_path: Path,
) -> None:
    output = tmp_path / "private"
    manifest = run_extraction(
        dataset / gen.ANTI_JOIN_FILE, dataset / gen.CASE_NOTES_FILE,
        secret=KEY, output_dir=output,
    )
    lines = (output / NOTES_FILE).read_text(encoding="utf-8").splitlines()
    assert len(lines) == manifest.summary.matched_note_rows > 0
    assert manifest.residual_findings == {}
    assert manifest.summary.participants_without_notes == 0

    leaked_values: set[str] = set()
    third_party: set[str] = set()
    for line in (dataset / gen.LABELS_FILE).read_text(encoding="utf-8").splitlines():
        for span in json.loads(line)["spans"]:
            if span["label"] == "THIRD_PARTY":
                third_party |= set(span["value"].split())
            elif span["label"] in REQUIRED_RECALL and len(span["value"]) >= 5:
                leaked_values.add(span["value"])
    # Honorific surnames also occur in unlabeled-scope third-party names (known gap).
    leaked_values -= third_party
    scrubbed = "\n".join(json.loads(line)["text"] for line in lines)
    assert not [value for value in leaked_values if value in scrubbed]

    manifest_text = (output / MANIFEST_FILE).read_text(encoding="utf-8")
    assert "text" not in json.loads(manifest_text)
    assert not [value for value in leaked_values if value in manifest_text]
    assert set(json.loads(lines[0])) == {
        "participant_token", "source_row", "text", "redactions",
    }


@pytest.mark.parametrize("relative", ["data/synthetic", "docs", "."])
def test_extraction_refuses_tracked_destinations(
    dataset: Path, tmp_path: Path, relative: str,
) -> None:
    with pytest.raises(IngestionError, match="output must be under"):
        run_extraction(
            dataset / gen.ANTI_JOIN_FILE, dataset / gen.CASE_NOTES_FILE,
            secret=KEY, output_dir=tmp_path / "repo" / relative, repo_root=tmp_path / "repo",
        )


@pytest.mark.parametrize("relative", ["temp/private", "data/private/run1"])
def test_extraction_allows_ignored_destinations(
    dataset: Path, tmp_path: Path, relative: str,
) -> None:
    run_extraction(
        dataset / gen.ANTI_JOIN_FILE, dataset / gen.CASE_NOTES_FILE,
        secret=KEY, output_dir=tmp_path / "repo" / relative, repo_root=tmp_path / "repo",
    )
    assert (tmp_path / "repo" / relative / MANIFEST_FILE).exists()
