"""Recognizer registry.

Adding a PII type is: write the class in this package, decorate it with
@register, and import the module at the bottom of this file.
"""

from .base import ContextualRegexRecognizer, Recognizer, RegexRecognizer

REGISTRY = {}


def register(cls):
    if not cls.name:
        raise ValueError(f"{cls.__name__} needs a name")
    if cls.name in REGISTRY:
        raise ValueError(f"duplicate recognizer name: {cls.name}")
    REGISTRY[cls.name] = cls
    return cls


def build(only=None, exclude=None):
    """Instantiate registered recognizers, optionally filtered by name."""
    names = set(only) if only else set(REGISTRY)
    unknown = names - set(REGISTRY)
    if unknown:
        raise KeyError(f"unknown recognizer(s): {sorted(unknown)}")
    names -= set(exclude or ())
    return [REGISTRY[name]() for name in sorted(names)]


from . import credit_card, dob, email, ip, ner, phone, ssn  # noqa: E402,F401  registration

__all__ = [
    "REGISTRY",
    "ContextualRegexRecognizer",
    "Recognizer",
    "RegexRecognizer",
    "build",
    "register",
]
