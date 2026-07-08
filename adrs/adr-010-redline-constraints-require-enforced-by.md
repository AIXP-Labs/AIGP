# ADR-010: Redline Constraints Require `enforced_by`

Status: Accepted

## Context

Generation plans often include safety red lines such as consent requirements,
rights checks, prohibited content and domain-specific restrictions. If those
red lines are only prose, consumers cannot tell whether they are backed by a
mechanism.

## Decision

Redline constraints must declare `enforced_by`. The field records the mechanism
intended to enforce the rule, such as an approval gate, consent record, policy
check, validator rule or runtime control.

Static validation can verify that `enforced_by` exists and follows the expected
shape. It cannot prove that every external mechanism was actually executed
unless the corresponding report evidence is present and independently trusted.

## Consequences

AINP keeps red lines auditable without pretending that prose is enforcement.
Missing enforcement metadata is a conformance problem; unverifiable enforcement
evidence remains a trust-boundary problem.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
