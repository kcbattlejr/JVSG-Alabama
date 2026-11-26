from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from jvsg_triage.dashboard_demo.generate import AS_OF, generate_candidates
from jvsg_triage.dashboard_demo.profile import (
    CLASSIFICATION_TOON_FIELDS,
    DOMAINS,
    PROFILE_COLUMNS,
    PROFILE_TOON_FIELDS,
    Profile,
    classify,
    generate_profiles,
    profile_csv_rows,
    toon_tables,
)
from jvsg_triage.toon.codec import ToonError, decode_table, encode_table

COMMITTED = Path(__file__).resolve().parents[1] / "data/synthetic/sharepoint_dashboard"
VOCAB = {"CRT", "ACT", "MIT", "RES", "UNK"}


def _blank() -> Profile:
    day = AS_OF - timedelta(days=30)
    return Profile("demo.p", "990000001", "Demo Office", day, day, day, "none", None,
                   False, False, False, None, False, False)  # fmt: skip


def _states(p: Profile) -> dict[str, tuple[str, str]]:
    return {c.domain: (c.state, c.rule_id) for c in classify(p)}


def test_codec_round_trip_and_quoting() -> None:
    fields = ("a", "b", "c")
    rows = [
        {"a": "x,y", "b": 'say "hi"\nnow', "c": None},
        {"a": "null", "b": "-3", "c": 7},
        {"a": "", "b": " pad ", "c": "plain"},
    ]
    text = encode_table(fields, rows)
    assert decode_table(text, fields) == rows
    assert encode_table(fields, []) == "[0]:\n" and decode_table("[0]:\n", fields) == []


@pytest.mark.parametrize(
    "text",
    ["[2]{a,b}:\n  x,y\n", "[1]{a,b}:\n  x\n", "[1]{a,b}:\nx,y\n", '[1]{a,b}:\n  "x,y\n'],
)
def test_codec_rejects_malformed(text: str) -> None:
    with pytest.raises(ToonError):
        decode_table(text, ("a", "b"))


def test_codec_rejects_unknown_fields() -> None:
    with pytest.raises(ToonError):
        encode_table(("a",), [{"a": "x", "b": "y"}])


def test_every_profile_gets_one_row_per_domain_in_closed_vocabulary() -> None:
    for p in generate_profiles(generate_candidates()):
        found = classify(p)
        assert [c.domain for c in found] == list(DOMAINS)
        assert {c.state for c in found} <= VOCAB


def test_rules() -> None:
    base = _blank()
    assert _states(base)["HSG"] == ("UNK", "HSG-0")
    assert _states(replace(base, housing_unstable=True))["HSG"] == ("ACT", "HSG-2")
    assert _states(replace(base, homeless=True, housing_unstable=True))["HSG"] == ("CRT", "HSG-1")
    assert _states(replace(base, disability=True))["MED"] == ("ACT", "MED-1")
    recent = AS_OF - timedelta(days=100)
    assert _states(replace(base, disability=True, last_medical_service=recent))["MED"] == (
        "MIT", "MED-2",
    )  # fmt: skip
    assert _states(replace(base, justice=True))["LEG"] == ("ACT", "LEG-1")
    assert _states(replace(base, last_employment_end=None))["TRN"] == ("ACT", "TRN-3")
    assert _states(replace(base, training_enrolled=True, last_employment_end=None))["TRN"] == (
        "MIT", "TRN-2",
    )  # fmt: skip
    done = replace(base, outcome_type="credential", outcome_date=recent)
    assert _states(done)["TRN"] == ("RES", "TRN-1")


def test_stale_evidence_and_partner_category_only_for_flagged_states() -> None:
    old = AS_OF - timedelta(days=400)
    _, classes = toon_tables([replace(_blank(), last_employment_end=old, justice=True)])
    rows = {r["domain"]: r for r in decode_table(classes, CLASSIFICATION_TOON_FIELDS)}
    assert rows["TRN"]["freshness"] == "stale" and rows["TRN"]["partner_category"]
    assert rows["LEG"]["freshness"] == "unknown" and rows["LEG"]["partner_category"]
    assert rows["MED"]["partner_category"] is None
    assert {r["verification_status"] for r in rows.values()} == {"Unverified"}


def test_toon_has_no_identifiers_and_round_trips() -> None:
    profiles = generate_profiles(generate_candidates())
    summary, classes = toon_tables(profiles)
    assert len(decode_table(summary, PROFILE_TOON_FIELDS)) == len(profiles)
    assert len(decode_table(classes, CLASSIFICATION_TOON_FIELDS)) == len(profiles) * 4
    for text in (summary, classes):
        assert "demo.person" not in text and "99000" not in text
    assert (summary, classes) == toon_tables(generate_profiles(generate_candidates()))


def test_profile_csv_columns() -> None:
    rows = profile_csv_rows(generate_profiles(generate_candidates()))
    assert tuple(rows[0]) == PROFILE_COLUMNS


def test_committed_profile_files_match_generator() -> None:
    profiles = generate_profiles(generate_candidates())
    summary, classes = toon_tables(profiles)
    assert (COMMITTED / "toon/profiles.toon").read_text(encoding="utf-8") == summary
    assert (COMMITTED / "toon/barrier_classifications.toon").read_text(encoding="utf-8") == classes
