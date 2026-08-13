import re

from . import register
from .base import RegexRecognizer

# A trailing full stop is sentence punctuation; a trailing ".5" means this is a
# longer dotted number and not an address.
_PATTERN = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)")


@register
class IpAddressRecognizer(RegexRecognizer):
    name = "ip"
    label = "IP_ADDRESS"
    priority = 85
    pattern = _PATTERN

    def validate(self, match) -> bool:
        parts = match.group().split(".")
        return all(part == "0" or not part.startswith("0") for part in parts) and all(
            int(part) <= 255 for part in parts
        )
