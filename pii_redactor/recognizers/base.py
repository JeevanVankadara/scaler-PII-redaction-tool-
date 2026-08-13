"""The contract every PII recognizer implements."""

import re
from abc import ABC, abstractmethod

from ..detection import Detection


class Recognizer(ABC):
    """Finds one kind of PII in a string.

    Subclasses set `name` and `label`, then implement `find`. Nothing here knows
    about .docx, runs, or how the value will be replaced.
    """

    name: str = ""
    label: str = ""
    priority: int = 0

    @abstractmethod
    def find(self, text: str):
        """Yield Detections for `text`."""

    def detection(self, start: int, end: int, text: str, score: float = 1.0) -> Detection:
        return Detection(
            start=start,
            end=end,
            text=text,
            label=self.label,
            recognizer=self.name,
            score=score,
            priority=self.priority,
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name}>"


class RegexRecognizer(Recognizer):
    """Recognizer driven by a pattern, with an optional validation hook.

    Subclasses set `pattern`; override `validate` to reject false positives that
    the pattern alone cannot (a Luhn check, a plausible date range) and `score_of`
    when confidence varies by match.
    """

    pattern: "re.Pattern" = None
    group: int = 0

    def find(self, text: str):
        for match in self.pattern.finditer(text):
            if not self.validate(match):
                continue
            yield self.detection(
                match.start(self.group),
                match.end(self.group),
                match.group(self.group),
                self.score_of(match),
            )

    def validate(self, match) -> bool:
        return True

    def score_of(self, match) -> float:
        return 1.0


class ContextualRegexRecognizer(RegexRecognizer):
    """Accepts a match only when a cue word sits just before it.

    Dates are the motivating case: a prospectus is full of them and essentially
    none are dates of birth, so the pattern alone is useless without context.
    """

    context: "re.Pattern" = None
    window: int = 50

    def validate(self, match) -> bool:
        left = max(0, match.start() - self.window)
        return bool(self.context.search(match.string, left, match.start()))
