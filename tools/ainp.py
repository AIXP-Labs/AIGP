#!/usr/bin/env python3
"""Unified AINP command-line entry point.

This is a thin dispatcher over the reference tools. It deliberately avoids
reimplementing validator logic; subcommands call the same stdlib-only tools
used by the release gate.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
PUBLIC_OUTPUT = PublicOutput(__file__)

ALIASES = {
    "validate": "ainp_validate.py",
    "report-check": "ainp_report_check.py",
    "release-check": "ainp_release_check.py",
    "project-check": "ainp_project_check.py",
    "rehash": "ainp_rehash.py",
    "check-doc-sync": "check_doc_sync.py",
    "check-markdown-links": "check_markdown_links.py",
}


@dataclass
class Check:
    label: str
    ok: bool
    command: list[str] | None = None
    stdout: str = ""
    stderr: str = ""
    detail: str = ""


def _run_tool(script: str, args: list[str]) -> int:
    cmd = [sys.executable, "-B", os.path.join(TOOLS, script), *args]
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def _run_check(label: str, command: list[str]) -> Check:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return Check(
        label=label,
        ok=proc.returncode == 0,
        command=[_display_arg(arg) for arg in command],
        stdout=_sanitize_output(proc.stdout.strip()),
        stderr=_sanitize_output(proc.stderr.strip()),
    )


def _display_arg(arg: str) -> str:
    if os.path.abspath(arg) == os.path.abspath(sys.executable):
        return "python"
    if os.path.isabs(arg):
        return PUBLIC_OUTPUT.display_path(arg)
    return arg


def _sanitize_output(text: str) -> str:
    return PUBLIC_OUTPUT.sanitize_text(text)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    seen = set()
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r} (parser-differential smuggling guard)")
        seen.add(key)
        out[key] = value
    return out


def _reject_constant(const: str) -> None:
    raise ValueError(f"non-standard JSON literal {const} (NaN/Infinity) rejected")


def _strict_json_load(fh):
    return json.load(
        fh,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )


def _required_files_check() -> Check:
    required = [
        "VERSION",
        "specification/AINP_Protocol.md",
        "specification/AINP_Protocol_cn.md",
        "schemas/ainp-generation-v1.0.0.schema.json",
        "schemas/ainp-generationreport-v1.0.0.schema.json",
        "schemas/ainp-generationfeedback-v1.0.0.schema.json",
        "schemas/ainp-generation-space-v1.0.0.schema.json",
        "schemas/ainp-reference-manifest-v1.0.0.schema.json",
        "schemas/high_risk_types-v1.0.0.schema.json",
        "schemas/high_risk_types.v1.0.0.json",
        "specification/standards/ainp-rules-v1.0.0.json",
        "examples/file_family/project.ainp.json",
        "examples/whitepaper_ainp/AINP.md",
        "examples/slugify_cli_ainp/AINP.md",
    ]
    missing = [item for item in required if not os.path.exists(os.path.join(ROOT, item))]
    return Check(
        label="required files",
        ok=not missing,
        detail="missing: " + ", ".join(missing) if missing else "all required files present",
    )


def _example_project_packages() -> list[str]:
    examples = os.path.join(ROOT, "examples")
    if not os.path.isdir(examples):
        return []
    return [
        os.path.join("examples", name).replace(os.sep, "/")
        for name in sorted(os.listdir(examples))
        if name.endswith("_ainp") and os.path.isdir(os.path.join(examples, name))
    ]


def _example_project_discovery_check(project_packages: list[str]) -> Check:
    return Check(
        label="example project discovery",
        ok=bool(project_packages),
        detail=(
            "discovered: " + ", ".join(project_packages)
            if project_packages
            else "no examples/*_ainp project packages found"
        ),
    )


def _file_family_files(*suffixes: str) -> list[str]:
    directory = os.path.join(ROOT, "examples", "file_family")
    if not os.path.isdir(directory):
        return []
    return [
        os.path.join("examples", "file_family", name).replace(os.sep, "/")
        for name in sorted(os.listdir(directory))
        if name.endswith(suffixes) and os.path.isfile(os.path.join(directory, name))
    ]


def _file_family_release_bundles() -> list[tuple[str, str]]:
    bundles: list[tuple[str, str]] = []
    family_root = os.path.join(ROOT, "examples", "file_family")
    for report_rel in _file_family_files(".generationreport.json"):
        report_abs = os.path.join(ROOT, *report_rel.split("/"))
        try:
            with open(report_abs, encoding="utf-8-sig") as fh:
                doc = _strict_json_load(fh)
            report = doc.get("generationreport", {})
            if not isinstance(report, dict):
                continue
            overall = report.get("overall", {})
            if not isinstance(overall, dict) or overall.get("conformant") is not True:
                continue
            plan_ref = report.get("plan_ref", {})
            if not isinstance(plan_ref, dict):
                continue
            plan_name = plan_ref.get("path")
            if not isinstance(plan_name, str) or not plan_name:
                continue
            plan_abs = os.path.realpath(os.path.join(family_root, plan_name))
            family_real = os.path.realpath(family_root)
            if os.path.commonpath([family_real, plan_abs]) != family_real:
                continue
            if not os.path.isfile(plan_abs):
                continue
        except (OSError, json.JSONDecodeError, ValueError, RecursionError):
            continue
        plan_rel = os.path.relpath(plan_abs, ROOT).replace(os.sep, "/")
        bundles.append((plan_rel, report_rel))
    return bundles


def _doctor_commands(include_tests: bool, include_pytest: bool,
                     project_packages: list[str]) -> list[tuple[str, list[str]]]:
    py = sys.executable
    file_family_validation = [
        *_file_family_files(".generation.json"),
        *_file_family_files(".generationfeedback.json"),
        *_file_family_files(".ainp.json"),
    ]
    commands = [
        ("plan/examples validation", [
            py, "-B", os.path.join(TOOLS, "ainp_validate.py"),
            *file_family_validation,
        ]),
    ]
    for report_rel in _file_family_files(".generationreport.json"):
        commands.append((f"file-family report check {report_rel}", [
            py, "-B", os.path.join(TOOLS, "ainp_report_check.py"),
            report_rel, "--mode", "release",
        ]))
    for plan_rel, report_rel in _file_family_release_bundles():
        commands.append((f"file-family release gate {report_rel}", [
            py, "-B", os.path.join(TOOLS, "ainp_release_check.py"),
            plan_rel, "--report", report_rel,
        ]))
    for project_package in project_packages:
        manifest = "/".join([project_package, "ainp", "references",
                             "reference_manifest.json"])
        if os.path.exists(os.path.join(ROOT, *manifest.split("/"))):
            commands.append((f"reference manifest check {manifest}", [
                py, "-B", os.path.join(TOOLS, "ainp_validate.py"),
                manifest,
            ]))
    for project_package in project_packages:
        commands.append((f"project package check {project_package}", [
            py, "-B", os.path.join(TOOLS, "ainp_project_check.py"),
            project_package,
        ]))
    for project_package in project_packages:
        commands.append((f"project hash freshness {project_package}", [
            py, "-B", os.path.join(TOOLS, "ainp_rehash.py"),
            project_package, "--check",
        ]))
    commands.extend([
        ("documentation synchronization", [
            py, "-B", os.path.join(TOOLS, "check_doc_sync.py"),
            "--root", ".",
        ]),
        ("markdown links", [
            py, "-B", os.path.join(TOOLS, "check_markdown_links.py"),
            "--root", ".",
        ]),
    ])
    commands.extend([
        ("conformance tests", [
            py, "-B", os.path.join(ROOT, "tests", "test_ainp.py"),
        ]),
    ] if include_tests else [])
    commands.extend([
        ("pytest discovery", [
            py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:asyncio",
        ]),
    ] if include_pytest else [])
    return commands


def doctor(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="ainp doctor",
        description="Run local AINP repository health checks. Structural checks only; not a trust proof.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--verbose", action="store_true", help="Print stdout/stderr for passing checks too.")
    parser.add_argument("--include-tests", action="store_true", help="Also run tests/test_ainp.py.")
    parser.add_argument("--include-pytest", action="store_true", help="Also run pytest discovery.")
    args = parser.parse_args(argv)

    project_packages = _example_project_packages()
    checks = [_required_files_check(), _example_project_discovery_check(project_packages)]
    for label, command in _doctor_commands(args.include_tests, args.include_pytest, project_packages):
        checks.append(_run_check(label, command))

    ok = all(check.ok for check in checks)
    if args.json:
        print(json.dumps({
            "ok": ok,
            "checks": [
                {
                    "label": check.label,
                    "ok": check.ok,
                    "command": check.command,
                    "detail": check.detail,
                    "stdout": check.stdout,
                    "stderr": check.stderr,
                }
                for check in checks
            ],
            "note": "AINP doctor checks structure and local consistency only; it is not a trust proof.",
        }, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            status = "PASS" if check.ok else "FAIL"
            print(f"{status} {check.label}")
            if check.detail:
                print(f"  {check.detail}")
            if args.verbose or not check.ok:
                if check.command:
                    print("  command: " + " ".join(check.command))
                if check.stdout:
                    print("  stdout:")
                    print(_indent(check.stdout))
                if check.stderr:
                    print("  stderr:")
                    print(_indent(check.stderr))
        print("NOTE: doctor checks structure and local consistency only; it is not a trust proof.")
    return 0 if ok else 1


def _indent(text: str) -> str:
    return "\n".join("    " + line for line in text.splitlines())


def print_help() -> None:
    commands = ", ".join([*ALIASES.keys(), "doctor"])
    print("Usage: ainp <command> [args...]")
    print()
    print("Commands:")
    for name, script in ALIASES.items():
        print(f"  {name:<20} forwards to tools/{script}")
    print("  doctor               run local repository health checks")
    print()
    print(f"Available commands: {commands}")
    print("Use `ainp <command> --help` for the forwarded tool's options.")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print_help()
        return 0
    command, rest = argv[0], argv[1:]
    if command == "doctor":
        return doctor(rest)
    if command in ALIASES:
        return _run_tool(ALIASES[command], rest)
    print(f"ERROR: unknown command {_sanitize_output(command)!r}", file=sys.stderr)
    print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
