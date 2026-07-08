# Getting Started

Install the test dependency if you want to run the full suite:

```bash
python -m pip install -e ".[dev]"
```

Install the optional documentation dependencies only when rendering the MkDocs
site:

```bash
python -m pip install "mkdocs>=1.6" "mkdocs-material>=9"
NO_MKDOCS_2_WARNING=true python -B -m mkdocs build --strict
```

Run the local publication gate:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
```

Validate a standalone plan:

```bash
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release
```

Check a report:

```bash
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json
```

Run a full project release gate:

```bash
python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp
```

Check the package wrapper:

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
```

Run the tests:

```bash
python -B tests/test_ainp.py
```

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
