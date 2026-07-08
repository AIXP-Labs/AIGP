# Governance — AINP v1.0.0

## Model

AINP is part of the AIXP protocol family and is governed as a **BDFL project** during its incubation phase. The BDFL owns: protocol versioning, the `high_risk_types` list, rule additions/removals, and release decisions.

## Immovable constraints

1. **Axiom 0 (HSAW)** is not modifiable through this project's governance. Proposals that remove or weaken the high-risk human approval gate (G6), the red-line assurance limits (G14/G15), the untrusted-input rules (spec §8), the disclosure requirements (G8), or the self-trust prohibition (G7) are rejected regardless of votes or popularity.
2. **The five honesty principles** (spec §7) are load-bearing: plan ≠ artifact; self-report ≠ verification; acceptance lives in the report; artifacts never self-declare trust; approval covers only its object.

## Change process

- **Breaking changes** to file formats or rules require a MAJOR protocol version bump and an upgrade note in CHANGELOG.
- **`high_risk_types.v1.0.0.json` is versioned data**: additions are MINOR; removals are MAJOR and require a written rationale (removing a protection is a breaking change to safety posture).
- Every substantive design decision is recorded as an ADR under `adrs/` (see ADR-001 for the decision discipline itself).
- Rule semantics live in `specification/AINP_Protocol.md`; the reference tools implement them 1:1; the teeth fixtures prove them. A change is not merged unless all three move together.
- New required fields, rule families or release-blocking gates require a demonstrated failure case, a teeth fixture, or a documented external interoperability/compliance driver. Convenience fields start optional or advisory until evidence shows they must become mandatory.

## Conformance claims

A tool may claim "AINP v1.0.0 conforming" only if it (a) implements the rules of spec §10 at the declared mode, (b) honors the untrusted-input rules of spec §8, and (c) never emits trust language beyond `structure-valid` (spec §10 boundary).

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
