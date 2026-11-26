"""Write the synthetic NASWA demo data in the SharePoint folder layout.

Standard library only, so the folder can be copied anywhere and run:

    python build_demo_data.py                    # writes ./Demo
    python build_demo_data.py --output D:\\JVSG\\Demo --as-of 2026-11-30

Everything here is invented: offices, areas, staff, usernames, State IDs and
distributions. Only the *shape* of the three MIS exports (column names, date
formats, file names, CRLF line endings, 0/1/blank flags, suppression below 10)
follows the real reports, so the Power Query files and Office Scripts run
unchanged. No private cohort profile or count is reproduced.
"""

import argparse
import csv
import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_AS_OF = date(2026, 11, 26)
# Like the real report, the fiscal-year window opens at FY start and runs through the as-of date.
DEFAULT_FY_START = date(2025, 10, 1)
DEFAULT_COUNT = 240
DEFAULT_SEED = 3042
SUPPRESSION_THRESHOLD = 10
MANAGER_REPORT_ID = "DEMO_FY2026_Notes_Candidate_Manager"

WORKLIST_COLUMNS = (
    "RESULT_STATUS", "FY_START", "FY_END", "AS_OF_DATE", "INDIVIDUAL_USERNAME",
    "STATE_ID", "STATE_ID_STATUS", "OFFICE", "OFFICE_NAME", "LWIA", "JVSG_NOTE_COUNT",
    "FIRST_JVSG_NOTE_DATE", "LAST_JVSG_NOTE_DATE", "LATEST_FY_203_DATE",
    "LAST_CONTACT_DATE", "LAST_CONTACT_STAFF", "LAST_CONTACT_STAFF_NAME",
    "DAYS_SINCE_CONTACT", "FOLLOW_UP_BAND", "UNCERTAIN_FY205_EXISTS",
    "UNDATED_WP205_EXISTS",
)  # fmt: skip
MANAGER_COLUMNS = (
    "REPORT_ID", "RESULT_STATUS", "FY_START", "FY_END", "AS_OF_DATE",
    "INDIVIDUAL_RECORD_LWIA", "LWIA_NAME", "FOLLOW_UP_BAND", "INDIVIDUALS",
)  # fmt: skip
PROFILE_COLUMNS = (
    "INDIVIDUAL_USERNAME", "STATE_ID", "AS_OF_DATE", "OFFICE_NAME", "LAST_CONTACT_DATE",
    "DAYS_SINCE_CONTACT", "CONTACT_INFO_UPDATED_DATE", "LAST_EMPLOYMENT_END_DATE",
    "LAST_OUTCOME_TYPE", "LAST_OUTCOME_DATE", "HOMELESS_FLAG", "HOUSING_UNSTABLE_FLAG",
    "DISABILITY_FLAG", "LAST_MEDICAL_SERVICE_DATE", "TRAINING_ENROLLED_FLAG", "JUSTICE_FLAG",
)  # fmt: skip

# (office code, office name, LWIA code, weight). Invented; not agency offices.
OFFICES = (
    ("11", "Demo Office Aster", "01", 7),
    ("12", "Demo Office Birch", "01", 5),
    ("13", "Demo Office Cedar", "01", 3),
    ("21", "Demo Office Dune", "02", 8),
    ("22", "Demo Office Elm", "02", 4),
    ("23", "Demo Office Fern", "02", 2),
    ("31", "Demo Office Grove", "03", 6),
    ("32", "Demo Office Harbor", "03", 4),
    ("33", "Demo Office Iris", "03", 2),
    ("41", "Demo Office Juniper", "04", 3),
    ("42", "Demo Office Kestrel", "04", 2),
    ("43", "Demo Office Larch", "04", 1),
)
LWIA_NAMES = {
    "01": "Demo Area North",
    "02": "Demo Area Coastal",
    "03": "Demo Area Central",
    "04": "Demo Area West",
}
STAFF_COUNT = 14
FLAG_UNKNOWN_RATE = 0.04


@dataclass(frozen=True)
class Candidate:
    username: str
    state_id: str
    office: str
    office_name: str
    lwia: str
    note_count: int
    first_note: datetime
    last_contact: datetime
    latest_203: date | None
    staff: str
    staff_name: str


def follow_up_band(days: int) -> str:
    if days >= 30:
        return "Overdue"
    if days >= 15:
        return "Due soon"
    return "Current"


def _stamp(value: datetime) -> str:
    """MIS style 'MM/DD/YYYY h:mm:ss AM', with no leading zero on the hour."""
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{value:%m/%d/%Y} {hour}:{value:%M:%S} {suffix}"


def _us(value: date | None) -> str:
    return "" if value is None else value.strftime("%m/%d/%Y")


def _days(as_of: date, last_contact: datetime) -> int:
    return (as_of - last_contact.date()).days


def fiscal_year(fy_start: date) -> tuple[date, date]:
    return fy_start, date(fy_start.year + 1, fy_start.month, fy_start.day) - timedelta(days=1)


def _work_time(rng: random.Random, day: date) -> datetime:
    return datetime.combine(day, datetime.min.time()) + timedelta(
        seconds=rng.randint(7 * 3600, 17 * 3600)
    )


def generate_candidates(
    count: int = DEFAULT_COUNT,
    seed: int = DEFAULT_SEED,
    as_of: date = DEFAULT_AS_OF,
    fy_start: date = DEFAULT_FY_START,
) -> list[Candidate]:
    rng = random.Random(seed)
    elapsed = (as_of - fy_start).days
    weights = [office[3] for office in OFFICES]
    state_ids = rng.sample(range(100000), count)
    staff = [(f"demo.staff{n:02d}", f"Staff, Demo {n:02d}") for n in range(1, STAFF_COUNT + 1)]
    rows: list[Candidate] = []
    for index in range(1, count + 1):
        code, name, lwia, _ = rng.choices(OFFICES, weights=weights)[0]
        # Invented skew: roughly 6 in 10 are 30+ days since the last note.
        tier = rng.choices(("current", "soon", "overdue"), weights=(28, 10, 62))[0]
        low, high = {"current": (0, 14), "soon": (15, 29), "overdue": (30, elapsed)}[tier]
        contact_day = as_of - timedelta(days=rng.randint(low, max(low, high)))
        last_contact = _work_time(rng, contact_day)
        note_count = rng.choices((1, 2, 3, 4, 5, 6, 8, 12), weights=(34, 22, 14, 10, 7, 5, 5, 3))[0]
        span = rng.randint(0, 140) if note_count > 1 else 0
        first_note = (
            last_contact
            if note_count == 1
            else _work_time(rng, max(fy_start, contact_day - timedelta(days=span)))
        )
        staff_user, staff_name = rng.choice(staff)
        has_203 = rng.random() < 0.18
        rows.append(
            Candidate(
                username=f"demo.person{index:03d}",
                state_id=f"99{state_ids[index - 1]:05d}",
                office=code,
                office_name=name,
                lwia=lwia,
                note_count=note_count,
                first_note=first_note,
                last_contact=last_contact,
                latest_203=contact_day - timedelta(days=rng.randint(0, 25)) if has_203 else None,
                staff=staff_user,
                staff_name=staff_name,
            )
        )
    rows.sort(key=lambda row: (row.office, row.username))
    return rows


def worklist_rows(
    candidates: Sequence[Candidate], as_of: date, fy_start: date = DEFAULT_FY_START
) -> list[dict[str, str]]:
    fy_start, fy_end = fiscal_year(fy_start)
    return [
        {
            "RESULT_STATUS": "candidate",
            "FY_START": _us(fy_start),
            "FY_END": _us(fy_end),
            "AS_OF_DATE": _us(as_of),
            "INDIVIDUAL_USERNAME": c.username,
            "STATE_ID": c.state_id,
            "STATE_ID_STATUS": "found",
            "OFFICE": c.office,
            "OFFICE_NAME": c.office_name,
            "LWIA": c.lwia,
            "JVSG_NOTE_COUNT": str(c.note_count),
            "FIRST_JVSG_NOTE_DATE": _stamp(c.first_note),
            "LAST_JVSG_NOTE_DATE": _stamp(c.last_contact),
            "LATEST_FY_203_DATE": _us(c.latest_203),
            "LAST_CONTACT_DATE": _stamp(c.last_contact),
            "LAST_CONTACT_STAFF": c.staff,
            "LAST_CONTACT_STAFF_NAME": c.staff_name,
            "DAYS_SINCE_CONTACT": str(_days(as_of, c.last_contact)),
            "FOLLOW_UP_BAND": follow_up_band(_days(as_of, c.last_contact)),
            "UNCERTAIN_FY205_EXISTS": "0",
            "UNDATED_WP205_EXISTS": "0",
        }
        for c in candidates
    ]


def manager_rows(
    candidates: Sequence[Candidate], as_of: date, fy_start: date = DEFAULT_FY_START
) -> list[dict[str, str]]:
    """Group by LWIA and band; omit groups below the threshold like step 21."""
    fy_start, fy_end = fiscal_year(fy_start)
    counts = Counter((c.lwia, follow_up_band(_days(as_of, c.last_contact))) for c in candidates)
    base = {
        "REPORT_ID": MANAGER_REPORT_ID,
        "FY_START": _us(fy_start),
        "FY_END": _us(fy_end),
        "AS_OF_DATE": _us(as_of),
    }
    visible = sorted((key, n) for key, n in counts.items() if n >= SUPPRESSION_THRESHOLD)
    if not visible:
        return [{**base, "RESULT_STATUS": "no_visible_groups", "INDIVIDUAL_RECORD_LWIA": "",
                 "LWIA_NAME": "", "FOLLOW_UP_BAND": "", "INDIVIDUALS": ""}]  # fmt: skip
    return [
        {**base, "RESULT_STATUS": "ready", "INDIVIDUAL_RECORD_LWIA": lwia,
         "LWIA_NAME": LWIA_NAMES[lwia], "FOLLOW_UP_BAND": band, "INDIVIDUALS": str(n)}
        for (lwia, band), n in visible
    ]  # fmt: skip


def profile_rows(
    candidates: Sequence[Candidate], as_of: date, seed: int = DEFAULT_SEED
) -> list[dict[str, str]]:
    """Invented structured profile. Service-code columns are filled as if mapped."""
    rng = random.Random(seed + 1)

    def back(max_days: int, chance: float = 1.0) -> date | None:
        return as_of - timedelta(days=rng.randint(0, max_days)) if rng.random() < chance else None

    def flag(chance: float) -> str:
        if rng.random() < FLAG_UNKNOWN_RATE:
            return ""
        return "1" if rng.random() < chance else "0"

    rows: list[dict[str, str]] = []
    for c in candidates:
        outcome = rng.choices(
            ("", "placement", "credential", "training_completion"), weights=(60, 12, 14, 14)
        )[0]
        disability = flag(0.35)
        medical = back(700, 0.6) if disability == "1" else None
        rows.append(
            {
                "INDIVIDUAL_USERNAME": c.username,
                "STATE_ID": c.state_id,
                "AS_OF_DATE": _us(as_of),
                "OFFICE_NAME": c.office_name,
                "LAST_CONTACT_DATE": _us(c.last_contact.date()),
                "DAYS_SINCE_CONTACT": str(_days(as_of, c.last_contact)),
                "CONTACT_INFO_UPDATED_DATE": _us(back(600)),
                "LAST_EMPLOYMENT_END_DATE": _us(back(900, 0.85)),
                "LAST_OUTCOME_TYPE": outcome,
                "LAST_OUTCOME_DATE": _us(back(700) if outcome else None),
                "HOMELESS_FLAG": "1" if rng.random() < 0.10 else "0",
                "HOUSING_UNSTABLE_FLAG": flag(0.16),
                "DISABILITY_FLAG": disability,
                "LAST_MEDICAL_SERVICE_DATE": _us(medical),
                "TRAINING_ENROLLED_FLAG": "1" if rng.random() < 0.10 else "0",
                "JUSTICE_FLAG": flag(0.12),
            }
        )
    return rows


def write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    """CRLF line endings and minimal quoting, like the MIS export."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def write_tree(
    output: Path, as_of: date, count: int, seed: int, fy_start: date = DEFAULT_FY_START
) -> list[Path]:
    """Write the three exports using the MIS 'NN_FreeFormSql_YYYYMMDD.csv' names."""
    candidates = generate_candidates(count, seed, as_of, fy_start)
    stamp = f"{as_of:%Y%m%d}"
    targets = [
        (output / "csv" / "manager" / f"21_FreeFormSql_{stamp}.csv", MANAGER_COLUMNS,
         manager_rows(candidates, as_of, fy_start)),
        (output / "restricted" / "csv" / "worklist" / f"17_FreeFormSql_{stamp}.csv",
         WORKLIST_COLUMNS, worklist_rows(candidates, as_of, fy_start)),
        (output / "restricted" / "csv" / "profile" / f"29_FreeFormSql_{stamp}.csv",
         PROFILE_COLUMNS, profile_rows(candidates, as_of, seed)),
    ]  # fmt: skip
    for path, columns, rows in targets:
        write_csv(path, columns, rows)
    return [path for path, _, _ in targets]


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "Demo")
    parser.add_argument("--as-of", type=date.fromisoformat, default=DEFAULT_AS_OF,
                        help="report as-of date, YYYY-MM-DD")  # fmt: skip
    parser.add_argument("--fy-start", type=date.fromisoformat, default=DEFAULT_FY_START,
                        help="fiscal year start, YYYY-MM-DD")  # fmt: skip
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    for path in write_tree(args.output, args.as_of, args.count, args.seed, args.fy_start):
        print(f"Wrote {path}")
    print("All data is invented. Delete older CSVs in each folder: the newest file wins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
