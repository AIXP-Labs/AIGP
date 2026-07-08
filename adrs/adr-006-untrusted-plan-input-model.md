# ADR-006: Untrusted Plan Input Model

Status: Accepted

## Context

AINP plans may be written by users, AI systems, generators or third-party
pipelines. A structurally valid plan can still be malicious, misleading,
stale, incomplete or outside the user's intent.

## Decision

AINP treats every plan, report, feedback file and binding as untrusted input
until an external trust decision is made. Validators may prove JSON shape,
schema conformance, path containment, hash consistency and rule coverage. They
do not prove that the generation request is safe, authorized, factual,
beneficial or worth executing.

Tools that consume AINP files must preserve this boundary:

- no plan field may silently override user intent;
- no binding may trigger network access or execution by itself;
- no self-declared safety claim may replace approval, consent or provenance;
- high-risk plans still require explicit human gates.

## Consequences

AINP can be safely used as an exchange format because consumers know what the
format proves and what it does not prove. The trust root remains outside the
package: user authorization, registry provenance, signatures, runtime policy or
an equivalent governance mechanism.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
