"""Private extraction: native downloads -> T2 redacted notes + T3 aggregate manifest.

Outputs hold scrubbed but still pseudonymous text, so they may only be written to a
Git-ignored private folder (``temp/`` or ``data/private/``) or outside the repository.
"""

import json
from collections import Counter
from pathlib import Path

from pydantic import SecretStr

from jvsg_triage.etl.contracts import CONTRACT_VERSION
from jvsg_triage.etl.ingest import IngestionError, ingest_reports
from jvsg_triage.etl.models import ExtractionManifest
from jvsg_triage.privacy.scrubber import PROTOCOL_VERSION, Redactor, redact_note

REPO_ROOT = Path(__file__).resolve().parents[3]
NOTES_FILE = "redacted_notes.jsonl"
MANIFEST_FILE = "manifest.json"


def check_private_destination(output_dir: Path, repo_root: Path = REPO_ROOT) -> Path:
    """Reject any in-repo destination that Git could track."""
    resolved = output_dir.resolve()
    root = repo_root.resolve()
    if not resolved.is_relative_to(root):
        return resolved
    allowed = (root / "temp", root / "data" / "private")
    if any(resolved.is_relative_to(directory) for directory in allowed):
        return resolved
    raise IngestionError(
        "extract: output must be under temp/, data/private/ or outside the repository"
    )


def run_extraction(
    anti_join_csv: Path,
    case_notes_xlsx: Path,
    *,
    secret: SecretStr,
    output_dir: Path,
    repo_root: Path = REPO_ROOT,
) -> ExtractionManifest:
    """Ingest, scrub, residual-scan and write private outputs; return counts only."""
    destination = check_private_destination(output_dir, repo_root)
    batch = ingest_reports(anti_join_csv, case_notes_xlsx, secret=secret)
    redactor = Redactor(batch.lexicon)
    redactions: Counter[str] = Counter()
    residual: Counter[str] = Counter()
    flagged = 0
    destination.mkdir(parents=True, exist_ok=True)
    with (destination / NOTES_FILE).open("w", encoding="utf-8", newline="\n") as stream:
        for note in batch.matched_notes:
            record = redact_note(note, redactor)
            redactions.update(record.redactions)
            findings = redactor.residual(record.text)
            if findings:
                flagged += 1
                residual.update(findings)
            stream.write(record.model_dump_json() + "\n")
    manifest = ExtractionManifest(
        contract_version=CONTRACT_VERSION,
        protocol_version=PROTOCOL_VERSION,
        summary=batch.summary,
        redactions=dict(sorted(redactions.items())),
        residual_findings=dict(sorted(residual.items())),
        notes_with_residual_findings=flagged,
    )
    (destination / MANIFEST_FILE).write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return manifest
