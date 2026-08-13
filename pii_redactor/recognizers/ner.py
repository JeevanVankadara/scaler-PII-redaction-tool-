"""Names, organisations and places, via spaCy.

The model is where recall comes from and where nearly all the noise comes from
too — on the source document it labelled "Offer" a person 113 times. One parse
per block is shared by the three recognizers below, and each applies its own
filters to what the model produced.
"""

from functools import lru_cache

from . import register
from .base import Recognizer
from .vocab import (
    GEO_KEEP,
    JARGON,
    NOT_A_PLACE,
    all_generic,
    all_jargon,
    has_company_suffix,
    has_digit,
    has_place_word,
    is_institution,
    strip_jargon_edges,
    tokens,
    words_of,
)

MODEL = "en_core_web_sm"
_TRIM = " \t\n\r\"'“”‘’(),;:./-"
_LABELS = {"PERSON": "PERSON", "ORG": "ORGANIZATION", "GPE": "LOCATION", "LOC": "LOCATION"}

_models = {}


def load_model(name: str = MODEL):
    if name not in _models:
        import spacy

        _models[name] = spacy.load(
            name, exclude=["parser", "lemmatizer", "attribute_ruler", "tagger"]
        )
    return _models[name]


@lru_cache(maxsize=8)
def analyse(text: str):
    """Entities as (start, end, text, label), cached so one parse serves all three."""
    found = []
    for entity in load_model()(text).ents:
        label = _LABELS.get(entity.label_)
        if label is None:
            continue
        span = _trim(text, entity.start_char, entity.end_char)
        if span is not None:
            found.append((*span, label))
    return tuple(found)


def _trim(text: str, start: int, end: int):
    """Drop leading articles and surrounding punctuation, keeping offsets honest."""
    while start < end and text[start] in _TRIM:
        start += 1
    while end > start and text[end - 1] in _TRIM:
        end -= 1
    if text[start:end].lower().startswith("the "):
        start += 4
    value = text[start:end]
    return (start, end, value) if len(value) >= 2 else None


class _NerRecognizer(Recognizer):
    entity_label = ""
    min_tokens = 1
    trim_edges = False

    def find(self, text: str):
        for start, end, value, label in analyse(text):
            if label == self.entity_label:
                yield from self._accept(start, end, value)

    def _accept(self, start: int, end: int, value: str):
        if self.skip(value):  # judged on the untrimmed span
            return
        if self.trim_edges:
            span = strip_jargon_edges(value)
            if span is None:
                return
            start, end, value = start + span[0], start + span[1], value[span[0] : span[1]]
        if len(tokens(value)) < self.min_tokens or all_jargon(value):
            return
        if self.keep(value):
            yield self.detection(start, end, value, self.score_of(value))

    def skip(self, value: str) -> bool:
        return False

    def keep(self, value: str) -> bool:
        return True

    def score_of(self, value: str) -> float:
        return 0.7


@register
class PersonRecognizer(_NerRecognizer):
    """Requires a title-cased, digit-free, multi-word span.

    Single tokens are where the model does its worst work here, and a full name
    is two tokens by definition. Spans that look like a company or a place are
    left to the other two recognizers rather than dropped.
    """

    name = "person"
    label = "PERSON"
    entity_label = "PERSON"
    priority = 45
    min_tokens = 2
    trim_edges = True

    def keep(self, value: str) -> bool:
        if has_digit(value) or has_company_suffix(value) or has_place_word(value):
            return False
        words = [word for word in tokens(value) if word[:1].isalpha()]
        return len(words) >= 2 and all(word[:1].isupper() for word in words)

    def score_of(self, value: str) -> float:
        return 0.8


@register
class OrganizationRecognizer(_NerRecognizer):
    """Company names, minus the regulators and exchanges.

    Public bodies are named because the law requires it, not because they
    identify anyone, so they are left in the clear deliberately.
    """

    name = "organization"
    label = "ORGANIZATION"
    entity_label = "ORGANIZATION"
    priority = 40
    trim_edges = True
    # Single tokens here are overwhelmingly financial acronyms — ASBA, IPO, PAN,
    # COGS. Allowing them cost far more precision than the handful of real names
    # it recovered, so a company name must be at least two words.
    min_tokens = 2

    def find(self, text: str):
        yield from super().find(text)
        for start, end, value, label in analyse(text):
            # The model routinely files companies under PERSON.
            if label == "PERSON" and has_company_suffix(value) and not all_jargon(value):
                yield self.detection(start, end, value, 0.7)

    def skip(self, value: str) -> bool:
        # Places belong to the location recognizer; institutions to nobody.
        return (
            is_institution(value)
            or has_place_word(value)
            or value.lower().replace(".", "") in GEO_KEEP
        )

    def keep(self, value: str) -> bool:
        if all_generic(value):
            return False
        if has_company_suffix(value):
            return True
        return sum(word[:1].isupper() for word in tokens(value)) >= 2


@register
class LocationRecognizer(_NerRecognizer):
    """Cities, towns and localities — the parts of an address that place a person.

    Countries and states are kept: neither identifies anybody on its own, and
    redacting "India" 97 times would leave the document unreadable.
    """

    name = "location"
    label = "LOCATION"
    entity_label = "LOCATION"
    priority = 35
    trim_edges = True

    def find(self, text: str):
        yield from super().find(text)
        for start, end, value, label in analyse(text):
            if label == "PERSON" and has_place_word(value) and not all_jargon(value):
                yield self.detection(start, end, value, 0.6)

    def skip(self, value: str) -> bool:
        return is_institution(value)

    def keep(self, value: str) -> bool:
        plain = value.lower().replace(".", "")
        if plain in GEO_KEEP or plain in NOT_A_PLACE:
            return False
        if any(word in JARGON for word in words_of(value)):
            return False
        return len(value) >= 3 and value[:1].isupper()
