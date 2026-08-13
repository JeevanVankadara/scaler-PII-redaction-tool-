import re

from . import register
from .base import ContextualRegexRecognizer

_MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

_PATTERN = re.compile(
    rf"""
    \b(?:
        \d{{1,2}}[/.-]\d{{1,2}}[/.-]\d{{2,4}}
      | {_MONTH}\s+\d{{1,2}},?\s+\d{{4}}
      | \d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTH},?\s+\d{{4}}
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

_CONTEXT = re.compile(
    r"(?:date\s+of\s+birth|\bd\.?o\.?b\b\.?|born(?:\s+on)?|birth\s*date)[^A-Za-z0-9]{0,12}$",
    re.IGNORECASE,
)


@register
class DateOfBirthRecognizer(ContextualRegexRecognizer):
    """Only a date introduced by a birth cue counts.

    The sample prospectus holds 276 dates and not one is a date of birth, so an
    ungated date pattern would be almost pure false positive. The cost is that a
    birth date stated with no nearby cue is missed — a deliberate trade of recall
    for precision, since redacting every date would destroy the document.
    """

    name = "dob"
    label = "DATE_OF_BIRTH"
    priority = 60
    pattern = _PATTERN
    context = _CONTEXT
    window = 50

    def score_of(self, match) -> float:
        return 0.9
