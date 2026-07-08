# Release Evidence Matrix

This matrix explains what the publication gate proves and what remains outside
local validation.

Run the local release gate:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest
```

## Required Checks

| Command | Evidence | Boundary |
|---|---|---|
| `python -B tools/ainp.py doctor --json` | Unified local health check covering required files, examples, project packages, hash freshness, docs and links | Structural consistency only; not external trust or legal certification |
| `python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json` | Plan-side validation with expected default-mode warnings | Not release-clean by itself; the example intentionally demonstrates a G9 missing binding |
| `python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release` | High-risk plan gates can pass release mode when approval/consent/disclosure are declared | Does not prove the consent or approval is externally authentic |
| `python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json` | Standalone P11 reference-manifest structure and integrity: bundled schema passes, local paths stay under `ainp/references/` and recorded hashes recompute | Does not fetch external URIs or prove reference authority, freshness or trust |
| `python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json` | Report shape, plan hash lock, artifact hash recompute and required content-file coverage | Does not make a failed criterion pass |
| `python -B tools/ainp_report_check.py examples/file_family/high_risk_likeness.generationreport.json --mode release` | High-risk report gate coverage: artifact hash recomputes, R7 disclosure/content-credential records are present, and R9 approval-gate evidence is recorded | Does not prove consent validity, approver authority, credential authenticity or legal compliance |
| `python -B tools/ainp_release_check.py examples/file_family/high_risk_likeness.generation.json --report examples/file_family/high_risk_likeness.generationreport.json` | Full release gate for the high-risk likeness file-family example | Still an evidence-structure gate; not a rights, safety or trust certificate |
| `python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp` | Full release gate for the project example, including the bundled-schema keyword subset gate | Still not legal/safety/trust certification; not a general JSON Schema validator |
| `python -B tools/ainp_project_check.py examples/whitepaper_ainp` | Complete project package wiring, planned content paths and report artifacts under `AINP.md.content_dir`, feedback-loop file/point alignment, and release gate | Does not prove external provenance or feedback truth |
| `python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py` and `python -B examples/aikp_navigator_aiap_ainp/aikp_navigator_aiap/tests/test_resolve_topic.py` | Example-project unit tests for generated content folders; the release script discovers `examples/*_ainp/*/tests/test_*.py` | Covers only the included behavior cases; not production assurance |
| `python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check` | Hash freshness check for project-local plan/report/artifact/space/reference-manifest local entries; invalid reference source shapes fail closed | Integrity only; rehashing is not validation or trust certification |
| `python -B tools/ainp_project_check.py examples/slugify_cli_ainp` | Complete program project package wiring: `AINP.md`, plan/report/feedback, source, tests and README artifacts under `content_dir` | Does not prove the program is secure or externally trusted |
| `python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp` | Complete AIAP-package generation example wiring: AINP plan/report/feedback plus P11 `ainp/references/` protocol/template manifest around generated `AIAP.md`, `agent_card.json`, `main.aisop.json`, helper tool, tests and README | Does not prove AIAP runtime execution, AIAP compliance, reference freshness or external trust |
| `python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json` | G12 breaking-change discipline | Requires real previous/current inputs |
| `python -B tests/test_ainp.py` | 79-test conformance, standards-layer, stale protocol-name guard, discovered project-package, discovered example-project tests, unified CLI doctor, doctor example-project and strict file-family discovery, delegated child-tool exit fail-closed checks, JSON-output path redaction on success and failure paths including encoded/fully-encoded unsafe-URI redaction plus Windows/UNC/POSIX local paths with spaces/no extension, release-script POSIX private-path guard, release-script failure-output redaction and bad-root guard, doc-sync/Markdown-checker failure-output redaction including Markdown image-link, reference-link definition/use/inline-code false-positive prevention, matched-fence and HTML href/src/srcset/poster unsafe-target coverage, hash-refresh/hash-sandbox/content-dir-required/content-dir-bounds/missing-artifact/duplicate-frontmatter/atomic-write/file-mode preservation, high-risk likeness approval-report release coverage, optional references/template manifest, reference-manifest source-type schema conditionals, stdlib schema-keyword subset guard and teeth suite | Does not cover a production generator |
| `powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1` | Local aggregate publication gate, including strict JSON syntax outside `tests/fixtures/invalid/`, forbidden residue scans for caches, `site/`, `build/`, `dist/` and `*.egg-info/`, and private-path/key scans including Windows user-profile paths on any drive, drive-relative user-profile forms and POSIX local absolute paths | In non-Git directories, clean-tree checks are skipped unless requested |
| `powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest` | Strong local/CI publication gate, adding pytest discovery on top of the stdlib release gate | Requires dev dependencies; still not external trust or legal certification |

## Hygiene Checks

| Command | Evidence |
|---|---|
| `python -B tools/check_doc_sync.py --root .` | README/docs/CI/release command synchronization, schema single-source guard and standards-layer boundary guard |
| `python -B tools/check_markdown_links.py --root .` | Local Markdown links, image links, reference-link definitions and anchors resolve; checker rejects missing scan targets, scan-target escapes, local machine-path inline/image/reference links, autolinks and HTML href/src/srcset/poster attributes, and raw or bounded percent-decoded unsafe schemes |
| `git diff --check` | Whitespace errors absent |
| `git diff --exit-code` | No tracked generated drift |
| `git status --porcelain=v1 --untracked-files=all` | No untracked generated artifacts |

## Expected Warnings

`AINP_W_EXTERNAL_VERIFICATION_REQUIRED` is an honest boundary signal. It means
rights, consent, provenance, source truth or approval authenticity require
external verification. It must not be hidden or converted into a trust claim.
Likewise, `content_credential.present=true` or
`verification_status=externally_verified` records external evidence; the local
tools do not validate C2PA manifests, signatures or trust lists.
Declared generator metadata and watermark evidence are handled the same way:
they are report-side evidence records for transparency, not proof of provider
trust or watermark detectability.

## Trust Boundary

All checks passing means the repository is structurally ready for release. It
does not mean generated content is safe, original, factual, rights-cleared or
legally compliant.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
