# First AINP Project

Start with a project folder named `<name>_ainp/`.

```text
<name>_ainp/
├── AINP.md
├── ainp/
│   ├── <name>.generation.json
│   ├── <name>.generationreport.json
│   ├── <name>_feedback.generationfeedback.json
│   └── project.ainp.json
└── <name>/
    └── content files
```

Use `examples/whitepaper_ainp/` as the canonical document package example and
`examples/slugify_cli_ainp/` as the canonical small program package example.

Minimum workflow:

1. Write the plan in `ainp/<name>.generation.json`, including
   `content_architecture.root`, concrete content files and each file's points.
2. Generate content into `<name>/`.
3. Record acceptance results and artifact hashes in the report, with artifacts
   linked to planned files through `file_id`.
4. Record content review feedback in `ainp/<name>_feedback.generationfeedback.json`,
   optionally targeting declared `file_id` / `point_id` values.
5. Add `AINP.md` with project-root-relative paths, including `feedback`.
6. Run the project check.

The plan guides the content through `content_architecture` and acceptance
criteria. The feedback file returns content review to the same plan generation
id so the next plan revision has structured evidence.

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
```

For release, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
```

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
