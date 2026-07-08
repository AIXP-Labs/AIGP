# ADR-005: High-Risk Generation Requires the HSAW Human Gate

Status: Accepted

## Context

Some generation projects can materially affect human sovereignty, safety,
privacy, regulated-domain decisions or public trust. Pure static validation
cannot decide whether a high-risk output is acceptable, and self-attested safety
claims are not enough.

## Decision

AINP defines high-risk triggers through `high_risk_types.v1.0.0.json` and
`risk_profile`:

- high-risk artifact carrier types,
- declared high-risk tags,
- `deployment_scope = mass_public`,
- `risk_level in {high, critical}`.

Triggered high-risk plans must declare `governance.approval_required = true`.
Reports must carry approval-gate evidence for release. Validators check that the
gate is declared and evidenced; they do not authenticate the approver or decide
legal compliance.

## Consequences

High-risk generation remains under human sovereignty control. The reference
tools can fail closed when the required gate is missing, while preserving the
honesty boundary that gate authenticity and domain compliance remain external
verification tasks.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
