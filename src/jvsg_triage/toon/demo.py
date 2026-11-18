<<<<<<< HEAD
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
=======
"""Standard TOON tabular arrays for the closed synthetic profile schema."""

from collections.abc import Sequence

from pydantic import ValidationError

from jvsg_triage.demo.models import DOMAINS, DemoError, Profile

FIELDS = (
    "demo_id", "office", "assessment_date", "last_contact_date", *DOMAINS,
    "review", "as_of", "idle_days", "alert",
)


def _header(count: int) -> str:
    return f"[{count}]{{{','.join(FIELDS)}}}:" if count else "[0]:"


def encode(profiles: Sequence[Profile]) -> str:
    rows = [_header(len(profiles))]
    for profile in profiles:
        values = profile.model_dump(mode="json")
        # Profile strings are fixed enums, synthetic IDs or ISO dates, all safe bare tokens.
        rows.append("  " + ",".join(
            "null" if values[field] is None else str(values[field]) for field in FIELDS
        ))
    return "\n".join(rows) + "\n"


def decode(text: str) -> list[Profile]:
    """Read the exact tabular form this exporter writes; not a general TOON parser."""
    lines = text.splitlines()
    if not lines or lines[0] != _header(len(lines) - 1):
        raise DemoError("TOON: invalid profile table header or row count")
    profiles = []
    try:
        for line in lines[1:]:
            cells = line.removeprefix("  ").split(",")
            if not line.startswith("  ") or len(cells) != len(FIELDS):
                raise DemoError("TOON: invalid profile row")
            profiles.append(Profile.model_validate({
                field: None if value == "null" else value
                for field, value in zip(FIELDS, cells, strict=True)
            }))
    except ValidationError:
        raise DemoError("TOON: invalid profile") from None
    if encode(profiles) != text:
        raise DemoError("TOON: noncanonical encoding")
    return profiles
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
