# AINP — AI Neogenesis Protocol

AINP (AI Neogenesis Protocol) standardizes a **complete generation project**:
the generation plan, the generated content, and the evidence report that binds
them, plus the feedback record that closes the loop. The plan says what to
create, under which constraints, and what counts as done; the content folder
carries the generated artifact itself; `content_architecture` declares the
content files and points; content feedback flows back to the plan.

- Normative specification: `specification/AINP_Protocol.md`
- Schemas: `schemas/` (normative machine-readable spec, indexed by `specification/schemas.md`) · Examples: `examples/file_family/`, `examples/whitepaper_ainp/`, `examples/slugify_cli_ainp/` and `examples/aikp_navigator_aiap_ainp/` · Reference tools: `tools/`
- Release evidence: `docs/reference/release-evidence-matrix.md` · Validator coverage: `docs/reference/validator-coverage.md`
- Integration roadmap: `docs/integrations/aixp-generation-lifecycle.md`
- Package maintenance: `docs/guides/package-maintenance.md`
- Chinese documentation: `docs_cn/` and `README_CN.md`

Complete distributable projects use the canonical package layout:

```text
<name>_ainp/
├── AINP.md                 # project declaration, index and validation entry point
├── ainp/                   # AINP plan folder
└── <name>/                 # project content folder
```

`AINP.md` is intentionally uppercase, matching AIAP's `AIAP.md` convention. It is
the project declaration, index and validation entry point, not a trust
certificate. `ainp/` stores the plan/report/feedback/space files; `<name>/`
stores the generated content itself. Project validation also requires planned
content paths and report artifacts to live under the declared content directory,
and feedback to reference the same generation id as the plan and report.

Project package check:

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp
```

Key ideas: plan ≠ artifact · content architecture is required · plan guides content · content feedback flows back to the plan · acceptance evidence lives in the hash-locked report · red lines name their enforcers · unverifiable is never a pass credential · high-risk generation requires a human (HSAW / Axiom 0) · generator/watermark records are evidence, not trust certificates · the plan is untrusted input.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
