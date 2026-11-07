"""Native-download contract and pipeline tests using exclusively synthetic rows."""

import csv
import json
from pathlib import Path

import pytest
from openpyxl import Workbook
from pydantic import SecretStr

from jvsg_triage.etl.__main__ import main
from jvsg_triage.etl.contracts import (
    ANTI_JOIN_CONTRACT,
    CASE_NOTES_CONTRACT,
    ReportContract,
    ReportKind,
)
from jvsg_triage.etl.ingest import IngestionError, ingest_reports, inspect_layout

KEY = SecretStr("synthetic-only-development-key-0001")
SENTINEL = "SYNTHETIC_PRIVATE_SENTINEL"


def headers(contract: ReportContract) -> list[str | None]:
    return [column.header for column in contract.columns]


def row(contract: ReportContract, values: dict[str, object]) -> list[object]:
    return [
        values.get(column.target or column.header or "", "")
        for column in contract.columns
    ]


def write_csv(
    path: Path, rows: list[list[object]], *, titles: int = 0,
    header: list[str | None] | None = None,
) -> Path:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerows([[SENTINEL]] * titles)
        writer.writerow(headers(ANTI_JOIN_CONTRACT) if header is None else header)
        writer.writerows(rows)
    return path


def write_xlsx(
    path: Path, rows: list[list[object]], *, titles: int = 3,
    header: list[str | None] | None = None,
) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    for _ in range(titles):
        sheet.append([SENTINEL])
    sheet.append(headers(CASE_NOTES_CONTRACT) if header is None else header)
    for values in rows:
        sheet.append(values)
    workbook.save(path)
    workbook.close()
    return path


def inputs(tmp_path: Path) -> tuple[Path, Path]:
    anti = write_csv(tmp_path / "synthetic.csv", [
        row(ANTI_JOIN_CONTRACT, {"participant_id": "0001", "Office": SENTINEL}),
        row(ANTI_JOIN_CONTRACT, {"participant_id": "0001", "Service": "203"}),
        row(ANTI_JOIN_CONTRACT, {"participant_id": "0002"}),
    ])
    notes = write_xlsx(tmp_path / "synthetic.xlsx", [
        row(CASE_NOTES_CONTRACT, {
            "participant_id": "0001", "text": SENTINEL, "Case\nSubject": SENTINEL,
            "Create\nDate": "ignored-unparsed-date",
            "Contact\nDate": "ignored-unparsed-date",
        }),
        row(CASE_NOTES_CONTRACT, {"participant_id": "0001", "text": SENTINEL}),
        row(CASE_NOTES_CONTRACT, {"participant_id": "0003", "text": SENTINEL}),
    ])
    return anti, notes


def test_observed_layouts_and_schema_are_value_free(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    csv_layout = inspect_layout(anti, ReportKind.ANTI_JOIN)
    xlsx_layout = inspect_layout(notes, ReportKind.CASE_NOTES)
    assert (csv_layout.header_row, csv_layout.column_count) == (1, 46)
    assert (xlsx_layout.header_row, xlsx_layout.column_count, xlsx_layout.sheet_index) == (4, 12, 0)
    assert CASE_NOTES_CONTRACT.columns[1].handling == "blank"
    for layout in (csv_layout, xlsx_layout):
        assert SENTINEL not in layout.model_dump_json()
        assert "synthetic." not in layout.model_dump_json()
    for contract in (ANTI_JOIN_CONTRACT, CASE_NOTES_CONTRACT):
        assert SENTINEL not in contract.model_dump_json()
    opaque = next(column for column in ANTI_JOIN_CONTRACT.columns if column.header == "Date1")
    assert opaque.target is None


@pytest.mark.parametrize("title_count", [0, 3, 10, 49])
def test_csv_skips_title_rows(tmp_path: Path, title_count: int) -> None:
    path = write_csv(tmp_path / "synthetic.csv", [], titles=title_count)
    assert inspect_layout(path, ReportKind.ANTI_JOIN).header_row == title_count + 1


@pytest.mark.parametrize("title_count", [0, 3, 8, 49])
def test_xlsx_skips_title_rows(tmp_path: Path, title_count: int) -> None:
    path = write_xlsx(tmp_path / "synthetic.xlsx", [], titles=title_count)
    assert inspect_layout(path, ReportKind.CASE_NOTES).header_row == title_count + 1


@pytest.mark.parametrize("kind", list(ReportKind))
def test_header_scan_is_bounded(tmp_path: Path, kind: ReportKind) -> None:
    if kind == ReportKind.ANTI_JOIN:
        path = write_csv(tmp_path / "synthetic.csv", [], titles=50)
    else:
        path = write_xlsx(tmp_path / "synthetic.xlsx", [], titles=50)
    with pytest.raises(IngestionError, match="within first 50 rows"):
        inspect_layout(path, kind)


def test_header_normalizes_line_breaks_spaces_case_and_bom(tmp_path: Path) -> None:
    header = [
        " \ufeff" + value.upper().replace("\n", "  ") if value else None
        for value in headers(CASE_NOTES_CONTRACT)
    ]
    # The BOM is a prefix, not an embedded part of a label.
    header = [value.strip() if value else None for value in header]
    path = write_xlsx(tmp_path / "synthetic.xlsx", [], header=header)
    assert inspect_layout(path, ReportKind.CASE_NOTES).column_count == 12


@pytest.mark.parametrize("mutation", ["unknown", "missing", "duplicate", "reorder", "extra"])
@pytest.mark.parametrize("kind", list(ReportKind))
def test_changed_headers_fail_without_echoing_cells(
    tmp_path: Path, mutation: str, kind: ReportKind,
) -> None:
    contract = ANTI_JOIN_CONTRACT if kind == ReportKind.ANTI_JOIN else CASE_NOTES_CONTRACT
    header = headers(contract)
    if mutation == "unknown":
        header[0] = SENTINEL
    elif mutation == "missing":
        header.pop(0)
    elif mutation == "duplicate":
        header[0] = header[-1]
    elif mutation == "reorder":
        header[0], header[2] = header[2], header[0]
    else:
        header.append(SENTINEL)
    path = (
        write_csv(tmp_path / "synthetic.csv", [], header=header)
        if kind == ReportKind.ANTI_JOIN
        else write_xlsx(tmp_path / "synthetic.xlsx", [], header=header)
    )
    with pytest.raises(IngestionError) as error:
        inspect_layout(path, kind)
    assert SENTINEL not in str(error.value)
    assert "synthetic." not in str(error.value)


def test_match_is_deterministic_preserves_rows_and_protects_outputs(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.summary.model_dump() == {
        "anti_join_rows": 3, "unique_participants": 2, "repeated_participant_rows": 1,
        "case_note_rows": 3, "matched_note_rows": 2, "unmatched_note_rows": 1,
        "participants_with_notes": 1, "participants_without_notes": 1,
    }
    assert len(batch.cohort) == 3
    assert len(batch.matched_notes) == 2
    assert batch.matched_notes[0].text.get_secret_value() == SENTINEL
    assert set(type(batch.cohort[0]).model_fields) == {"source", "participant_token"}
    assert set(type(batch.matched_notes[0]).model_fields) == {
        "source", "participant_token", "text",
    }
    assert batch.cohort[0].source.row_number == 2
    assert batch.matched_notes[0].source.row_number == 5
    repeat = ingest_reports(anti, notes, secret=KEY)
    assert repeat == batch
    other = ingest_reports(anti, notes, secret=SecretStr("synthetic-other-development-key-0002"))
    assert other.cohort[0].participant_token != batch.cohort[0].participant_token
    for record in [batch, *batch.cohort, *batch.matched_notes]:
        for rendered in [repr(record), record.model_dump_json(), str(record.model_dump())]:
            assert SENTINEL not in rendered
            assert "0001" not in rendered
            assert batch.cohort[0].participant_token not in rendered


def test_header_only_inputs_produce_empty_batch(tmp_path: Path) -> None:
    anti = write_csv(tmp_path / "synthetic.csv", [])
    notes = write_xlsx(tmp_path / "synthetic.xlsx", [])
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.summary.anti_join_rows == batch.summary.case_note_rows == 0
    assert batch.cohort == batch.matched_notes == ()


@pytest.mark.parametrize("value", ["", None])
def test_missing_identity_is_sanitized(tmp_path: Path, value: object) -> None:
    anti, notes = inputs(tmp_path)
    write_csv(anti, [row(ANTI_JOIN_CONTRACT, {"participant_id": value, "Office": SENTINEL})])
    with pytest.raises(IngestionError, match="StateID"):
        ingest_reports(anti, notes, secret=KEY)


@pytest.mark.parametrize("value", [True, -1, 1.5])
def test_invalid_excel_identity_is_sanitized(tmp_path: Path, value: object) -> None:
    anti, notes = inputs(tmp_path)
    write_xlsx(notes, [row(CASE_NOTES_CONTRACT, {"participant_id": value, "text": SENTINEL})])
    with pytest.raises(IngestionError, match="StateID"):
        ingest_reports(anti, notes, secret=KEY)


def test_excel_integer_identity_preserves_csv_text_zeros(tmp_path: Path) -> None:
    anti = write_csv(tmp_path / "synthetic.csv", [
        row(ANTI_JOIN_CONTRACT, {"participant_id": "123"}),
        row(ANTI_JOIN_CONTRACT, {"participant_id": "0123"}),
    ])
    notes = write_xlsx(tmp_path / "synthetic.xlsx", [
        row(CASE_NOTES_CONTRACT, {"participant_id": 123, "text": SENTINEL}),
    ])
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.summary.unique_participants == 2
    assert batch.summary.matched_note_rows == 1
    assert batch.matched_notes[0].participant_token == batch.cohort[0].participant_token


@pytest.mark.parametrize("field", ["Create\nDate", "Contact\nDate", "Last Edit Date"])
def test_unneeded_dates_are_not_parsed_or_retained(tmp_path: Path, field: str) -> None:
    anti, notes = inputs(tmp_path)
    write_xlsx(notes, [row(CASE_NOTES_CONTRACT, {
        "participant_id": "unknown-synthetic", "text": SENTINEL, field: SENTINEL,
    })])
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.summary.unmatched_note_rows == 1
    assert SENTINEL not in batch.model_dump_json()


def test_empty_note_is_not_silently_skipped(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    write_xlsx(notes, [row(CASE_NOTES_CONTRACT, {"participant_id": "0001"})])
    with pytest.raises(IngestionError, match="Case Notes requires nonblank text"):
        ingest_reports(anti, notes, secret=KEY)


@pytest.mark.parametrize("text", [123, True, " \n "])
def test_invalid_note_type_is_sanitized(tmp_path: Path, text: object) -> None:
    anti, notes = inputs(tmp_path)
    write_xlsx(notes, [row(CASE_NOTES_CONTRACT, {"participant_id": "0001", "text": text})])
    with pytest.raises(IngestionError, match="Case Notes requires nonblank text"):
        ingest_reports(anti, notes, secret=KEY)


def test_note_text_is_preserved_exactly(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    text = "  Synthetic note:\n    - preserve indentation and trailing newline\n"
    write_xlsx(notes, [row(CASE_NOTES_CONTRACT, {"participant_id": "0001", "text": text})])
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.matched_notes[0].text.get_secret_value() == text


@pytest.mark.parametrize("width", [45, 47])
def test_wrong_csv_row_width_is_sanitized(tmp_path: Path, width: int) -> None:
    anti, notes = inputs(tmp_path)
    write_csv(anti, [[SENTINEL] * width])
    with pytest.raises(IngestionError, match="incorrect width") as error:
        ingest_reports(anti, notes, secret=KEY)
    assert SENTINEL not in str(error.value)


def test_populated_blank_xlsx_column_fails(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    values = row(CASE_NOTES_CONTRACT, {"participant_id": "0001", "text": SENTINEL})
    values[1] = SENTINEL
    write_xlsx(notes, [values])
    with pytest.raises(IngestionError, match="blank layout column 2"):
        ingest_reports(anti, notes, secret=KEY)


def test_multiple_worksheets_are_not_silently_ignored(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.xlsx"
    workbook = Workbook()
    workbook.create_sheet(SENTINEL)
    workbook.save(path)
    workbook.close()
    with pytest.raises(IngestionError, match="exactly one worksheet") as error:
        inspect_layout(path, ReportKind.CASE_NOTES)
    assert SENTINEL not in str(error.value)


@pytest.mark.parametrize("kind", list(ReportKind))
def test_invalid_file_errors_do_not_echo_paths(tmp_path: Path, kind: ReportKind) -> None:
    extension = ".csv" if kind == ReportKind.ANTI_JOIN else ".xlsx"
    path = tmp_path / f"{SENTINEL}{extension}"
    with pytest.raises(IngestionError) as error:
        inspect_layout(path, kind)
    assert SENTINEL not in str(error.value)
    path.write_bytes(b"\xff\x00INVALID")
    with pytest.raises(IngestionError) as error:
        inspect_layout(path, kind)
    assert SENTINEL not in str(error.value)


def test_wrong_extension_fails(tmp_path: Path) -> None:
    with pytest.raises(IngestionError, match="expected .csv"):
        inspect_layout(tmp_path / "synthetic.xlsx", ReportKind.ANTI_JOIN)


def test_short_secret_fails_without_echoing_key(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    with pytest.raises(IngestionError, match="at least 32") as error:
        ingest_reports(anti, notes, secret=SecretStr(SENTINEL))
    assert SENTINEL not in str(error.value)


def test_cli_inspect_never_reads_malformed_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    anti, notes = inputs(tmp_path)
    with anti.open("a", encoding="utf-8") as stream:
        stream.write('"' + SENTINEL)
    monkeypatch.setattr("sys.argv", [
        "etl", "inspect", "--anti-join", str(anti), "--case-notes", str(notes),
    ])
    assert main() == 0
    output = capsys.readouterr().out
    assert SENTINEL not in output
    assert [layout["header_row"] for layout in json.loads(output)] == [1, 4]


def test_blank_rows_skipped_without_losing_other_rows(tmp_path: Path) -> None:
    anti, notes = inputs(tmp_path)
    write_csv(anti, [[], [""] * 46, row(ANTI_JOIN_CONTRACT, {"participant_id": "0001"})])
    batch = ingest_reports(anti, notes, secret=KEY)
    assert batch.summary.anti_join_rows == 1


def test_checked_in_contract_matches_model() -> None:
    schema = Path(__file__).resolve().parents[1] / "data" / "schemas" / "mis_reports.v1.json"
    actual = json.loads(schema.read_text(encoding="utf-8"))
    assert actual == {
        "anti_join": ANTI_JOIN_CONTRACT.model_dump(mode="json"),
        "case_notes": CASE_NOTES_CONTRACT.model_dump(mode="json"),
    }


def test_cli_schema_and_error_are_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["etl", "schema"])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["case_notes"]["observed_header_row"] == 4
    monkeypatch.setattr("sys.argv", [
        "etl", "inspect", "--anti-join", str(tmp_path / f"{SENTINEL}.csv"),
        "--case-notes", str(tmp_path / f"{SENTINEL}.xlsx"),
    ])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert SENTINEL not in capsys.readouterr().err
