import re

from . import register
from .base import RegexRecognizer

# Ranges the SSA never issues are excluded, and the separator must be consistent.
_PATTERN = re.compile(r"\b(?!000|666|9\d{2})\d{3}([- ])(?!00)\d{2}\1(?!0000)\d{4}\b")


@register
class SsnRecognizer(RegexRecognizer):
    name = "ssn"
    label = "SSN"
    priority = 90
    pattern = _PATTERN
