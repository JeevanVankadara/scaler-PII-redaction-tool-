import re

from . import register
from .base import RegexRecognizer

_PATTERN = re.compile(r"(?<![\d-])(?:\d[ -]?){12,18}\d(?!\d)")


def luhn(digits: str) -> bool:
    total = 0
    for index, character in enumerate(reversed(digits)):
        digit = int(character)
        if index % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


@register
class CreditCardRecognizer(RegexRecognizer):
    """Any long digit run is a candidate; Luhn is what makes it a card.

    Without the checksum this pattern would swallow phone numbers, CINs and
    share counts. With it, a false positive needs a 1-in-10 coincidence.
    """

    name = "credit_card"
    label = "CREDIT_CARD"
    priority = 95
    pattern = _PATTERN

    def validate(self, match) -> bool:
        value = match.group()
        if match.string[: match.start()].rstrip().endswith("+"):
            return False

        digits = "".join(character for character in value if character.isdigit())
        if not 13 <= len(digits) <= 19:
            return False
        if len({character for character in value if not character.isdigit()}) > 1:
            return False
        return luhn(digits)
