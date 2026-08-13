"""Transforms turn a TextBlock into a list of Replacements."""

from .engine import RedactionEngine
from .pipeline import scan
from .policies import FakeIdentityPolicy, NumberedPlaceholderPolicy, PlaceholderPolicy
from .recognizers import build
from .recognizers.gazetteer import NameGazetteer

POLICIES = {
    "fake": FakeIdentityPolicy,
    "placeholder": PlaceholderPolicy,
    "numbered": NumberedPlaceholderPolicy,
}

TRANSFORMS = ("passthrough", "redact")


def passthrough(block):
    """Leave the document untouched — proves the read/write path is lossless."""
    return []


def build_transform(name, only=None, exclude=None, policy="fake"):
    if name == "passthrough":
        return passthrough
    if name == "redact":
        return RedactionEngine(build(only, exclude), POLICIES[policy]())
    raise KeyError(f"unknown transform: {name}")


def link_names(source, transform, include_headers: bool = True) -> int:
    """A first pass over the document, so the second one knows every name in it.

    Two things need the whole picture up front: deciding whether a short name is
    ambiguous, and finding names the model only caught in some paragraphs.
    """
    detections = scan(source, transform, include_headers)
    known = {"PERSON": set(), "ORGANIZATION": set()}
    for detection in detections:
        if detection.label in known:
            known[detection.label].add(detection.text)
    if not any(known.values()):
        return 0

    registry = getattr(getattr(transform, "policy", None), "identities", None)
    if registry is not None:
        registry.prime(known["PERSON"])
    for label, names in known.items():
        transform.recognizers.append(NameGazetteer(names, label=label))
    return sum(len(names) for names in known.values())
