"""Run with: python tests/test_recognizers.py

Negatives are drawn from the real prospectus: money amounts, CINs, page
references, share counts and filing dates are the things that actually cause
false positives in this document.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.engine import RedactionEngine
from pii_redactor.recognizers import build
from pii_redactor.recognizers.credit_card import CreditCardRecognizer, luhn
from pii_redactor.recognizers.dob import DateOfBirthRecognizer
from pii_redactor.recognizers.email import EmailRecognizer
from pii_redactor.recognizers.ip import IpAddressRecognizer
from pii_redactor.recognizers.phone import PhoneRecognizer
from pii_redactor.recognizers.ssn import SsnRecognizer


def found(recognizer, text):
    return [d.text for d in recognizer.find(text)]


def check(recognizer, positives, negatives):
    for text, expected in positives.items():
        assert found(recognizer, text) == expected, f"{text!r} -> {found(recognizer, text)}"
    for text in negatives:
        assert found(recognizer, text) == [], f"false positive in {text!r}"


def test_phone_formats_from_the_document():
    check(
        PhoneRecognizer(),
        {
            "Telephone: + 91 20 45053237": ["+ 91 20 45053237"],
            "Telephone: +91 22 4009 4400": ["+91 22 4009 4400"],
            "Telephone: +91 81081 14949": ["+91 81081 14949"],
            "Telephone: +91-20-26234000": ["+91-20-26234000"],
            "Telephone: + 91 (20) 6729 5100": ["+ 91 (20) 6729 5100"],
            "Telephone: 022-68052182": ["022-68052182"],
            "Telephone: +91 22 30752929, +91 22 30752928": [
                "+91 22 30752929",
                "+91 22 30752928",
            ],
        },
        [
            "aggregating up to ₹4,200.00 million",
            "U28129PN1979PLC141032",
            "see “Offer Structure” on page 417",
            "1,23,45,678 Equity Shares",
            "Dated December 10, 2025",
        ],
    )


def test_ssn_rejects_never_issued_ranges():
    check(
        SsnRecognizer(),
        {"SSN: 123-45-6789": ["123-45-6789"], "SSN 078 05 1120": ["078 05 1120"]},
        [
            "SSN: 000-45-6789",
            "SSN: 666-45-6789",
            "SSN: 900-45-6789",
            "SSN: 123-00-6789",
            "SSN: 123-45-0000",
            "SSN: 123-45 6789",
            "invoice 123-456-7890",
        ],
    )


def test_credit_card_needs_a_valid_checksum():
    check(
        CreditCardRecognizer(),
        {
            "Card: 4532-0151-1283-0366": ["4532-0151-1283-0366"],
            "Card: 4532015112830366": ["4532015112830366"],
            "Card: 4532 0151 1283 0366": ["4532 0151 1283 0366"],
        },
        [
            "Card: 4532-0151-1283-0367",
            "Card: 4532-0151 1283-0366",
            "Telephone: +91 22 30752929",
            "CIN U28129PN1979PLC141032",
        ],
    )


def test_luhn():
    assert luhn("4532015112830366")
    assert not luhn("4532015112830367")


def test_ip_validates_octets():
    check(
        IpAddressRecognizer(),
        {"from 192.168.1.100 at": ["192.168.1.100"], "host 10.0.0.1.": ["10.0.0.1"]},
        ["version 256.1.1.1", "build 1.2.3.4.5", "clause 01.2.3.4", "₹4.200.00.00"],
    )


def test_dob_requires_a_birth_cue():
    check(
        DateOfBirthRecognizer(),
        {
            "DOB: 14/08/2000": ["14/08/2000"],
            "Date of Birth: 14 August 2000": ["14 August 2000"],
            "D.O.B. August 14, 2000": ["August 14, 2000"],
            "born on 1 Jan 1975": ["1 Jan 1975"],
        },
        [
            "Dated December 10, 2025",
            "the agreement dated August 16, 2011",
            "for the year ended March 31, 2024",
            "listed on April 20, 2002",
        ],
    )


def test_dob_cue_does_not_leak_to_later_dates():
    text = "Date of Birth: 14/08/2000. The agreement dated August 16, 2011 applies."
    assert found(DateOfBirthRecognizer(), text) == ["14/08/2000"]


def test_email_still_isolated():
    check(
        EmailRecognizer(),
        {"write to ksh.ipo@nuvama.com now": ["ksh.ipo@nuvama.com"]},
        ["see page 417 @ the office"],
    )


PATTERN_TYPES = ["credit_card", "dob", "email", "ip", "phone", "ssn"]


def test_card_beats_phone_on_a_shared_span():
    engine = RedactionEngine(build(only=PATTERN_TYPES))
    labels = [d.label for d in engine.detect("Card: 4532 0151 1283 0366")]
    assert labels == ["CREDIT_CARD"]


def test_all_types_in_one_pass():
    engine = RedactionEngine(build(only=PATTERN_TYPES))
    text = (
        "Name: John Doe, Email: john.doe@example.com, Telephone: +91 22 4009 4400, "
        "DOB: 14/08/2000, SSN: 123-45-6789, Card: 4532-0151-1283-0366, IP: 192.168.1.100"
    )
    assert [d.label for d in engine.detect(text)] == [
        "EMAIL",
        "PHONE",
        "DATE_OF_BIRTH",
        "SSN",
        "CREDIT_CARD",
        "IP_ADDRESS",
    ]


def test_registry_holds_every_pattern_type():
    assert {r.name for r in build()} >= set(PATTERN_TYPES)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
