#!/usr/bin/env python3
"""ainp_release_check.py — AINP v1.0.0 release gate wrapper.

Runs the complete release-side reference gate for one plan/report pair:

  1. plan/report/high-risk data validate against the bundled JSON Schemas
  2. tools/ainp_validate.py <plan> --mode release
  3. tools/ainp_report_check.py <report> --plan <plan> --mode release
  4. wrapper check: report.overall.conformant must be true

This is still structural/evidence-chain validation only. It proves that the
release package has the required plan, report, disclosure/gate records and
recomputable artifact hashes. It never proves legal safety, rights validity,
factual truth, approval authenticity, provider trust, watermark detectability,
or content trust.

Zero-dependency: Python 3.10+ stdlib only.
Exit codes: 0 = no FAIL, 1 = FAIL present, 2 = usage/tool error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PUBLIC_OUTPUT = PublicOutput(__file__)
MAX_NESTING_DEPTH = 150


def add(items: list[dict], level: str, code: str, rule: str, message: str,
        path: str = "") -> None:
    items.append({"level": level, "code": code, "rule": rule,
                  "message": message, "path": path})


def add_public_base(path: str | None) -> None:
    PUBLIC_OUTPUT.add_base(path)


def register_input_path(path: str | None) -> None:
    PUBLIC_OUTPUT.register_input_path(path)


def display_path(path: str) -> str:
    return PUBLIC_OUTPUT.display_path(path)


def sanitize_text(text: str) -> str:
    return PUBLIC_OUTPUT.sanitize_text(text)


def public_findings(findings: list[dict]) -> list[dict]:
    return PUBLIC_OUTPUT.public_findings(findings)


def infer_report_path(plan: str) -> str:
    if plan.endswith(".generation.json"):
        return plan[:-len(".generation.json")] + ".generationreport.json"
    return plan + ".generationreport.json"


def default_high_risk_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "schemas",
                                        "high_risk_types.v1.0.0.json"))


def schema_path(name: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "schemas", name))


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    seen = set()
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r} (parser-differential smuggling guard)")
        seen.add(key)
        out[key] = value
    return out


def reject_constant(const: str) -> None:
    raise ValueError(f"non-standard JSON literal {const} (NaN/Infinity) rejected")


def depth_exceeds(obj, limit: int) -> bool:
    stack = [(obj, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > limit:
            return True
        if isinstance(node, dict):
            stack.extend((value, depth + 1) for value in node.values())
        elif isinstance(node, list):
            stack.extend((value, depth + 1) for value in node)
    return False


def reject_excessive_depth(doc):
    if depth_exceeds(doc, MAX_NESTING_DEPTH):
        raise ValueError(
            f"nesting exceeds {MAX_NESTING_DEPTH} levels (untrusted-input guard)"
        )
    return doc


def strict_json_load(fh):
    return reject_excessive_depth(
        json.load(fh,
                  object_pairs_hook=reject_duplicate_keys,
                  parse_constant=reject_constant)
    )


def strict_json_loads(text: str):
    return reject_excessive_depth(
        json.loads(text,
                   object_pairs_hook=reject_duplicate_keys,
                   parse_constant=reject_constant)
    )


def load_json(path: str, findings: list[dict], code: str, label: str):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return strict_json_load(fh)
    except (OSError, json.JSONDecodeError, ValueError, RecursionError) as e:
        add(findings, "fail", code, "SCHEMA",
            f"cannot read {label}: {e}", path)
        return None


def json_type_ok(value, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def resolve_ref(root: dict, ref: str):
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported non-local $ref {ref!r}")
    node = root
    for raw in ref[2:].split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"unresolved $ref {ref!r}")
        node = node[part]
    return node


def schema_errors(value, schema: dict, root: dict, pointer: str,
                  depth: int = 0) -> list[str]:
    errors: list[str] = []
    validate_schema_node(value, schema, root, pointer, errors, depth)
    return errors


def validate_schema_node(value, schema: dict, root: dict, pointer: str,
                         errors: list[str], depth: int = 0) -> None:
    if depth > 200:
        errors.append(f"{pointer}: schema validation depth exceeded")
        return
    if "$ref" in schema:
        try:
            ref_schema = resolve_ref(root, schema["$ref"])
        except ValueError as e:
            errors.append(f"{pointer}: {e}")
            return
        validate_schema_node(value, ref_schema, root, pointer, errors, depth + 1)
        schema = {key: val for key, val in schema.items() if key != "$ref"}
        if not schema:
            return

    for i, item_schema in enumerate(schema.get("allOf") or []):
        if isinstance(item_schema, dict):
            validate_schema_node(value, item_schema, root, f"{pointer}/allOf[{i}]",
                                 errors, depth + 1)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        if not any(
            isinstance(item_schema, dict)
            and not schema_errors(value, item_schema, root, pointer, depth + 1)
            for item_schema in any_of
        ):
            errors.append(f"{pointer}: value does not match anyOf")

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        matches = sum(
            1 for item_schema in one_of
            if isinstance(item_schema, dict)
            and not schema_errors(value, item_schema, root, pointer, depth + 1)
        )
        if matches != 1:
            errors.append(f"{pointer}: value matches {matches} oneOf branches, expected 1")

    not_schema = schema.get("not")
    if isinstance(not_schema, dict) and not schema_errors(value, not_schema, root, pointer, depth + 1):
        errors.append(f"{pointer}: value matches forbidden `not` schema")

    if_schema = schema.get("if")
    if isinstance(if_schema, dict):
        matched = not schema_errors(value, if_schema, root, pointer, depth + 1)
        branch = schema.get("then") if matched else schema.get("else")
        if isinstance(branch, dict):
            validate_schema_node(value, branch, root, pointer, errors, depth + 1)

    declared_type = schema.get("type")
    if declared_type is not None:
        allowed = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(json_type_ok(value, t) for t in allowed):
            errors.append(f"{pointer}: expected type {allowed}, got "
                          f"{type(value).__name__}")
            return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{pointer}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{pointer}: value {value!r} not in enum {schema['enum']!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{pointer}: string shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{pointer}: string longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and re.match(schema["pattern"], value) is None:
            errors.append(f"{pointer}: string does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{pointer}: value below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{pointer}: value above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{pointer}: value not above exclusiveMinimum {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            errors.append(f"{pointer}: value not below exclusiveMaximum {schema['exclusiveMaximum']}")
        if "multipleOf" in schema:
            divisor = schema["multipleOf"]
            if not isinstance(divisor, (int, float)) or isinstance(divisor, bool) or divisor <= 0:
                errors.append(f"{pointer}: invalid multipleOf {divisor!r}")
            else:
                quotient = value / divisor
                if abs(quotient - round(quotient)) > 1e-12:
                    errors.append(f"{pointer}: value is not a multiple of {divisor}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{pointer}: array has fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{pointer}: array has more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") is True:
            seen = set()
            for item in value:
                key = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if key in seen:
                    errors.append(f"{pointer}: array items are not unique")
                    break
                seen.add(key)
        start_index = 0
        prefix_items = schema.get("prefixItems")
        if isinstance(prefix_items, list):
            for i, item_schema in enumerate(prefix_items[:len(value)]):
                if isinstance(item_schema, dict):
                    validate_schema_node(value[i], item_schema, root, f"{pointer}/{i}",
                                         errors, depth + 1)
            start_index = len(prefix_items)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(value[start_index:], start_index):
                validate_schema_node(item, item_schema, root, f"{pointer}/{i}",
                                     errors, depth + 1)
        elif item_schema is False and len(value) > start_index:
            errors.append(f"{pointer}: array has items after prefixItems but items=false")

    if isinstance(value, dict):
        props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        pattern_props = (
            schema.get("patternProperties")
            if isinstance(schema.get("patternProperties"), dict)
            else {}
        )
        required = schema.get("required") if isinstance(schema.get("required"), list) else []
        for name in required:
            if name not in value:
                errors.append(f"{pointer}: missing required property {name!r}")
        property_names = schema.get("propertyNames")
        if isinstance(property_names, dict):
            for name in value:
                validate_schema_node(name, property_names, root,
                                     f"{pointer}/propertyNames/{name}",
                                     errors, depth + 1)
        pattern_matched: set[str] = set()
        for pattern, prop_schema in pattern_props.items():
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                errors.append(f"{pointer}: invalid patternProperties regex {pattern!r}: {exc}")
                continue
            for name, item in value.items():
                if compiled.search(name):
                    pattern_matched.add(name)
                    if isinstance(prop_schema, dict):
                        validate_schema_node(item, prop_schema, root, f"{pointer}/{name}",
                                             errors, depth + 1)
        if schema.get("additionalProperties") is False:
            for name in sorted(set(value) - set(props)):
                if name not in pattern_matched:
                    errors.append(f"{pointer}: additional property {name!r} is not allowed")
        elif isinstance(schema.get("additionalProperties"), dict):
            for name in sorted(set(value) - set(props) - pattern_matched):
                validate_schema_node(value[name], schema["additionalProperties"], root,
                                     f"{pointer}/{name}", errors, depth + 1)
        for name, prop_schema in props.items():
            if name in value and isinstance(prop_schema, dict):
                validate_schema_node(value[name], prop_schema, root, f"{pointer}/{name}",
                                     errors, depth + 1)


def validate_against_schema(doc_path: str, schema_file: str, findings: list[dict],
                            label: str) -> None:
    schema = load_json(schema_path(schema_file), findings,
                       "AINP_E_RELEASE_SCHEMA_UNREADABLE", f"schema {schema_file}")
    doc = load_json(doc_path, findings, "AINP_E_RELEASE_JSON_UNREADABLE", label)
    if not isinstance(schema, dict) or doc is None:
        return
    errors: list[str] = []
    validate_schema_node(doc, schema, schema, "$", errors)
    max_errors = 25
    for err in errors[:max_errors]:
        add(findings, "fail", "AINP_E_RELEASE_SCHEMA_INVALID", "SCHEMA",
            f"{label} does not match {schema_file}: {err}", doc_path)
    if len(errors) > max_errors:
        add(findings, "fail", "AINP_E_RELEASE_SCHEMA_INVALID", "SCHEMA",
            f"{label} has {len(errors) - max_errors} additional schema errors "
            "after truncation", doc_path)


def run_json_tool(script: str, args: list[str]) -> tuple[int, list[dict]]:
    here = os.path.dirname(os.path.abspath(__file__))
    cmd = [sys.executable, "-B", os.path.join(here, script), *args, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    try:
        data = strict_json_loads(proc.stdout)
        findings = data.get("findings", [])
        if not isinstance(findings, list):
            raise ValueError("findings is not a list")
    except (json.JSONDecodeError, ValueError, RecursionError) as e:
        findings = []
        add(findings, "fail", "AINP_E_RELEASE_TOOL_OUTPUT", "RELEASE",
            f"{script} did not produce valid JSON output: {e}; stderr={proc.stderr!r}")
        return 2, findings
    if proc.returncode not in (0, 1):
        add(findings, "fail", "AINP_E_RELEASE_TOOL_EXIT", "RELEASE",
            f"{script} exited with unexpected code {proc.returncode}; stderr={proc.stderr!r}")
    elif proc.returncode == 1 and not any(item.get("level") == "fail" for item in findings):
        add(findings, "fail", "AINP_E_RELEASE_TOOL_EXIT", "RELEASE",
            f"{script} exited with code 1 but emitted no FAIL finding")
    return proc.returncode, findings


def load_report_overall(report: str, findings: list[dict]) -> None:
    try:
        with open(report, encoding="utf-8-sig") as fh:
            doc = strict_json_load(fh)
    except (OSError, json.JSONDecodeError, ValueError, RecursionError) as e:
        add(findings, "fail", "AINP_E_RELEASE_REPORT_UNREADABLE", "RELEASE",
            f"cannot read report for final conformant gate: {e}", report)
        return
    r = doc.get("generationreport") if isinstance(doc, dict) else None
    overall = r.get("overall") if isinstance(r, dict) and isinstance(r.get("overall"), dict) else {}
    if overall.get("conformant") is not True:
        add(findings, "fail", "AINP_E_RELEASE_NOT_CONFORMANT", "RELEASE",
            "release gate requires report.overall.conformant=true; a structurally "
            "valid report with conformant=false is evidence of a failed run, not a "
            "releasable artifact", report)


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
    print(f"RESULT: {'FAIL' if fails else 'PASS release-structure-valid'} "
          f"({fails} fail, {warns} warn)")
    print("NOTE: release-structure-valid proves only that the reference release "
          "gate's structural/evidence-chain checks passed. It is not legal "
          "compliance, rights verification, factual truth, approval authenticity, "
          "provider trust, watermark detectability, or content trust.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AINP v1.0.0 release gate wrapper")
    ap.add_argument("plan", help="*.generation.json")
    ap.add_argument("--report", default=None,
                    help="*.generationreport.json (default: replace .generation.json)")
    ap.add_argument("--archive", action="append", default=[],
                    help="archived-plan blob dir(s) for report R8 (repeatable)")
    ap.add_argument("--project-root", default=None,
                    help="AINP project package root; when set, release artifact paths "
                         "are recomputed relative to this sandbox instead of the "
                         "report directory")
    ap.add_argument("--high-risk-types", default=None,
                    help="path to high_risk_types.v1.0.0.json")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    findings: list[dict] = []
    plan = os.path.abspath(args.plan)
    report = os.path.abspath(args.report or infer_report_path(args.plan))
    project_root = os.path.abspath(args.project_root) if args.project_root else None
    register_input_path(args.plan)
    register_input_path(args.report)
    register_input_path(report)
    add_public_base(project_root)
    register_input_path(args.high_risk_types)
    for archive in args.archive:
        add_public_base(archive)

    if not os.path.exists(plan):
        add(findings, "fail", "AINP_E_RELEASE_PLAN_MISSING", "RELEASE",
            "release gate requires a plan file", plan)
    if not os.path.exists(report):
        add(findings, "fail", "AINP_E_RELEASE_REPORT_MISSING", "RELEASE",
            "release gate requires a generationreport; plan-only release validation "
            "is not a complete release gate", report)
    if project_root and not os.path.isdir(project_root):
        add(findings, "fail", "AINP_E_RELEASE_PROJECT_ROOT_MISSING", "RELEASE",
            "project-root must be an existing AINP project package directory",
            project_root)

    if os.path.exists(plan):
        validate_against_schema(plan, "ainp-generation-v1.0.0.schema.json",
                                findings, "plan")
    if os.path.exists(report):
        validate_against_schema(report, "ainp-generationreport-v1.0.0.schema.json",
                                findings, "report")
    hrt_path = os.path.abspath(args.high_risk_types) if args.high_risk_types \
        else default_high_risk_path()
    if os.path.exists(hrt_path):
        validate_against_schema(hrt_path, "high_risk_types-v1.0.0.schema.json",
                                findings, "high_risk_types")

    plan_args = [plan, "--mode", "release"]
    if args.high_risk_types:
        plan_args += ["--high-risk-types", args.high_risk_types]
    _, plan_findings = run_json_tool("ainp_validate.py", plan_args)
    findings.extend(plan_findings)

    if os.path.exists(report):
        report_args = [report, "--plan", plan, "--mode", "release"]
        if project_root:
            report_args += ["--artifact-root", project_root]
        for archive in args.archive:
            report_args += ["--archive", archive]
        _, report_findings = run_json_tool("ainp_report_check.py", report_args)
        findings.extend(report_findings)
        load_report_overall(report, findings)

    render(findings, args.as_json)
    return 1 if any(i["level"] == "fail" for i in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
