"""Offline native CSV/XLSX ingestion with bounded header and footer validation."""

import csv
import hashlib
import hmac
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook
from pydantic import SecretStr

from jvsg_triage.etl.contracts import (
    CONTRACTS,
    FOOTER_TOTAL,
    ReportContract,
    ReportKind,
    normalize_header,
)
from jvsg_triage.etl.models import (
    AntiJoinRecord,
    CaseNoteRecord,
    IntakeBatch,
    Provenance,
    Reconciliation,
    RedactionLexicon,
    SourceLayout,
)

MAX_HEADER_ROWS = 50
MIN_SECRET_BYTES = 32


class IngestionError(ValueError):
    """Sanitized failure: report kind, coordinates and field labels only."""


@dataclass
class _SourceRow:
    source: Provenance
    projected: dict[str, object]
    lexicon: list[tuple[str, object]]


@dataclass
class _Report:
    layout: SourceLayout
    rows: list[_SourceRow] = field(default_factory=list)
    declared_total: int | None = None


@contextmanager
def _rows(path: Path, kind: ReportKind) -> Iterator[Iterator[tuple[int, Sequence[object]]]]:
    contract = CONTRACTS[kind]
    if path.suffix.lower() != f".{contract.format}":
        raise IngestionError(f"{kind}: expected .{contract.format} input")
    if contract.format == "csv":
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            yield iter(enumerate(csv.reader(stream, strict=True), 1))
    else:
        # A handle closes workbook resources even when discovery stops early.
        with path.open("rb") as binary_stream:
            workbook = load_workbook(binary_stream, read_only=True, data_only=True)
            try:
                if len(workbook.worksheets) != 1:
                    raise IngestionError(f"{kind}: expected exactly one worksheet")
                yield iter(enumerate(workbook.worksheets[0].iter_rows(values_only=True), 1))
            finally:
                workbook.close()


def _is_blank(row: Sequence[object]) -> bool:
    return all(value is None or (isinstance(value, str) and not value.strip()) for value in row)


def _matches_header(row: Sequence[object], contract: ReportContract) -> bool:
    expected = tuple(normalize_header(column.header) for column in contract.columns)
    return tuple(normalize_header(cell) for cell in row) == expected


def _find_header(
    rows: Iterator[tuple[int, Sequence[object]]], contract: ReportContract,
) -> SourceLayout:
    for number, row in rows:
        if number > MAX_HEADER_ROWS:
            break
        if _matches_header(row, contract):
            return SourceLayout(
                report=contract.kind,
                header_row=number,
                column_count=len(contract.columns),
                sheet_index=0 if contract.format == "xlsx" else None,
            )
        if set(contract.anchors).issubset(normalize_header(cell) for cell in row):
            raise IngestionError(
                f"{contract.kind}: header layout changed at row {number}; "
                f"expected ordered contract v{contract.version} columns"
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


def _read_footer(
    rows: Iterator[tuple[int, Sequence[object]]], kind: ReportKind, header_row: int,
) -> int:
    """Native XLSX footer: repeated header, then 'Total Rows: N', then blanks only."""
    declared: int | None = None
    for number, row in rows:
        if _is_blank(row):
            continue
        first = row[0] if row else None
        match = FOOTER_TOTAL.fullmatch(str(first).strip()) if isinstance(first, str) else None
        if declared is None and match and _is_blank(row[1:]):
            declared = int(match.group(1).replace(",", ""))
            continue
        raise IngestionError(f"{kind}: unexpected content at row {number} after footer header")
    if declared is None:
        raise IngestionError(
            f"{kind}: footer after row {header_row} lacks 'Total Rows'; download may be truncated"
        )
    return declared


def _read_report(path: Path, kind: ReportKind) -> _Report:
    contract = CONTRACTS[kind]
    with _rows(path, kind) as rows:
        report = _Report(layout=_find_header(rows, contract))
        footer_seen = False
        for number, row in rows:
            if _is_blank(row):
                continue
            if contract.footer == "repeated_header_total_rows" and _matches_header(row, contract):
                report.declared_total = _read_footer(rows, kind, number)
                footer_seen = True
                break
            if len(row) != report.layout.column_count:
                raise IngestionError(
                    f"{kind}: row {number} has incorrect width; "
                    f"expected {report.layout.column_count}"
                )
            projected: dict[str, object] = {}
            lexicon: list[tuple[str, object]] = []
            for column in contract.columns:
                value = row[column.position - 1]
                if column.handling == "blank" and not _is_blank([value]):
                    raise IngestionError(
                        f"{kind}: row {number}, blank layout column {column.position} has data"
                    )
                if column.handling == "projected" and column.target:
                    projected[column.target] = value
                elif column.handling == "lexicon" and column.target:
                    lexicon.append((column.target, value))
            report.rows.append(_SourceRow(
                Provenance(report=kind, row_number=number, sheet_index=report.layout.sheet_index),
                projected,
                lexicon,
            ))
        if contract.footer == "repeated_header_total_rows" and not footer_seen:
            raise IngestionError(f"{kind}: native footer missing; download may be truncated")
        if report.declared_total is not None and report.declared_total != len(report.rows):
            raise IngestionError(
                f"{kind}: footer declares {report.declared_total} rows but "
                f"{len(report.rows)} were read"
            )
    return report


def identifier_text(value: object) -> str | None:
    """Normalize an MIS identifier cell; Excel integers become decimal text."""
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return str(value)
    return None


def participant_token(identifier: str, secret: bytes) -> str:
    """HMAC-SHA256 pseudonym; stable for one key, unlinkable without it."""
    return hmac.new(secret, identifier.encode("utf-8"), hashlib.sha256).hexdigest()


def _token(value: object, secret: bytes, source: Provenance) -> str:
    identifier = identifier_text(value)
    if identifier is None:
        if value is None or (isinstance(value, str) and not value.strip()):
            raise IngestionError(f"{source.report}: row {source.row_number}, StateID is required")
        raise IngestionError(
            f"{source.report}: row {source.row_number}, StateID must be text or an integer"
        )
    return participant_token(identifier, secret)


def _secret_bytes(secret: SecretStr) -> bytes:
    key = secret.get_secret_value().encode("utf-8")
    if len(key) < MIN_SECRET_BYTES:
        raise IngestionError(
            f"intake: HMAC secret must contain at least {MIN_SECRET_BYTES} UTF-8 bytes"
        )
    return key


def ingest_reports(anti_join_csv: Path, case_notes_xlsx: Path, *, secret: SecretStr) -> IntakeBatch:
    """Match notes to the supplied cohort privately; preserve source row multiplicity.

    No files are written and no service-code or FY rules are inferred. Note text is
    raw (T1): pass the batch to ``jvsg_triage.privacy.redact_batch`` before any use.
    """
    key = _secret_bytes(secret)
    person_names: set[str] = set()
    staff_names: set[str] = set()
    identifiers: set[str] = set()

    def collect(entries: list[tuple[str, object]]) -> list[str]:
        names: list[str] = []
        for target, value in entries:
            text = identifier_text(value)
            if text is None:
                continue
            if target == "person_name":
                person_names.add(text)
                names.append(text)
            elif target == "staff_name":
                staff_names.add(text)
                names.append(text)
            else:
                identifiers.add(text)
        return names

    try:
        anti = _read_report(anti_join_csv, ReportKind.ANTI_JOIN)
        notes_report = _read_report(case_notes_xlsx, ReportKind.CASE_NOTES)
        cohort: list[AntiJoinRecord] = []
        for row in anti.rows:
            collect(row.lexicon)
            sid = identifier_text(row.projected["participant_id"])
            if sid:
                identifiers.add(sid)
            cohort.append(AntiJoinRecord(
                source=row.source,
                participant_token=_token(row.projected["participant_id"], key, row.source),
            ))
        tokens = {record.participant_token for record in cohort}
        matched: list[CaseNoteRecord] = []
        for row in notes_report.rows:
            names = collect(row.lexicon)
            sid = identifier_text(row.projected["participant_id"])
            if sid:
                identifiers.add(sid)
            token = _token(row.projected["participant_id"], key, row.source)
            text = row.projected["text"]
            if not isinstance(text, str) or not text.strip():
                raise IngestionError(
                    f"case_notes: row {row.source.row_number}, Case Notes requires nonblank text"
                )
            if token in tokens:
                matched.append(CaseNoteRecord(
                    source=row.source,
                    participant_token=token,
                    text=SecretStr(text),
                    context_names=tuple(SecretStr(name) for name in names),
                ))
        with_notes = {note.participant_token for note in matched}
        return IntakeBatch(
            layouts=(anti.layout, notes_report.layout),
            summary=Reconciliation(
                anti_join_rows=len(cohort),
                unique_participants=len(tokens),
                repeated_participant_rows=len(cohort) - len(tokens),
                case_note_rows=len(notes_report.rows),
                declared_case_note_rows=notes_report.declared_total,
                matched_note_rows=len(matched),
                unmatched_note_rows=len(notes_report.rows) - len(matched),
                participants_with_notes=len(with_notes),
                participants_without_notes=len(tokens - with_notes),
            ),
            cohort=tuple(cohort),
            matched_notes=tuple(matched),
            lexicon=RedactionLexicon(
                person_names=frozenset(person_names),
                staff_names=frozenset(staff_names),
                identifiers=frozenset(identifiers),
            ),
        )
    except IngestionError:
        raise
    except Exception:
        raise IngestionError(
            "intake: report parsing failed; verify file access, cell types and encoding"
        ) from None
