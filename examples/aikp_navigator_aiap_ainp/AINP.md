---
protocol: "AINP v1.0.0"
authority: ainp.dev
axiom_0: Human_Sovereignty_and_Wellbeing
name: aikp_navigator_aiap
version: "1.0.0"
summary: "Complete AINP project package showing how an AIAP Creator run can generate a small AIAP application package under AINP plan, report and feedback governance."
status: active
artifact_type: code
plan_dir: ainp/
content_dir: aikp_navigator_aiap/
plan: ainp/aikp_navigator_aiap.generation.json
report: ainp/aikp_navigator_aiap.generationreport.json
feedback: ainp/aikp_navigator_aiap_feedback.generationfeedback.json
space: ainp/project.ainp.json
references: ainp/references/reference_manifest.json
license: Apache-2.0
---

## Project Declaration

This package demonstrates AINP governing the creation of an AIAP application
package. The root `AINP.md` is the project declaration, index and validation
entry point. The `ainp/` directory holds the generation plan, report, feedback
generation-space index and optional reference materials. The
`aikp_navigator_aiap/` directory is the generated AIAP content package.

## Generation Plan

Primary plan: `ainp/aikp_navigator_aiap.generation.json`.
Acceptance evidence: `ainp/aikp_navigator_aiap.generationreport.json`.
Generation space: `ainp/project.ainp.json`.
Reference manifest: `ainp/references/reference_manifest.json`.

The plan records an AIAP Creator style generation run without importing AIAP
runtime semantics into AINP. AINP governs what was intended, what files were
generated, what evidence was recorded and how feedback returns to the plan.

## Reference Materials

Reference manifest: `ainp/references/reference_manifest.json`.
Protocol reference snapshot: `ainp/references/aiap_protocol_reference.md`.
Package template: `ainp/references/templates/aiap_package.template.md`.

These files are generation references, not generated content. Their hashes prove
local integrity only; they do not prove external authority, freshness, legal
sufficiency or runtime trust.

## Content Artifacts

Generated package entry: `aikp_navigator_aiap/AIAP.md`.
Agent card: `aikp_navigator_aiap/agent_card.json`.
AISOP candidate flow: `aikp_navigator_aiap/main.aisop.json`.
Helper tool: `aikp_navigator_aiap/tools/resolve_topic.py`.
Unit tests: `aikp_navigator_aiap/tests/test_resolve_topic.py`.
Package README: `aikp_navigator_aiap/README.md`.

The plan declares each file in `generation.content_architecture`; the report
binds each artifact back to its declared `file_id` and recomputable SHA-256
hash relative to the project root.

## Feedback Loop

Content feedback: `ainp/aikp_navigator_aiap_feedback.generationfeedback.json`.

The feedback record accepts the example and records that AINP must remain the
generation-governance layer, not the AIAP runtime or an execution proof.

## How To Validate

```bash
python -B examples/aikp_navigator_aiap_ainp/aikp_navigator_aiap/tests/test_resolve_topic.py
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp
```

Project validation proves package wiring, schema/rule consistency and local
hash recomputability. The unit test proves only the small helper behavior
covered by this example.

## Honesty Boundary

This is a worked example of governing AIAP package generation with AINP. AINP
validation does not prove that the generated AIAP application is production
ready, externally trusted, legally compliant or executed by an AIAP runtime.
Bindings and generated runtime files remain untrusted until separately
authorized and verified.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
