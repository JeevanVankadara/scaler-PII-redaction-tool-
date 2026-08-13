"""Finds names already known from elsewhere in the document.

The model detects a name in one paragraph and only part of it in another —
"ROHIT KUSHAL HEGDE" came out as "ROHIT" plus a redacted "KUSHAL HEGDE". Once
the full name is known, a plain case-insensitive search closes that gap. Built
at runtime from a first pass, so it is not in the registry.
"""

import re

from .base import Recognizer


class NameGazetteer(Recognizer):
    label = "PERSON"
    priority = 50  # outranks the model, which produced the partial match

    def __init__(self, names, label: str = "PERSON", min_tokens: int = 2):
        self.name = f"gazetteer:{label.lower()}"
        self.label = label
        self.names = sorted(
            {name.strip() for name in names if len(name.split()) >= min_tokens},
            key=len,
            reverse=True,
        )
        self.pattern = self._compile(self.names)

    @staticmethod
    def _compile(names):
        if not names:
            return None
        # Longest first, so "Rohit Kushal Hegde" wins over "Kushal Hegde".
        alternatives = "|".join(re.escape(name).replace(r"\ ", r"\s+") for name in names)
        return re.compile(rf"(?<![A-Za-z]){alternatives}(?![A-Za-z])", re.IGNORECASE)

    def find(self, text: str):
        if self.pattern is None:
            return
        for match in self.pattern.finditer(text):
            yield self.detection(match.start(), match.end(), match.group(), 0.9)

    def __repr__(self) -> str:
        return f"<NameGazetteer {len(self.names)} names>"
