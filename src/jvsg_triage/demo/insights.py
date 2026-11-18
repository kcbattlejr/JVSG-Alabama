"""Plain-count summaries shared by the HTML and Excel charts; counts only, no scoring."""

from collections.abc import Sequence

from jvsg_triage.demo.labels import (
    ALERT_LABELS,
    DOMAIN_LABELS,
    OFFICE_LABELS,
    REVIEW_LABELS,
    STATE_LABELS,
)
from jvsg_triage.demo.models import DOMAINS, Alert, Office, Profile, Review, State

NEEDS_SUPPORT = (State.CRT, State.ACT)
Row = tuple[str, list[int]]


def office_follow_up(profiles: Sequence[Profile]) -> list[Row]:
    return [
        (OFFICE_LABELS[office], [
            sum(p.office == office and p.alert == alert for p in profiles) for alert in Alert
        ])
        for office in Office if any(p.office == office for p in profiles)
    ]


def office_review(profiles: Sequence[Profile]) -> list[Row]:
    return [
        (OFFICE_LABELS[office], [
            sum(p.office == office and p.review == review for p in profiles) for review in Review
        ])
        for office in Office if any(p.office == office for p in profiles)
    ]


def support_by_area(profiles: Sequence[Profile]) -> list[Row]:
    return [
        (DOMAIN_LABELS[domain], [
            sum(getattr(p, domain) == state for p in profiles) for state in State
        ])
        for domain in DOMAINS
    ]


def areas_needing_support(profile: Profile) -> int:
    return sum(getattr(profile, domain) in NEEDS_SUPPORT for domain in DOMAINS)


def people_by_area_count(profiles: Sequence[Profile]) -> list[Row]:
    counts = [areas_needing_support(p) for p in profiles]
    return [
        ("No area marked" if number == 0 else f"{number} area{'s' if number > 1 else ''}",
         [counts.count(number)])
        for number in range(len(DOMAINS) + 1)
    ]


def review_first(profiles: Sequence[Profile]) -> list[Profile]:
    """Longest-waiting people with a critical barrier; a sorting aid, not a decision."""
    return sorted(
        (p for p in profiles if p.alert == Alert.RED and p.priority == State.CRT),
        key=lambda p: (-p.idle_days, p.demo_id),
    )


def most_common_areas(profiles: Sequence[Profile]) -> tuple[list[str], int]:
    counts = {
        DOMAIN_LABELS[domain]: sum(getattr(p, domain) in NEEDS_SUPPORT for p in profiles)
        for domain in DOMAINS
    }
    top = max(counts.values())
    return [label for label, count in counts.items() if count == top], top


ALERT_SERIES = [ALERT_LABELS[alert] for alert in Alert]
REVIEW_SERIES = [REVIEW_LABELS[review] for review in Review]
STATE_SERIES = [STATE_LABELS[state] for state in State]
