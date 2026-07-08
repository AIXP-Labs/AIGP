# ADR-008: Report Hash-Lock Discipline

Status: Accepted

## Context

AINP reports claim what was generated and how it was checked. Without stable
links to the plan and artifacts, a report can drift from the files it describes.

## Decision

Generation reports must hash-lock the evidence they cite:

- `plan_ref.sha256` binds the report to the plan file;
- each artifact record binds a relative artifact path to its SHA-256 hash;
- report checks describe methods and results, but hashes bind those claims to
  concrete bytes on disk.

Hash-locks prove integrity of the referenced bytes, not safety or trust.

## Consequences

Reviewers can detect stale reports, artifact swaps and accidental drift. They
still need human or external review for claims such as factuality, authorship,
licensing and suitability.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
