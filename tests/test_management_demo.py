"""Entirely invented workbook data; no network, credentials or private inputs."""

import json
from datetime import timedelta
from pathlib import Path
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook

from jvsg_triage.demo.__main__ import main
from jvsg_triage.demo.intake import (
    MAX_BYTES,
    fixture_records,
    read_source,
    source_workbook,
    transform,
)
from jvsg_triage.demo.models import (
    AS_OF,
    Alert,
    DemoError,
    Profile,
    SourceRecord,
    State,
)
from jvsg_triage.demo.pipeline import (
    ARTIFACTS,
    digest,
    prepare,
    rehearse,
    run_pipeline,
    verify_batch,
)
from jvsg_triage.demo.presentation import excel_dashboard, save_workbook, summary
from jvsg_triage.toon.demo import decode, encode


def modified_source(tmp_path: Path, cell: str, value: object) -> bytes:
    workbook = source_workbook(fixture_records())
    workbook["Demo Intake"][cell] = value
    path = tmp_path / "synthetic.xlsx"
    save_workbook(workbook, path)
    return path.read_bytes()


@pytest.mark.parametrize(
    ("days", "expected"), [(0, Alert.GREEN), (14, Alert.GREEN), (15, Alert.YELLOW),
                           (29, Alert.YELLOW), (30, Alert.RED), (45, Alert.RED)],
)
def test_exact_aging_boundaries(days: int, expected: Alert) -> None:
    values = fixture_records()[0].model_dump()
    values["last_contact_date"] = AS_OF - timedelta(days=days)
    profile = transform([SourceRecord.model_validate(values)], AS_OF)[0]
    assert (profile.idle_days, profile.alert) == (days, expected)


def test_missing_contact_uses_assessment_and_future_dates_fail() -> None:
    values = fixture_records()[0].model_dump()
    values.update(last_contact_date=None, assessment_date=AS_OF - timedelta(days=15))
    assert transform([SourceRecord.model_validate(values)], AS_OF)[0].idle_days == 15
    values["assessment_date"] = AS_OF + timedelta(days=1)
    with pytest.raises(DemoError, match="future"):
        transform([SourceRecord.model_validate(values)], AS_OF)


@pytest.mark.parametrize(
    ("cell", "value"),
    [
        ("A1", "SYNTHETIC_REJECTED_SENTINEL"),
        ("A2", "SYNTHETIC_REJECTED_SENTINEL"),
        ("A3", "SYNTHETIC_REJECTED_SENTINEL"),
        ("A4", "DEMO-0001"),
        ("B3", "SYNTHETIC_REJECTED_SENTINEL"),
        ("C3", "11/20/2026"), ("D3", 45_000),
        ("C3", "2026-W47-5"),
        ("E3", '=HYPERLINK("https://example.invalid","synthetic")'),
        ("F3", "NOT_A_STATE"), ("I3", "AI_Approved"), ("J3", "extra"),
        ("D3", "2026-01-01"),
    ],
)
def test_closed_intake_rejects_bad_cells_without_echo(
    tmp_path: Path, cell: str, value: object,
) -> None:
    with pytest.raises(DemoError) as error:
        read_source(modified_source(tmp_path, cell, value))
    assert "SYNTHETIC_REJECTED_SENTINEL" not in str(error.value)
    assert "https://" not in str(error.value)


def test_intake_handles_native_excel_dates_and_rejects_time(tmp_path: Path) -> None:
    from datetime import datetime

    content = modified_source(tmp_path, "D3", datetime(2026, 11, 20))
    assert read_source(content)[0].last_contact_date == AS_OF
    with pytest.raises(DemoError, match="date-only"):
        read_source(modified_source(tmp_path, "D3", datetime(2026, 11, 20, 12)))


def test_intake_rejects_empty_other_sheets_and_corrupt_files(tmp_path: Path) -> None:
    for data in (b"not an xlsx", b"x" * (MAX_BYTES + 1)):
        with pytest.raises(DemoError):
            read_source(data)
    workbook = source_workbook([])
    path = tmp_path / "empty.xlsx"
    save_workbook(workbook, path)
    with pytest.raises(DemoError, match="empty"):
        read_source(path.read_bytes())
    workbook = source_workbook(fixture_records())
    workbook.create_sheet("Unexpected")
    save_workbook(workbook, path)
    with pytest.raises(DemoError, match="only"):
        read_source(path.read_bytes())


def test_unknown_is_not_treated_as_resolved() -> None:
    values = fixture_records()[0].model_dump()
    values.update(TRN=State.RES, HSG=State.RES, MED=State.UNK, LEG=State.RES)
    assert SourceRecord.model_validate(values).priority == State.UNK


def test_all_profiles_round_trip_losslessly_including_nulls() -> None:
    profiles = transform(fixture_records(refreshed=True), AS_OF)
    values = profiles[0].model_dump()
    values.update(last_contact_date=None, idle_days=70, alert=Alert.RED)
    profiles.append(Profile.model_validate(values))
    for profile in profiles:
        assert decode(encode(profile)) == profile


@pytest.mark.parametrize("mutation", ["version", "extra", "order", "leading-zero", "inconsistent"])
def test_toon_rejects_malformed_or_noncanonical_profiles(mutation: str) -> None:
    text = encode(transform(fixture_records(), AS_OF)[0])
    if mutation == "version":
        text = text.replace("V:demo-1", "V:unapproved")
    elif mutation == "extra":
        text += "|EXTRA:1"
    elif mutation == "order":
        text = text.replace("ID:DEMO-0001", "OFF:DEMO-0001")
    elif mutation == "leading-zero":
        text = text.replace("IDLE:0", "IDLE:00")
    else:
        text = text.replace("ALERT:GREEN", "ALERT:RED")
    with pytest.raises(DemoError):
        decode(text)


def test_rehearsal_refresh_reconciliation_and_exact_reproducibility(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = rehearse(first_root)
    second = rehearse(second_root)
    assert first == second
    assert first["added_demo_ids"] == ["DEMO-0019"]
    assert first["updated_demo_ids"] == ["DEMO-0005"]
    assert first["source_review_values_preserved"] is True
    first_files = {
        str(path.relative_to(first_root)): path.read_bytes()
        for path in first_root.rglob("*") if path.is_file()
    }
    second_files = {
        str(path.relative_to(second_root)): path.read_bytes()
        for path in second_root.rglob("*") if path.is_file()
    }
    assert first_files == second_files
    assert rehearse(first_root) == first
    latest = json.loads((first_root / "latest.json").read_text())
    manifest = verify_batch(first_root / latest["path"])
    assert manifest.records == 19
    baseline_summary = summary(transform(fixture_records(), AS_OF))
    assert baseline_summary["alerts"] == {"GREEN": 6, "YELLOW": 6, "RED": 6}
    refreshed_summary = summary(transform(fixture_records(refreshed=True), AS_OF))
    assert refreshed_summary["alerts"] == {"GREEN": 8, "YELLOW": 6, "RED": 5}


@pytest.mark.parametrize("artifact", sorted(ARTIFACTS))
def test_tampering_is_detected(tmp_path: Path, artifact: str) -> None:
    source = prepare(tmp_path / "intake")["baseline"]
    batch = run_pipeline(source, as_of=AS_OF, output=tmp_path / "out")
    (batch / artifact).write_bytes(b"synthetic tampering")
    with pytest.raises(DemoError, match="integrity"):
        verify_batch(batch)


def test_manifest_cannot_relabel_source_profiles(tmp_path: Path) -> None:
    source = prepare(tmp_path / "intake")["baseline"]
    batch = run_pipeline(source, as_of=AS_OF, output=tmp_path / "out")
    altered = batch / "profiles.json"
    altered.write_text("[]\n")
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["sha256"]["profiles.json"] = digest(altered.read_bytes())
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(DemoError, match="differ from source"):
        verify_batch(batch)


def test_failed_refresh_preserves_last_good_batch_and_marks_failure(tmp_path: Path) -> None:
    source = prepare(tmp_path / "intake")["baseline"]
    root = tmp_path / "out"
    batch = run_pipeline(source, as_of=AS_OF, output=root)
    before = (root / "latest.json").read_bytes()
    source.write_bytes(b"invalid synthetic workbook")
    with pytest.raises(DemoError, match="unreadable"):
        run_pipeline(source, as_of=AS_OF, output=root)
    assert (root / "latest.json").read_bytes() == before
    assert json.loads((root / "status.json").read_bytes())["state"] == "failed"
    assert verify_batch(batch).records == 18
    assert not list((root / "batches").glob(".staging-*"))


def test_failed_first_refresh_does_not_publish_success(tmp_path: Path) -> None:
    with pytest.raises(DemoError, match="cannot read"):
        run_pipeline(tmp_path / "missing.xlsx", as_of=AS_OF, output=tmp_path / "out")
    assert not (tmp_path / "out" / "latest.json").exists()
    status = json.loads((tmp_path / "out" / "status.json").read_bytes())
    assert status["last_success_preserved"] is False


def test_tracked_output_destination_is_rejected() -> None:
    with pytest.raises(DemoError, match="output must"):
        prepare(Path(__file__).resolve().parents[1] / "docs" / "forbidden-demo-output")


def test_excel_and_html_are_real_snapshots_with_matching_data(tmp_path: Path) -> None:
    sources = prepare(tmp_path / "intake")
    batch = run_pipeline(sources["baseline"], as_of=AS_OF, output=tmp_path / "out")
    workbook = load_workbook(batch / "dashboard.xlsx", data_only=True)
    assert workbook.sheetnames == [
        "Dashboard", "Watchlist", "TOON", "Definitions", "Provenance",
    ]
    assert workbook["Dashboard"]["B4"].value == 18
    rows = list(workbook["Watchlist"].iter_rows(min_row=2, values_only=True))
    assert len(rows) == 18
    assert rows[4][10:12] == (30, "Extended gap in contact")
    assert rows[1][8] == "Staff review recorded"
    assert workbook["TOON"]["B2"].value == encode(transform(fixture_records(), AS_OF)[0])
    workbook.close()
    with ZipFile(batch / "dashboard.xlsx") as archive:
        assert len([name for name in archive.namelist() if name.startswith("xl/charts/chart")]) == 2
        assert not any("externalLinks" in name for name in archive.namelist())
    html = (batch / "dashboard.html").read_text()
    assert 'id="count-RED">6' in html
    assert "No live connection" in html
    assert "<tr data-office=" in html
    assert "https://" not in html


def test_management_surfaces_use_plain_language_and_hide_technical_details(tmp_path: Path) -> None:
    from html.parser import HTMLParser

    class VisibleText(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.depth = 0
            self.text: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag in ("script", "style", "details"):
                self.depth += 1

        def handle_endtag(self, tag: str) -> None:
            if tag in ("script", "style", "details"):
                self.depth -= 1

        def handle_data(self, data: str) -> None:
            if self.depth == 0:
                self.text.append(data)

    source = prepare(tmp_path / "intake")["baseline"]
    batch = run_pipeline(source, as_of=AS_OF, output=tmp_path / "out")
    parser = VisibleText()
    parser.feed((batch / "dashboard.html").read_text())
    visible = " ".join(parser.text)
    for label in (
        "Recent contact", "Follow-up due", "Extended gap in contact",
        "Transportation", "Housing", "Health", "Legal", "Critical barrier",
        "Needs support", "Partly addressed", "Resolved", "Not yet assessed",
        "Awaiting staff review", "Nov 20, 2026",
    ):
        assert label in visible
    for abbreviation in (
        "TRN", "HSG", "MED", "LEG", "CRT", "ACT", "MIT", "RES", "UNK",
        "GREEN", "YELLOW", "RED", "ETL", "SHA-256", "idle_days",
    ):
        assert abbreviation not in visible.split()
    workbook = load_workbook(batch / "dashboard.xlsx")
    for name in ("TOON", "Provenance"):
        assert workbook[name].sheet_state == "hidden"
    headers = [cell.value for cell in workbook["Watchlist"][1]]
    assert headers[4:9] == [
        "Transportation", "Housing", "Health", "Legal", "Staff review status",
    ]
    assert workbook["Watchlist"]["F6"].value == "Critical barrier"
    assert workbook["Watchlist"]["M6"].value == "Critical barrier: Housing"
    workbook.close()
    workbook = load_workbook(source)
    assert workbook["Demo Intake"]["E2"].value == "Transportation"
    assert workbook["Demo Intake"]["F7"].value == "Critical barrier"
    assert workbook["Demo Intake"]["I3"].value == "Awaiting staff review"
    workbook.close()


def test_demo_file_links_are_visible_and_resolve_to_generated_files(tmp_path: Path) -> None:
    from html.parser import HTMLParser

    class FileLinks(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.downloads: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attributes = dict(attrs)
            if tag == "a" and "download" in attributes:
                href = attributes.get("href")
                assert href is not None
                self.downloads.append(href)

    root = tmp_path / "demo"
    result = rehearse(root)
    pages = [root / "index.html"]
    for key in ("baseline", "refreshed"):
        entry = result[key]
        assert isinstance(entry, dict)
        pages.append(root / entry["path"] / "dashboard.html")
    for page in pages:
        html = page.read_text()
        assert html.index("Demo files - open or download here") < html.index(
            "What changed" if page.name == "index.html" else "How long since"
        )
        parser = FileLinks()
        parser.feed(html)
        assert len(parser.downloads) >= 3
        assert {Path(link).name for link in parser.downloads} >= {
            "dashboard.xlsx", "source.xlsx", "profiles.toon",
        }
        for link in parser.downloads:
            assert (page.parent / link).is_file()
        assert "temp/management-demo/" in html
        assert "Downloads list" in html


def test_legacy_source_codes_remain_supported(tmp_path: Path) -> None:
    from jvsg_triage.demo.models import HEADERS

    workbook = source_workbook(fixture_records())
    sheet = workbook["Demo Intake"]
    for column, field in enumerate(HEADERS, start=1):
        sheet.cell(2, column, field)
    for number, record in enumerate(fixture_records(), start=3):
        for column, value in enumerate(record.model_dump(mode="json").values(), start=1):
            sheet.cell(number, column, value)
    path = tmp_path / "legacy.xlsx"
    save_workbook(workbook, path)
    assert read_source(path.read_bytes()) == fixture_records()


def test_xlsx_bytes_stable_across_wall_clock_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import openpyxl.writer.excel

    before = tmp_path / "before.xlsx"
    after = tmp_path / "after.xlsx"
    profiles = transform(fixture_records(), AS_OF)
    save_workbook(excel_dashboard(profiles, "synthetic"), before)

    from datetime import datetime, timezone
    from types import SimpleNamespace

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2030, 3, 5, 12)

    monkeypatch.setattr(
        openpyxl.writer.excel, "datetime", SimpleNamespace(datetime=Later, timezone=timezone),
    )
    save_workbook(excel_dashboard(profiles, "synthetic"), after)
    assert before.read_bytes() == after.read_bytes()


def test_cli_runs_rehearsal_and_sanitizes_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    import sys

    monkeypatch.setattr(sys, "argv", ["demo", "rehearse", "--output", str(tmp_path / "demo")])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["source_review_values_preserved"] is True
    monkeypatch.setattr(sys, "argv", [
        "demo", "run", "--source", str(tmp_path / "SYNTHETIC_REJECTED_SENTINEL"),
        "--as-of", AS_OF.isoformat(), "--output", str(tmp_path / "demo"),
    ])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "SYNTHETIC_REJECTED_SENTINEL" not in capsys.readouterr().err
