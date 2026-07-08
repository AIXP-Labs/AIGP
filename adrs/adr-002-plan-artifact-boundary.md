# ADR-002: Plan Is Not Artifact; Both Are First-Class

Status: Accepted

## Context

AINP governs generation projects. Early drafts could be misread as a plan-only
format, while generated content could be treated as an unstructured afterthought.
That weakens auditability: a valid plan alone does not prove that content exists,
and content without a plan/report cannot explain its constraints or acceptance
criteria.

## Decision

AINP project packages treat `ainp/` and `<name>/` as co-equal first-class
folders:

- `ainp/` holds the generation plan, evidence report, feedback and generation
  space index.
- `<name>/` holds the generated content itself.
- `AINP.md` binds those folders and serves as the package entry point.

The plan is never the artifact. A structurally valid plan does not imply that
the artifact is safe, original, factual, lawful or complete.

## Consequences

Validators can make strong structural claims about package layout, declared
content paths and report bindings. They still cannot make trust claims about the
content. This preserves the honesty boundary while making generated content a
first-class part of the package.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
