# ADR-004: Content Architecture Binds Generated Files and Points

Status: Accepted

## Context

Human-readable outlines are useful, but they are not enough for multi-file
generation projects. Validators and reports need stable ids for files and
content points so that generated artifacts, acceptance criteria and feedback can
refer to the same objects.

## Decision

AINP uses `generation.content_architecture` as the machine-binding layer:

- `structure[]` remains the human-readable outline.
- `content_architecture.files[]` declares generated files with ids, paths,
  types, required status and points.
- Report artifacts bind back through `artifacts[].file_id`.
- Feedback issues may target declared `file_id` and `point_id` values.
- Complete project packages require `content_architecture`; standalone plans may
  omit it.

## Consequences

Project packages can verify that planned content, report artifacts and feedback
targets refer to the same generated-content structure. AINP still does not turn
content architecture into an execution graph; it is a binding and audit layer,
not a runtime.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
