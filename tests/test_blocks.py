"""Run with: python tests/test_blocks.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.blocks import Replacement, TextBlock, resolve_overlaps


class FakeRun:
    def __init__(self, text):
        self.text = text


def block(*texts):
    return TextBlock([FakeRun(t) for t in texts])


def test_reads_runs_as_one_string():
    assert block("Hello ", "world").text == "Hello world"


def test_replacement_inside_a_single_run():
    b = block("Email: ", "rashi@gmail.com", " (work)")
    b.apply([Replacement(7, 22, "john@example.com")])
    assert b.text == "Email: john@example.com (work)"


def test_replacement_straddling_runs():
    b = block("Rash", "i Pa", "til is here")
    b.apply([Replacement(0, 11, "John Doe")])
    assert b.text == "John Doe is here"


def test_multiple_replacements_keep_offsets_valid():
    b = block("A ", "rashi@x.com", " and ", "rohan@y.com", " done")
    b.apply(
        [
            Replacement(2, 13, "john@example.com"),
            Replacement(18, 29, "peter@example.com"),
        ]
    )
    assert b.text == "A john@example.com and peter@example.com done"


def test_formatting_survives_partial_run_edits():
    runs = [FakeRun("Contact "), FakeRun("Rashi Patil"), FakeRun(" today")]
    b = TextBlock(runs)
    b.apply([Replacement(8, 19, "John Doe")])
    assert [r.text for r in runs] == ["Contact ", "John Doe", " today"]


def test_overlaps_prefer_earliest_then_longest():
    kept = resolve_overlaps(
        [
            Replacement(0, 5, "a"),
            Replacement(0, 9, "b"),
            Replacement(3, 7, "c"),
            Replacement(10, 12, "d"),
        ]
    )
    assert [(r.start, r.end) for r in kept] == [(0, 9), (10, 12)]


def test_empty_block_is_safe():
    b = block("")
    assert b.apply([Replacement(0, 4, "x")]) == []
    assert b.text == ""


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
