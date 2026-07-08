# What Is AINP?

AINP is the AI Neogenesis Protocol. It standardizes a complete generation
project: the generation plan, the generated content, and the evidence report
that binds them, plus the feedback record that closes the loop. The plan is the
machine-readable, governable blueprint for creating content: it includes
`content_architecture`, which declares the content root, files and per-file
points. Content feedback returns structured review to the plan.

AINP does not claim that generated content is safe, original, true or legally
compliant. It defines what is requested, which constraints govern the work,
where generated content belongs in a project package, and what evidence must be
recorded before a result can be treated as accepted or revised.

## Boundary

```text
AIIP intent -> AINP generation plan -> AIJP job -> artifact -> AIKP knowledge
```

- The intent says what is wanted.
- The AINP plan defines the artifact shape, content file architecture and acceptance contract.
- The job executes work.
- The artifact is the generated content.
- The knowledge layer may retain vetted results later.

## Core Units

| Unit | Role |
|---|---|
| `*.generation.json` | The plan and acceptance contract |
| `*.generationreport.json` | Evidence and verdicts for one run |
| `*.generationfeedback.json` | Content review fed back to the plan |
| `*.ainp.json` | Generation-space index |
| `<name>_ainp/AINP.md` | Project declaration and validation entry point |
| `<name>_ainp/<name>/` | Generated content folder for accepted artifacts |

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
