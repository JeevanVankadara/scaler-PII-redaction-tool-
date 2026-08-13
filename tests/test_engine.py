"""Run with: python tests/test_engine.py"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.blocks import TextBlock
from pii_redactor.detection import Detection
from pii_redactor.engine import RedactionEngine, resolve
from pii_redactor.policies import NumberedPlaceholderPolicy, PlaceholderPolicy
from pii_redactor.recognizers import REGISTRY, RegexRecognizer, build
from pii_redactor.recognizers.email import EmailRecognizer


class FakeRun:
    def __init__(self, text):
        self.text = text


def block(*texts):
    return TextBlock([FakeRun(t) for t in texts])


def det(start, end, text, label="X", priority=0, score=1.0):
    return Detection(start, end, text, label, priority=priority, score=score)


def test_email_recognizer_finds_addresses():
    found = list(EmailRecognizer().find("write to cs.connect@kshinternational.com today"))
    assert [d.text for d in found] == ["cs.connect@kshinternational.com"]
    assert found[0].label == "EMAIL"


def test_email_recognizer_ignores_non_addresses():
    assert list(EmailRecognizer().find("see page 417 @ the office")) == []


def test_resolve_keeps_non_overlapping():
    kept = resolve([det(0, 4, "aaaa"), det(10, 14, "bbbb")])
    assert [d.start for d in kept] == [0, 10]


def test_resolve_prefers_higher_priority():
    card = det(0, 19, "4532-0151-1283-0366", label="CARD", priority=90)
    phone = det(0, 10, "4532-0151-", label="PHONE", priority=50)
    assert [d.label for d in resolve([phone, card])] == ["CARD"]


def test_resolve_prefers_longer_at_equal_priority():
    kept = resolve([det(0, 5, "short"), det(0, 11, "much longer")])
    assert [d.length for d in kept] == [11]


def test_resolve_returns_document_order():
    kept = resolve([det(20, 24, "d"), det(0, 4, "a"), det(10, 14, "c")])
    assert [d.start for d in kept] == [0, 10, 20]


def test_min_score_filters_weak_detections():
    class Weak(RegexRecognizer):
        name, label = "weak", "WEAK"
        pattern = re.compile(r"maybe")

        def score_of(self, match):
            return 0.3

    assert RedactionEngine([Weak()], min_score=0.5).detect("maybe") == []
    assert len(RedactionEngine([Weak()], min_score=0.2).detect("maybe")) == 1


def test_same_value_always_gets_the_same_surrogate():
    policy = NumberedPlaceholderPolicy()
    engine = RedactionEngine([EmailRecognizer()], policy)
    b = block("a@x.com then b@x.com then a@x.com")
    b.apply(engine.redact(b))
    assert b.text == "[EMAIL_1] then [EMAIL_2] then [EMAIL_1]"


def test_engine_redacts_through_a_block():
    engine = RedactionEngine([EmailRecognizer()], PlaceholderPolicy())
    b = block("Email: ", "cs.connect@ksh", "international.com", " Telephone")
    b.apply(engine.redact(b))
    assert b.text == "Email: [EMAIL] Telephone"


def test_adding_a_pii_type_needs_no_engine_change():
    class PanRecognizer(RegexRecognizer):
        name, label, priority = "pan", "PAN", 85
        pattern = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")

    engine = RedactionEngine([EmailRecognizer(), PanRecognizer()], PlaceholderPolicy())
    b = block("PAN ABCDE1234F for a@x.com")
    b.apply(engine.redact(b))
    assert b.text == "PAN [PAN] for [EMAIL]"


def test_build_filters_by_name():
    assert [r.name for r in build(only=["email"])] == ["email"]
    assert "email" not in {r.name for r in build(exclude=["email"])}
    assert set(REGISTRY) >= {"email"}


def test_build_rejects_unknown_names():
    try:
        build(only=["nope"])
    except KeyError:
        return
    raise AssertionError("expected KeyError")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
