# ADR-007: AINP Project Package Layout

Status: Accepted

## Context

AINP governs both generation plans and generated content. A repository-level
project needs a predictable shape so humans and tools can find the entry point,
the plans and the content without guessing.

## Decision

The canonical project package shape is:

```text
<name>_ainp/
├── AINP.md
├── ainp/
│   ├── project.ainp.json
│   ├── <artifact>.generation.json
│   ├── <artifact>.generationreport.json
│   └── <artifact>_feedback.generationfeedback.json
└── <name>/
    └── generated content
```

`AINP.md` is the human entry point. `ainp/` holds governance materials. The
content folder holds the generated artifact itself. The package manifest binds
those parts through relative paths and hashes.

## Consequences

The package is portable and inspectable on disk. Tools can validate containment,
required files, package status and content references without importing another
runtime model.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
