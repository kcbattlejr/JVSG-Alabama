"""Write a seeded synthetic copy of both native downloads plus PII ground truth.

Outputs mirror the native layouts the ETL contract expects: a 46-column CSV with
the header on row 1 and a single-sheet XLSX with three title rows, wrapped headers,
a blank column B and the repeated-header ``Total Rows`` footer. Every value is
invented; see ``vocab`` and ``profile`` for provenance.
"""

import csv
import hashlib
import json
import random
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment

from jvsg_triage.etl.contracts import ANTI_JOIN_HEADERS, CASE_NOTE_HEADERS, CONTRACT_VERSION
from jvsg_triage.synthetic import vocab
from jvsg_triage.synthetic.notes import (
    TEMPLATES,
    NoteContext,
    NoteDraft,
    Participant,
    Staff,
    fake_phone,
    hiring_event,
)
from jvsg_triage.synthetic.profile import DEFAULT_PROFILE, SyntheticProfile

GENERATOR_VERSION = "1.1"
ANTI_JOIN_FILE = "fy2026_203_205_anti_join.synthetic.csv"
CASE_NOTES_FILE = "fy2026_case_notes.synthetic.xlsx"
LABELS_FILE = "fy2026_case_notes.pii_labels.jsonl"
MANIFEST_FILE = "manifest.json"
FIRST_DATA_ROW = 5
_FIXED_TIMESTAMP = datetime(2026, 1, 1)


def _day(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def _mis_datetime(value: date | None) -> str:
    return f"{value:%m/%d/%Y} 00:00:00" if value else ""


def _unique_ids(rng: random.Random, count: int) -> list[int]:
    """Mostly 7-digit, some 6- and 5-digit values in reserved-looking 99/98/97 bands."""
    seen: set[int] = set()
    while len(seen) < count:
        roll = rng.random()
        if roll < 0.9:
            seen.add(rng.randint(9_900_000, 9_999_999))
        elif roll < 0.98:
            seen.add(rng.randint(980_000, 989_999))
        else:
            seen.add(rng.randint(97_000, 97_999))
    values = sorted(seen)
    rng.shuffle(values)
    return values


def _participants(rng: random.Random, count: int) -> list[Participant]:
    pairs = rng.sample(
        [(first, last) for first in vocab.FIRST_NAMES for last in vocab.LAST_NAMES], count,
    )
    state_ids = _unique_ids(rng, count)
    userids = rng.sample(range(9_600_000, 9_700_000), count)
    app_ids = rng.sample(range(9_500_000, 9_600_000), count)
    people: list[Participant] = []
    for index, (first, last) in enumerate(pairs):
        if rng.random() < 0.06:
            last = f"{rng.choice(vocab.MIDDLE_PARTICLES)} {last}"
        handle = "".join(ch for ch in f"{first}.{last}".lower() if ch.isalpha() or ch == ".")
        people.append(Participant(
            state_id=state_ids[index],
            userid=userids[index],
            app_id=app_ids[index],
            first=first,
            last=last,
            honorific=rng.choice(("Mr.", "Ms.")),
            phone=fake_phone(rng),
            email=f"{handle}{rng.randint(1, 99)}@example.org",
            street=(
                f"{rng.randint(100, 9999)} {rng.choice(vocab.STREETS)} "
                f"{rng.choice(vocab.STREET_TYPES)}"
            ),
            unit=rng.choice(vocab.UNITS) if rng.random() < 0.3 else None,
            zip_code=rng.choice(("36603", "36605", "36606", "36608", "36609", "36695")),
        ))
    return people


def _staff() -> list[Staff]:
    return [
        Staff(last, suffix, first, title, f"251-555-01{index:02d}",
              f"{first[0].lower()}{last.split('-')[0].lower()}@example.gov")
        for index, (last, suffix, first, title) in enumerate(vocab.STAFF)
    ]


def _cohort_note_count(rng: random.Random, profile: SyntheticProfile) -> int:
    roll, cumulative = rng.random(), 0.0
    for low, high, share in profile.cohort_note_bins:
        cumulative += share
        if roll < cumulative:
            return rng.randint(low, high)
    low, high, _ = profile.cohort_note_bins[-1]
    return rng.randint(low, high)


def _anti_join_rows(
    rng: random.Random, cohort: list[Participant], staff: Staff, profile: SyntheticProfile,
    fy: tuple[date, date],
) -> list[dict[str, str]]:
    repeated = rng.sample(cohort, profile.repeated_cohort_rows)
    case_managers = (
        [f" {last}, {first}" for last, suffix, first in vocab.CASE_MANAGER_NAMES if not suffix]
        + [f" {last}, {suffix}., {first}" for last, suffix, first in vocab.CASE_MANAGER_NAMES
           if suffix]
    )
    rows: list[dict[str, str]] = []
    for person in sorted([*cohort, *repeated], key=lambda p: (p.last, p.first)):
        created = _day(rng, *fy)
        caps = rng.random() < profile.caps_name_share
        row = dict.fromkeys(ANTI_JOIN_HEADERS, "")
        row.update({
            "programdesc3": "Title III - Wagner-Peyser (WP)",
            "Username": str(person.userid),
            "StateID": str(person.state_id),
            "Region": "Southwest Alabama Partnership for Training & Employment (SWAPTE)",
            "Office": "Mobile Comprehensive Career Center",
            "FirstName": person.first.upper() if caps else person.first,
            "LastName": person.last.upper() if caps else person.last,
            "CityStateCountry": "****",
            "primephone": "****",
            "email": "****",
            "Service": "203 - Objective Assessment",
            "CompletionStatus": "Successful Completion",
            "StaffCreated": staff.mis_name,
            "Date1": _mis_datetime(created),
            "Date2": _mis_datetime(created),
            "Date3": _mis_datetime(min(created + timedelta(days=rng.randint(0, 5)), fy[1])),
            "Date4": _mis_datetime(created),
            "Date5": _mis_datetime(_day(rng, date(2020, 1, 1), created)),
            "col_exitdate": _mis_datetime(
                _day(rng, created, fy[1]) if rng.random() < profile.exit_date_share else None
            ),
            "employmentdate": _mis_datetime(
                _day(rng, date(2024, 1, 1), fy[1])
                if rng.random() < profile.employment_date_share else None
            ),
            "EditStaff": staff.mis_name,
            "AppID": str(person.app_id),
            "CaseManager": rng.choices([*case_managers, ""], weights=(0.54, 0.30, 0.16))[0],
            "registeredapprenticeship": "Not Disclose",
            "Hispanic": "Yes" if rng.random() < 0.08 else "No",
            "learningmode": (
                "Virtual/Online (Yes)" if rng.random() < profile.virtual_learning_share
                else "No Virtual/Online, In-person Only"
            ),
            "col_offender": rng.choices(("N/A", "No", "Yes"), weights=(0.45, 0.45, 0.10))[0],
            "itapaying": "No",
            "textbox81": "Create Date",
            "textbox82": "Actual Date",
            "textbox83": "Edit Date",
            "textbox84": "Scheduled Date",
            "textbox85": "Application Date",
        })
        rows.append(row)
    return rows


def _note_rows(
    rng: random.Random, cohort: list[Participant], others: list[Participant],
    staff_members: list[Staff], profile: SyntheticProfile, fy: tuple[date, date],
) -> list[tuple[Participant, Staff, date, NoteDraft]]:
    events = [
        (rng.choice(vocab.EMPLOYERS), _day(rng, fy[0], fy[1])) for _ in range(3)
    ]
    plan = [(person, _cohort_note_count(rng, profile)) for person in cohort]
    plan += [(person, rng.randint(*profile.other_notes_range)) for person in others]
    templates = [template for template, _ in TEMPLATES]
    weights = [weight for _, weight in TEMPLATES]
    notes: list[tuple[Participant, Staff, date, NoteDraft]] = []
    for person, count in plan:
        for _ in range(count):
            # One primary author, as in the observed download.
            staff = staff_members[0] if rng.random() < 0.9 else rng.choice(staff_members[1:])
            contact = _day(rng, *fy)
            ctx = NoteContext(rng, person, staff, contact, *fy)
            if rng.random() < profile.hiring_event_share:
                draft = hiring_event(ctx, rng.choice(events))
            else:
                draft = rng.choices(templates, weights)[0](ctx, rng.choice(events))
            notes.append((person, staff, contact, draft))
    notes.sort(key=lambda item: (item[0].individual, item[2]))
    return notes


def _write_xlsx(
    path: Path, rows: list[tuple[Participant, Staff, date, NoteDraft]],
    rng: random.Random, profile: SyntheticProfile, fy: tuple[date, date],
) -> None:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Case Notes"
    workbook.properties.creator = "jvsg_triage synthetic generator"
    workbook.properties.created = _FIXED_TIMESTAMP
    workbook.properties.modified = _FIXED_TIMESTAMP
    sheet.append(["Case Notes Report (SYNTHETIC)"])
    sheet.append([
        f"Report Criteria:\nContact Date: {fy[0]:%m/%d/%Y} - {fy[1]:%m/%d/%Y}\n"
        "Office: Mobile Comprehensive Career Center",
        "All records are synthetic",
    ])
    sheet.append([])
    sheet.append(list(CASE_NOTE_HEADERS))
    wrap = Alignment(wrap_text=True, vertical="top")
    for cell in sheet[4]:
        cell.alignment = wrap
    for person, staff, contact, draft in rows:
        created = min(contact + timedelta(days=rng.randint(0, 3)), fy[1])
        edited = rng.random() >= profile.unedited_share
        sheet.append([
            person.userid,
            None,
            person.individual,
            staff.mis_name,
            f"{created:%m/%d/%Y}",
            f"{contact:%m/%d/%Y}",
            draft.contact_type,
            staff.mis_name if edited else None,
            f"{min(created + timedelta(days=rng.randint(0, 10)), fy[1]):%m/%d/%Y}"
            if edited else None,
            person.state_id,
            draft.subject,
            draft.text,
        ])
    sheet.append([])
    sheet.append(list(CASE_NOTE_HEADERS))
    sheet.append([f"Total Rows: {len(rows):,}"])
    for column, width in zip("ABCDEFGHIJKL", (10, 2, 24, 26, 11, 11, 12, 26, 11, 10, 30, 90),
                             strict=True):
        sheet.column_dimensions[column].width = width
    workbook.save(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_dataset(
    output_dir: Path, *, seed: int = 42, profile: SyntheticProfile = DEFAULT_PROFILE,
) -> dict[str, object]:
    """Write CSV, XLSX, PII labels and a manifest; return the manifest."""
    rng = random.Random(seed)
    fy = (date(*profile.fiscal_year_start), date(*profile.fiscal_year_end))
    people = _participants(rng, profile.cohort_participants + profile.other_participants)
    cohort, others = people[:profile.cohort_participants], people[profile.cohort_participants:]
    staff_members = _staff()
    output_dir.mkdir(parents=True, exist_ok=True)

    anti_rows = _anti_join_rows(rng, cohort, staff_members[0], profile, fy)
    anti_path = output_dir / ANTI_JOIN_FILE
    with anti_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=ANTI_JOIN_HEADERS, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(anti_rows)

    notes = _note_rows(rng, cohort, others, staff_members, profile, fy)
    _write_xlsx(output_dir / CASE_NOTES_FILE, notes, rng, profile, fy)

    labels_path = output_dir / LABELS_FILE
    with labels_path.open("w", encoding="utf-8", newline="\n") as stream:
        for offset, (person, _, _, draft) in enumerate(notes):
            stream.write(json.dumps({
                "row": FIRST_DATA_ROW + offset,
                "state_id": str(person.state_id),
                "spans": [asdict(span) for span in draft.spans],
            }, separators=(",", ":")) + "\n")

    cohort_ids = {person.state_id for person in cohort}
    contact_types: dict[str, int] = {}
    for _, _, _, draft in notes:
        key = draft.contact_type or "(blank)"
        contact_types[key] = contact_types.get(key, 0) + 1
    manifest: dict[str, object] = {
        "synthetic": True,
        "notice": "Every value is invented. No record, name, ID or text comes from MIS data.",
        "generator_version": GENERATOR_VERSION,
        "contract_version": CONTRACT_VERSION,
        "seed": seed,
        "profile": asdict(profile),
        "files": {
            "anti_join": {"name": ANTI_JOIN_FILE, "sha256": _sha256(anti_path)},
            "case_notes": {"name": CASE_NOTES_FILE, "sha256": None,
                           "note": "XLSX bytes vary by zip metadata; compare cell values"},
            "pii_labels": {"name": LABELS_FILE, "sha256": _sha256(labels_path)},
        },
        "counts": {
            "anti_join_rows": len(anti_rows),
            "cohort_participants": len(cohort),
            "case_note_rows": len(notes),
            "cohort_note_rows": sum(1 for person, *_ in notes if person.state_id in cohort_ids),
            "note_participants": len({person.state_id for person, *_ in notes}),
            "contact_types": dict(sorted(contact_types.items())),
            "pii_spans": sum(len(draft.spans) for *_, draft in notes),
        },
    }
    with (output_dir / MANIFEST_FILE).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    return manifest
