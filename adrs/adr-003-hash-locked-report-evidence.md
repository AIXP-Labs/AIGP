# ADR-003: Acceptance Evidence Lives in Hash-Locked Reports

Status: Accepted

## Context

Acceptance criteria belong in the generation plan, but acceptance results belong
to a specific generation run. If results were written back into the plan, the
plan would mix desired state with run evidence. If reports did not lock the plan
snapshot, a later plan edit could make old evidence appear to validate a
different contract.

## Decision

AINP keeps acceptance definitions and acceptance evidence separate:

- `*.generation.json` defines acceptance criteria and constraints.
- `*.generationreport.json` records run evidence and `overall.conformant`.
- `generationreport.plan_ref.sha256` locks the report to the exact plan bytes it
  judged.
- Release checks recompute the plan hash and, when requested, artifact hashes.

## Consequences

Reports become evidence containers rather than self-certifying truth claims.
Changing the plan requires refreshing the evidence chain or explicitly retaining
an archived plan blob. Hashes prove local byte integrity only; they do not prove
rights, provenance, factual truth or approval authenticity.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
