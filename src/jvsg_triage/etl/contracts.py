"""Versioned, header-only contracts for native MIS report downloads.

Every source column carries a PII class and a handling rule. The contract stores
layout and classification only, never example record values.
"""

import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

CONTRACT_VERSION = "1.1"


class ReportKind(StrEnum):
    """Supported downloads, not independently verified service populations."""

    ANTI_JOIN = "anti_join"
    CASE_NOTES = "case_notes"


class PiiClass(StrEnum):
    """Protocol classification; see docs/pii_protocol.md."""

    DIRECT_IDENTIFIER = "direct_identifier"
    PARTICIPANT_IDENTIFIER = "participant_identifier"
    STAFF_IDENTIFIER = "staff_identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    SENSITIVE_ATTRIBUTE = "sensitive_attribute"
    FREE_TEXT = "free_text"
    OPERATIONAL = "operational"
    REPORT_LABEL = "report_label"
    BLANK = "blank"


Handling = Literal["projected", "lexicon", "discarded", "blank"]
"""projected: kept in the protected model; lexicon: read transiently to build the
redaction dictionary, never retained; discarded: never read beyond validation."""


class ColumnContract(BaseModel):
    """Describe a source position without storing example record values."""

    model_config = ConfigDict(frozen=True)

    position: int
    header: str | None
    pii_class: PiiClass
    handling: Handling
    target: str | None = None
    description: str | None = None


class ReportContract(BaseModel):
    """Exact ordered layout; header discovery tolerates preceding title rows."""

    model_config = ConfigDict(frozen=True)

    version: str = CONTRACT_VERSION
    kind: ReportKind
    format: Literal["csv", "xlsx"]
    observed_header_row: int
    footer: Literal["none", "repeated_header_total_rows"]
    columns: tuple[ColumnContract, ...]
    anchors: tuple[str, ...]


def normalize_header(value: object) -> str:
    """Ignore BOM, line wrapping, spacing and case, but not field identity."""
    return re.sub(r"\s+", "", str(value or "").strip().lstrip("\ufeff")).casefold()


_P = PiiClass
_DATE_LABEL = "SSRS date; label supplied by {}"

# (header, pii_class, handling, target, description)
_ANTI_JOIN_SPEC: tuple[tuple[str, PiiClass, Handling, str | None, str | None], ...] = (
    ("programdesc3", _P.OPERATIONAL, "discarded", None, "Program description"),
    ("Username", _P.PARTICIPANT_IDENTIFIER, "lexicon", "identifier",
     "Participant MIS account number"),
    ("StateID", _P.PARTICIPANT_IDENTIFIER, "projected", "participant_id",
     "State ID (SID); sole join key, HMAC-tokenized on read"),
    ("Textbox72", _P.REPORT_LABEL, "discarded", None, "Unused SSRS textbox"),
    ("Region", _P.OPERATIONAL, "discarded", None, "Workforce region"),
    ("Office", _P.OPERATIONAL, "discarded", None, "Career center"),
    ("OfficeResponsible", _P.OPERATIONAL, "discarded", None, None),
    ("FirstName", _P.DIRECT_IDENTIFIER, "lexicon", "person_name", None),
    ("LastName", _P.DIRECT_IDENTIFIER, "lexicon", "person_name", None),
    ("SSN", _P.DIRECT_IDENTIFIER, "discarded", None, "Blank in observed download"),
    ("CityStateCountry", _P.QUASI_IDENTIFIER, "discarded", None, "Masked by MIS"),
    ("primephone", _P.DIRECT_IDENTIFIER, "discarded", None, "Masked by MIS"),
    ("email", _P.DIRECT_IDENTIFIER, "discarded", None, "Masked by MIS"),
    ("employmentdate", _P.QUASI_IDENTIFIER, "discarded", None, None),
    ("Service", _P.OPERATIONAL, "discarded", None, "Service code and description"),
    ("Naics", _P.OPERATIONAL, "discarded", None, None),
    ("onetcode", _P.OPERATIONAL, "discarded", None, None),
    ("CompletionStatus", _P.OPERATIONAL, "discarded", None, None),
    ("programserv", _P.OPERATIONAL, "discarded", None, None),
    ("Provider", _P.OPERATIONAL, "discarded", None, None),
    ("StaffCreated", _P.STAFF_IDENTIFIER, "lexicon", "staff_name", None),
    ("Date1", _P.QUASI_IDENTIFIER, "discarded", None, _DATE_LABEL.format("textbox81")),
    ("Date2", _P.QUASI_IDENTIFIER, "discarded", None, _DATE_LABEL.format("textbox82")),
    ("Date3", _P.QUASI_IDENTIFIER, "discarded", None, _DATE_LABEL.format("textbox83")),
    ("Date4", _P.QUASI_IDENTIFIER, "discarded", None, _DATE_LABEL.format("textbox84")),
    ("Date5", _P.QUASI_IDENTIFIER, "discarded", None, _DATE_LABEL.format("textbox85")),
    ("col_exitdate", _P.QUASI_IDENTIFIER, "discarded", None, "Program exit date"),
    ("EditStaff", _P.STAFF_IDENTIFIER, "lexicon", "staff_name", None),
    ("DSSClientID", _P.DIRECT_IDENTIFIER, "discarded", None, None),
    ("EDGStatus", _P.OPERATIONAL, "discarded", None, None),
    ("TimeLimitedStatus", _P.OPERATIONAL, "discarded", None, None),
    ("AppID", _P.PARTICIPANT_IDENTIFIER, "lexicon", "identifier", "Application ID"),
    ("CaseManager", _P.STAFF_IDENTIFIER, "lexicon", "staff_name", None),
    ("registeredapprenticeship", _P.OPERATIONAL, "discarded", None, None),
    ("apprenticeshiptype", _P.OPERATIONAL, "discarded", None, None),
    ("Hispanic", _P.SENSITIVE_ATTRIBUTE, "discarded", None, "Ethnicity"),
    ("learningmode", _P.OPERATIONAL, "discarded", None, None),
    ("agencycode", _P.OPERATIONAL, "discarded", None, None),
    ("col_offender", _P.SENSITIVE_ATTRIBUTE, "discarded", None, "Justice involvement"),
    ("comments", _P.FREE_TEXT, "discarded", None, "Blank in observed download"),
    ("itapaying", _P.OPERATIONAL, "discarded", None, None),
    ("textbox81", _P.REPORT_LABEL, "discarded", None, "Label for Date1: Create Date"),
    ("textbox82", _P.REPORT_LABEL, "discarded", None, "Label for Date2: Actual Date"),
    ("textbox83", _P.REPORT_LABEL, "discarded", None, "Label for Date3: Edit Date"),
    ("textbox84", _P.REPORT_LABEL, "discarded", None, "Label for Date4: Scheduled Date"),
    ("textbox85", _P.REPORT_LABEL, "discarded", None, "Label for Date5: Application Date"),
)

_CASE_NOTES_SPEC: tuple[tuple[str | None, PiiClass, Handling, str | None, str | None], ...] = (
    ("Userid", _P.PARTICIPANT_IDENTIFIER, "lexicon", "identifier",
     "Participant MIS account number"),
    (None, _P.BLANK, "blank", None, "Unlabeled column; must stay empty"),
    ("Individual", _P.DIRECT_IDENTIFIER, "lexicon", "person_name", "Participant name"),
    ("Created By", _P.STAFF_IDENTIFIER, "lexicon", "staff_name", None),
    ("Create\nDate", _P.QUASI_IDENTIFIER, "discarded", None, None),
    ("Contact\nDate", _P.QUASI_IDENTIFIER, "discarded", None, None),
    ("Contact\nType", _P.OPERATIONAL, "discarded", None, None),
    ("Last\nEdited By", _P.STAFF_IDENTIFIER, "lexicon", "staff_name", None),
    ("Last Edit Date", _P.QUASI_IDENTIFIER, "discarded", None, None),
    ("State\nID", _P.PARTICIPANT_IDENTIFIER, "projected", "participant_id",
     "State ID (SID); sole join key, HMAC-tokenized on read"),
    ("Case\nSubject", _P.FREE_TEXT, "discarded", None, "Free-text subject"),
    ("Case Notes", _P.FREE_TEXT, "projected", "text", "Unstructured note; scrubbed"),
)


def _columns(
    spec: tuple[tuple[str | None, PiiClass, Handling, str | None, str | None], ...],
) -> tuple[ColumnContract, ...]:
    return tuple(
        ColumnContract(
            position=index, header=header, pii_class=pii_class, handling=handling,
            target=target, description=description,
        )
        for index, (header, pii_class, handling, target, description) in enumerate(spec, 1)
    )


ANTI_JOIN_HEADERS: tuple[str, ...] = tuple(str(row[0]) for row in _ANTI_JOIN_SPEC)
CASE_NOTE_HEADERS: tuple[str | None, ...] = tuple(row[0] for row in _CASE_NOTES_SPEC)

ANTI_JOIN_CONTRACT = ReportContract(
    kind=ReportKind.ANTI_JOIN,
    format="csv",
    observed_header_row=1,
    footer="none",
    columns=_columns(_ANTI_JOIN_SPEC),
    anchors=("stateid", "service", "officeresponsible"),
)

CASE_NOTES_CONTRACT = ReportContract(
    kind=ReportKind.CASE_NOTES,
    format="xlsx",
    observed_header_row=4,
    footer="repeated_header_total_rows",
    columns=_columns(_CASE_NOTES_SPEC),
    anchors=("stateid", "casesubject", "casenotes"),
)

CONTRACTS = {
    ReportKind.ANTI_JOIN: ANTI_JOIN_CONTRACT,
    ReportKind.CASE_NOTES: CASE_NOTES_CONTRACT,
}

FOOTER_TOTAL = re.compile(r"Total Rows:\s*([\d,]+)")
