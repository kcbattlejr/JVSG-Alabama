"""Header-only CLI: intentionally offers no real-record processing or export."""

import argparse
import json
from pathlib import Path

from jvsg_triage.etl.contracts import CONTRACTS, ReportKind
from jvsg_triage.etl.ingest import IngestionError, inspect_layout


def main() -> int:
    """Emit only versioned schema metadata or validated layout coordinates."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema", help="Print header-only source contracts")
    inspect = commands.add_parser("inspect", help="Validate headers without ingesting data rows")
    inspect.add_argument("--anti-join", required=True, type=Path)
    inspect.add_argument("--case-notes", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "schema":
        print(json.dumps(
            {kind.value: contract.model_dump(mode="json") for kind, contract in CONTRACTS.items()},
            indent=2,
        ))
        return 0
    try:
        layouts = (
            inspect_layout(args.anti_join, ReportKind.ANTI_JOIN),
            inspect_layout(args.case_notes, ReportKind.CASE_NOTES),
        )
    except IngestionError as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps([layout.model_dump(mode="json") for layout in layouts], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
