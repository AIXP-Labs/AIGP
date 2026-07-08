# ADR-011: Unverifiable Is Not a Pass Credential

Status: Accepted

## Context

AI generation often produces claims that cannot be fully verified by static
tools: factual correctness, legal sufficiency, originality, model behavior,
source provenance and human consent are common examples.

## Decision

Unverifiable claims must not be converted into pass credentials. AINP tools may
record them, warn about them or require external evidence, but they must not
present self-attestation as independent verification.

When a check is outside static scope, reports and validators should say so
plainly. The correct outcome is an honest warning, required external evidence or
manual approval, not a green claim that exceeds what was checked.

## Consequences

AINP avoids the common failure mode where a clean validation report is mistaken
for proof of safety. This keeps the protocol credible as a governance layer and
preserves the human decision boundary required by Axiom 0.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
