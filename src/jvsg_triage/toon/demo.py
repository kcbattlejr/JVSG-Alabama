"""Lossless, closed-vocabulary @TOON demo dialect, not an approved federal contract."""

from pydantic import ValidationError

from jvsg_triage.demo.models import VERSION, DemoError, Profile

KEYS = (
    ("demo_id", "ID"), ("office", "OFF"), ("assessment_date", "CA"),
    ("last_contact_date", "TOUCH"), ("TRN", "TRN"), ("HSG", "HSG"),
    ("MED", "MED"), ("LEG", "LEG"), ("review", "REVIEW"), ("as_of", "ASOF"),
    ("idle_days", "IDLE"), ("alert", "ALERT"),
)


def encode(profile: Profile) -> str:
    values = profile.model_dump(mode="json")
    fields = [f"{key}:{'~' if values[field] is None else values[field]}" for field, key in KEYS]
    return f"@TOON|V:{VERSION}|" + "|".join(fields)


def decode(text: str) -> Profile:
    parts = text.split("|")
    if len(parts) != len(KEYS) + 2 or parts[:2] != ["@TOON", f"V:{VERSION}"]:
        raise DemoError("TOON: unsupported version or field count")
    values: dict[str, object] = {}
    for (field, key), part in zip(KEYS, parts[2:], strict=True):
        prefix = f"{key}:"
        if not part.startswith(prefix):
            raise DemoError("TOON: invalid field order")
        value = part[len(prefix):]
        values[field] = None if value == "~" else value
    try:
        profile = Profile.model_validate(values)
    except ValidationError:
        raise DemoError("TOON: invalid profile") from None
    if encode(profile) != text:
        raise DemoError("TOON: noncanonical encoding")
    return profile
