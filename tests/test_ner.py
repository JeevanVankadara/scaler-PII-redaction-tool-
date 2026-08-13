"""Run with: python tests/test_ner.py

The vocabulary tests are pure functions. The recognizer tests load the spaCy
model once, so this file is slower than the rest of the suite.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.recognizers.ner import (
    LocationRecognizer,
    OrganizationRecognizer,
    PersonRecognizer,
)
from pii_redactor.recognizers.vocab import (
    all_generic,
    all_jargon,
    has_company_suffix,
    has_place_word,
    is_institution,
    strip_jargon_edges,
)


def found(recognizer, text):
    return sorted(d.text for d in recognizer.find(text))


def test_jargon_spans_are_recognised():
    assert all_jargon("Equity Shares")
    assert all_jargon("the Offer Price")
    assert not all_jargon("Kushal Subbayya Hegde")
    assert not all_jargon("HDFC Bank Limited")


def test_institutions_match_through_spacy_fragments():
    assert is_institution("Securities and Exchange Board of India")
    assert is_institution("and Exchange Board of India")
    assert is_institution("BSE")
    assert not is_institution("HDFC Bank Limited")


def test_generic_fragments_are_not_companies():
    assert all_generic("Bank Limited")
    assert all_generic("FAMILY TRUST")
    assert not all_generic("Dhaulagiri Family Trust")


def test_company_and_place_words():
    assert has_company_suffix("Nuvama Wealth Management Limited")
    assert not has_company_suffix("Kushal Subbayya Hegde")
    assert has_place_word("Bandra Kurla Complex")
    assert has_place_word("Chakan Taluka-Khed")
    assert not has_place_word("Sarthak Malvadkar")


def test_edge_trimming_keeps_the_name():
    for value, expected in [
        ("Sharmila Joshi Website", "Sharmila Joshi"),
        ("Sarthak Malvadkar Company", "Sarthak Malvadkar"),
        ("Rajesh Branch", "Rajesh"),
    ]:
        span = strip_jargon_edges(value)
        assert value[span[0] : span[1]] == expected

    assert strip_jargon_edges("Equity Shares") is None


def test_person_finds_real_names():
    text = "Kushal Subbayya Hegde is the Promoter and Sarthak Malvadkar is the Company Secretary."
    assert found(PersonRecognizer(), text) == ["Kushal Subbayya Hegde", "Sarthak Malvadkar"]


def test_person_rejects_document_jargon():
    for text in ["The Offer opens today", "Equity Shares of the Company", "the Cap Price"]:
        assert found(PersonRecognizer(), text) == []


def test_organization_keeps_companies_and_drops_regulators():
    text = "HDFC Bank Limited and the Securities and Exchange Board of India"
    detected = found(OrganizationRecognizer(), text)
    assert "HDFC Bank Limited" in detected
    assert not any("Exchange Board" in value for value in detected)


def test_countries_and_states_are_kept_in_the_clear():
    location, organization = LocationRecognizer(), OrganizationRecognizer()
    for value in ["India", "Maharashtra", "Gujarat", "United States"]:
        assert not location.keep(value), value
        assert organization.skip(value), value
    assert location.keep("Pune")
    assert location.keep("Ahmednagar")


def test_single_token_organizations_are_dropped():
    """Known limitation, deliberately chosen: see OrganizationRecognizer.

    A city the model happens to label ORG rather than GPE is missed. Allowing
    single tokens through readmitted ASBA, IPO, Forms, Bonus and Fraud, which
    cost far more precision than it recovered.
    """
    organization = OrganizationRecognizer()
    assert list(organization.find("ASBA Forms must be submitted")) == []
    assert organization.keep("HDFC Bank Limited")


def test_offsets_stay_aligned_after_trimming():
    text = (
        "Kushal Subbayya Hegde is the Promoter, Sarthak Malvadkar Company is the "
        "Company Secretary, and HDFC Bank Limited is the Banker at Pune."
    )
    detections = [
        d
        for recognizer in (PersonRecognizer(), OrganizationRecognizer(), LocationRecognizer())
        for d in recognizer.find(text)
    ]
    assert detections, "expected at least one entity"
    for detection in detections:
        assert text[detection.start : detection.end] == detection.text


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
