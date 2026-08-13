import re

from . import register
from .base import RegexRecognizer

# Formats seen in the source document: "+ 91 20 45053237", "+91 22 4009 4400",
# "+91 81081 14949", "+91-20-26234000", "+ 91 (20) 6729 5100", "022-68052182".
_PATTERN = re.compile(
    r"""
    (?<![\d.])
    (?:
        \+\s?\d{1,3}[\s./-]?(?:\(\d{1,5}\)|\d{1,5})(?:[\s./-]?\d{2,10}){1,3}
      | 0\d{2,4}[\s./-]\d{6,8}
    )
    (?!\d)
    """,
    re.VERBOSE,
)


@register
class PhoneRecognizer(RegexRecognizer):
    name = "phone"
    label = "PHONE"
    priority = 70
    pattern = _PATTERN
    min_digits = 9
    max_digits = 15

    def validate(self, match) -> bool:
        digits = sum(character.isdigit() for character in match.group())
        return self.min_digits <= digits <= self.max_digits
