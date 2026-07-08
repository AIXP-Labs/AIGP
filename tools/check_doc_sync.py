#!/usr/bin/env python3
"""Lightweight documentation synchronization checks for AINP."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput

COMMANDS = [
    "python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json",
    "python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release",
    "python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json",
    "python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json",
    "python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp",
    "python -B tools/ainp_project_check.py examples/whitepaper_ainp",
    "python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py",
    "python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check",
    "python -B tools/ainp_project_check.py examples/slugify_cli_ainp",
    "python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json",
    "python -B tests/test_ainp.py",
    "powershell -ExecutionPolicy Bypass -File scripts\\release_check.ps1",
    "python -B tools/check_doc_sync.py --root .",
    "python -B tools/check_markdown_links.py --root .",
    "git diff --check",
    "git diff --exit-code",
    "git status --porcelain=v1 --untracked-files=all",
    "powershell -ExecutionPolicy Bypass -File scripts\\release_check.ps1 -IncludePytest",
]

DOC_COMMAND_TARGETS = [
    "README.md",
    "README_CN.md",
    "docs/reference/release-evidence-matrix.md",
    "docs/reference/validator-coverage.md",
    "tools/README.md",
]

WORKFLOW_NEEDLES = [
    "python -m pip install --quiet \"jsonschema>=4\" \"pytest>=8\"",
    "./scripts/release_check.ps1 -IncludePytest",
    "git diff --exit-code",
    "git status --porcelain=v1 --untracked-files=all",
    "git diff-tree --check --root -r HEAD",
]

PYPROJECT_NEEDLES = [
    "license = \"Apache-2.0\"",
    "[build-system]",
    "build-backend = \"setuptools.build_meta\"",
    "packages = [\"tools\"]",
    "ainp = \"tools.ainp:main\"",
    "ainp-rehash",
    "\"jsonschema>=4\"",
    "\"pytest>=8\"",
    "docs = [",
    "\"mkdocs>=1.6\"",
    "\"mkdocs-material>=9\"",
]

RELEASE_SCRIPT_NEEDLES = [
    "Assert-RepositoryLayout",
    "tools/ainp_public.py",
    "Invoke-PythonSyntaxCheck",
    "Get-ExampleProjectPackages",
    "examples/*_ainp",
    "python -B tests/test_ainp.py",
    "python -B -m pytest -q -p no:cacheprovider -p no:asyncio",
    "python -B tools/ainp.py doctor --json",
    "Invoke-ExampleProjectProgramTests",
    "Invoke-ExampleReferenceManifestChecks",
    "python -B tools/ainp_validate.py $rel",
    "test_*.py",
    "python -B tools/ainp_rehash.py $rel --check",
    "python -B tools/ainp_project_check.py $rel",
    "python -B tools/check_doc_sync.py --root .",
    "python -B tools/check_markdown_links.py --root .",
    "Assert-NoSchemaMirrors",
    "Assert-NoPrivatePathLeak",
    "POSIX local absolute path",
    "Assert-NoForbiddenResidue",
    "rev-parse --is-inside-work-tree",
    "git -C $rootPath status --porcelain=v1 --untracked-files=all",
    '"site"',
    '".egg-info"',
    '".ainp_test_tmp"',
]

MKDOCS_NEEDLES = [
    "Package Maintenance: guides/package-maintenance.md",
    "Standards Reference: reference/standards.md",
]

UPPER_STALE_PROTOCOL_NAME = "AI" + "GP"
LOWER_STALE_PROTOCOL_NAME = "ai" + "gp"

STALE_PROTOCOL_PATTERN = re.compile(
    re.escape("AI " + "Generation Protocol")
    + "|"
    + re.escape("AIXP-Labs/" + UPPER_STALE_PROTOCOL_NAME)
    + "|"
    + re.escape(UPPER_STALE_PROTOCOL_NAME + "-Protocol")
    + "|"
    + re.escape(UPPER_STALE_PROTOCOL_NAME)
    + "|"
    + re.escape(LOWER_STALE_PROTOCOL_NAME + ".dev")
    + "|"
    + re.escape(LOWER_STALE_PROTOCOL_NAME + ".v1.0.0")
    + "|_"
    + re.escape(LOWER_STALE_PROTOCOL_NAME)
    + r"\b|\."
    + re.escape(LOWER_STALE_PROTOCOL_NAME)
    + r"\b|"
    + re.escape(LOWER_STALE_PROTOCOL_NAME + "-")
    + r"|\b"
    + re.escape(LOWER_STALE_PROTOCOL_NAME)
    + r"\b"
)

STANDARD_FILES = [
    "README.md",
    "AINP_Standard.core.json",
    "AINP_Standard.security.json",
    "AINP_Standard.ecosystem.json",
    "ainp-rules-v1.0.0.json",
]

STANDARD_FORBIDDEN_TOKENS = [
    "main.aisop.json",
    "node_engine",
    "agent_card",
    "quality_baseline",
    "governance_hash",
    "TRI-SYNC",
]

FORBIDDEN_PATTERNS = [
    (re.compile("python " + r"tools/ainp_"), "use `python -B tools/ainp_...`"),
    (re.compile("python " + r"tests/test_ainp\.py"), "use `python -B tests/test_ainp.py`"),
]

TEST_COUNT_RE = re.compile(
    r"\b(\d+)-test\b"
    r"|\b(\d+)\s+tests\b"
    r"|\b(\d+)/(\d+)\s+(?:green|pass(?:ed|es)?|tests?)\b"
    r"|\b(?:tests?|suite|conformance)\b[^\n]{0,80}?\b(\d+)/(\d+)\b",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\\\n", " ")).strip()


def check_contains(path: Path, needles: list[str]) -> list[str]:
    text = normalized(read_text(path))
    missing = []
    for needle in needles:
        if normalized(needle) not in text:
            missing.append(f"{path}: missing `{needle}`")
    return missing


def count_test_functions(root: Path) -> int:
    suite = root / "tests" / "test_ainp.py"
    if not suite.exists():
        return 0
    return len(re.findall(r"^def test_", read_text(suite), re.MULTILINE))


def check_forbidden(path: Path, actual_test_count: int) -> list[str]:
    text = read_text(path)
    failures = []
    for pattern, replacement in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            failures.append(f"{path}: old form matched `{pattern.pattern}`; {replacement}")
    if actual_test_count:
        for match in TEST_COUNT_RE.finditer(text):
            numbers = [int(group) for group in match.groups() if group is not None]
            if numbers and any(number != actual_test_count for number in numbers):
                failures.append(
                    f"{path}: stale test-count reference `{match.group(0)}`; "
                    f"actual suite count is {actual_test_count}/{actual_test_count}"
                )
    return failures


def check_schema_single_source(root: Path) -> list[str]:
    spec = root / "specification"
    if not spec.is_dir():
        return [f"{spec}: missing specification directory"]
    mirrors = [
        path.name for path in spec.iterdir()
        if path.is_file()
        and (path.name.endswith(".schema.json")
             or (path.name.startswith("high_risk_types.v") and path.name.endswith(".json")))
    ]
    return [f"{spec}: schema/data mirrors are forbidden: {sorted(mirrors)}"] if mirrors else []


def check_standards_layer(root: Path) -> list[str]:
    standards = root / "specification" / "standards"
    failures = []
    if not standards.is_dir():
        return [f"{standards}: missing standards directory"]

    for name in STANDARD_FILES:
        if not (standards / name).is_file():
            failures.append(f"{standards}: missing `{name}`")

    aisop_files = sorted(str(path.relative_to(root)) for path in standards.rglob("*.aisop.json"))
    if aisop_files:
        failures.append(f"{standards}: AISOP flow files are forbidden here: {aisop_files}")

    standards_readme = standards / "README.md"
    if standards_readme.exists():
        failures.extend(check_contains(standards_readme, [
            "They are not JSON Schema mirrors",
            "They are not AISOP flows, AIAP programs, runtime extensions",
            "Do not add `*.aisop.json` files to this directory",
        ]))

    standards_reference = root / "docs" / "reference" / "standards.md"
    if standards_reference.exists():
        failures.extend(check_contains(standards_reference, [
            "They are not JSON Schema mirrors, AISOP flows, AIAP programs",
            "The release gate checks this boundary through `tests/test_ainp.py` and",
            "`tools/check_doc_sync.py`",
        ]))
    else:
        failures.append(f"{standards_reference}: missing standards reference page")

    for path in standards.rglob("*"):
        if not path.is_file() or path.suffix not in {".json", ".md"}:
            continue
        text = read_text(path)
        for token in STANDARD_FORBIDDEN_TOKENS:
            if token in text:
                failures.append(f"{path}: runtime/AIAP token `{token}` is forbidden in standards")
    return failures


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    seen = set()
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r}")
        seen.add(key)
        out[key] = value
    return out


def reject_constant(const: str) -> None:
    raise ValueError(f"non-standard JSON literal {const!r}")


def is_intentional_invalid_fixture(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).parts
    return len(rel) >= 3 and rel[:3] == ("tests", "fixtures", "invalid")


def strict_json_loads(text: str):
    return json.loads(text,
                      object_pairs_hook=reject_duplicate_keys,
                      parse_constant=reject_constant)


def check_json_files(root: Path) -> list[str]:
    failures = []
    for path in root.rglob("*.json"):
        rel = path.relative_to(root).parts
        if ".git" in rel:
            continue
        if is_intentional_invalid_fixture(path, root):
            continue
        try:
            strict_json_loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path}: invalid JSON: {exc}")
    return failures


def check_error_code_reference(root: Path) -> list[str]:
    reference = root / "docs" / "reference" / "error-codes.md"
    if not reference.exists():
        return [f"{reference}: missing error-code reference"]
    documented = set(re.findall(r"`(AINP_[EWI]_[A-Z0-9_]+)`", read_text(reference)))
    tool_text = "\n".join(read_text(path) for path in (root / "tools").glob("*.py"))
    implemented = set(re.findall(r"AINP_[EWI]_[A-Z0-9_]+", tool_text))
    implemented.update(
        code.replace("AINP_W_", "AINP_E_", 1)
        for code in list(implemented)
        if code.startswith("AINP_W_")
    )
    missing = sorted(documented - implemented)
    return [f"{reference}: documented code not emitted by tools: {code}" for code in missing]


def check_stale_protocol_names(root: Path) -> list[str]:
    failures = []
    text_suffixes = {
        ".md", ".json", ".py", ".ps1", ".yml", ".yaml", ".toml", ".txt", "",
    }
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if ".git" in path.parts:
            continue
        if STALE_PROTOCOL_PATTERN.search(rel):
            failures.append(
                f"{path}: stale protocol identifier is forbidden"
            )
            continue
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if STALE_PROTOCOL_PATTERN.search(text):
            failures.append(
                f"{path}: stale protocol identifier is forbidden"
            )
    return failures


def public_failure(message: str, root: Path) -> str:
    return PublicOutput(__file__, bases=[str(root)]).sanitize_text(message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check AINP documentation command synchronization.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    failures: list[str] = []
    actual_test_count = count_test_functions(root)
    for rel in DOC_COMMAND_TARGETS:
        path = root / rel
        if not path.exists():
            failures.append(f"{path}: missing documentation target")
            continue
        failures.extend(check_contains(path, COMMANDS[:9]))
        failures.extend(check_forbidden(path, actual_test_count))

    workflow = root / ".github" / "workflows" / "validate.yml"
    if workflow.exists():
        failures.extend(check_contains(workflow, WORKFLOW_NEEDLES))
    else:
        failures.append(f"{workflow}: missing CI workflow")

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        failures.extend(check_contains(pyproject, PYPROJECT_NEEDLES))
    else:
        failures.append(f"{pyproject}: missing project metadata")

    mkdocs = root / "mkdocs.yml"
    if mkdocs.exists():
        failures.extend(check_contains(mkdocs, MKDOCS_NEEDLES))
    else:
        failures.append(f"{mkdocs}: missing MkDocs navigation")

    release_script = root / "scripts" / "release_check.ps1"
    if release_script.exists():
        failures.extend(check_contains(release_script, RELEASE_SCRIPT_NEEDLES))
    else:
        failures.append(f"{release_script}: missing local release gate")

    for rel in ("README.md", "README_CN.md", "CONTRIBUTING.md", "CONTRIBUTING_CN.md", "tests/README.md", "CHANGELOG.md"):
        path = root / rel
        if path.exists():
            failures.extend(check_forbidden(path, actual_test_count))

    failures.extend(check_schema_single_source(root))
    failures.extend(check_standards_layer(root))
    failures.extend(check_json_files(root))
    failures.extend(check_error_code_reference(root))
    failures.extend(check_stale_protocol_names(root))
    public_failures = [public_failure(failure, root) for failure in failures]

    if args.json:
        print(json.dumps({"failures": public_failures,
                          "failure_count": len(public_failures)}, indent=2))
    elif failures:
        for failure in public_failures:
            print(failure)
        print(f"doc sync failed: {len(public_failures)} problem(s)", file=sys.stderr)
    else:
        print("doc sync ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
