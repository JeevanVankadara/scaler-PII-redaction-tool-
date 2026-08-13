"""Policies decide what a detected value is replaced with.

The base class memoises per (label, value), so the same person or email gets the
same surrogate everywhere in the document. Subclasses only supply `generate`.
"""

from abc import ABC, abstractmethod

from .detection import Detection


class SurrogatePolicy(ABC):
    def __init__(self):
        self.mapping = {}

    def surrogate(self, detection: Detection) -> str:
        key = (detection.label, detection.text)
        if key not in self.mapping:
            self.mapping[key] = self.generate(detection)
        return self.mapping[key]

    @abstractmethod
    def generate(self, detection: Detection) -> str:
        """Produce a surrogate for a value seen for the first time."""

    def reset(self) -> None:
        self.mapping.clear()


class PlaceholderPolicy(SurrogatePolicy):
    """[EMAIL], [PERSON] — readable, and makes review of a run trivial."""

    def __init__(self, template: str = "[{label}]"):
        super().__init__()
        self.template = template

    def generate(self, detection: Detection) -> str:
        return self.template.format(label=detection.label)


class NumberedPlaceholderPolicy(SurrogatePolicy):
    """[EMAIL_1], [EMAIL_2] — distinct values stay distinguishable.

    Useful for checking that one real person maps to exactly one surrogate.
    """

    def __init__(self):
        super().__init__()
        self._counts = {}

    def generate(self, detection: Detection) -> str:
        index = self._counts.get(detection.label, 0) + 1
        self._counts[detection.label] = index
        return f"[{detection.label}_{index}]"

    def reset(self) -> None:
        super().reset()
        self._counts.clear()
