"""Shared plain-language vocabulary for workbooks and the management dashboard."""

from datetime import date

from jvsg_triage.demo.models import Alert, Office, Profile, Review, State

DOMAIN_LABELS = {
    "TRN": "Transportation",
    "HSG": "Housing",
    "MED": "Health",
    "LEG": "Legal",
}
STATE_LABELS = {
    State.CRT: "Critical barrier",
    State.ACT: "Needs support",
    State.MIT: "Partly addressed",
    State.RES: "Resolved",
    State.UNK: "Not yet assessed",
}
STATE_MEANINGS = {
    State.CRT: "A serious barrier is recorded; qualified staff must assess the response.",
    State.ACT: "An ongoing barrier is recorded and still needs support.",
    State.MIT: "Some support is in place, but the barrier is not fully resolved.",
    State.RES: "The supplied record marks this barrier as resolved.",
    State.UNK: "There is not enough information to describe this barrier.",
}
ALERT_LABELS = {
    Alert.GREEN: "Recent contact",
    Alert.YELLOW: "Follow-up due",
    Alert.RED: "Extended gap in contact",
}
ALERT_MEANINGS = {
    Alert.GREEN: "0-14 days since contact",
    Alert.YELLOW: "15-29 days since contact",
    Alert.RED: "30 or more days since contact",
}
OFFICE_LABELS = {
    Office.NORTH: "North demonstration office",
    Office.CENTRAL: "Central demonstration office",
    Office.SOUTH: "South demonstration office",
}
REVIEW_LABELS = {
    Review.PENDING: "Awaiting staff review",
    Review.REVIEWED: "Staff review recorded",
}
FIELD_LABELS = {
    "demo_id": "Demonstration participant",
    "office": "Demonstration office",
    "assessment_date": "Assessment date",
    "last_contact_date": "Last recorded contact",
    **DOMAIN_LABELS,
    "review": "Staff review status",
    "as_of": "Report date",
    "idle_days": "Days since contact or assessment",
    "alert": "Follow-up status",
}
SOURCE_VALUE_CODES = {
    "office": {label: code.value for code, label in OFFICE_LABELS.items()},
    "review": {label: code.value for code, label in REVIEW_LABELS.items()},
    **{
        field: {label: code.value for code, label in STATE_LABELS.items()}
        for field in DOMAIN_LABELS
    },
}


def display_date(value: date | None) -> str:
    return f"{value:%b} {value.day}, {value.year}" if value else "No contact recorded"


def barrier_summary(profile: Profile) -> str:
    domains = ", ".join(
        label for field, label in DOMAIN_LABELS.items()
        if getattr(profile, field) == profile.priority
    )
    return f"{STATE_LABELS[profile.priority]}: {domains}"


def profile_values(profile: Profile) -> dict[str, object]:
    return {
        "demo_id": profile.demo_id,
        "office": OFFICE_LABELS[profile.office],
        "assessment_date": profile.assessment_date,
        "last_contact_date": profile.last_contact_date,
        **{field: STATE_LABELS[getattr(profile, field)] for field in DOMAIN_LABELS},
        "review": REVIEW_LABELS[profile.review],
        "as_of": profile.as_of,
        "idle_days": profile.idle_days,
        "alert": ALERT_LABELS[profile.alert],
    }
