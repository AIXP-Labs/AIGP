# ADR-012: AINP With AIAP Creator

Status: Accepted

## Context

AIAP Creator can generate application packages. AINP can govern the generation
process by recording the plan, acceptance criteria, generated files, evidence
report and feedback. This relationship should be explicit without making AINP
an AIAP runtime or importing AIAP package structure into AINP itself.

## Decision

AINP integrates with AIAP Creator through references and lifecycle evidence:

- AIIP may express the original intent;
- AINP records the generation plan and content architecture;
- AIJP may schedule or track generation jobs;
- AIAP Creator may produce an AIAP application package as the artifact;
- AINP reports hash-lock the generated application files and checks;
- AIKP may retain lessons, patterns and review outcomes.

Cross-protocol bindings are references, not execution authority. AINP tools must
not auto-execute AIAP, AISOP, AISP or AIJP targets because a binding exists, and
must not treat a binding as a trust proof.

## Consequences

AINP can support AIAP Creator, SoulIDE, SoulBot and related AIXP workflows while
remaining a generation-governance protocol. The generated application remains
owned by its target protocol; AINP owns the plan/report/feedback evidence around
its creation.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
