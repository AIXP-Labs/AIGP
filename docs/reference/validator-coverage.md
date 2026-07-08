# Validator Coverage Matrix

The reference toolchain is a conformance gate, not a trust oracle.

## Canonical Commands

```bash
python -B tools/ainp.py doctor --json
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release
python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json
python -B tools/ainp_report_check.py examples/file_family/high_risk_likeness.generationreport.json --mode release
python -B tools/ainp_release_check.py examples/file_family/high_risk_likeness.generation.json --report examples/file_family/high_risk_likeness.generationreport.json
python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json
python -B tests/test_ainp.py
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest
```

## Coverage

| Tool | Checks | Does not prove |
|---|---|---|
| `ainp.py` | Unified command dispatch and `doctor` health checks across required files, examples, project packages, hash freshness, docs and links | Independent validation logic, external trust, legal compliance or content truth |
| `ainp_validate.py` | G/FB/SP shape, gates, schema profile binding, declared content-architecture shape, standalone P11 reference-manifest bundled-schema integrity and static safety rules | Artifact quality, legal compliance, rights validity, factual truth, reference freshness or trust |
| `ainp_report_check.py` | Report shape, plan hash lock, report-side disclosure/approval gates including declared generator metadata and watermark evidence, artifact hash recompute in sandbox, required content-file coverage via `file_id` | Evidence source trust, approval authenticity, provider trust, watermark detectability, source truth |
| `ainp_release_check.py` | Bundled-schema keyword subset gate, including local composition/conditional schema keywords used by this repository, plus release-mode plan/report checks and `overall.conformant=true` | Full JSON Schema support beyond the bundled schema keyword set; external legal/safety/trust claims |
| `ainp_project_check.py` | `AINP.md + ainp/ + <name>/` package wiring, required project-package content architecture, report artifact placement and planned content paths under `AINP.md.content_dir`, approved/active feedback-loop alignment including file/point targets, and release gate with project root | Registry approval or package trust, feedback truth or completeness |
| `ainp_rehash.py` | Authoring-time refresh/check of project-local plan/report/artifact/space/reference-manifest hashes, with atomic same-directory replacement, original file-mode preservation for existing files and fail-closed reference source shape checks | Validation, safety, rights, provenance, provider trust or content trust |
| `check_doc_sync.py` | Command/docs/CI/release-gate synchronization, strict JSON syntax outside `tests/fixtures/invalid/`, schema single-source guard, standards-layer boundary guard, stale protocol-name guard and structured/public failure output | Technical correctness beyond the checked strings |
| `check_markdown_links.py` | Local Markdown targets, image targets, reference-link definitions and heading anchors; missing scan-target rejection; scan-target escape rejection; local machine-path inline-link/image-link/reference-link/autolink/HTML href-src-srcset-poster rejection; matched Markdown fence and inline-code handling; raw and bounded percent-decoded unsafe-scheme rejection | External URL availability |

## Repository Hygiene Commands

```bash
python -B tools/check_doc_sync.py --root .
python -B tools/check_markdown_links.py --root .
git diff --check
git diff --exit-code
git status --porcelain=v1 --untracked-files=all
```

These commands prove local repository hygiene. They do not prove external trust.
The local release wrapper is stdlib-only and validates the bundled schemas with
the keyword subset used here, including the local composition/conditional
keywords present in those schemas; full Draft 2020-12 behavior is covered by
the `jsonschema` tests.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
