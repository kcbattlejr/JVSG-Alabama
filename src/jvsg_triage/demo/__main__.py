"""Reproduce the synthetic SharePoint workbook demo without cloud credentials."""

import argparse
import json
from datetime import date
from pathlib import Path

from jvsg_triage.demo.models import DemoError
from jvsg_triage.demo.pipeline import prepare, rehearse, run_pipeline, verify_batch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "rehearse"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path, default=Path("temp/management-demo"))
        if name == "run":
            command.add_argument("--source", type=Path, required=True)
            command.add_argument("--as-of", type=date.fromisoformat, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            sources = prepare(args.output)
            result: object = {"prepared": sorted(sources), "synthetic_only": True}
        elif args.command == "run":
            path = run_pipeline(args.source, as_of=args.as_of, output=args.output)
            result = {"verified": True, "batch_id": path.name}
        elif args.command == "verify":
            manifest = verify_batch(args.batch)
            result = {"verified": True, "batch_id": manifest.batch_id, "records": manifest.records}
        else:
            result = rehearse(args.output)
    except DemoError as error:
        parser.exit(2, f"{error}\n")
    except OSError:
        parser.exit(2, "demo: filesystem operation failed; check output access and disk space\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
