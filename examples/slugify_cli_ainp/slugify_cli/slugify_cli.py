#!/usr/bin/env python3
"""Small stdlib-only CLI that turns text into URL-safe slugs."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata


def slugify(text: str, *, max_length: int = 80) -> str:
    """Return a lowercase ASCII slug made from text."""
    if max_length < 1:
        raise ValueError("max_length must be >= 1")
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        slug = "untitled"
    return slug[:max_length].rstrip("-") or "untitled"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert text to a lowercase ASCII slug."
    )
    parser.add_argument("text", nargs="*", help="Text to slugify. Reads stdin when omitted.")
    parser.add_argument(
        "--max-length",
        type=int,
        default=80,
        help="Maximum slug length, default: 80.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    text = " ".join(args.text) if args.text else sys.stdin.read()
    try:
        print(slugify(text, max_length=args.max_length))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
