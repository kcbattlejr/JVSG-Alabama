"""Entirely invented workbook data; no network, credentials or private inputs."""

import json
from datetime import timedelta
from pathlib import Path
<<<<<<< HEAD
=======
from xml.etree import ElementTree
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook

from jvsg_triage.demo.__main__ import main
<<<<<<< HEAD
=======
from jvsg_triage.demo.briefing import MAX_BRIEFING_BYTES, fingerprint
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
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

<<<<<<< HEAD
    content = modified_source(tmp_path, "D3", datetime(2026, 11, 20))
    assert read_source(content)[0].last_contact_date == AS_OF
    with pytest.raises(DemoError, match="date-only"):
        read_source(modified_source(tmp_path, "D3", datetime(2026, 11, 20, 12)))
=======
    content = modified_source(tmp_path, "D3", datetime.combine(AS_OF, datetime.min.time()))
    assert read_source(content)[0].last_contact_date == AS_OF
    with pytest.raises(DemoError, match="date-only"):
        read_source(modified_source(tmp_path, "D3", datetime.combine(
            AS_OF, datetime.min.time().replace(hour=12),
        )))
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88


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
<<<<<<< HEAD
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
=======
    text = encode(profiles)
    assert text.startswith(
        "[20]{demo_id,office,assessment_date,last_contact_date,TRN,HSG,MED,LEG,"
        "review,as_of,idle_days,alert}:\n  DEMO-0001,"
    )
    assert ",null," in text
    assert decode(text) == profiles


@pytest.mark.parametrize(
    "mutation", ["row-count", "extra", "order", "leading-zero", "inconsistent"],
)
def test_toon_rejects_malformed_or_noncanonical_profiles(mutation: str) -> None:
    text = encode(transform(fixture_records(), AS_OF)[:1])
    if mutation == "row-count":
        text = text.replace("[1]", "[2]")
    elif mutation == "extra":
        text = text.rstrip("\n") + ",extra\n"
    elif mutation == "order":
        text = text.replace("demo_id,office", "office,demo_id")
    elif mutation == "leading-zero":
        text = text.replace(",0,GREEN", ",00,GREEN")
    else:
        text = text.replace(",GREEN", ",RED")
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
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
    assert first["profile_inputs"] == (
        "Synthetic human-review inputs; not extracted or classified from case notes."
    )
    intake = first["native_intake"]
    assert isinstance(intake, dict)
    for name, expected in (("baseline", 18), ("refreshed", 19)):
        stage = intake[name]
        assert isinstance(stage, dict)
        assert stage["unique_participants"] == expected
        assert stage["summary"]["matched_note_rows"] == expected
        assert (first_root / stage["anti_join_file"]).is_file()
        assert (first_root / stage["case_notes_file"]).is_file()
        assert (first_root / stage["private_output"] / "redacted_notes.jsonl").is_file()
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
<<<<<<< HEAD
=======
    assert first["briefing"] == {"mode": "deterministic"}
    assert "Verified snapshot changes only (no AI copy)." in (first_root / "index.html").read_text()


BRIEFING_DRAFT = (
    Path(__file__).resolve().parents[1] / "data/synthetic/management_briefing.draft.json"
)


def test_offline_prompt_and_reviewed_briefing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    import sys

    monkeypatch.setattr(sys, "argv", ["demo", "briefing-prompt"])
    assert main() == 0
    prompt = json.loads(capsys.readouterr().out)
    assert prompt["facts"] == {
        "synthetic_only": True, "as_of": "2026-11-19", "records_added": 1,
        "existing_records_updated": 1,
        "baseline": {"participants": 18, "awaiting_staff_review": 16,
                     "contact_bands": {"GREEN": 6, "YELLOW": 6, "RED": 6}},
        "refreshed": {"participants": 19, "awaiting_staff_review": 17,
                      "contact_bands": {"GREEN": 8, "YELLOW": 6, "RED": 5}},
        "contact_band_definitions": {
            "GREEN": "0-14 days", "YELLOW": "15-29 days", "RED": "30 or more days",
        },
    }
    payload = json.loads(BRIEFING_DRAFT.read_bytes())
    assert payload["review_status"] == "draft"
    assert payload["facts_sha256"] == prompt["response_shape"]["facts_sha256"]
    payload["review_status"] = "reviewed"  # Exercise the operator gate with a test fixture.
    payload["talking_points"][0] = "<em>Fictional only</em>"
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(json.dumps(payload))
    root = tmp_path / "demo"
    original = rehearse(root)
    monkeypatch.setattr(sys, "argv", [
        "demo", "rehearse", "--output", str(root), "--reviewed-briefing", str(reviewed),
    ])
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert {k: v for k, v in result.items() if k != "briefing"} == {
        k: v for k, v in original.items() if k != "briefing"
    }
    assert result["briefing"] == {
        "mode": "reviewed_ai_copy", "payload": payload, "sha256": fingerprint(payload),
    }
    assert json.loads((root / "rehearsal.json").read_bytes()) == result
    assert verify_batch(root / result["refreshed"]["path"]).records == 19
    html = (root / "index.html").read_text()
    assert "AI-drafted; human-reviewed." in html
    assert "&lt;em&gt;Fictional only&lt;/em&gt;" in html
    assert "<em>Fictional only</em>" not in html


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("draft", "draft must be reviewed"),
        ("stale", "source facts changed"),
        ("unknown", "cannot read or validate"),
        ("too_long", "cannot read or validate"),
        ("too_large", "cannot read or validate"),
        ("duplicate", "cannot read or validate"),
    ],
)
def test_invalid_opt_in_briefing_does_not_publish(
    tmp_path: Path, case: str, error: str,
) -> None:
    payload = json.loads(BRIEFING_DRAFT.read_bytes())
    if case != "draft":
        payload["review_status"] = "reviewed"
    if case == "stale":
        payload["facts_sha256"] = "0" * 64
    elif case == "unknown":
        payload["unapproved_field"] = True
    elif case == "too_long":
        payload["talking_points"][0] = "x" * 241
    data = json.dumps(payload)
    if case == "too_large":
        data += " " * MAX_BRIEFING_BYTES
    elif case == "duplicate":
        data = '{"review_status": "draft", ' + data[1:]
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text(data)
    root = tmp_path / "demo"
    with pytest.raises(DemoError, match=error):
        rehearse(root, reviewed_briefing=reviewed)
    for name in ("batches", "index.html", "rehearsal.json", "latest.json"):
        assert not (root / name).exists()
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88


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
    dashboard = workbook["Dashboard"]
    assert dashboard["A1"].value == "Veteran follow-up and support needs"
    assert dashboard["A5"].value == 18
<<<<<<< HEAD
    assert [dashboard[cell].value for cell in ("D5", "G5", "J5")] == [6, 6, 6]
=======
    assert [dashboard[cell].value for cell in ("E5", "J5", "N5")] == [6, 6, 6]
    assert dashboard.max_column == 17
    assert dashboard.print_area == "'Dashboard'!$A$1:$Q$36"
    assert {str(area) for area in dashboard.merged_cells.ranges} >= {
        "A1:Q1", "A7:Q7", "A28:H28", "J28:Q28", "A29:Q29", "A30:D30", "E30:Q30",
    }
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
    assert dashboard["A1"].font.size == 22
    assert dashboard["A1"].fill.fgColor.rgb.endswith("16324F")
    assert dashboard.row_dimensions[1].height == 42
    assert len(dashboard._charts) == 2
    assert dashboard.page_setup.orientation == "landscape"
    assert dashboard.page_setup.fitToWidth == 1
    watchlist = workbook["Watchlist"]
    assert watchlist["A1"].alignment.wrap_text is True
    assert watchlist.column_dimensions["M"].width == 40
    assert watchlist.row_dimensions[2].height == 42
    assert watchlist.freeze_panes == "C2"
    rows = list(workbook["Watchlist"].iter_rows(min_row=2, values_only=True))
    assert len(rows) == 18
    assert rows[4][10:12] == (30, "Extended gap in contact")
    assert rows[1][8] == "Staff review recorded"
<<<<<<< HEAD
    assert workbook["TOON"]["B2"].value == encode(transform(fixture_records(), AS_OF)[0])
=======
    row_toon = workbook["TOON"]["B2"].value
    assert isinstance(row_toon, str)
    assert decode(row_toon + "\n") == transform(fixture_records(), AS_OF)[:1]
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
    workbook.close()
    with ZipFile(batch / "dashboard.xlsx") as archive:
        assert len([name for name in archive.namelist() if name.startswith("xl/charts/chart")]) == 2
        assert not any("externalLinks" in name for name in archive.namelist())
<<<<<<< HEAD
=======
        sheet_xml = ElementTree.fromstring(archive.read("xl/worksheets/sheet2.xml"))
        table_xml = ElementTree.fromstring(archive.read("xl/tables/table1.xml"))
        assert sheet_xml.find("{*}autoFilter") is None
        assert table_xml.find("{*}autoFilter[@ref='A1:N19']") is not None
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
    html = (batch / "dashboard.html").read_text()
    assert 'id="count-RED">6' in html
    assert "No live connection" in html
    assert "<tr data-office=" in html
    assert "https://" not in html


<<<<<<< HEAD
@pytest.mark.parametrize("refreshed", [False, True])
def test_watchlist_filter_belongs_only_to_the_excel_table(
    tmp_path: Path, refreshed: bool,
) -> None:
    from xml.etree import ElementTree

    profiles = transform(fixture_records(refreshed=refreshed), AS_OF)
    path = tmp_path / "dashboard.xlsx"
    save_workbook(excel_dashboard(profiles, "synthetic"), path)
    namespace = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as archive:
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet2.xml"))
        table = ElementTree.fromstring(archive.read("xl/tables/table1.xml"))
    assert sheet.find("s:autoFilter", namespace) is None
    assert sheet.find("s:tableParts/s:tablePart", namespace) is not None
    table_filter = table.find("s:autoFilter", namespace)
    assert table_filter is not None
    assert table_filter.attrib["ref"] == table.attrib["ref"] == f"A1:N{len(profiles) + 1}"
=======
def test_refreshed_chart_columns_have_explicit_labels_and_counts(tmp_path: Path) -> None:
    source = prepare(tmp_path / "intake")["refreshed"]
    batch = run_pipeline(source, as_of=AS_OF, output=tmp_path / "out")
    workbook = load_workbook(batch / "dashboard.xlsx", data_only=True)
    with ZipFile(batch / "dashboard.xlsx") as archive:
        contact = ElementTree.fromstring(archive.read("xl/charts/chart1.xml"))
        support = ElementTree.fromstring(archive.read("xl/charts/chart2.xml"))
        drawing = ElementTree.fromstring(archive.read("xl/drawings/drawing1.xml"))
    assert [
        tuple(anchor.findtext(f"{{*}}{marker}/{{*}}{coord}")
              for marker in ("from", "to") for coord in ("col", "row"))
        for anchor in drawing.findall("{*}twoCellAnchor")
    ] == [("0", "8", "8", "26"), ("9", "8", "17", "26")]
    assert [point.text for point in contact.findall(".//{*}strCache/{*}pt/{*}v")] == [
        "0-14 days", "15-29 days", "30+ days",
    ]
    assert support.find(".//{*}barDir[@val='col']") is not None
    assert len(support.findall(".//{*}ser")) == 1
    assert support.find(".//{*}dLblPos[@val='outEnd']") is not None
    assert support.find(".//{*}showVal[@val='1']") is not None
    assert support.find(".//{*}catAx/{*}title") is None
    assert support.find(".//{*}valAx/{*}title") is None
    assert [point.text for point in support.findall(".//{*}strCache/{*}pt/{*}v")] == [
        "Transportation", "Housing", "Health", "Legal",
    ]
    ref = support.findtext(".//{*}ser/{*}val/{*}numRef/{*}f")
    assert ref == "'Watchlist'!$Q$7:$Q$10"
    assert [row[0].value for row in workbook["Watchlist"]["Q7":"Q10"]] == [9, 7, 6, 7]
    assert "more than one" in str(workbook["Dashboard"]["J28"].value)
    workbook.close()
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88


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
<<<<<<< HEAD
        "Awaiting staff review", "Nov 20, 2026",
=======
        "Awaiting staff review", "Nov 19, 2026",
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
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
            "dashboard.xlsx", "reviewed_profiles.xlsx", "profiles.toon",
        }
        for link in parser.downloads:
            assert (page.parent / link).is_file()
        assert "temp/management-demo/" in html
        assert "Downloads list" in html
        if page.name == "index.html":
            assert "paired report upload" in html.lower()


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
