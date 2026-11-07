"""Template case notes with injected fake PII and character-exact ground-truth labels.

Templates imitate the observed note genres (staff e-mails with signature blocks, a
mass hiring-event invitation, phone contacts, objective assessments, referrals) and
the observed theme mix. They are written from scratch, not paraphrased from records.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta

from jvsg_triage.synthetic import vocab

LABELS = (
    "NAME", "STAFF", "HONORIFIC_NAME", "THIRD_PARTY",
    "EMAIL", "URL", "PHONE", "DATE", "ADDRESS", "ZIP", "ID",
)
# Third-party names without an honorific are outside the scrubber's design scope;
# recall is reported for them but not required.
REQUIRED_RECALL = tuple(label for label in LABELS if label != "THIRD_PARTY")


@dataclass(frozen=True)
class LabelSpan:
    label: str
    start: int
    end: int
    value: str


@dataclass(frozen=True)
class Participant:
    state_id: int
    userid: int
    app_id: int
    first: str
    last: str
    honorific: str
    phone: str
    email: str
    street: str
    unit: str | None
    zip_code: str

    @property
    def individual(self) -> str:
        return f"{self.last}, {self.first}"


@dataclass(frozen=True)
class Staff:
    last: str
    suffix: str | None
    first: str
    title: str
    phone: str
    email: str

    @property
    def mis_name(self) -> str:
        return f"{self.last}, {self.suffix}., {self.first}" if self.suffix else (
            f"{self.last}, {self.first}"
        )


@dataclass
class NoteBuilder:
    parts: list[str] = field(default_factory=list)
    spans: list[LabelSpan] = field(default_factory=list)
    length: int = 0

    def add(self, text: str) -> "NoteBuilder":
        self.parts.append(text)
        self.length += len(text)
        return self

    def pii(self, label: str, value: str) -> "NoteBuilder":
        self.spans.append(LabelSpan(label, self.length, self.length + len(value), value))
        return self.add(value)

    @property
    def text(self) -> str:
        return "".join(self.parts)


@dataclass(frozen=True)
class NoteContext:
    rng: random.Random
    participant: Participant
    staff: Staff
    contact_date: date
    fy_start: date
    fy_end: date


@dataclass(frozen=True)
class NoteDraft:
    subject: str
    contact_type: str | None
    text: str
    spans: tuple[LabelSpan, ...]


def fake_phone(rng: random.Random) -> str:
    """555-01xx is reserved for fiction in the North American Numbering Plan."""
    line = f"555-01{rng.randint(0, 99):02d}"
    return rng.choice((f"251-{line}", f"(251) {line}", f"251.{line.replace('-', '.')}"))


def _date_text(rng: random.Random, value: date) -> str:
    styles = (
        f"{value:%m/%d/%Y}",
        f"{value.month}/{value.day}/{value:%y}",
        f"{value:%B} {value.day}, {value.year}",
        f"{value:%B} {value.day}",
        f"{value:%b} {value.day}",
    )
    return rng.choice(styles)


def _future(ctx: NoteContext, days: tuple[int, int]) -> date:
    return min(ctx.contact_date + timedelta(days=ctx.rng.randint(*days)), ctx.fy_end)


def _name(b: NoteBuilder, ctx: NoteContext) -> None:
    p = ctx.participant
    style = ctx.rng.random()
    if style < 0.35:
        b.pii("NAME", p.first)
    elif style < 0.65:
        b.add(f"{p.honorific} ").pii("NAME", p.last)
    elif style < 0.9:
        b.pii("NAME", p.first).add(" ").pii("NAME", p.last)
    else:
        b.pii("NAME", p.first.upper()).add(" ").pii("NAME", p.last.upper())


def _signature(b: NoteBuilder, ctx: NoteContext) -> None:
    s = ctx.staff
    b.add("\n\nRespectfully,\n\n").pii("STAFF", s.first).add(" ").pii("STAFF", s.last)
    b.add(f"\n{s.title}\nMobile Comprehensive Career Center\n")
    b.pii("ADDRESS", f"{vocab.OFFICE_ADDRESS[0]}, {vocab.OFFICE_ADDRESS[1]}")
    b.add("\nMobile, AL ").pii("ZIP", "36602").add("\nOffice: ").pii("PHONE", s.phone)
    b.add("\nEmail: ").pii("EMAIL", s.email)
    if ctx.rng.random() < 0.5:
        b.add("\nWeb: ").pii("URL", "https://www.example.gov/veterans")
    b.add(
        "\n\nCONFIDENTIALITY NOTICE: This message may contain information protected by "
        "law. If you received it in error, notify the sender and delete it."
    )


def _home_address(b: NoteBuilder, ctx: NoteContext) -> None:
    p = ctx.participant
    b.pii("ADDRESS", p.street)
    if p.unit:
        b.add(f", {p.unit}")
    b.add(", Mobile, AL ").pii("ZIP", p.zip_code)


THEME_SENTENCES: dict[str, Callable[[NoteBuilder, NoteContext], None]] = {}


def _theme(code: str) -> Callable[
    [Callable[[NoteBuilder, NoteContext], None]], Callable[[NoteBuilder, NoteContext], None]
]:
    def register(
        function: Callable[[NoteBuilder, NoteContext], None],
    ) -> Callable[[NoteBuilder, NoteContext], None]:
        THEME_SENTENCES[code] = function
        return function
    return register


@_theme("EMP")
def _employment(b: NoteBuilder, ctx: NoteContext) -> None:
    rng = ctx.rng
    occupation = rng.choice(vocab.OCCUPATIONS)
    b.add(
        f"Veteran is seeking full-time work as a {occupation} and reports "
        f"{rng.randint(2, 18)} years of related experience. Reviewed resume and "
        "registered veteran in the state job bank. "
    )
    if rng.random() < 0.5:
        b.add(f"Veteran reported a start date at {rng.choice(vocab.EMPLOYERS)} on ")
        b.pii("DATE", _date_text(rng, _future(ctx, (3, 30)))).add(". ")


@_theme("MED")
def _medical(b: NoteBuilder, ctx: NoteContext) -> None:
    b.add(
        "Veteran is enrolled for VA health care and reports a service-connected "
        "disability rating; no work restrictions were disclosed. "
    )
    if ctx.rng.random() < 0.5:
        b.add("VA claim # ").pii("ID", str(ctx.rng.randint(40_000_000, 49_999_999)))
        b.add(" is pending. ")
    b.add("Follow-up appointment at the VA Medical Center is scheduled for ")
    b.pii("DATE", _date_text(ctx.rng, _future(ctx, (5, 45)))).add(". ")


@_theme("TRAIN")
def _training(b: NoteBuilder, ctx: NoteContext) -> None:
    rng = ctx.rng
    b.add(
        f"Discussed WIOA training options at {rng.choice(vocab.TRAINING_PROVIDERS)}; "
        f"veteran is interested in a {rng.choice(vocab.OCCUPATIONS)} certificate and "
        "will submit an ITA application once the program is confirmed. "
    )


@_theme("CONTACT")
def _contact(b: NoteBuilder, ctx: NoteContext) -> None:
    b.add("Veteran confirmed best contact number is ").pii("PHONE", ctx.participant.phone)
    b.add(" and personal email is ").pii("EMAIL", ctx.participant.email).add(". ")


@_theme("LEG")
def _legal(b: NoteBuilder, ctx: NoteContext) -> None:
    rng = ctx.rng
    b.add(
        "Veteran disclosed prior justice involvement; discussed fair-chance employers "
        "and record-sealing resources. Spoke with "
    )
    b.add(f"{rng.choice(('Ms.', 'Mr.', 'Mrs.'))} ")
    b.pii("HONORIFIC_NAME", rng.choice(vocab.THIRD_PARTY_LAST))
    b.add(" at the Legal Services clinic, who will contact the veteran directly. ")


@_theme("TRN")
def _transport(b: NoteBuilder, ctx: NoteContext) -> None:
    b.add(
        "Veteran lacks reliable transportation and relies on rides from family; "
        "referred to the transit voucher program and discussed bus routes near "
        "target employers. "
    )


@_theme("HSG")
def _housing(b: NoteBuilder, ctx: NoteContext) -> None:
    rng = ctx.rng
    b.add("Veteran reports unstable housing and is staying with family at ")
    _home_address(b, ctx)
    b.add(". Referred to ")
    b.pii(
        "THIRD_PARTY",
        f"{rng.choice(vocab.THIRD_PARTY_FIRST)} {rng.choice(vocab.THIRD_PARTY_LAST)}",
    )
    b.add(f", {rng.choice(('HUD-VASH', 'SSVF'))} case manager, for a housing assessment. ")


def hiring_event(ctx: NoteContext, event: tuple[str, date]) -> NoteDraft:
    """Mass invitation: identical body for every recipient, as in bulk outreach."""
    employer, event_day = event
    b = NoteBuilder()
    b.add("Good afternoon,\n\nYou are invited to the ").add(employer)
    b.add(f" Veteran Hiring Event on {event_day:%A}, ")
    b.pii("DATE", f"{event_day:%B} {event_day.day}, {event_day.year}")
    b.add(" from 9:00 a.m. to 1:00 p.m. at ")
    b.pii("ADDRESS", f"{vocab.OFFICE_ADDRESS[0]}").add(", Mobile, AL ").pii("ZIP", "36602")
    b.add(
        ". Employers will conduct on-the-spot interviews for production, logistics and "
        "maintenance positions. Veterans receive priority of service.\n\n"
        "Please bring several copies of your resume, a DD-214 or other proof of "
        "service, and dress for an interview. Transportation assistance is available "
        "on request. Reply to this message or call our office to reserve a time slot."
    )
    _signature(b, ctx)
    return NoteDraft("Veteran Hiring Event Invitation", ctx.rng.choice(("Other", "E-mail")),
                     b.text, tuple(b.spans))


def email_follow_up(ctx: NoteContext, event: tuple[str, date]) -> NoteDraft:
    b = NoteBuilder().add("Good morning ")
    _name(b, ctx)
    b.add(
        ",\n\nI am following up on our conversation about your job search. I have "
        "attached three openings that match your experience. Please review them and let "
        "me know which ones interest you so I can send a referral. "
    )
    THEME_SENTENCES[ctx.rng.choice(("EMP", "TRAIN", "EMP"))](b, ctx)
    b.add("\n\nPlease respond by ").pii("DATE", _date_text(ctx.rng, _future(ctx, (2, 10))))
    b.add(" so we can stay on schedule.")
    _signature(b, ctx)
    return NoteDraft("Job Search Follow-up", "E-mail" if ctx.rng.random() < 0.6 else "Other",
                     b.text, tuple(b.spans))


def phone_contact(ctx: NoteContext, event: tuple[str, date]) -> NoteDraft:
    b = NoteBuilder()
    if ctx.rng.random() < 0.5:
        b.add("Called ")
        _name(b, ctx)
        b.add(" at ").pii("PHONE", ctx.participant.phone)
        b.add("; no answer and left a voicemail requesting a call back.")
    else:
        b.add("Received call from ")
        _name(b, ctx)
        b.add(
            ". Veteran asked about upcoming hiring events and the status of employer "
            "referrals. Advised veteran to check email and confirmed SID "
        )
        b.pii("ID", str(ctx.participant.state_id)).add(" on file. ")
        THEME_SENTENCES["EMP"](b, ctx)
    return NoteDraft("Phone Contact", "Telephone", b.text, tuple(b.spans))


def objective_assessment(ctx: NoteContext, event: tuple[str, date]) -> NoteDraft:
    rng = ctx.rng
    b = NoteBuilder().add("203 Objective Assessment completed with ")
    _name(b, ctx)
    b.add(" (Userid ").pii("ID", str(ctx.participant.userid)).add(") on ")
    b.pii("DATE", _date_text(rng, ctx.contact_date)).add(".\n\n")
    b.add(
        "Eligibility and significant barrier to employment were reviewed. Veteran "
        "resides at "
    )
    _home_address(b, ctx)
    b.add(".\n\n")
    themes = ["EMP", *rng.sample(("MED", "TRAIN", "CONTACT", "LEG", "TRN", "HSG"), k=3)]
    for theme in themes:
        THEME_SENTENCES[theme](b, ctx)
        b.add("\n")
    b.add(
        "\nIndividual Employment Plan goals: obtain full-time employment, address "
        "identified barriers and maintain monthly contact. Next contact scheduled for "
    )
    b.pii("DATE", _date_text(rng, _future(ctx, (14, 35)))).add(".")
    contact_type = "Face-to-Face" if rng.random() < 0.6 else "Other"
    return NoteDraft("Objective Assessment", contact_type, b.text, tuple(b.spans))


def referral(ctx: NoteContext, event: tuple[str, date]) -> NoteDraft:
    rng = ctx.rng
    agency, theme = rng.choice(vocab.REFERRAL_AGENCIES)
    b = NoteBuilder().add(f"Referral made to {agency} for ")
    _name(b, ctx)
    b.add(". ")
    THEME_SENTENCES[theme](b, ctx)
    b.add("Will follow up on referral outcome by ")
    b.pii("DATE", _date_text(rng, _future(ctx, (7, 21)))).add(".")
    contact_type = rng.choice(("Other", "Other", None))
    return NoteDraft("Supportive Service Referral", contact_type, b.text, tuple(b.spans))


TEMPLATES: tuple[tuple[Callable[[NoteContext, tuple[str, date]], NoteDraft], float], ...] = (
    (email_follow_up, 0.32),
    (phone_contact, 0.18),
    (objective_assessment, 0.22),
    (referral, 0.28),
)
