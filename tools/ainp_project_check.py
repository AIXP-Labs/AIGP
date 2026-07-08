#!/usr/bin/env python3
"""ainp_project_check.py — AINP v1.0.0 project package checker.

Checks one complete AINP project package:

  <name>_ainp/
  ├── AINP.md
  ├── ainp/
  │   ├── <name>.generation.json
  │   └── <name>.generationreport.json
  │   └── <name>_feedback.generationfeedback.json
  └── <name>/
      └── artifact files

AINP.md is the project package declaration, index and validation entry point,
analogous to AIAP.md in AIAP packages but scoped to generation projects. The
`ainp/` directory is the AINP plan folder, and `<name>/` is the project content
folder. The plan folder and content folder are co-equal parts of a complete
AINP package: the report binds the plan to concrete generated artifacts under
the content folder, and feedback binds content review back to the same plan
generation id. AINP.md is not a trust proof; the checker still delegates the
release evidence chain to ainp_release_check.py.
The checker additionally validates that the plan's content_architecture points
inside the project content directory and that feedback issues can bind back to
declared files/points.

Zero-dependency: Python 3.10+ stdlib only.
Exit codes: 0 = no FAIL, 1 = FAIL present, 2 = usage/tool error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

try:
    from .ainp_release_check import validate_against_schema as release_validate_against_schema
    from .ainp_release_check import strict_json_loads
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_release_check import validate_against_schema as release_validate_against_schema
    from ainp_release_check import strict_json_loads
    from ainp_public import PublicOutput

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*_ainp$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(-((0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(\.(0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(\+([0-9A-Za-z-]+)(\.([0-9A-Za-z-]+))*)?$"
)
SCHEME_OR_DRIVE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
STATUS = {"draft", "under_review", "approved", "active", "superseded", "retired"}
REFERENCE_SOURCE_TYPES = {"local_file", "external_uri"}
REFERENCE_KINDS = {
    "protocol_spec", "schema", "template", "brief", "style_guide",
    "interface_spec", "research_material", "policy", "example", "other",
}
REQUIRED_FIELDS = {
    "protocol", "authority", "axiom_0", "name", "version", "summary", "status",
    "plan_dir", "content_dir", "plan", "report",
}
FEEDBACK_REQUIRED_STATUSES = {"approved", "active"}
REQUIRED_SECTIONS = (
    "## Project Declaration",
    "## Generation Plan",
    "## Content Artifacts",
    "## Feedback Loop",
    "## How To Validate",
    "## Honesty Boundary",
)
SELF_TRUST_FIELDS = {"safe", "verified", "original", "trusted", "authentic"}
SIDE_SCHEMAS = {
    "feedback": "ainp-generationfeedback-v1.0.0.schema.json",
    "space": "ainp-generation-space-v1.0.0.schema.json",
}
REFERENCE_MANIFEST_SCHEMA = "ainp-reference-manifest-v1.0.0.schema.json"
PUBLIC_OUTPUT = PublicOutput(__file__)


def add(items: list[dict], level: str, code: str, rule: str, message: str,
        path: str = "") -> None:
    items.append({"level": level, "code": code, "rule": rule,
                  "message": message, "path": path})


def add_public_base(path: str | None) -> None:
    PUBLIC_OUTPUT.add_base(path)


def display_path(path: str) -> str:
    return PUBLIC_OUTPUT.display_path(path)


def sanitize_text(text: str) -> str:
    return PUBLIC_OUTPUT.sanitize_text(text)


def public_findings(findings: list[dict]) -> list[dict]:
    return PUBLIC_OUTPUT.public_findings(findings)


def has_fail(findings: list[dict]) -> bool:
    return any(item.get("level") == "fail" for item in findings)


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(path: str, findings: list[dict]) -> tuple[dict, str]:
    try:
        text = open(path, encoding="utf-8-sig").read()
    except OSError as e:
        add(findings, "fail", "AINP_E_P2_AINP_MD_UNREADABLE", "P2",
            f"cannot read AINP.md: {e}", path)
        return {}, ""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        add(findings, "fail", "AINP_E_P5_FRONTMATTER_MISSING", "P5",
            "AINP.md must start with YAML-style frontmatter delimited by ---", path)
        return {}, text
    close_index = None
    for i, line in enumerate(lines[1:], start=1):
        line_body = line.rstrip("\r\n")
        if line_body == "---":
            close_index = i
            break
        if line_body.startswith("---"):
            add(findings, "fail", "AINP_E_P5_FRONTMATTER_MISSING", "P5",
                "AINP.md frontmatter closing delimiter must be an exact --- line", path)
            return {}, text
    if close_index is None:
        add(findings, "fail", "AINP_E_P5_FRONTMATTER_MISSING", "P5",
            "AINP.md frontmatter closing delimiter is missing", path)
        return {}, text
    front = [line.rstrip("\r\n") for line in lines[1:close_index]]
    body = "".join(lines[close_index + 1:])
    data: dict[str, str] = {}
    for line_no, raw in enumerate(front, start=2):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            add(findings, "fail", "AINP_E_P5_FRONTMATTER_BAD_LINE", "P5",
                f"frontmatter line {line_no} is not a simple key: value pair", path)
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not NAME_RE.match(key):
            add(findings, "fail", "AINP_E_P5_FRONTMATTER_BAD_KEY", "P5",
                f"frontmatter key {key!r} must be snake_case", path)
            continue
        if key in data:
            add(findings, "fail", "AINP_E_P5_FRONTMATTER_DUPLICATE_KEY", "P5",
                f"frontmatter key {key!r} appears more than once", path)
            continue
        data[key] = strip_quotes(value)
    return data, body


def resolve_project_path(root: str, rel: str, findings: list[dict], where: str,
                         code: str = "AINP_E_P5_PATH_ESCAPES") -> str | None:
    if not isinstance(rel, str) or not rel:
        add(findings, "fail", code, "P5", f"{where} must be a non-empty relative path", root)
        return None
    if os.path.isabs(rel) or SCHEME_OR_DRIVE_RE.match(rel):
        add(findings, "fail", code, "P5",
            f"{where} must be project-root relative, not absolute, URI, or drive-relative: {rel!r}",
            root)
        return None
    root_real = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_real, rel))
    try:
        inside = os.path.commonpath([root_real, target]) == root_real
    except ValueError:
        inside = False
    if not inside:
        add(findings, "fail", code, "P5",
            f"{where} escapes the AINP project package root: {rel!r}", root)
        return None
    return target


def path_inside(base: str, path: str) -> bool:
    base_real = os.path.realpath(base)
    path_real = os.path.realpath(path)
    try:
        return os.path.commonpath([base_real, path_real]) == base_real
    except ValueError:
        return False


def run_release(root: str, plan: str, report: str, findings: list[dict]) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        sys.executable,
        "-B",
        os.path.join(here, "ainp_release_check.py"),
        plan,
        "--report", report,
        "--project-root", root,
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    try:
        data = strict_json_loads(proc.stdout)
        tool_findings = data.get("findings", [])
        if not isinstance(tool_findings, list):
            raise ValueError("findings is not a list")
    except (json.JSONDecodeError, ValueError, RecursionError) as e:
        add(findings, "fail", "AINP_E_P7_RELEASE_TOOL_OUTPUT", "P7",
            f"ainp_release_check.py did not produce valid JSON: {e}; stderr={proc.stderr!r}",
            root)
        return
    if proc.returncode not in (0, 1):
        add(findings, "fail", "AINP_E_P7_RELEASE_TOOL_EXIT", "P7",
            f"ainp_release_check.py exited with unexpected code {proc.returncode}; "
            f"stderr={proc.stderr!r}", root)
    elif proc.returncode == 1 and not has_fail(tool_findings):
        add(findings, "fail", "AINP_E_P7_RELEASE_TOOL_EXIT", "P7",
            "ainp_release_check.py exited with code 1 but emitted no FAIL finding",
            root)
    findings.extend(tool_findings)


def run_schema_validate(files: list[tuple[str, str]], findings: list[dict]) -> None:
    for kind, path in files:
        raw_findings: list[dict] = []
        release_validate_against_schema(path, SIDE_SCHEMAS[kind], raw_findings,
                                        f"project {kind}")
        for item in raw_findings:
            code_map = {
                "AINP_E_RELEASE_SCHEMA_UNREADABLE": "AINP_E_P6_SCHEMA_UNREADABLE",
                "AINP_E_RELEASE_JSON_UNREADABLE": "AINP_E_P6_JSON_UNREADABLE",
                "AINP_E_RELEASE_SCHEMA_INVALID": "AINP_E_P6_SCHEMA_INVALID",
            }
            add(findings, item.get("level", "fail"),
                code_map.get(item.get("code"), "AINP_E_P6_SCHEMA_INVALID"),
                "P6",
                f"{kind} side file schema check failed: {item.get('message', '')}",
                item.get("path", path))


def run_validate(files: list[str], findings: list[dict]) -> None:
    if not files:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        sys.executable,
        "-B",
        os.path.join(here, "ainp_validate.py"),
        *files,
        "--mode", "strict",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    try:
        data = strict_json_loads(proc.stdout)
        tool_findings = data.get("findings", [])
        if not isinstance(tool_findings, list):
            raise ValueError("findings is not a list")
    except (json.JSONDecodeError, ValueError, RecursionError) as e:
        add(findings, "fail", "AINP_E_P6_VALIDATE_TOOL_OUTPUT", "P6",
            f"ainp_validate.py did not produce valid JSON for project side files: "
            f"{e}; stderr={proc.stderr!r}")
        return
    if proc.returncode not in (0, 1):
        add(findings, "fail", "AINP_E_P6_VALIDATE_TOOL_EXIT", "P6",
            f"ainp_validate.py exited with unexpected code {proc.returncode}; "
            f"stderr={proc.stderr!r}")
    elif proc.returncode == 1 and not has_fail(tool_findings):
        add(findings, "fail", "AINP_E_P6_VALIDATE_TOOL_EXIT", "P6",
            "ainp_validate.py exited with code 1 but emitted no FAIL finding")
    findings.extend(tool_findings)


def run_reference_manifest_schema_validate(path: str, findings: list[dict]) -> None:
    raw_findings: list[dict] = []
    release_validate_against_schema(path, REFERENCE_MANIFEST_SCHEMA, raw_findings,
                                    "project references manifest")
    for item in raw_findings:
        code_map = {
            "AINP_E_RELEASE_SCHEMA_UNREADABLE": "AINP_E_P11_SCHEMA_UNREADABLE",
            "AINP_E_RELEASE_JSON_UNREADABLE": "AINP_E_P11_MANIFEST_UNREADABLE",
            "AINP_E_RELEASE_SCHEMA_INVALID": "AINP_E_P11_MANIFEST_SCHEMA_INVALID",
        }
        add(findings, item.get("level", "fail"),
            code_map.get(item.get("code"), "AINP_E_P11_MANIFEST_SCHEMA_INVALID"),
            "P11",
            f"references manifest schema check failed: {item.get('message', '')}",
            item.get("path", path))


def load_json_file(path: str, findings: list[dict], code: str, rule: str):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return strict_json_loads(fh.read())
    except (OSError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        add(findings, "fail", code, rule, f"cannot read JSON: {exc}", path)
        return None


def resolve_project_path_silent(root: str, rel: str) -> str | None:
    if not isinstance(rel, str) or not rel:
        return None
    if os.path.isabs(rel) or SCHEME_OR_DRIVE_RE.match(rel):
        return None
    root_real = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_real, rel))
    try:
        if os.path.commonpath([root_real, target]) != root_real:
            return None
    except ValueError:
        return None
    return target


def check_report_artifacts_under_content_dir(root: str, report: str,
                                             content_dir_path: str,
                                             findings: list[dict]) -> None:
    doc = load_json_file(report, findings, "AINP_E_P7_REPORT_UNREADABLE", "P7")
    if not isinstance(doc, dict):
        return
    report_payload = doc.get("generationreport")
    if not isinstance(report_payload, dict):
        return
    artifacts = report_payload.get("artifacts")
    if not isinstance(artifacts, list):
        return
    for i, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        raw = artifact.get("path")
        target = resolve_project_path_silent(root, raw)
        if target is None:
            continue  # R3/release gate reports invalid or escaping paths.
        if not path_inside(content_dir_path, target):
            add(findings, "fail", "AINP_E_P7_ARTIFACT_OUTSIDE_CONTENT_DIR", "P7",
                f"generationreport.artifacts[{i}].path must live under the project "
                f"content directory declared by AINP.md.content_dir (got {raw!r})",
                report)


def payload_object(doc, key: str) -> dict:
    if isinstance(doc, dict) and isinstance(doc.get(key), dict):
        return doc[key]
    return {}


def content_files_by_id(plan_payload: dict) -> dict:
    arch = plan_payload.get("content_architecture") if isinstance(plan_payload, dict) else None
    files = arch.get("files") if isinstance(arch, dict) else None
    if not isinstance(files, list):
        return {}
    out = {}
    for item in files:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
            out[item["id"]] = item
    return out


def check_content_architecture_under_content_dir(root: str, plan: str,
                                                 content_dir_path: str,
                                                 findings: list[dict]) -> None:
    doc = load_json_file(plan, findings, "AINP_E_P10_PLAN_UNREADABLE", "P10")
    plan_payload = payload_object(doc, "generation")
    arch = plan_payload.get("content_architecture") if isinstance(plan_payload, dict) else None
    if not isinstance(arch, dict):
        add(findings, "fail", "AINP_E_P10_CONTENT_ARCHITECTURE_REQUIRED", "P10",
            "complete AINP project packages require generation.content_architecture "
            "so the plan can declare the content root, files and per-file points",
            plan)
        return

    root_rel = arch.get("root")
    root_path = resolve_project_path_silent(root, root_rel)
    if root_path is None:
        add(findings, "fail", "AINP_E_P10_CONTENT_ROOT_INVALID", "P10",
            f"content_architecture.root must be a safe project-root relative path: {root_rel!r}",
            plan)
    elif not path_inside(content_dir_path, root_path):
        add(findings, "fail", "AINP_E_P10_CONTENT_ROOT_OUTSIDE_CONTENT_DIR", "P10",
            "content_architecture.root must resolve under AINP.md.content_dir",
            plan)

    for i, content_file in enumerate(arch.get("files") if isinstance(arch.get("files"), list) else []):
        if not isinstance(content_file, dict):
            continue
        raw = content_file.get("path")
        target = resolve_project_path_silent(root, raw)
        if target is None:
            add(findings, "fail", "AINP_E_P10_CONTENT_FILE_PATH_INVALID", "P10",
                f"content_architecture.files[{i}].path must be a safe project-root "
                f"relative path: {raw!r}", plan)
        elif not path_inside(content_dir_path, target):
            add(findings, "fail", "AINP_E_P10_CONTENT_FILE_OUTSIDE_CONTENT_DIR", "P10",
                f"content_architecture.files[{i}].path must live under "
                f"AINP.md.content_dir (got {raw!r})", plan)


def check_feedback_issue_targets(plan_payload: dict, feedback_payload: dict,
                                 findings: list[dict], feedback: str) -> None:
    files_by_id = content_files_by_id(plan_payload)
    if not files_by_id:
        return
    points_by_file = {
        file_id: {
            point.get("id") for point in content_file.get("points", [])
            if isinstance(point, dict) and isinstance(point.get("id"), str)
        }
        for file_id, content_file in files_by_id.items()
    }
    issues = feedback_payload.get("issues")
    if not isinstance(issues, list):
        return
    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        target = issue.get("target")
        file_id = issue.get("file_id")
        point_id = issue.get("point_id")
        if target == "file" and not file_id:
            add(findings, "fail", "AINP_E_P6_FEEDBACK_TARGET_INCOMPLETE", "P6",
                f"issues[{i}] target=file requires file_id", feedback)
            continue
        if target == "point" and (not file_id or not point_id):
            add(findings, "fail", "AINP_E_P6_FEEDBACK_TARGET_INCOMPLETE", "P6",
                f"issues[{i}] target=point requires file_id and point_id", feedback)
            continue
        if file_id:
            if file_id not in files_by_id:
                add(findings, "fail", "AINP_E_P6_FEEDBACK_UNKNOWN_FILE_ID", "P6",
                    f"issues[{i}].file_id {file_id!r} is not declared in "
                    "plan.content_architecture.files", feedback)
                continue
            if point_id and point_id not in points_by_file.get(file_id, set()):
                add(findings, "fail", "AINP_E_P6_FEEDBACK_UNKNOWN_POINT_ID", "P6",
                    f"issues[{i}].point_id {point_id!r} is not declared under "
                    f"content file {file_id!r}", feedback)
        elif point_id:
            add(findings, "fail", "AINP_E_P6_FEEDBACK_TARGET_INCOMPLETE", "P6",
                f"issues[{i}].point_id requires a file_id", feedback)


def check_feedback_loop(plan: str, report: str, feedback: str,
                        findings: list[dict]) -> None:
    plan_doc = load_json_file(plan, findings, "AINP_E_P6_PLAN_UNREADABLE", "P6")
    report_doc = load_json_file(report, findings, "AINP_E_P6_REPORT_UNREADABLE", "P6")
    feedback_doc = load_json_file(feedback, findings, "AINP_E_P6_FEEDBACK_UNREADABLE", "P6")
    if not all(isinstance(doc, dict) for doc in (plan_doc, report_doc, feedback_doc)):
        return

    plan_id = payload_object(plan_doc, "generation").get("id")
    report_id = payload_object(report_doc, "generationreport").get("generation_id")
    plan_payload = payload_object(plan_doc, "generation")
    feedback_payload = payload_object(feedback_doc, "generationfeedback")
    feedback_id = feedback_payload.get("generation_id")
    if not all(isinstance(item, str) and item for item in (plan_id, report_id, feedback_id)):
        return  # Schema/FB1/R2 already report missing or malformed identifiers.
    if report_id != plan_id:
        add(findings, "fail", "AINP_E_P6_REPORT_ID_MISMATCH", "P6",
            f"report generation_id {report_id!r} must match plan id {plan_id!r}",
            report)
    if feedback_id != plan_id:
        add(findings, "fail", "AINP_E_P6_FEEDBACK_ID_MISMATCH", "P6",
            f"feedback generation_id {feedback_id!r} must match plan id {plan_id!r}",
            feedback)
    check_feedback_issue_targets(plan_payload, feedback_payload, findings, feedback)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_reference_manifest(root: str, plan_dir_path: str, meta: dict,
                             findings: list[dict]) -> None:
    references_dir = os.path.join(plan_dir_path, "references")
    if os.path.exists(references_dir) and not os.path.isdir(references_dir):
        add(findings, "fail", "AINP_E_P11_REFERENCES_DIR_NOT_DIRECTORY", "P11",
            "ainp/references exists but is not a directory", references_dir)
        return

    declared = meta.get("references")
    manifest_path: str | None = None
    if declared:
        manifest_path = resolve_project_path(
            root, declared, findings, "references",
            code="AINP_E_P11_REFERENCES_PATH_INVALID",
        )
        if manifest_path and not path_inside(references_dir, manifest_path):
            add(findings, "fail", "AINP_E_P11_MANIFEST_NOT_IN_REFERENCES_DIR", "P11",
                "AINP.md references path must live under ainp/references/", manifest_path)
        if manifest_path and not os.path.isfile(manifest_path):
            add(findings, "fail", "AINP_E_P11_MANIFEST_MISSING", "P11",
                "AINP.md references path does not exist", manifest_path)
            return
    elif os.path.isdir(references_dir):
        candidate = os.path.join(references_dir, "reference_manifest.json")
        if os.path.isfile(candidate):
            manifest_path = candidate
        else:
            add(findings, "warn", "AINP_W_P11_REFERENCES_MANIFEST_MISSING", "P11",
                "ainp/references/ exists but no reference_manifest.json is present; "
                "references/templates are not machine-indexed", references_dir)
            return
    else:
        return

    if not manifest_path or not os.path.isfile(manifest_path):
        return

    run_reference_manifest_schema_validate(manifest_path, findings)
    doc = load_json_file(manifest_path, findings, "AINP_E_P11_MANIFEST_UNREADABLE", "P11")
    manifest = payload_object(doc, "reference_manifest")
    references = manifest.get("references") if isinstance(manifest, dict) else None
    if not isinstance(references, list):
        return

    seen_ids: set[str] = set()
    for i, item in enumerate(references):
        if not isinstance(item, dict):
            continue
        ref_id = item.get("id")
        if isinstance(ref_id, str):
            if ref_id in seen_ids:
                add(findings, "fail", "AINP_E_P11_DUPLICATE_REFERENCE_ID", "P11",
                    f"reference_manifest.references[{i}].id {ref_id!r} is duplicated",
                    manifest_path)
            seen_ids.add(ref_id)
        kind = item.get("kind")
        if kind is not None and kind not in REFERENCE_KINDS:
            add(findings, "fail", "AINP_E_P11_BAD_REFERENCE_KIND", "P11",
                f"reference kind must be one of {sorted(REFERENCE_KINDS)}", manifest_path)
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        source_type = source.get("type")
        if source_type is not None and source_type not in REFERENCE_SOURCE_TYPES:
            add(findings, "fail", "AINP_E_P11_BAD_SOURCE_TYPE", "P11",
                f"reference source.type must be one of {sorted(REFERENCE_SOURCE_TYPES)}",
                manifest_path)
            continue
        if source_type == "local_file":
            raw = source.get("path")
            if source.get("uri"):
                add(findings, "fail", "AINP_E_P11_LOCAL_REFERENCE_URI_INVALID", "P11",
                    f"references[{i}].source.type=local_file must use source.path; "
                    "use source_url for external origin hints",
                    manifest_path)
            target = resolve_project_path_silent(root, raw)
            if target is None:
                add(findings, "fail", "AINP_E_P11_LOCAL_REFERENCE_PATH_INVALID", "P11",
                    f"references[{i}].source.path must be a safe project-root relative path: {raw!r}",
                    manifest_path)
                continue
            if not path_inside(references_dir, target):
                add(findings, "fail", "AINP_E_P11_LOCAL_REFERENCE_OUTSIDE_REFERENCES_DIR", "P11",
                    f"references[{i}].source.path must live under ainp/references/ (got {raw!r})",
                    manifest_path)
                continue
            if not os.path.isfile(target):
                add(findings, "fail", "AINP_E_P11_LOCAL_REFERENCE_MISSING", "P11",
                    f"local reference/template file does not exist: {raw!r}", manifest_path)
                continue
            declared_hash = item.get("sha256")
            if not declared_hash:
                add(findings, "warn", "AINP_W_P11_LOCAL_REFERENCE_HASH_MISSING", "P11",
                    f"local reference/template {raw!r} has no sha256 integrity anchor",
                    manifest_path)
            elif declared_hash != sha256_file(target):
                add(findings, "fail", "AINP_E_P11_REFERENCE_HASH_MISMATCH", "P11",
                    f"local reference/template {raw!r} sha256 does not match current file",
                    manifest_path)
        elif source_type == "external_uri":
            if source.get("path"):
                add(findings, "fail", "AINP_E_P11_EXTERNAL_REFERENCE_PATH_INVALID", "P11",
                    f"references[{i}].source.type=external_uri must use source.uri, not source.path",
                    manifest_path)
            if item.get("sha256"):
                add(findings, "fail", "AINP_E_P11_EXTERNAL_REFERENCE_HASH_UNVERIFIABLE", "P11",
                    f"references[{i}].sha256 is only allowed for local_file references; "
                    "local tools do not fetch external_uri entries",
                    manifest_path)
            if not source.get("uri"):
                add(findings, "fail", "AINP_E_P11_EXTERNAL_REFERENCE_URI_MISSING", "P11",
                    f"references[{i}].source.type=external_uri requires source.uri", manifest_path)


def check_project(root: str, findings: list[dict]) -> None:
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        add(findings, "fail", "AINP_E_P1_PROJECT_ROOT_MISSING", "P1",
            "AINP project package root must be an existing directory", root)
        return

    package = os.path.basename(root)
    if not PACKAGE_RE.match(package):
        add(findings, "fail", "AINP_E_P1_BAD_PROJECT_DIR", "P1",
            "AINP project package directory must be named <name>_ainp using snake_case",
            root)
    expected_name = package[:-len("_ainp")] if package.endswith("_ainp") else package

    root_entries = set(os.listdir(root))
    ainp_md = os.path.join(root, "AINP.md")
    lowercase = os.path.join(root, "ainp.md")
    if "ainp.md" in root_entries:
        add(findings, "fail", "AINP_E_P2_LOWERCASE_AINP_MD", "P2",
            "project package entry file must be uppercase AINP.md, matching AIAP.md style",
            lowercase)
    if "AINP.md" not in root_entries or not os.path.isfile(ainp_md):
        add(findings, "fail", "AINP_E_P2_AINP_MD_MISSING", "P2",
            "AINP project package root must contain AINP.md", ainp_md)
        return

    meta, body = parse_frontmatter(ainp_md, findings)
    for field in sorted(REQUIRED_FIELDS):
        if not meta.get(field):
            add(findings, "fail", "AINP_E_P5_REQUIRED_FIELD_MISSING", "P5",
                f"AINP.md frontmatter missing required field {field!r}", ainp_md)

    if meta.get("protocol") != "AINP v1.0.0":
        add(findings, "fail", "AINP_E_P5_BAD_PROTOCOL", "P5",
            "AINP.md protocol must be exactly 'AINP v1.0.0'", ainp_md)
    if meta.get("authority") != "ainp.dev":
        add(findings, "fail", "AINP_E_P5_BAD_AUTHORITY", "P5",
            "AINP.md authority must be ainp.dev", ainp_md)
    if meta.get("axiom_0") != "Human_Sovereignty_and_Wellbeing":
        add(findings, "fail", "AINP_E_P5_BAD_AXIOM_0", "P5",
            "AINP.md axiom_0 must be Human_Sovereignty_and_Wellbeing", ainp_md)
    if meta.get("name") != expected_name:
        add(findings, "fail", "AINP_E_P5_NAME_DIR_MISMATCH", "P5",
            f"AINP.md name must match package directory stem {expected_name!r}", ainp_md)
    if meta.get("version") and not SEMVER_RE.match(meta["version"]):
        add(findings, "fail", "AINP_E_P5_VERSION_NOT_SEMVER", "P5",
            "AINP.md version must be SemVer 2.0.0", ainp_md)
    if meta.get("status") and meta["status"] not in STATUS:
        add(findings, "fail", "AINP_E_P5_BAD_STATUS", "P5",
            f"AINP.md status must be one of {sorted(STATUS)}", ainp_md)
    for key in meta:
        if key in SELF_TRUST_FIELDS:
            add(findings, "fail", "AINP_E_P9_SELF_TRUST_CLAIM", "P9",
                f"AINP.md must not self-declare artifact trust via field {key!r}",
                ainp_md)

    plan_dir = meta.get("plan_dir", "")
    content_dir = meta.get("content_dir", "")
    if plan_dir.rstrip("/\\") != "ainp":
        add(findings, "fail", "AINP_E_P3_BAD_PLAN_DIR", "P3",
            "AINP.md plan_dir must be ainp/", ainp_md)
    if content_dir.rstrip("/\\") != expected_name:
        add(findings, "fail", "AINP_E_P4_BAD_CONTENT_DIR", "P4",
            f"AINP.md content_dir must be {expected_name}/", ainp_md)

    plan_dir_path = os.path.join(root, "ainp")
    content_dir_path = os.path.join(root, expected_name)
    if not os.path.isdir(plan_dir_path):
        add(findings, "fail", "AINP_E_P3_PLAN_DIR_MISSING", "P3",
            "AINP project package must contain ainp/ for plans, reports, feedback and space files",
            plan_dir_path)
    if not os.path.isdir(content_dir_path):
        add(findings, "fail", "AINP_E_P4_CONTENT_DIR_MISSING", "P4",
            f"AINP project package must contain {expected_name}/ for generated content",
            content_dir_path)

    plan = resolve_project_path(root, meta.get("plan", ""), findings, "plan")
    report = resolve_project_path(root, meta.get("report", ""), findings, "report")
    for label, path in (("plan", plan), ("report", report)):
        if path and not os.path.isfile(path):
            add(findings, "fail", "AINP_E_P5_PATH_MISSING", "P5",
                f"AINP.md {label} path does not exist", path)
        if path and not path_inside(plan_dir_path, path):
            add(findings, "fail", "AINP_E_P5_PATH_NOT_IN_AINP_DIR", "P5",
                f"AINP.md {label} path must live under ainp/", path)
    if meta.get("status") in FEEDBACK_REQUIRED_STATUSES and not meta.get("feedback"):
        add(findings, "fail", "AINP_E_P6_FEEDBACK_REQUIRED", "P6",
            "approved/active AINP project packages must declare AINP.md.feedback "
            "so content review can feed back to the plan", ainp_md)

    feedback_path: str | None = None
    side_files: list[str] = []
    side_schema_files: list[tuple[str, str]] = []
    for optional in ("feedback", "space"):
        if meta.get(optional):
            path = resolve_project_path(root, meta[optional], findings, optional)
            if path and not os.path.isfile(path):
                add(findings, "fail", "AINP_E_P5_PATH_MISSING", "P5",
                    f"AINP.md {optional} path does not exist", path)
            if path and not path_inside(plan_dir_path, path):
                add(findings, "fail", "AINP_E_P5_PATH_NOT_IN_AINP_DIR", "P5",
                    f"AINP.md {optional} path must live under ainp/", path)
            if path and os.path.isfile(path):
                if optional == "feedback":
                    feedback_path = path
                side_files.append(path)
                side_schema_files.append((optional, path))

    for section in REQUIRED_SECTIONS:
        if section not in body:
            add(findings, "fail", "AINP_E_P5_REQUIRED_SECTION_MISSING", "P5",
                f"AINP.md body missing required section {section!r}", ainp_md)

    run_schema_validate(side_schema_files, findings)
    run_validate(side_files, findings)
    check_reference_manifest(root, plan_dir_path, meta, findings)
    if plan and report and os.path.isfile(plan) and os.path.isfile(report):
        check_content_architecture_under_content_dir(root, plan, content_dir_path, findings)
        check_report_artifacts_under_content_dir(root, report, content_dir_path, findings)
        if feedback_path and os.path.isfile(feedback_path):
            check_feedback_loop(plan, report, feedback_path, findings)
        run_release(root, plan, report, findings)


def render(findings: list[dict], as_json: bool) -> None:
    findings = public_findings(findings)
    if as_json:
        print(json.dumps({"findings": findings,
                          "summary": {"fail": sum(1 for i in findings if i["level"] == "fail"),
                                      "warn": sum(1 for i in findings if i["level"] == "warn"),
                                      "info": sum(1 for i in findings if i["level"] == "info")}},
                         ensure_ascii=False, indent=2))
        return
    for i in findings:
        print(f"[{i['level'].upper():4}] {i['code']} ({i['rule']}) "
              f"{i.get('path', '')}: {i['message']}")
    fails = sum(1 for i in findings if i["level"] == "fail")
    warns = sum(1 for i in findings if i["level"] == "warn")
    print(f"RESULT: {'FAIL' if fails else 'PASS project-structure-valid'} "
          f"({fails} fail, {warns} warn)")
    print("NOTE: project-structure-valid proves package structure, schema/rule "
          "consistency and hash recomputability only. It is not legal compliance, "
          "rights verification, factual truth, approval authenticity, provider trust, "
          "watermark detectability, or content trust.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AINP v1.0.0 project package checker")
    ap.add_argument("project_root", help="<name>_ainp directory containing AINP.md")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    findings: list[dict] = []
    add_public_base(args.project_root)
    check_project(args.project_root, findings)
    render(findings, args.as_json)
    return 1 if any(i["level"] == "fail" for i in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
