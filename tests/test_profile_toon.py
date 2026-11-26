from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from jvsg_triage.dashboard_demo.generate import AS_OF, generate_candidates
from jvsg_triage.dashboard_demo.profile import (
    CLASSIFICATION_TOON_FIELDS,
    DOMAINS,
    PARTNER_CATEGORIES,
    PROFILE_COLUMNS,
    PROFILE_TOON_FIELDS,
    Profile,
    classify,
    freshness,
    generate_profiles,
    profile_csv_rows,
    toon_tables,
)
from jvsg_triage.toon.codec import ToonError, decode_table, encode_table

COMMITTED = Path(__file__).resolve().parents[1] / "data/synthetic/sharepoint_dashboard"
QUERIES = Path(__file__).resolve().parents[1] / "src/jvsg_triage/m365/sharepoint_demo/power-query"
CELLS = Path(__file__).resolve().parents[1] / "src/jvsg_triage/m365/excel_python"
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


def test_profile_power_query_requires_only_generated_columns() -> None:
    import re

    text = (QUERIES / "Profile.pq").read_text(encoding="utf-8")
    block = re.search(r"Required = \{(.*?)\}", text, re.S)
    assert block and set(re.findall(r'"([A-Z0-9_]+)"', block.group(1))) == set(PROFILE_COLUMNS)


def test_classification_power_query_matches_python_rule_ids() -> None:
    import re

    text = (QUERIES / "Classification.pq").read_text(encoding="utf-8")
    in_pq = set(re.findall(r'"((?:TRN|HSG|MED|LEG)-\d)"', text))
    p = _blank()
    in_py = {c.rule_id for c in classify(p)}
    for variant in (
        replace(p, homeless=True), replace(p, housing_unstable=True),
        replace(p, disability=True), replace(p, justice=True), replace(p, training_enrolled=True),
        replace(p, last_employment_end=None),
        replace(p, outcome_type="credential", outcome_date=AS_OF),
        replace(p, disability=True, last_medical_service=AS_OF),
    ):  # fmt: skip
        in_py |= {c.rule_id for c in classify(variant)}
    assert in_pq == in_py
    assert 'rules_version = "profile-rules-v1"' in text


def test_excel_python_cell_matches_committed_toon() -> None:
    pd = pytest.importorskip("pandas")
    scope: dict[str, Any] = {}
    for name in ("cell1_scrub", "cell2_rules", "cell3_toon", "cell4_profile_toon"):
        exec((CELLS / f"{name}.py").read_text(), scope)  # noqa: S102 - repo-owned cells
    profiles = generate_profiles(generate_candidates())
    class_rows = []
    for index, p in enumerate(profiles, start=1):
        for c in classify(p):
            flagged = c.state in ("CRT", "ACT")
            class_rows.append({
                "profile_id": f"P{index:04d}", "domain": c.domain, "state": c.state,
                "rule_id": c.rule_id, "evidence_field": c.evidence_field,
                "evidence_value": c.evidence_value,
                "evidence_as_of": pd.Timestamp(c.evidence_as_of) if c.evidence_as_of else pd.NaT,
                "freshness": freshness(c.evidence_as_of),
                "partner_category": PARTNER_CATEGORIES[c.domain] if flagged else None,
                "rules_version": "profile-rules-v1", "verification_status": "Unverified",
            })  # fmt: skip
    class_df = pd.DataFrame(class_rows)
    profile_df = pd.DataFrame([
        {"AS_OF_DATE": pd.Timestamp(AS_OF), "OFFICE_NAME": p.office_name,
         "DAYS_SINCE_CONTACT": p.days_since_contact,
         "CONTACT_INFO_UPDATED_DATE": (
             pd.Timestamp(p.contact_info_updated) if p.contact_info_updated else pd.NaT)}
        for p in profiles
    ])  # fmt: skip
    class_chunks, summary_chunks = scope["profile_toon"](profile_df, class_df)
    assert len(class_chunks) > 1 and all(len(c) <= 32767 for c in class_chunks)
    got = [r for chunk in class_chunks for r in decode_table(chunk, CLASSIFICATION_TOON_FIELDS)]
    got_summary = [r for chunk in summary_chunks for r in decode_table(chunk, PROFILE_TOON_FIELDS)]
    summary, classes = toon_tables(profiles)
    assert got == decode_table(classes, CLASSIFICATION_TOON_FIELDS)
    assert got_summary == decode_table(summary, PROFILE_TOON_FIELDS)


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "sql").is_dir(),
    reason="restricted SQL not present",
)
def test_profile_sql_aliases_match_profile_columns() -> None:
    import re

    text = (
        Path(__file__).resolve().parents[1] / "sql" / "29_fy2026_referral_profile.sql"
    ).read_text(encoding="utf-8")
    final = text[text.rindex("SELECT c.username") :]
    aliases = tuple(a.upper() for a in re.findall(r"AS \[(\w+)\]", final))
    assert aliases == PROFILE_COLUMNS
