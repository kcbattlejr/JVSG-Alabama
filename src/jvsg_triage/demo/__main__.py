"""Reproduce the synthetic SharePoint workbook demo without cloud credentials."""

import argparse
import json
from datetime import date
from pathlib import Path

<<<<<<< HEAD
from jvsg_triage.demo.models import DemoError
=======
from jvsg_triage.demo.briefing import briefing_facts, draft_prompt
from jvsg_triage.demo.intake import fixture_records, transform
from jvsg_triage.demo.models import AS_OF, DemoError
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
from jvsg_triage.demo.pipeline import (
    prepare_workflow,
    rehearse,
    run_pipeline,
    verify_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "rehearse"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path, default=Path("temp/management-demo"))
        if name == "run":
            command.add_argument("--source", type=Path, required=True)
            command.add_argument("--as-of", type=date.fromisoformat, required=True)
<<<<<<< HEAD
=======
        if name == "rehearse":
            command.add_argument("--reviewed-briefing", type=Path, help="reviewed synthetic JSON")
    commands.add_parser("briefing-prompt", help="print a prompt with invented aggregate facts")
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
    verify = commands.add_parser("verify")
    verify.add_argument("--batch", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare_workflow(args.output)
            result: object = {
                "prepared": [
                    "simulated SharePoint report pairs",
                    "synthetic human-review profiles",
                ],
                "synthetic_only": True,
            }
        elif args.command == "run":
            path = run_pipeline(args.source, as_of=args.as_of, output=args.output)
            result = {"verified": True, "batch_id": path.name}
        elif args.command == "verify":
            manifest = verify_batch(args.batch)
            result = {"verified": True, "batch_id": manifest.batch_id, "records": manifest.records}
<<<<<<< HEAD
        else:
            result = rehearse(args.output)
=======
        elif args.command == "briefing-prompt":
            result = draft_prompt(briefing_facts(
                transform(fixture_records(), AS_OF),
                transform(fixture_records(refreshed=True), AS_OF),
            ))
        else:
            result = rehearse(args.output, reviewed_briefing=args.reviewed_briefing)
>>>>>>> 1ecb868d1248580299d68dfc5a605be8e2059a88
    except DemoError as error:
        parser.exit(2, f"{error}\n")
    except OSError:
        parser.exit(2, "demo: filesystem operation failed; check output access and disk space\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
