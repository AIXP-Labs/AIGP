---
protocol: "AINP v1.0.0"
authority: ainp.dev
axiom_0: Human_Sovereignty_and_Wellbeing
name: whitepaper
version: "1.0.0"
summary: "Complete AINP project package for an illustrative protocol whitepaper: AINP.md, AINP plan folder and project content folder."
status: active
artifact_type: document
plan_dir: ainp/
content_dir: whitepaper/
plan: ainp/whitepaper.generation.json
report: ainp/whitepaper.generationreport.json
feedback: ainp/whitepaper_feedback.generationfeedback.json
space: ainp/project.ainp.json
license: Apache-2.0
---

## Project Declaration

This package demonstrates the canonical AINP project layout. The root `AINP.md`
is the project declaration, index and validation entry point. The `ainp/`
directory is the AINP plan folder: it contains the generation plan, report,
feedback and generation-space index. The `whitepaper/` directory is the project
content folder: it contains the generated content itself. The two folders are
co-equal parts of the package: `ainp/` carries the contract and evidence;
`whitepaper/` carries the generated artifact.

## Generation Plan

Primary plan: `ainp/whitepaper.generation.json`.
Acceptance evidence: `ainp/whitepaper.generationreport.json`.
Generation space: `ainp/project.ainp.json`.
Candidate realization target: `ainp/programs/generate_document.aisop.json`.

The candidate realization target is a non-executable example descriptor. It
exists so the plan can demonstrate G9 local-target presence without claiming
that an AISOP runtime has executed or verified the binding.

## Content Artifacts

Primary artifact: `whitepaper/whitepaper.md`.

The plan declares this file in `generation.content_architecture` as
`file_whitepaper_md`; the report binds its artifact record back to that
`file_id`. The report records the path relative to the project root, and the
project checker requires both the planned path and reported artifact path to
remain under `AINP.md.content_dir`, so the artifact hash can be recomputed
without allowing reads outside the package or placing accepted content in the
plan folder.

## Feedback Loop

Content feedback: `ainp/whitepaper_feedback.generationfeedback.json`.

The plan guides the artifact through `content_architecture`, constraints and
acceptance criteria. The generated artifact feeds back to the same plan
generation id through the feedback file, so the package records both
directions: plan-to-content guidance and content-to-plan review. In this
example the feedback verdict is `revise`, demonstrating that content review can
request a future plan/content iteration without breaking package structure.
Feedback is a structured review record, not proof that every external claim is
true.

## How To Validate

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
```

Project validation proves package structure, schema/rule consistency and local
hash recomputability. It does not prove rights validity, factual truth, legal
compliance, approval authenticity or content trust.

## Honesty Boundary

A valid AINP project package means `AINP.md`, the AINP plan folder and the
project content folder are wired together in a checkable way. The plan and
content are different, but both are first-class parts of the package; feedback
keeps the loop open from content back to plan. `AINP.md` is not a trust
certificate; it is an index and declaration. Consumers must still evaluate the
artifact and external evidence according to their own trust policy.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
