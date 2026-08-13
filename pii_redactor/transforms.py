"""Transforms turn a TextBlock into a list of Replacements."""

from .engine import RedactionEngine
from .policies import NumberedPlaceholderPolicy, PlaceholderPolicy
from .recognizers import build

POLICIES = {
    "placeholder": PlaceholderPolicy,
    "numbered": NumberedPlaceholderPolicy,
}

TRANSFORMS = ("passthrough", "redact")


def passthrough(block):
    """Leave the document untouched — proves the read/write path is lossless."""
    return []


def build_transform(name, only=None, exclude=None, policy="placeholder"):
    if name == "passthrough":
        return passthrough
    if name == "redact":
        return RedactionEngine(build(only, exclude), POLICIES[policy]())
    raise KeyError(f"unknown transform: {name}")
