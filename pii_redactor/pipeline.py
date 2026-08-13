"""End-to-end run: read a .docx, transform every block, write it back."""

import time
from collections import Counter
from dataclasses import dataclass, field

from .docx_io import iter_blocks, load, save


@dataclass
class RunStats:
    blocks: int = 0
    non_empty_blocks: int = 0
    characters: int = 0
    replacements: int = 0
    by_label: Counter = field(default_factory=Counter)
    seconds: float = 0.0

    def summary(self) -> str:
        lines = [
            f"blocks scanned    : {self.blocks}",
            f"  with text       : {self.non_empty_blocks}",
            f"characters        : {self.characters}",
            f"replacements      : {self.replacements}",
            f"elapsed           : {self.seconds:.1f}s",
        ]
        for label, count in self.by_label.most_common():
            lines.append(f"  {label or 'unlabelled':<16}: {count}")
        return "\n".join(lines)


def run(source, destination, transform, include_headers: bool = True) -> RunStats:
    started = time.perf_counter()
    document = load(source)
    stats = RunStats()

    for block in iter_blocks(document, include_headers=include_headers):
        stats.blocks += 1
        stats.characters += len(block.text)
        if not block.text.strip():
            continue
        stats.non_empty_blocks += 1

        replacements = transform(block)
        if not replacements:
            continue
        applied = block.apply(replacements)
        stats.replacements += len(applied)
        for replacement in applied:
            stats.by_label[replacement.label] += 1

    if destination is not None:
        save(document, destination)

    stats.seconds = time.perf_counter() - started
    return stats
