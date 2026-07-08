# AINP Schema Index

This page indexes the normative machine-readable schema files for AINP v1.0.0.
Chinese companion: `specification/schemas_cn.md`.

The canonical files live in the top-level `schemas/` directory. They are part of
the AINP specification, but they are not duplicated under `specification/` so the
repository keeps one machine-readable source of truth.

## Canonical Files

| File | Profile | Purpose |
|---|---|---|
| `schemas/ainp-generation-v1.0.0.schema.json` | `ainp.v1.0.0.generation` | Generation plan schema |
| `schemas/ainp-generationreport-v1.0.0.schema.json` | `ainp.v1.0.0.generationreport` | Generation report schema |
| `schemas/ainp-generationfeedback-v1.0.0.schema.json` | `ainp.v1.0.0.generationfeedback` | Content-review feedback schema |
| `schemas/ainp-generation-space-v1.0.0.schema.json` | `ainp.v1.0.0.generation_space` | Generation-space index schema |
| `schemas/ainp-reference-manifest-v1.0.0.schema.json` | `ainp.v1.0.0.reference_manifest` | Optional `ainp/references/` manifest schema for reference files, templates and snapshots |
| `schemas/high_risk_types-v1.0.0.schema.json` | `ainp.v1.0.0.high_risk_types` | High-risk control-data schema |
| `schemas/high_risk_types.v1.0.0.json` | `ainp.v1.0.0.high_risk_types` | Versioned high-risk control data |

## Authority

- `specification/AINP_Protocol.md` defines the normative semantics.
- `schemas/` defines the normative machine-readable shapes used by tools and
  tests.
- `specification/standards/AINP_Standard.core.json`,
  `AINP_Standard.security.json`, `AINP_Standard.ecosystem.json`, and
  `ainp-rules-v1.0.0.json` provide lightweight standard-library reference data
  for dashboards and tooling. They are not schema mirrors and not runtime flows.
- This file is an index only. It must not become a second copy of the schemas.

## Maintenance Rule

When a schema changes, update the canonical file in `schemas/`, update the
protocol text and tests as needed, and keep this index accurate. Do not add
schema mirrors under `specification/`.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
