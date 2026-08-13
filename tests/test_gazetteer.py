"""Run with: python tests/test_gazetteer.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.identities import IdentityRegistry
from pii_redactor.recognizers.gazetteer import NameGazetteer


def found(gazetteer, text):
    return [(d.text, d.start, d.end) for d in gazetteer.find(text)]


def test_matches_regardless_of_case():
    gazetteer = NameGazetteer(["Rohit Kushal Hegde"])
    assert found(gazetteer, "OUR PROMOTERS: ROHIT KUSHAL HEGDE, and others") == [
        ("ROHIT KUSHAL HEGDE", 15, 33)
    ]


def test_prefers_the_longest_known_name():
    gazetteer = NameGazetteer(["Kushal Hegde", "Rohit Kushal Hegde"])
    assert [text for text, _, _ in found(gazetteer, "signed by Rohit Kushal Hegde")] == [
        "Rohit Kushal Hegde"
    ]


def test_tolerates_odd_whitespace():
    gazetteer = NameGazetteer(["Rajesh Kushal Hegde"])
    assert found(gazetteer, "Rajesh\tKushal  Hegde signed")


def test_does_not_match_inside_a_word():
    gazetteer = NameGazetteer(["Ann Lee"])
    assert found(gazetteer, "Ann Leeson attended") == []


def test_single_token_names_are_ignored():
    assert NameGazetteer(["Rohit", "Rohit Kushal Hegde"]).names == ["Rohit Kushal Hegde"]


def test_empty_gazetteer_is_safe():
    assert found(NameGazetteer([]), "anything at all") == []


def test_priming_makes_ambiguity_visible():
    """The defect this pass exists to fix.

    Met in isolation, "Kushal Hegde" looks like a short form of whichever full
    name happens to be known already. Priming shows it sits inside four of them.
    """
    full_names = [
        "Kushal Subbayya Hegde",
        "Rajesh Kushal Hegde",
        "Pushpa Kushal Hegde",
        "Rohit Kushal Hegde",
    ]

    ordered = IdentityRegistry()
    ordered.for_name("Rohit Kushal Hegde")
    assert ordered.for_name("Kushal Hegde").full == ordered.for_name("Rohit Kushal Hegde").full

    primed = IdentityRegistry()
    primed.prime(full_names + ["Kushal Hegde"])
    short = primed.for_name("Kushal Hegde").full
    assert short not in {primed.for_name(name).full for name in full_names}


def test_priming_still_links_unambiguous_short_forms():
    registry = IdentityRegistry()
    registry.prime(["Rajesh Kushal Hegde", "Pushpa Kushal Hegde", "Rajesh Hegde"])
    assert registry.for_name("Rajesh Hegde").full == registry.for_name("Rajesh Kushal Hegde").full


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
