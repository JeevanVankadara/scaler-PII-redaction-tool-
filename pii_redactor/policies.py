"""Policies decide what a detected value is replaced with.

The base class memoises per (label, value), so the same person or email gets the
same surrogate everywhere in the document. Subclasses only supply `generate`.
"""

from abc import ABC, abstractmethod

from .detection import Detection
from .identities import IdentityRegistry, seed_for
from .surrogates import (
    fake_card,
    fake_date,
    fake_ip,
    fake_phone,
    fake_postal_code,
    fake_ssn,
    is_postal_code,
    match_case,
)


class SurrogatePolicy(ABC):
    def __init__(self):
        self.mapping = {}

    def surrogate(self, detection: Detection) -> str:
        key = (detection.label, detection.text)
        if key not in self.mapping:
            self.mapping[key] = self.generate(detection)
        return self.mapping[key]

    @abstractmethod
    def generate(self, detection: Detection) -> str:
        """Produce a surrogate for a value seen for the first time."""

    def reset(self) -> None:
        self.mapping.clear()


class PlaceholderPolicy(SurrogatePolicy):
    """[EMAIL], [PERSON] — readable, and makes review of a run trivial."""

    def __init__(self, template: str = "[{label}]"):
        super().__init__()
        self.template = template

    def generate(self, detection: Detection) -> str:
        return self.template.format(label=detection.label)


class NumberedPlaceholderPolicy(SurrogatePolicy):
    """[EMAIL_1], [EMAIL_2] — distinct values stay distinguishable.

    Useful for checking that one real person maps to exactly one surrogate.
    """

    def __init__(self):
        super().__init__()
        self._counts = {}

    def generate(self, detection: Detection) -> str:
        index = self._counts.get(detection.label, 0) + 1
        self._counts[detection.label] = index
        return f"[{detection.label}_{index}]"

    def reset(self) -> None:
        super().reset()
        self._counts.clear()


class FakeIdentityPolicy(SurrogatePolicy):
    """Replaces PII with plausible fake values instead of markers.

    A person and their email address resolve to one identity, so Rashi Patil
    becomes John Doe and rashi.patil@gmail.com becomes john.doe@example.com.
    Everything else keeps the shape of what it replaced, so the document still
    reads as a document.
    """

    def __init__(self, domain: str = "example.com"):
        super().__init__()
        self.identities = IdentityRegistry(domain)

    def generate(self, detection: Detection) -> str:
        label, value = detection.label, detection.text
        if label == "PERSON":
            return match_case(value, self.identities.for_name(value).full)
        if label == "EMAIL":
            return self.identities.for_email(value).email
        if label == "ORGANIZATION":
            return match_case(value, self._faker(value).company())
        if label == "LOCATION":
            if is_postal_code(value):
                return fake_postal_code(value)
            return match_case(value, self._faker(value).city())
        if label == "PHONE":
            return fake_phone(value)
        if label == "DATE_OF_BIRTH":
            return fake_date(value)
        if label == "SSN":
            return fake_ssn(value)
        if label == "CREDIT_CARD":
            return fake_card(value)
        if label == "IP_ADDRESS":
            return fake_ip(value)
        if label == "URL":
            return self._fake_website(value)
        return f"[{label}]"

    def _fake_website(self, value: str) -> str:
        """Keep the scheme and the www, replace the domain, drop any path."""
        lowered = value.lower()
        scheme = value[: value.index("//") + 2] if "//" in value else ""
        prefix = "www." if lowered.startswith("www.") or "//www." in lowered else ""
        return f"{scheme}{prefix}{self._faker(value).domain_name()}"

    @staticmethod
    def _faker(value: str):
        from faker import Faker

        faker = Faker("en_US")
        faker.seed_instance(seed_for(value))
        return faker

    def reset(self) -> None:
        super().reset()
        self.identities = IdentityRegistry(self.identities.domain)
