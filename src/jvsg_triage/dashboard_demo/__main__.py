"""Generate synthetic report CSVs and a local dashboard workbook.

python -m jvsg_triage.dashboard_demo --output temp/dashboard-demo
"""

import argparse
from pathlib import Path

from jvsg_triage.dashboard_demo.generate import (
    generate_candidates,
    write_sharepoint_tree,
)
from jvsg_triage.dashboard_demo.workbook import build_workbook, read_csv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("temp/dashboard-demo"))
    parser.add_argument("--count", type=int, default=160)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--csv-only", action="store_true", help="skip the .xlsx")
    args = parser.parse_args()
    candidates = generate_candidates(args.count, args.seed)
    manager, worklist = write_sharepoint_tree(args.output, candidates)
    print(f"Wrote {manager}\nWrote {worklist}")
    if not args.csv_only:
        book = build_workbook(
            read_csv(manager), read_csv(worklist), args.output / "JVSG_Dashboard_Demo.xlsx"
        )
        print(f"Wrote {book}\nOpen it in Excel; all data is invented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
