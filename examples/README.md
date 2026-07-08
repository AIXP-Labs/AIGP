# AINP Examples

Examples are split by package style:

- `file_family/` contains standalone AINP file-family examples.
- `bindings/` contains non-normative cross-protocol binding examples.
- `whitepaper_ainp/` contains a complete distributable `<name>_ainp/` project package.
- `slugify_cli_ainp/` contains a complete program-generation project package with source, tests, README, report and feedback.
- `aikp_navigator_aiap_ainp/` contains a complete AIAP-package generation example governed by AINP.

All file-family examples pass `tools/ainp_validate.py` (default mode) and their JSON Schemas (`additionalProperties: false`). Intentional WARNs are part of the demonstration:

| File | Demonstrates |
|---|---|
| `file_family/whitepaper.generation.json` | Low-risk document plan; includes `content_architecture` for `out/whitepaper.md`; red lines with multi-control-point `enforced_by`; a `soft` style constraint; `bindings` as never-auto-executed candidates (the missing local target intentionally produces `AINP_W_G9_BINDING_TARGET_MISSING` — WARN in default, FAIL in strict/release **by design**, pinned in the tests' example×mode matrix) |
| `file_family/high_risk_likeness.generation.json` | **HSAW gate**: `likeness` risk tag ⇒ approval + consent (recorded, evidence-referenced, scope-bounded) + mandatory disclosure; passes `--mode release` |
| `file_family/high_risk_likeness.generationreport.json` | Release-grade report for the likeness example: artifact hash recomputes, R7 disclosure/content-credential gates are recorded, and R9 approval gate evidence is present without claiming local trust proof |
| `file_family/high_risk_likeness_feedback.generationfeedback.json` | Feedback record for the likeness example, pointing back to the portrait content point and preserving the evidence-vs-trust boundary |
| `file_family/landing_page.generation.json` | `deployment_scope: mass_public` triggers the approval gate with zero risk tags; passes `--mode release` |
| `file_family/dataset.generation.json` | Non-human-facing artifact: disclosure_policy declared with switches legitimately false; open-license input with `external_verify_required` provenance (boundary WARN by design) |
| `file_family/medical_advice.generation.json` | High-risk regulated-domain example: medical-advice tags trigger approval + disclosure while forbidding diagnosis/dosage/personalized treatment advice; passes `--mode release` |
| `file_family/security_exploit.generation.json` | High-risk security example: defensive lab material with approval gate and abuse-prevention red lines; passes `--mode release` |
| `file_family/whitepaper.generationreport.json` | Hash-locked acceptance evidence (`plan_ref.sha256` recomputes); artifact `file_id` binds to the plan's content architecture; an honestly FAILED criterion (a2) ⇒ derived `conformant: false`; passes `ainp_report_check.py --mode release` (artifact hash recomputes against `file_family/out/whitepaper.md`) but intentionally fails the full `ainp_release_check.py` gate because `overall.conformant=false`; verifiers record who **actually** checked — the pipeline's own `structure-checker`, never the AINP reference checker (it validates report structure/gates R1–R10 and does not execute acceptance checks) |
| `file_family/whitepaper_feedback.generationfeedback.json` | Feedback closing the loop from failed content review back to a specific declared content point |
| `file_family/project.ainp.json` | Generation space with re-hashable local entries (SP2); refs are recomputed only inside the space-file sandbox |
| `whitepaper_ainp/` | Complete active AINP project package: uppercase `AINP.md`, `ainp/` AINP plan folder, and `whitepaper/` project content folder; plan content architecture and report artifacts live under `AINP.md.content_dir`; active-package feedback points back to the same generation id and demonstrates a structured `revise` loop; includes a non-executable candidate binding descriptor for G9 target-presence demonstration; passes `ainp_project_check.py` |
| `slugify_cli_ainp/` | Complete active AINP **program** project package: uppercase `AINP.md`, `ainp/` plan/evidence folder, and `slugify_cli/` generated content folder with `README.md`, `slugify_cli.py` and `tests/test_slugify_cli.py`; report artifacts bind all required files by `file_id`; passes the program unittest and `ainp_project_check.py` |
| `aikp_navigator_aiap_ainp/` | Complete active AINP-governed **AIAP package generation** example: uppercase `AINP.md`, `ainp/` plan/evidence folder, optional `ainp/references/` protocol/template references, and `aikp_navigator_aiap/` generated content folder with `AIAP.md`, `agent_card.json`, `main.aisop.json`, helper tool, tests and README; shows AIAP Creator integration without claiming that AINP executes or certifies the AIAP runtime |
| `bindings/` | Cross-protocol examples for AIIP→AINP, AINP→AIJP, AINP→AIKP and AIAP Creator governed by AINP; uses `example_profile`, not AINP `schema`, so these files are references rather than normative AINP documents |

The example artifact `file_family/out/whitepaper.md` exists so the flat report's artifact hash is genuinely recomputable — evidence, not decoration.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
