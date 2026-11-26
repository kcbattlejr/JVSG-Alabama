import csv
import importlib.util
import re
from datetime import date
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1] / "demo" / "naswa_demo"
spec = importlib.util.spec_from_file_location("build_demo_data", KIT / "build_demo_data.py")
assert spec and spec.loader
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def _required(query: str) -> list[str]:
    text = (KIT / "power-query" / query).read_text(encoding="utf-8")
    block = re.search(r"Required = \{(.*?)\}", text, re.S)
    assert block
    return re.findall(r'"([A-Z0-9_]+)"', block.group(1))


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("Demo")
    demo.write_tree(out, demo.DEFAULT_AS_OF, demo.DEFAULT_COUNT, demo.DEFAULT_SEED)
    return out


def test_layout_and_columns_match_queries(tree: Path) -> None:
    manager = _read(next((tree / "csv" / "manager").glob("21_FreeFormSql_*.csv")))
    worklist = _read(next((tree / "restricted" / "csv" / "worklist").glob("17_FreeFormSql_*.csv")))
    profile = _read(next((tree / "restricted" / "csv" / "profile").glob("29_FreeFormSql_*.csv")))
    for rows, query in (
        (manager, "Manager.pq"),
        (worklist, "Worklist.pq"),
        (profile, "Profile.pq"),
    ):
        assert set(_required(query)) <= set(rows[0])
    assert list(worklist[0]) == list(demo.WORKLIST_COLUMNS)
    assert list(manager[0]) == list(demo.MANAGER_COLUMNS)
    assert list(profile[0]) == list(demo.PROFILE_COLUMNS)


def test_local_queries_read_the_demo_folder() -> None:
    for name in ("Manager.pq", "Worklist.pq", "Profile.pq"):
        text = (KIT / "power-query" / name).read_text(encoding="utf-8")
        assert "Folder.Files(DemoFolder)" in text
        assert "SharePoint" not in text


def test_data_is_invented_and_mis_formatted(tree: Path) -> None:
    path = next((tree / "restricted" / "csv" / "worklist").glob("*.csv"))
    assert b"\r\n" in path.read_bytes()
    rows = _read(path)
    assert len(rows) == demo.DEFAULT_COUNT
    assert len({r["STATE_ID"] for r in rows}) == len(rows)
    for r in rows:
        assert r["INDIVIDUAL_USERNAME"].startswith("demo.")
        assert re.fullmatch(r"99\d{5}", r["STATE_ID"])
        assert r["OFFICE_NAME"].startswith("Demo Office")
        assert re.fullmatch(r"\d\d/\d\d/\d{4} \d{1,2}:\d\d:\d\d [AP]M", r["LAST_CONTACT_DATE"])
        assert r["FOLLOW_UP_BAND"] == demo.follow_up_band(int(r["DAYS_SINCE_CONTACT"]))


def test_manager_groups_are_suppressed_below_threshold(tree: Path) -> None:
    manager = _read(next((tree / "csv" / "manager").glob("*.csv")))
    worklist = _read(next((tree / "restricted" / "csv" / "worklist").glob("*.csv")))
    assert manager
    assert all(int(r["INDIVIDUALS"]) >= demo.SUPPRESSION_THRESHOLD for r in manager)
    assert sum(int(r["INDIVIDUALS"]) for r in manager) < len(worklist)


def test_generation_is_deterministic_and_shipped_files_are_current(tmp_path: Path) -> None:
    demo.write_tree(tmp_path, demo.DEFAULT_AS_OF, demo.DEFAULT_COUNT, demo.DEFAULT_SEED)
    for generated in tmp_path.rglob("*.csv"):
        shipped = KIT / "Demo" / generated.relative_to(tmp_path)
        assert shipped.read_bytes() == generated.read_bytes()


def test_other_as_of_dates_stay_inside_the_window(tmp_path: Path) -> None:
    as_of = date(2026, 12, 15)
    demo.write_tree(tmp_path, as_of, 40, 1)
    rows = _read(next(tmp_path.rglob("17_FreeFormSql_20261215.csv")))
    assert {r["AS_OF_DATE"] for r in rows} == {"12/15/2026"}
    assert all(
        0 <= int(r["DAYS_SINCE_CONTACT"]) <= (as_of - demo.DEFAULT_FY_START).days for r in rows
    )
