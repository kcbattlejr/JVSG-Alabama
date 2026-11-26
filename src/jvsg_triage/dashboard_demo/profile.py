"""Synthetic structured profiles, deterministic barrier classification and TOON export.

The classifier uses only structured fields in the profile (flags, dates, outcome
types). It never reads case notes. Every output row is an ``Unverified`` suggestion
for qualified staff review. "No indicator" means no structured evidence, not that
the barrier is absent, so it maps to ``UNK``.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from jvsg_triage.dashboard_demo.generate import AS_OF, Candidate
from jvsg_triage.toon.codec import Cell, encode_table

RULES_VERSION = "profile-rules-v1"
STALE_DAYS = 180
DOMAINS = ("TRN", "HSG", "MED", "LEG")
PARTNER_CATEGORIES = {
    "TRN": "Training and employment support",
    "HSG": "Housing assistance",
    "MED": "Health and VA benefits navigation",
    "LEG": "Legal aid",
}
PROFILE_COLUMNS = (
    "INDIVIDUAL_USERNAME", "STATE_ID", "AS_OF_DATE", "OFFICE_NAME", "LAST_CONTACT_DATE",
    "DAYS_SINCE_CONTACT", "CONTACT_INFO_UPDATED_DATE", "LAST_EMPLOYMENT_END_DATE",
    "LAST_OUTCOME_TYPE", "LAST_OUTCOME_DATE", "HOMELESS_FLAG", "HOUSING_UNSTABLE_FLAG",
    "DISABILITY_FLAG", "LAST_MEDICAL_SERVICE_DATE", "TRAINING_ENROLLED_FLAG",
    "JUSTICE_FLAG",
)  # fmt: skip
OUTCOME_TYPES = ("none", "placement", "credential", "training_completion")

PROFILE_TOON_FIELDS = (
    "profile_id", "office", "as_of", "days_since_contact", "contact_info_age_days",
    "contact_freshness", "domains_flagged",
)  # fmt: skip
CLASSIFICATION_TOON_FIELDS = (
    "profile_id", "domain", "state", "rule_id", "evidence_field", "evidence_value",
    "evidence_as_of", "freshness", "partner_category", "rules_version",
    "verification_status", "reviewer_action", "reviewer_role", "reviewed_on",
)  # fmt: skip


@dataclass(frozen=True)
class Profile:
    username: str
    state_id: str
    office_name: str
    last_contact: date
    contact_info_updated: date | None
    last_employment_end: date | None
    outcome_type: str
    outcome_date: date | None
    homeless: bool
    housing_unstable: bool
    disability: bool
    last_medical_service: date | None
    training_enrolled: bool
    justice: bool

    @property
    def days_since_contact(self) -> int:
        return (AS_OF - self.last_contact).days


@dataclass(frozen=True)
class Classification:
    domain: str
    state: str
    rule_id: str
    evidence_field: str
    evidence_value: str
    evidence_as_of: date | None


def generate_profiles(candidates: Sequence[Candidate], seed: int = 2026) -> list[Profile]:
    rng = random.Random(seed + 1)

    def back(max_days: int, chance: float = 1.0) -> date | None:
        return AS_OF - timedelta(days=rng.randint(0, max_days)) if rng.random() < chance else None

    profiles: list[Profile] = []
    for c in candidates:
        outcome = rng.choices(OUTCOME_TYPES, weights=(5, 2, 2, 2))[0]
        disability = rng.random() < 0.35
        profiles.append(
            Profile(
                username=c.username,
                state_id=c.state_id,
                office_name=c.office_name,
                last_contact=c.last_contact,
                contact_info_updated=back(600, 0.9),
                last_employment_end=back(900, 0.8),
                outcome_type=outcome,
                outcome_date=None if outcome == "none" else back(700),
                homeless=rng.random() < 0.12,
                housing_unstable=rng.random() < 0.2,
                disability=disability,
                last_medical_service=back(700, 0.6) if disability else None,
                training_enrolled=rng.random() < 0.1,
                justice=rng.random() < 0.15,
            )
        )
    return profiles


def _within(value: date | None, days: int) -> bool:
    return value is not None and 0 <= (AS_OF - value).days <= days


def classify(profile: Profile) -> list[Classification]:
    """Return one classification per domain; the first matching rule wins."""
    out: list[Classification] = []
    p = profile
    if p.homeless:
        out.append(Classification("HSG", "CRT", "HSG-1", "homeless_flag", "1", None))
    elif p.housing_unstable:
        out.append(Classification("HSG", "ACT", "HSG-2", "housing_unstable_flag", "1", None))
    else:
        out.append(Classification("HSG", "UNK", "HSG-0", "housing_flags", "none", None))

    if p.disability and _within(p.last_medical_service, 365):
        out.append(
            Classification(
                "MED",
                "MIT",
                "MED-2",
                "last_medical_service_date",
                _iso(p.last_medical_service),
                p.last_medical_service,
            )
        )
    elif p.disability:
        out.append(Classification("MED", "ACT", "MED-1", "disability_flag", "1", None))
    else:
        out.append(Classification("MED", "UNK", "MED-0", "disability_flag", "0", None))

    if p.outcome_type in ("credential", "training_completion") and _within(p.outcome_date, 365):
        out.append(
            Classification(
                "TRN", "RES", "TRN-1", "last_outcome_type", p.outcome_type, p.outcome_date
            )
        )
    elif p.training_enrolled:
        out.append(Classification("TRN", "MIT", "TRN-2", "training_enrolled_flag", "1", None))
    elif p.last_employment_end is None or (AS_OF - p.last_employment_end).days >= 180:
        out.append(
            Classification(
                "TRN",
                "ACT",
                "TRN-3",
                "last_employment_end_date",
                _iso(p.last_employment_end),
                p.last_employment_end,
            )
        )
    else:
        out.append(Classification("TRN", "UNK", "TRN-0", "last_employment_end_date",
                                  _iso(p.last_employment_end), p.last_employment_end))  # fmt: skip

    if p.justice:
        out.append(Classification("LEG", "ACT", "LEG-1", "justice_flag", "1", None))
    else:
        out.append(Classification("LEG", "UNK", "LEG-0", "justice_flag", "0", None))
    return sorted(out, key=lambda c: DOMAINS.index(c.domain))


def _iso_or_none(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _iso(value: date | None) -> str:
    return "unknown" if value is None else value.isoformat()


def freshness(as_of: date | None) -> str:
    """Flag evidence older than STALE_DAYS; undated flags have unknown freshness."""
    if as_of is None:
        return "unknown"
    return "stale" if (AS_OF - as_of).days > STALE_DAYS else "current"


def profile_id(index: int) -> str:
    """Row key for exports; the crosswalk to a veteran stays in the workbook."""
    return f"P{index:04d}"


def toon_tables(profiles: Sequence[Profile]) -> tuple[str, str]:
    """Return (profiles, barrier_classifications) TOON text. No names or State IDs."""
    summary: list[dict[str, Cell]] = []
    rows: list[dict[str, Cell]] = []
    for index, p in enumerate(profiles, start=1):
        pid = profile_id(index)
        found = classify(p)
        info_age = None if p.contact_info_updated is None else (AS_OF - p.contact_info_updated).days
        summary.append({
            "profile_id": pid,
            "office": p.office_name,
            "as_of": AS_OF.isoformat(),
            "days_since_contact": p.days_since_contact,
            "contact_info_age_days": info_age,
            "contact_freshness": freshness(p.contact_info_updated),
            "domains_flagged": sum(1 for f in found if f.state in ("CRT", "ACT")),
        })  # fmt: skip
        for f in found:
            flagged = f.state in ("CRT", "ACT")
            rows.append({
                "profile_id": pid,
                "domain": f.domain,
                "state": f.state,
                "rule_id": f.rule_id,
                "evidence_field": f.evidence_field,
                "evidence_value": f.evidence_value,
                "evidence_as_of": _iso_or_none(f.evidence_as_of),
                "freshness": freshness(f.evidence_as_of),
                "partner_category": PARTNER_CATEGORIES[f.domain] if flagged else None,
                "rules_version": RULES_VERSION,
                "verification_status": "Unverified",
                "reviewer_action": None,
                "reviewer_role": None,
                "reviewed_on": None,
            })  # fmt: skip
    return (
        encode_table(PROFILE_TOON_FIELDS, summary),
        encode_table(CLASSIFICATION_TOON_FIELDS, rows),
    )


def profile_csv_rows(profiles: Sequence[Profile]) -> list[dict[str, str]]:
    def us(v: date | None) -> str:
        return "" if v is None else v.strftime("%m/%d/%Y")

    return [
        {
            "INDIVIDUAL_USERNAME": p.username,
            "STATE_ID": p.state_id,
            "AS_OF_DATE": us(AS_OF),
            "OFFICE_NAME": p.office_name,
            "LAST_CONTACT_DATE": us(p.last_contact),
            "DAYS_SINCE_CONTACT": str(p.days_since_contact),
            "CONTACT_INFO_UPDATED_DATE": us(p.contact_info_updated),
            "LAST_EMPLOYMENT_END_DATE": us(p.last_employment_end),
            "LAST_OUTCOME_TYPE": p.outcome_type,
            "LAST_OUTCOME_DATE": us(p.outcome_date),
            "HOMELESS_FLAG": str(int(p.homeless)),
            "HOUSING_UNSTABLE_FLAG": str(int(p.housing_unstable)),
            "DISABILITY_FLAG": str(int(p.disability)),
            "LAST_MEDICAL_SERVICE_DATE": us(p.last_medical_service),
            "TRAINING_ENROLLED_FLAG": str(int(p.training_enrolled)),
            "JUSTICE_FLAG": str(int(p.justice)),
        }
        for p in profiles
    ]
