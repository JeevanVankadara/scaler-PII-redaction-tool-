import re

from . import register
from .base import RegexRecognizer


@register
class EmailRecognizer(RegexRecognizer):
    name = "email"
    label = "EMAIL"
    priority = 80
    pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
