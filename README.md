# AINP — AI Neogenesis Protocol

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](VERSION)
[![Protocol](https://img.shields.io/badge/family-AIXP-7c3aed.svg)](https://aixp.dev)

[中文文档](README_CN.md) | English

[Specification](specification/AINP_Protocol.md) | [Quick Start](#quick-start) | [Examples](examples/README.md) | [Package Maintenance](docs/guides/package-maintenance.md) | [Integration Roadmap](docs/integrations/aixp-generation-lifecycle.md) | [Release Evidence](docs/reference/release-evidence-matrix.md) | [Validator Coverage](docs/reference/validator-coverage.md)

**AINP (AI Neogenesis Protocol) standardizes a complete generation project**:
the generation plan, the generated content, the evidence report that binds
them, and the feedback record that closes the loop. The plan is the
machine-readable, governable blueprint for creating *any*
content (documents, code, images, audio, video, datasets, landing pages, …):
what to create, under which constraints, and **what counts as done**. The
content is the generated artifact itself; in a complete AINP project package,
plan and content are different but co-equal first-class parts. The plan guides
content; content feedback flows back to the plan.

```
AIIP intent ─▶ AINP generation plan ─▶ AIJP job ─▶ artifact ─▶ AIKP knowledge
                ▲        │                                  all under HSAW / Axiom 0
                └────────┴── feedback from content
```

- **Plan ≠ artifact; both belong to the project.** A valid plan proves structure and declarations — never that the artifact is safe, original, true, or compliant. A complete project also carries the generated content and report-side evidence.
- **Plan guides content; content feeds back to plan.** Standalone plans may declare `content_architecture`; complete project packages must declare it so generated-content roots, files and per-file points are machine-bound. `approved`/`active` project packages also declare `AINP.md.feedback` and validate that the feedback record points back to the same generation id.
- **Acceptance lives in the report.** The plan sets criteria; evidence lands in `*.generationreport.json`, hash-locked to the exact plan snapshot it judged.
- **Red lines name their enforcers.** Every hard/safety/ip/approval/disclosure/privacy constraint carries an `enforced_by[]` control-point array with explicit assurance levels; `unverifiable` is an honest record, never a pass credential.
- **High-risk generation needs a human.** Likeness, biometrics, voice cloning, minors, medical/legal/financial advice, mass persuasion, election content, security exploits, mass-public distribution and any plan self-assessed `risk_level ∈ {high, critical}` all require the HSAW human sovereignty gate.
- **Disclosure can carry generator and watermark evidence.** A plan may require report-side generator identity metadata and watermark records; those records support transparency but are not trust certificates.
- **The plan is untrusted input.** Conforming tools never auto-execute bindings, never download inputs, never trust embedded hashes.

## File family

Canonical JSON Schemas and the versioned high-risk control data live in
`schemas/`. They are the machine-readable part of the AINP specification and are
indexed from `specification/schemas.md` / `specification/schemas_cn.md`; they are not duplicated under
`specification/`.

Machine-readable standards live in `specification/standards/`: `AINP_Standard.core.json`,
`AINP_Standard.security.json`, `AINP_Standard.ecosystem.json`, and the
`ainp-rules-v1.0.0.json` rule index. These are standard-library reference data,
not JSON Schema mirrors, AISOP flows, AIAP programs or runtime trust proofs.

The local release wrapper is stdlib-only and validates the bundled schemas with
the Draft 2020-12 keyword subset used in this repository, including the
composition/conditional keywords present in those schemas. The conformance
tests use `jsonschema` for full Draft 2020-12 schema validation.

AINP is the sole v1.0.0 public identifier. Reference tools validate only the
canonical AINP package shape, schema profiles, CLI names and finding-code
prefixes documented here.

| File | Profile | Purpose |
|---|---|---|
| `*.generation.json` | `ainp.v1.0.0.generation` | **The generation plan and acceptance contract** |
| `*.generationreport.json` | `ainp.v1.0.0.generationreport` | Acceptance evidence for one run |
| `*.generationfeedback.json` | `ainp.v1.0.0.generationfeedback` | Feedback from content review back to the plan |
| `*.ainp.json` | `ainp.v1.0.0.generation_space` | Index of plans |
| `ainp/references/reference_manifest.json` | `ainp.v1.0.0.reference_manifest` | Optional index for reference files, templates, briefs and snapshots |
| `high_risk_types.v1.0.0.json` | `ainp.v1.0.0.high_risk_types` | Versioned high-risk list (single source of truth) |

## Project package

A complete AINP project package is named `<name>_ainp/`. It contains the
project declaration, the AINP plan folder, and the project content folder.
The plan folder and content folder are co-equal: `ainp/` explains and records
the generation process; `<name>/` holds the generated content itself; feedback
records how content review returns to the plan.

```text
<name>_ainp/
├── AINP.md                 # project declaration, index and validation entry point
├── ainp/                   # AINP plan folder: plan, report, feedback, generation space
│   └── references/          # optional: protocol snapshots, templates, briefs, style guides
└── <name>/                 # project content folder: generated content itself
```

`AINP.md` must be uppercase (enforced by P2), matching AIAP's `AIAP.md` convention. It
is the project declaration, index, bootstrap document and validation entry
point. It is not a trust proof.

`ainp/` is the AINP plan folder. It stores the generation plan, generation
report, feedback and generation-space index. `<name>/` is the project content
folder. It stores the generated content itself. The plan's
`content_architecture` must describe that content folder with concrete file ids,
paths and points; report artifacts bind back to those file ids, and feedback can
target declared files or points. Project validation requires release report
artifacts and planned content paths to resolve under `AINP.md.content_dir`, so
accepted content cannot be silently placed back into the plan folder. For
`approved`/`active` packages it also requires `AINP.md.feedback` to exist and to
reference the same generation id as the plan and report.

`ainp/references/` is optional. Use it for generation reference materials such
as protocol/spec snapshots, templates, briefs, style guides, interface notes,
policy excerpts or research notes. If present, it should contain
`reference_manifest.json`; project checking validates that local entries remain
under `ainp/references/` and that recorded hashes recompute. These hashes prove
local integrity only, not external authority, freshness, legal sufficiency or
runtime trust. A standalone manifest can also be checked directly with
`tools/ainp_validate.py`; that still proves only structure and local integrity.
`external_uri` entries are recorded but not fetched, and cannot carry local
`sha256` anchors.

## Quick start

```bash
# quick local health check
python -B tools/ainp.py doctor --json

# run the local publication gate
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
# after installing dev dependencies, include pytest discovery as well:
python -m pip install "jsonschema>=4" "pytest>=8"
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest

# validate a plan (default | strict | release; the whitepaper example intentionally
# FAILs strict/release — a G9 missing-binding demo, see examples/README.md)
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release
python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json

# check a report against its plan (hash-locked)
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json
python -B tools/ainp_report_check.py examples/file_family/high_risk_likeness.generationreport.json --mode release

# full release gate (JSON Schemas + plan + report + artifact hashes + conformant report)
python -B tools/ainp_release_check.py examples/file_family/high_risk_likeness.generation.json \
    --report examples/file_family/high_risk_likeness.generationreport.json
python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json \
    --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json \
    --project-root examples/whitepaper_ainp

# check a complete AINP project package
python -B tools/ainp.py project-check examples/whitepaper_ainp
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B examples/aikp_navigator_aiap_ainp/aikp_navigator_aiap/tests/test_resolve_topic.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp

# breaking-change discipline (G12): acceptance changes require a MAJOR bump
python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json

# run the conformance + teeth suite
python -B tests/test_ainp.py
```

Optional documentation-site check:

```powershell
python -m pip install "mkdocs>=1.6" "mkdocs-material>=9"
$env:NO_MKDOCS_2_WARNING = "true"
python -B -m mkdocs build --strict
```

The release gate does not require MkDocs. The command installs only the docs
renderer dependencies so it does not create `*.egg-info/` package metadata in
the repository. `NO_MKDOCS_2_WARNING` suppresses the upstream Material for
MkDocs announcement so strict mode remains focused on this project's
documentation warnings.

Conforming validators output `PASS structure-valid` / `WARN external-verification-required` — and **never** `PASS legally-safe`, `PASS rights-verified`, or `PASS content-trusted`. Embedded hashes prove recomputable integrity only; content-credential, generator and watermark fields record external evidence but are not locally verified as cryptographic trust, provider trust or watermark detectability by the reference tools.

## Repository layout

```
AINP-Protocol/
├── specification/       AINP_Protocol.md + _cn.md + schema indexes + standards/
├── schemas/             normative machine-readable schemas + high-risk data
├── examples/            file_family/, bindings/ and complete <name>_ainp/ project packages
├── tools/               unified CLI, validators, release helpers, doc/link checks
├── scripts/             release_check.ps1 local publication gate
├── .github/             CI validation workflow
├── tests/               conformance suite + 36 fixture files (teeth + G12 positive twin)
├── adrs/                architecture decision records
└── docs/ docs_cn/       narrative docs (mkdocs)
```

## AIXP Labs [aixp.dev](https://aixp.dev)

AIXP Labs develops and maintains the following core projects:

| Project | Description | Website |
|---------|-------------|---------|
| [HSAW](https://hsaw.dev) | Human Sovereignty and Wellbeing — Axiom 0 white paper (foundation) | hsaw.dev |
| [AIZP](https://aizp.dev) | AI Zenith-Zero Protocol — runtime behavioral alignment | aizp.dev |
| [AILP](https://ailp.dev) | AI List Protocol — agent discovery and capability advertising | ailp.dev |
| [AIVP](https://aivp.dev) | AI Value Protocol — international commerce, crypto asset settlement | aivp.dev |
| [AIRP](https://airp.dev) | AI RMB Protocol — Mainland China commerce, RMB licensed settlement | airp.dev |
| [AIBP](https://aibp.dev) | AI Bot Protocol — social communication and trust | aibp.dev |
| [AIAP](https://aiap.dev) | AI Application Protocol — governance and compliance | aiap.dev |
| [AINP](https://ainp.dev) | AI Neogenesis Protocol — governable generation projects: plan + content + evidence **(this project)** | ainp.dev |
| [AISP](https://aisp.dev) | AI Skill Protocol — single-file skills with machine-enforced contract red lines | aisp.dev |
| [AISOP](https://aisop.dev) | AI Standard Operating Protocol — flow program definition | aisop.dev |
| [SoulSkill](https://soulskill.dev) | AISP skill reference library & multi-CLI plugin distribution | soulskill.dev |
| [SoulAgent](https://soulagent.dev) | Drop-in AI agent invoked directly by any CLI / SDK / IDE | soulagent.dev |
| [SoulBot](https://soulbot.dev) | AI agent runtime & orchestration framework (scheduling, agent-spawn, inter-agent comms) | soulbot.dev |
| [SoulACP](https://soulacp.dev) | Adapter library — bridging CLI tools and LLM providers | soulacp.dev |

## Disclaimer

This specification and its reference tooling are **experimental** and provided for research and educational purposes. AINP validation is **not** legal compliance certification; passing validation proves structural consistency only. See [SECURITY.md](SECURITY.md) for the untrusted-input rules and [LICENSE](LICENSE) for Apache-2.0 terms.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
