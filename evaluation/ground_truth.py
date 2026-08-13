"""Loading and validating hand-written ground truth.

Run directly to check every annotation still lines up with the document:

    python evaluation/ground_truth.py

An annotation that no longer occurs in its block means the file drifted from the
document, and any evaluation built on it would be quietly wrong.
"""

import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pii_redactor.docx_io import iter_blocks, load

DEFAULT_FILES = ("ground_truth.json", "ground_truth_synthetic.json")


@dataclass(frozen=True)
class Annotation:
    block: int
    label: str
    text: str


class GroundTruth:
    def __init__(self, path):
        self.path = Path(path)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.source = ROOT / data["source"]
        self.sample = data["sample"]
        self.conventions = data["conventions"]
        scope = data["scope"]
        self.first_block = scope["first_block"]
        self.last_block = scope["last_block"]
        self.annotations = [
            Annotation(entry["block"], label, text)
            for entry in data["annotations"]
            for label, text in entry["items"]
        ]

    @property
    def blocks_annotated(self):
        return {annotation.block for annotation in self.annotations}

    def in_scope(self, index: int) -> bool:
        """Blocks that were read. Detections outside this range cannot be scored."""
        return self.first_block <= index <= self.last_block

    def scored_blocks(self):
        """(index, text) for every block that was read, annotated or not."""
        return [
            (index, text)
            for index, text in enumerate(self.document_blocks())
            if self.in_scope(index) and text.strip()
        ]

    def by_label(self) -> Counter:
        return Counter(annotation.label for annotation in self.annotations)

    def document_blocks(self):
        return [block.text for block in iter_blocks(load(self.source))]

    def validate(self):
        """Return a list of problems; empty means the file matches the document."""
        blocks = self.document_blocks()
        problems = []
        wanted = Counter((a.block, a.text) for a in self.annotations)

        for (index, text), expected in sorted(wanted.items()):
            if index >= len(blocks):
                problems.append(f"block {index} does not exist ({len(blocks)} blocks)")
                continue
            if not self.in_scope(index):
                problems.append(f"block {index} is annotated but outside the stated scope")
                continue
            actual = blocks[index].count(text)
            if actual < expected:
                problems.append(
                    f"block {index}: {text!r} annotated {expected}x, found {actual}x"
                )
        return problems


def main(paths):
    failed = False
    for path in paths:
        truth = GroundTruth(path)
        problems = truth.validate()
        labels = truth.by_label()

        print(f"=== {truth.path.name}")
        print(f"  source     : {truth.source.name}")
        print(f"  sample     : {truth.sample}")
        scored = truth.scored_blocks()
        print(f"  blocks read: {len(scored)} with text, of which {len(truth.blocks_annotated)} carry PII")
        print(f"  annotations: {len(truth.annotations)}")
        for label, count in labels.most_common():
            print(f"    {label:<14} {count}")
        if problems:
            failed = True
            print(f"  PROBLEMS ({len(problems)}):")
            for problem in problems:
                print(f"    {problem}")
        else:
            print("  validated  : every annotation found in its block")
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    given = sys.argv[1:] or [Path(__file__).parent / name for name in DEFAULT_FILES]
    raise SystemExit(main(given))
