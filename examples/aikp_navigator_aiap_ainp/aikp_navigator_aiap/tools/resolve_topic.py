#!/usr/bin/env python3
"""Normalize a topic into a tiny AIKP navigation request.

Stdlib-only example helper. It performs no network access, no file writes, no
subprocess calls and no credential handling.
"""
from __future__ import annotations

import argparse
import json
import re
import sys


def normalize_topic(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def build_request(topic: str) -> dict[str, object]:
    normalized = normalize_topic(topic)
    return {
        "protocol_hint": "AIKP",
        "topic": topic,
        "topic_slug": normalized,
        "requested_views": ["summary", "sources", "risks"],
        "boundary": "local example request; not an external retrieval or trust proof",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an AIKP navigation request.")
    parser.add_argument("topic", nargs="*", help="Topic words.")
    args = parser.parse_args(argv)

    topic = " ".join(args.topic).strip()
    if not topic:
        topic = "untitled"
    print(json.dumps(build_request(topic), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
