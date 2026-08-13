"""Fake values that keep the shape of what they replace.

A redacted document should still read like a document: "+ 91 20 45053237" is
replaced by something that still looks like a Pune landline, not by a token. Every
generator is seeded from the original value, so a run is reproducible and does
not depend on the order values were encountered in.
"""

import random
import re

from .identities import seed_for

_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_MONTH_NAME = re.compile(r"[A-Za-z]{3,}")
_NUMERIC_DATE = re.compile(r"^(\d{1,2})([/.-])(\d{1,2})\2(\d{2,4})$")


def rng(value: str) -> random.Random:
    return random.Random(seed_for(value))


def match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original.islower():
        return replacement.lower()
    return replacement


def fake_phone(original: str) -> str:
    """Keep punctuation and the country code; randomise the subscriber digits.

    "+ 91 20 45053237" stays a +91 number with the same spacing, which is what
    the assignment's own example does.
    """
    random_source = rng(original)
    keep = 2 if original.lstrip().startswith("+") else 0
    seen = 0
    out = []
    for character in original:
        if not character.isdigit():
            out.append(character)
            continue
        seen += 1
        out.append(character if seen <= keep else str(random_source.randint(0, 9)))
    return "".join(out)


def fake_date(original: str) -> str:
    """A plausible birth date in the same format as the one found."""
    random_source = rng(original)
    day, month, year = (
        random_source.randint(1, 28),
        random_source.randint(1, 12),
        random_source.randint(1950, 2000),
    )

    numeric = _NUMERIC_DATE.match(original.strip())
    if numeric:
        first, separator, second, last = numeric.groups()
        return separator.join(
            [
                f"{day:0{len(first)}d}",
                f"{month:0{len(second)}d}",
                str(year) if len(last) > 2 else f"{year % 100:02d}",
            ]
        )

    name = _MONTHS[month - 1]
    if _MONTH_NAME.search(original.strip()[:3]):
        return f"{name} {day}, {year}"
    return f"{day} {name} {year}"


def fake_ssn(original: str) -> str:
    random_source = rng(original)
    separator = next((c for c in original if not c.isdigit()), "-")
    area = random_source.randint(1, 665)
    return f"{area:03d}{separator}{random_source.randint(1, 99):02d}{separator}{random_source.randint(1, 9999):04d}"


def fake_card(original: str) -> str:
    """A 16-digit number that passes Luhn, grouped like the original."""
    random_source = rng(original)
    separator = next((c for c in original if not c.isdigit()), "")
    body = [random_source.randint(0, 9) for _ in range(15)]
    body[0] = 4
    digits = "".join(str(digit) for digit in body)
    digits += str(_luhn_check_digit(digits))
    groups = [digits[index : index + 4] for index in range(0, 16, 4)]
    return separator.join(groups) if separator else digits


def _luhn_check_digit(digits: str) -> int:
    total = 0
    for index, character in enumerate(reversed(digits)):
        digit = int(character)
        if index % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return (10 - total % 10) % 10


def fake_ip(original: str) -> str:
    random_source = rng(original)
    return ".".join(str(random_source.randint(1, 254)) for _ in range(4))
