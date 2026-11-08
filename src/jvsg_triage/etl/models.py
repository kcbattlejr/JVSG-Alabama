"""Protected in-memory intake records and value-free reconciliation models.

Data tiers (docs/pii_protocol.md): T1 records here hold raw note text and are never
serialized; T2 RedactedNote holds scrubbed text for private local use only; T3
manifests hold aggregate counts only.
"""

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from jvsg_triage.etl.contracts import CONTRACT_VERSION, ReportKind


class IntakeModel(BaseModel):
    """Forbid silent extra fields and hide input values in validation messages."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class SourceLayout(IntakeModel):
    """Safe report coordinates, deliberately excluding filenames and titles."""

    report: ReportKind
    contract_version: str = CONTRACT_VERSION
    header_row: int
    column_count: int
    sheet_index: int | None = None


class Provenance(IntakeModel):
    """A row location within the caller's private input files."""

    report: ReportKind
    row_number: int
    sheet_index: int | None = None


class AntiJoinRecord(IntakeModel):
    """T1: one supplied anti-join row; membership only, no eligibility inferred."""

    source: Provenance
    participant_token: str = Field(repr=False, exclude=True)


class CaseNoteRecord(IntakeModel):
    """T1: raw note plus the row's own names for scrubbing; never send to inference."""

    source: Provenance
    participant_token: str = Field(repr=False, exclude=True)
    text: SecretStr = Field(repr=False, exclude=True)
    context_names: tuple[SecretStr, ...] = Field(default=(), repr=False, exclude=True)


class RedactionLexicon(IntakeModel):
    """T1: identities read transiently from lexicon columns; memory only."""

    person_names: frozenset[str] = Field(default=frozenset(), repr=False, exclude=True)
    staff_names: frozenset[str] = Field(default=frozenset(), repr=False, exclude=True)
    identifiers: frozenset[str] = Field(default=frozenset(), repr=False, exclude=True)


class Reconciliation(IntakeModel):
    """Counts only; duplicates remain visible and no notes are silently collapsed."""

    anti_join_rows: int
    unique_participants: int
    repeated_participant_rows: int
    case_note_rows: int
    declared_case_note_rows: int | None
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
    lexicon: RedactionLexicon = Field(repr=False, exclude=True)


class RedactedNote(IntakeModel):
    """T2: scrubbed note keyed by HMAC token. Pseudonymous, not anonymous."""

    participant_token: str
    source_row: int
    text: str = Field(repr=False)
    redactions: dict[str, int]


class ExtractionManifest(IntakeModel):
    """T3: aggregate-only record of an extraction run; safe to log locally."""

    contract_version: str
    protocol_version: str
    summary: Reconciliation
    redactions: dict[str, int]
    residual_findings: dict[str, int]
    notes_with_residual_findings: int
