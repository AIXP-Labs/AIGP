# Conformance Rules

The normative rules are in
`specification/AINP_Protocol.md` section 10 and indexed for tooling in
`specification/standards/ainp-rules-v1.0.0.json`. The surrounding
standard-library reference files `AINP_Standard.core.json`,
`AINP_Standard.security.json` and `AINP_Standard.ecosystem.json` group those
rules into core semantics, security boundaries and ecosystem package
requirements. They are machine-readable reference data, not runtime flows.

| Family | Tool | Scope |
|---|---|---|
| G1-G16 | `tools/ainp_validate.py` | Plan-side generation rules, including content-architecture shape when declared |
| FB1 | `tools/ainp_validate.py` | Feedback binding and required fields |
| SP1-SP2 | `tools/ainp_validate.py` | Generation-space binding, hash and sandbox rules |
| P11 manifest | `tools/ainp_validate.py` | Standalone `ainp.v1.0.0.reference_manifest` bundled-schema/profile check, local reference/template containment and recorded hash recompute |
| R1-R10 | `tools/ainp_report_check.py` | Report evidence, plan/report consistency and required content-file coverage |
| P1-P11 | `tools/ainp_project_check.py` | Complete project package shape, required project-package content architecture, content-folder placement, approved/active feedback-loop alignment, optional references/template manifest checks and release gate |

The rules are intentionally split by evidence type. Static plan checks do not
prove report evidence. Report checks do not prove external truth. Project checks
do not prove trust; they only prove that the declaration, plan folder, content
folder, planned content architecture, report evidence and feedback loop are
wired consistently when those components are required or declared.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
