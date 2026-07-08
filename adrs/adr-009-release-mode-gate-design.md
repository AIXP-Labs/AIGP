# ADR-009: Release Mode Gate Design

Status: Accepted

## Context

Draft work should be easy to iterate, while release candidates need stronger
proof that required gates, reports, feedback and package bindings are present.

## Decision

AINP validators support stricter release checks without making draft authoring
unnecessarily heavy. Release mode raises selected warnings or missing evidence
into failures when the package is meant to be shared or published.

Release mode checks include, but are not limited to:

- high-risk approval and disclosure evidence;
- report-to-plan and report-to-artifact hash locks;
- package-level manifest consistency;
- feedback requirements for active or approved packages;
- path containment and binding safety.

## Consequences

The protocol remains usable during drafting while providing a clear publication
gate. A green release check is a structural and evidence-integrity claim, not a
claim that the generated content is true, lawful or safe in every deployment.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
