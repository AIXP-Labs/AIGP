# AINP Standards

This directory contains lightweight machine-readable standard-library references
for AINP v1.0.0.

| File | Role |
|---|---|
| `AINP_Standard.core.json` | Core terms, file-family rules, project-package shape and rule-family index. |
| `AINP_Standard.security.json` | Untrusted-input, high-risk, provenance, sandbox and honesty boundaries. |
| `AINP_Standard.ecosystem.json` | Complete project package, release-gate and feedback-loop alignment rules. |
| `ainp-rules-v1.0.0.json` | Human-readable conformance-rule index used by docs and tests. |

## Boundary

- These files are reference data for documentation, dashboards and tooling.
- They are not JSON Schema mirrors. Canonical schemas remain in `../../schemas/`.
- They are not AISOP flows, AIAP programs, runtime extensions, registry trust
  roots, legal certificates or safety certificates.
- Do not add `*.aisop.json` files to this directory.

## Maintenance

- Update `AINP_Standard.core.json` when rule families, terms, file-family shape
  or project-package shape change.
- Update `AINP_Standard.security.json` when untrusted-input, high-risk,
  provenance, sandbox or honesty rules change.
- Update `AINP_Standard.ecosystem.json` when package, release or feedback-loop
  binding rules change.
- Update `ainp-rules-v1.0.0.json` when conformance rule IDs or rule summaries
  change.
