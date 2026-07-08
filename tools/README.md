# AINP Reference Tools

Zero-dependency (Python 3.10+ stdlib).

The bundled schema gate reads the canonical machine-readable schemas from the
top-level `schemas/` directory. `specification/` indexes those files but does not
mirror them.

## Canonical release commands

```bash
python -B tools/ainp.py doctor --json
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release
python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json
python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B examples/aikp_navigator_aiap_ainp/aikp_navigator_aiap/tests/test_resolve_topic.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp
python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json
python -B tests/test_ainp.py
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest
```

## ainp.py — unified CLI + doctor

```bash
python -B tools/ainp.py doctor
python -B tools/ainp.py validate examples/file_family/medical_advice.generation.json --mode release
python -B tools/ainp.py project-check examples/slugify_cli_ainp
```

`ainp.py` is a thin dispatcher over the reference tools. It does not duplicate
validation logic. `ainp doctor` checks required files, example validation,
report checks, project package checks, hash freshness, documentation
synchronization and local Markdown links. It proves local structural consistency
only, not trust, legal compliance, rights validity or factual truth.

## ainp_validate.py — file-family rules (G1–G16, FB1, SP1, SP2, P11 manifest)

```bash
python -B tools/ainp_validate.py <files...> [--mode default|strict|release] [--json]
python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json   # G12
python -B tools/ainp_validate.py plan.generation.json --high-risk-types path/to/high_risk_types.v1.0.0.json
python -B tools/ainp_validate.py project/ainp/references/reference_manifest.json
```

The validator can check a standalone `ainp.v1.0.0.reference_manifest` file:
bundled JSON Schema/profile shape, reference ids, local `ainp/references/`
containment and recorded local hashes. It does not fetch external URIs and does
not prove reference trust or freshness.

## ainp_report_check.py — report-side rules (R1–R10)

```bash
python -B tools/ainp_report_check.py report.generationreport.json [--plan plan.json] [--archive dir] [--mode release] [--json]
python -B tools/ainp_report_check.py report.generationreport.json --plan plan.json --mode release --artifact-root project_root
```

R7 records every true `disclosure_policy.*_required` switch on the report side,
including generator metadata and watermark evidence when declared. These records
support transparency; they do not prove provider trust or watermark
detectability.

R10 binds report artifacts back to the plan's declared content architecture:
required content files need matching `artifacts[].file_id` and path coverage.

## ainp_release_check.py — full release gate wrapper

```bash
python -B tools/ainp_release_check.py plan.generation.json --report report.generationreport.json [--json]
python -B tools/ainp_release_check.py project/ainp/plan.generation.json --report project/ainp/report.generationreport.json --project-root project
```

Runs the bundled JSON Schema gate first (plan, report and high-risk data), then
the release-mode plan/report checkers and the final `overall.conformant=true`
wrapper gate. It remains stdlib-only; the schema gate intentionally implements
the Draft 2020-12 keyword subset used by the bundled schemas in this repository,
including the local composition/conditional keywords they contain. It is not a
general JSON Schema validator. The test suite uses `jsonschema` as the full
Draft 2020-12 reference check. The wrapper uses the same strict JSON
parsing posture as the validators: duplicate object keys and non-standard
literals such as `NaN`/`Infinity` fail closed.

## ainp_project_check.py — complete project package checker

```bash
python -B tools/ainp_project_check.py <name>_ainp/ [--json]
```

Checks the canonical package layout: uppercase `AINP.md` for the project
declaration/index, `ainp/` as the AINP plan folder, `<name>/` as the project
content folder, AINP.md frontmatter/body alignment, report artifacts under
`AINP.md.content_dir`, planned content architecture paths under the same content
directory, approved/active feedback loop alignment including file/point targets,
side-file JSON Schema + strict-rule validation for declared side files, optional
`ainp/references/` manifest integrity for reference files/templates, and the
release gate with the project root as artifact sandbox.

## ainp_rehash.py — project-local hash refresh helper

```bash
python -B tools/ainp_rehash.py <name>_ainp/ --check
python -B tools/ainp_rehash.py <name>_ainp/ --write
```

Refreshes `generationreport.plan_ref.sha256`, report artifact hashes, local
generation-space hashes and local `reference_manifest` hashes. This is an
authoring convenience only: hashes prove local integrity, not safety, rights,
provenance or trust. After `--write`, run the normal validation/release gates.
While scanning `reference_manifest.json`, invalid reference source shapes such
as `external_uri` entries with local `sha256` anchors fail closed instead of
being silently skipped.

Scope boundary: the tool operates on complete `<name>_ainp/` project packages
(it resolves everything through `AINP.md`). Standalone file-family documents
have no package entry point — recompute their hashes manually or move them into
a project package first.

All tools: exit 0 = no FAIL, 1 = FAIL present, 2 = usage/tool error. Output language is deliberately bounded: `PASS structure-valid` / `PASS release-structure-valid` / `WARN external-verification-required` — never `legally-safe` / `rights-verified` / `content-trusted`.

All tools share public-output sanitization for paths and unsafe URI text. Public
logs use repository-relative paths where possible and redact Windows, UNC and
POSIX local-machine paths, unsafe URI schemes and bounded percent-encoded
unsafe URI forms.

Security posture (spec §8): plans are untrusted input — no binding execution, no input downloads, no trust in embedded hashes, local hash recompute stays inside a realpath/common-path sandbox, >10 MB files rejected.

Repository hygiene:

```bash
python -B tools/check_doc_sync.py --root .
python -B tools/check_markdown_links.py --root .
git diff --check
git diff --exit-code
git status --porcelain=v1 --untracked-files=all
```

`check_markdown_links.py` checks only repository-root-contained Markdown
targets. It rejects missing scan targets, scan-target escapes and local
machine-path Markdown inline links, image links, reference-link definitions,
autolinks and HTML `href`/`src`/`srcset`/`poster` targets, including drive,
drive-relative and UNC forms, and rejects raw or percent-encoded unsafe schemes
with bounded repeated decoding instead of silently treating private machine
paths or unsafe URLs as ordinary external links. Fenced code blocks are skipped
only when the closing fence marker matches the opening marker.

`check_doc_sync.py` and `scripts/release_check.ps1` also run strict JSON syntax
checks across repository JSON files, except for the intentional adversarial
fixtures under `tests/fixtures/invalid/`. They also enforce the schema
single-source rule and the `specification/standards/` boundary: standards are
reference data, not schema mirrors, AISOP flows, AIAP programs or trust proofs.
The release script discovers and runs example project tests under
`examples/*_ainp/*/tests/test_*.py`, so new checked examples cannot carry
untested self-reported unit-test evidence.
Reference manifests under `ainp/references/` are optional. When present, they
are treated as generation context integrity anchors, not content artifacts and
not trust proofs.
Generated residue such as `site/`, `build/`, `dist/`, `*.egg-info/` and Python
bytecode/cache directories must be removed before release.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
