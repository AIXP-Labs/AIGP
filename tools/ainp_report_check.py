#!/usr/bin/env python3
"""ainp_report_check.py — AINP v1.0.0 reference checker (report-side rules R1-R10).

Checks a *.generationreport.json against its plan:

  R1  profile <-> payload key strong binding
  R2  generation_id resolves to the plan
  R3  artifacts[] each carry id/path/mime/sha256
  R4  acceptance_results[] correspond 1:1 to the plan's acceptance_criteria[]
  R5  every result carries method/evidence/verifier/limitations (+ passed)
  R6  overall.conformant is DERIVABLE from results + gates (never self-set)
  R7  every required disclosure policy switch has report-side evidence recorded
  R8  plan_ref.sha256 matches the CURRENT plan file, or an archived plan blob
      findable by hash; neither -> the report cannot serve as evidence for the
      current plan (it may remain a historical record of an older plan)
  R9  if the plan requires human approval, the report records approval evidence
  R10 required generation.content_architecture files are covered by report
      artifacts via file_id, and file_id/path bindings match the plan

Modes: default | strict | release. In release mode artifacts must exist and
their sha256 must recompute (delivery-evidence completeness).

HONESTY BOUNDARY: a report is an EVIDENCE CONTAINER, not absolute truth.
Tool verifiers only prove what the tool actually checked; human/external
entries record identity/source/version/time. Content credentials, generator
metadata and watermarks are evidence records only; this checker does not
validate provider trust, C2PA signatures or watermark detectability. It proves
report STRUCTURE and plan<->report CONSISTENCY — nothing more.

Zero-dependency: Python 3.10+ stdlib only.
Exit codes: 0 = no FAIL, 1 = FAIL present, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput

# Deterministic UTF-8 output regardless of host console (Windows cp936 pipes).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROFILE_REPORT = "ainp.v1.0.0.generationreport"
PROFILE_GENERATION = "ainp.v1.0.0.generation"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCHEME_OR_DRIVE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
MODES = {"default", "strict", "release"}
VERIFICATION_METHOD = {"static", "external", "human"}
VERIFIER_TYPES = {"tool", "human", "external"}
CONTENT_CREDENTIAL_STATUS = {"external_verify_required", "externally_verified", "unverified"}
GENERATOR_METADATA_REQUIRED = ("provider", "system", "content_id", "generated_at")
WATERMARK_REQUIRED_FIELDS = ("present", "scheme")
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_NESTING_DEPTH = 150   # §8 nesting guard (mirrors ainp_validate.py)
MAX_FINDINGS = 1000       # §8 flood guard
PUBLIC_OUTPUT = PublicOutput(__file__)


class Findings:
    def __init__(self) -> None:
        self.items: list[dict] = []
        self._truncated = False

    def add(self, level, code, rule, message, path=""):
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

    @property
    def has_fail(self):
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
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate object key {k!r} (parser-differential smuggling guard)")
        d[k] = v
    return d


def _reject_nonstandard(const):
    raise ValueError(f"non-standard JSON literal {const} (NaN/Infinity) rejected — "
                     "strict parsers would reject this file")


def _depth_exceeds(obj, limit):
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


def load_json(path, f):
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            f.fail("AINP_E_FILE_TOO_LARGE", "SEC",
                   f"file exceeds {MAX_FILE_BYTES} bytes (untrusted-input guard)", path)
            return None
        with open(path, encoding="utf-8-sig") as fh:
            doc = json.load(fh, object_pairs_hook=_reject_dup_keys,
                            parse_constant=_reject_nonstandard)
    except (OSError, ValueError, RecursionError) as e:
        f.fail("AINP_E_UNREADABLE", "IO", f"cannot parse JSON: {e}", path)
        return None
    if _depth_exceeds(doc, MAX_NESTING_DEPTH):
        f.fail("AINP_E_NESTING_TOO_DEEP", "SEC",
               f"nesting exceeds {MAX_NESTING_DEPTH} levels (untrusted-input guard)", path)
        return None
    return doc


def sha256_of(path):
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


def _evidence_ok(evidence, f: Findings, report_path: str, where: str,
                 rule: str = "R5",
                 no_evidence_code: str = "AINP_E_R5_NO_EVIDENCE",
                 bad_evidence_code: str = "AINP_E_R5_BAD_EVIDENCE") -> bool:
    if not isinstance(evidence, list) or not evidence:
        f.fail(no_evidence_code, rule,
               f"{where}.evidence[] must be a non-empty array", report_path)
        return False
    ok = True
    for i, ev in enumerate(evidence):
        if not isinstance(ev, dict):
            f.fail(bad_evidence_code, rule,
                   f"{where}.evidence[{i}] must be an object", report_path)
            ok = False
            continue
        for k in ("type", "summary"):
            if not ev.get(k):
                f.fail(bad_evidence_code, rule,
                       f"{where}.evidence[{i}].{k} is required", report_path)
                ok = False
    return ok


def _verifier_ok(verifier, f: Findings, report_path: str, where: str,
                 rule: str = "R5",
                 bad_verifier_code: str = "AINP_E_R5_BAD_VERIFIER") -> bool:
    if not isinstance(verifier, dict):
        f.fail(bad_verifier_code, rule,
               f"{where}.verifier must be an object with type/name", report_path)
        return False
    ok = True
    if verifier.get("type") not in VERIFIER_TYPES:
        f.fail(bad_verifier_code, rule,
               f"{where}.verifier.type must be one of {sorted(VERIFIER_TYPES)}",
               report_path)
        ok = False
    if not verifier.get("name"):
        f.fail(bad_verifier_code, rule,
               f"{where}.verifier.name is required", report_path)
        ok = False
    return ok


def disclosure_gate_ok(plan: dict, report: dict, disclosure, f: Findings, report_path: str) -> bool:
    """R7 gate: every true disclosure_policy switch must be recorded as satisfied."""
    dp = plan.get("disclosure_policy") or {}
    required = {
        "ai_generated_disclosure_required": "ai_generated",
        "human_visible_label_required": "human_visible_label_present",
        "machine_readable_metadata_required": "machine_readable_metadata_present",
    }
    ok = True
    for policy_key, report_key in required.items():
        if dp.get(policy_key) is True:
            if not isinstance(disclosure, dict) or disclosure.get(report_key) is not True:
                f.fail("AINP_E_R7_DISCLOSURE_NOT_RECORDED", "R7",
                       f"plan requires {policy_key}=true but report.disclosure."
                       f"{report_key} is not recorded true", report_path)
                ok = False
    if dp.get("generator_metadata_required") is True:
        generator = report.get("generator") if isinstance(report, dict) else None
        missing = []
        if not isinstance(generator, dict):
            missing = list(GENERATOR_METADATA_REQUIRED)
        else:
            for key in GENERATOR_METADATA_REQUIRED:
                if not (isinstance(generator.get(key), str) and generator.get(key)):
                    missing.append(key)
        if missing:
            f.fail("AINP_E_R7_GENERATOR_METADATA_NOT_RECORDED", "R7",
                   "plan requires generator_metadata_required=true but report.generator "
                   f"does not record required fields: {', '.join(missing)}", report_path)
            ok = False
    if dp.get("watermark_required") is True:
        watermarks = disclosure.get("watermarks") if isinstance(disclosure, dict) else None
        has_present = isinstance(watermarks, list) and any(
            isinstance(wm, dict)
            and wm.get("present") is True
            and isinstance(wm.get("scheme"), str)
            and bool(wm.get("scheme"))
            for wm in watermarks
        )
        if not has_present:
            f.fail("AINP_E_R7_WATERMARK_NOT_RECORDED", "R7",
                   "plan requires watermark_required=true but report.disclosure."
                   "watermarks[] does not record a present watermark with a scheme",
                   report_path)
            ok = False
    if dp.get("content_credential_required") is True:
        cc = disclosure.get("content_credential") if isinstance(disclosure, dict) else None
        if not isinstance(cc, dict) or cc.get("present") is not True:
            f.fail("AINP_E_R7_CONTENT_CREDENTIAL_NOT_RECORDED", "R7",
                   "plan requires content_credential_required=true but the report "
                   "does not record a present content credential", report_path)
            ok = False
        elif cc.get("verification_status") != "externally_verified":
            f.fail("AINP_E_R7_CONTENT_CREDENTIAL_NOT_VERIFIED", "R7",
                   "content credentials satisfy R7 only when external verification is "
                   "recorded; report.disclosure.content_credential."
                   "verification_status must be 'externally_verified'", report_path)
            ok = False
    return ok


def approval_gate_ok(plan: dict, report: dict, f: Findings, report_path: str) -> bool:
    """R9 gate: approval_required=true must have its own report-side evidence."""
    governance = plan.get("governance") if isinstance(plan.get("governance"), dict) else {}
    if governance.get("approval_required") is not True:
        return True
    gr = report.get("governance_results") if isinstance(report.get("governance_results"), dict) else {}
    gate = gr.get("approval_gate") if isinstance(gr.get("approval_gate"), dict) else None
    if gate is None:
        f.fail("AINP_E_R9_APPROVAL_NOT_RECORDED", "R9",
               "plan.governance.approval_required=true but report.governance_results."
               "approval_gate is missing — plan approval and artifact acceptance are "
               "separate status chains", report_path)
        return False
    ok = True
    if gate.get("required") is not True:
        f.fail("AINP_E_R9_APPROVAL_NOT_RECORDED", "R9",
               "approval_gate.required must be true when the plan requires approval",
               report_path)
        ok = False
    if gate.get("passed") is not True:
        f.fail("AINP_E_R9_APPROVAL_NOT_PASSED", "R9",
               "approval_gate.passed must be true for a conformant approved-delivery "
               "report", report_path)
        ok = False
    if gate.get("method") not in ("human", "external"):
        f.fail("AINP_E_R9_APPROVAL_BAD_METHOD", "R9",
               "approval_gate.method must be 'human' or 'external'", report_path)
        ok = False
    if not gate.get("limitations"):
        f.fail("AINP_E_R9_APPROVAL_MISSING_FIELD", "R9",
               "approval_gate.limitations is required", report_path)
        ok = False
    ok = _evidence_ok(gate.get("evidence"), f, report_path,
                      "governance_results.approval_gate",
                      "R9", "AINP_E_R9_APPROVAL_MISSING_FIELD",
                      "AINP_E_R9_APPROVAL_BAD_EVIDENCE") and ok
    ok = _verifier_ok(gate.get("verifier"), f, report_path,
                      "governance_results.approval_gate",
                      "R9", "AINP_E_R9_APPROVAL_BAD_VERIFIER") and ok
    return ok


def content_files_by_id(plan: dict) -> dict:
    arch = plan.get("content_architecture") if isinstance(plan, dict) else None
    files = arch.get("files") if isinstance(arch, dict) else None
    if not isinstance(files, list):
        return {}
    out = {}
    for item in files:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]:
            out[item["id"]] = item
    return out


def check_content_artifact_coverage(plan: dict | None, artifacts: list,
                                    f: Findings, report_path: str) -> None:
    """R10: report artifacts bind back to the plan's content architecture.

    Hashes prove integrity only; this rule proves artifact coverage and
    reference consistency for the declared content files.
    """
    if plan is None:
        return
    files_by_id = content_files_by_id(plan)
    if not files_by_id:
        return

    covered: set[str] = set()
    for i, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            continue
        file_id = artifact.get("file_id")
        if file_id is None:
            continue
        if file_id not in files_by_id:
            f.fail("AINP_E_R10_UNKNOWN_FILE_ID", "R10",
                   f"artifacts[{i}].file_id {file_id!r} does not exist in "
                   "plan.content_architecture.files", report_path)
            continue
        declared = files_by_id[file_id]
        if artifact.get("path") != declared.get("path"):
            f.fail("AINP_E_R10_FILE_PATH_MISMATCH", "R10",
                   f"artifacts[{i}] file_id {file_id!r} path {artifact.get('path')!r} "
                   f"does not match plan content path {declared.get('path')!r}",
                   report_path)
        covered.add(file_id)

    for file_id, declared in sorted(files_by_id.items()):
        if declared.get("required") is True and file_id not in covered:
            f.fail("AINP_E_R10_REQUIRED_FILE_MISSING_ARTIFACT", "R10",
                   f"required content file {file_id!r} is not covered by any "
                   "generationreport.artifacts[].file_id", report_path)


def check_report(report_path: str, plan_path: str | None, archive_dirs: list[str],
                 mode: str, f: Findings, artifact_root: str | None = None) -> None:
    doc = load_json(report_path, f)
    if doc is None:
        return

    # R1 — binding
    if doc.get("schema") != PROFILE_REPORT or "generationreport" not in doc:
        f.fail("AINP_E_R1_PROFILE_KEY_MISMATCH", "R1",
               f"schema must be '{PROFILE_REPORT}' with payload key 'generationreport'", report_path)
        return
    r = doc["generationreport"]
    if not isinstance(r, dict):
        f.fail("AINP_E_R1_PAYLOAD_NOT_OBJECT", "R1",
               "'generationreport' must be an object", report_path)
        return
    base = os.path.dirname(os.path.abspath(report_path))
    artifact_base = os.path.abspath(artifact_root) if artifact_root else base
    if artifact_root and mode == "release" and not os.path.isdir(artifact_base):
        f.fail("AINP_E_R3_ARTIFACT_ROOT_MISSING", "R3",
               f"release mode: artifact_root {artifact_root!r} must be an existing "
               "directory", report_path)

    # resolve plan: --plan wins; else plan_ref.path relative to report dir
    plan_ref = r.get("plan_ref") if isinstance(r.get("plan_ref"), dict) else {}
    if plan_path is None and isinstance(plan_ref.get("path"), str):
        plan_path = os.path.normpath(os.path.join(base, plan_ref["path"]))
    plan = None
    if plan_path and os.path.exists(plan_path):
        plan_doc = load_json(plan_path, f)
        if isinstance(plan_doc, dict) and isinstance(plan_doc.get("generation"), dict):
            plan = plan_doc["generation"]
    if plan is None:
        f.fail("AINP_E_R2_PLAN_UNRESOLVED", "R2",
               f"cannot resolve the plan (looked at {plan_path!r}); R2/R4/R7/R8 need it", report_path)

    # R2 — generation_id points to the plan
    if plan is not None and r.get("generation_id") != plan.get("id"):
        f.fail("AINP_E_R2_ID_MISMATCH", "R2",
               f"report.generation_id ({r.get('generation_id')!r}) != plan.id ({plan.get('id')!r})",
               report_path)

    # R3 — artifacts
    artifacts = r.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        f.fail("AINP_E_R3_NO_ARTIFACTS", "R3", "artifacts[] must be a non-empty array", report_path)
        artifacts = []
    for i, a in enumerate(artifacts):
        if not isinstance(a, dict):
            f.fail("AINP_E_R3_BAD_ARTIFACT", "R3", f"artifacts[{i}] must be an object", report_path)
            continue
        for k in ("id", "path", "mime", "sha256"):
            if not a.get(k):
                f.fail("AINP_E_R3_MISSING_FIELD", "R3", f"artifacts[{i}].{k} is required", report_path)
        sha = a.get("sha256")
        if isinstance(sha, str) and sha and not SHA256_RE.match(sha):
            f.fail("AINP_E_R3_BAD_SHA256", "R3",
                   f"artifacts[{i}].sha256 must be 64 lowercase hex chars", report_path)
        elif mode == "release" and isinstance(a.get("path"), str):
            raw = a["path"]
            target = resolve_sandbox_path(artifact_base, raw)
            if target is None:
                # §8: the report is untrusted input — never read files it points
                # outside its artifact sandbox (the report dir by default; project
                # root only when a project checker passes --artifact-root). Use
                # realpath/commonpath so symlinks/junctions cannot smuggle reads
                # outside the sandbox.
                f.fail("AINP_E_R3_PATH_ESCAPES", "R3",
                       f"release mode: artifacts[{i}].path {raw!r} is absolute or escapes "
                       "the artifact sandbox — refusing to read it", report_path)
            elif not os.path.exists(target):
                f.fail("AINP_E_R3_ARTIFACT_MISSING_RELEASE", "R3",
                       f"release mode: artifacts[{i}].path {a['path']!r} must exist "
                       "(delivery evidence must be recomputable)", report_path)
            else:
                actual = sha256_of(target)
                if actual and actual != sha:
                    f.fail("AINP_E_R3_ARTIFACT_HASH_MISMATCH_RELEASE", "R3",
                           f"release mode: artifacts[{i}].sha256 does not recompute", report_path)

    # R10 — report artifacts cover the plan's declared content architecture.
    check_content_artifact_coverage(plan, artifacts, f, report_path)

    # R4 — 1:1 correspondence with plan acceptance_criteria
    results = r.get("acceptance_results")
    if not isinstance(results, list):
        f.fail("AINP_E_R4_NO_RESULTS", "R4", "acceptance_results[] is required", report_path)
        results = []
    if plan is not None:
        plan_ids = [c.get("id") for c in (plan.get("acceptance_criteria") or [])
                    if isinstance(c, dict)]
        result_ids = [x.get("criterion") for x in results if isinstance(x, dict)]
        for cid in plan_ids:
            if cid not in result_ids:
                f.fail("AINP_E_R4_MISSING_RESULT", "R4",
                       f"plan criterion {cid!r} has no acceptance_result", report_path)
        for rid in result_ids:
            if rid not in plan_ids:
                f.fail("AINP_E_R4_ORPHAN_RESULT", "R4",
                       f"acceptance_result references unknown criterion {rid!r}", report_path)
        seen: set = set()
        for rid in result_ids:
            if rid in seen:
                f.fail("AINP_E_R4_DUPLICATE_RESULT", "R4",
                       f"criterion {rid!r} has multiple acceptance_results — 1:1 "
                       "correspondence is violated and the authoritative result is "
                       "undefined", report_path)
            seen.add(rid)

    # R5 — evidence discipline per result
    for i, x in enumerate(results):
        if not isinstance(x, dict):
            f.fail("AINP_E_R5_BAD_RESULT", "R5", f"acceptance_results[{i}] must be an object", report_path)
            continue
        if not isinstance(x.get("passed"), bool):
            f.fail("AINP_E_R5_MISSING_PASSED", "R5",
                   f"acceptance_results[{i}].passed (boolean) is required", report_path)
        for k in ("method", "verifier", "limitations"):
            if not x.get(k):
                f.fail("AINP_E_R5_MISSING_FIELD", "R5",
                       f"acceptance_results[{i}].{k} is required "
                       "('we checked' without method/verifier/limitations is not evidence)", report_path)
        if x.get("method") is not None and x.get("method") not in VERIFICATION_METHOD:
            f.fail("AINP_E_R5_BAD_METHOD", "R5",
                   f"acceptance_results[{i}].method must be one of "
                   f"{sorted(VERIFICATION_METHOD)}", report_path)
        _evidence_ok(x.get("evidence"), f, report_path, f"acceptance_results[{i}]")
        _verifier_ok(x.get("verifier"), f, report_path, f"acceptance_results[{i}]")

    # R6 — conformant must be derivable (fail-level criteria all passed + gates)
    overall = r.get("overall") if isinstance(r.get("overall"), dict) else {}
    disclosure = r.get("disclosure") if isinstance(r.get("disclosure"), dict) else None
    disclosure_ok = approval_ok = True
    if plan is not None:
        disclosure_ok = disclosure_gate_ok(plan, r, disclosure, f, report_path)
        approval_ok = approval_gate_ok(plan, r, f, report_path)
    if plan is not None and not isinstance(overall.get("conformant"), bool):
        f.fail("AINP_E_R6_MISSING_OVERALL", "R6",
               "overall.conformant (boolean) is required — omitting it would silently "
               "evade the R6 derivation (the schema requires it too)", report_path)
    if plan is not None and isinstance(overall.get("conformant"), bool):
        sev = {c.get("id"): c.get("severity", "fail")
               for c in (plan.get("acceptance_criteria") or []) if isinstance(c, dict)}
        fail_ok = all(x.get("passed") is True
                      for x in results if isinstance(x, dict)
                      and sev.get(x.get("criterion"), "fail") == "fail")
        gates_ok = disclosure_ok and approval_ok
        derived = fail_ok and gates_ok
        if overall["conformant"] != derived:
            f.fail("AINP_E_R6_CONFORMANT_NOT_DERIVABLE", "R6",
                   f"overall.conformant={overall['conformant']} but derivation from "
                   f"fail-level results ({fail_ok}) and mandatory gates ({gates_ok}) "
                   f"yields {derived} — conformant may never be self-set", report_path)
        warn_failed = [x.get("criterion") for x in results if isinstance(x, dict)
                       and x.get("passed") is False
                       and sev.get(x.get("criterion")) == "warn"]
        listed = overall.get("warnings")
        if not isinstance(listed, list):   # a string here would substring-match and
            listed = []                    # silently swallow the warning

        for w in warn_failed:
            if w not in listed:
                f.warn("AINP_W_R6_WARN_NOT_LISTED", "R6",
                       f"warn-level criterion {w!r} failed but is not in overall.warnings", report_path)

    # R8 — plan_ref hash lock (current plan, else archived blob, else FAIL)
    ref_sha = plan_ref.get("sha256")
    if not (isinstance(ref_sha, str) and SHA256_RE.match(ref_sha or "")):
        f.fail("AINP_E_R8_BAD_PLAN_REF", "R8",
               "plan_ref.sha256 (64 lowercase hex) is required", report_path)
    elif plan_path and os.path.exists(plan_path):
        actual = sha256_of(plan_path)
        if actual == ref_sha:
            f.info("AINP_I_R8_PLAN_REF_MATCHES", "R8",
                   "plan_ref.sha256 matches the current plan file", report_path)
        else:
            found = None
            for d in archive_dirs:
                if not d or not os.path.isdir(d):
                    continue
                for name in sorted(os.listdir(d)):
                    p = os.path.join(d, name)
                    if os.path.isfile(p) and sha256_of(p) == ref_sha:
                        found = p
                        break
                if found:
                    break
            if found:
                f.warn("AINP_W_R8_REPORT_FOR_ARCHIVED_PLAN", "R8",
                       f"plan_ref.sha256 matches archived blob {found!r}, not the current "
                       "plan — this report is a historical record of the OLD plan and "
                       "CANNOT serve as acceptance evidence for the current plan", report_path)
            else:
                f.fail("AINP_E_R8_PLAN_REF_MISMATCH", "R8",
                       "plan_ref.sha256 matches neither the current plan file nor any "
                       "archived plan blob — acceptance is void for the current plan and "
                       "must be re-run (never silently carried over)", report_path)


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
    print(f"RESULT: {'FAIL' if fails else 'PASS structure-valid'} ({fails} fail, {warns} warn)")
    print("NOTE: a report is an evidence container, not absolute truth; this checker "
          "proves structure, required gate records, and plan<->report consistency only. "
          "It does not prove provider trust or watermark detectability.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AINP v1.0.0 report checker (R1-R10)")
    ap.add_argument("report", help="*.generationreport.json")
    ap.add_argument("--plan", default=None, help="plan path (default: resolve plan_ref.path)")
    ap.add_argument("--archive", action="append", default=[],
                    help="archived-plan blob dir(s) for R8 (repeatable)")
    ap.add_argument("--artifact-root", default=None,
                    help="artifact sandbox root for release hash recompute "
                         "(default: report directory; project checkers pass project root)")
    ap.add_argument("--mode", choices=sorted(MODES), default="default")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    f = Findings()
    register_input_path(args.report)
    register_input_path(args.plan)
    add_public_base(args.artifact_root)
    for archive in args.archive:
        add_public_base(archive)
    base = os.path.dirname(os.path.abspath(args.report))
    archive_dirs = list(args.archive) + [os.path.join(base, "archive")]
    check_report(args.report, args.plan, archive_dirs, args.mode, f, args.artifact_root)
    render(f, args.as_json)
    return 1 if f.has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
