"""Offline presentation copy from synthetic aggregate changes only."""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from jvsg_triage.demo.models import DemoError, Profile
from jvsg_triage.demo.presentation import json_text, summary

MAX_BRIEFING_BYTES = 4096
TalkingPoint = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240),
]
Fingerprint = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class Briefing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, strict=True)

    version: Literal["aggregate-briefing-1"]
    review_status: Literal["draft", "reviewed"]
    facts_sha256: Fingerprint
    talking_points: tuple[TalkingPoint, TalkingPoint, TalkingPoint]


def briefing_facts(
    baseline: list[Profile], refreshed: list[Profile],
) -> dict[str, object]:
    def counts(profiles: list[Profile]) -> dict[str, object]:
        snapshot = summary(profiles)
        return {
            "participants": snapshot["participants"],
            "contact_bands": snapshot["alerts"],
            "awaiting_staff_review": snapshot["pending_review"],
        }

    old = {profile.demo_id: profile for profile in baseline}
    new = {profile.demo_id: profile for profile in refreshed}
    return {
        "synthetic_only": True,
        "as_of": refreshed[0].as_of.isoformat(),
        "contact_band_definitions": {
            "GREEN": "0-14 days", "YELLOW": "15-29 days", "RED": "30 or more days",
        },
        "baseline": counts(baseline),
        "refreshed": counts(refreshed),
        "records_added": len(new.keys() - old.keys()),
        "existing_records_updated": sum(old[key] != new[key] for key in old.keys() & new.keys()),
    }


def fingerprint(payload: object) -> str:
    return hashlib.sha256(json_text(payload).encode("utf-8")).hexdigest()


def draft_prompt(facts: dict[str, object]) -> dict[str, object]:
    return {
        "instruction": (
            "Return only a JSON object with the four keys shown in response_shape. "
            "Replace the three placeholders with short, plain-language management talking "
            "points drawn only from facts. Describe the snapshot comparison, not people or "
            "individual decisions. Contact bands use days since recorded contact, or "
            "assessment if no contact is recorded. Do not infer causes, service outcomes, "
            "or referrals. Each point must be at most 240 characters. Leave review_status "
            "as draft; only the human reviewer can mark the final wording reviewed."
        ),
        "facts": facts,
        "response_shape": {
            "version": "aggregate-briefing-1",
            "review_status": "draft",
            "facts_sha256": fingerprint(facts),
            "talking_points": ["point 1", "point 2", "point 3"],
        },
    }


def read_reviewed_briefing(path: Path, facts: dict[str, object]) -> Briefing:
    try:
        with path.open("rb") as stream:
            data = stream.read(MAX_BRIEFING_BYTES + 1)
        if len(data) > MAX_BRIEFING_BYTES:
            raise ValueError("briefing exceeds the demo size limit")
        # Reject ambiguous JSON before Pydantic's JSON-mode validation.
        json.loads(data, object_pairs_hook=_unique_keys)
        briefing = Briefing.model_validate_json(data)
    except (OSError, ValueError, RecursionError):
        raise DemoError("briefing: cannot read or validate the reviewed JSON file") from None
    if briefing.review_status != "reviewed":
        raise DemoError("briefing: draft must be reviewed before display")
    if briefing.facts_sha256 != fingerprint(facts):
        raise DemoError("briefing: source facts changed; regenerate and review the draft")
    return briefing


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result
