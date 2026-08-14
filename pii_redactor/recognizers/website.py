"""Company websites.

Not one of the nine types the assignment lists, and included anyway: company
names are on that list, and www.kshinternational.com is the company's name.
Leaving the address in place undoes the work done on every other mention of the
issuer.
"""

import re

from . import register
from .base import RegexRecognizer

_PATTERN = re.compile(
    r"(?:https?://|www\.)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*(?:/[^\s,;)\]]*)?",
    re.IGNORECASE,
)


@register
class WebsiteRecognizer(RegexRecognizer):
    name = "website"
    label = "URL"
    priority = 75
    pattern = _PATTERN

    def validate(self, match) -> bool:
        # An email address ends in a domain too, and belongs to the email
        # recognizer; anything preceded by an @ is part of one.
        return not match.string[: match.start()].rstrip().endswith("@")
