"""Synthetic SharePoint file-drop boundary and vectorized workbook transformation."""

import io
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

import polars as pl
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from pydantic import ValidationError

from jvsg_triage.demo.labels import (
    FIELD_LABELS,
    OFFICE_LABELS,
    REVIEW_LABELS,
    SOURCE_VALUE_CODES,
    STATE_LABELS,
)
from jvsg_triage.demo.models import (
    AS_OF,
    HEADERS,
    MARKER,
    Alert,
    DemoError,
    Office,
    Profile,
    Review,
    SourceRecord,
    State,
)

MAX_ROWS = 10_000
MAX_BYTES = 5_000_000


def fixture_records(*, refreshed: bool = False) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    states = list(State)
    for index in range(18):
        values = {
            "demo_id": f"DEMO-{index + 1:04d}",
            "office": list(Office)[index // 6],
            "assessment_date": AS_OF - timedelta(days=70 + index),
            "last_contact_date": AS_OF - timedelta(days=(0, 14, 15, 29, 30, 45)[index % 6]),
            "TRN": states[index % 5], "HSG": states[(index + 1) % 5],
            "MED": states[(index + 2) % 5], "LEG": states[(index + 3) % 5],
            "review": Review.REVIEWED if index in (1, 9) else Review.PENDING,
        }
        records.append(SourceRecord.model_validate(values))
    if refreshed:
        values = records[4].model_dump()
        values.update(last_contact_date=AS_OF, HSG=State.MIT)
        records[4] = SourceRecord.model_validate(values)
        values = records[0].model_dump()
        values.update(demo_id="DEMO-0019", office=Office.SOUTH)
        records.append(SourceRecord.model_validate(values))
    return records


def source_workbook(records: list[SourceRecord]) -> Workbook:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Demo Intake"
    sheet.append([MARKER])
    sheet.append([FIELD_LABELS[field] for field in HEADERS])
    for record in records:
        values = record.model_dump()
        values["office"] = OFFICE_LABELS[record.office]
        values["review"] = REVIEW_LABELS[record.review]
        for field in ("TRN", "HSG", "MED", "LEG"):
            values[field] = STATE_LABELS[getattr(record, field)]
        sheet.append([values[field] for field in HEADERS])
    sheet.freeze_panes = "C3"
    sheet.auto_filter.ref = f"A2:I{len(records) + 2}"
    for column in ("A", "B", "C", "D", "E", "F", "G", "H", "I"):
        sheet.column_dimensions[column].width = 29
    for row in sheet.iter_rows(min_row=3, min_col=3, max_col=4):
        for cell in row:
            cell.number_format = "mmm d, yyyy"
    return workbook


def read_source(content: bytes) -> list[SourceRecord]:
    if len(content) > MAX_BYTES:
        raise DemoError("intake: workbook exceeds demo size limit")
    try:
        with ZipFile(io.BytesIO(content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > 25_000_000:
                raise DemoError("intake: expanded workbook exceeds demo size limit")
        workbook = load_workbook(
            io.BytesIO(content), read_only=True, data_only=False, keep_links=False,
        )
    except DemoError:
        raise
    except (BadZipFile, InvalidFileException, OSError, ValueError, KeyError, ParseError):
        raise DemoError("intake: unreadable XLSX workbook") from None
    try:
        if workbook.sheetnames != ["Demo Intake"]:
            raise DemoError("intake: expected only the Demo Intake worksheet")
        sheet = workbook["Demo Intake"]
        if sheet.max_column != len(HEADERS) or (sheet.max_row or 0) > MAX_ROWS + 2:
            raise DemoError("intake: worksheet dimensions exceed the demo contract")
        rows = sheet.iter_rows(values_only=True)
        marker = next(rows, ())
        if marker != (MARKER, *([None] * (len(HEADERS) - 1))):
            raise DemoError("intake: synthetic marker missing")
        headers = next(rows, ())
        if headers not in (HEADERS, tuple(FIELD_LABELS[field] for field in HEADERS)):
            raise DemoError("intake: headers differ from the demo contract")
        records = []
        seen: set[str] = set()
        for number, row in enumerate(rows, start=3):
            if number > MAX_ROWS + 2 or len(row) != len(HEADERS):
                raise DemoError("intake: row limit or column mismatch")
            values = dict(zip(HEADERS, row, strict=True))
            for field, codes in SOURCE_VALUE_CODES.items():
                value = values[field]
                if isinstance(value, str) and value in codes:
                    values[field] = codes[value]
            for field in ("assessment_date", "last_contact_date"):
                value = values[field]
                if isinstance(value, datetime):
                    if value.time() != datetime.min.time():
                        raise DemoError(f"intake: row {number} requires date-only cells")
                    values[field] = value.date()
                elif value is not None and not isinstance(value, date):
                    if not isinstance(value, str) or len(value) != 10:
                        raise DemoError(f"intake: row {number} requires ISO dates")
                    try:
                        parsed = date.fromisoformat(value)
                    except ValueError:
                        raise DemoError(f"intake: row {number} requires ISO dates") from None
                    if parsed.isoformat() != value:
                        raise DemoError(f"intake: row {number} requires YYYY-MM-DD dates")
                    values[field] = parsed
            try:
                record = SourceRecord.model_validate(values)
            except ValidationError:
                raise DemoError(f"intake: row {number} violates the closed demo schema") from None
            if record.demo_id in seen:
                raise DemoError(f"intake: duplicate demo ID at row {number}")
            seen.add(record.demo_id)
            records.append(record)
        if not records:
            raise DemoError("intake: empty demo workbook")
        return records
    except (BadZipFile, ParseError, KeyError, ValueError) as error:
        if isinstance(error, DemoError):
            raise
        raise DemoError("intake: malformed worksheet") from None
    finally:
        workbook.close()


def transform(records: list[SourceRecord], as_of: date) -> list[Profile]:
    if not records:
        raise DemoError("transform: empty batch")
    frame = pl.DataFrame([record.model_dump(mode="json") for record in records])
    frame = frame.with_columns(
        pl.col("assessment_date").str.to_date("%Y-%m-%d"),
        pl.col("last_contact_date").cast(pl.String).str.to_date("%Y-%m-%d"),
    ).with_columns(
        pl.coalesce("last_contact_date", "assessment_date").alias("touch")
    )
    if frame.filter(
        (pl.col("assessment_date") > pl.lit(as_of)) | (pl.col("touch") > pl.lit(as_of))
    ).height:
        raise DemoError("transform: future dates are not allowed")
    frame = frame.with_columns(
        (pl.lit(as_of) - pl.col("touch")).dt.total_days().alias("idle_days")
    ).with_columns(
        pl.when(pl.col("idle_days") >= 30).then(pl.lit(Alert.RED.value))
        .when(pl.col("idle_days") >= 15).then(pl.lit(Alert.YELLOW.value))
        .otherwise(pl.lit(Alert.GREEN.value)).alias("alert"),
        pl.lit(as_of).alias("as_of"),
    ).drop("touch").sort("demo_id")
    return [Profile.model_validate(row) for row in frame.to_dicts()]


def read_bytes(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            content = stream.read(MAX_BYTES + 1)
    except OSError:
        raise DemoError("intake: cannot read source workbook") from None
    return content
