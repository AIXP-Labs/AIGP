#!/usr/bin/env python3
"""Check local Markdown links and heading anchors."""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput


DEFAULT_TARGETS = [
    "README.md",
    "README_CN.md",
    "docs",
    "docs_cn",
    "examples",
    "specification",
    "adrs",
    "tools",
    "CONTRIBUTING.md",
    "CONTRIBUTING_CN.md",
    "SECURITY.md",
    "GOVERNANCE.md",
    "CODE_OF_CONDUCT.md",
]

EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "app://")
UNSAFE_PREFIXES = ("file:", "javascript:", "data:", "vbscript:")
HTML_LINK_ATTR_RE = re.compile(
    r"\b(href|src|srcset|poster)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
    re.IGNORECASE,
)
REFERENCE_LINK_DEF_RE = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(\S.*)$")
REFERENCE_LINK_USE_RE = re.compile(r"!?\[([^\]\n]+)\]\[([^\]\n]*)\]")
INLINE_CODE_SPAN_RE = re.compile(r"`+[^`]*`+")


def iter_markdown_content_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    fence_marker: str | None = None
    for line_no, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            continue
        if fence_marker is None:
            lines.append((line_no, line))
    return lines


def reference_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip()).casefold()


def iter_markdown_files(root: Path, targets: list[str],
                        public: PublicOutput) -> tuple[list[Path], list[dict[str, Any]]]:
    files: list[Path] = []
    problems: list[dict[str, Any]] = []
    for target in targets:
        path = (root / target).resolve()
        shown = public_link(str(path) if Path(target).is_absolute() else target, public)
        try:
            path.relative_to(root)
        except ValueError:
            problems.append({
                "path": ".",
                "line": 0,
                "link": shown,
                "message": "target escapes repository root",
            })
            continue
        if not path.exists():
            problems.append({
                "path": ".",
                "line": 0,
                "link": shown,
                "message": "missing scan target",
            })
            continue
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
    return sorted({path for path in files}), problems


def inline_text(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    return text.replace("*", "").replace("~", "")


def github_like_anchor(text: str) -> str:
    text = inline_text(text).strip().lower()
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\-\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def heading_anchors(path: Path) -> set[str]:
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        base = github_like_anchor(match.group(2))
        counts[base] = counts.get(base, 0) + 1
        anchors.add(base if counts[base] == 1 else f"{base}-{counts[base] - 1}")
    return anchors


def extract_links(text: str) -> list[tuple[int, str]]:
    links: list[tuple[int, str]] = []
    pattern = re.compile(
        r"(?:!?\[[^\]]+\]\(([^)]+)\)|"
        r"<((?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|\\\\|\.?\.?/|[^:>\s]+/)[^>\s]*)>)"
    )
    for line_no, line in iter_markdown_content_lines(text):
        ref_match = REFERENCE_LINK_DEF_RE.match(line)
        if ref_match:
            raw = ref_match.group(2).strip()
            if raw:
                links.append((line_no, raw))
        for match in pattern.finditer(line):
            if (match.group(2) is not None
                    and re.match(r"^</[A-Za-z][A-Za-z0-9:-]*\s*>$", match.group(0))):
                continue
            raw = (match.group(1) or match.group(2) or "").strip()
            if raw:
                links.append((line_no, raw))
        for match in HTML_LINK_ATTR_RE.finditer(line):
            attr = match.group(1).lower()
            raw = (match.group(2) or match.group(3) or match.group(4) or "").strip()
            if not raw:
                continue
            if attr == "srcset":
                for candidate in raw.split(","):
                    url = candidate.strip().split()[0] if candidate.strip() else ""
                    if url:
                        links.append((line_no, url))
            else:
                links.append((line_no, raw))
    return links


def extract_reference_link_labels(text: str) -> tuple[set[str], list[tuple[int, str]]]:
    definitions: set[str] = set()
    uses: list[tuple[int, str]] = []
    for line_no, line in iter_markdown_content_lines(text):
        ref_match = REFERENCE_LINK_DEF_RE.match(line)
        if ref_match:
            definitions.add(reference_label(ref_match.group(1)))
        line_without_code = INLINE_CODE_SPAN_RE.sub("", line)
        for match in REFERENCE_LINK_USE_RE.finditer(line_without_code):
            label = match.group(2) or match.group(1)
            uses.append((line_no, label))
    return definitions, uses


def link_target(raw_link: str) -> str:
    target = raw_link.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split()[0].strip("<>")


def decode_link_component(value: str) -> str:
    decoded = value
    for _ in range(3):
        next_decoded = urllib.parse.unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


def is_local_machine_link(path_part: str) -> bool:
    return (
        bool(re.match(r"^[a-zA-Z]:", path_part))
        or path_part.startswith("\\\\")
        or path_part.startswith("//")
    )


def check_links(root: Path, targets: list[str],
                public: PublicOutput | None = None) -> list[dict[str, Any]]:
    root = root.resolve()
    public = public or PublicOutput(__file__, bases=[str(root)])
    files, problems = iter_markdown_files(root, targets, public)
    anchors: dict[Path, set[str]] = {}
    for file_path in files:
        text = file_path.read_text(encoding="utf-8-sig", errors="replace")
        definitions, reference_uses = extract_reference_link_labels(text)
        for line_no, label in reference_uses:
            if reference_label(label) not in definitions:
                problems.append(problem(root, file_path, line_no, f"[{label}]",
                                        "undefined reference link label", public))
        for line_no, raw_link in extract_links(text):
            target = link_target(raw_link)
            decoded_target = decode_link_component(target)
            target_lower = decoded_target.lower()
            if target_lower.startswith(EXTERNAL_PREFIXES):
                continue
            if target_lower.startswith(UNSAFE_PREFIXES):
                problems.append(problem(root, file_path, line_no, raw_link, "unsafe scheme", public))
                continue
            path_part, _, fragment = target.partition("#")
            path_part = decode_link_component(path_part)
            if path_part.lower().startswith(UNSAFE_PREFIXES):
                problems.append(problem(root, file_path, line_no, raw_link, "unsafe scheme", public))
                continue
            if is_local_machine_link(path_part):
                problems.append(problem(root, file_path, line_no, raw_link, "local machine path", public))
                continue
            if re.match(r"^[a-zA-Z]+:", path_part):
                continue
            candidate = file_path if not path_part else (file_path.parent / path_part).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                problems.append(problem(root, file_path, line_no, raw_link, "escapes repository root", public))
                continue
            if not candidate.exists():
                problems.append(problem(root, file_path, line_no, raw_link, "missing target", public))
                continue
            if fragment and candidate.is_file() and candidate.suffix.lower() == ".md":
                if candidate not in anchors:
                    anchors[candidate] = heading_anchors(candidate)
                decoded = urllib.parse.unquote(fragment).lower()
                if decoded not in anchors[candidate]:
                    problems.append(problem(root, file_path, line_no, raw_link,
                                            f"missing anchor #{fragment}", public))
    return problems


def public_link(link: str, public: PublicOutput | None = None) -> str:
    raw = link.strip()
    target = link_target(raw)
    decoded = decode_link_component(target.partition("#")[0])
    lower_decoded = decoded.lower()
    if lower_decoded.startswith(UNSAFE_PREFIXES):
        return f"{lower_decoded.split(':', 1)[0]}:<redacted>"
    if is_local_machine_link(decoded):
        return "<local-machine-path>"
    if Path(decoded).is_absolute():
        return (public or PublicOutput(__file__)).display_path(decoded)
    return (public or PublicOutput(__file__)).sanitize_text(decode_link_component(raw))


def problem(root: Path, path: Path, line: int, link: str, message: str,
            public: PublicOutput | None = None) -> dict[str, Any]:
    public = public or PublicOutput(__file__)
    return {
        "path": path.relative_to(root).as_posix(),
        "line": line,
        "link": public_link(link, public),
        "message": public.sanitize_text(decode_link_component(message)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local Markdown links and heading anchors.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("targets", nargs="*", help="Files or directories to scan, relative to root.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    public = PublicOutput(__file__, bases=[str(root)])
    targets = args.targets or DEFAULT_TARGETS
    problems = check_links(root, targets, public)
    if args.json:
        print(json.dumps({"problems": problems, "problem_count": len(problems)}, indent=2))
    elif problems:
        for item in problems:
            print(f"{item['path']}:{item['line']}: {item['message']}: {item['link']}")
        print(f"markdown link check failed: {len(problems)} problem(s)", file=sys.stderr)
    else:
        print("markdown links ok")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
