import re

from . import register
from .base import RegexRecognizer
from .vocab import PLACE_WORDS, words_of

# Trailing comma is allowed: an address almost always continues "410 501,
# Maharashtra". Only a following digit means this is part of a longer number.
_PATTERN = re.compile(r"(?<![\d,.])[1-9]\d{2}\s?\d{3}(?!\d)")

# A six digit number is only a postal code if it sits in something that reads
# like an address, so the whole block has to carry an address word.
_CUES = PLACE_WORDS | {"india", "maharashtra", "pin", "pincode", "office", "registered"}


@register
class PostalCodeRecognizer(RegexRecognizer):
    """Indian PIN codes, written as 410501 or 410 501.

    Labelled LOCATION rather than given its own type: a postal code is part of a
    mailing address, and the ground truth annotates it that way.
    """

    name = "postal_code"
    label = "LOCATION"
    priority = 65
    pattern = _PATTERN

    def validate(self, match) -> bool:
        return bool(set(words_of(match.string)) & _CUES)
