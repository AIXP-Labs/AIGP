# AINP File-Family Examples

This directory contains standalone AINP file-family examples. They are not a
complete project package; use `../whitepaper_ainp/` for the canonical document
package and `../slugify_cli_ainp/` for the canonical small program package.

| File | Purpose |
|---|---|
| `whitepaper.generation.json` | Low-risk document generation plan with `content_architecture` and intentional G9 binding-target WARN in default mode |
| `whitepaper.generationreport.json` | Hash-locked report for the whitepaper plan; structurally valid but not releasable because `overall.conformant=false` |
| `out/whitepaper.md` | Recomputable artifact for the flat report |
| `whitepaper_feedback.generationfeedback.json` | Feedback record that returns the failed content review to a declared content point in the plan |
| `project.ainp.json` | Generation-space index covering the flat plans |
| `high_risk_likeness.generation.json` | HSAW approval, consent and disclosure gate example |
| `high_risk_likeness.generationreport.json` | Release-grade evidence example for likeness generation, including approval gate, disclosure and content-credential records |
| `high_risk_likeness_feedback.generationfeedback.json` | Feedback record for the likeness example; records evidence boundaries rather than trust proof |
| `out/g_portrait_illustration.png` | Recomputable image artifact for the high-risk likeness report |
| `landing_page.generation.json` | `mass_public` deployment approval gate example |
| `dataset.generation.json` | Synthetic dataset plan with external provenance boundary |
| `medical_advice.generation.json` | Regulated-domain medical education example with approval and disclosure gates |
| `security_exploit.generation.json` | Defensive security lab example with approval and abuse-prevention red lines |

Example:

```bash
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json --mode release
```

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
