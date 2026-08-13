"""What a recognizer reports when it finds something."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    """One span of a block's text believed to be PII.

    `score` is the recognizer's own confidence. `priority` breaks ties between
    recognizers that claim overlapping spans — a validated credit card should win
    over a phone number that matched the same digits.
    """

    start: int
    end: int
    text: str
    label: str
    recognizer: str = ""
    score: float = 1.0
    priority: int = 0

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Detection") -> bool:
        return self.start < other.end and other.start < self.end

    def __repr__(self) -> str:
        return f"{self.label}[{self.start}:{self.end}]={self.text!r}"
