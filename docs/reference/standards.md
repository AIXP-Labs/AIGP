# Standards Reference

`specification/standards/` contains lightweight machine-readable reference data
for AINP v1.0.0.

| File | Purpose |
|---|---|
| `AINP_Standard.core.json` | Core terms, file-family rules, complete project-package shape and rule-family index |
| `AINP_Standard.security.json` | Untrusted-input, high-risk, provenance, sandbox and honesty boundaries |
| `AINP_Standard.ecosystem.json` | Project package, release-gate and feedback-loop alignment rules |
| `ainp-rules-v1.0.0.json` | Conformance-rule index used by docs and tests |
| `README.md` | Directory boundary and maintenance contract |

## Boundary

These files are standard-library reference data for documentation, dashboards
and tooling. They are not JSON Schema mirrors, AISOP flows, AIAP programs,
runtime extensions, registry trust roots, legal certificates or safety
certificates.

Canonical schemas remain in top-level `schemas/`. Normative semantics remain in
`specification/AINP_Protocol.md`.

The release gate checks this boundary through `tests/test_ainp.py` and
`tools/check_doc_sync.py`.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
