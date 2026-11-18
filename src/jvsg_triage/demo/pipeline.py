"""Content-addressed, verified snapshots; the last successful batch is never overwritten."""

import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from datetime import date
from html import escape
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from openpyxl import load_workbook
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from jvsg_triage.demo.briefing import briefing_facts, fingerprint, read_reviewed_briefing
from jvsg_triage.demo.intake import (
    fixture_records,
    read_bytes,
    read_source,
    source_workbook,
    transform,
)
from jvsg_triage.demo.models import AS_OF, VERSION, DemoError, Profile
from jvsg_triage.demo.presentation import (
    PRESENTATION_VERSION,
    add_source_validation,
    excel_dashboard,
    html_dashboard,
    json_text,
    save_workbook,
    summary,
)
from jvsg_triage.etl.ingest import IngestionError
from jvsg_triage.etl.pipeline import check_private_destination, run_extraction
from jvsg_triage.synthetic.generator import ANTI_JOIN_FILE, CASE_NOTES_FILE, generate_dataset
from jvsg_triage.synthetic.profile import DEFAULT_PROFILE
from jvsg_triage.toon.demo import decode, encode

ARTIFACTS = frozenset({
    "reviewed_profiles.xlsx", "profiles.json", "profiles.toon", "summary.json",
    "dashboard.xlsx", "dashboard.html",
})
RUNTIME_PACKAGES = ("openpyxl", "polars", "pydantic")
DEMO_HMAC_SECRET = SecretStr("synthetic-only-demonstration-key-0001")


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    version: Literal["demo-2"] = VERSION
    synthetic_only: Literal[True] = True
    sharepoint_delivery: Literal["simulated-file-drop"] = "simulated-file-drop"
    as_of: date
    batch_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    records: int = Field(ge=1)
    dependencies: dict[str, str]
    sha256: dict[str, str]
    json_utf8_bytes: int = Field(gt=0)
    toon_utf8_bytes: int = Field(gt=0)


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def runtime_versions() -> dict[str, str]:
    return {package: version(package) for package in RUNTIME_PACKAGES}


def batch_id(content: bytes, as_of: date, dependencies: dict[str, str]) -> str:
    metadata = json_text({
        "version": VERSION, "as_of": as_of.isoformat(), "dependencies": dependencies,
        "presentation_version": PRESENTATION_VERSION,
    })
    return digest(content + metadata.encode("utf-8"))


def output_root(path: Path) -> Path:
    try:
        return check_private_destination(path)
    except IngestionError:
        raise DemoError("demo: output must be under temp/, data/private/ or outside the repo") \
            from None


def write_json(path: Path, payload: object) -> None:
    path.write_text(json_text(payload), encoding="utf-8", newline="\n")


def atomic_json(path: Path, payload: object) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False,
    ) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(json_text(payload))
            stream.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def compact_json_bytes(profiles: list[Profile]) -> int:
    return len(json.dumps(
        [p.model_dump(mode="json") for p in profiles], separators=(",", ":"), sort_keys=True,
    ).encode("utf-8"))


def verify_batch(path: Path) -> Manifest:
    """Verify every file hash plus source-to-profile reconciliation and TOON equality."""
    try:
        manifest = Manifest.model_validate_json((path / "manifest.json").read_bytes())
        if set(manifest.sha256) != ARTIFACTS:
            raise DemoError("verify: manifest artifact set mismatch")
        for name, expected in manifest.sha256.items():
            artifact = path / name
            if artifact.is_symlink() or digest(artifact.read_bytes()) != expected:
                raise DemoError("verify: artifact integrity mismatch")
        content = (path / "reviewed_profiles.xlsx").read_bytes()
        if digest(content) != manifest.source_sha256:
            raise DemoError("verify: source hash mismatch")
        if batch_id(content, manifest.as_of, manifest.dependencies) != manifest.batch_id:
            raise DemoError("verify: batch identity mismatch")
        profiles = transform(read_source(content), manifest.as_of)
        expected_json = json_text([p.model_dump(mode="json") for p in profiles])
        if (path / "profiles.json").read_text(encoding="utf-8") != expected_json:
            raise DemoError("verify: normalized profiles differ from source")
        toon = (path / "profiles.toon").read_text(encoding="utf-8")
        if decode(toon) != profiles:
            raise DemoError("verify: TOON round trip differs from source")
        if (path / "summary.json").read_text(encoding="utf-8") != json_text(summary(profiles)):
            raise DemoError("verify: aggregate reconciliation failed")
        if (path / "dashboard.html").read_text(encoding="utf-8") != html_dashboard(
            profiles, manifest.source_sha256,
        ):
            raise DemoError("verify: HTML differs from profiles")
        if (
            manifest.records != len(profiles)
            or manifest.json_utf8_bytes != compact_json_bytes(profiles)
            or manifest.toon_utf8_bytes != len(toon.encode("utf-8"))
        ):
            raise DemoError("verify: record or byte counts differ")
        return manifest
    except (OSError, ValidationError, UnicodeError, json.JSONDecodeError):
        raise DemoError("verify: missing or invalid batch artifact") from None


@contextmanager
def track_refresh(root: Path, operation: Literal["batch", "rehearsal"]) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    completed = False
    try:
        atomic_json(root / "status.json", {"state": "in_progress", "operation": operation})
        yield
        completed = True
    finally:
        if not completed:
            atomic_json(root / "status.json", {
                "state": "failed", "operation": operation,
                "last_success_preserved": (root / "latest.json").exists(),
                "message": "Refresh failed. Do not present the previous snapshot as current.",
            })


def publish_latest(
    root: Path, batch: Path, as_of: date, operation: Literal["batch", "rehearsal"],
) -> None:
    atomic_json(root / "status.json", {
        "state": "success", "operation": operation, "batch_id": batch.name,
    })
    atomic_json(root / "latest.json", {
        "batch_id": batch.name, "path": f"batches/{batch.name}", "as_of": as_of.isoformat(),
    })


def build_batch(source: Path, *, as_of: date, root: Path) -> Path:
    content = read_bytes(source)
    profiles = transform(read_source(content), as_of)
    dependencies = runtime_versions()
    identity = batch_id(content, as_of, dependencies)
    batches = root / "batches"
    batches.mkdir(exist_ok=True)
    destination = batches / identity
    if destination.exists():
        existing = verify_batch(destination)
        if existing.batch_id != identity:
            raise DemoError("publish: existing batch identity mismatch")
        return destination
    with tempfile.TemporaryDirectory(prefix=".staging-", dir=batches) as temporary:
        stage = Path(temporary)
        (stage / "reviewed_profiles.xlsx").write_bytes(content)
        write_json(stage / "profiles.json", [p.model_dump(mode="json") for p in profiles])
        toon = encode(profiles)
        (stage / "profiles.toon").write_text(toon, encoding="utf-8", newline="\n")
        write_json(stage / "summary.json", summary(profiles))
        (stage / "dashboard.html").write_text(
            html_dashboard(profiles, digest(content)), encoding="utf-8", newline="\n",
        )
        save_workbook(excel_dashboard(profiles, digest(content)), stage / "dashboard.xlsx")
        manifest = Manifest(
            as_of=as_of, batch_id=identity, source_sha256=digest(content),
            records=len(profiles), dependencies=dependencies,
            sha256={name: digest((stage / name).read_bytes()) for name in sorted(ARTIFACTS)},
            json_utf8_bytes=compact_json_bytes(profiles),
            toon_utf8_bytes=len(toon.encode("utf-8")),
        )
        write_json(stage / "manifest.json", manifest.model_dump(mode="json"))
        verify_batch(stage)
        stage.rename(destination)
    return destination


def run_pipeline(source: Path, *, as_of: date, output: Path) -> Path:
    root = output_root(output)
    with track_refresh(root, "batch"):
        batch = build_batch(source, as_of=as_of, root=root)
        publish_latest(root, batch, as_of, "batch")
    return batch


def prepare(output: Path) -> dict[str, Path]:
    root = output_root(output)
    root.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, refreshed in (("baseline", False), ("refreshed", True)):
        path = root / f"{name}.xlsx"
        workbook = source_workbook(fixture_records(refreshed=refreshed))
        add_source_validation(workbook)
        save_workbook(workbook, path)
        result[name] = path
    return result


def prepare_native_sources(output: Path) -> dict[str, dict[str, Path]]:
    root = output_root(output)
    root.mkdir(parents=True, exist_ok=True)
    profile = replace(
        DEFAULT_PROFILE,
        cohort_participants=19,
        repeated_cohort_rows=0,
        cohort_note_bins=((1, 1, 1.0),),
        other_participants=0,
    )
    with tempfile.TemporaryDirectory(prefix="synthetic-native-") as temporary:
        generated = Path(temporary)
        generate_dataset(generated, seed=42, profile=profile)
        generated_csv = generated / ANTI_JOIN_FILE
        with generated_csv.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames
            rows = list(reader)
        if not headers or len(rows) != 19:
            raise DemoError("prepare: synthetic anti-join fixture does not match its contract")
        participant_ids = {row.get("StateID", "") for row in rows}
        participant_ids.discard("")
        if len(participant_ids) != 19:
            raise DemoError("prepare: synthetic cohort does not contain 19 unique participants")
        added_id = max(participant_ids, key=int)
        generated_xlsx = generated / CASE_NOTES_FILE
        prepared: dict[str, dict[str, Path]] = {}
        for name, selected_rows, excluded_id in (
            ("baseline", [row for row in rows if row.get("StateID") != added_id], added_id),
            ("refreshed", rows, None),
        ):
            anti_join = root / f"{name}_203_205_anti_join.synthetic.csv"
            with anti_join.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=headers, lineterminator="\r\n", extrasaction="raise",
                )
                writer.writeheader()
                writer.writerows(selected_rows)

            case_notes = root / f"{name}_case_notes.synthetic.xlsx"
            workbook = load_workbook(generated_xlsx)
            if workbook.sheetnames != ["Case Notes"]:
                workbook.close()
                raise DemoError("prepare: synthetic case-notes fixture has an unexpected layout")
            sheet = workbook["Case Notes"]
            header = tuple(cell.value for cell in sheet[4])
            note_rows: list[list[object]] = []
            for source_row in sheet.iter_rows(min_row=5, values_only=True):
                if not any(value is not None for value in source_row):
                    continue
                first = source_row[0]
                if isinstance(first, str) and first.startswith("Total Rows:"):
                    break
                if tuple(source_row[:len(header)]) == header:
                    break
                if excluded_id is None or str(source_row[9]).strip() != excluded_id:
                    note_rows.append(list(source_row[:len(header)]))
            sheet.delete_rows(5, sheet.max_row - 4)
            for note_row in note_rows:
                sheet.append(note_row)
            sheet.append([None] * len(header))
            sheet.append(list(header))
            sheet.append([f"Total Rows: {len(note_rows):,}"])
            save_workbook(workbook, case_notes)
            prepared[name] = {"anti_join": anti_join, "case_notes": case_notes}
    return prepared


def prepare_workflow(output: Path) -> dict[str, object]:
    root = output_root(output)
    return {
        "reviewed_profiles": prepare(root / "reviewed_profiles"),
        "native_sources": prepare_native_sources(root / "simulated_sharepoint"),
    }


def rehearse(output: Path, *, reviewed_briefing: Path | None = None) -> dict[str, object]:
    root = output_root(output)
    with track_refresh(root, "rehearsal"):
        result = build_rehearsal(root, reviewed_briefing=reviewed_briefing)
    return result


def build_rehearsal(root: Path, *, reviewed_briefing: Path | None) -> dict[str, object]:
    profile_sources = prepare(root / "reviewed_profiles")
    baseline_profiles = transform(read_source(read_bytes(profile_sources["baseline"])), AS_OF)
    refreshed_profiles = transform(read_source(read_bytes(profile_sources["refreshed"])), AS_OF)
    facts = briefing_facts(baseline_profiles, refreshed_profiles)
    briefing = read_reviewed_briefing(reviewed_briefing, facts) if reviewed_briefing else None
    briefing_html = "<p><strong>Briefing:</strong> Verified snapshot changes only (no AI copy).</p>"
    briefing_metadata: dict[str, object] = {"mode": "deterministic"}
    if briefing is not None:
        payload = briefing.model_dump(mode="json")
        briefing_metadata = {
            "mode": "reviewed_ai_copy", "payload": payload, "sha256": fingerprint(payload),
        }
        points = "".join(f"<li>{escape(point)}</li>" for point in briefing.talking_points)
        briefing_html = (
            "<h2>AI-assisted management briefing</h2>"
            "<p><strong>AI-drafted; human-reviewed.</strong> Invented aggregate counts only. "
            "Not a referral recommendation.</p>"
            f"<ul>{points}</ul><p>Compared with the verified snapshots linked above.</p>"
        )
    native_sources = prepare_native_sources(root / "simulated_sharepoint")
    intake: dict[str, dict[str, object]] = {}
    profile_counts = {"baseline": len(baseline_profiles), "refreshed": len(refreshed_profiles)}
    for name, inputs in native_sources.items():
        manifest = run_extraction(
            inputs["anti_join"], inputs["case_notes"],
            secret=DEMO_HMAC_SECRET, output_dir=root / "restricted" / name,
        )
        if manifest.summary.unique_participants != profile_counts[name]:
            raise DemoError("rehearsal: reviewed profiles do not match synthetic cohort size")
        intake[name] = {
            "anti_join_file": inputs["anti_join"].relative_to(root).as_posix(),
            "case_notes_file": inputs["case_notes"].relative_to(root).as_posix(),
            "unique_participants": manifest.summary.unique_participants,
            "matched_note_rows": manifest.summary.matched_note_rows,
            "source_sha256": {
                "anti_join": digest(read_bytes(inputs["anti_join"])),
                "case_notes": digest(read_bytes(inputs["case_notes"])),
            },
            "summary": manifest.summary.model_dump(mode="json"),
            "redactions": manifest.redactions,
            "residual_findings": manifest.residual_findings,
            "notes_with_residual_findings": manifest.notes_with_residual_findings,
            "private_output": f"restricted/{name}",
        }
    baseline = build_batch(profile_sources["baseline"], as_of=AS_OF, root=root)
    refreshed = build_batch(profile_sources["refreshed"], as_of=AS_OF, root=root)
    first = verify_batch(baseline)
    second = verify_batch(refreshed)
    old = {p.demo_id: p for p in baseline_profiles}
    new = {p.demo_id: p for p in refreshed_profiles}
    reviews_preserved = all(old[key].review == new[key].review for key in old)
    if not reviews_preserved:
        raise DemoError("rehearsal: source human-review values changed")
    result: dict[str, object] = {
        "synthetic_only": True, "as_of": AS_OF.isoformat(),
        "baseline": {"path": f"batches/{first.batch_id}", **summary(baseline_profiles)},
        "refreshed": {"path": f"batches/{second.batch_id}", **summary(refreshed_profiles)},
        "native_intake": intake,
        "profile_inputs": (
            "Synthetic human-review inputs; not extracted or classified from case notes."
        ),
        "added_demo_ids": sorted(new.keys() - old.keys()),
        "updated_demo_ids": sorted(key for key in old if old[key] != new[key]),
        "source_review_values_preserved": reviews_preserved,
        "briefing": briefing_metadata,
        "verification": "All hashes, reconciliation and TOON round trips passed",
    }
    write_json(root / "rehearsal.json", result)
    baseline_intake = intake["baseline"]
    refreshed_intake = intake["refreshed"]
    landing = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Paired report workflow | Synthetic demonstration</title>
<style>body{{font:18px/1.55 'Segoe UI',sans-serif;max-width:1050px;margin:36px auto;
padding:24px;background:#f2f6f8;color:#17324f}}a{{color:#126b62}}h1,h2{{color:#16324f}}
li{{margin:10px 0}}section{{background:#fff;padding:18px 24px;margin:18px 0;
border-radius:8px;box-shadow:0 2px 8px #17324f16}}.notice{{padding:14px;background:#e6f3ef;
border-left:5px solid #2e8b57}}code{{font-size:.9em}}</style><body>
<h1>From paired report upload to reviewed dashboard</h1>
<p class="notice"><strong>Synthetic-only rehearsal.</strong> All files are invented.
SharePoint delivery is simulated locally. This page makes no cloud or model calls.</p>
<section><h2>1. Upload the raw report pair</h2>
<p>These are the original synthetic-layout inputs in the simulated SharePoint folder.
The anti-join establishes cohort membership; the paired case-notes report is matched
and scrubbed in the local processing step.</p><ul>
<li><a href="{baseline_intake['anti_join_file']}" download>
Open/download baseline anti-join CSV</a></li>
<li><a href="{baseline_intake['case_notes_file']}" download>
Open/download baseline case-notes workbook</a></li>
<li><a href="{refreshed_intake['anti_join_file']}" download>
Open/download refreshed anti-join CSV</a></li>
<li><a href="{refreshed_intake['case_notes_file']}" download>
Open/download refreshed case-notes workbook</a></li>
</ul><p>Folder: <code>temp/management-demo/simulated_sharepoint/</code></p></section>
<section><h2>2. Validate, match, and privacy-process</h2>
<p>The run checks native headers and the case-notes footer, HMAC-tokenizes the join key,
matches the supplied cohort, and writes scrubbed notes to a restricted local folder.
The notes are not embedded in the dashboard or TOON file.</p>
<ul><li>Baseline: {baseline_intake['unique_participants']} unique cohort members;
{baseline_intake['matched_note_rows']} matched notes.</li>
<li>Refreshed: {refreshed_intake['unique_participants']} unique cohort members;
{refreshed_intake['matched_note_rows']} matched notes.</li></ul></section>
<section><h2>3. Supply the synthetic human-review profile</h2>
<p>The current native reports do not supply the demo's office, aging, or four-domain
profile fields. Those values come from separate, invented human-review inputs—not
automated case-note classification. In production, the fields and review process
need an approved source contract.</p></section>
<section><h2>4. Populate the visualization and package TOON</h2>
<section aria-labelledby="demo-files-title">
<h2 id="demo-files-title">Demo files - open or download here</h2>
<p>In VS Code, open <code>temp/management-demo/</code> for the standard demo.
Paths below are relative to that output folder. These links open the generated
files, not the Python source code.</p>
<ul>
<li><a href="batches/{second.batch_id}/dashboard.xlsx" download>
Download the updated Excel report</a> - charts and participant list.<br>
<code>batches/{second.batch_id}/dashboard.xlsx</code></li>
<li><a href="batches/{second.batch_id}/reviewed_profiles.xlsx" download>
Download the synthetic human-review profile input</a> - the reviewed fields used for the report.<br>
<code>batches/{second.batch_id}/reviewed_profiles.xlsx</code></li>
<li><a href="batches/{second.batch_id}/profiles.toon" download>
Download the TOON data file</a> - compact machine-readable records.<br>
<code>batches/{second.batch_id}/profiles.toon</code></li>
</ul>
<p>Excel may download rather than open in the browser. Check your browser's Downloads list.
Each report also has its own file links at the top of the page.</p></section>
<h2>Start with the first report, then see what changed</h2>
<ol><li><a href="batches/{first.batch_id}/dashboard.html">First report: 18 fictional people</a>
 - see who may need follow-up and what support needs are recorded.</li>
<li><a href="batches/{second.batch_id}/dashboard.html">Updated report: 19 fictional people</a>
 - see the result after a new workbook arrives.</li>
<li><a href="batches/{second.batch_id}/dashboard.xlsx">Open the updated Excel report</a>
 - the same information, with charts and a filterable list.</li></ol>
{briefing_html}
<h2>What changed in this example?</h2>
<ul><li>Participant DEMO-0005 has a new recorded contact: 0 days since contact instead of 30.</li>
<li>The same person's housing barrier is now partly addressed instead of critical.</li>
<li>Participant DEMO-0019 is added. Existing staff review information stays unchanged.</li></ul>
<p>Qualified staff remain responsible for next steps. No referrals are sent.</p>
<details><summary>Technical evidence (for IT review)</summary><ul>
<li><a href="batches/{second.batch_id}/profiles.toon">Compact machine-readable data (TOON)</a></li>
<li><a href="rehearsal.json">Source hashes, reconciliation, and privacy-processing counts</a></li>
<li><a href="rehearsal.json">Processing checks and exact changes</a></li>
</ul></details></section></body></html>"""
    (root / "index.html").write_text(landing, encoding="utf-8", newline="\n")
    publish_latest(root, refreshed, AS_OF, "rehearsal")
    return result
