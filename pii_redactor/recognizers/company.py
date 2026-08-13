"""Company names by their legal suffix.

The model misses companies on short, label-prefixed lines: it returns nothing at
all for "Company: Acme Technologies Limited", and nothing for the two registrar
names written across a tab. A name ending in Limited, LLP or Private Limited is
a company by construction, so the pattern does not need the model's help.
"""

import re

from . import register
from .base import RegexRecognizer
from .vocab import GEO_KEEP, all_generic, has_place_word, is_institution, words_of

_PATTERN = re.compile(
    r"\b(?:(?:[A-Z][\w.'’-]*|&)[ \t]+){1,5}"
    r"(?i:private[ \t]+)?"
    r"(?i:limited|ltd\.?|llp|plc|inc\.?|corporation)\b"
)


# Capitalised words that introduce a company name without being part of it.
_LEADING = {"formerly", "erstwhile", "our", "the", "and", "by", "at", "from", "to", "with"}


@register
class CompanyRecognizer(RegexRecognizer):
    name = "company"
    label = "ORGANIZATION"
    priority = 55
    pattern = _PATTERN

    def find(self, text: str):
        for detection in super().find(text):
            yield self._trim_lead(detection)

    def _trim_lead(self, detection):
        value, start = detection.text, detection.start
        while True:
            head, _, rest = value.partition(" ")
            if not rest or head.strip().lower() not in _LEADING:
                break
            start += len(value) - len(rest.lstrip())
            value = rest.lstrip()
        if value == detection.text:
            return detection
        return self.detection(start, start + len(value), value, detection.score)

    def validate(self, match) -> bool:
        value = match.group()
        if all_generic(value) or is_institution(value) or has_place_word(value):
            return False
        # "National Stock Exchange of India Limited" stops the pattern at the
        # lowercase "of" and leaves "India Limited", which names nobody.
        return not set(words_of(value)) <= GEO_KEEP | {"private", "limited", "ltd"}
