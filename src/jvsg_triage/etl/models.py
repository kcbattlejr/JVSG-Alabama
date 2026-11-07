"""Protected in-memory intake records and value-free reconciliation models."""

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from jvsg_triage.etl.contracts import ReportKind


class IntakeModel(BaseModel):
    """Forbid silent extra fields and hide input values in validation messages."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SourceLayout(IntakeModel):
    """Safe report coordinates, deliberately excluding filenames and titles."""

    report: ReportKind
    contract_version: str = "1.0"
    header_row: int
    column_count: int
    sheet_index: int | None = None


class Provenance(IntakeModel):
    """A row location within the caller's private input files."""

    report: ReportKind
    row_number: int
    sheet_index: int | None = None


class AntiJoinRecord(IntakeModel):
    """A row in the supplied MIS anti-join; no eligibility claims are inferred."""

    source: Provenance
    participant_token: str = Field(repr=False, exclude=True)


class CaseNoteRecord(IntakeModel):
    """Private evidence, not scrubbed text and never safe for an inference prompt."""

    source: Provenance
    participant_token: str = Field(repr=False, exclude=True)
    text: SecretStr = Field(repr=False, exclude=True)


class Reconciliation(IntakeModel):
    """Counts only; duplicates remain visible and no notes are silently collapsed."""

    anti_join_rows: int
    unique_participants: int
    repeated_participant_rows: int
    case_note_rows: int
    matched_note_rows: int
    unmatched_note_rows: int
    participants_with_notes: int
    participants_without_notes: int


class IntakeBatch(IntakeModel):
    """Private API result; standard serialization exposes only layouts and counts."""

    layouts: tuple[SourceLayout, SourceLayout]
    summary: Reconciliation
    cohort: tuple[AntiJoinRecord, ...] = Field(repr=False, exclude=True)
    matched_notes: tuple[CaseNoteRecord, ...] = Field(repr=False, exclude=True)
