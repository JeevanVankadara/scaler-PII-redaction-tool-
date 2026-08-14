"""Run with: python tests/test_identities.py"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.blocks import TextBlock
from pii_redactor.detection import Detection
from pii_redactor.engine import RedactionEngine
from pii_redactor.identities import IdentityRegistry, signature
from pii_redactor.policies import FakeIdentityPolicy
from pii_redactor.recognizers import build
from pii_redactor.recognizers.credit_card import luhn
from pii_redactor.surrogates import (
    digits_of,
    fake_card,
    fake_date,
    fake_ip,
    fake_phone,
    fake_ssn,
    match_case,
)


class FakeRun:
    def __init__(self, text):
        self.text = text


def block(*texts):
    return TextBlock([FakeRun(t) for t in texts])


def surrogate(policy, label, value):
    return policy.surrogate(Detection(0, len(value), value, label))


def test_signature_ignores_punctuation_case_and_digits():
    # The registry signs the local part of an address, never the domain.
    assert signature("Sarthak Malvadkar") == signature("Sarthak.malvadkar")
    assert signature("pravin.teli2") == {"pravin", "teli"}


def test_a_person_keeps_one_identity():
    registry = IdentityRegistry()
    first = registry.for_name("Rashi Patil")
    assert registry.for_name("Rashi Patil") is first
    assert registry.for_name("Rashi Patil").full == first.full


def test_email_follows_the_person():
    registry = IdentityRegistry()
    person = registry.for_name("Rashi Patil")
    linked = registry.for_email("rashi.patil@gmail.com")
    assert linked is person
    assert linked.email == f"{person.first}.{person.last}@example.com".lower()


def test_linking_works_in_either_order():
    from_email = IdentityRegistry()
    from_email.for_email("rashi.patil@gmail.com")
    assert from_email.for_name("Rashi Patil").full == from_email.for_email(
        "rashi.patil@gmail.com"
    ).full


def test_short_form_links_to_a_single_full_name():
    registry = IdentityRegistry()
    full = registry.for_name("Kushal Subbayya Hegde")
    assert registry.for_name("Kushal Hegde") is full


def test_ambiguous_short_form_stays_separate():
    """Kushal Hegde is inside two different people's names — guessing is worse."""
    registry = IdentityRegistry()
    registry.for_name("Kushal Subbayya Hegde")
    registry.for_name("Rajesh Kushal Hegde")
    short = registry.for_name("Kushal Hegde")
    assert short.full not in {
        registry.for_name("Kushal Subbayya Hegde").full,
        registry.for_name("Rajesh Kushal Hegde").full,
    }


def test_different_people_get_different_identities():
    registry = IdentityRegistry()
    names = ["Rajesh Kushal Hegde", "Pushpa Kushal Hegde", "Rohit Kushal Hegde"]
    identities = {registry.for_name(name).full for name in names}
    assert len(identities) == 3


def test_output_is_reproducible():
    assert IdentityRegistry().for_name("Rashi Patil").full == (
        IdentityRegistry().for_name("Rashi Patil").full
    )
    assert fake_phone("+91 22 4009 4400") == fake_phone("+91 22 4009 4400")


def test_phone_keeps_shape_and_country_code():
    for original in ["+ 91 20 45053237", "+91-20-26234000", "022-68052182"]:
        result = fake_phone(original)
        assert len(result) == len(original)
        assert [c.isdigit() for c in result] == [c.isdigit() for c in original]
        assert result != original
    assert fake_phone("+91 9876543210").startswith("+91 ")


def test_one_number_written_two_ways_gets_one_replacement():
    """The document writes the same office number with and without a space.

    Seeded from the literal these came out as two different numbers, which reads
    as two offices. The replacement now follows the digits, not the spelling.
    """
    spaced, unspaced = fake_phone("+ 91 20 4505 3237"), fake_phone("+ 91 20 45053237")
    assert digits_of(spaced) == digits_of(unspaced)
    assert spaced != unspaced  # each keeps its own spacing


def test_phone_variants_agree_through_the_policy():
    policy = FakeIdentityPolicy()
    first = surrogate(policy, "PHONE", "+91 22 4009 4400")
    second = surrogate(policy, "PHONE", "+91 22 40094400")
    assert digits_of(first) == digits_of(second)


def test_websites_become_a_fake_domain():
    policy = FakeIdentityPolicy()
    for original in ["www.kshinternational.com", "https://kshinternational.com/investors"]:
        assert "kshinternational" not in surrogate(policy, "URL", original)
    assert surrogate(policy, "URL", "www.kshinternational.com").startswith("www.")
    assert surrogate(policy, "URL", "https://kshinternational.com/x").startswith("https://")


def test_dates_keep_their_format():
    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", fake_date("14/08/2000"))
    assert re.fullmatch(r"[A-Z][a-z]+ \d{1,2}, \d{4}", fake_date("August 14, 2000"))
    assert re.fullmatch(r"\d{1,2} [A-Z][a-z]+ \d{4}", fake_date("14 August 2000"))


def test_generated_card_passes_luhn():
    result = fake_card("4532-0151-1283-0366")
    assert re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{4}", result)
    assert luhn(result.replace("-", ""))
    assert result != "4532-0151-1283-0366"


def test_postal_codes_stay_postal_codes():
    """A PIN replaced by a city name reads as a bug in the output."""
    policy = FakeIdentityPolicy()
    assert re.fullmatch(r"[1-9]\d{2} \d{3}", surrogate(policy, "LOCATION", "410 501"))
    assert re.fullmatch(r"[1-9]\d{5}", surrogate(policy, "LOCATION", "411001"))
    named = surrogate(policy, "LOCATION", "Pune")
    assert named and not any(character.isdigit() for character in named)


def test_ssn_and_ip_keep_their_shape():
    assert re.fullmatch(r"\d{3}-\d{2}-\d{4}", fake_ssn("123-45-6789"))
    assert re.fullmatch(r"\d{3} \d{2} \d{4}", fake_ssn("078 05 1120"))
    octets = [int(part) for part in fake_ip("192.168.1.100").split(".")]
    assert len(octets) == 4 and all(0 < octet < 255 for octet in octets)


def test_case_is_preserved():
    assert match_case("KUSHAL HEGDE", "John Doe") == "JOHN DOE"
    assert match_case("Kushal Hegde", "John Doe") == "John Doe"


def test_policy_replaces_a_whole_block_consistently():
    policy = FakeIdentityPolicy()
    name = surrogate(policy, "PERSON", "Rashi Patil")
    email = surrogate(policy, "EMAIL", "rashi.patil@gmail.com")
    first, last = name.split()
    assert email == f"{first}.{last}@example.com".lower()
    assert surrogate(policy, "PERSON", "Rashi Patil") == name


def test_the_assignment_example_end_to_end():
    """Rashi Patil -> John Doe, and her email follows her."""
    engine = RedactionEngine(build(only=["email", "person", "phone"]), FakeIdentityPolicy())
    b = block("Rashi Patil, ", "rashi.patil@gmail.com", ", +91 9876543210")
    b.apply(engine.redact(b))

    assert "rashi" not in b.text.lower()
    assert "9876543210" not in b.text

    name, email = b.text.split(",")[0].strip(), b.text.split(",")[1].strip()
    assert email == f"{name.replace(' ', '.')}@example.com".lower()
    assert b.text.split(",")[2].strip().startswith("+91 ")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
