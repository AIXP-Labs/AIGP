#!/usr/bin/env python3
"""ainp_rehash.py - refresh project-local AINP integrity hashes.

This is a creation/editing helper, not a validator and not a trust proof. It
recomputes only package-local integrity hashes that are intentionally checked by
the reference validators:

  * generationreport.plan_ref.sha256
  * generationreport.artifacts[].sha256
  * generation_space.generations[].sha256 for local refs
  * reference_manifest.references[].sha256 for local references/templates

Run the normal validation/release gates after using this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass

try:
    from .ainp_public import PublicOutput
except ImportError:  # script execution from tools/
    from ainp_public import PublicOutput

SCHEME_OR_DRIVE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
PUBLIC_OUTPUT = PublicOutput(__file__)


@dataclass
class Update:
    file: str
    field: str
    old: str | None
    new: str


def _inside(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([os.path.realpath(base), os.path.realpath(path)]) == os.path.realpath(base)
    except ValueError:
        return False


def display_path(path: str, project_root: str) -> str:
    PUBLIC_OUTPUT.add_base(project_root)
    return PUBLIC_OUTPUT.display_path(path)


def sanitize_text(text: str, project_root: str) -> str:
    PUBLIC_OUTPUT.add_base(project_root)
    return PUBLIC_OUTPUT.sanitize_text(text)


def public_update(update: Update, project_root: str) -> dict:
    data = update.__dict__.copy()
    data["file"] = display_path(update.file, project_root)
    return data


def reject_duplicate_keys(pairs):
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


def load_json(path: str):
    with open(path, encoding="utf-8-sig") as fh:
        return json.loads(
            fh.read(),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_constant,
        )


def write_json(path: str, doc) -> None:
    directory = os.path.dirname(os.path.abspath(path)) or "."
    prefix = f".{os.path.basename(path)}."
    original_mode: int | None = None
    try:
        original_mode = os.stat(path).st_mode & 0o777
    except OSError:
        pass
    fd, tmp_path = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        if original_mode is not None:
            os.chmod(tmp_path, original_mode)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("AINP.md must start with --- frontmatter")
    try:
        close = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValueError("AINP.md frontmatter closing --- is missing") from exc
    data: dict[str, str] = {}
    for raw in lines[1:close]:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"frontmatter line is not key: value: {raw!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"duplicate AINP.md frontmatter key: {key!r}")
        data[key] = strip_quotes(value)
    return data


def resolve_under(base: str, rel: str, label: str) -> str:
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"{label} must be a non-empty relative path")
    if os.path.isabs(rel) or SCHEME_OR_DRIVE_RE.match(rel):
        raise ValueError(f"{label} must not be absolute, URI-like, or drive-relative: {rel!r}")
    base_real = os.path.realpath(base)
    target = os.path.realpath(os.path.join(base_real, rel))
    try:
        inside = os.path.commonpath([base_real, target]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise ValueError(f"{label} escapes its sandbox: {rel!r}")
    return target


def path_inside(base: str, path: str) -> bool:
    base_real = os.path.realpath(base)
    path_real = os.path.realpath(path)
    try:
        return os.path.commonpath([base_real, path_real]) == base_real
    except ValueError:
        return False


def set_hash(updates: list[Update], file_path: str, field: str, obj: dict, new_hash: str) -> None:
    old = obj.get("sha256")
    if old != new_hash:
        obj["sha256"] = new_hash
        updates.append(Update(file_path, field, old if isinstance(old, str) else None, new_hash))


def scan_report(project_root: str, report_path: str, plan_path: str,
                content_dir_path: str | None) -> tuple[dict, list[Update]]:
    doc = load_json(report_path)
    report = doc.get("generationreport")
    if not isinstance(report, dict):
        raise ValueError(f"{report_path}: missing generationreport object")
    updates: list[Update] = []

    plan_ref = report.get("plan_ref")
    if not isinstance(plan_ref, dict):
        raise ValueError(f"{report_path}: generationreport.plan_ref must be an object")
    set_hash(updates, report_path, "generationreport.plan_ref.sha256", plan_ref, sha256_file(plan_path))

    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"{report_path}: generationreport.artifacts must be an array")
    for i, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ValueError(f"{report_path}: artifacts[{i}] must be an object")
        raw = artifact.get("path")
        target = resolve_under(project_root, raw, f"artifacts[{i}].path")
        if not os.path.isfile(target):
            raise ValueError(f"{report_path}: artifact file does not exist: {raw!r}")
        if content_dir_path and not path_inside(content_dir_path, target):
            raise ValueError(
                f"{report_path}: artifacts[{i}].path must live under "
                f"AINP.md.content_dir before hashes are refreshed: {raw!r}"
            )
        set_hash(updates, report_path, f"generationreport.artifacts[{i}].sha256", artifact, sha256_file(target))
    return doc, updates


def scan_space(space_path: str) -> tuple[dict, list[Update]]:
    doc = load_json(space_path)
    space = doc.get("generation_space")
    if not isinstance(space, dict):
        raise ValueError(f"{space_path}: missing generation_space object")
    generations = space.get("generations")
    if not isinstance(generations, list):
        raise ValueError(f"{space_path}: generation_space.generations must be an array")

    updates: list[Update] = []
    base = os.path.dirname(space_path)
    for i, item in enumerate(generations):
        if not isinstance(item, dict):
            raise ValueError(f"{space_path}: generations[{i}] must be an object")
        ref = item.get("ref")
        if not isinstance(ref, str) or "://" in ref:
            continue
        target = resolve_under(base, ref, f"generations[{i}].ref")
        if not os.path.isfile(target):
            continue
        set_hash(updates, space_path, f"generation_space.generations[{i}].sha256", item, sha256_file(target))
    return doc, updates


def scan_reference_manifest(project_root: str, manifest_path: str) -> tuple[dict, list[Update]]:
    doc = load_json(manifest_path)
    manifest = doc.get("reference_manifest")
    if not isinstance(manifest, dict):
        raise ValueError(f"{manifest_path}: missing reference_manifest object")
    references = manifest.get("references")
    if not isinstance(references, list):
        raise ValueError(f"{manifest_path}: reference_manifest.references must be an array")

    references_dir = os.path.realpath(os.path.join(project_root, "ainp", "references"))
    updates: list[Update] = []
    for i, item in enumerate(references):
        if not isinstance(item, dict):
            raise ValueError(f"{manifest_path}: references[{i}] must be an object")
        source = item.get("source")
        if not isinstance(source, dict):
            raise ValueError(f"{manifest_path}: references[{i}].source must be an object")
        source_type = source.get("type")
        if source_type == "external_uri":
            if source.get("path"):
                raise ValueError(
                    f"{manifest_path}: references[{i}].source.type=external_uri "
                    "must use source.uri, not source.path"
                )
            if item.get("sha256"):
                raise ValueError(
                    f"{manifest_path}: references[{i}].sha256 is only allowed for "
                    "local_file references; local tools do not fetch external_uri entries"
                )
            if not source.get("uri"):
                raise ValueError(
                    f"{manifest_path}: references[{i}].source.type=external_uri "
                    "requires source.uri"
                )
            continue
        if source_type != "local_file":
            raise ValueError(
                f"{manifest_path}: references[{i}].source.type must be "
                "local_file or external_uri"
            )
        if source.get("uri"):
            raise ValueError(
                f"{manifest_path}: references[{i}].source.type=local_file must use "
                "source.path; use source_url for external origin hints"
            )
        raw = source.get("path")
        target = resolve_under(project_root, raw, f"references[{i}].source.path")
        if not path_inside(references_dir, target):
            raise ValueError(
                f"{manifest_path}: references[{i}].source.path must live under "
                f"ainp/references/: {raw!r}"
            )
        if not os.path.isfile(target):
            raise ValueError(f"{manifest_path}: local reference/template file does not exist: {raw!r}")
        set_hash(updates, manifest_path, f"reference_manifest.references[{i}].sha256",
                 item, sha256_file(target))
    return doc, updates


def collect_updates(project_root: str, write: bool) -> list[Update]:
    project_root = os.path.realpath(project_root)
    frontmatter = parse_frontmatter(os.path.join(project_root, "AINP.md"))
    plan_path = resolve_under(project_root, frontmatter.get("plan", ""), "AINP.md.plan")
    report_path = resolve_under(project_root, frontmatter.get("report", ""), "AINP.md.report")
    if not frontmatter.get("content_dir"):
        raise ValueError("AINP.md.content_dir is required before artifact hashes are refreshed")
    content_dir_path = resolve_under(project_root, frontmatter["content_dir"], "AINP.md.content_dir")
    if not os.path.isfile(plan_path):
        raise ValueError(f"plan file does not exist: {frontmatter.get('plan')!r}")
    if not os.path.isfile(report_path):
        raise ValueError(f"report file does not exist: {frontmatter.get('report')!r}")

    # Single scan for every mode: hashes are updated on the in-memory document
    # and recorded as Update entries; files are rewritten only when write=True.
    doc, updates = scan_report(project_root, report_path, plan_path, content_dir_path)
    if write and updates:
        write_json(report_path, doc)

    space_rel = frontmatter.get("space")
    if space_rel:
        space_path = resolve_under(project_root, space_rel, "AINP.md.space")
        if not os.path.isfile(space_path):
            raise ValueError(f"space file does not exist: {space_rel!r}")
        space_doc, space_updates = scan_space(space_path)
        if write and space_updates:
            write_json(space_path, space_doc)
        updates.extend(space_updates)

    references_rel = frontmatter.get("references")
    default_references = os.path.join("ainp", "references", "reference_manifest.json")
    references_path: str | None = None
    if references_rel:
        references_path = resolve_under(project_root, references_rel, "AINP.md.references")
        if not os.path.isfile(references_path):
            raise ValueError(f"references manifest does not exist: {references_rel!r}")
    else:
        candidate = os.path.join(project_root, default_references)
        if os.path.isfile(candidate):
            references_path = candidate
    if references_path:
        ref_doc, ref_updates = scan_reference_manifest(project_root, references_path)
        if write and ref_updates:
            write_json(references_path, ref_doc)
        updates.extend(ref_updates)
    return updates


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh project-local AINP integrity hashes. Not a validator or trust proof."
    )
    parser.add_argument("project_root", help="Complete <name>_ainp project package root.")
    parser.add_argument("--write", action="store_true", help="Write refreshed hashes in place.")
    parser.add_argument("--check", action="store_true", help="Fail if any hash is stale; do not write.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    if args.write and args.check:
        parser.error("--write and --check are mutually exclusive")

    project_root = os.path.realpath(args.project_root)
    try:
        updates = collect_updates(project_root, write=args.write)
    except Exception as exc:  # noqa: BLE001
        message = sanitize_text(str(exc), project_root)
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2))
        else:
            print(f"ERROR: {message}", file=sys.stderr)
        return 2

    payload = {
        "ok": True,
        "mode": "write" if args.write else "check" if args.check else "dry-run",
        "updated": len(updates),
        "updates": [public_update(update, project_root) for update in updates],
        "note": "Integrity hashes only; run validation/release gates next. This is not a trust proof.",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for update in updates:
            verb = "updated" if args.write else "would update"
            print(f"{verb}: {display_path(update.file, project_root)}: {update.field}")
        if not updates:
            print("hashes already current")
        print("NOTE: integrity hashes only; run validation/release gates next.")
    if args.check and updates:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
