"""Invented distributions for synthetic demonstration and testing.

Counts and shares are demonstration choices, not measurements of real reports.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyntheticProfile:
    """Distribution knobs for a fictional cohort with varied note formats."""

    cohort_participants: int = 50
    repeated_cohort_rows: int = 3
    # (low, high, share) bins for notes per cohort participant.
    cohort_note_bins: tuple[tuple[int, int, float], ...] = (
        (1, 3, 0.50), (4, 9, 0.25), (10, 19, 0.15), (20, 34, 0.10),
    )
    # Non-cohort participants keep the unmatched-note path exercised at small scale.
    other_participants: int = 100
    other_notes_range: tuple[int, int] = (1, 5)
    contact_types: tuple[tuple[str | None, float], ...] = (
        ("Other", 0.40), ("Telephone", 0.20), ("E-mail", 0.20),
        ("Face-to-Face", 0.10), (None, 0.10),
    )
    hiring_event_share: float = 0.20
    unedited_share: float = 0.15
    virtual_learning_share: float = 0.50
    exit_date_share: float = 0.50
    employment_date_share: float = 0.25
    caps_name_share: float = 0.15
    fiscal_year_start: tuple[int, int, int] = (2025, 10, 1)
    fiscal_year_end: tuple[int, int, int] = (2026, 9, 30)
    themes: tuple[str, ...] = field(
        default=("EMP", "MED", "TRAIN", "CONTACT", "LEG", "TRN", "HSG"),
    )


DEFAULT_PROFILE = SyntheticProfile()
