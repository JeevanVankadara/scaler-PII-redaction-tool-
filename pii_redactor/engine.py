"""Runs every recognizer over a block, settles conflicts, emits Replacements."""

from .blocks import Replacement
from .detection import Detection
from .policies import PlaceholderPolicy, SurrogatePolicy
from .recognizers import build


class RedactionEngine:
    """Callable, so it drops straight into the pipeline as a transform."""

    def __init__(self, recognizers=None, policy: SurrogatePolicy = None, min_score: float = 0.0):
        self.recognizers = list(recognizers) if recognizers is not None else build()
        self.policy = policy or PlaceholderPolicy()
        self.min_score = min_score

    def detect(self, text: str):
        """All detections for `text`, overlaps settled, in document order."""
        found = []
        for recognizer in self.recognizers:
            for detection in recognizer.find(text):
                if detection.score >= self.min_score:
                    found.append(detection)
        return resolve(found)

    def redact(self, block):
        replacements = []
        for detection in self.detect(block.text):
            surrogate = self.policy.surrogate(detection)
            if surrogate != detection.text:
                replacements.append(
                    Replacement(detection.start, detection.end, surrogate, detection.label)
                )
        return replacements

    def __call__(self, block):
        return self.redact(block)

    def __repr__(self) -> str:
        names = ", ".join(r.name for r in self.recognizers)
        return f"<RedactionEngine [{names}]>"


def resolve(detections):
    """Keep the strongest claim on each span: priority, then score, then length.

    Two recognizers matching the same characters is normal — a phone pattern and
    a credit card pattern both like long digit runs. Only one can be replaced.
    """
    ranked = sorted(
        detections,
        key=lambda d: (-d.priority, -d.score, -d.length, d.start),
    )
    kept = []
    for detection in ranked:
        if detection.length > 0 and not any(detection.overlaps(k) for k in kept):
            kept.append(detection)
    return sorted(kept, key=lambda d: d.start)
