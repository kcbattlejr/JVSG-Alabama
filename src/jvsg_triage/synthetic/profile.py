"""Rounded, aggregate-only shape of the FY2026 downloads used to drive synthesis.

Every number here is a rounded count or share from a local profile of the real
reports. No record value, name, ID, date or text fragment is carried over.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyntheticProfile:
    """Distribution knobs; defaults mirror the FY2026 profile at reduced volume."""

    cohort_participants: int = 64
    repeated_cohort_rows: int = 2
    # (low, high, share) bins for notes per cohort participant.
    cohort_note_bins: tuple[tuple[int, int, float], ...] = (
        (1, 3, 0.64), (4, 9, 0.14), (10, 19, 0.08), (20, 34, 0.14),
    )
    # Non-cohort participants keep the unmatched-note path exercised at small scale.
    other_participants: int = 140
    other_notes_range: tuple[int, int] = (1, 5)
    contact_types: tuple[tuple[str | None, float], ...] = (
        ("Other", 0.66), ("Telephone", 0.12), ("E-mail", 0.085),
        ("Face-to-Face", 0.06), (None, 0.075),
    )
    hiring_event_share: float = 0.14
    unedited_share: float = 0.10
    virtual_learning_share: float = 0.76
    exit_date_share: float = 0.60
    employment_date_share: float = 0.27
    caps_name_share: float = 0.10
    fiscal_year_start: tuple[int, int, int] = (2025, 10, 1)
    fiscal_year_end: tuple[int, int, int] = (2026, 9, 30)
    themes: tuple[str, ...] = field(
        default=("EMP", "MED", "TRAIN", "CONTACT", "LEG", "TRN", "HSG"),
    )


DEFAULT_PROFILE = SyntheticProfile()
