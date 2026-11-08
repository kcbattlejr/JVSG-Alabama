"""Scrubber unit tests on invented text only."""

import pytest

from jvsg_triage.etl.models import RedactionLexicon
from jvsg_triage.privacy.scrubber import NAME_STOPWORDS, Redactor, Span, merge_spans

LEXICON = RedactionLexicon(
    person_names=frozenset({"Okafor-Vale, Tamsin", "Hope, Brannagh", "Van Dunmore, Corin"}),
    staff_names=frozenset({"Quintavalle, Jr., Ferris"}),
    identifiers=frozenset({"9912345", "9634567"}),
)
REDACTOR = Redactor(LEXICON)


def scrub(text: str, own: tuple[str, ...] = ()) -> str:
    return REDACTOR.redact(text, own)[0]


@pytest.mark.parametrize(("text", "placeholder"), [
    ("reach me at tamsin.v@example.org today", "[EMAIL]"),
    ("see https://www.example.gov/jobs?id=4 now", "[URL]"),
    ("SSN 900-12-3456 on file", "[SSN]"),
    ("call (251) 555-0147 ext 12", "[PHONE]"),
    ("call 251.555.0147", "[PHONE]"),
    ("call 555-0147", "[PHONE]"),
    ("on 03/14/2026", "[DATE]"),
    ("on 3/4/26", "[DATE]"),
    ("on March 14, 2026", "[DATE]"),
    ("on Sept. 3", "[DATE]"),
    ("on 14th March", "[DATE]"),
    ("lives at 1234 Magnolia Bend Rd, Apt 4B now", "[ADDRESS]"),
    ("mail to PO Box 812", "[ADDRESS]"),
    ("Mobile, AL 36695-1234", "[ZIP]"),
    ("Mobile, Alabama 36695", "[ZIP]"),
    ("claim # 44719823", "[ID]"),
    ("SID 9912345", "[ID]"),
])
def test_structured_pii_is_replaced(text: str, placeholder: str) -> None:
    out = scrub(text)
    assert placeholder in out
    assert not any(char.isdigit() for char in out.split(placeholder)[0][-3:])


def test_ordinary_numbers_survive() -> None:
    assert scrub("worked 12 years, 3 kids, 40 hours") == "worked 12 years, 3 kids, 40 hours"


def test_own_row_names_any_case_including_short_and_hyphenated_parts() -> None:
    out = scrub("tamsin and OKAFOR-VALE and vale met", own=("Okafor-Vale, Tamsin",))
    assert out == "[NAME] and [NAME] and [NAME] met"


def test_global_names_only_when_capitalized() -> None:
    assert scrub("Spoke with Corin Dunmore today") == "Spoke with [NAME] [NAME] today"
    assert scrub("the dunmore file") == "the dunmore file"


def test_stopwords_survive_global_pass_but_not_own_row() -> None:
    assert "hope" in NAME_STOPWORDS
    assert scrub("Hope you are well") == "Hope you are well"
    assert scrub("Hope you are well", own=("Hope, Brannagh",)) == "[NAME] you are well"


def test_staff_names_and_honorifics() -> None:
    assert scrub("Ferris Quintavalle\nDVOP") == "[STAFF] [STAFF]\nDVOP"
    assert scrub("Spoke with Ms. Penhallow at legal aid") == "Spoke with Ms. [NAME] at legal aid"


def test_name_inside_email_is_one_email_span() -> None:
    out, counts = REDACTOR.redact("tamsin.okafor-vale@example.org", ("Okafor-Vale, Tamsin",))
    assert out == "[EMAIL]"
    assert counts == {"EMAIL": 1}


def test_merge_keeps_union_and_priority_label() -> None:
    merged = merge_spans([Span(0, 5, "NAME"), Span(3, 10, "EMAIL"), Span(12, 14, "ID")])
    assert merged == [Span(0, 10, "EMAIL"), Span(12, 14, "ID")]


def test_residual_scan_ignores_placeholders_and_flags_leaks() -> None:
    clean = scrub("Called Corin at 251-555-0101 on 1/2/2026")
    assert REDACTOR.residual(clean) == {}
    assert REDACTOR.residual("Leaked Dunmore at 251-555-0101") == {
        "LEXICON_NAME": 1, "PHONE": 1,
    }


def test_third_party_name_without_honorific_is_a_documented_gap() -> None:
    assert "Rowena Ashcombe" in scrub("Referred to Rowena Ashcombe at SSVF")
