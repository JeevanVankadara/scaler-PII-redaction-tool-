"""Run with: python tests/test_ground_truth.py

Slow: it opens both source documents. Worth it, because an evaluation built on
annotations that no longer match the document would be quietly wrong.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.ground_truth import GroundTruth

FILES = [ROOT / "evaluation" / name for name in ("ground_truth.json", "ground_truth_synthetic.json")]


def load_all():
    return [GroundTruth(path) for path in FILES]


def test_every_annotation_is_present_in_its_block():
    for truth in load_all():
        problems = truth.validate()
        assert not problems, f"{truth.path.name}: {problems}"


def test_annotations_lie_inside_the_stated_scope():
    for truth in load_all():
        for annotation in truth.annotations:
            assert truth.in_scope(annotation.block), annotation


def test_clean_blocks_are_in_scope_too():
    """Precision needs the blocks that were read and found empty, not just the hits."""
    truth = GroundTruth(FILES[0])
    scored = {index for index, _ in truth.scored_blocks()}
    assert scored > truth.blocks_annotated
    assert len(scored - truth.blocks_annotated) > 50


def test_all_nine_required_types_are_covered_somewhere():
    covered = set()
    for truth in load_all():
        covered |= set(truth.by_label())
    assert covered >= {
        "PERSON",
        "EMAIL",
        "PHONE",
        "ORGANIZATION",
        "LOCATION",
        "SSN",
        "CREDIT_CARD",
        "DATE_OF_BIRTH",
        "IP_ADDRESS",
    }


def test_conventions_are_recorded():
    for truth in load_all():
        assert truth.conventions, f"{truth.path.name} states no annotation conventions"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
