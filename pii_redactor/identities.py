"""Stable fake identities, and the linking that keeps a person's details together.

The assignment's example requires more than value-for-value substitution: when
Rashi Patil becomes John Doe, rashi.patil@gmail.com has to become
john.doe@example.com. That means recognising that a name and an email address
belong to the same person, which is what the registry below does.
"""

import hashlib
import re
from dataclasses import dataclass

from faker import Faker

_TOKEN = re.compile(r"[A-Za-z]+")
_MIN_TOKEN = 2


def signature(value: str) -> frozenset:
    """Name tokens, so "Sarthak Malvadkar" and "Sarthak.malvadkar@x.com" agree."""
    return frozenset(
        token.lower() for token in _TOKEN.findall(value) if len(token) >= _MIN_TOKEN
    )


def seed_for(key: str) -> int:
    """A stable seed per key, so output does not depend on encounter order."""
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:12], 16)


@dataclass(frozen=True)
class Identity:
    first: str
    last: str
    domain: str = "example.com"

    @property
    def full(self) -> str:
        return f"{self.first} {self.last}"

    @property
    def email(self) -> str:
        return f"{self.first}.{self.last}@{self.domain}".lower()


class IdentityRegistry:
    """One fake identity per real person, found again by name or by email."""

    def __init__(self, domain: str = "example.com"):
        self.domain = domain
        self._by_signature = {}

    def prime(self, names) -> None:
        """Register every known name, longest first, before any replacement runs.

        Without this the result depends on reading order: "Kushal Hegde" met
        while only "Rohit Kushal Hegde" is known looks unambiguous and merges
        into it, which is how two different people end up sharing one identity.
        Seeing all the full names first makes the ambiguity visible.
        """
        for name in sorted(set(names), key=lambda value: (-len(signature(value)), value)):
            self.for_name(name)

    def for_name(self, name: str) -> Identity:
        return self._resolve(signature(name), name)

    def for_email(self, address: str) -> Identity:
        local = address.split("@", 1)[0]
        return self._resolve(signature(local), address)

    def _resolve(self, key: frozenset, source: str) -> Identity:
        if not key:
            return self._create(key, source)
        if key in self._by_signature:
            return self._by_signature[key]

        match = self._unambiguous_alias(key)
        if match is not None:
            self._by_signature[key] = self._by_signature[match]
            return self._by_signature[key]
        return self._create(key, source)

    def _unambiguous_alias(self, key: frozenset):
        """Link "Kushal Hegde" to "Kushal Subbayya Hegde" — but only if unique.

        "Kushal Hegde" is also a subset of "Rajesh Kushal Hegde", and guessing
        between two people is worse than treating the short form as its own.
        """
        supersets = [known for known in self._by_signature if key < known]
        subsets = [known for known in self._by_signature if known < key]
        candidates = supersets or subsets
        return candidates[0] if len(candidates) == 1 else None

    def _create(self, key: frozenset, source: str) -> Identity:
        faker = Faker("en_US")
        faker.seed_instance(seed_for(" ".join(sorted(key)) or source))
        identity = Identity(faker.first_name(), faker.last_name(), self.domain)
        if key:
            self._by_signature[key] = identity
        return identity

    def __len__(self) -> int:
        return len(set(self._by_signature.values()))
