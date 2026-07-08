# AIAP Package Template

Use this template when generating a minimal AIAP-style package as AINP content.

Required generated files:

1. `AIAP.md` — package declaration and honesty boundary.
2. `agent_card.json` — package identity, summary and capabilities.
3. `main.aisop.json` — candidate flow descriptor, without execution claims.
4. `README.md` — how to run, how to test and boundary notes.
5. `tools/<tool>.py` — stdlib-only helper code when needed.
6. `tests/test_<tool>.py` — local unit tests for generated helper behavior.

Template rules:

- Keep runtime claims separate from generation evidence.
- Keep all generated content under `AINP.md.content_dir`.
- Declare every generated file in `generation.content_architecture.files[]`.
- Bind every required generated file back through
  `generationreport.artifacts[].file_id`.
- State that AINP validation is not AIAP runtime certification.

Boundary: this template is guidance for generation only. It is not generated
content, not runtime proof and not a trust certificate.
