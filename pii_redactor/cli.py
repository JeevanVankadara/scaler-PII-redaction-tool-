"""Command line entry point: python -m pii_redactor.cli --help"""

import argparse
import json
import sys
from pathlib import Path

from .pipeline import run
from .recognizers import REGISTRY
from .transforms import POLICIES, TRANSFORMS, build_transform, link_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pii-redactor",
        description="Read a .docx, replace the PII in it, write a new .docx.",
    )
    parser.add_argument("source", type=Path, help="input .docx")
    parser.add_argument("-o", "--output", type=Path, help="output .docx")
    parser.add_argument("-t", "--transform", choices=TRANSFORMS, default="redact")
    parser.add_argument(
        "-p",
        "--policy",
        choices=sorted(POLICIES),
        default="fake",
        help="what detected values are replaced with",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        metavar="FILE",
        help="write the real-to-fake mapping as JSON, for review",
    )
    parser.add_argument(
        "--only",
        metavar="NAMES",
        help=f"comma-separated recognizers to run ({', '.join(sorted(REGISTRY))})",
    )
    parser.add_argument("--exclude", metavar="NAMES", help="recognizers to skip")
    parser.add_argument("--no-headers", action="store_true", help="skip headers and footers")
    parser.add_argument(
        "--single-pass",
        action="store_true",
        help="skip the name-linking pass (faster, weaker recall on partial names)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="scan and report without writing an output file",
    )
    return parser


def _names(value):
    return [part.strip() for part in value.split(",") if part.strip()] if value else None


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if not args.source.exists():
        print(f"error: {args.source} not found", file=sys.stderr)
        return 1

    try:
        transform = build_transform(
            args.transform,
            only=_names(args.only),
            exclude=_names(args.exclude),
            policy=args.policy,
        )
    except KeyError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    linked = 0
    if args.transform == "redact" and not args.single_pass:
        linked = link_names(args.source, transform, include_headers=not args.no_headers)

    destination = None
    if not args.dry_run:
        destination = args.output or args.source.with_name(f"{args.source.stem}.redacted.docx")

    stats = run(
        args.source,
        destination,
        transform,
        include_headers=not args.no_headers,
    )

    print(f"source            : {args.source}")
    print(f"transform         : {args.transform}")
    if linked:
        print(f"names linked      : {linked}")
    print(stats.summary())
    if destination:
        print(f"written           : {destination}")
    if args.mapping:
        count = _write_mapping(args.mapping, transform)
        print(f"mapping           : {args.mapping} ({count} values)")
    return 0


def _write_mapping(path: Path, transform) -> int:
    policy = getattr(transform, "policy", None)
    mapping = getattr(policy, "mapping", {})
    rows = [
        {"type": label, "original": original, "replacement": fake}
        for (label, original), fake in sorted(mapping.items())
    ]
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(rows)


if __name__ == "__main__":
    raise SystemExit(main())
