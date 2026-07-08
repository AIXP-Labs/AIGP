# Project Package

A complete distributable AINP project uses this layout:

```text
<name>_ainp/
├── AINP.md
├── ainp/
└── <name>/
```

`AINP.md` is the project declaration, index and validation entry point. `ainp/`
is the AINP plan folder for plan/report/feedback/space files. `<name>/` is the
project content folder for generated content. The plan folder and content
folder are co-equal parts of the package: one records the generation contract
and evidence, the other carries the generated artifacts. Feedback is required
for `approved` and `active` packages so content review can return to the same
plan generation id.

Project validation checks package wiring, side-file schema/rule consistency and
the release gate with the project root as artifact sandbox. It also requires
the plan's `content_architecture.root` and every declared content file path to
resolve under `AINP.md.content_dir`. Report artifacts bind back to those
declared content files through `file_id`, so accepted content is kept in the
content folder rather than the plan folder. For `approved` and `active`
packages, `AINP.md.feedback` must point to a matching
`*.generationfeedback.json`; feedback issues can target declared files or
points. It is not a trust certificate.

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
```

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
