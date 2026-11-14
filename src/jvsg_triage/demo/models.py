"""Closed demo vocabulary: no names, raw identifiers, contacts or narrative text."""

from datetime import date
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION: Final = "demo-1"
AS_OF = date(2026, 11, 20)
MARKER = "JVSG_SYNTHETIC_DEMO_V1"
HEADERS = (
    "demo_id", "office", "assessment_date", "last_contact_date",
    "TRN", "HSG", "MED", "LEG", "review",
)
DOMAINS = ("TRN", "HSG", "MED", "LEG")


class DemoError(ValueError):
    """Sanitized operator-facing failure; never include source cell values."""


class State(StrEnum):
    CRT = "CRT"
    ACT = "ACT"
    MIT = "MIT"
    RES = "RES"
    UNK = "UNK"


class Office(StrEnum):
    NORTH = "DEMO-NORTH"
    CENTRAL = "DEMO-CENTRAL"
    SOUTH = "DEMO-SOUTH"


class Review(StrEnum):
    PENDING = "Pending"
    REVIEWED = "Reviewed"


class Alert(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


def aging_alert(days: int) -> Alert:
    return Alert.RED if days >= 30 else Alert.YELLOW if days >= 15 else Alert.GREEN


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    demo_id: str = Field(pattern=r"^DEMO-[0-9]{4}$")
    office: Office
    assessment_date: date
    last_contact_date: date | None
    TRN: State
    HSG: State
    MED: State
    LEG: State
    review: Review

    @model_validator(mode="after")
    def contact_after_assessment(self) -> "SourceRecord":
        if self.last_contact_date is not None and self.last_contact_date < self.assessment_date:
            raise ValueError("contact predates assessment")
        return self

    @property
    def priority(self) -> State:
        states = (self.TRN, self.HSG, self.MED, self.LEG)
        return next(
            state for state in (State.CRT, State.ACT, State.UNK, State.MIT, State.RES)
            if state in states
        )


class Profile(SourceRecord):
    as_of: date
    idle_days: int = Field(ge=0)
    alert: Alert

    @model_validator(mode="after")
    def consistent_aging(self) -> "Profile":
        touch = self.last_contact_date or self.assessment_date
        if touch > self.as_of or self.assessment_date > self.as_of:
            raise ValueError("future date")
        if self.idle_days != (self.as_of - touch).days:
            raise ValueError("inconsistent idle days")
        if self.alert != aging_alert(self.idle_days):
            raise ValueError("inconsistent alert")
        return self
