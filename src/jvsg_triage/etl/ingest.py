"""Offline native CSV/XLSX ingestion with bounded header discovery."""

import csv
import hashlib
import hmac
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date, datetime, time
from pathlib import Path
from typing import BinaryIO, TextIO

from openpyxl import load_workbook
from pydantic import SecretStr

from jvsg_triage.etl.contracts import CONTRACTS, ReportContract, ReportKind, normalize_header
from jvsg_triage.etl.models import (
    AntiJoinRecord,
    CaseNoteRecord,
    IntakeBatch,
    Provenance,
    Reconciliation,
    SourceLayout,
)

MAX_HEADER_ROWS = 50


class IngestionError(ValueError):
    """Sanitized failure: report kind, coordinates and field labels only."""


@contextmanager
def _rows(path: Path, kind: ReportKind) -> Iterator[Iterator[tuple[int, Sequence[object]]]]:
    contract = CONTRACTS[kind]
    if path.suffix.lower() != f".{contract.format}":
        raise IngestionError(f"{kind}: expected .{contract.format} input")
    stream: TextIO | BinaryIO | None = None
    try:
        if kind == ReportKind.ANTI_JOIN:
            stream = path.open("r", encoding="utf-8-sig", newline="")
            yield iter(enumerate(csv.reader(stream, strict=True), 1))
        else:
            # Use a file handle so workbook resources close even when header discovery stops early.
            stream = path.open("rb")
            workbook = load_workbook(stream, read_only=True, data_only=True)
            try:
                if len(workbook.worksheets) != 1:
                    raise IngestionError(f"{kind}: expected exactly one worksheet")
                yield iter(enumerate(workbook.worksheets[0].iter_rows(values_only=True), 1))
            finally:
                workbook.close()
    finally:
        if stream is not None:
            stream.close()


def _find_header(
    rows: Iterator[tuple[int, Sequence[object]]], contract: ReportContract,
) -> SourceLayout:
    expected = tuple(normalize_header(column.header) for column in contract.columns)
    for number, row in rows:
        if number > MAX_HEADER_ROWS:
            break
        actual = tuple(normalize_header(cell) for cell in row)
        if actual == expected:
            return SourceLayout(
                report=contract.kind,
                header_row=number,
                column_count=len(expected),
                sheet_index=0 if contract.format == "xlsx" else None,
            )
        if set(contract.anchors).issubset(actual):
            raise IngestionError(
                f"{contract.kind}: header layout changed at row {number}; "
                "expected ordered contract v1.0 columns"
            )
    raise IngestionError(
        f"{contract.kind}: required header not found within first {MAX_HEADER_ROWS} rows"
    )


def inspect_layout(path: Path, kind: ReportKind) -> SourceLayout:
    """Read only through the header; return no filenames, titles or data values."""
    try:
        with _rows(path, kind) as rows:
            return _find_header(rows, CONTRACTS[kind])
    except IngestionError:
        raise
    except Exception:
        # Parser errors can quote record values, paths or workbook XML; do not propagate them.
        raise IngestionError(f"{kind}: cannot read report; verify format and file access") from None


def _text(value: object) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _token(value: object, secret: bytes, source: Provenance) -> str:
    if isinstance(value, str):
        identifier = value.strip()
    elif isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        identifier = str(value)
    else:
        raise IngestionError(
            f"{source.report}: row {source.row_number}, StateID must be text or an integer"
        )
    if not identifier:
        raise IngestionError(f"{source.report}: row {source.row_number}, StateID is required")
    return hmac.new(secret, identifier.encode("utf-8"), hashlib.sha256).hexdigest()


def _timestamp(value: object, field: str, source: Provenance) -> datetime | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time())
    if isinstance(value, str):
        for pattern in (
            "%m/%d/%Y", "%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M %p", "%m/%d/%Y %I:%M:%S %p",
            "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                return datetime.strptime(value.strip(), pattern)
            except ValueError:
                continue
    raise IngestionError(
        f"{source.report}: row {source.row_number}, {field} requires an Excel date "
        "or supported US/ISO date text"
    )


def _mapped_rows(
    path: Path, kind: ReportKind,
) -> Iterator[tuple[SourceLayout, Provenance, dict[str, object]]]:
    contract = CONTRACTS[kind]
    with _rows(path, kind) as rows:
        layout = _find_header(rows, contract)
        for number, row in rows:
            if all(value is None or value == "" for value in row):
                continue
            if len(row) != layout.column_count:
                raise IngestionError(
                    f"{kind}: row {number} has incorrect width; expected {layout.column_count}"
                )
            for column in contract.columns:
                if column.handling == "blank" and _text(row[column.position - 1]) is not None:
                    raise IngestionError(
                        f"{kind}: row {number}, blank layout column {column.position} has data"
                    )
            values = {
                column.target: row[column.position - 1]
                for column in contract.columns if column.target is not None
            }
            yield layout, Provenance(
                report=kind, row_number=number, sheet_index=layout.sheet_index,
            ), values


def ingest_reports(anti_join_csv: Path, case_notes_xlsx: Path, *, secret: SecretStr) -> IntakeBatch:
    """Match notes to the supplied cohort privately; preserve source row multiplicity.

    The secret must be a locally supplied key of at least 32 UTF-8 bytes.
    No files are written, no service-code or FY rules are inferred, and this API
    does not scrub note content or authorize its use by an inference service.
    """
    key = secret.get_secret_value().encode("utf-8")
    if len(key) < 32:
        raise IngestionError("intake: HMAC secret must contain at least 32 UTF-8 bytes")
    cohort: list[AntiJoinRecord] = []
    notes: list[CaseNoteRecord] = []
    layouts: list[SourceLayout] = []
    try:
        # Independent inspections also provide layouts for valid header-only inputs.
        layouts.append(inspect_layout(anti_join_csv, ReportKind.ANTI_JOIN))
        layouts.append(inspect_layout(case_notes_xlsx, ReportKind.CASE_NOTES))
        for _, source, values in _mapped_rows(anti_join_csv, ReportKind.ANTI_JOIN):
            cohort.append(AntiJoinRecord(
                source=source,
                participant_token=_token(values["participant_id"], key, source),
                region=_text(values["region"]),
                office=_text(values["office"]),
                office_responsible=_text(values["office_responsible"]),
                service=_text(values["service"]),
                completion_status=_text(values["completion_status"]),
            ))
        tokens = {record.participant_token for record in cohort}
        total_notes = 0
        for _, source, values in _mapped_rows(case_notes_xlsx, ReportKind.CASE_NOTES):
            participant_token = _token(values["participant_id"], key, source)
            text = _text(values["text"])
            if text is None:
                raise IngestionError(f"case_notes: row {source.row_number}, Case Notes is required")
            subject = _text(values["subject"])
            note = CaseNoteRecord(
                source=source,
                participant_token=participant_token,
                created_at=_timestamp(values["created_at"], "Create Date", source),
                contact_at=_timestamp(values["contact_at"], "Contact Date", source),
                last_edited_at=_timestamp(values["last_edited_at"], "Last Edit Date", source),
                contact_type=_text(values["contact_type"]),
                subject=SecretStr(subject) if subject else None,
                text=SecretStr(text),
            )
            total_notes += 1
            if participant_token in tokens:
                notes.append(note)
        with_notes = {note.participant_token for note in notes}
        return IntakeBatch(
            layouts=(layouts[0], layouts[1]),
            summary=Reconciliation(
                anti_join_rows=len(cohort),
                unique_participants=len(tokens),
                repeated_participant_rows=len(cohort) - len(tokens),
                case_note_rows=total_notes,
                matched_note_rows=len(notes),
                unmatched_note_rows=total_notes - len(notes),
                participants_with_notes=len(with_notes),
                participants_without_notes=len(tokens - with_notes),
            ),
            cohort=tuple(cohort),
            matched_notes=tuple(notes),
        )
    except IngestionError:
        raise
    except Exception:
        raise IngestionError(
            "intake: report parsing failed; verify file access, cell types and encoding"
        ) from None
