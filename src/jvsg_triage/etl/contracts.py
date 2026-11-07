"""Versioned, header-only contracts for native MIS report downloads."""

import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReportKind(StrEnum):
    """Supported downloads, not independently verified service populations."""

    ANTI_JOIN = "anti_join"
    CASE_NOTES = "case_notes"


class ColumnContract(BaseModel):
    """Describe a source position without storing example record values."""

    model_config = ConfigDict(frozen=True)

    position: int
    header: str | None
    target: str | None = None
    handling: Literal["protected", "unmapped", "blank"] = "unmapped"
    data_type: Literal["identifier", "text", "unknown", "blank"]


class ReportContract(BaseModel):
    """Exact ordered layout; header discovery tolerates preceding title rows."""

    model_config = ConfigDict(frozen=True)

    version: Literal["1.0"] = "1.0"
    kind: ReportKind
    format: Literal["csv", "xlsx"]
    observed_header_row: int
    columns: tuple[ColumnContract, ...]
    anchors: tuple[str, ...]


def normalize_header(value: object) -> str:
    """Ignore BOM, line wrapping, spacing and case, but not field identity."""
    return re.sub(r"\s+", "", str(value or "").strip().lstrip("\ufeff")).casefold()


ANTI_JOIN_HEADERS = (
    "programdesc3", "Username", "StateID", "Textbox72", "Region", "Office",
    "OfficeResponsible", "FirstName", "LastName", "SSN", "CityStateCountry",
    "primephone", "email", "employmentdate", "Service", "Naics", "onetcode",
    "CompletionStatus", "programserv", "Provider", "StaffCreated", "Date1", "Date2",
    "Date3", "Date4", "Date5", "col_exitdate", "EditStaff", "DSSClientID", "EDGStatus",
    "TimeLimitedStatus", "AppID", "CaseManager", "registeredapprenticeship",
    "apprenticeshiptype", "Hispanic", "learningmode", "agencycode", "col_offender",
    "comments", "itapaying", "textbox81", "textbox82", "textbox83", "textbox84",
    "textbox85",
)

CASE_NOTE_HEADERS = (
    "Userid", None, "Individual", "Created By", "Create\nDate", "Contact\nDate",
    "Contact\nType", "Last\nEdited By", "Last Edit Date", "State\nID",
    "Case\nSubject", "Case Notes",
)


def _columns(
    headers: tuple[str | None, ...], mappings: dict[str, str],
) -> tuple[ColumnContract, ...]:
    return tuple(
        ColumnContract(
            position=index,
            header=header,
            target=mappings.get(normalize_header(header)),
            handling=(
                "blank" if header is None
                else "protected" if normalize_header(header) in mappings
                else "unmapped"
            ),
            data_type=(
                "blank" if header is None
                else "identifier" if mappings.get(normalize_header(header)) == "participant_id"
                else "text" if normalize_header(header) in mappings
                else "unknown"
            ),
        )
        for index, header in enumerate(headers, 1)
    )


ANTI_JOIN_CONTRACT = ReportContract(
    kind=ReportKind.ANTI_JOIN,
    format="csv",
    observed_header_row=1,
    columns=_columns(
        ANTI_JOIN_HEADERS,
        {"stateid": "participant_id"},
    ),
    anchors=("stateid", "service", "officeresponsible"),
)

CASE_NOTES_CONTRACT = ReportContract(
    kind=ReportKind.CASE_NOTES,
    format="xlsx",
    observed_header_row=4,
    columns=_columns(
        CASE_NOTE_HEADERS,
        {
            "stateid": "participant_id",
            "casenotes": "text",
        },
    ),
    anchors=("stateid", "casesubject", "casenotes"),
)

CONTRACTS = {
    ReportKind.ANTI_JOIN: ANTI_JOIN_CONTRACT,
    ReportKind.CASE_NOTES: CASE_NOTES_CONTRACT,
}
