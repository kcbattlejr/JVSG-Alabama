"""Deterministic invented data in the step 17 (worklist) and step 21 (manager) layouts.

The real reports come from restricted MIS SQL kept outside this repository. This
module reproduces only their output columns, the 15/30-day follow-up bands and the
suppression of groups below 10, using invented offices, areas and people.
"""

import csv
import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 11, 20)
FY_START = date(2025, 10, 1)
FY_END = date(2026, 9, 30)
SUPPRESSION_THRESHOLD = 10
MANAGER_REPORT_ID = "DEMO_Notes_Candidate_Manager"

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
BANDS = ("Overdue", "Due soon", "Current")

# (office code, office name, LWIA code, relative weight). Invented, not agency names.
OFFICES = (
    ("0101", "Demo Office North", "A1", 5),
    ("0102", "Demo Office Lakeside", "A1", 3),
    ("0201", "Demo Office South", "B2", 6),
    ("0202", "Demo Office Harbor", "B2", 4),
    ("0301", "Demo Office East", "C3", 4),
    ("0302", "Demo Office Central", "C3", 2),
    ("0401", "Demo Office West", "D4", 1),
)
LWIA_NAMES = {
    "A1": "Demo Area North",
    "B2": "Demo Area South",
    "C3": "Demo Area East, Central",
    "D4": "Demo Area West",
}
STAFF = (
    ("demo.staff1", "Demo Staff One"),
    ("demo.staff2", "Demo Staff Two"),
    ("demo.staff3", "Demo Staff Three"),
)


@dataclass(frozen=True)
class Candidate:
    username: str
    state_id: str
    office: str
    office_name: str
    lwia: str
    note_count: int
    first_note: date
    last_note: date
    latest_203: date | None
    last_contact: date
    staff: str
    staff_name: str

    @property
    def days_since_contact(self) -> int:
        return (AS_OF - self.last_contact).days

    @property
    def band(self) -> str:
        return follow_up_band(self.days_since_contact)


def follow_up_band(days: int) -> str:
    if days >= 30:
        return "Overdue"
    if days >= 15:
        return "Due soon"
    return "Current"


def generate_candidates(count: int = 160, seed: int = 2026) -> list[Candidate]:
    rng = random.Random(seed)
    weights = [office[3] for office in OFFICES]
    rows: list[Candidate] = []
    for index in range(1, count + 1):
        code, name, lwia, _ = rng.choices(OFFICES, weights=weights)[0]
        # Invented skew: most candidates are well past the 30-day mark.
        days = int(
            rng.choices(
                (rng.randint(0, 14), rng.randint(15, 29), rng.randint(30, 320)), weights=(2, 2, 6)
            )[0]
        )
        last_contact = AS_OF - timedelta(days=days)
        first_note = max(FY_START, last_contact - timedelta(days=rng.randint(0, 120)))
        staff, staff_name = rng.choice(STAFF)
        has_203 = rng.random() < 0.45
        rows.append(
            Candidate(
                username=f"demo.person{index:03d}",
                state_id=f"99{index:07d}",
                office=code,
                office_name=name,
                lwia=lwia,
                note_count=rng.randint(1, 9),
                first_note=first_note,
                last_note=last_contact,
                latest_203=last_contact - timedelta(days=rng.randint(0, 20)) if has_203 else None,
                last_contact=last_contact,
                staff=staff,
                staff_name=staff_name,
            )
        )
    rows.sort(key=lambda row: (row.office, row.username))
    return rows


def _us(value: date | None) -> str:
    return "" if value is None else value.strftime("%m/%d/%Y")


def worklist_rows(candidates: Sequence[Candidate]) -> list[dict[str, str]]:
    return [
        {
            "RESULT_STATUS": "candidate",
            "FY_START": _us(FY_START),
            "FY_END": _us(FY_END),
            "AS_OF_DATE": _us(AS_OF),
            "INDIVIDUAL_USERNAME": c.username,
            "STATE_ID": c.state_id,
            "STATE_ID_STATUS": "found",
            "OFFICE": c.office,
            "OFFICE_NAME": c.office_name,
            "LWIA": c.lwia,
            "JVSG_NOTE_COUNT": str(c.note_count),
            "FIRST_JVSG_NOTE_DATE": _us(c.first_note),
            "LAST_JVSG_NOTE_DATE": _us(c.last_note),
            "LATEST_FY_203_DATE": _us(c.latest_203),
            "LAST_CONTACT_DATE": _us(c.last_contact),
            "LAST_CONTACT_STAFF": c.staff,
            "LAST_CONTACT_STAFF_NAME": c.staff_name,
            "DAYS_SINCE_CONTACT": str(c.days_since_contact),
            "FOLLOW_UP_BAND": c.band,
            "UNCERTAIN_FY205_EXISTS": "0",
            "UNDATED_WP205_EXISTS": "0",
        }
        for c in candidates
    ]


def manager_rows(candidates: Sequence[Candidate]) -> list[dict[str, str]]:
    """Group by LWIA and band; omit groups below the threshold like step 21."""
    counts = Counter((c.lwia, c.band) for c in candidates)
    base = {
        "REPORT_ID": MANAGER_REPORT_ID,
        "FY_START": _us(FY_START),
        "FY_END": _us(FY_END),
        "AS_OF_DATE": _us(AS_OF),
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


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sharepoint_tree(output: Path, candidates: Sequence[Candidate]) -> tuple[Path, Path]:
    """Write CSVs into the folder layout the Power Query files read."""
    manager = output / "csv" / "manager" / "synthetic_manager_report.csv"
    worklist = output / "restricted" / "csv" / "worklist" / "synthetic_worklist_report.csv"
    _write_csv(manager, MANAGER_COLUMNS, manager_rows(candidates))
    _write_csv(worklist, WORKLIST_COLUMNS, worklist_rows(candidates))
    return manager, worklist
