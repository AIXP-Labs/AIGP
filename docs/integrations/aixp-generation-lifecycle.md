# AIXP Generation Lifecycle Integration Roadmap

This page is a non-normative integration roadmap. The normative AINP contract is
still `specification/AINP_Protocol.md`; this page explains how adjacent tools can
use AINP without importing their runtime semantics into the protocol.

## Lifecycle

```text
AIIP intent
  -> AINP generation project
  -> AIJP work plan
  -> AISOP / AIAP / AISP execution
  -> generated content
  -> AINP report
  -> AINP feedback
  -> AIKP knowledge retention
```

The binding direction is intentionally reference-based:

- AIIP may point to an AINP plan.
- AINP may point to candidate AIJP/AISOP/AISP/AIAP execution records.
- AIJP may derive jobs from AINP `content_architecture` and acceptance criteria.
- AINP reports bind generated artifacts back to the plan.
- AIKP may cite AINP report evidence as provenance for retained knowledge.

Bindings are never auto-executed by AINP reference tools.

## AIAP Creator

AIAP Creator can use AINP to govern generation of an AIAP package:

```text
<name>_aiap_ainp/
├── AINP.md
├── ainp/
│   ├── <name>.generation.json
│   ├── <name>.generationreport.json
│   ├── <name>_feedback.generationfeedback.json
│   └── project.ainp.json
└── <name>_aiap/
    ├── AIAP.md
    ├── agent_card.json
    ├── main.aisop.json
    ├── tools/
    └── tests/
```

Recommended minimum:

1. Derive `content_architecture` from the files AIAP Creator will generate.
2. Write acceptance criteria before generation starts.
3. Run AIAP package tests outside AINP.
4. Record test and file evidence in `*.generationreport.json`.
5. Record review outcomes in `*.generationfeedback.json` before marking the
   project `approved` or `active`.

AINP does not certify the AIAP package as safe or compliant. It records the
generation contract and evidence chain.

See `examples/aikp_navigator_aiap_ainp/` for a complete checked example package
with `AINP.md`, `ainp/` plan/report/feedback files, generated `AIAP.md`,
`agent_card.json`, `main.aisop.json`, helper tool, tests and README.

## SoulIDE

SoulIDE can make AINP visible as a project-side governance surface:

- show `AINP.md` as the generation project entry point;
- show the `ainp/` plan/report/feedback folder separately from the generated
  content folder;
- run `python -B tools/ainp.py doctor --json` and display structural results;
- warn users that `structure-valid` is not content trust;
- help refresh hashes with `ainp rehash` only after content edits.

SoulIDE should not execute AINP bindings automatically.

## SoulBot

SoulBot can orchestrate generation workflows around AINP:

- create or update an AINP plan before generation tasks start;
- schedule human approval gates for high-risk plans;
- run project checks after artifact generation;
- attach report and feedback paths to a run log;
- prevent an `approved` or `active` package without feedback alignment.

SoulBot should treat AINP files as untrusted input and should require explicit
authorization before executing any referenced external job, tool or runtime.

## Example Files

See `examples/bindings/` for small non-normative JSON examples:

- AIIP intent to AINP plan;
- AINP plan to AIJP job outline;
- AINP report to AIKP ingestion;
- AIAP Creator run governed by AINP.

See `examples/aikp_navigator_aiap_ainp/` for the corresponding complete project
package form.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
