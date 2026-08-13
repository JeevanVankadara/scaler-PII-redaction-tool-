"""Text blocks and the span-replacement machinery the whole pipeline is built on."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Replacement:
    """A character span of a block's text to swap for something else."""

    start: int
    end: int
    text: str
    label: str = ""

    @property
    def length(self) -> int:
        return self.end - self.start


class TextBlock:
    """One paragraph, exposed as flat text with edits mapped back onto its runs.

    A paragraph's text is split across runs at arbitrary points, so a match can
    straddle several of them. Rewriting the paragraph wholesale would flatten its
    formatting, so edits are pushed back into the individual runs instead.
    """

    def __init__(self, runs, location: str = ""):
        self._runs = list(runs)
        self.location = location
        self._reindex()

    def _reindex(self) -> None:
        self._spans = []
        cursor = 0
        for run in self._runs:
            length = len(run.text)
            self._spans.append((cursor, cursor + length))
            cursor += length
        self.text = "".join(run.text for run in self._runs)

    def apply(self, replacements):
        """Apply replacements right-to-left so earlier offsets stay valid.

        Returns the replacements that actually landed, overlaps discarded.
        """
        resolved = resolve_overlaps(replacements)
        applied = [r for r in reversed(resolved) if self._apply_one(r)]
        if applied:
            self._reindex()
        return applied[::-1]

    def _apply_one(self, replacement: Replacement) -> bool:
        touched = [
            index
            for index, (start, end) in enumerate(self._spans)
            if start < replacement.end and end > replacement.start
        ]
        if not touched:
            return False

        # The new text lands entirely in the first run; the rest keep only their tails.
        for position, index in enumerate(touched):
            start, _ = self._spans[index]
            original = self._runs[index].text
            head = original[: _clamp(replacement.start - start, len(original))]
            tail = original[_clamp(replacement.end - start, len(original)) :]
            insert = replacement.text if position == 0 else ""
            self._runs[index].text = head + insert + tail
        return True

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return f"TextBlock({self.location!r}, {preview!r})"


def resolve_overlaps(replacements):
    """Drop overlapping replacements, preferring the earliest then the longest."""
    ordered = sorted(replacements, key=lambda r: (r.start, -r.length))
    kept = []
    boundary = -1
    for replacement in ordered:
        if replacement.start >= boundary and replacement.length > 0:
            kept.append(replacement)
            boundary = replacement.end
    return kept


def _clamp(value: int, limit: int) -> int:
    return max(0, min(value, limit))
