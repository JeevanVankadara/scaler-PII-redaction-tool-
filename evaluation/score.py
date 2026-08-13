"""Scores the tool against the hand-written ground truth.

    python evaluation/score.py                 # both annotation sets
    python evaluation/score.py --single-pass   # without the name-linking pass
    python evaluation/score.py --json results.json

Two scores are reported for each run. The typed score requires the tool to agree
with the annotation about which kind of PII a span is. The untyped score only
asks whether the span was redacted at all. They differ because spaCy moves names
between PERSON and ORG freely, and a name replaced with a company name is still
a name that left the document.
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.ground_truth import DEFAULT_FILES, GroundTruth
from pii_redactor.engine import RedactionEngine
from pii_redactor.recognizers import build
from pii_redactor.transforms import link_names


@dataclass
class Counts:
    """Spans are scored by coverage, in both directions separately.

    Annotation granularity and detection granularity do not have to agree. The
    tool emits "Chakan Taluka - Khed" as one span where the ground truth lists
    "Chakan" and "Khed" as two, and one-to-one matching would score that as one
    hit and one miss even though both places left the document. So recall asks
    whether each annotated span is covered by some detection, and precision asks
    whether each detection overlaps some annotation. The two hit counts differ,
    and both are printed rather than collapsed into a single TP.
    """

    covered: int = 0  # annotated spans some detection overlapped
    matched: int = 0  # detections that overlapped some annotation
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def true_positives(self) -> int:
        return self.covered

    @property
    def precision(self) -> float:
        found = self.matched + self.false_positives
        return self.matched / found if found else 0.0

    @property
    def recall(self) -> float:
        actual = self.covered + self.false_negatives
        return self.covered / actual if actual else 0.0

    @property
    def f1(self) -> float:
        total = self.precision + self.recall
        return 2 * self.precision * self.recall / total if total else 0.0

    @property
    def accuracy(self) -> float:
        """(covered + matched) / (annotated + detected).

        There is no meaningful count of true negatives when the task is finding
        spans in free text, so the textbook accuracy formula does not apply. This
        is the share of all spans, annotated and detected, that were accounted
        for on both sides. The definition is stated here rather than left for the
        reader to guess.
        """
        total = self.covered + self.false_negatives + self.matched + self.false_positives
        return (self.covered + self.matched) / total if total else 0.0


@dataclass
class Result:
    typed: dict = field(default_factory=lambda: defaultdict(Counts))
    untyped: Counts = field(default_factory=Counts)
    missed: list = field(default_factory=list)
    spurious: list = field(default_factory=list)

    @property
    def overall(self) -> Counts:
        total = Counts()
        for counts in self.typed.values():
            total.covered += counts.covered
            total.matched += counts.matched
            total.false_positives += counts.false_positives
            total.false_negatives += counts.false_negatives
        return total


def expected_spans(text: str, items):
    """Locate each annotation in the block, honouring repeats of the same value."""
    spans, cursor = [], {}
    for annotation in items:
        value = annotation.text
        start = text.find(value, cursor.get(value, 0))
        if start < 0:
            start = text.find(value)
        cursor[value] = start + len(value)
        spans.append((start, start + len(value), annotation.label, value))
    return spans


def overlaps(left, right) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def cover(expected, predicted, typed: bool, strict: bool = False):
    """Which annotations were covered, and which detections landed on something.

    Many-to-one is allowed in both directions: one detection may cover several
    annotations, and one annotation may be covered by several detections.
    `strict` restores greedy one-to-one pairing, which is available so the effect
    of that choice can be measured rather than asserted.
    """
    if strict:
        return _pair_one_to_one(expected, predicted, typed)

    covered = {
        index
        for index, span in enumerate(expected)
        if any(
            overlaps(span, other) and (not typed or span[2] == other[2])
            for other in predicted
        )
    }
    matched = {
        index
        for index, span in enumerate(predicted)
        if any(
            overlaps(span, other) and (not typed or span[2] == other[2])
            for other in expected
        )
    }
    return covered, matched


def _pair_one_to_one(expected, predicted, typed: bool):
    taken, covered = set(), set()
    for index, span in enumerate(expected):
        for other, candidate in enumerate(predicted):
            if other in taken or (typed and span[2] != candidate[2]):
                continue
            if overlaps(span, candidate):
                taken.add(other)
                covered.add(index)
                break
    return covered, taken


def evaluate(truth: GroundTruth, engine: RedactionEngine, strict: bool = False) -> Result:
    by_block = defaultdict(list)
    for annotation in truth.annotations:
        by_block[annotation.block].append(annotation)

    result = Result()
    for index, text in truth.scored_blocks():
        expected = expected_spans(text, by_block.get(index, []))
        predicted = [
            (d.start, d.end, d.label, d.text) for d in engine.detect(text)
        ]

        covered, matched = cover(expected, predicted, typed=True, strict=strict)
        for position, span in enumerate(expected):
            if position in covered:
                result.typed[span[2]].covered += 1
            else:
                result.typed[span[2]].false_negatives += 1
                result.missed.append((index, span[2], span[3]))
        for position, span in enumerate(predicted):
            if position in matched:
                result.typed[span[2]].matched += 1
            else:
                result.typed[span[2]].false_positives += 1
                result.spurious.append((index, span[2], span[3]))

        loose_covered, loose_matched = cover(expected, predicted, typed=False, strict=strict)
        result.untyped.covered += len(loose_covered)
        result.untyped.matched += len(loose_matched)
        result.untyped.false_negatives += len(expected) - len(loose_covered)
        result.untyped.false_positives += len(predicted) - len(loose_matched)

    return result


def format_table(result: Result) -> str:
    columns = (
        f"{'type':<16}{'cover':>6}{'miss':>6}{'match':>6}{'spur':>6}"
        f"{'prec':>9}{'recall':>9}{'F1':>9}"
    )
    lines = [columns, "-" * len(columns)]

    def row(name, counts):
        return (
            f"{name:<16}{counts.covered:>6}{counts.false_negatives:>6}"
            f"{counts.matched:>6}{counts.false_positives:>6}"
            f"{counts.precision:>9.3f}{counts.recall:>9.3f}{counts.f1:>9.3f}"
        )

    for label in sorted(result.typed):
        lines.append(row(label, result.typed[label]))
    lines.append("-" * len(columns))
    lines.append(row("TYPED TOTAL", result.overall))
    lines.append(row("REDACTED AT ALL", result.untyped))
    lines.append("")
    lines.append(
        f"accuracy (covered+matched)/(annotated+detected): "
        f"typed {result.overall.accuracy:.3f}, untyped {result.untyped.accuracy:.3f}"
    )
    return "\n".join(lines)


def build_engine(source, single_pass: bool):
    engine = RedactionEngine(build())
    if not single_pass:
        link_names(source, engine)
    return engine


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Score the redactor against ground truth.")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--single-pass", action="store_true")
    parser.add_argument(
        "--strict-pairing",
        action="store_true",
        help="score with one-to-one span matching instead of coverage",
    )
    parser.add_argument("--json", type=Path, help="write the raw numbers to a file")
    parser.add_argument("--errors", type=int, default=15, help="how many misses to list")
    args = parser.parse_args(argv)

    paths = args.files or [Path(__file__).parent / name for name in DEFAULT_FILES]
    payload = {}

    for path in paths:
        truth = GroundTruth(path)
        engine = build_engine(truth.source, args.single_pass)
        result = evaluate(truth, engine, strict=args.strict_pairing)

        print(f"=== {truth.path.name}  ({truth.sample})")
        print(f"    linking pass: {'off' if args.single_pass else 'on'}")
        print(format_table(result))

        if result.missed:
            print(f"\n  missed ({len(result.missed)}):")
            for block, label, value in result.missed[: args.errors]:
                print(f"    block {block:<5} {label:<14} {value!r}")
        if result.spurious:
            print(f"\n  false positives ({len(result.spurious)}):")
            for block, label, value in result.spurious[: args.errors]:
                print(f"    block {block:<5} {label:<14} {value!r}")
        print()

        payload[truth.path.name] = {
            "sample": truth.sample,
            "single_pass": args.single_pass,
            "typed": {
                label: {
                    "covered": counts.covered,
                    "matched": counts.matched,
                    "fp": counts.false_positives,
                    "fn": counts.false_negatives,
                    "precision": round(counts.precision, 4),
                    "recall": round(counts.recall, 4),
                    "f1": round(counts.f1, 4),
                }
                for label, counts in sorted(result.typed.items())
            },
            "overall": {
                "precision": round(result.overall.precision, 4),
                "recall": round(result.overall.recall, 4),
                "f1": round(result.overall.f1, 4),
                "accuracy": round(result.overall.accuracy, 4),
            },
            "untyped": {
                "precision": round(result.untyped.precision, 4),
                "recall": round(result.untyped.recall, 4),
                "f1": round(result.untyped.f1, 4),
                "accuracy": round(result.untyped.accuracy, 4),
            },
            "missed": [list(row) for row in result.missed],
            "false_positives": [list(row) for row in result.spurious],
        }

    if args.json:
        args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
