# Security Model

AINP treats every plan, report and generation-space file as untrusted input.
Validation proves structure and local evidence-chain consistency only.

## Main Risks

| Risk | AINP control |
|---|---|
| Prompt injection in plan text | Text is data; tools do not execute instructions from fields |
| Path traversal in report artifacts or space refs | Realpath/common-path sandbox checks |
| Hash oracle against local files | Absolute and escaping paths are rejected before hashing |
| Findings flood or deep nesting | Size, nesting and findings limits |
| Self-declared trust | `safe`, `verified`, `trusted`, `original`, `authentic` keys are rejected where applicable |
| High-risk generation without human gate | G6 approval requirement and report-side R9 evidence |
| Generator or watermark evidence overclaim | R7 records required generator/watermark evidence but never treats it as provider trust or watermark verification |

## Honesty Boundary

The reference tools never prove rights validity, consent authenticity, factual
truth, scanner reliability, provider trust, watermark detectability, legal
compliance or content trust. Those are external verification and governance
questions.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
