---
protocol: "AINP v1.0.0"
authority: ainp.dev
axiom_0: Human_Sovereignty_and_Wellbeing
name: slugify_cli
version: "1.0.0"
summary: "Complete AINP project package for a generated Python CLI program: AINP.md, AINP plan folder, source code, tests and evidence report."
status: active
artifact_type: code
plan_dir: ainp/
content_dir: slugify_cli/
plan: ainp/slugify_cli.generation.json
report: ainp/slugify_cli.generationreport.json
feedback: ainp/slugify_cli_feedback.generationfeedback.json
space: ainp/project.ainp.json
license: Apache-2.0
---

## Project Declaration

This package demonstrates a complete AINP project for a generated program. The
root `AINP.md` is the project declaration, index and validation entry point.
The `ainp/` directory is the plan/evidence folder: it contains the generation
plan, report, feedback and generation-space index. The `slugify_cli/` directory
is the generated program content folder: it contains the CLI source, tests and
program README. The two folders are co-equal parts of the package.

## Generation Plan

Primary plan: `ainp/slugify_cli.generation.json`.
Acceptance evidence: `ainp/slugify_cli.generationreport.json`.
Generation space: `ainp/project.ainp.json`.
Candidate realization target: external developer workflow recorded in the plan.

The execution binding is intentionally marked `external`. AINP records what was
planned and what evidence was reported; it does not claim that a local runtime
executed or independently trusted the development workflow.

## Content Artifacts

Program README: `slugify_cli/README.md`.
CLI source: `slugify_cli/slugify_cli.py`.
Unit tests: `slugify_cli/tests/test_slugify_cli.py`.

The plan declares all three files in `generation.content_architecture` with
stable `file_id` values. The report binds every artifact back to its declared
`file_id` and records recomputable hashes relative to the project root.

## Feedback Loop

Content feedback: `ainp/slugify_cli_feedback.generationfeedback.json`.

The plan guides the program through file-level points and acceptance criteria.
The generated program feeds review back to the same generation id through the
feedback file, so future revisions can change the plan with structured evidence
instead of undocumented edits.

## How To Validate

```bash
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
```

Project validation proves package wiring, schema/rule consistency and local
hash recomputability. The unittest command proves only the behavior covered by
the included tests.

## Honesty Boundary

This package is a worked example of using AINP for software generation. A valid
AINP project package does not prove the program is secure, production-ready,
legally compliant or externally trusted. It proves that the program files,
plan, evidence report and feedback record are wired together in a checkable
way.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
