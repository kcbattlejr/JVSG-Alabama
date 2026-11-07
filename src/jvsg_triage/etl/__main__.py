"""MIS intake CLI. Console output is limited to schema metadata, layouts and counts.

Commands
    schema       print the versioned header/PII contract
    inspect      validate native report headers without reading data rows
    extract      scrub cohort notes into a private folder (requires SID_HMAC_SECRET)
    synthesize   write the seeded synthetic practice dataset
    evaluate     score scrubber recall against synthetic PII labels
"""

import argparse
import json
from pathlib import Path

from jvsg_triage.etl.contracts import CONTRACTS, ReportKind
from jvsg_triage.etl.ingest import IngestionError, inspect_layout


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def main() -> int:
    """Dispatch a command; failures print sanitized messages only."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema", help="Print header-only source contracts")
    inspect = commands.add_parser("inspect", help="Validate headers without ingesting data rows")
    extract = commands.add_parser("extract", help="Write T2 redacted notes to a private folder")
    evaluate = commands.add_parser("evaluate", help="Score scrubber recall on synthetic data")
    for command in (inspect, extract, evaluate):
        command.add_argument("--anti-join", required=True, type=Path)
        command.add_argument("--case-notes", required=True, type=Path)
    extract.add_argument("--output", required=True, type=Path,
                         help="temp/, data/private/ or a folder outside the repository")
    evaluate.add_argument("--labels", required=True, type=Path)
    synthesize = commands.add_parser("synthesize", help="Write the synthetic practice dataset")
    synthesize.add_argument("--output", type=Path, default=Path("data/synthetic"))
    synthesize.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    try:
        if args.command == "schema":
            _print({kind.value: c.model_dump(mode="json") for kind, c in CONTRACTS.items()})
        elif args.command == "inspect":
            _print([
                inspect_layout(args.anti_join, ReportKind.ANTI_JOIN).model_dump(mode="json"),
                inspect_layout(args.case_notes, ReportKind.CASE_NOTES).model_dump(mode="json"),
            ])
        elif args.command == "extract":
            from jvsg_triage.etl.pipeline import run_extraction
            from jvsg_triage.settings import Settings

            secret = Settings().sid_hmac_secret
            if secret is None:
                parser.exit(2, "extract: set SID_HMAC_SECRET (32+ bytes) in the environment\n")
            manifest = run_extraction(
                args.anti_join, args.case_notes, secret=secret, output_dir=args.output,
            )
            _print(manifest.model_dump(mode="json"))
        elif args.command == "synthesize":
            from jvsg_triage.synthetic import generate_dataset

            _print(generate_dataset(args.output, seed=args.seed)["counts"])
        else:
            from jvsg_triage.synthetic.evaluate import evaluate_recall

            result = evaluate_recall(args.anti_join, args.case_notes, args.labels)
            _print(result)
            return 0 if result["required_recall_met"] else 1
    except IngestionError as error:
        parser.exit(2, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
