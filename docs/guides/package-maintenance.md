# Package Maintenance

This guide covers normal AINP package maintenance: refreshing integrity hashes,
checking a package after content edits, and validating a package before
publication.

## Package Shape

A complete AINP project package uses this shape:

```text
<name>_ainp/
├── AINP.md
├── ainp/
│   ├── <plan>.generation.json
│   ├── <plan>.generationreport.json
│   ├── <feedback>.generationfeedback.json
│   ├── project.ainp.json
│   └── references/              # optional: local references, templates and briefs
└── <name>/
```

`AINP.md` is the package entry point. It declares `plan_dir`, `content_dir`,
`plan`, `report`, `feedback`, and optional `space` / `references` paths. The
content folder named by `content_dir` stores the generated content itself.
If `references` is declared, it should point at `ainp/references/reference_manifest.json`.

## Refresh Integrity Hashes

Content edits, plan edits, report edits and reference edits can invalidate
stored hashes. Refresh project-local hashes with the author helper, then run the
normal validation gates:

```bash
python -B tools/ainp_rehash.py <name>_ainp --write
python -B tools/ainp_rehash.py <name>_ainp --check
python -B tools/ainp_project_check.py <name>_ainp
```

`ainp_rehash.py` is not a trust proof. It only updates recomputable local
integrity fields. Release checks must still run afterward.

## Update Package Metadata

After changing a package, check these fields before running the release gate:

- `AINP.md.status` reflects the package state.
- `AINP.md.plan_dir` is `ainp/`.
- `AINP.md.content_dir` points to the generated content folder.
- `AINP.md.plan`, `report`, `feedback` and optional `space` paths exist.
- `generation.content_architecture.root` matches the content folder.
- Each required generated file has a stable `file_id`, path and points.
- Report artifacts bind back to the planned files through `file_id`.
- Feedback uses the same `generation_id` as the plan and report.

## Standalone File-Family Checks

Standalone file-family examples do not have `AINP.md`. Validate them directly:

```bash
python -B tools/ainp_validate.py path/to/project.ainp.json
python -B tools/ainp_report_check.py path/to/file.generationreport.json --mode release
```

For standalone reports, the report directory is the artifact sandbox. For
complete project packages, `ainp_project_check.py` passes the package root as
the sandbox and also enforces `content_dir` placement.

## Final Gate

Before publication, run:

```bash
python -B tools/ainp.py doctor --json
python -B tests/test_ainp.py
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest
```

The expected result is:

- local doctor passes;
- conformance tests pass;
- release check passes.

## Boundary

Passing these checks proves local package structure, schema/rule consistency and
recomputable integrity fields. It does not prove the generated content is safe,
original, lawful, factual, externally trusted or production-ready.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
