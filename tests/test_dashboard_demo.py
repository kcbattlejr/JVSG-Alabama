import re
from pathlib import Path

import pytest
from openpyxl import load_workbook

from jvsg_triage.dashboard_demo.generate import (
    MANAGER_COLUMNS,
    SUPPRESSION_THRESHOLD,
    WORKLIST_COLUMNS,
    follow_up_band,
    generate_candidates,
    manager_rows,
    worklist_rows,
    write_sharepoint_tree,
)
from jvsg_triage.dashboard_demo.workbook import build_workbook

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "src/jvsg_triage/m365/sharepoint_demo/power-query"
COMMITTED = ROOT / "data/synthetic/sharepoint_dashboard"


def _required(query: str) -> list[str]:
    text = (QUERIES / query).read_text(encoding="utf-8")
    block = re.search(r"Required = \{(.*?)\}", text, re.S)
    assert block
    return re.findall(r'"([A-Z0-9_]+)"', block.group(1))


def test_bands_follow_15_and_30_day_cutoffs() -> None:
    assert [follow_up_band(d) for d in (0, 14, 15, 29, 30, 400)] == [
        "Current", "Current", "Due soon", "Due soon", "Overdue", "Overdue",
    ]  # fmt: skip


def test_generation_is_deterministic_and_invented() -> None:
    first, second = generate_candidates(), generate_candidates()
    assert first == second
    assert all(c.username.startswith("demo.") and c.state_id.startswith("99") for c in first)


def test_columns_satisfy_power_query_requirements() -> None:
    assert set(_required("Worklist.pq")) <= set(WORKLIST_COLUMNS)
    assert set(_required("Manager.pq")) <= set(MANAGER_COLUMNS)


def test_manager_report_suppresses_small_groups_like_step_21() -> None:
    candidates = generate_candidates()
    rows = manager_rows(candidates)
    assert rows and all(int(r["INDIVIDUALS"]) >= SUPPRESSION_THRESHOLD for r in rows)
    visible = {(r["INDIVIDUAL_RECORD_LWIA"], r["FOLLOW_UP_BAND"]) for r in rows}
    all_groups = {(c.lwia, c.band) for c in candidates}
    assert visible < all_groups, "default data should demonstrate suppression"
    assert sum(int(r["INDIVIDUALS"]) for r in rows) < len(candidates)


def test_no_visible_groups_result() -> None:
    rows = manager_rows(generate_candidates(count=5))
    assert [r["RESULT_STATUS"] for r in rows] == ["no_visible_groups"]
    assert rows[0]["INDIVIDUALS"] == ""


def test_committed_csvs_match_generator(tmp_path: Path) -> None:
    manager, worklist = write_sharepoint_tree(tmp_path, generate_candidates())
    assert (
        manager.read_bytes()
        == (COMMITTED / "csv/manager/synthetic_manager_report.csv").read_bytes()
    )
    assert (
        worklist.read_bytes()
        == (COMMITTED / "restricted/csv/worklist/synthetic_worklist_report.csv").read_bytes()
    )


def test_workbook_has_tables_and_suppression_formulas(tmp_path: Path) -> None:
    candidates = generate_candidates()
    path = build_workbook(manager_rows(candidates), worklist_rows(candidates), tmp_path / "d.xlsx")
    book = load_workbook(path)
    assert book.sheetnames == ["Overview", "Watchlist", "Manager_Data", "Worklist"]
    assert set(book["Manager_Data"].tables) == {"Manager"}
    assert set(book["Worklist"].tables) == {"Worklist"}
    assert "Suppressed" in str(book["Overview"]["B5"].value)
    assert book["Worklist"]["F2"].value.startswith("99")  # State ID stays text


@pytest.mark.skipif(not (ROOT / "sql").is_dir(), reason="restricted SQL not present")
def test_columns_match_restricted_sql_aliases() -> None:
    for sql_file, columns in (
        ("17_fy2026_wp_noncm_notes_watchlist.sql", WORKLIST_COLUMNS),
        ("21_fy2026_wp_noncm_notes_manager.sql", MANAGER_COLUMNS),
    ):
        text = (ROOT / "sql" / sql_file).read_text(encoding="utf-8")
        final = text[list(re.finditer(r"^SELECT", text, re.M))[-1].start() :]
        aliases = [a.upper() for a in re.findall(r"AS \[(\w+)\]", final)]
        assert set(aliases) == set(columns), sql_file
