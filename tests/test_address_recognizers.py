"""Run with: python tests/test_address_recognizers.py

The city, postal code and company recognizers were all added in response to
specific misses in the evaluation. Each test names the miss it closes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.recognizers.city import CityRecognizer
from pii_redactor.recognizers.company import CompanyRecognizer
from pii_redactor.recognizers.postal_code import PostalCodeRecognizer


def found(recognizer, text):
    return [d.text for d in recognizer.find(text)]


def test_cities_are_found_without_the_model():
    recognizer = CityRecognizer()
    assert found(recognizer, "issued by Registrar of Companies at Bombay") == ["Bombay"]
    assert found(recognizer, "Baner, Pune – 411 045") == ["Baner", "Pune"]
    assert found(recognizer, "PUNE EDITION OF LOKSATTA") == ["PUNE"]


def test_city_names_do_not_match_inside_words():
    assert found(CityRecognizer(), "Puneet Sharma and Delhite") == []


def test_postal_codes_need_an_address_around_them():
    recognizer = PostalCodeRecognizer()
    assert found(recognizer, "Village Birdewadi, Khed, Pune – 410 501") == ["410 501"]
    assert found(recognizer, "123 MG Road, Pune 411001, India") == ["411001"]
    # No address words: a bare six-digit number is a quantity, not a PIN.
    assert found(recognizer, "aggregating to 410501 equity shares") == []


def test_postal_code_allows_a_trailing_comma():
    """The miss that motivated the fix: an address almost always continues."""
    assert found(PostalCodeRecognizer(), "Pune – 410 501, Maharashtra, India") == ["410 501"]


def test_companies_are_found_by_their_legal_suffix():
    recognizer = CompanyRecognizer()
    assert found(recognizer, "Company: Acme Technologies Limited") == [
        "Acme Technologies Limited"
    ]
    assert found(recognizer, "ICICI\tSecurities Limited") == ["ICICI\tSecurities Limited"]
    assert found(recognizer, "(Formerly Link Intime India Private Limited)") == [
        "Link Intime India Private Limited"
    ]
    assert found(recognizer, "certified by Kirtane & Pandit LLP") == ["Kirtane & Pandit LLP"]


def test_company_pattern_rejects_fragments_and_institutions():
    recognizer = CompanyRecognizer()
    assert found(recognizer, "listed on the National Stock Exchange of India Limited") == []
    assert found(recognizer, "a Bank Limited holds") == []
    assert found(recognizer, "at Waterloo Industrial Park VI Private Limited") == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
