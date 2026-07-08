#!/usr/bin/env python3
"""ainp_validate.py — AINP v1.0.0 file-family reference validator.

Validates AINP files against the machine-checkable rule sets:

  *.generation.json          G1-G9, G11-G16 (G10 moved to R8 in ainp_report_check.py)
  *.generationfeedback.json  FB1
  *.ainp.json / *_space      SP1, SP2
  ainp/references/reference_manifest.json  P11

Modes (--mode): default | strict | release  (escalation per spec §11).
Version-diff mode (--previous/--current): enables G12; single-file runs emit
AINP_I_G12_REQUIRES_VERSION_DIFF instead.

HONESTY BOUNDARY (spec §10): this validator checks STRUCTURE and DECLARATIONS
only. It outputs "PASS structure-valid" / "WARN external-verification-required".
It NEVER outputs "legally-safe", "rights-verified" or "content-trusted" —
rights/consent/provenance truth, factual accuracy, scanner reliability,
credential validity, provider trust, watermark detectability and human-approval
authenticity are EXTERNAL verification.

SECURITY (spec §8): a plan is UNTRUSTED INPUT. This tool never executes
bindings, never downloads/opens inputs.source URIs, never expands local://,
treats every embedded string as data (not instructions), and only stat()s
binding targets for existence. Generation-space hash recompute is confined to
the space file's directory sandbox. Files larger than MAX_FILE_BYTES are rejected.

Zero-dependency: Python 3.10+ stdlib only.
Exit codes: 0 = no FAIL findings, 1 = at least one FAIL, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

try:
    from .ainp_release_check import validate_against_schema as release_validate_against_schema
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_release_check import validate_against_schema as release_validate_against_schema
    from ainp_public import PublicOutput

# Deterministic UTF-8 output regardless of host console (Windows cp936 pipes).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Term registry (single source of truth — mirrors spec §3 "closed enums")
# ---------------------------------------------------------------------------

REDLINE_TYPES = {"hard", "safety", "ip", "approval", "disclosure", "privacy"}
CONSTRAINT_TYPES = REDLINE_TYPES | {"soft"}
ASSURANCE = {"static", "runtime", "evidence_recorded", "external_required",
             "externally_verified", "attested", "unverifiable"}
STAGE = {"plan_validation", "generation_runtime", "report_check",
         "distribution_gate", "external_review"}
RIGHTS_STATUS = {"owned", "licensed", "public_domain", "open_license",
                 "public_reference", "user_provided", "consent_required",
                 "consent_recorded", "unknown", "external_verify_required"}
PROVENANCE_STATUS = {"unverified", "retrieved", "external_verify_required",
                     "externally_verified"}
DEPLOYMENT_SCOPE = {"internal_draft", "limited", "public", "mass_public"}
RISK_LEVEL = {"low", "medium", "high", "critical"}
STATUS = {"draft", "under_review", "approved", "active", "superseded", "retired"}
ORIGIN = {"human", "agent", "hybrid"}
FEEDBACK_SOURCE = {"human", "agent", "consumer"}
FEEDBACK_TARGET = {"plan", "artifact", "file", "point"}
CONSENT_STATUS = {"not_required", "pending", "recorded", "verified", "expired", "revoked"}
CONSENT_PROCEED = {"recorded", "verified"}
CONSENT_SCOPE = {"single_generation", "project", "time_bounded"}
VERDICT = {"accept", "revise", "reject"}
SEVERITY = {"fail", "warn", "info"}
VERIFICATION_METHOD = {"static", "external", "human"}
EXECUTION_PROTOCOLS = {"AISOP", "AISP", "AIJP", "external", "none"}
MODES = {"default", "strict", "release"}
PUBLIC_OUTPUT = PublicOutput(__file__)

# Suggested (open) enums — unknown values WARN (strict: FAIL), same policy as G3.
ARTIFACT_TYPES_SUGGESTED = {"document", "code", "image", "audio", "video",
                            "dataset", "design", "landing_page", "campaign",
                            "3d", "mixed"}
STRUCTURE_KIND_SUGGESTED = {"section", "subsection", "component", "module",
                            "scene", "asset"}

# Registered static check ids for acceptance_criteria.verification (G5).
CHECK_ID_REGISTRY = {
    "structure.sections_nonempty",
    "inputs.rights_declared",
    "length.within_bounds",
    "disclosure.policy_declared",
}

# G7: keys a plan must never use to self-declare artifact trust (exact match).
SELF_TRUST_KEYS = {"safe", "verified", "original", "trusted", "authentic"}

# Assurances that SATISFY a red-line control point, per mode (spec §5 matrix).
# 'static' satisfies in all modes (fully machine-checked at plan validation),
# but release additionally requires G15's operational trio.
SATISFYING = {
    "default": {"static", "runtime", "evidence_recorded", "externally_verified",
                "external_required"},
    "strict": {"static", "runtime", "evidence_recorded", "externally_verified"},
    "release": {"static", "runtime", "evidence_recorded", "externally_verified"},
}
G15_OPERATIONAL = {"runtime", "evidence_recorded", "externally_verified"}

_SEMVER_NUM = r"(0|[1-9]\d*)"  # SemVer 2.0.0 numeric identifiers: no leading zeros
_SEMVER_PRERELEASE_ID = r"(0|[1-9]\d*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_RE = re.compile(rf"^{_SEMVER_NUM}\.{_SEMVER_NUM}\.{_SEMVER_NUM}"
                       rf"(-{_SEMVER_PRERELEASE_ID}(\.{_SEMVER_PRERELEASE_ID})*)?"
                       r"(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")
MECHANISM_RE = re.compile(r"^(validator|report|runtime|external):.+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCHEME_OR_DRIVE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ARTIFACT_TYPE_SEPARATOR_RE = re.compile(r"[\s_-]+", re.UNICODE)

MAX_FILE_BYTES = 10 * 1024 * 1024  # §8 oversized-input guard
MAX_NESTING_DEPTH = 150            # §8 nesting guard: keeps every traversal recursion-safe
MAX_FINDINGS = 1000                # §8 flood guard: bounds memory on hostile inputs

PROFILE_GENERATION = "ainp.v1.0.0.generation"
PROFILE_FEEDBACK = "ainp.v1.0.0.generationfeedback"
PROFILE_SPACE = "ainp.v1.0.0.generation_space"
PROFILE_REPORT = "ainp.v1.0.0.generationreport"
PROFILE_HIGH_RISK = "ainp.v1.0.0.high_risk_types"
PROFILE_REFERENCE = "ainp.v1.0.0.reference_manifest"


def normalize_high_risk_artifact_type(value: object) -> str | None:
    """Canonicalize high-risk carrier forms without changing free-text policy.

    This normalization is intentionally scoped to matching
    high_risk_types.artifact_types. It closes separator/case spelling variants
    such as "Deepfake", "deep fake", "deep-fake" and "deep_fake" without
    treating arbitrary artifact_type prose as trusted risk classification.
    """
    if not isinstance(value, str):
        return None
    normalized = ARTIFACT_TYPE_SEPARATOR_RE.sub("", value).casefold()
    return normalized or None
REFERENCE_MANIFEST_SCHEMA = "ainp-reference-manifest-v1.0.0.schema.json"
REFERENCE_SOURCE_TYPES = {"local_file", "external_uri"}
REFERENCE_KINDS = {
    "protocol_spec", "schema", "template", "brief", "style_guide",
    "interface_spec", "research_material", "policy", "example", "other",
}

# ---------------------------------------------------------------------------
# Finding machinery
# ---------------------------------------------------------------------------

class Findings:
    def __init__(self) -> None:
        self.items: list[dict] = []
        self._truncated = False

    def add(self, level: str, code: str, rule: str, message: str, path: str = "") -> None:
        assert level in ("fail", "warn", "info")
        if self._truncated:
            return
        if len(self.items) >= MAX_FINDINGS:
            self._truncated = True
            self.items.append({"level": "fail", "code": "AINP_E_FINDINGS_TRUNCATED",
                               "rule": "SEC",
                               "message": f"more than {MAX_FINDINGS} findings; output "
                                          "truncated (untrusted-input flood guard)",
                               "path": path})
            return
        self.items.append({"level": level, "code": code, "rule": rule,
                           "message": message, "path": path})

    def fail(self, code, rule, msg, path=""):
        self.add("fail", code, rule, msg, path)

    def warn(self, code, rule, msg, path=""):
        self.add("warn", code, rule, msg, path)

    def info(self, code, rule, msg, path=""):
        self.add("info", code, rule, msg, path)

    def escalatable(self, mode, code, rule, msg, path=""):
        """WARN in default, FAIL in strict/release (spec §11 escalation)."""
        if mode in ("strict", "release"):
            self.fail(code.replace("AINP_W_", "AINP_E_"), rule, msg, path)
        else:
            self.warn(code, rule, msg, path)

    @property
    def has_fail(self) -> bool:
        return any(i["level"] == "fail" for i in self.items)


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


def _reject_dup_keys(pairs):
    """RFC 8259 interop hazard: parsers disagree on which duplicate wins —
    a smuggling vector when a human reviews one value and a machine acts on the other."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate object key {k!r} (parser-differential smuggling guard)")
        d[k] = v
    return d


def _reject_nonstandard(const):
    raise ValueError(f"non-standard JSON literal {const} (NaN/Infinity) rejected — "
                     "strict parsers would reject this file")


def _depth_exceeds(obj, limit: int) -> bool:
    stack = [(obj, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > limit:
            return True
        if isinstance(node, dict):
            stack.extend((v, depth + 1) for v in node.values())
        elif isinstance(node, list):
            stack.extend((v, depth + 1) for v in node)
    return False


def load_json(path: str, f: Findings):
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            f.fail("AINP_E_FILE_TOO_LARGE", "SEC",
                   f"file exceeds {MAX_FILE_BYTES} bytes (untrusted-input guard)", path)
            return None
        with open(path, encoding="utf-8-sig") as fh:
            doc = json.load(fh, object_pairs_hook=_reject_dup_keys,
                            parse_constant=_reject_nonstandard)
    except (OSError, ValueError, RecursionError) as e:
        # ValueError covers JSONDecodeError + the strictness hooks above;
        # RecursionError covers parser blowup on hostile deep nesting.
        f.fail("AINP_E_UNREADABLE", "IO", f"cannot parse JSON: {e}", path)
        return None
    if _depth_exceeds(doc, MAX_NESTING_DEPTH):
        f.fail("AINP_E_NESTING_TOO_DEEP", "SEC",
               f"nesting exceeds {MAX_NESTING_DEPTH} levels (untrusted-input guard; "
               "all downstream traversal stays recursion-safe below this bound)", path)
        return None
    return doc


def req_list(f: Findings, path: str, val, where: str, rule: str) -> list:
    """Container gate: None -> []; non-array -> ONE controlled FAIL, never iterated
    (a 10MB string iterated per-char would otherwise flood findings — DoS guard)."""
    if val is None:
        return []
    if not isinstance(val, list):
        f.fail("AINP_E_CONTAINER_NOT_ARRAY", rule,
               f"{where} must be an array (got {type(val).__name__})", path)
        return []
    return val


def sha256_of(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def resolve_sandbox_path(base: str, raw: str) -> str | None:
    """Resolve raw under base without allowing absolute, URI, .., symlink, or
    junction escape. Returns a real path inside the sandbox, or None."""
    if os.path.isabs(raw) or SCHEME_OR_DRIVE_RE.match(raw):
        return None
    base_real = os.path.realpath(base)
    target = os.path.realpath(os.path.join(base_real, raw))
    try:
        if os.path.commonpath([base_real, target]) != base_real:
            return None
    except ValueError:
        return None
    return target


def load_high_risk_types(path: str | None, f: Findings) -> dict:
    """Load the versioned high-risk list (single source of truth, spec §7)."""
    if path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "..", "schemas", "high_risk_types.v1.0.0.json")
    doc = load_json(path, f)
    if doc is None:
        # load_json already recorded a FAIL — the whole run is fail-closed.
        f.warn("AINP_W_HIGH_RISK_TYPES_MISSING", "G6",
               "high_risk_types data file unreadable — run is FAIL-closed (see "
               "AINP_E_UNREADABLE); artifact_type/tag gates cannot be evaluated "
               "until the data file is restored", path or "")
        return {"artifact_types": [], "risk_tags": []}
    if not isinstance(doc, dict) or doc.get("schema") != PROFILE_HIGH_RISK:
        f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
               f"high_risk_types data file does not carry profile '{PROFILE_HIGH_RISK}' "
               "— refusing to run with a degraded high-risk gate (fail-closed)", path or "")
        return {"artifact_types": [], "risk_tags": []}
    valid = True
    artifact_types = doc.get("artifact_types")
    if not isinstance(artifact_types, list) or not artifact_types:
        f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
               "high_risk_types.artifact_types must be a non-empty string array "
               "— refusing to run with a degraded high-risk gate (fail-closed)", path or "")
        valid = False
        artifact_types = []
    seen_types: set[str] = set()
    for i, item in enumerate(artifact_types):
        if not isinstance(item, str) or not item.strip():
            f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                   f"high_risk_types.artifact_types[{i}] must be a non-empty string",
                   path or "")
            valid = False
            continue
        norm = normalize_high_risk_artifact_type(item)
        if norm in seen_types:
            f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                   f"duplicate high-risk artifact type after case/separator normalization: {item!r}",
                   path or "")
            valid = False
        if norm is not None:
            seen_types.add(norm)

    risk_tags = doc.get("risk_tags")
    if not isinstance(risk_tags, list) or not risk_tags:
        f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
               "high_risk_types.risk_tags must be a non-empty array — refusing to "
               "run with a degraded high-risk gate (fail-closed)", path or "")
        valid = False
        risk_tags = []
    seen_tags: set[str] = set()
    for i, tag in enumerate(risk_tags):
        if not isinstance(tag, dict):
            f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                   f"high_risk_types.risk_tags[{i}] must be an object", path or "")
            valid = False
            continue
        tag_id = tag.get("id")
        if not isinstance(tag_id, str) or not tag_id:
            f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                   f"high_risk_types.risk_tags[{i}].id must be a non-empty string",
                   path or "")
            valid = False
        elif tag_id in seen_tags:
            f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                   f"duplicate high-risk risk_tag id: {tag_id!r}", path or "")
            valid = False
        else:
            seen_tags.add(tag_id)
        for bit in ("approval_required", "consent_required", "disclosure_required"):
            if not isinstance(tag.get(bit), bool):
                f.fail("AINP_E_HIGH_RISK_TYPES_INVALID", "G6",
                       f"high_risk_types.risk_tags[{i}].{bit} must be boolean",
                       path or "")
                valid = False
    if not valid:
        return {"artifact_types": [], "risk_tags": []}
    return doc


class HighRiskTypesCache:
    def __init__(self, path: str | None, findings: Findings) -> None:
        self.path = path
        self.findings = findings
        self._loaded = False
        self._value: dict | None = None

    def get(self) -> dict:
        if not self._loaded:
            self._value = load_high_risk_types(self.path, self.findings)
            self._loaded = True
        return self._value or {"artifact_types": [], "risk_tags": []}


# ---------------------------------------------------------------------------
# Generation plan rules (G1-G9, G11-G16)
# ---------------------------------------------------------------------------

def _safe_relative_plan_path(raw: str) -> bool:
    if not isinstance(raw, str) or not raw.strip():
        return False
    if os.path.isabs(raw) or SCHEME_OR_DRIVE_RE.match(raw):
        return False
    normalized = raw.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return bool(parts) and ".." not in parts


def validate_content_architecture(g: dict, path: str, f: Findings) -> None:
    """G16: if present, the generated-content project blueprint is machine-bound.

    This is intentionally not an AISOP-style execution graph. It declares
    content roots, files and per-file points so reports/feedback can bind to
    planned content, while execution remains external to AINP. Complete
    <name>_ainp/ project packages require it through P10; standalone plans may
    omit it.
    """
    arch = g.get("content_architecture")
    if arch is None:
        return
    if not isinstance(arch, dict):
        f.fail("AINP_E_G16_CONTENT_ARCHITECTURE_BAD_SHAPE", "G16",
               "generation.content_architecture, when present, must be an object "
               "declaring the generated content root, files and per-file points",
               path)
        return

    root = arch.get("root")
    if not _safe_relative_plan_path(root):
        f.fail("AINP_E_G16_CONTENT_ROOT_INVALID", "G16",
               "content_architecture.root must be a non-empty relative path with "
               "no URI, drive, absolute path or '..' segment", path)

    directory_ids: set[str] = set()
    for i, directory in enumerate(req_list(f, path, arch.get("directories"),
                                           "content_architecture.directories", "G16")):
        if not isinstance(directory, dict):
            f.fail("AINP_E_G16_DIRECTORY_BAD_SHAPE", "G16",
                   f"content_architecture.directories[{i}] must be an object", path)
            continue
        did = directory.get("id")
        if not isinstance(did, str) or not did:
            f.fail("AINP_E_G16_DIRECTORY_MISSING_FIELD", "G16",
                   f"content_architecture.directories[{i}].id is required", path)
        elif did in directory_ids:
            f.fail("AINP_E_G16_DUPLICATE_DIRECTORY_ID", "G16",
                   f"duplicate content directory id {did!r}", path)
        else:
            directory_ids.add(did)
        if not _safe_relative_plan_path(directory.get("path")):
            f.fail("AINP_E_G16_DIRECTORY_PATH_INVALID", "G16",
                   f"content_architecture.directories[{i}].path must be a safe "
                   "relative path", path)
        if not isinstance(directory.get("purpose"), str) or not directory.get("purpose"):
            f.fail("AINP_E_G16_DIRECTORY_MISSING_FIELD", "G16",
                   f"content_architecture.directories[{i}].purpose is required", path)

    files = arch.get("files")
    if not isinstance(files, list) or not files:
        f.fail("AINP_E_G16_FILES_MISSING", "G16",
               "content_architecture.files must be a non-empty array", path)
        return

    acceptance_ids = {
        c.get("id") for c in req_list(f, path, g.get("acceptance_criteria"),
                                      "generation.acceptance_criteria", "G16")
        if isinstance(c, dict) and isinstance(c.get("id"), str)
    }
    file_ids: set[str] = set()
    for i, content_file in enumerate(files):
        if not isinstance(content_file, dict):
            f.fail("AINP_E_G16_FILE_BAD_SHAPE", "G16",
                   f"content_architecture.files[{i}] must be an object", path)
            continue
        fid = content_file.get("id")
        if not isinstance(fid, str) or not fid:
            f.fail("AINP_E_G16_FILE_MISSING_FIELD", "G16",
                   f"content_architecture.files[{i}].id is required", path)
        elif fid in file_ids:
            f.fail("AINP_E_G16_DUPLICATE_FILE_ID", "G16",
                   f"duplicate content file id {fid!r}", path)
        else:
            file_ids.add(fid)
        for field in ("type", "summary"):
            if not isinstance(content_file.get(field), str) or not content_file.get(field):
                f.fail("AINP_E_G16_FILE_MISSING_FIELD", "G16",
                       f"content_architecture.files[{i}].{field} is required", path)
        if not isinstance(content_file.get("required"), bool):
            f.fail("AINP_E_G16_FILE_MISSING_FIELD", "G16",
                   f"content_architecture.files[{i}].required must be boolean", path)
        if not _safe_relative_plan_path(content_file.get("path")):
            f.fail("AINP_E_G16_FILE_PATH_INVALID", "G16",
                   f"content_architecture.files[{i}].path must be a safe relative path", path)

        points = content_file.get("points")
        if not isinstance(points, list) or not points:
            f.fail("AINP_E_G16_REQUIRED_FILE_NO_POINTS", "G16",
                   f"content_architecture.files[{i}].points must be a non-empty array", path)
            continue
        point_ids: set[str] = set()
        point_orders: set[int] = set()
        for j, point in enumerate(points):
            if not isinstance(point, dict):
                f.fail("AINP_E_G16_POINT_BAD_SHAPE", "G16",
                       f"content_architecture.files[{i}].points[{j}] must be an object", path)
                continue
            pid = point.get("id")
            if not isinstance(pid, str) or not pid:
                f.fail("AINP_E_G16_POINT_MISSING_FIELD", "G16",
                       f"content_architecture.files[{i}].points[{j}].id is required", path)
            elif pid in point_ids:
                f.fail("AINP_E_G16_DUPLICATE_POINT_ID", "G16",
                       f"duplicate point id {pid!r} in content file {fid!r}", path)
            else:
                point_ids.add(pid)
            order = point.get("order")
            if not isinstance(order, int) or order < 1:
                f.fail("AINP_E_G16_POINT_MISSING_FIELD", "G16",
                       f"content_architecture.files[{i}].points[{j}].order must be "
                       "a positive integer", path)
            elif order in point_orders:
                f.fail("AINP_E_G16_DUPLICATE_POINT_ORDER", "G16",
                       f"duplicate point order {order!r} in content file {fid!r}", path)
            else:
                point_orders.add(order)
            if not isinstance(point.get("title"), str) or not point.get("title"):
                f.fail("AINP_E_G16_POINT_MISSING_FIELD", "G16",
                       f"content_architecture.files[{i}].points[{j}].title is required", path)
            requirements = point.get("requirements")
            if not isinstance(requirements, list) or not requirements or not all(
                    isinstance(item, str) and item for item in requirements):
                f.fail("AINP_E_G16_POINT_REQUIREMENTS_INVALID", "G16",
                       f"content_architecture.files[{i}].points[{j}].requirements "
                       "must be a non-empty string array", path)
            for ref in req_list(f, path, point.get("acceptance_refs"),
                                f"content_architecture.files[{i}].points[{j}].acceptance_refs",
                                "G16"):
                if ref not in acceptance_ids:
                    f.fail("AINP_E_G16_ACCEPTANCE_REF_UNKNOWN", "G16",
                           f"content point {pid!r} references unknown acceptance "
                           f"criterion {ref!r}", path)

def validate_generation(doc: dict, path: str, mode: str, hrt: dict, f: Findings) -> None:
    # G1 — profile <-> payload key strong binding
    if doc.get("schema") != PROFILE_GENERATION or "generation" not in doc:
        f.fail("AINP_E_G1_PROFILE_KEY_MISMATCH", "G1",
               f"schema must be '{PROFILE_GENERATION}' with payload key 'generation' "
               f"(got schema={doc.get('schema')!r}, keys={sorted(set(doc) - {'schema'})})", path)
        return
    g = doc["generation"]
    if not isinstance(g, dict):
        f.fail("AINP_E_G1_PAYLOAD_NOT_OBJECT", "G1", "'generation' must be an object", path)
        return

    # G2 — required fields + closed-enum formats
    required = ["id", "version", "title", "summary", "status", "artifact_type",
                "brief", "acceptance_criteria", "governance"]
    for k in required:
        if k not in g or g[k] in (None, "", []):
            f.fail("AINP_E_G2_MISSING_FIELD", "G2", f"required field missing/empty: generation.{k}", path)
    ver = g.get("version")
    if isinstance(ver, str) and not SEMVER_RE.match(ver):
        f.fail("AINP_E_G2_VERSION_NOT_SEMVER", "G2",
               f"generation.version must be semver MAJOR.MINOR.PATCH (got {ver!r})", path)
    if g.get("status") is not None and g.get("status") not in STATUS:
        f.fail("AINP_E_G2_BAD_STATUS", "G2",
               f"generation.status must be one of {sorted(STATUS)} (got {g.get('status')!r})", path)
    if g.get("source") is not None and g.get("source") not in ORIGIN:
        f.fail("AINP_E_G2_BAD_SOURCE", "G2",
               f"generation.source must be one of {sorted(ORIGIN)} (got {g.get('source')!r})", path)
    if isinstance(g.get("acceptance_criteria"), list) and not g["acceptance_criteria"]:
        f.fail("AINP_E_G2_EMPTY_ACCEPTANCE", "G2",
               "acceptance_criteria must be a non-empty array (a plan without "
               "acceptance criteria has no machine-checkable notion of 'done')", path)

    # G3 — artifact_type declared; suggested enum advisory.
    # High-risk membership is separator-normalized (§7): spelling variants such
    # as "Deepfake", "deepfake ", "deep fake", "deep-fake" and "deep_fake"
    # must not slip past the sovereignty gate.
    at = g.get("artifact_type")
    hrt_types_norm = {norm for norm in
                      (normalize_high_risk_artifact_type(t)
                       for t in hrt.get("artifact_types", []))
                      if norm is not None}
    at_norm = normalize_high_risk_artifact_type(at)
    if isinstance(at, str) and at and at not in ARTIFACT_TYPES_SUGGESTED \
            and at_norm not in hrt_types_norm:
        f.escalatable(mode, "AINP_W_G3_UNLISTED_ARTIFACT_TYPE", "G3",
                      f"artifact_type {at!r} not in suggested enum "
                      f"{sorted(ARTIFACT_TYPES_SUGGESTED)} nor high_risk_types", path)

    # structure kinds (suggested enum, same policy as G3)
    for i, node in enumerate(req_list(f, path, g.get("structure"), "generation.structure", "G3")):
        kind = node.get("kind") if isinstance(node, dict) else None
        if kind and kind not in STRUCTURE_KIND_SUGGESTED:
            f.escalatable(mode, "AINP_W_G3_UNLISTED_STRUCTURE_KIND", "G3",
                          f"structure[{i}].kind {kind!r} not in suggested enum", path)

    # ---- risk profile / tag matching (needed by G4/G6/G8 mappings) ----
    rp = g.get("risk_profile")
    tag_index = {t.get("id"): t for t in hrt.get("risk_tags", []) if isinstance(t, dict)}
    matched_tags: list[dict] = []
    if not isinstance(rp, dict):
        f.fail("AINP_E_G6_MISSING_RISK_PROFILE", "G6", "risk_profile is required", path)
        rp = {}
    else:
        if rp.get("risk_level") not in RISK_LEVEL:
            f.fail("AINP_E_G6_BAD_RISK_LEVEL", "G6",
                   f"risk_profile.risk_level must be one of {sorted(RISK_LEVEL)}", path)
        if rp.get("deployment_scope") not in DEPLOYMENT_SCOPE:
            f.fail("AINP_E_G6_BAD_DEPLOYMENT_SCOPE", "G6",
                   f"risk_profile.deployment_scope must be one of {sorted(DEPLOYMENT_SCOPE)}", path)
        for tag in req_list(f, path, rp.get("risk_tags"), "risk_profile.risk_tags", "G6"):
            if tag in tag_index:
                matched_tags.append(tag_index[tag])
            else:
                f.fail("AINP_E_G6_UNKNOWN_RISK_TAG", "G6",
                       f"risk_tag {tag!r} not in high_risk_types.risk_tags "
                       "(closed value domain, single source of truth)", path)

    governance = g.get("governance") if isinstance(g.get("governance"), dict) else {}

    # G4 — inputs: source/rights.status/provenance.status; consent discipline
    any_consent_required = False
    inputs_list = req_list(f, path, g.get("inputs"), "generation.inputs", "G4")
    for i, inp in enumerate(inputs_list):
        if not isinstance(inp, dict):
            f.fail("AINP_E_G4_BAD_INPUT", "G4", f"inputs[{i}] must be an object", path)
            continue
        if not inp.get("source"):
            f.fail("AINP_E_G4_MISSING_SOURCE", "G4", f"inputs[{i}].source is required", path)
        rs = (inp.get("rights") or {}).get("status")
        if rs not in RIGHTS_STATUS:
            f.fail("AINP_E_G4_BAD_RIGHTS_STATUS", "G4",
                   f"inputs[{i}].rights.status must be one of {sorted(RIGHTS_STATUS)} (got {rs!r})", path)
        ps = (inp.get("provenance") or {}).get("status")
        if ps not in PROVENANCE_STATUS:
            f.fail("AINP_E_G4_BAD_PROVENANCE_STATUS", "G4",
                   f"inputs[{i}].provenance.status must be one of {sorted(PROVENANCE_STATUS)} (got {ps!r})", path)
        consent = inp.get("consent")
        if isinstance(consent, dict):
            if consent.get("required") is True:
                any_consent_required = True
                if not consent.get("evidence_ref"):
                    f.fail("AINP_E_G4_CONSENT_NO_EVIDENCE", "G4",
                           f"inputs[{i}].consent.required=true but evidence_ref missing", path)
                cs = consent.get("status")
                if cs not in CONSENT_PROCEED:
                    f.fail("AINP_E_G4_CONSENT_STATUS_BLOCKS", "G4",
                           f"inputs[{i}].consent.status={cs!r} does not permit generation "
                           f"(must be one of {sorted(CONSENT_PROCEED)})", path)
            elif consent.get("status") is not None and consent.get("status") not in CONSENT_STATUS:
                f.fail("AINP_E_G4_BAD_CONSENT_STATUS", "G4",
                       f"inputs[{i}].consent.status must be one of {sorted(CONSENT_STATUS)}", path)
            if consent.get("scope") is not None and consent.get("scope") not in CONSENT_SCOPE:
                f.fail("AINP_E_G4_BAD_CONSENT_SCOPE", "G4",
                       f"inputs[{i}].consent.scope must be one of {sorted(CONSENT_SCOPE)}", path)
        # rights-status path: consent_required on an input demands a consent record on it
        if rs == "consent_required" and not (isinstance(consent, dict) and consent.get("required") is True):
            f.fail("AINP_E_G4_RIGHTS_CONSENT_NO_RECORD", "G4",
                   f"inputs[{i}].rights.status=consent_required but the input carries no "
                   "consent object with required=true — declaring that consent is needed "
                   "without recording it is never permission to proceed", path)
    # tag trigger mapping: consent_required -> at least one consent-bearing input (spec §7)
    if any(t.get("consent_required") for t in matched_tags) and not any_consent_required:
        f.fail("AINP_E_G4_CONSENT_REQUIRED_BY_TAG", "G4",
               "a matched risk_tag declares consent_required=true but no inputs[] "
               "carries consent.required=true", path)
    # NOTE (honesty boundary): this proves consent is DECLARED with evidence refs,
    # not that consent is real/valid — external/registry/human verification only.

    # G5 — acceptance criteria shape + check_id registry
    for i, ac in enumerate(req_list(f, path, g.get("acceptance_criteria"),
                                    "generation.acceptance_criteria", "G5")):
        if not isinstance(ac, dict):
            f.fail("AINP_E_G5_BAD_CRITERION", "G5", f"acceptance_criteria[{i}] must be an object", path)
            continue
        for k in ("id", "description", "severity", "verification"):
            if not ac.get(k):
                f.fail("AINP_E_G5_MISSING_FIELD", "G5",
                       f"acceptance_criteria[{i}].{k} is required", path)
        if ac.get("severity") is not None and ac.get("severity") not in SEVERITY:
            f.fail("AINP_E_G5_BAD_SEVERITY", "G5",
                   f"acceptance_criteria[{i}].severity must be one of {sorted(SEVERITY)}", path)
        v = ac.get("verification")
        if isinstance(v, dict):
            m = v.get("method")
            if m not in VERIFICATION_METHOD:
                f.fail("AINP_E_G5_BAD_METHOD", "G5",
                       f"acceptance_criteria[{i}].verification.method must be one of "
                       f"{sorted(VERIFICATION_METHOD)} (got {m!r})", path)
            if m == "static":
                cid = v.get("check_id")
                if not cid:
                    f.fail("AINP_E_G5_MISSING_CHECK_ID", "G5",
                           f"acceptance_criteria[{i}]: method=static requires check_id", path)
                elif cid not in CHECK_ID_REGISTRY:
                    f.escalatable(mode, "AINP_W_G5_UNKNOWN_CHECK_ID", "G5",
                                  f"acceptance_criteria[{i}].check_id {cid!r} not in registered set "
                                  f"{sorted(CHECK_ID_REGISTRY)}", path)

    # G16 — generated-content architecture is a first-class plan component.
    validate_content_architecture(g, path, f)

    # G6 — high-risk gate (type ∪ tags ∪ scope ∪ risk_level) + tag approval bits.
    # Type membership uses the separator-normalized form computed at G3.
    high_risk = (
        (at_norm is not None and at_norm in hrt_types_norm)
        or bool(rp.get("risk_tags"))
        or rp.get("deployment_scope") == "mass_public"
        or rp.get("risk_level") in ("high", "critical")
        or any(t.get("approval_required") for t in matched_tags)
    )
    if high_risk and governance.get("approval_required") is not True:
        f.fail("AINP_E_G6_MISSING_APPROVAL", "G6",
               "high-risk plan (artifact_type ∈ high_risk_types [case/separator-normalized] "
               "∪ risk_tags nonempty ∪ deployment_scope=mass_public ∪ risk_level ∈ "
               "{high, critical}) requires governance.approval_required=true "
               "(HSAW human sovereignty gate)", path)

    # G7 — no self-declared artifact trust
    def scan_trust(node, ptr):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in SELF_TRUST_KEYS:
                    f.fail("AINP_E_G7_SELF_TRUST_CLAIM", "G7",
                           f"plan self-declares artifact trust at {ptr}/{k} — trust marks "
                           "(safe/verified/original/trusted/authentic) may only be assigned "
                           "by consumers/registries/reviewers, never by the plan", path)
                scan_trust(v, f"{ptr}/{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan_trust(v, f"{ptr}[{i}]")
    scan_trust(g, "generation")

    # G8 — disclosure_policy universally required + tag disclosure bits
    dp = g.get("disclosure_policy")
    if not isinstance(dp, dict) or "ai_generated_disclosure_required" not in dp:
        f.fail("AINP_E_G8_MISSING_DISCLOSURE_POLICY", "G8",
               "every plan must declare disclosure_policy (with "
               "ai_generated_disclosure_required) — the policy declares the stance; "
               "switches may legitimately be false for non-human-facing artifacts", path)
    elif any(t.get("disclosure_required") for t in matched_tags) \
            and dp.get("ai_generated_disclosure_required") is not True:
        f.fail("AINP_E_G8_DISCLOSURE_REQUIRED_BY_TAG", "G8",
               "a matched risk_tag declares disclosure_required=true, so "
               "disclosure_policy.ai_generated_disclosure_required must be true", path)

    # G9 — bindings structure + target existence (stat only, never open/execute)
    b = g.get("bindings")
    if b is not None:
        if not isinstance(b, dict):
            f.fail("AINP_E_G9_BAD_BINDINGS", "G9", "bindings must be an object", path)
        else:
            eb = b.get("execution_binding")
            if isinstance(eb, dict):
                if eb.get("protocol") not in EXECUTION_PROTOCOLS:
                    f.fail("AINP_E_G9_BAD_EXECUTION_PROTOCOL", "G9",
                           f"execution_binding.protocol must be one of {sorted(EXECUTION_PROTOCOLS)}", path)
            base = os.path.dirname(os.path.abspath(path))
            for key, field in (("aijp_binding", "target"), ("execution_binding", "target"),
                               ("aikp_binding", "focus")):
                bind = b.get(key)
                if isinstance(bind, dict) and isinstance(bind.get(field), str):
                    if bind.get("protocol") in ("external", "none"):
                        continue
                    target = bind[field]
                    if "://" in target:  # URI targets: existence is external verification
                        continue
                    if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                        f.escalatable(mode, "AINP_W_G9_BINDING_TARGET_MISSING", "G9",
                                      f"bindings.{key}.{field} does not resolve locally: {target!r} "
                                      "(candidate path only — never auto-executed)", path)

    # G11/G14/G15 — red-line constraints: enforced_by control points + assurance
    for i, c in enumerate(req_list(f, path, g.get("constraints"),
                                   "generation.constraints", "G11")):
        if not isinstance(c, dict):
            f.fail("AINP_E_G11_BAD_CONSTRAINT", "G11", f"constraints[{i}] must be an object", path)
            continue
        ctype = c.get("type")
        if ctype not in CONSTRAINT_TYPES:
            f.fail("AINP_E_G11_BAD_TYPE", "G11",
                   f"constraints[{i}].type must be one of {sorted(CONSTRAINT_TYPES)} (got {ctype!r})", path)
            continue
        if ctype not in REDLINE_TYPES:
            continue  # soft constraints: schema-legal, no enforcement gates
        eb = c.get("enforced_by")
        if not isinstance(eb, list) or not eb:
            f.fail("AINP_E_G11_ENFORCED_BY_MISSING", "G11",
                   f"red-line constraint {c.get('id', i)!r} (type={ctype}) requires a "
                   "non-empty enforced_by[] control-point array", path)
            continue
        assurances = []
        for j, cp in enumerate(eb):
            if not isinstance(cp, dict):
                f.fail("AINP_E_G11_BAD_CONTROL_POINT", "G11",
                       f"constraints[{i}].enforced_by[{j}] must be an object", path)
                continue
            if cp.get("stage") not in STAGE:
                f.fail("AINP_E_G11_BAD_STAGE", "G11",
                       f"constraints[{i}].enforced_by[{j}].stage must be one of {sorted(STAGE)}", path)
            if cp.get("assurance") not in ASSURANCE:
                f.fail("AINP_E_G11_BAD_ASSURANCE", "G11",
                       f"constraints[{i}].enforced_by[{j}].assurance must be one of {sorted(ASSURANCE)}", path)
            else:
                assurances.append(cp["assurance"])
            mech = cp.get("mechanism")
            if not (isinstance(mech, str) and MECHANISM_RE.match(mech)):
                f.fail("AINP_E_G11_BAD_MECHANISM", "G11",
                       f"constraints[{i}].enforced_by[{j}].mechanism must match "
                       "'validator:|report:|runtime:|external:<ref>'", path)
        satisfied = any(a in SATISFYING[mode] for a in assurances)
        # G14 — unverifiable must not carry a red line
        if "unverifiable" in assurances and not satisfied:
            msg = (f"red-line constraint {c.get('id', i)!r} relies on assurance=unverifiable "
                   "with no satisfying control point — honest record, not a pass credential")
            if mode == "default":
                f.warn("AINP_W_G14_UNVERIFIABLE_REDLINE", "G14", msg, path)
            else:
                f.fail("AINP_E_G14_UNVERIFIABLE_REDLINE", "G14", msg, path)
        elif not satisfied and assurances:
            # e.g. attested-only / external_required-only in strict
            f.warn("AINP_W_G14_NO_SATISFYING_CONTROL", "G14",
                   f"red-line constraint {c.get('id', i)!r} has no control point whose "
                   f"assurance satisfies mode={mode} (found: {sorted(set(assurances))})", path)
        # G15 — release: at least one operational control point per red line
        if mode == "release" and not any(a in G15_OPERATIONAL for a in assurances):
            f.fail("AINP_E_G15_NO_OPERATIONAL_CONTROL", "G15",
                   f"release mode: red-line constraint {c.get('id', i)!r} must have at least "
                   f"one control point with assurance ∈ {sorted(G15_OPERATIONAL)}", path)
        # condition is declarative text in v1.0.0: existence-only, never evaluated
        if "condition" in c and not isinstance(c.get("condition"), str):
            f.fail("AINP_E_G11_BAD_CONDITION", "G11",
                   f"constraints[{i}].condition must be a string (declarative text; "
                   "v1.0.0 validators check existence only, never evaluate)", path)

    # G13 — governance.risk_level is DERIVED; must match risk_profile
    grl = governance.get("risk_level")
    if grl is not None and rp.get("risk_level") is not None and grl != rp.get("risk_level"):
        f.fail("AINP_E_G13_RISK_LEVEL_CONFLICT", "G13",
               f"governance.risk_level ({grl!r}) conflicts with risk_profile.risk_level "
               f"({rp.get('risk_level')!r}) — risk_profile is the single source of truth", path)

    # External-verification honesty summary
    ext_needed = [i for i, inp in enumerate(inputs_list)
                  if isinstance(inp, dict)
                  and ((inp.get("provenance") or {}).get("status") == "external_verify_required"
                       or (inp.get("rights") or {}).get("status") in
                       ("external_verify_required", "unknown", "consent_required"))]
    if ext_needed:
        f.warn("AINP_W_EXTERNAL_VERIFICATION_REQUIRED", "BOUNDARY",
               f"inputs {ext_needed} declare rights/provenance that only external "
               "verification can prove — structure-valid ≠ rights-verified", path)


# ---------------------------------------------------------------------------
# G12 — version-diff mode
# ---------------------------------------------------------------------------

def _redlines(g: dict):
    return sorted((json.dumps(c, sort_keys=True, ensure_ascii=False)
                   for c in (g.get("constraints") or [])
                   if isinstance(c, dict) and c.get("type") in REDLINE_TYPES))


def validate_version_diff(prev_doc: dict, cur_doc: dict, prev_path: str,
                          cur_path: str, mode: str, f: Findings) -> None:
    pg = prev_doc.get("generation")
    cg = cur_doc.get("generation")
    pg = pg if isinstance(pg, dict) else {}   # non-dict payloads already FAILed G1;
    cg = cg if isinstance(cg, dict) else {}   # diff proceeds fail-closed vs empty
    ac_changed = (json.dumps(pg.get("acceptance_criteria"), sort_keys=True, ensure_ascii=False)
                  != json.dumps(cg.get("acceptance_criteria"), sort_keys=True, ensure_ascii=False))
    rl_changed = _redlines(pg) != _redlines(cg)
    if not (ac_changed or rl_changed):
        f.info("AINP_I_G12_NO_BREAKING_CHANGE", "G12",
               "no acceptance_criteria / red-line constraint changes detected", cur_path)
        return
    pv, cv = str(pg.get("version", "")), str(cg.get("version", ""))
    try:
        p_major = int(pv.split(".")[0])
        c_major = int(cv.split(".")[0])
        major_bumped = c_major > p_major
    except (ValueError, IndexError):
        major_bumped = False
    what = " and ".join(x for x, y in
                        (("acceptance_criteria", ac_changed), ("red-line constraints", rl_changed)) if y)
    if not major_bumped:
        msg = (f"{what} changed between {os.path.basename(prev_path)} (v{pv}) and "
               f"{os.path.basename(cur_path)} (v{cv}) — the 'what counts as done' predicate "
               "flipped, which REQUIRES a MAJOR version bump (spec §4)")
        if mode == "default":
            f.warn("AINP_W_G12_BREAKING_CHANGE_NOT_MAJOR", "G12", msg, cur_path)
        else:
            f.fail("AINP_E_G12_BREAKING_CHANGE_NOT_MAJOR", "G12", msg, cur_path)
    else:
        f.info("AINP_I_G12_MAJOR_BUMP_OK", "G12",
               f"{what} changed and version was MAJOR-bumped ({pv} -> {cv})", cur_path)


# ---------------------------------------------------------------------------
# FB1 / SP1 / SP2
# ---------------------------------------------------------------------------

def validate_feedback(doc: dict, path: str, mode: str, f: Findings) -> None:
    if doc.get("schema") != PROFILE_FEEDBACK or "generationfeedback" not in doc:
        f.fail("AINP_E_FB1_PROFILE_KEY_MISMATCH", "FB1",
               f"schema must be '{PROFILE_FEEDBACK}' with payload key 'generationfeedback'", path)
        return
    fb = doc["generationfeedback"]
    if not isinstance(fb, dict):
        f.fail("AINP_E_FB1_PAYLOAD_NOT_OBJECT", "FB1",
               "'generationfeedback' must be an object", path)
        return
    for k in ("generation_id", "source", "verdict"):
        if not fb.get(k):
            f.fail("AINP_E_FB1_MISSING_FIELD", "FB1", f"generationfeedback.{k} is required", path)
    if fb.get("source") is not None and fb.get("source") not in FEEDBACK_SOURCE:
        f.fail("AINP_E_FB1_BAD_SOURCE", "FB1",
               f"source must be one of {sorted(FEEDBACK_SOURCE)}", path)
    if fb.get("verdict") is not None and fb.get("verdict") not in VERDICT:
        f.fail("AINP_E_FB1_BAD_VERDICT", "FB1",
               f"verdict must be one of {sorted(VERDICT)}", path)
    for i, issue in enumerate(req_list(f, path, fb.get("issues"),
                                       "generationfeedback.issues", "FB1")):
        if not isinstance(issue, dict):
            f.fail("AINP_E_FB1_BAD_ISSUE", "FB1",
                   f"issues[{i}] must be an object", path)
            continue
        if issue.get("target") is not None and issue.get("target") not in FEEDBACK_TARGET:
            f.fail("AINP_E_FB1_BAD_TARGET", "FB1",
                   f"issues[{i}].target must be one of {sorted(FEEDBACK_TARGET)}", path)
        if issue.get("severity") is not None and issue.get("severity") not in SEVERITY:
            f.fail("AINP_E_FB1_BAD_SEVERITY", "FB1",
                   f"issues[{i}].severity must be one of {sorted(SEVERITY)}", path)
        if issue.get("target") == "file" and not issue.get("file_id"):
            f.fail("AINP_E_FB1_FILE_TARGET_MISSING_FILE_ID", "FB1",
                   f"issues[{i}] target=file requires file_id", path)
        if issue.get("target") == "point" and (not issue.get("file_id") or not issue.get("point_id")):
            f.fail("AINP_E_FB1_POINT_TARGET_INCOMPLETE", "FB1",
                   f"issues[{i}] target=point requires both file_id and point_id", path)


def validate_space(doc: dict, path: str, mode: str, f: Findings) -> None:
    if doc.get("schema") != PROFILE_SPACE or "generation_space" not in doc:
        f.fail("AINP_E_SP1_PROFILE_KEY_MISMATCH", "SP1",
               f"schema must be '{PROFILE_SPACE}' with payload key 'generation_space'", path)
        return
    sp = doc["generation_space"]
    if not isinstance(sp, dict):
        f.fail("AINP_E_SP1_PAYLOAD_NOT_OBJECT", "SP1",
               "'generation_space' must be an object", path)
        return
    base = os.path.dirname(os.path.abspath(path))
    for i, entry in enumerate(req_list(f, path, sp.get("generations"),
                                       "generation_space.generations", "SP1")):
        if not isinstance(entry, dict):
            f.fail("AINP_E_SP1_BAD_ENTRY", "SP1", f"generations[{i}] must be an object", path)
            continue
        # SP1 — ref + sha256 required
        for k in ("ref", "sha256"):
            if not entry.get(k):
                f.fail("AINP_E_SP1_MISSING_FIELD", "SP1", f"generations[{i}].{k} is required", path)
        sha = entry.get("sha256")
        if isinstance(sha, str) and sha and not SHA256_RE.match(sha):
            f.fail("AINP_E_SP1_BAD_SHA256", "SP1",
                   f"generations[{i}].sha256 must be 64 lowercase hex chars", path)
            continue
        # SP2 — recompute (registration-time integrity only; consumers must re-hash)
        ref = entry.get("ref")
        if isinstance(ref, str) and ref and isinstance(sha, str) and SHA256_RE.match(sha or ""):
            if "://" in ref:
                f.info("AINP_I_SP2_REF_EXTERNAL", "SP2",
                       f"generations[{i}].ref {ref!r} is external; local hash "
                       "recompute is not attempted", path)
                continue
            target = resolve_sandbox_path(base, ref)
            if target is None:
                f.fail("AINP_E_SP2_PATH_ESCAPES", "SP2",
                       f"generations[{i}].ref {ref!r} is absolute or escapes the "
                       "generation-space sandbox — refusing to read it", path)
                continue
            if not os.path.exists(target):
                f.info("AINP_I_SP2_REF_UNRESOLVED", "SP2",
                       f"generations[{i}].ref {ref!r} not resolvable from space file "
                       "(hash cannot be recomputed here)", path)
            else:
                actual = sha256_of(target)
                if actual and actual != sha:
                    f.escalatable(mode, "AINP_W_SP2_HASH_MISMATCH", "SP2",
                                  f"generations[{i}].sha256 does not match recomputed hash of "
                                  f"{ref!r} — space hash only proves registration-time integrity", path)


def infer_reference_project_root(path: str) -> str | None:
    """Infer <name>_ainp/ from <name>_ainp/ainp/references/reference_manifest.json."""
    references_dir = os.path.dirname(os.path.abspath(path))
    ainp_dir = os.path.dirname(references_dir)
    project_root = os.path.dirname(ainp_dir)
    if os.path.basename(references_dir) != "references":
        return None
    if os.path.basename(ainp_dir) != "ainp":
        return None
    return project_root


def path_inside(base: str, path: str) -> bool:
    base_real = os.path.realpath(base)
    path_real = os.path.realpath(path)
    try:
        return os.path.commonpath([base_real, path_real]) == base_real
    except ValueError:
        return False


def validate_reference_manifest_schema(path: str, f: Findings) -> None:
    raw_findings: list[dict] = []
    release_validate_against_schema(
        path, REFERENCE_MANIFEST_SCHEMA, raw_findings, "reference manifest",
    )
    code_map = {
        "AINP_E_RELEASE_SCHEMA_UNREADABLE": "AINP_E_P11_SCHEMA_UNREADABLE",
        "AINP_E_RELEASE_JSON_UNREADABLE": "AINP_E_P11_MANIFEST_UNREADABLE",
        "AINP_E_RELEASE_SCHEMA_INVALID": "AINP_E_P11_SCHEMA_INVALID",
    }
    for item in raw_findings:
        level = item.get("level")
        code = code_map.get(item.get("code"), "AINP_E_P11_SCHEMA_INVALID")
        message = str(item.get("message", "reference manifest schema check failed"))
        if level == "fail":
            f.fail(code, "P11", message, path)
        elif level == "warn":
            f.warn(code.replace("AINP_E_", "AINP_W_", 1), "P11", message, path)
        elif level == "info":
            f.info(code.replace("AINP_E_", "AINP_I_", 1), "P11", message, path)


def validate_reference_manifest(doc: dict, path: str, mode: str, f: Findings) -> None:
    validate_reference_manifest_schema(path, f)
    if doc.get("schema") != PROFILE_REFERENCE or "reference_manifest" not in doc:
        f.fail("AINP_E_P11_PROFILE_KEY_MISMATCH", "P11",
               f"schema must be '{PROFILE_REFERENCE}' with payload key 'reference_manifest'", path)
        return
    manifest = doc["reference_manifest"]
    if not isinstance(manifest, dict):
        f.fail("AINP_E_P11_PAYLOAD_NOT_OBJECT", "P11",
               "'reference_manifest' must be an object", path)
        return
    for k in ("id", "title", "references"):
        if not manifest.get(k):
            f.fail("AINP_E_P11_MISSING_FIELD", "P11",
                   f"reference_manifest.{k} is required", path)

    references = req_list(f, path, manifest.get("references"),
                          "reference_manifest.references", "P11")
    project_root = infer_reference_project_root(path)
    references_dir = (
        os.path.realpath(os.path.join(project_root, "ainp", "references"))
        if project_root else None
    )
    seen_ids: set[str] = set()
    for i, item in enumerate(references):
        if not isinstance(item, dict):
            f.fail("AINP_E_P11_BAD_REFERENCE", "P11",
                   f"references[{i}] must be an object", path)
            continue
        ref_id = item.get("id")
        if not isinstance(ref_id, str) or not ref_id:
            f.fail("AINP_E_P11_MISSING_REFERENCE_ID", "P11",
                   f"references[{i}].id is required", path)
        elif ref_id in seen_ids:
            f.fail("AINP_E_P11_DUPLICATE_REFERENCE_ID", "P11",
                   f"references[{i}].id {ref_id!r} is duplicated", path)
        else:
            seen_ids.add(ref_id)

        kind = item.get("kind")
        if kind not in REFERENCE_KINDS:
            f.fail("AINP_E_P11_BAD_REFERENCE_KIND", "P11",
                   f"references[{i}].kind must be one of {sorted(REFERENCE_KINDS)}", path)
        for k in ("purpose", "trust_boundary"):
            if not item.get(k):
                f.fail("AINP_E_P11_MISSING_FIELD", "P11",
                       f"references[{i}].{k} is required", path)

        source = item.get("source")
        if not isinstance(source, dict):
            f.fail("AINP_E_P11_BAD_SOURCE", "P11",
                   f"references[{i}].source must be an object", path)
            continue
        source_type = source.get("type")
        if source_type not in REFERENCE_SOURCE_TYPES:
            f.fail("AINP_E_P11_BAD_SOURCE_TYPE", "P11",
                   f"references[{i}].source.type must be one of {sorted(REFERENCE_SOURCE_TYPES)}", path)
            continue

        sha = item.get("sha256")
        if isinstance(sha, str) and sha and not SHA256_RE.match(sha):
            f.fail("AINP_E_P11_BAD_SHA256", "P11",
                   f"references[{i}].sha256 must be 64 lowercase hex chars when present", path)
            continue
        if source_type == "external_uri":
            if source.get("path"):
                f.fail("AINP_E_P11_EXTERNAL_REFERENCE_PATH_INVALID", "P11",
                       f"references[{i}].source.type=external_uri must use source.uri, not source.path", path)
            if sha:
                f.fail("AINP_E_P11_EXTERNAL_REFERENCE_HASH_UNVERIFIABLE", "P11",
                       f"references[{i}].sha256 is only allowed for local_file references; "
                       "local tools do not fetch external_uri entries", path)
            if not source.get("uri"):
                f.fail("AINP_E_P11_EXTERNAL_REFERENCE_URI_MISSING", "P11",
                       f"references[{i}].source.type=external_uri requires source.uri", path)
            else:
                f.info("AINP_I_P11_EXTERNAL_REFERENCE_NOT_FETCHED", "P11",
                       f"references[{i}] is external; local tools do not fetch or verify it", path)
            continue

        raw = source.get("path")
        if source.get("uri"):
            f.fail("AINP_E_P11_LOCAL_REFERENCE_URI_INVALID", "P11",
                   f"references[{i}].source.type=local_file must use source.path; "
                   "use source_url for external origin hints", path)
        if not isinstance(raw, str) or not raw:
            f.fail("AINP_E_P11_LOCAL_REFERENCE_PATH_INVALID", "P11",
                   f"references[{i}].source.path is required for local_file references", path)
            continue
        if project_root is None or references_dir is None:
            f.warn("AINP_W_P11_PROJECT_ROOT_UNINFERRED", "P11",
                   "reference_manifest is not located under ainp/references/; "
                   "local reference hash recompute is skipped", path)
            continue
        target = resolve_sandbox_path(project_root, raw)
        if target is None:
            f.fail("AINP_E_P11_LOCAL_REFERENCE_PATH_INVALID", "P11",
                   f"references[{i}].source.path must be a safe project-root relative path: {raw!r}", path)
            continue
        if not path_inside(references_dir, target):
            f.fail("AINP_E_P11_LOCAL_REFERENCE_OUTSIDE_REFERENCES_DIR", "P11",
                   f"references[{i}].source.path must live under ainp/references/ (got {raw!r})", path)
            continue
        if not os.path.exists(target):
            f.fail("AINP_E_P11_LOCAL_REFERENCE_MISSING", "P11",
                   f"local reference/template file does not exist: {raw!r}", path)
            continue
        if not isinstance(sha, str) or not sha:
            f.warn("AINP_W_P11_LOCAL_REFERENCE_HASH_MISSING", "P11",
                   f"local reference/template {raw!r} has no sha256 integrity anchor", path)
            continue
        actual = sha256_of(target)
        if actual and actual != sha:
            f.fail("AINP_E_P11_REFERENCE_HASH_MISMATCH", "P11",
                   f"local reference/template {raw!r} sha256 does not match current file", path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def detect_and_validate(path: str, mode: str, hrt: HighRiskTypesCache, f: Findings) -> None:
    doc = load_json(path, f)
    if doc is None:
        return
    if not isinstance(doc, dict):
        f.fail("AINP_E_NOT_OBJECT", "IO", "top level must be a JSON object", path)
        return
    profile = doc.get("schema", "")
    if profile == PROFILE_GENERATION or "generation" in doc:
        validate_generation(doc, path, mode, hrt.get(), f)
        if profile == PROFILE_GENERATION:
            f.info("AINP_I_G12_REQUIRES_VERSION_DIFF", "G12",
                   "G12 (breaking-change-needs-MAJOR) only runs in version-diff mode "
                   "(--previous/--current)", path)
    elif profile == PROFILE_FEEDBACK or "generationfeedback" in doc:
        validate_feedback(doc, path, mode, f)
    elif profile == PROFILE_SPACE or "generation_space" in doc:
        validate_space(doc, path, mode, f)
    elif profile == PROFILE_REFERENCE or "reference_manifest" in doc:
        validate_reference_manifest(doc, path, mode, f)
    elif profile == PROFILE_REPORT or "generationreport" in doc:
        f.info("AINP_I_USE_REPORT_CHECK", "R", "reports are validated by ainp_report_check.py", path)
    else:
        f.fail("AINP_E_UNKNOWN_PROFILE", "G1",
               f"unrecognized schema profile {profile!r}", path)


def render(f: Findings, as_json: bool) -> None:
    items = public_findings(f.items)
    if as_json:
        print(json.dumps({"findings": items,
                          "summary": {"fail": sum(1 for i in items if i["level"] == "fail"),
                                      "warn": sum(1 for i in items if i["level"] == "warn"),
                                      "info": sum(1 for i in items if i["level"] == "info")}},
                         ensure_ascii=False, indent=2))
        return
    for i in items:
        print(f"[{i['level'].upper():4}] {i['code']} ({i['rule']}) {i['path']}: {i['message']}")
    fails = sum(1 for i in items if i["level"] == "fail")
    warns = sum(1 for i in items if i["level"] == "warn")
    if fails:
        print(f"RESULT: FAIL ({fails} fail, {warns} warn)")
    elif warns:
        print(f"RESULT: PASS structure-valid, WARN external-verification-required "
              f"({warns} warn)")
    else:
        print("RESULT: PASS structure-valid")
    print("NOTE: structure-valid ≠ artifact safe/original/compliant/conformant. "
          "Rights, consent, provenance, facts and approvals require external verification.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AINP v1.0.0 file-family reference validator")
    ap.add_argument("files", nargs="*",
                    help="*.generation.json / *.generationfeedback.json / *.ainp.json / reference_manifest.json")
    ap.add_argument("--mode", choices=sorted(MODES), default="default")
    ap.add_argument("--high-risk-types", default=None,
                    help="path to high_risk_types.v1.0.0.json (default: ../schemas/ relative to this tool)")
    ap.add_argument("--previous", help="G12 version-diff mode: previous plan")
    ap.add_argument("--current", help="G12 version-diff mode: current plan")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    f = Findings()
    hrt = HighRiskTypesCache(args.high_risk_types, f)
    register_input_path(args.high_risk_types)
    register_input_path(args.previous)
    register_input_path(args.current)
    for path in args.files:
        register_input_path(path)

    if bool(args.previous) != bool(args.current):
        print("--previous and --current must be given together", file=sys.stderr)
        return 2
    if args.previous and args.current:
        prev, cur = load_json(args.previous, f), load_json(args.current, f)
        for p_, d_ in ((args.previous, prev), (args.current, cur)):
            if d_ is not None and not isinstance(d_, dict):
                f.fail("AINP_E_NOT_OBJECT", "IO", "top level must be a JSON object", p_)
        if isinstance(prev, dict) and isinstance(cur, dict):
            validate_generation(cur, args.current, args.mode, hrt.get(), f)
            validate_version_diff(prev, cur, args.previous, args.current, args.mode, f)
    elif not args.files:
        ap.print_usage()
        return 2

    for path in args.files:
        detect_and_validate(path, args.mode, hrt, f)

    render(f, args.as_json)
    return 1 if f.has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
