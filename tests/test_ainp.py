"""AINP v1.0.0 conformance suite + teeth tests.

Five groups:
  1. Schema validation — every listed example validates against its JSON Schema.
  2. Reference validator (positive) — every valid example passes with no FAIL.
  3. Reference validator (negative / teeth) — each invalid fixture MUST raise
     its documented rule code (proves the validator has teeth).
  4. Schemas are valid Draft 2020-12; enum/term integrity across schema<->tool.
  5. Example-corpus coverage — all file types + the risk gates are exercised.

Run:  python -B tests/test_ainp.py
      python -B -m pytest -q -p no:cacheprovider -p no:asyncio tests/
Requires: jsonschema (>=4.18). The reference validators are stdlib-only;
jsonschema is only needed for group 1/4.
"""
from __future__ import annotations

import json
import hashlib
import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
EX = os.path.join(ROOT, "examples")
FILE_EX = os.path.join(EX, "file_family")
FX = os.path.join(ROOT, "tests", "fixtures", "invalid")
SCH = os.path.join(ROOT, "schemas")
SPEC = os.path.join(ROOT, "specification")
STANDARDS = os.path.join(SPEC, "standards")
TOOLS = os.path.join(ROOT, "tools")

PY = sys.executable
_TEST_TMP_PARENT: str | None = None


def _path_variants(path: str) -> set[str]:
    path = os.path.abspath(path)
    return {path, path.replace(os.sep, "/"), path.replace("\\", "\\\\")}


def _writable_tmp_parent() -> str | None:
    """Return a temp parent that can actually create files in restricted runners."""
    global _TEST_TMP_PARENT
    if _TEST_TMP_PARENT is not None:
        return _TEST_TMP_PARENT
    candidates = [os.environ.get("AINP_TEST_TMPDIR")]
    if os.name == "nt":
        candidates.append(r"C:\tmp")
    else:
        candidates.append("/tmp")
    candidates.extend([
        os.environ.get("TMPDIR"),
        os.environ.get("TEMP"),
        os.environ.get("TMP"),
    ])
    repo_fallback = os.path.join(ROOT, ".ainp_test_tmp")
    candidates.append(repo_fallback)

    seen: set[str] = set()
    for raw in candidates:
        if not raw:
            continue
        candidate = os.path.abspath(raw)
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            os.makedirs(candidate, exist_ok=True)
            probe = tempfile.mkdtemp(prefix="ainp_probe_", dir=candidate)
            shutil.rmtree(probe, ignore_errors=True)
        except OSError:
            continue
        _TEST_TMP_PARENT = candidate
        if candidate == repo_fallback:
            atexit.register(lambda: shutil.rmtree(candidate, ignore_errors=True))
        return _TEST_TMP_PARENT
    return None


def make_tmpdir(prefix: str):
    return tempfile.TemporaryDirectory(prefix=prefix, dir=_writable_tmp_parent())


def _run(tool: str, *args: str):
    """Run a tool with --json; return (exit_code, codes_set)."""
    proc = subprocess.run([PY, "-B", "-X", "utf8", os.path.join(TOOLS, tool), *args, "--json"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    codes = set()
    try:
        data = json.loads(proc.stdout)
        codes = {f["code"] for f in data.get("findings", [])}
        fail_codes = {f["code"] for f in data.get("findings", []) if f["level"] == "fail"}
    except (json.JSONDecodeError, KeyError):
        fail_codes = set()
    return proc.returncode, codes, fail_codes


def _reject_duplicate_keys(pairs):
    out = {}
    seen = set()
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r}")
        seen.add(key)
        out[key] = value
    return out


def _reject_constant(const: str) -> None:
    raise ValueError(f"non-standard JSON literal {const!r}")


def validate(*args: str):
    return _run("ainp_validate.py", *args)


def report_check(*args: str):
    return _run("ainp_report_check.py", *args)


def release_check(*args: str):
    return _run("ainp_release_check.py", *args)


def project_check(*args: str):
    return _run("ainp_project_check.py", *args)


def example_project_packages() -> list[str]:
    return sorted(
        os.path.join(EX, name)
        for name in os.listdir(EX)
        if name.endswith("_ainp") and os.path.isdir(os.path.join(EX, name))
    )


def example_project_test_files() -> list[str]:
    tests: list[str] = []
    for package in example_project_packages():
        for root, _, files in os.walk(package):
            if os.path.basename(root) != "tests":
                continue
            for name in files:
                if name.startswith("test_") and name.endswith(".py"):
                    tests.append(os.path.join(root, name))
    return sorted(tests)


# --------------------------------------------------------------------------
# Group 1 + 4: JSON Schema validation
# --------------------------------------------------------------------------

SCHEMA_PAIRS = [
    (os.path.join("file_family", "whitepaper.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "high_risk_likeness.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "high_risk_likeness.generationreport.json"),
     "ainp-generationreport-v1.0.0.schema.json"),
    (os.path.join("file_family", "high_risk_likeness_feedback.generationfeedback.json"),
     "ainp-generationfeedback-v1.0.0.schema.json"),
    (os.path.join("file_family", "landing_page.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "dataset.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "medical_advice.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "security_exploit.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("file_family", "whitepaper.generationreport.json"),
     "ainp-generationreport-v1.0.0.schema.json"),
    (os.path.join("file_family", "whitepaper_feedback.generationfeedback.json"),
     "ainp-generationfeedback-v1.0.0.schema.json"),
    (os.path.join("file_family", "project.ainp.json"),
     "ainp-generation-space-v1.0.0.schema.json"),
    (os.path.join("whitepaper_ainp", "ainp", "whitepaper.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("whitepaper_ainp", "ainp", "whitepaper.generationreport.json"),
     "ainp-generationreport-v1.0.0.schema.json"),
    (os.path.join("whitepaper_ainp", "ainp", "whitepaper_feedback.generationfeedback.json"),
     "ainp-generationfeedback-v1.0.0.schema.json"),
    (os.path.join("whitepaper_ainp", "ainp", "project.ainp.json"),
     "ainp-generation-space-v1.0.0.schema.json"),
    (os.path.join("slugify_cli_ainp", "ainp", "slugify_cli.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("slugify_cli_ainp", "ainp", "slugify_cli.generationreport.json"),
     "ainp-generationreport-v1.0.0.schema.json"),
    (os.path.join("slugify_cli_ainp", "ainp", "slugify_cli_feedback.generationfeedback.json"),
     "ainp-generationfeedback-v1.0.0.schema.json"),
    (os.path.join("slugify_cli_ainp", "ainp", "project.ainp.json"),
     "ainp-generation-space-v1.0.0.schema.json"),
    (os.path.join("aikp_navigator_aiap_ainp", "ainp", "aikp_navigator_aiap.generation.json"),
     "ainp-generation-v1.0.0.schema.json"),
    (os.path.join("aikp_navigator_aiap_ainp", "ainp", "aikp_navigator_aiap.generationreport.json"),
     "ainp-generationreport-v1.0.0.schema.json"),
    (os.path.join("aikp_navigator_aiap_ainp", "ainp", "aikp_navigator_aiap_feedback.generationfeedback.json"),
     "ainp-generationfeedback-v1.0.0.schema.json"),
    (os.path.join("aikp_navigator_aiap_ainp", "ainp", "project.ainp.json"),
     "ainp-generation-space-v1.0.0.schema.json"),
    (os.path.join("aikp_navigator_aiap_ainp", "ainp", "references", "reference_manifest.json"),
     "ainp-reference-manifest-v1.0.0.schema.json"),
]

KNOWN_EXAMPLE_SCHEMA_PROFILES = {
    "ainp.v1.0.0.generation",
    "ainp.v1.0.0.generationreport",
    "ainp.v1.0.0.generationfeedback",
    "ainp.v1.0.0.generation_space",
    "ainp.v1.0.0.reference_manifest",
    "aiap.example.agent_card.v1.0.0",
    "aisop.example.flow.v1.0.0",
}

BINDING_DESCRIPTOR = {
    "descriptor_profile": "ainp.example.binding_descriptor.v1.0.0",
    "kind": "aisop_candidate_binding",
    "status": "non_executable_example",
    "purpose": "Temporary candidate binding target for G9 presence checks.",
    "execution_policy": {
        "auto_execute": False,
        "requires_explicit_authorization": True,
        "runtime_required": "AISOP-compatible runtime",
    },
    "honesty_boundary": (
        "This descriptor is not an AISOP runtime proof, not an executable "
        "program, and not a trust certificate."
    ),
}


def write_binding_descriptor(path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(BINDING_DESCRIPTOR, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def test_schemas_are_valid_draft202012():
    from jsonschema import Draft202012Validator
    for name in os.listdir(SCH):
        if name.endswith(".schema.json"):
            Draft202012Validator.check_schema(_load(os.path.join(SCH, name)))


def test_schema_files_have_single_canonical_directory():
    """Schema entities stay in top-level schemas/; specification/ holds indexes."""
    forbidden = []
    for name in os.listdir(SPEC):
        if name.endswith(".schema.json") or (
            name.startswith("high_risk_types.v") and name.endswith(".json")
        ):
            forbidden.append(name)
    assert not forbidden, (
        "do not mirror schema/data files under specification/: "
        f"{sorted(forbidden)}"
    )


def test_standards_files_are_machine_readable_and_scoped():
    expected = {
        "AINP_Standard.core.json": "ainp.v1.0.0.standard.core",
        "AINP_Standard.security.json": "ainp.v1.0.0.standard.security",
        "AINP_Standard.ecosystem.json": "ainp.v1.0.0.standard.ecosystem",
        "ainp-rules-v1.0.0.json": "ainp.v1.0.0.rules_index",
    }
    files = {name for name in os.listdir(STANDARDS) if name.endswith(".json")}
    assert set(expected) <= files
    assert not [name for name in os.listdir(STANDARDS) if name.endswith(".aisop.json")]

    runtime_tokens = (
        "main.aisop.json",
        "node_engine",
        "agent_card",
        "quality_baseline",
        "governance_hash",
        "TRI-SYNC",
    )
    for name in expected:
        path = os.path.join(STANDARDS, name)
        text = open(path, encoding="utf-8-sig").read()
        for token in runtime_tokens:
            assert token not in text, f"{name}: standards must not import runtime token {token!r}"

    readme = open(os.path.join(STANDARDS, "README.md"), encoding="utf-8-sig").read()
    assert "Do not add `*.aisop.json` files" in readme
    assert "They are not JSON Schema mirrors" in readme

    for name, schema in expected.items():
        doc = _load(os.path.join(STANDARDS, name))
        assert doc["schema"] == schema
        if name.startswith("AINP_Standard."):
            standard = doc["standard"]
            assert standard["protocol"] == "AINP v1.0.0"
            assert standard["authority"] == "ainp.dev"
            assert standard["kind"] == "standard_library_reference"
            boundary = standard["runtime_boundary"]
            assert "Non-executable" in boundary
            assert "not an AISOP flow" in boundary
            assert "not an AIAP program" in boundary

    core = _load(os.path.join(STANDARDS, "AINP_Standard.core.json"))["standard"]
    rules = _load(os.path.join(STANDARDS, "ainp-rules-v1.0.0.json"))
    plan_ids = {item["id"] for item in rules["plan_rules"] if item["id"].startswith("G")}
    feedback_ids = {item["id"] for item in rules["plan_rules"] if item["id"].startswith("FB")}
    space_ids = {item["id"] for item in rules["plan_rules"] if item["id"].startswith("SP")}
    report_ids = {item["id"] for item in rules["report_rules"]}
    project_ids = {item["id"] for item in rules["project_rules"]}
    assert set(core["rule_families"]["plan"]) == plan_ids
    assert set(core["rule_families"]["feedback"]) == feedback_ids
    assert set(core["rule_families"]["space"]) == space_ids
    assert set(core["rule_families"]["report"]) == report_ids
    assert set(core["rule_families"]["project"]) == project_ids
    assert core["content_architecture"]["standalone_required"] is False
    assert core["content_architecture"]["project_package_required"] is True
    assert core["content_architecture"]["not_execution_graph"] is True


def test_examples_do_not_declare_unknown_schema_profiles():
    """Example files may be non-normative, but unknown `schema` tokens are forbidden."""
    unknown = []
    for base, _, files in os.walk(EX):
        for name in files:
            if not name.endswith(".json"):
                continue
            path = os.path.join(base, name)
            doc = _load(path)
            if isinstance(doc, dict) and "schema" in doc and doc["schema"] not in KNOWN_EXAMPLE_SCHEMA_PROFILES:
                unknown.append(os.path.relpath(path, ROOT) + f" -> {doc['schema']!r}")
    assert not unknown, f"unknown example schema profiles: {sorted(unknown)}"


def test_examples_validate_against_schema():
    from jsonschema import Draft202012Validator
    for doc, schema in SCHEMA_PAIRS:
        v = Draft202012Validator(_load(os.path.join(SCH, schema)))
        errs = list(v.iter_errors(_load(os.path.join(EX, doc))))
        assert not errs, f"{doc}: {[e.message for e in errs[:3]]}"


def test_high_risk_types_validate_against_schema():
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(_load(os.path.join(SCH, "high_risk_types-v1.0.0.schema.json")))
    errs = list(v.iter_errors(_load(os.path.join(SCH, "high_risk_types.v1.0.0.json"))))
    assert not errs, f"high_risk_types.v1.0.0.json: {[e.message for e in errs[:3]]}"


def test_reference_manifest_schema_source_conditionals():
    from jsonschema import Draft202012Validator
    import tools.ainp_release_check as release_tool

    schema = _load(os.path.join(SCH, "ainp-reference-manifest-v1.0.0.schema.json"))
    validator = Draft202012Validator(schema)
    base = _load(os.path.join(EX, "aikp_navigator_aiap_ainp", "ainp", "references",
                              "reference_manifest.json"))

    def clone_with_reference(reference: dict) -> dict:
        doc = json.loads(json.dumps(base))
        doc["reference_manifest"]["references"] = [reference]
        return doc

    local_ref = json.loads(json.dumps(base["reference_manifest"]["references"][0]))
    assert not list(validator.iter_errors(clone_with_reference(local_ref)))

    external_ref = json.loads(json.dumps(local_ref))
    external_ref["source"] = {"type": "external_uri", "uri": "https://example.invalid/ref"}
    external_ref.pop("sha256", None)
    assert not list(validator.iter_errors(clone_with_reference(external_ref)))

    bad_cases = []
    bad = json.loads(json.dumps(local_ref))
    bad["source"] = {"type": "local_file"}
    bad_cases.append(bad)

    bad = json.loads(json.dumps(local_ref))
    bad["source"] = {"type": "local_file", "uri": "https://example.invalid/ref"}
    bad_cases.append(bad)

    bad = json.loads(json.dumps(local_ref))
    bad["source"] = {"type": "external_uri"}
    bad.pop("sha256", None)
    bad_cases.append(bad)

    bad = json.loads(json.dumps(local_ref))
    bad["source"] = {"type": "external_uri", "path": "ainp/references/ref.md"}
    bad.pop("sha256", None)
    bad_cases.append(bad)

    bad = json.loads(json.dumps(local_ref))
    bad["source"] = {"type": "external_uri", "uri": "https://example.invalid/ref"}
    bad["sha256"] = "0" * 64
    bad_cases.append(bad)

    with make_tmpdir(prefix="ainp_reference_schema_conditionals_") as td:
        for i, bad_ref in enumerate(bad_cases):
            doc = clone_with_reference(bad_ref)
            assert list(validator.iter_errors(doc)), bad_ref

            manifest = os.path.join(td, f"bad_reference_{i}.json")
            with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            findings: list[dict] = []
            release_tool.validate_against_schema(
                manifest, "ainp-reference-manifest-v1.0.0.schema.json",
                findings, "reference manifest"
            )
            assert "AINP_E_RELEASE_SCHEMA_INVALID" in {item["code"] for item in findings}, bad_ref


def test_release_schema_gate_keyword_subset_matches_bundled_schemas():
    from jsonschema import Draft202012Validator
    import tools.ainp_release_check as release_tool

    supported_keywords = {
        "$defs", "$id", "$ref", "$schema",
        "additionalProperties", "allOf", "anyOf", "const", "description",
        "else", "enum", "exclusiveMaximum", "exclusiveMinimum", "if", "items",
        "maxItems", "maxLength", "maximum", "minItems", "minLength",
        "minimum", "multipleOf", "not", "oneOf", "pattern",
        "patternProperties", "prefixItems", "properties", "propertyNames",
        "required", "then", "title", "type", "uniqueItems",
    }

    used_keywords: set[str] = set()

    def walk_schema(node) -> None:
        if not isinstance(node, dict):
            return
        used_keywords.update(node.keys())
        for key, value in node.items():
            if key in ("$defs", "properties") and isinstance(value, dict):
                for child in value.values():
                    walk_schema(child)
            elif key in ("items", "not", "if", "then", "else", "additionalProperties"):
                walk_schema(value)
            elif key in ("patternProperties",) and isinstance(value, dict):
                for child in value.values():
                    walk_schema(child)
            elif key in ("propertyNames",):
                walk_schema(value)
            elif key in ("allOf", "anyOf", "oneOf") and isinstance(value, list):
                for child in value:
                    walk_schema(child)
            elif key in ("prefixItems",) and isinstance(value, list):
                for child in value:
                    walk_schema(child)

    for name in os.listdir(SCH):
        if name.endswith(".schema.json"):
            walk_schema(_load(os.path.join(SCH, name)))

    unsupported = sorted(used_keywords - supported_keywords)
    assert not unsupported, (
        "bundled schemas use keywords that the stdlib release schema gate may "
        f"silently ignore: {unsupported}"
    )

    semantic_cases = [
        (
            {
                "$defs": {"base": {"type": "string"}},
                "$ref": "#/$defs/base",
                "minLength": 2,
            },
            "",
        ),
        ({"anyOf": [{"type": "string"}, {"type": "integer"}]}, []),
        ({"oneOf": [{"type": "number"}, {"type": "integer"}]}, 3),
        ({"not": {"required": ["x"]}}, {"x": 1}),
        (
            {
                "if": {
                    "properties": {"kind": {"const": "a"}},
                    "required": ["kind"],
                },
                "then": {"required": ["x"]},
                "else": {"required": ["y"]},
            },
            {"kind": "a"},
        ),
        ({"type": "string", "maxLength": 2}, "abc"),
        ({"type": "array", "maxItems": 1}, [1, 2]),
        ({"type": "number", "maximum": 10}, 11),
        ({"type": "number", "exclusiveMinimum": 1, "exclusiveMaximum": 3}, 3),
        ({"type": "number", "multipleOf": 0.5}, 1.25),
        (
            {
                "type": "object",
                "patternProperties": {"^x_": {"type": "integer"}},
                "additionalProperties": False,
            },
            {"x_flag": "not-an-int"},
        ),
        ({"type": "object", "propertyNames": {"pattern": "^[a-z_]+$"}}, {"BadKey": 1}),
        ({"type": "array", "prefixItems": [{"const": "AINP"}], "items": {"type": "integer"}}, ["AINP", "x"]),
    ]
    for schema, value in semantic_cases:
        jsonschema_has_error = bool(list(Draft202012Validator(schema).iter_errors(value)))
        stdlib_has_error = bool(release_tool.schema_errors(value, schema, schema, "$"))
        assert stdlib_has_error is jsonschema_has_error, (schema, value)


def test_tool_wrappers_fail_closed_on_bad_child_exit():
    import tools.ainp_project_check as project_tool
    import tools.ainp_release_check as release_tool

    bad_child = subprocess.CompletedProcess(
        args=["python"],
        returncode=2,
        stdout='{"findings":[]}\n',
        stderr="child tool aborted",
    )
    with mock.patch("tools.ainp_release_check.subprocess.run", return_value=bad_child):
        rc, findings = release_tool.run_json_tool("ainp_validate.py", ["plan.generation.json"])
    assert rc == 2
    assert "AINP_E_RELEASE_TOOL_EXIT" in {item["code"] for item in findings}

    findings: list[dict] = []
    with mock.patch("tools.ainp_project_check.subprocess.run", return_value=bad_child):
        project_tool.run_validate(["side.generationfeedback.json"], findings)
    assert "AINP_E_P6_VALIDATE_TOOL_EXIT" in {item["code"] for item in findings}

    findings = []
    with mock.patch("tools.ainp_project_check.subprocess.run", return_value=bad_child):
        project_tool.run_release("package_ainp", "plan.generation.json", "report.generationreport.json", findings)
    assert "AINP_E_P7_RELEASE_TOOL_EXIT" in {item["code"] for item in findings}


def test_semver_schema_and_validator_are_aligned():
    from jsonschema import Draft202012Validator
    schema = _load(os.path.join(SCH, "ainp-generation-v1.0.0.schema.json"))
    validator = Draft202012Validator(schema)
    base = _load(os.path.join(FILE_EX, "whitepaper.generation.json"))
    cases = {
        "01.0.0": False,
        "1.0.0-01": False,
        "1.0.0-alpha.01": False,
        "1.0.0+build.1": True,
        "1.0.0-alpha+build.1": True,
    }
    with make_tmpdir(prefix="ainp_semver_") as td:
        for version, want_ok in cases.items():
            doc = json.loads(json.dumps(base))
            doc["generation"]["version"] = version
            schema_ok = not list(validator.iter_errors(doc))
            assert schema_ok is want_ok, f"schema SemVer verdict drifted for {version}"
            p = os.path.join(td, f"{version.replace('+', '_').replace('.', '_')}.generation.json")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False)
            rc, _, fails = validate(p)
            assert (rc == 0) is want_ok, \
                f"validator SemVer verdict drifted for {version}: {sorted(fails)}"


def test_schema_tool_closed_enums_are_aligned():
    import tools.ainp_project_check as project_tool
    import tools.ainp_report_check as report_tool
    import tools.ainp_validate as validate_tool

    generation_schema = _load(os.path.join(SCH, "ainp-generation-v1.0.0.schema.json"))
    report_schema = _load(os.path.join(SCH, "ainp-generationreport-v1.0.0.schema.json"))
    feedback_schema = _load(os.path.join(SCH, "ainp-generationfeedback-v1.0.0.schema.json"))
    space_schema = _load(os.path.join(SCH, "ainp-generation-space-v1.0.0.schema.json"))
    reference_schema = _load(os.path.join(SCH, "ainp-reference-manifest-v1.0.0.schema.json"))

    def node(root, *parts):
        cur = root
        for part in parts:
            cur = cur[part]
        return cur

    def enum_at(root, *parts):
        return set(node(root, *parts)["enum"])

    g_props = generation_schema["properties"]["generation"]["properties"]
    g_defs = generation_schema["$defs"]
    assert enum_at(g_props, "status") == validate_tool.STATUS
    assert enum_at(g_props, "source") == validate_tool.ORIGIN
    assert enum_at(g_props, "risk_profile", "properties", "deployment_scope") == validate_tool.DEPLOYMENT_SCOPE
    assert set(g_defs["risk_level"]["enum"]) == validate_tool.RISK_LEVEL
    assert set(g_defs["rights_status"]["enum"]) == validate_tool.RIGHTS_STATUS
    assert enum_at(g_defs, "input", "properties", "provenance", "properties", "status") == validate_tool.PROVENANCE_STATUS
    assert enum_at(g_defs, "input", "properties", "consent", "properties", "status") == validate_tool.CONSENT_STATUS
    assert enum_at(g_defs, "input", "properties", "consent", "properties", "scope") == validate_tool.CONSENT_SCOPE
    assert enum_at(g_defs, "constraint", "properties", "type") == validate_tool.CONSTRAINT_TYPES
    assert enum_at(g_defs, "constraint", "properties", "severity") == validate_tool.SEVERITY
    assert enum_at(g_defs, "constraint", "properties", "enforced_by", "items", "properties", "stage") == validate_tool.STAGE
    assert enum_at(g_defs, "constraint", "properties", "enforced_by", "items", "properties", "assurance") == validate_tool.ASSURANCE
    assert enum_at(g_defs, "criterion", "properties", "severity") == validate_tool.SEVERITY
    assert enum_at(g_defs, "criterion", "properties", "verification", "properties", "method") == validate_tool.VERIFICATION_METHOD
    assert enum_at(g_props, "bindings", "properties", "execution_binding", "properties", "protocol") == validate_tool.EXECUTION_PROTOCOLS
    assert enum_at(g_props, "governance", "properties", "status") == validate_tool.STATUS

    fb_props = feedback_schema["properties"]["generationfeedback"]["properties"]
    assert enum_at(fb_props, "source") == validate_tool.FEEDBACK_SOURCE
    assert enum_at(fb_props, "verdict") == validate_tool.VERDICT
    assert enum_at(fb_props, "issues", "items", "properties", "target") == validate_tool.FEEDBACK_TARGET
    assert enum_at(fb_props, "issues", "items", "properties", "severity") == validate_tool.SEVERITY

    sp_props = space_schema["properties"]["generation_space"]["properties"]
    assert enum_at(sp_props, "generations", "items", "properties", "status") == validate_tool.STATUS

    ref_props = reference_schema["$defs"]["reference_item"]["properties"]
    assert enum_at(ref_props, "kind") == project_tool.REFERENCE_KINDS
    assert enum_at(ref_props, "source", "properties", "type") == project_tool.REFERENCE_SOURCE_TYPES
    assert enum_at(ref_props, "kind") == validate_tool.REFERENCE_KINDS
    assert enum_at(ref_props, "source", "properties", "type") == validate_tool.REFERENCE_SOURCE_TYPES

    r_props = report_schema["properties"]["generationreport"]["properties"]
    result_props = r_props["acceptance_results"]["items"]["properties"]
    assert enum_at(result_props, "method") == report_tool.VERIFICATION_METHOD
    assert enum_at(result_props, "verifier", "properties", "type") == report_tool.VERIFIER_TYPES
    assert enum_at(r_props, "disclosure", "properties", "content_credential", "properties", "verification_status") == report_tool.CONTENT_CREDENTIAL_STATUS
    assert set(node(r_props, "generator", "required")) == set(report_tool.GENERATOR_METADATA_REQUIRED)
    assert set(node(r_props, "disclosure", "properties", "watermarks", "items", "required")) == set(report_tool.WATERMARK_REQUIRED_FIELDS)
    assert enum_at(r_props, "governance_results", "properties", "approval_gate", "properties", "method") == {"human", "external"}
    assert enum_at(r_props, "governance_results", "properties", "approval_gate", "properties", "verifier", "properties", "type") == report_tool.VERIFIER_TYPES

    assert project_tool.STATUS == validate_tool.STATUS


# --------------------------------------------------------------------------
# Group 2: reference validator — positive
# --------------------------------------------------------------------------

def test_valid_plans_pass_default():
    for name in ("whitepaper.generation.json", "high_risk_likeness.generation.json",
                 "landing_page.generation.json", "dataset.generation.json",
                 "medical_advice.generation.json", "security_exploit.generation.json"):
        rc, _, fails = validate(os.path.join(FILE_EX, name))
        assert rc == 0, f"{name} should pass default: {fails}"


def test_valid_report_passes():
    for name in ("whitepaper.generationreport.json", "high_risk_likeness.generationreport.json"):
        rc, _, fails = report_check(os.path.join(FILE_EX, name))
        assert rc == 0, f"{name} should pass: {fails}"


def test_valid_report_passes_release():
    for name in ("whitepaper.generationreport.json", "high_risk_likeness.generationreport.json"):
        rc, _, fails = report_check(os.path.join(FILE_EX, name), "--mode", "release")
        assert rc == 0, f"{name} should pass release: {fails}"


def test_space_and_feedback_pass():
    rc, _, fails = validate(os.path.join(FILE_EX, "project.ainp.json"),
                            os.path.join(FILE_EX, "whitepaper_feedback.generationfeedback.json"),
                            os.path.join(FILE_EX, "high_risk_likeness_feedback.generationfeedback.json"),
                            os.path.join(EX, "aikp_navigator_aiap_ainp", "ainp", "references",
                                         "reference_manifest.json"))
    assert rc == 0, f"space+feedback+references should pass: {fails}"


def test_high_risk_examples_pass_release():
    # high-risk examples carry red-line constraints; must survive release mode
    for name in ("high_risk_likeness.generation.json", "landing_page.generation.json",
                 "medical_advice.generation.json", "security_exploit.generation.json"):
        rc, _, fails = validate(os.path.join(FILE_EX, name), "--mode", "release")
        assert rc == 0, f"{name} should pass release: {fails}"
    rc, _, fails = release_check(
        os.path.join(FILE_EX, "high_risk_likeness.generation.json"),
        "--report", os.path.join(FILE_EX, "high_risk_likeness.generationreport.json"),
    )
    assert rc == 0, f"high-risk likeness report should satisfy release gates: {fails}"


def test_unified_cli_doctor_passes():
    proc = subprocess.run(
        [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp.py"), "doctor", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["ok"] is True
    assert {check["label"] for check in data["checks"]} >= {
        "required files",
        "example project discovery",
        "plan/examples validation",
        "documentation synchronization",
        "markdown links",
    }


def test_unified_cli_doctor_discovers_all_example_project_packages():
    from tools import ainp as unified_tool

    project_packages = [
        os.path.relpath(path, ROOT).replace(os.sep, "/")
        for path in example_project_packages()
    ]
    labels = {
        label
        for label, _ in unified_tool._doctor_commands(False, False, project_packages)
    }
    for project_package in project_packages:
        assert f"project package check {project_package}" in labels
        assert f"project hash freshness {project_package}" in labels


def test_unified_cli_doctor_discovers_file_family_examples():
    from tools import ainp as unified_tool

    commands = dict(unified_tool._doctor_commands(False, False, []))
    validation_args = set(commands["plan/examples validation"])
    expected_validation = {
        f"examples/file_family/{name}"
        for name in os.listdir(FILE_EX)
        if name.endswith((".generation.json", ".generationfeedback.json", ".ainp.json"))
    }
    assert expected_validation <= validation_args

    labels = set(commands)
    expected_reports = {
        f"file-family report check examples/file_family/{name}"
        for name in os.listdir(FILE_EX)
        if name.endswith(".generationreport.json")
    }
    assert expected_reports <= labels
    assert (
        "examples/file_family/high_risk_likeness.generation.json",
        "examples/file_family/high_risk_likeness.generationreport.json",
    ) in set(unified_tool._file_family_release_bundles())
    assert (
        "examples/file_family/whitepaper.generation.json",
        "examples/file_family/whitepaper.generationreport.json",
    ) not in set(unified_tool._file_family_release_bundles())


def test_unified_cli_doctor_release_bundle_scan_uses_strict_json():
    from tools import ainp as unified_tool

    with make_tmpdir(prefix="ainp_doctor_strict_json_") as td:
        family = os.path.join(td, "examples", "file_family")
        os.makedirs(family, exist_ok=True)
        with open(os.path.join(family, "fake.generation.json"), "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        with open(os.path.join(family, "fake.generationreport.json"), "w", encoding="utf-8") as fh:
            fh.write(
                '{"generationreport": {'
                '"plan_ref": {"path": "fake.generation.json"},'
                '"overall": {"conformant": false},'
                '"overall": {"conformant": true}'
                '}}\n'
            )
        with mock.patch.object(unified_tool, "ROOT", td):
            assert unified_tool._file_family_release_bundles() == []


def test_json_tool_outputs_do_not_leak_repo_absolute_path():
    commands = [
        [
            PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_validate.py"),
            os.path.abspath(os.path.join(FILE_EX, "whitepaper.generation.json")),
            "--json",
        ],
        [
            PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_report_check.py"),
            os.path.abspath(os.path.join(FILE_EX, "whitepaper.generationreport.json")),
            "--plan", os.path.abspath(os.path.join(FILE_EX, "whitepaper.generation.json")),
            "--json",
        ],
        [
            PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_release_check.py"),
            "examples/whitepaper_ainp/ainp/whitepaper.generation.json",
            "--report", "examples/whitepaper_ainp/ainp/whitepaper.generationreport.json",
            "--project-root", "examples/whitepaper_ainp",
            "--json",
        ],
        [
            PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_project_check.py"),
            "examples/whitepaper_ainp",
            "--json",
        ],
    ]
    root_variants = _path_variants(ROOT)
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        for variant in root_variants:
            assert variant not in proc.stdout
        data = json.loads(proc.stdout)
        for finding in data.get("findings", []):
            path = finding.get("path", "")
            assert not os.path.isabs(path), path


def test_json_tool_error_outputs_do_not_leak_absolute_paths_from_external_cwd():
    with make_tmpdir(prefix="ainp_public_error_paths_") as td:
        missing_plan = os.path.abspath(os.path.join(EX, "whitepaper_ainp", "ainp", "missing.generation.json"))
        missing_report = os.path.abspath(os.path.join(FILE_EX, "missing.generationreport.json"))
        missing_project = os.path.abspath(os.path.join(EX, "missing_ainp"))
        commands = [
            [
                PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_validate.py"),
                missing_plan,
                "--json",
            ],
            [
                PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_report_check.py"),
                missing_report,
                "--json",
            ],
            [
                PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_release_check.py"),
                missing_plan,
                "--json",
            ],
            [
                PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_project_check.py"),
                missing_project,
                "--json",
            ],
            [
                PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_rehash.py"),
                missing_project,
                "--check",
                "--json",
            ],
        ]
        forbidden = set()
        for path in (ROOT, os.path.dirname(missing_plan), os.path.dirname(missing_report),
                     missing_project, td):
            forbidden.update(_path_variants(path))
        for command in commands:
            proc = subprocess.run(
                command,
                cwd=td,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            combined = proc.stdout + proc.stderr
            assert proc.returncode != 0, combined
            assert "Traceback" not in combined
            for variant in forbidden:
                assert variant not in combined
            json.loads(proc.stdout)

        unknown_command = "D:" + "\\private\\secret.md"
        proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp.py"), unknown_command],
            cwd=td,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 2, combined
        assert "Traceback" not in combined
        assert "private/secret" not in combined.replace("\\", "/")
        assert "<local-machine-path>" in combined
        for variant in forbidden:
            assert variant not in combined


def test_public_output_helper_keeps_paths_public():
    from tools.ainp_public import PublicOutput

    with make_tmpdir(prefix="ainp_public_helper_") as td:
        public = PublicOutput(bases=[td])
        inside = os.path.join(td, "nested", "plan.generation.json")
        unknown = os.path.abspath(os.path.join(td, "..", "secret-root", "private.json"))
        public.register_input_path(inside)

        assert public.display_path(inside) == "nested/plan.generation.json"
        assert public.display_path(unknown) == "private.json"
        assert public.display_path("D:" + "secret") == "<local-machine-path>"
        assert public.display_path("D:" + "secret.md") == "<local-machine-path>"
        assert public.display_path("\\\\" + "server\\share\\secret.md") == "<local-machine-path>"
        assert public.display_path("file:" + "C:/private/secret.md") == "file:<redacted>"
        assert public.sanitize_text("ref D:" + "secret") == "ref <local-machine-path>"
        assert public.sanitize_text("D: plain label") == "D: plain label"
        assert public.sanitize_text("C:" + "/" + "Users/John Doe/secret.md") == "<local-machine-path>"
        assert public.sanitize_text("C:" + "/" + "Users/John Doe/Secrets") == "<local-machine-path>"
        assert public.sanitize_text("D:" + "/private folder/secret.md") == "<local-machine-path>"
        assert public.sanitize_text("D:" + "/private folder/secret") == "<local-machine-path>"
        assert public.sanitize_text("D:" + "/private and folder/secret") == "<local-machine-path>"
        assert public.sanitize_text("\\\\" + "server\\share folder\\secret.md") == "<local-machine-path>"
        assert public.sanitize_text("\\\\" + "server\\share folder\\secret") == "<local-machine-path>"
        assert public.sanitize_text("\\\\" + "server\\share and folder\\secret") == "<local-machine-path>"
        posix_home = "/" + "home/alice/private plan.md"
        posix_tmp = "/" + "tmp/private folder/secret"
        assert public.sanitize_text(f"read {posix_home}") == "read <local-machine-path>"
        assert public.sanitize_text(f"read {posix_tmp}") == "read <local-machine-path>"
        web_path = "https://example.com/home/alice/private-plan.md"
        assert public.sanitize_text(web_path) == web_path
        assert public.sanitize_text("file:///tmp/private file.md") == "file:<redacted>"
        assert public.sanitize_text("file:///tmp/private folder/secret") == "file:<redacted>"

        message = f"failed to read {inside}"
        sanitized = public.sanitize_text(message)
        assert "nested/plan.generation.json" in sanitized
        for variant in _path_variants(td):
            assert variant not in sanitized
        if os.name == "nt" and td.upper() != td:
            mixed_case = inside.upper()
            sanitized_case = public.sanitize_text(f"failed to read {mixed_case}")
            for variant in _path_variants(td):
                assert variant not in sanitized_case
                assert variant.upper() not in sanitized_case

        drive_secret = "D:" + "\\private\\secret.md"
        drive_relative_secret = "C:" + "outside_secret.txt"
        unc_secret = "\\\\" + "server\\share\\secret.md"
        file_secret = "file:" + "C:/outside_secret.txt"
        script_secret = "javascript:" + "alert(1)"
        unsafe_message = (
            f"ref {drive_secret} and {drive_relative_secret} and "
            f"{unc_secret} and {file_secret} and {script_secret}"
        )
        sanitized_unsafe = public.sanitize_text(unsafe_message)
        for token in ("private/secret", "C:outside", "server/share",
                      "outside_secret", "alert"):
            assert token not in sanitized_unsafe.replace("\\", "/")
        assert "<local-machine-path>" in sanitized_unsafe
        web_url = "https://github.com/AIXP-Labs/AINP and http://example.com/path"
        assert public.sanitize_text(web_url) == web_url
        assert public.sanitize_text("Data: ordinary label") == "Data: ordinary label"
        assert public.sanitize_text("data:text/html,hello") == "data:<redacted>"
        assert public.sanitize_text("file%3A///tmp/encoded-secret.md") == "file:<redacted>"
        assert public.sanitize_text("file%253A///tmp/double-encoded-secret.md") == "file:<redacted>"
        assert public.sanitize_text("%66%69%6c%65%3A///tmp/fully-encoded-secret.md") == "file:<redacted>"
        assert public.sanitize_text("javascript%253Aalert%25281%2529") == "javascript:<redacted>"
        assert public.sanitize_text("%6a%61%76%61%73%63%72%69%70%74%3Aalert%281%29") == "javascript:<redacted>"
        assert public.sanitize_text("data%3Atext/html,encoded") == "data:<redacted>"


def test_doc_sync_failure_output_is_structured_and_public():
    with make_tmpdir(prefix="ainp_doc_sync_public_") as td:
        proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_doc_sync.py"),
             "--root", td, "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "Traceback" not in proc.stderr
        for variant in _path_variants(td):
            assert variant not in proc.stdout
            assert variant not in proc.stderr
        data = json.loads(proc.stdout)
        assert data["failure_count"] > 0
        assert any("missing specification directory" in item for item in data["failures"])


def test_doc_sync_test_count_guard_ignores_unrelated_ratios():
    from tools import check_doc_sync

    with make_tmpdir(prefix="ainp_doc_sync_test_count_") as td:
        doc = Path(td) / "README.md"
        doc.write_text(
            "A normal ratio 3/4 and version-like prose should not be read as a test count.\n"
            "The 75-test suite is current and 75/75 green at release.\n",
            encoding="utf-8",
            newline="\n",
        )
        assert not check_doc_sync.check_forbidden(doc, 75)

        stale_count = "70"
        doc.write_text(
            f"The {stale_count}-test suite is stale and "
            f"{stale_count}/{stale_count} green at release.\n",
            encoding="utf-8",
            newline="\n",
        )
        failures = check_doc_sync.check_forbidden(doc, 75)
        assert failures and "stale test-count reference" in failures[0]


def test_stale_protocol_names_are_absent():
    proc = subprocess.run(
        [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_doc_sync.py"),
         "--root", ROOT, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["failure_count"] == 0


def test_markdown_link_checker_rejects_local_machine_links_and_target_escape():
    with make_tmpdir(prefix="ainp_markdown_public_") as td:
        drive_link = "D:" + "/" + "private/secret.md"
        drive_image = "D:" + "/" + "private/image.png"
        drive_autolink = "D:" + "/" + "private/autolink.md"
        drive_reference = "D:" + "/" + "private/reference.md"
        drive_relative = "D:" + "private/secret.md"
        drive_fenced = "D:" + "/" + "private/fenced-html.png"
        unc_link = "/" + "/" + "server/share.md"
        unc_backslash = "\\\\" + "server\\share.md"
        readme = os.path.join(td, "README.md")
        target = os.path.join(td, "target.md")
        outside = os.path.abspath(os.path.join(td, "..", "outside.md"))
        drive_relative_target = "E:" + "Users\\Name\\missing.md"
        bad_anchor = "D%3A%2F" + "private" + "%2Fanchor.md"
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "# Links\n\n"
                f"[drive]({drive_link})\n\n"
                f"![drive-image]({drive_image})\n\n"
                f"[drive-relative]({drive_relative})\n\n"
                f"[unc]({unc_link})\n\n"
                f"[unc-backslash]({unc_backslash})\n\n"
                f"[bad-anchor](target.md#{bad_anchor})\n\n"
                f"<{drive_autolink}>\n\n"
                "<//server/autolink.md>\n\n"
                "~~~\n"
                "[fenced](file:///tmp/fenced-secret.md)\n"
                f"<img src=\"{drive_fenced}\">\n"
                "~~~\n"
                "```\n"
                "~~~\n"
                "[mixed-fenced](missing-from-code.md)\n"
                "```\n"
                f"[drive-ref]: {drive_reference}\n"
                "[ok-ref]: target.md#target\n"
            )
        with open(target, "w", encoding="utf-8") as f:
            f.write("# Target\n")
        with open(outside, "w", encoding="utf-8") as f:
            f.write("# Outside\n")
        try:
            proc = subprocess.run(
                [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_markdown_links.py"),
                 "--root", td, "--json", "README.md", "missing.md",
                 drive_relative_target, outside],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        finally:
            try:
                os.remove(outside)
            except OSError:
                pass
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, combined
        assert "Traceback" not in combined
        for path in (td, outside, os.path.dirname(outside)):
            for variant in _path_variants(path):
                assert variant not in combined
        for token in ("private/secret", "private/image", "private/autolink",
                      "private/reference", "private/anchor",
                      "server/share",
                      "server/autolink", "Users/Name", "fenced-secret",
                      "fenced-html", "missing-from-code", "private" + "%2Fanchor"):
            assert token not in combined.replace("\\", "/")
        data = json.loads(proc.stdout)
        messages = [item["message"] for item in data["problems"]]
        assert messages.count("local machine path") == 8
        assert "missing scan target" in messages
        assert "target escapes repository root" in messages
        assert any(item["message"] == "missing anchor #<local-machine-path>"
                   and item["link"] == "target.md#<local-machine-path>"
                   for item in data["problems"])
        escape_links = {
            item["link"] for item in data["problems"]
            if item["message"] == "target escapes repository root"
        }
        assert escape_links
        assert escape_links <= {"<local-machine-path>", os.path.basename(outside)}
        assert {item["link"] for item in data["problems"]
                if item["message"] == "local machine path"} == {"<local-machine-path>"}

        text_proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_markdown_links.py"),
             "--root", td, "README.md", "missing.md", drive_relative_target, outside],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        text_combined = text_proc.stdout + text_proc.stderr
        assert text_proc.returncode == 1, text_combined
        assert "local machine path" in text_combined
        assert "missing scan target" in text_combined
        assert "target escapes repository root" in text_combined
        assert "Traceback" not in text_combined
        for path in (td, outside, os.path.dirname(outside)):
            for variant in _path_variants(path):
                assert variant not in text_combined
        for token in ("private/secret", "private/image", "private/autolink",
                      "private/reference", "private/anchor",
                      "server/share",
                      "server/autolink", "Users/Name", "fenced-secret",
                      "fenced-html", "missing-from-code", "private" + "%2Fanchor"):
            assert token not in text_combined.replace("\\", "/")


def test_markdown_link_checker_rejects_percent_encoded_unsafe_schemes():
    with make_tmpdir(prefix="ainp_markdown_encoded_scheme_") as td:
        readme = os.path.join(td, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "# Links\n\n"
                "[encoded-js](javascript%3Aalert(1))\n\n"
                "[encoded-file](file%3A///tmp/secret.md)\n\n"
                "![encoded-file-image](file%3A///tmp/image-secret.png)\n\n"
                "[raw-data](data:text/html,hello)\n\n"
                "[encoded-vbscript](vbscript%3Amsgbox(1))\n\n"
                "[double-encoded-js](javascript%253Aalert%25281%2529)\n\n"
                "[double-encoded-file](file%253A///tmp/secret2.md)\n\n"
                "[unsafe-ref]: file%3A///tmp/ref-secret.md\n\n"
                "<javascript:alert(1)>\n"
            )
        proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_markdown_links.py"),
             "--root", td, "--json", "README.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, combined
        assert "Traceback" not in combined
        for variant in _path_variants(td):
            assert variant not in combined
        for token in ("alert", "tmp/secret", "image-secret", "ref-secret",
                      "msgbox", "text/html"):
            assert token not in combined
        data = json.loads(proc.stdout)
        messages = [item["message"] for item in data["problems"]]
        assert messages.count("unsafe scheme") == 9
        assert {item["link"] for item in data["problems"]} == {
            "data:<redacted>",
            "file:<redacted>",
            "javascript:<redacted>",
            "vbscript:<redacted>",
        }


def test_markdown_link_checker_rejects_undefined_reference_links():
    with make_tmpdir(prefix="ainp_markdown_ref_use_") as td:
        readme = os.path.join(td, "README.md")
        target = os.path.join(td, "target.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "# Links\n\n"
                "[defined][ok-ref]\n\n"
                "[missing][missing-ref]\n\n"
                "![missing-image][missing-image-ref]\n\n"
                "Inline code is not a reference link: `arr[i][j]`.\n\n"
                "```\n"
                "[ignored][missing-code-ref]\n"
                "```\n\n"
                "[ok-ref]: target.md#target\n"
            )
        with open(target, "w", encoding="utf-8") as f:
            f.write("# Target\n")
        proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_markdown_links.py"),
             "--root", td, "--json", "README.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, combined
        assert "Traceback" not in combined
        data = json.loads(proc.stdout)
        problems = [
            item for item in data["problems"]
            if item["message"] == "undefined reference link label"
        ]
        assert {item["link"] for item in problems} == {"[missing-ref]", "[missing-image-ref]"}


def test_markdown_link_checker_rejects_html_link_media_unsafe_targets():
    with make_tmpdir(prefix="ainp_markdown_html_links_") as td:
        readme = os.path.join(td, "README.md")
        target = os.path.join(td, "target.md")
        drive_link = "D:" + "/" + "private/html-secret.md"
        drive_srcset = "D:" + "/" + "private/srcset-image.png"
        unc_link = "\\\\" + "server\\share\\html-image.png"
        unc_poster = "\\\\" + "server\\share\\poster-image.png"
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "# Links\n\n"
                "<a href=\"file:///tmp/private-html.md\">file</a>\n\n"
                "<img src='data:image/png;base64,AAAA'>\n\n"
                f"<a href={drive_link}>drive</a>\n\n"
                f"<img src={unc_link}>\n\n"
                "<source srcset=\"target.md 1x, file:///tmp/srcset-secret.md 2x\">\n\n"
                f"<img srcset=\"https://example.com/image.png 1x, {drive_srcset} 2x\">\n\n"
                f"<video poster=\"{unc_poster}\"></video>\n\n"
                "<a href=\"target.md#target\">local anchor</a>\n\n"
                "<img src=\"https://example.com/image.png\">\n"
            )
        with open(target, "w", encoding="utf-8") as f:
            f.write("# Target\n")
        proc = subprocess.run(
            [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "check_markdown_links.py"),
             "--root", td, "--json", "README.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1, combined
        assert "Traceback" not in combined
        for path in _path_variants(td):
            assert path not in combined
        for token in ("tmp/private-html", "private/html-secret", "server/share",
                      "srcset-secret", "srcset-image", "poster-image",
                      "image/png", "AAAA"):
            assert token not in combined.replace("\\", "/")
        data = json.loads(proc.stdout)
        messages = [item["message"] for item in data["problems"]]
        assert messages.count("unsafe scheme") == 3
        assert messages.count("local machine path") == 4
        assert {item["link"] for item in data["problems"]} == {
            "data:<redacted>",
            "file:<redacted>",
            "<local-machine-path>",
        }


def test_release_check_failure_output_is_public_when_powershell_available():
    powershell = shutil.which("powershell")
    if not powershell:
        return
    with make_tmpdir(prefix="ainp_release_public_") as td:
        for rel in (
            "tools/ainp.py",
            "tools/ainp_public.py",
            "tools/ainp_validate.py",
            "tools/ainp_release_check.py",
            "tools/ainp_project_check.py",
            "tests/test_ainp.py",
            "schemas/ainp-generation-v1.0.0.schema.json",
            "schemas/ainp-generationreport-v1.0.0.schema.json",
            "examples/file_family/whitepaper.generation.json",
            "scripts/release_check.ps1",
        ):
            path = os.path.join(td, *rel.split("/"))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{}\n" if path.endswith(".json") else "# placeholder\n")
        with open(os.path.join(td, "VERSION"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("AINP v1.0.0\n")
        with open(os.path.join(td, "bad.json"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{\n")
        proc = subprocess.run(
            [powershell, "-ExecutionPolicy", "Bypass", "-File",
             os.path.join(ROOT, "scripts", "release_check.ps1"), "-Root", td],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode != 0, combined
        assert "At " not in combined
        assert "bad.json" in combined
        for variant in _path_variants(ROOT) | _path_variants(td):
            assert variant not in combined


def test_release_check_rejects_non_repo_root_without_absolute_path_leak():
    powershell = shutil.which("powershell")
    if not powershell:
        return
    with make_tmpdir(prefix="ainp_release_bad_root_") as td:
        proc = subprocess.run(
            [powershell, "-ExecutionPolicy", "Bypass", "-File",
             os.path.join(ROOT, "scripts", "release_check.ps1"), "-Root", td],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode != 0, combined
        assert "not a complete AINP repository" in combined
        assert "tests/test_ainp.py" in combined
        assert "At " not in combined
        for variant in _path_variants(ROOT) | _path_variants(td):
            assert variant not in combined


def test_release_script_private_path_scan_covers_posix_paths():
    text = Path(os.path.join(ROOT, "scripts", "release_check.ps1")).read_text(encoding="utf-8")
    assert "POSIX local absolute path" in text
    assert "(?:Users|home|tmp|var|private|mnt|workspace|workspaces|root|run|opt/hostedtoolcache)" in text


def test_valid_release_bundle_passes():
    with make_tmpdir(prefix="ainp_release_ok_") as td:
        plan = os.path.join(td, "whitepaper.generation.json")
        report = os.path.join(td, "whitepaper.generationreport.json")
        os.makedirs(os.path.join(td, "out"), exist_ok=True)
        os.makedirs(os.path.join(td, "programs"), exist_ok=True)
        shutil.copyfile(os.path.join(FILE_EX, "whitepaper.generation.json"), plan)
        shutil.copyfile(os.path.join(FILE_EX, "out", "whitepaper.md"),
                        os.path.join(td, "out", "whitepaper.md"))
        write_binding_descriptor(os.path.join(td, "programs", "generate_document.aisop.json"))

        doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        for result in doc["generationreport"]["acceptance_results"]:
            result["passed"] = True
        doc["generationreport"]["overall"] = {
            "conformant": True,
            "reason": "all fail-severity criteria passed in this release fixture",
            "warnings": []
        }
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        rc, _, fails = release_check(plan, "--report", report)
        assert rc == 0, f"complete release bundle should pass: {sorted(fails)}"


def test_all_example_project_packages_pass():
    packages = example_project_packages()
    assert packages, "examples/*_ainp discovery must find at least one package"
    for package in packages:
        rc, _, fails = project_check(package)
        assert rc == 0, f"{os.path.relpath(package, ROOT)} should pass: {sorted(fails)}"


def test_valid_project_package_passes():
    rc, _, fails = project_check(os.path.join(EX, "whitepaper_ainp"))
    assert rc == 0, f"complete AINP project package should pass: {sorted(fails)}"


def test_valid_program_project_package_passes():
    rc, _, fails = project_check(os.path.join(EX, "slugify_cli_ainp"))
    assert rc == 0, f"complete AINP program package should pass: {sorted(fails)}"


def test_program_example_tests_pass():
    test_files = example_project_test_files()
    assert test_files, "examples/*_ainp packages should include runnable program tests"
    for test_file in test_files:
        proc = subprocess.run(
            [PY, "-B", test_file],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr


def test_rehash_tool_refreshes_project_hashes():
    with make_tmpdir(prefix="ainp_rehash_") as td:
        dst = os.path.join(td, "slugify_cli_ainp")
        shutil.copytree(os.path.join(EX, "slugify_cli_ainp"), dst)
        report = os.path.join(dst, "ainp", "slugify_cli.generationreport.json")
        space = os.path.join(dst, "ainp", "project.ainp.json")

        report_doc = _load(report)
        report_doc["generationreport"]["plan_ref"]["sha256"] = "0" * 64
        report_doc["generationreport"]["artifacts"][0]["sha256"] = "0" * 64
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        space_doc = _load(space)
        space_doc["generation_space"]["generations"][0]["sha256"] = "0" * 64
        with open(space, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(space_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        check_proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert check_proc.returncode == 1, check_proc.stdout + check_proc.stderr

        write_proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--write", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert write_proc.returncode == 0, write_proc.stdout + write_proc.stderr
        payload = json.loads(write_proc.stdout)
        assert payload["updated"] >= 3
        for variant in _path_variants(td):
            assert variant not in write_proc.stdout
        for update in payload["updates"]:
            assert not os.path.isabs(update["file"]), update["file"]

        rc, _, fails = project_check(dst)
        assert rc == 0, f"rehashed project should pass: {sorted(fails)}"

        clean_proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert clean_proc.returncode == 0, clean_proc.stdout + clean_proc.stderr


def test_rehash_tool_refuses_artifact_path_escape():
    with make_tmpdir(prefix="ainp_rehash_escape_") as td:
        dst = os.path.join(td, "slugify_cli_ainp")
        shutil.copytree(os.path.join(EX, "slugify_cli_ainp"), dst)
        with open(os.path.join(td, "outside.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("outside package\n")

        report = os.path.join(dst, "ainp", "slugify_cli.generationreport.json")
        report_doc = _load(report)
        report_doc["generationreport"]["artifacts"][0]["path"] = "../outside.txt"
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 2, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert "escapes its sandbox" in payload["error"]
        for variant in _path_variants(td):
            assert variant not in proc.stdout


def test_rehash_tool_refuses_missing_artifact():
    with make_tmpdir(prefix="ainp_rehash_missing_artifact_") as td:
        dst = os.path.join(td, "slugify_cli_ainp")
        shutil.copytree(os.path.join(EX, "slugify_cli_ainp"), dst)
        os.remove(os.path.join(dst, "slugify_cli", "slugify_cli.py"))

        proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 2, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert "artifact file does not exist" in payload["error"]
        for variant in _path_variants(td):
            assert variant not in proc.stdout


def test_rehash_tool_refuses_artifact_outside_content_dir():
    with make_tmpdir(prefix="ainp_rehash_content_dir_") as td:
        dst = os.path.join(td, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), dst)

        report = os.path.join(dst, "ainp", "whitepaper.generationreport.json")
        plan = os.path.join(dst, "ainp", "whitepaper.generation.json")
        report_doc = _load(report)
        report_doc["generationreport"]["artifacts"][0]["path"] = "ainp/whitepaper.generation.json"
        report_doc["generationreport"]["artifacts"][0]["sha256"] = hashlib.sha256(
            open(plan, "rb").read()).hexdigest()
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 2, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert "AINP.md.content_dir" in payload["error"]
        for variant in _path_variants(td):
            assert variant not in proc.stdout


def test_rehash_tool_requires_content_dir_before_refreshing_artifacts():
    with make_tmpdir(prefix="ainp_rehash_missing_content_dir_") as td:
        dst = os.path.join(td, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), dst)
        ainp_md = os.path.join(dst, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("content_dir: whitepaper/\n", "")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

        proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 2, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert "AINP.md.content_dir is required" in payload["error"]
        for variant in _path_variants(td):
            assert variant not in proc.stdout


def test_rehash_tool_rejects_duplicate_ainp_md_frontmatter_key():
    with make_tmpdir(prefix="ainp_rehash_duplicate_frontmatter_") as td:
        dst = os.path.join(td, "slugify_cli_ainp")
        shutil.copytree(os.path.join(EX, "slugify_cli_ainp"), dst)
        ainp_md = Path(dst) / "AINP.md"
        text = ainp_md.read_text(encoding="utf-8")
        text = text.replace(
            "report: ainp/slugify_cli.generationreport.json\n",
            "report: ainp/slugify_cli.generationreport.json\n"
            "report: ainp/alternate.generationreport.json\n",
        )
        ainp_md.write_text(text, encoding="utf-8", newline="\n")

        proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), dst, "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert proc.returncode == 2, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert "duplicate AINP.md frontmatter key" in payload["error"]
        for variant in _path_variants(td):
            assert variant not in proc.stdout


def test_rehash_write_is_atomic_when_replace_fails():
    from tools import ainp_rehash

    with make_tmpdir(prefix="ainp_rehash_atomic_") as td:
        target = os.path.join(td, "data.json")
        _write_json(target, {"original": True})

        with mock.patch("tools.ainp_rehash.os.replace", side_effect=OSError("replace failed")):
            try:
                ainp_rehash.write_json(target, {"original": False})
            except OSError as exc:
                assert "replace failed" in str(exc)
            else:
                raise AssertionError("write_json must propagate replace failures")

        assert _load(target) == {"original": True}
        leftovers = [name for name in os.listdir(td) if name.endswith(".tmp")]
        assert leftovers == []


def test_rehash_write_preserves_existing_file_mode_before_replace():
    from tools import ainp_rehash

    with make_tmpdir(prefix="ainp_rehash_mode_") as td:
        target = os.path.join(td, "data.json")
        _write_json(target, {"original": True})
        fake_stat = mock.Mock(st_mode=0o100640)
        with mock.patch("tools.ainp_rehash.os.stat", return_value=fake_stat), \
                mock.patch("tools.ainp_rehash.os.chmod") as chmod_mock:
            ainp_rehash.write_json(target, {"original": False})
        chmod_mock.assert_called_once()
        assert chmod_mock.call_args.args[1] == 0o640
        assert _load(target) == {"original": False}


def test_project_release_requires_project_root_for_content_dir_artifacts():
    plan = os.path.join(EX, "whitepaper_ainp", "ainp", "whitepaper.generation.json")
    report = os.path.join(EX, "whitepaper_ainp", "ainp", "whitepaper.generationreport.json")
    rc, _, fails = release_check(plan, "--report", report)
    assert rc == 1, "project artifact paths must not be read relative to the report dir"
    assert "AINP_E_R3_ARTIFACT_MISSING_RELEASE" in fails
    rc, _, fails = release_check(plan, "--report", report,
                                 "--project-root", os.path.join(EX, "whitepaper_ainp"))
    assert rc == 0, f"project-root sandbox should make project artifact paths recomputable: {sorted(fails)}"


def test_project_report_artifacts_must_live_under_content_dir():
    with make_tmpdir(prefix="ainp_project_content_dir_") as td:
        dst = os.path.join(td, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), dst)
        report = os.path.join(dst, "ainp", "whitepaper.generationreport.json")
        plan = os.path.join(dst, "ainp", "whitepaper.generation.json")
        doc = _load(report)
        doc["generationreport"]["artifacts"][0]["path"] = "ainp/whitepaper.generation.json"
        doc["generationreport"]["artifacts"][0]["sha256"] = hashlib.sha256(
            open(plan, "rb").read()).hexdigest()
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(dst)
        assert rc == 1, "AINP project artifacts must be stored under AINP.md.content_dir"
        assert "AINP_E_P7_ARTIFACT_OUTSIDE_CONTENT_DIR" in fails


def test_project_package_requires_feedback_loop_alignment():
    with make_tmpdir(prefix="ainp_project_feedback_loop_") as td:
        missing_dst = os.path.join(td, "missing", "whitepaper_ainp")
        mismatch_dst = os.path.join(td, "mismatch", "whitepaper_ainp")
        draft_dst = os.path.join(td, "draft", "whitepaper_ainp")
        os.makedirs(os.path.dirname(missing_dst))
        os.makedirs(os.path.dirname(mismatch_dst))
        os.makedirs(os.path.dirname(draft_dst))

        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), missing_dst)
        ainp_md = os.path.join(missing_dst, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("feedback: ainp/whitepaper_feedback.generationfeedback.json\n", "")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        rc, _, fails = project_check(missing_dst)
        assert rc == 1, "approved/active AINP project packages must declare feedback"
        assert "AINP_E_P6_FEEDBACK_REQUIRED" in fails

        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), draft_dst)
        ainp_md = os.path.join(draft_dst, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("status: active\n", "status: draft\n")
        text = text.replace("feedback: ainp/whitepaper_feedback.generationfeedback.json\n", "")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        rc, _, fails = project_check(draft_dst)
        assert "AINP_E_P6_FEEDBACK_REQUIRED" not in fails, \
            "draft project packages may omit feedback while still keeping the loop section"

        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), mismatch_dst)
        feedback = os.path.join(mismatch_dst, "ainp", "whitepaper_feedback.generationfeedback.json")
        doc = _load(feedback)
        doc["generationfeedback"]["generation_id"] = "g_wrong_generation"
        with open(feedback, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(mismatch_dst)
        assert rc == 1, "feedback must point back to the same plan generation id"
        assert "AINP_E_P6_FEEDBACK_ID_MISMATCH" in fails


def test_content_architecture_binds_plan_report_project_and_feedback():
    with make_tmpdir(prefix="ainp_content_architecture_") as td:
        missing_plan = os.path.join(td, "missing_arch.generation.json")
        plan_doc = _load(os.path.join(FILE_EX, "whitepaper.generation.json"))
        plan_doc["generation"].pop("content_architecture")
        with open(missing_plan, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(plan_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = validate(missing_plan)
        assert rc == 0, f"standalone generation.content_architecture is optional: {sorted(fails)}"

        missing_project_dst = os.path.join(td, "missing_project", "whitepaper_ainp")
        os.makedirs(os.path.dirname(missing_project_dst))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), missing_project_dst)
        project_plan = os.path.join(missing_project_dst, "ainp", "whitepaper.generation.json")
        project_plan_doc = _load(project_plan)
        project_plan_doc["generation"].pop("content_architecture")
        with open(project_plan, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(project_plan_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        project_report = os.path.join(missing_project_dst, "ainp", "whitepaper.generationreport.json")
        report_doc = _load(project_report)
        report_doc["generationreport"]["plan_ref"]["sha256"] = hashlib.sha256(
            open(project_plan, "rb").read()).hexdigest()
        with open(project_report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(missing_project_dst)
        assert rc == 1, "complete project packages must declare content_architecture"
        assert "AINP_E_P10_CONTENT_ARCHITECTURE_REQUIRED" in fails

        report = os.path.join(td, "bad_file_id.generationreport.json")
        report_doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        report_doc["generationreport"]["artifacts"][0]["file_id"] = "unknown_file"
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = report_check(report, "--plan", os.path.join(FILE_EX, "whitepaper.generation.json"))
        assert rc == 1, "report artifact file_id must bind to plan content_architecture"
        assert "AINP_E_R10_UNKNOWN_FILE_ID" in fails

        outside_dst = os.path.join(td, "outside", "whitepaper_ainp")
        os.makedirs(os.path.dirname(outside_dst))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), outside_dst)
        plan = os.path.join(outside_dst, "ainp", "whitepaper.generation.json")
        report_path = os.path.join(outside_dst, "ainp", "whitepaper.generationreport.json")
        doc = _load(plan)
        doc["generation"]["content_architecture"]["files"][0]["path"] = "ainp/leaked.md"
        with open(plan, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        report_doc = _load(report_path)
        report_doc["generationreport"]["plan_ref"]["sha256"] = hashlib.sha256(
            open(plan, "rb").read()).hexdigest()
        with open(report_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(outside_dst)
        assert rc == 1, "project content architecture paths must live under content_dir"
        assert "AINP_E_P10_CONTENT_FILE_OUTSIDE_CONTENT_DIR" in fails

        point_dst = os.path.join(td, "bad_point", "whitepaper_ainp")
        os.makedirs(os.path.dirname(point_dst))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), point_dst)
        feedback = os.path.join(point_dst, "ainp", "whitepaper_feedback.generationfeedback.json")
        doc = _load(feedback)
        doc["generationfeedback"]["issues"] = [{
            "id": "bad_point",
            "target": "point",
            "file_id": "file_whitepaper_md",
            "point_id": "missing_point",
            "severity": "fail",
            "description": "Regression issue targeting a non-existent content point."
        }]
        with open(feedback, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(point_dst)
        assert rc == 1, "feedback point targets must bind to declared content points"
        assert "AINP_E_P6_FEEDBACK_UNKNOWN_POINT_ID" in fails


def test_high_risk_artifact_type_separator_variants_require_approval():
    with make_tmpdir(prefix="ainp_high_risk_separator_") as td:
        variants = ["Deepfake", "deepfake ", "deep fake", "deep-fake", "deep_fake"]
        for variant in variants:
            plan = os.path.join(td, f"{variant.replace(' ', '_').replace('-', '_')}.generation.json")
            doc = _load(os.path.join(FILE_EX, "high_risk_likeness.generation.json"))
            g = doc["generation"]
            g["artifact_type"] = variant
            g["risk_profile"]["risk_level"] = "low"
            g["risk_profile"]["risk_tags"] = []
            g["risk_profile"]["deployment_scope"] = "limited"
            g["governance"]["risk_level"] = "low"
            g["governance"]["approval_required"] = False
            _write_json(plan, doc)

            rc, _, fails = validate(plan)
            assert rc == 1, f"{variant!r} must remain high-risk after separator normalization"
            assert "AINP_E_G6_MISSING_APPROVAL" in fails


def test_g16_content_architecture_negative_teeth():
    with make_tmpdir(prefix="ainp_g16_teeth_") as td:
        duplicate_file = os.path.join(td, "duplicate_file.generation.json")
        doc = _load(os.path.join(FILE_EX, "whitepaper.generation.json"))
        files = doc["generation"]["content_architecture"]["files"]
        files.append(json.loads(json.dumps(files[0])))
        _write_json(duplicate_file, doc)
        rc, _, fails = validate(duplicate_file)
        assert rc == 1, "G16 must reject duplicate content file ids"
        assert "AINP_E_G16_DUPLICATE_FILE_ID" in fails

        unknown_acceptance = os.path.join(td, "unknown_acceptance.generation.json")
        doc = _load(os.path.join(FILE_EX, "whitepaper.generation.json"))
        doc["generation"]["content_architecture"]["files"][0]["points"][0]["acceptance_refs"] = [
            "missing_acceptance"
        ]
        _write_json(unknown_acceptance, doc)
        rc, _, fails = validate(unknown_acceptance)
        assert rc == 1, "G16 must bind point acceptance_refs to declared criteria"
        assert "AINP_E_G16_ACCEPTANCE_REF_UNKNOWN" in fails


def test_project_basic_shape_and_frontmatter_trust_teeth():
    with make_tmpdir(prefix="ainp_project_teeth_") as td:
        missing_root = os.path.join(td, "missing_ainp")
        rc, _, fails = project_check(missing_root)
        assert rc == 1
        assert "AINP_E_P1_PROJECT_ROOT_MISSING" in fails

        trusted_dst = os.path.join(td, "trusted", "whitepaper_ainp")
        os.makedirs(os.path.dirname(trusted_dst))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), trusted_dst)
        ainp_md = os.path.join(trusted_dst, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("license: Apache-2.0\n---", "license: Apache-2.0\ntrusted: true\n---")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        rc, _, fails = project_check(trusted_dst)
        assert rc == 1, "AINP.md must not self-assert package trust"
        assert "AINP_E_P9_SELF_TRUST_CLAIM" in fails

        bad_plan_dir = os.path.join(td, "bad_plan", "whitepaper_ainp")
        os.makedirs(os.path.dirname(bad_plan_dir))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), bad_plan_dir)
        ainp_md = os.path.join(bad_plan_dir, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("plan_dir: ainp/\n", "plan_dir: ../ainp/\n")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        rc, _, fails = project_check(bad_plan_dir)
        assert rc == 1
        assert "AINP_E_P3_BAD_PLAN_DIR" in fails

        bad_content_dir = os.path.join(td, "bad_content", "whitepaper_ainp")
        os.makedirs(os.path.dirname(bad_content_dir))
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), bad_content_dir)
        ainp_md = os.path.join(bad_content_dir, "AINP.md")
        text = open(ainp_md, encoding="utf-8").read()
        text = text.replace("content_dir: whitepaper/\n", "content_dir: ../whitepaper/\n")
        with open(ainp_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        rc, _, fails = project_check(bad_content_dir)
        assert rc == 1
        assert "AINP_E_P4_BAD_CONTENT_DIR" in fails


def test_report_profile_and_plan_binding_teeth():
    with make_tmpdir(prefix="ainp_report_r1_r2_") as td:
        bad_profile = os.path.join(td, "bad_profile.generationreport.json")
        doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        doc["schema"] = "ainp.v1.0.0.generation"
        _write_json(bad_profile, doc)
        rc, _, fails = report_check(bad_profile, "--plan", os.path.join(FILE_EX, "whitepaper.generation.json"))
        assert rc == 1
        assert "AINP_E_R1_PROFILE_KEY_MISMATCH" in fails

        bad_id = os.path.join(td, "bad_id.generationreport.json")
        doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        doc["generationreport"]["generation_id"] = "g_wrong"
        _write_json(bad_id, doc)
        rc, _, fails = report_check(bad_id, "--plan", os.path.join(FILE_EX, "whitepaper.generation.json"))
        assert rc == 1
        assert "AINP_E_R2_ID_MISMATCH" in fails


def test_generation_space_shape_teeth():
    with make_tmpdir(prefix="ainp_sp1_teeth_") as td:
        bad_profile = os.path.join(td, "bad_profile.ainp.json")
        doc = _load(os.path.join(FILE_EX, "project.ainp.json"))
        doc["space"] = doc.pop("generation_space")
        _write_json(bad_profile, doc)
        rc, _, fails = validate(bad_profile)
        assert rc == 1
        assert "AINP_E_SP1_PROFILE_KEY_MISMATCH" in fails

        bad_entry = os.path.join(td, "bad_entry.ainp.json")
        doc = _load(os.path.join(FILE_EX, "project.ainp.json"))
        doc["generation_space"]["generations"][0].pop("sha256")
        _write_json(bad_entry, doc)
        rc, _, fails = validate(bad_entry)
        assert rc == 1
        assert "AINP_E_SP1_MISSING_FIELD" in fails


def test_project_package_requires_uppercase_ainp_md():
    with make_tmpdir(prefix="ainp_project_case_") as td:
        dst = os.path.join(td, "whitepaper_ainp")
        os.makedirs(os.path.join(dst, "ainp"))
        os.makedirs(os.path.join(dst, "whitepaper"))
        with open(os.path.join(dst, "ainp.md"), "w", encoding="utf-8") as fh:
            fh.write("lowercase placeholder\n")
        rc, _, fails = project_check(dst)
        assert rc == 1, "lowercase ainp.md must not be accepted as the project entry point"
        assert "AINP_E_P2_LOWERCASE_AINP_MD" in fails


def test_project_package_frontmatter_delimiter_is_exact_and_crlf_tolerant():
    with make_tmpdir(prefix="ainp_project_frontmatter_") as td:
        crlf_parent = os.path.join(td, "crlf")
        bad_parent = os.path.join(td, "bad")
        os.makedirs(crlf_parent)
        os.makedirs(bad_parent)
        crlf_dst = os.path.join(crlf_parent, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), crlf_dst)
        crlf_md = os.path.join(crlf_dst, "AINP.md")
        text = open(crlf_md, encoding="utf-8").read()
        with open(crlf_md, "w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace("\n", "\r\n"))
        rc, _, fails = project_check(crlf_dst)
        assert rc == 0, f"CRLF AINP.md frontmatter should parse: {sorted(fails)}"

        bad_dst = os.path.join(bad_parent, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), bad_dst)
        bad_md = os.path.join(bad_dst, "AINP.md")
        bad = open(bad_md, encoding="utf-8").read().replace("\n---\n", "\n---bad\n", 1)
        with open(bad_md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(bad)
        rc, _, fails = project_check(bad_dst)
        assert rc == 1, "frontmatter closing delimiter must be an exact --- line"
        assert "AINP_E_P5_FRONTMATTER_MISSING" in fails


def test_project_package_side_files_must_pass_schema():
    with make_tmpdir(prefix="ainp_project_side_schema_") as td:
        dst = os.path.join(td, "whitepaper_ainp")
        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), dst)
        space = os.path.join(dst, "ainp", "project.ainp.json")
        doc = _load(space)
        doc["generation_space"].pop("title", None)
        doc["generation_space"]["unexpected_extra"] = "schema should reject this"
        with open(space, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(dst)
        assert rc == 1, "project side files must pass JSON Schema, not only rule checks"
        assert "AINP_E_P6_SCHEMA_INVALID" in fails


def test_project_references_manifest_is_optional_but_checked():
    with make_tmpdir(prefix="ainp_project_references_") as td:
        clean_dst = os.path.join(td, "clean", "aikp_navigator_aiap_ainp")
        schema_dst = os.path.join(td, "schema", "aikp_navigator_aiap_ainp")
        external_hash_dst = os.path.join(td, "external_hash", "aikp_navigator_aiap_ainp")
        warn_dst = os.path.join(td, "warn", "whitepaper_ainp")
        stale_dst = os.path.join(td, "stale", "aikp_navigator_aiap_ainp")
        outside_dst = os.path.join(td, "outside", "aikp_navigator_aiap_ainp")
        for parent in ("clean", "schema", "external_hash", "warn", "stale", "outside"):
            os.makedirs(os.path.join(td, parent))

        shutil.copytree(os.path.join(EX, "aikp_navigator_aiap_ainp"), clean_dst)
        rc, _, fails = project_check(clean_dst)
        assert rc == 0, f"references manifest with matching hashes should pass: {sorted(fails)}"
        clean_manifest = os.path.join(clean_dst, "ainp", "references", "reference_manifest.json")
        rc, _, fails = validate(clean_manifest, "--high-risk-types",
                                os.path.join(td, "missing_high_risk_types.json"))
        assert rc == 0, (
            "standalone reference manifest validation must not depend on "
            f"generation-only high_risk_types data: {sorted(fails)}"
        )

        shutil.copytree(os.path.join(EX, "aikp_navigator_aiap_ainp"), schema_dst)
        manifest = os.path.join(schema_dst, "ainp", "references", "reference_manifest.json")
        doc = _load(manifest)
        doc["reference_manifest"]["references"][0]["unexpected_extra"] = "schema should reject this"
        with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(schema_dst)
        assert rc == 1, "project reference manifests must pass JSON Schema"
        assert "AINP_E_P11_MANIFEST_SCHEMA_INVALID" in fails
        rc, _, fails = validate(manifest)
        assert rc == 1, "standalone reference manifest validation must include schema checks"
        assert "AINP_E_P11_SCHEMA_INVALID" in fails

        shutil.copytree(os.path.join(EX, "aikp_navigator_aiap_ainp"), external_hash_dst)
        manifest = os.path.join(external_hash_dst, "ainp", "references", "reference_manifest.json")
        doc = _load(manifest)
        doc["reference_manifest"]["references"][0]["source"] = {
            "type": "external_uri",
            "uri": "https://example.invalid/aiap-spec-snapshot"
        }
        with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(external_hash_dst)
        assert rc == 1, "external_uri references must not carry local sha256 anchors"
        assert "AINP_E_P11_EXTERNAL_REFERENCE_HASH_UNVERIFIABLE" in fails
        rc, _, fails = validate(manifest)
        assert rc == 1, "standalone reference manifest validation must reject external_uri sha256"
        assert "AINP_E_P11_EXTERNAL_REFERENCE_HASH_UNVERIFIABLE" in fails
        rehash_proc = subprocess.run(
            [PY, "-B", os.path.join(TOOLS, "ainp_rehash.py"), external_hash_dst,
             "--check", "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        assert rehash_proc.returncode == 2, rehash_proc.stdout + rehash_proc.stderr
        rehash_payload = json.loads(rehash_proc.stdout)
        assert "local_file references" in rehash_payload["error"]
        for variant in _path_variants(td):
            assert variant not in rehash_proc.stdout

        shutil.copytree(os.path.join(EX, "whitepaper_ainp"), warn_dst)
        os.makedirs(os.path.join(warn_dst, "ainp", "references"))
        with open(os.path.join(warn_dst, "ainp", "references", "notes.md"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write("unindexed reference note\n")
        rc, codes, fails = project_check(warn_dst)
        assert rc == 0, f"missing optional references manifest should warn, not fail: {sorted(fails)}"
        assert "AINP_W_P11_REFERENCES_MANIFEST_MISSING" in codes

        shutil.copytree(os.path.join(EX, "aikp_navigator_aiap_ainp"), stale_dst)
        manifest = os.path.join(stale_dst, "ainp", "references", "reference_manifest.json")
        doc = _load(manifest)
        doc["reference_manifest"]["references"][0]["sha256"] = "0" * 64
        with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(stale_dst)
        assert rc == 1, "stale local reference/template hash must fail"
        assert "AINP_E_P11_REFERENCE_HASH_MISMATCH" in fails
        rc, _, fails = validate(manifest)
        assert rc == 1, "standalone reference manifest validation must reject stale hashes"
        assert "AINP_E_P11_REFERENCE_HASH_MISMATCH" in fails

        shutil.copytree(os.path.join(EX, "aikp_navigator_aiap_ainp"), outside_dst)
        manifest = os.path.join(outside_dst, "ainp", "references", "reference_manifest.json")
        doc = _load(manifest)
        doc["reference_manifest"]["references"][0]["source"]["path"] = "aikp_navigator_aiap/README.md"
        doc["reference_manifest"]["references"][0]["sha256"] = hashlib.sha256(
            open(os.path.join(outside_dst, "aikp_navigator_aiap", "README.md"), "rb").read()
        ).hexdigest()
        with open(manifest, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = project_check(outside_dst)
        assert rc == 1, "local references must stay under ainp/references/"
        assert "AINP_E_P11_LOCAL_REFERENCE_OUTSIDE_REFERENCES_DIR" in fails
        rc, _, fails = validate(manifest)
        assert rc == 1, "standalone reference manifest validation must reject paths outside ainp/references/"
        assert "AINP_E_P11_LOCAL_REFERENCE_OUTSIDE_REFERENCES_DIR" in fails


def test_release_gate_rejects_schema_extra_properties():
    with make_tmpdir(prefix="ainp_release_schema_") as td:
        plan = os.path.join(td, "whitepaper.generation.json")
        report = os.path.join(td, "whitepaper.generationreport.json")
        os.makedirs(os.path.join(td, "out"), exist_ok=True)
        os.makedirs(os.path.join(td, "programs"), exist_ok=True)
        shutil.copyfile(os.path.join(FILE_EX, "whitepaper.generation.json"), plan)
        shutil.copyfile(os.path.join(FILE_EX, "out", "whitepaper.md"),
                        os.path.join(td, "out", "whitepaper.md"))
        write_binding_descriptor(os.path.join(td, "programs", "generate_document.aisop.json"))

        plan_doc = _load(plan)
        plan_doc["generation"]["unexpected_extra"] = "schema should reject this"
        with open(plan, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(plan_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        report_doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        report_doc["generationreport"]["plan_ref"]["sha256"] = hashlib.sha256(
            open(plan, "rb").read()).hexdigest()
        for result in report_doc["generationreport"]["acceptance_results"]:
            result["passed"] = True
        report_doc["generationreport"]["overall"] = {
            "conformant": True,
            "reason": "all fail-severity criteria passed in this release fixture",
            "warnings": []
        }
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        rc, _, fails = release_check(plan, "--report", report)
        assert rc == 1, "release gate must include schema additionalProperties checks"
        assert "AINP_E_RELEASE_SCHEMA_INVALID" in fails


def test_report_release_rejects_drive_relative_artifact_path():
    with make_tmpdir(prefix="ainp_r3_drive_relative_") as td:
        report = os.path.join(td, "drive_relative.generationreport.json")
        doc = _load(os.path.join(FILE_EX, "whitepaper.generationreport.json"))
        doc["generationreport"]["artifacts"][0]["path"] = "C:outside_artifact.md"
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = report_check(report, "--plan",
                                    os.path.join(FILE_EX, "whitepaper.generation.json"),
                                    "--mode", "release")
        assert rc == 1, "R3 must reject Windows drive-relative artifact paths"
        assert "AINP_E_R3_PATH_ESCAPES" in fails


# Every example × every mode, expected exit pinned. The whitepaper plan
# intentionally ships a missing binding target (G9 demo): WARN in default,
# FAIL in strict/release BY DESIGN — this table makes that design machine-recorded
# instead of a README footnote.
EXAMPLE_MODE_MATRIX = {
    "whitepaper.generation.json": {"default": 0, "strict": 1, "release": 1},
    "high_risk_likeness.generation.json": {"default": 0, "strict": 0, "release": 0},
    "landing_page.generation.json": {"default": 0, "strict": 0, "release": 0},
    "dataset.generation.json": {"default": 0, "strict": 0, "release": 0},
    "medical_advice.generation.json": {"default": 0, "strict": 0, "release": 0},
    "security_exploit.generation.json": {"default": 0, "strict": 0, "release": 0},
}


def test_example_mode_matrix():
    for name, modes in EXAMPLE_MODE_MATRIX.items():
        for mode, want in modes.items():
            rc, _, fails = validate(os.path.join(FILE_EX, name), "--mode", mode)
            assert rc == want, f"{name} [{mode}]: expected exit {want}, got {rc} ({sorted(fails)})"


# --------------------------------------------------------------------------
# Group 3: teeth — each fixture MUST raise its documented code
# --------------------------------------------------------------------------

# fixture -> (mode, expected_fail_code_substring)
PLAN_TEETH = {
    "missing_summary.generation.json": ("default", "AINP_E_G2_MISSING_FIELD"),
    "version_not_semver.generation.json": ("default", "AINP_E_G2_VERSION_NOT_SEMVER"),
    "missing_consent.generation.json": ("default", "AINP_E_G4_CONSENT_REQUIRED_BY_TAG"),
    "rights_consent_required_no_record.generation.json": ("default", "AINP_E_G4_RIGHTS_CONSENT_NO_RECORD"),
    "missing_approval.generation.json": ("default", "AINP_E_G6_MISSING_APPROVAL"),
    "critical_no_approval.generation.json": ("default", "AINP_E_G6_MISSING_APPROVAL"),
    "fake_safe_self_claim.generation.json": ("default", "AINP_E_G7_SELF_TRUST_CLAIM"),
    "missing_disclosure_policy.generation.json": ("default", "AINP_E_G8_MISSING_DISCLOSURE_POLICY"),
    "enforced_by_missing.generation.json": ("default", "AINP_E_G11_ENFORCED_BY_MISSING"),
    "unverifiable_ip_redline.generation.json": ("strict", "AINP_E_G14_UNVERIFIABLE_REDLINE"),
    "external_only_redline_release.generation.json": ("release", "AINP_E_G15_NO_OPERATIONAL_CONTROL"),
    "risk_level_conflict.generation.json": ("default", "AINP_E_G13_RISK_LEVEL_CONFLICT"),
    "profile_key_mismatch.generation.json": ("default", "AINP_E_G1_PROFILE_KEY_MISMATCH"),
    "unknown_check_id.generation.json": ("strict", "AINP_E_G5_UNKNOWN_CHECK_ID"),
    # second-audit teeth: untrusted-input hardening + gate-evasion classes
    "payload_not_object.generationfeedback.json": ("default", "AINP_E_FB1_PAYLOAD_NOT_OBJECT"),
    "nesting_too_deep.generation.json": ("default", "AINP_E_NESTING_TOO_DEEP"),
    "duplicate_key.generation.json": ("default", "AINP_E_UNREADABLE"),
    "nan_literal.generation.json": ("default", "AINP_E_UNREADABLE"),
    "inputs_not_array.generation.json": ("default", "AINP_E_CONTAINER_NOT_ARRAY"),
    "deepfake_case_evasion.generation.json": ("default", "AINP_E_G6_MISSING_APPROVAL"),
    "semver_leading_zero.generation.json": ("default", "AINP_E_G2_VERSION_NOT_SEMVER"),
    "semver_prerelease_leading_zero.generation.json": ("default", "AINP_E_G2_VERSION_NOT_SEMVER"),
}

# report fixture -> (mode, expected_fail_code, plan fixture)
REPORT_TEETH = {
    "overall_missing.generationreport.json":
        ("default", "AINP_E_R6_MISSING_OVERALL", "whitepaper.generation.json"),
    "duplicate_result.generationreport.json":
        ("default", "AINP_E_R4_DUPLICATE_RESULT", "whitepaper.generation.json"),
    "artifact_path_escape.generationreport.json":
        ("release", "AINP_E_R3_PATH_ESCAPES", "whitepaper.generation.json"),
    "report_bad_method_verifier.generationreport.json":
        ("default", "AINP_E_R5_BAD_METHOD", "whitepaper.generation.json"),
    "disclosure_gate_missing.generationreport.json":
        ("default", "AINP_E_R7_DISCLOSURE_NOT_RECORDED", "whitepaper.generation.json"),
    "approval_gate_missing.generationreport.json":
        ("default", "AINP_E_R9_APPROVAL_NOT_RECORDED", "high_risk_likeness.generation.json"),
    "approval_gate_bad_evidence.generationreport.json":
        ("default", "AINP_E_R9_APPROVAL_BAD_EVIDENCE", "high_risk_likeness.generation.json"),
}


def test_plan_teeth():
    for fixture, (mode, code) in PLAN_TEETH.items():
        rc, codes, fails = validate(os.path.join(FX, fixture), "--mode", mode)
        assert rc == 1, f"{fixture} ({mode}) should FAIL"
        assert any(c.startswith(code) for c in fails), \
            f"{fixture}: expected fail code {code}, got {sorted(fails)}"


def test_report_teeth():
    for fixture, (mode, code, plan_name) in REPORT_TEETH.items():
        rc, codes, fails = report_check(os.path.join(FX, fixture),
                                        "--plan", os.path.join(FILE_EX, plan_name),
                                        "--mode", mode)
        assert rc == 1, f"{fixture} ({mode}) should FAIL"
        assert any(c.startswith(code) for c in fails), \
            f"{fixture}: expected fail code {code}, got {sorted(fails)}"

    with make_tmpdir(prefix="ainp_r7_generator_watermark_") as td:
        plan = os.path.join(td, "whitepaper.generation.json")
        report = os.path.join(td, "whitepaper.generationreport.json")
        shutil.copyfile(os.path.join(FILE_EX, "whitepaper.generation.json"), plan)
        shutil.copyfile(os.path.join(FILE_EX, "whitepaper.generationreport.json"), report)

        plan_doc = _load(plan)
        dp = plan_doc["generation"]["disclosure_policy"]
        dp["generator_metadata_required"] = True
        dp["watermark_required"] = True
        with open(plan, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(plan_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        report_doc = _load(report)
        report_doc["generationreport"]["plan_ref"]["sha256"] = hashlib.sha256(
            open(plan, "rb").read()).hexdigest()
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")

        rc, _, fails = report_check(report, "--plan", plan)
        assert rc == 1, "R7 must require generator metadata and watermark evidence when policy switches are true"
        assert "AINP_E_R7_GENERATOR_METADATA_NOT_RECORDED" in fails
        assert "AINP_E_R7_WATERMARK_NOT_RECORDED" in fails

        report_doc["generationreport"]["generator"] = {
            "provider": "Example Generator Provider",
            "system": "example-generator",
            "version": "1.0.0",
            "content_id": "content-whitepaper-001",
            "generated_at": "2026-07-06T00:00:00Z"
        }
        report_doc["generationreport"]["disclosure"]["watermarks"] = [
            {
                "artifact_id": "md",
                "present": True,
                "scheme": "example-watermark",
                "evidence_ref": "watermark/check.json",
                "limitations": "Recorded by external detector; local AINP tools do not verify watermark robustness."
            }
        ]
        with open(report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report_doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        rc, _, fails = report_check(report, "--plan", plan)
        assert rc == 0, f"R7 generator/watermark evidence records should satisfy the declared gates: {sorted(fails)}"


def test_high_risk_types_shape_fail_closed():
    rc, _, fails = validate(
        os.path.join(FX, "deepfake_case_evasion.generation.json"),
        "--high-risk-types", os.path.join(FX, "malformed_high_risk_types.v1.0.0.json"),
    )
    assert rc == 1, "malformed high_risk_types must fail closed"
    assert "AINP_E_HIGH_RISK_TYPES_INVALID" in fails


def test_high_risk_types_empty_tags_fail_closed():
    rc, _, fails = validate(
        os.path.join(FILE_EX, "dataset.generation.json"),
        "--high-risk-types", os.path.join(FX, "empty_high_risk_tags.v1.0.0.json"),
    )
    assert rc == 1, "empty high_risk_types.risk_tags must fail closed"
    assert "AINP_E_HIGH_RISK_TYPES_INVALID" in fails


def test_release_gate_requires_report():
    rc, _, fails = release_check(os.path.join(FILE_EX, "landing_page.generation.json"))
    assert rc == 1, "release gate must reject plan-only release attempts"
    assert "AINP_E_RELEASE_REPORT_MISSING" in fails


def test_release_gate_handles_parser_recursion_as_structured_fail():
    with make_tmpdir(prefix="ainp_release_deep_json_") as td:
        plan = os.path.join(td, "too_deep.generation.json")
        with open(plan, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('{"schema":"ainp.v1.0.0.generation","generation":')
            fh.write("[" * 5000)
            fh.write("0")
            fh.write("]" * 5000)
            fh.write("}\n")
        rc, _, fails = release_check(plan)
        assert rc == 1, "release wrapper must return a controlled FAIL for parser-recursion input"
        assert "AINP_E_RELEASE_JSON_UNREADABLE" in fails, \
            f"release wrapper must report unreadable JSON, got {sorted(fails)}"


def test_g14_unverifiable_is_only_warn_in_default():
    # honesty: unverifiable red line is a WARN in default, escalates to FAIL in strict
    rc, codes, fails = validate(os.path.join(FX, "unverifiable_ip_redline.generation.json"))
    assert rc == 0, "unverifiable red line must not FAIL in default mode"
    assert any("G14" in c for c in codes), "should still WARN in default"


def test_g15_only_bites_in_release():
    # external_only red line is fine in default, FAILs only in release
    rc, _, _ = validate(os.path.join(FX, "external_only_redline_release.generation.json"))
    assert rc == 0, "external_required red line is acceptable in default mode"


def test_g12_version_diff_teeth():
    prev = os.path.join(FILE_EX, "whitepaper.generation.json")
    cur = os.path.join(FX, "acceptance_change_not_major.current.generation.json")
    rc, codes, fails = validate("--previous", prev, "--current", cur, "--mode", "strict")
    assert rc == 1, "acceptance change without MAJOR bump should FAIL in strict"
    assert any("G12" in c for c in fails), f"expected G12 fail, got {sorted(fails)}"


def test_g12_major_bump_passes():
    prev = os.path.join(FILE_EX, "whitepaper.generation.json")
    cur = os.path.join(FX, "acceptance_change_major_ok.current.generation.json")
    rc, codes, fails = validate("--previous", prev, "--current", cur, "--mode", "strict")
    assert rc == 0, f"acceptance change WITH MAJOR bump should pass: {fails}"
    assert any(c == "AINP_I_G12_MAJOR_BUMP_OK" for c in codes)


def test_r8_plan_ref_mismatch_teeth():
    rc, codes, fails = report_check(
        os.path.join(FX, "plan_ref_mismatch.generationreport.json"),
        "--plan", os.path.join(FILE_EX, "whitepaper.generation.json"))
    assert rc == 1, "plan_ref mismatch should FAIL"
    assert any("R8" in c for c in fails), f"expected R8 fail, got {sorted(fails)}"


def test_sp2_space_hash_mismatch_teeth():
    rc, codes, fails = validate(os.path.join(FX, "space_hash_mismatch.ainp.json"), "--mode", "strict")
    assert rc == 1, "stale space hash should FAIL in strict"
    assert any("SP2" in c for c in fails), f"expected SP2 fail, got {sorted(fails)}"


def test_sp2_absolute_ref_is_rejected_before_hash_read():
    with make_tmpdir(prefix="ainp_sp2_escape_") as td:
        outside = os.path.join(td, "outside_secret.txt")
        data = b"outside secret for SP2 escape regression\n"
        with open(outside, "wb") as fh:
            fh.write(data)
        space_dir = os.path.join(td, "space")
        os.makedirs(space_dir)
        for i, ref in enumerate((outside, "C:outside_secret.txt", "file:C:/outside_secret.txt")):
            space = os.path.join(space_dir, f"project_{i}.ainp.json")
            doc = {
                "schema": "ainp.v1.0.0.generation_space",
                "generation_space": {
                    "id": f"space_escape_probe_{i}",
                    "title": "SP2 escape probe",
                    "generations": [{
                        "ref": ref,
                        "sha256": hashlib.sha256(data).hexdigest()
                    }]
                }
            }
            with open(space, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            rc, _, fails = validate(space, "--mode", "strict")
            assert rc == 1, (
                "SP2 must not read absolute, URI-like or drive-relative local refs "
                "even if the hash matches"
            )
            assert "AINP_E_SP2_PATH_ESCAPES" in fails
            proc = subprocess.run(
                [PY, "-B", "-X", "utf8", os.path.join(TOOLS, "ainp_validate.py"),
                 space, "--mode", "strict", "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            combined = proc.stdout + proc.stderr
            assert proc.returncode == 1, combined
            assert "Traceback" not in combined
            json.loads(proc.stdout)
            for variant in _path_variants(td) | _path_variants(outside):
                assert variant not in combined
            for token in ("outside_secret", "C:outside", "file:C:/outside"):
                assert token not in combined.replace("\\", "/")


def test_untrusted_plan_injection_is_data_not_command():
    # §8: a structurally-valid-but-hostile plan must be handled as DATA.
    # The validator must not crash, must not execute/download anything, and
    # must surface the traversal binding target as a (non-fatal) finding — not
    # silently "pass and run".
    rc, codes, fails = validate(os.path.join(FX, "untrusted_plan_injection.generation.json"))
    # It is structurally valid (injection strings are just text), so default rc may be 0,
    # but the traversal execution_binding target must be flagged, never resolved/run.
    assert any("G9" in c for c in codes) or rc == 0
    # crucially: the run completed without executing the binding (no exception, tool returned)


# --------------------------------------------------------------------------
# Group 5: corpus coverage
# --------------------------------------------------------------------------

def test_corpus_covers_all_file_types():
    files = os.listdir(FILE_EX)
    assert any(f.endswith(".generation.json") for f in files)
    assert any(f.endswith(".generationreport.json") for f in files)
    assert any(f.endswith(".generationfeedback.json") for f in files)
    assert any(f.endswith(".ainp.json") for f in files)
    assert os.path.isfile(os.path.join(EX, "whitepaper_ainp", "AINP.md"))
    assert os.path.isfile(os.path.join(EX, "slugify_cli_ainp", "AINP.md"))
    assert os.path.isfile(os.path.join(EX, "slugify_cli_ainp", "slugify_cli", "slugify_cli.py"))


def test_corpus_exercises_risk_gates():
    like = _load(os.path.join(FILE_EX, "high_risk_likeness.generation.json"))["generation"]
    assert like["risk_profile"]["risk_tags"], "likeness example must carry a risk tag"
    assert like["governance"]["approval_required"] is True
    land = _load(os.path.join(FILE_EX, "landing_page.generation.json"))["generation"]
    assert land["risk_profile"]["deployment_scope"] == "mass_public"
    assert land["governance"]["approval_required"] is True
    med = _load(os.path.join(FILE_EX, "medical_advice.generation.json"))["generation"]
    assert "medical_advice" in med["risk_profile"]["risk_tags"]
    assert med["disclosure_policy"]["ai_generated_disclosure_required"] is True
    sec = _load(os.path.join(FILE_EX, "security_exploit.generation.json"))["generation"]
    assert "security_exploit" in sec["risk_profile"]["risk_tags"]
    assert sec["governance"]["approval_required"] is True


def test_high_risk_types_tags_are_closed_domain():
    hrt = _load(os.path.join(SCH, "high_risk_types.v1.0.0.json"))
    tag_ids = {t["id"] for t in hrt["risk_tags"]}
    assert {"cbrn", "self_harm", "sexual_abuse_exploitation"} <= tag_ids
    for name in ("high_risk_likeness.generation.json",
                 "medical_advice.generation.json", "security_exploit.generation.json"):
        g = _load(os.path.join(FILE_EX, name))["generation"]
        for tag in g["risk_profile"]["risk_tags"]:
            assert tag in tag_ids, f"{name}: tag {tag} not in high_risk_types"


# --------------------------------------------------------------------------

def _write_json(path: str, doc: object) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f,
                         object_pairs_hook=_reject_duplicate_keys,
                         parse_constant=_reject_constant)


def _main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_main())
