"""Content-addressed, verified snapshots; the last successful batch is never overwritten."""

import hashlib
import json
import os
import tempfile
from datetime import date
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

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
from jvsg_triage.etl.pipeline import check_private_destination
from jvsg_triage.toon.demo import decode, encode

ARTIFACTS = frozenset({
    "source.xlsx", "profiles.json", "profiles.toon", "summary.json",
    "dashboard.xlsx", "dashboard.html",
})
RUNTIME_PACKAGES = ("openpyxl", "polars", "pydantic")


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    version: Literal["demo-1"] = VERSION
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
        content = (path / "source.xlsx").read_bytes()
        if digest(content) != manifest.source_sha256:
            raise DemoError("verify: source hash mismatch")
        if batch_id(content, manifest.as_of, manifest.dependencies) != manifest.batch_id:
            raise DemoError("verify: batch identity mismatch")
        profiles = transform(read_source(content), manifest.as_of)
        expected_json = json_text([p.model_dump(mode="json") for p in profiles])
        if (path / "profiles.json").read_text(encoding="utf-8") != expected_json:
            raise DemoError("verify: normalized profiles differ from source")
        toon = (path / "profiles.toon").read_text(encoding="utf-8")
        if [decode(line) for line in toon.splitlines()] != profiles:
            raise DemoError("verify: TOON round trip differs from source")
        if toon != "".join(encode(p) + "\n" for p in profiles):
            raise DemoError("verify: noncanonical TOON stream")
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


def run_pipeline(source: Path, *, as_of: date, output: Path) -> Path:
    root = output_root(output)
    root.mkdir(parents=True, exist_ok=True)
    try:
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
        else:
            with tempfile.TemporaryDirectory(prefix=".staging-", dir=batches) as temporary:
                stage = Path(temporary)
                (stage / "source.xlsx").write_bytes(content)
                write_json(stage / "profiles.json", [p.model_dump(mode="json") for p in profiles])
                toon = "".join(encode(profile) + "\n" for profile in profiles)
                (stage / "profiles.toon").write_text(toon, encoding="utf-8", newline="\n")
                write_json(stage / "summary.json", summary(profiles))
                (stage / "dashboard.html").write_text(
                    html_dashboard(profiles, digest(content)), encoding="utf-8", newline="\n",
                )
                save_workbook(excel_dashboard(profiles, digest(content)), stage / "dashboard.xlsx")
                manifest = Manifest(
                    as_of=as_of, batch_id=identity, source_sha256=digest(content),
                    records=len(profiles), dependencies=dependencies,
                    sha256={
                        name: digest((stage / name).read_bytes()) for name in sorted(ARTIFACTS)
                    },
                    json_utf8_bytes=compact_json_bytes(profiles),
                    toon_utf8_bytes=len(toon.encode("utf-8")),
                )
                write_json(stage / "manifest.json", manifest.model_dump(mode="json"))
                verify_batch(stage)
                stage.rename(destination)
        atomic_json(root / "latest.json", {
            "batch_id": identity, "path": f"batches/{identity}", "as_of": as_of.isoformat(),
        })
        atomic_json(root / "status.json", {"state": "success", "batch_id": identity})
        return destination
    except (DemoError, OSError):
        atomic_json(root / "status.json", {
            "state": "failed", "last_success_preserved": (root / "latest.json").exists(),
            "message": "Refresh failed. Do not present the last successful snapshot as current.",
        })
        raise


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


def rehearse(output: Path) -> dict[str, object]:
    root = output_root(output)
    sources = prepare(root / "simulated_sharepoint")
    baseline = run_pipeline(sources["baseline"], as_of=AS_OF, output=root)
    refreshed = run_pipeline(sources["refreshed"], as_of=AS_OF, output=root)
    first = verify_batch(baseline)
    second = verify_batch(refreshed)
    baseline_profiles = transform(read_source(read_bytes(sources["baseline"])), AS_OF)
    refreshed_profiles = transform(read_source(read_bytes(sources["refreshed"])), AS_OF)
    old = {p.demo_id: p for p in baseline_profiles}
    new = {p.demo_id: p for p in refreshed_profiles}
    reviews_preserved = all(old[key].review == new[key].review for key in old)
    if not reviews_preserved:
        raise DemoError("rehearsal: source human-review values changed")
    result: dict[str, object] = {
        "synthetic_only": True, "as_of": AS_OF.isoformat(),
        "baseline": {"path": f"batches/{first.batch_id}", **summary(baseline_profiles)},
        "refreshed": {"path": f"batches/{second.batch_id}", **summary(refreshed_profiles)},
        "added_demo_ids": sorted(new.keys() - old.keys()),
        "updated_demo_ids": sorted(key for key in old if old[key] != new[key]),
        "source_review_values_preserved": reviews_preserved,
        "verification": "All hashes, reconciliation and TOON round trips passed",
    }
    write_json(root / "rehearsal.json", result)
    landing = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Veteran follow-up demonstration | Start here</title>
<style>body{{font:20px/1.6 'Segoe UI',sans-serif;max-width:950px;margin:40px auto;
padding:24px;background:#06182c;color:#f8fafc}}a,h1,h2{{color:#52d19c}}
li{{margin:16px 0}}</style><body>
<h1>Veteran follow-up and support needs</h1>
<p>All people and situations are fictional. No live SharePoint connection.</p>
<section aria-labelledby="demo-files-title">
<h2 id="demo-files-title">Demo files - open or download here</h2>
<p>In VS Code, open <code>temp/management-demo/</code> for the standard demo.
Paths below are relative to that output folder. These links open the generated
files, not the Python source code.</p>
<ul>
<li><a href="batches/{second.batch_id}/dashboard.xlsx" download>
Download the updated Excel report</a> - charts and participant list.<br>
<code>batches/{second.batch_id}/dashboard.xlsx</code></li>
<li><a href="batches/{second.batch_id}/source.xlsx" download>
Download the source Excel workbook</a> - fictional input for the updated report.<br>
<code>batches/{second.batch_id}/source.xlsx</code></li>
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
<h2>What changed in this example?</h2>
<ul><li>Participant DEMO-0005 has a new recorded contact: 0 days since contact instead of 30.</li>
<li>The same person's housing barrier is now partly addressed instead of critical.</li>
<li>Participant DEMO-0019 is added. Existing staff review information stays unchanged.</li></ul>
<p>Qualified staff remain responsible for next steps. No referrals are sent.</p>
<details><summary>Technical evidence (for IT review)</summary><ul>
<li><a href="batches/{second.batch_id}/profiles.toon">Compact machine-readable data (TOON)</a></li>
<li><a href="rehearsal.json">Processing checks and exact changes</a></li>
</ul></details></body></html>"""
    (root / "index.html").write_text(landing, encoding="utf-8", newline="\n")
    return result
