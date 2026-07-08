# ADR-001 — Disk-verify, then decide, then record

Status: **Accepted** · Date: 2026-07-06

## Context

During the AINP planning chain (docs 01→12), the question "should `governance.risk_level` be kept alongside `risk_profile.risk_level`?" produced fence-sitting across two plan versions ("if kept, then...; otherwise delete"). A spec must not be two-minded.

## Decision

The tiebreak was made by **verifying the actual family convention on disk** (the AIIP repository's examples and schema genuinely carry `governance.risk_level` with a closed enum), then deciding accordingly (keep it as a DERIVED field, consistency-enforced by G13), and recording the evidence.

This ADR generalizes that move into the standing decision discipline for AINP:

1. When a design question hinges on "what does the family/ecosystem actually do", **verify on disk / at the source** — never decide from memory or assumption.
2. Decide one way. No conditional dual-track normative text.
3. Record the evidence (what was checked, what was found) in the ADR or the plan document.

## Consequences

- G13 exists because the family convention was verified as real.
- Future fence-sitting items must follow this three-step discipline before entering the spec.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
