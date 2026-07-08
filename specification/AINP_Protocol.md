# AINP — AI Neogenesis Protocol · Specification v1.0.0

Status: **v1.0.0** (initial release). Normative source of truth for the AINP file family, conformance rules, governance gates and honesty boundaries.

---

## 1. Overview and positioning

**AINP (AI Neogenesis Protocol) standardizes a complete generation project**:
the generation plan, the generated content, and the evidence report that binds
them, plus the feedback record that closes the loop. The plan is a
machine-readable, governable blueprint for creating *any* content — what to
create, under which constraints, and **what counts as done**. The plan is never
the content itself, but a complete AINP project package contains both
first-class sides: the plan/evidence folder and the generated content folder,
with feedback linking content review back to the plan.

Ecosystem chain (all under HSAW / Axiom 0):

```
AIIP intent  ─▶  AINP generation plan  ─▶  AIJP job  ─▶  artifact  ─▶  AIKP knowledge
 (why/what)      (blueprint + acceptance     (work)                     (retained
                  contract)                                              knowledge)
```

Boundary identities: **plan ≠ intent ≠ job ≠ program ≠ artifact.** Package
identity: **AINP project = declaration + plan/evidence folder + content
folder + feedback loop**. The plan guides content through structure,
constraints and acceptance criteria; generated content feeds back to the plan
through `*.generationfeedback.json`. The distinction prevents false trust
claims; it does not demote generated content to an optional afterthought.

- vs **AIIP**: intent says *what is wanted*; AINP says *what the thing looks like and when it is acceptable*.
- vs **AIJP**: AIJP schedules the work; AINP is the drawing the work implements.
- vs **AISOP/AISP**: those are execution languages/skills; an AINP plan may be realized by any of them.
- The plan is a **first-class reviewable, versionable artifact** that may exist without ever being executed.
- In a distributable `<name>_ainp/` package, the generated content is also a **first-class project component**; the report links the plan to concrete content artifacts.
- Feedback is the reverse edge: it records content-side review back to the same generation id so the next plan revision has structured evidence to act on.

## 2. Axiom 0

AINP aligns to **Axiom 0: Human Sovereignty and Wellbeing** (owned by HSAW, not by AINP). Concretely: high-risk generation requires a human approval gate (G6); consent-required inputs require recorded evidence (G4); red-line constraints must name their enforcers (G11); unverifiable enforcement can never satisfy a red line in strict/release (G14/G15); artifacts and package declarations must not self-declare trust (G7/P9); disclosure is mandatory where declared or tag-required (G8).

## 3. Terms — single source of truth

All rules in this specification reference the enums below. **Closed enums** are enforced by JSON Schema `enum`; **suggested enums** are open strings on which validators emit `WARN` for unknown values (`FAIL` in strict).

Closed:

```text
REDLINE_TYPES    = { hard, safety, ip, approval, disclosure, privacy }
CONSTRAINT_TYPES = REDLINE_TYPES ∪ { soft }        # soft = style/preference; no enforcement gates
ASSURANCE        = { static, runtime, evidence_recorded, external_required,
                     externally_verified, attested, unverifiable }
STAGE            = { plan_validation, generation_runtime, report_check,
                     distribution_gate, external_review }
RIGHTS_STATUS    = { owned, licensed, public_domain, open_license, public_reference,
                     user_provided, consent_required, consent_recorded, unknown,
                     external_verify_required }
PROVENANCE_STATUS= { unverified, retrieved, external_verify_required, externally_verified }
DEPLOYMENT_SCOPE = { internal_draft, limited, public, mass_public }
RISK_LEVEL       = { low, medium, high, critical }
STATUS           = { draft, under_review, approved, active, superseded, retired }
ORIGIN           = { human, agent, hybrid }                # generation.source
FEEDBACK_SOURCE  = { human, agent, consumer }
CONSENT_STATUS   = { not_required, pending, recorded, verified, expired, revoked }
                   # generation may proceed only on: recorded | verified
CONSENT_SCOPE    = { single_generation, project, time_bounded }
VERDICT          = { accept, revise, reject }
SEVERITY         = { fail, warn, info }
VERIFICATION_METHOD = { static, external, human }
EXECUTION_PROTOCOLS = { AISOP, AISP, AIJP, external, none }
MODES            = { default, strict, release }
```

Suggested (open, validator-advisory):

```text
ARTIFACT_TYPES_SUGGESTED = { document, code, image, audio, video, dataset,
                             design, landing_page, campaign, 3d, mixed }
STRUCTURE_KIND_SUGGESTED = { section, subsection, component, module, scene, asset }
```

Registered static `check_id` values (G5): `structure.sections_nonempty`, `inputs.rights_declared`, `length.within_bounds`, `disclosure.policy_declared`.

## 4. File family, naming and versioning

| profile (`schema`, underscore) | payload key | schema file (hyphen) |
|---|---|---|
| `ainp.v1.0.0.generation` | `generation` | `ainp-generation-v1.0.0.schema.json` |
| `ainp.v1.0.0.generationreport` | `generationreport` | `ainp-generationreport-v1.0.0.schema.json` |
| `ainp.v1.0.0.generationfeedback` | `generationfeedback` | `ainp-generationfeedback-v1.0.0.schema.json` |
| `ainp.v1.0.0.generation_space` | `generation_space` | `ainp-generation-space-v1.0.0.schema.json` |
| `ainp.v1.0.0.reference_manifest` | `reference_manifest` | `ainp-reference-manifest-v1.0.0.schema.json` |
| `ainp.v1.0.0.high_risk_types` | — (data file) | `high_risk_types.v1.0.0.json` + `high_risk_types-v1.0.0.schema.json` |

Schema discipline: every schema uses `additionalProperties: false`; the `schema` string and the payload key are **strongly bound** (G1/R1/FB1/SP1). The canonical machine-readable schema files live in the top-level `schemas/` directory and are indexed by `specification/schemas.md` / `specification/schemas_cn.md`; they are part of this specification, but are not duplicated under `specification/` to avoid drift. Those canonical schemas are Draft 2020-12 schemas. Full Draft 2020-12 behavior is verified by the test suite through `jsonschema`; the stdlib schema gate embedded in `tools/ainp_release_check.py` is intentionally a bundled-schema keyword subset, including the composition/conditional keywords used by those bundled schemas, not a general JSON Schema validator. The full release wrapper enforces that bundled schema gate for plan/report/high-risk data before running release-mode rule checks. Family version tokens are lowercase `v1.0.0` (AISOP `V1.0.0` is a declared historical exception).

`specification/standards/` contains lightweight machine-readable standard-library
references: `AINP_Standard.core.json`, `AINP_Standard.security.json`,
`AINP_Standard.ecosystem.json`, and `ainp-rules-v1.0.0.json`. These files index
core semantics, security boundaries, ecosystem/package requirements and rule
families for dashboards and tooling. They do **not** mirror JSON Schemas, and
they are not AISOP flows, AIAP programs, runtime extensions or trust proofs.

**Plan versioning** (`generation.version`, required, semver):

- **MAJOR** — any add/remove/change of `acceptance_criteria` or of any red-line (`type ∈ REDLINE_TYPES`) constraint: the "what counts as done" predicate flips, invalidating prior report correspondence. Machine-enforced by G12 (version-diff mode) and closed by R8 (`plan_ref` hash lock).
- **MINOR** — brief/structure/soft constraint adjustments.
- **PATCH** — typos, descriptions.

### 4.1 AINP project package

The file family remains valid as standalone files, but a complete distributable
AINP project package MUST use this layout:

```text
<name>_ainp/
├── AINP.md                 # project declaration, index and validation entry point
├── ainp/                   # AINP plan folder: plan, report, feedback, generation space
│   └── references/          # optional: reference materials, templates, briefs, spec snapshots
└── <name>/                 # project content folder: generated content itself
```

`AINP.md` intentionally follows AIAP's uppercase `AIAP.md` convention. It is a
project declaration, index, human/AI bootstrap document and validation entry
point; it is **not** a trust certificate. `ainp/` is the AINP plan folder:
it stores the generation plan, generation report, feedback and generation-space
index, plus optional reference materials. `<name>/` is the project content
folder: it stores the generated content itself. The plan folder and content
folder are co-equal parts of the package:
`ainp/` describes, constrains and records the generation; `<name>/` carries the
content that was generated. Required frontmatter fields: `protocol`, `authority`, `axiom_0`,
`name`, `version`, `summary`, `status`, `plan_dir`, `content_dir`, `plan`,
`report`. `feedback` is required for `status ∈ {approved, active}` packages
and optional for draft/under-review packages. Recommended fields: `space`,
`references`, `artifact_type`, `license`.
The body SHOULD include: `Project Declaration`, `Generation Plan`, `Content
Artifacts`, `Feedback Loop`, `How To Validate`, and `Honesty Boundary`.

`ainp/references/` is optional. It MAY contain generation reference materials:
protocol/spec snapshots, templates, briefs, style guides, interface notes,
policy excerpts, research notes and similar inputs that informed the plan.
These files are not generated content and MUST NOT be counted as content
artifacts under `AINP.md.content_dir`. If the directory exists, it SHOULD
contain `reference_manifest.json` using profile
`ainp.v1.0.0.reference_manifest`; `AINP.md.references` MAY point to that
manifest. P11 treats a missing manifest as a warning, but once a manifest is
declared or present, local reference/template paths MUST remain under
`ainp/references/`, local hashes MUST match when recorded, and the manifest
MUST pass its schema. `tools/ainp_validate.py` MAY validate the standalone
manifest; `tools/ainp_project_check.py` validates package placement and
`AINP.md.references` wiring. `source.type=local_file` entries use `source.path`
and MAY carry `sha256`; `source.type=external_uri` entries use `source.uri`,
are never fetched by local tools and MUST NOT carry `sha256`. Reference hashes
prove local integrity only; they do not prove external authority,
latest-version freshness, legal sufficiency, factual truth or runtime trust.

In a project package, `generationreport.artifacts[].path` is project-root
relative. A project checker may pass the package root as the release artifact
sandbox; without that explicit project-root context, report checkers default to
the report directory as their sandbox. Project-package validation additionally
requires each report artifact path that resolves inside the package root to live
under the content directory declared by `AINP.md.content_dir`; malformed or
escaping paths still fail under R3/release sandbox rules.

The complete package loop is bidirectional. The plan guides content through the
declared brief, `content_architecture`, constraints and acceptance criteria.
`content_architecture` is the declarative content-project blueprint: it names
the generated-content root, directories, concrete files and per-file
points/requirements. It is not an AISOP-style execution graph and does not make
runtime claims. For approved/active packages, the content feeds back to the plan
through `AINP.md.feedback`, which MUST point to a `*.generationfeedback.json`
file under `ainp/` whose `generation_id` matches the plan id and report
`generation_id`. This proves loop wiring only; it does not prove the feedback
is wise, complete or externally true.

## 5. Generation plan (`*.generation.json`)

See `schemas/ainp-generation-v1.0.0.schema.json` for the normative machine-readable shape, `specification/schemas.md` for the schema index, `examples/file_family/` for standalone file-family instances, `examples/whitepaper_ainp/` for a complete document project package, `examples/slugify_cli_ainp/` for a complete program project package and `examples/aikp_navigator_aiap_ainp/` for a complete AIAP package-generation example. Field groups: identity (`id/version/title/summary/status/source`), `artifact_type(+subtype)`, `brief`, `audience`, `structure[]` (recursive), `content_architecture`, `inputs[]` (`source` / `rights` / `provenance` / `privacy` / `consent`), `rights_policy`, `risk_profile`, `constraints[]`, `acceptance_criteria[]`, `disclosure_policy`, `bindings`, `governance`, `permission`.

Key semantics:

- **`risk_profile` is the single source of truth for risk.** `governance.risk_level` is a derived family-compatibility field and must match (G13). The gate decision reads **only** `governance.approval_required`.
- **`structure[]` is an advisory human-readable outline.** It helps authors and reviewers navigate the intended artifact shape, but it is not a coverage gate. Machine-bound content anchors live in `content_architecture.files[].points[]`, and those points bind to acceptance through `acceptance_refs[]`.
- **`content_architecture` is optional for standalone plans and required for complete project packages.** It declares `root`, optional `directories[]`, and concrete `files[]` with `id/path/type/required/summary/points[]`. Each point carries ordered `requirements[]` and may link to `acceptance_criteria` via `acceptance_refs[]` (G16/P10). This is a content blueprint, not an execution plan; generation may be implemented by AISOP, AISP, AIJP or another authorized pipeline.
- **`intended_audience` is advisory free text in v1.0.0** — not part of gate judgment. Minor/vulnerable-audience risk is expressed through `risk_tags` (e.g. `minor_related`).
- **`consent`** (per input): when `required=true`, generation may proceed only with `status ∈ {recorded, verified}` **and** a non-empty `evidence_ref` (G4). Declaring `rights.status = consent_required` on an input requires that same input to carry `consent.required == true` (G4) — "consent needed" without a record is never permission to proceed. Validators prove consent is *declared with evidence references* — never that consent is real or valid (external/registry/human verification).
- **`provenance`** (per input) is declared or evidence-referenced status, not a full lineage proof. `provenance.status=externally_verified` records that an external verifier was referenced; it does not by itself prove source authenticity or a complete W3C PROV-style graph. Input `sha256` values are recomputation anchors only, never trust credentials.
- **Constraints** carry `type ∈ CONSTRAINT_TYPES`. Red-line constraints (`type ∈ REDLINE_TYPES`) must name their enforcers via a **control-point array** `enforced_by[] = {stage, mechanism, assurance, limitations}` (G11). `soft` constraints are schema-legal preferences with no enforcement gates.
- **`condition` is declarative text in v1.0.0**: validators check existence only and never evaluate it. Machine gate judgment is carried by G6 via `risk_profile`. A controlled `condition_id` registry is deferred to a future version.
- **`bindings` are candidate paths, never auto-executed** (§8). `execution_binding.protocol ∈ EXECUTION_PROTOCOLS`; plan-valid ≠ target trusted. Local, non-URI targets are stat-checked for existence (G9, WARN → strict FAIL); URI-form and `external/none` targets are external-verification territory.
- **`disclosure_policy` is a report gate map.** When `generator_metadata_required=true`, the report must record `generator.{provider, system, content_id, generated_at}`. When `watermark_required=true`, the report must record at least one present watermark with a scheme in `disclosure.watermarks[]`. These are evidence records for downstream transparency; they do not prove provider trust, watermark robustness or regulatory compliance.

**Assurance matrix** — control-point effect by mode. Final constraint verdicts are still produced by G14/G15:

| assurance | default | strict | release |
|---|---|---|---|
| static | counts for G14 | counts for G14 | counts for G14, but G15 still requires one operational control point |
| runtime / evidence_recorded / externally_verified | ✅ | ✅ | ✅ |
| external_required | counts for G14 | WARN; does not satisfy a red line by itself | FAIL if no operational control point also exists (G15) |
| attested | WARN; does not satisfy a red line by itself | WARN; does not satisfy a red line by itself | FAIL if no operational control point also exists (G15) |
| **unverifiable** | **WARN** | **FAIL** | **FAIL** |

Cell semantics are **control-point level** ("does this control point count"); the **constraint-level** verdict is produced by rules. G14 catches red lines with no satisfying control point for the selected mode and emits `AINP_W_G14_NO_SATISFYING_CONTROL` when non-operational evidence is recorded but insufficient. G15 catches release-mode red lines lacking any operational (`runtime | evidence_recorded | externally_verified`) control point and emits `AINP_E_G15_NO_OPERATIONAL_CONTROL`. `external_required`, `attested` and `unverifiable` are honest records, never pass credentials.

## 6. Generation report (`*.generationreport.json`)

Acceptance verdicts live **in the report, never in the plan**. The report locks the exact plan snapshot it judged via `plan_ref.sha256` (R8). Every `acceptance_results[]` entry carries `passed / method / evidence[] / verifier / limitations` with legal method/verifier/evidence shape (R5) and corresponds 1:1 with the plan's criteria (R4). `overall.conformant` is **derived** — all fail-severity criteria passed AND all mandatory gates satisfied — and may never be self-set (R6).

Mandatory report gates are explicit, not inferred from prose: every true `disclosure_policy.*_required` switch must be recorded as satisfied in the report (R7). This includes `report.disclosure` records for labels, machine-readable metadata, content credentials and watermarks, plus `report.generator` records when generator metadata is required. Any plan with `governance.approval_required == true` must carry `governance_results.approval_gate` with method/evidence/verifier/limitations and `passed=true` (R9). These records are still evidence containers: they record who/what claimed the gate passed; they do not independently prove legal authority, consent validity, provider trust, watermark detectability or credential authenticity.

Report honesty boundary: the report is an **evidence container, not absolute truth**. Tool verifiers prove only what the tool actually checked; human/external verifiers are recorded with identity/source/version/time. `content_credential.present=true` records that a credential or manifest reference is present; `verification_status=externally_verified` records external verification evidence, not local cryptographic trust. The AINP reference tools do not validate C2PA manifests, signatures, certificate chains, issuer policies or trust lists.

If the judged plan declares `content_architecture`, report artifacts SHOULD
carry `file_id` values pointing to `generation.content_architecture.files[].id`.
R10 requires every `required=true` content file to be covered by an artifact and
requires `file_id` + `path` to match the plan. This proves plan/report content
coverage only; it does not prove artifact quality or truth.

## 7. Governance, high-risk gates and the five honesty principles

**High-risk definition**: `artifact_type ∈ high_risk_types.artifact_types` ∪ `risk_tags ≠ ∅` ∪ `deployment_scope = mass_public` ∪ `risk_profile.risk_level ∈ {high, critical}` ⇒ `governance.approval_required` MUST be `true` and delivery MUST pass the HSAW human sovereignty gate (G6). Type membership is matched after **case/separator normalization** — whitespace, `_` and `-` separators are ignored, so `"Deepfake"` / `"deepfake "` / `"deep fake"` / `"deep-fake"` / `"deep_fake"` must not slip past the sovereignty gate on spelling (risk tags stay exact-match: an unknown tag is already a hard FAIL, fail-closed). Risk tags are **declared**; omission is not statically detectable — external review is the backstop. The `high_risk_types` data file itself must keep `artifact_types[]` and `risk_tags[]` non-empty; malformed or empty control data fails closed.

**Risk-tag trigger-bit → field enforcement mapping** (bits live in `high_risk_types.v1.0.0.json`):

| tag bit | enforced field | rule |
|---|---|---|
| `approval_required: true` | `governance.approval_required == true`; report records `governance_results.approval_gate` before release | G6 + R9 |
| `consent_required: true` | ≥ 1 `inputs[]` with `consent.required == true` | G4 |
| `disclosure_required: true` | `disclosure_policy.ai_generated_disclosure_required == true` | G8 |

**Five honesty principles** (inherited across the AIXP family):

1. **Plan ≠ artifact** — a valid/approved plan is a declaration of intent-to-create, never proof the artifact is safe/original/true/harmless.
2. **Self-report ≠ verification** — rights, consent, provenance and factuality are declared; hashes prove local integrity only.
3. **Acceptance lives in the report, not the plan** — the plan sets criteria; evidence lands in `*.generationreport.json`.
4. **Artifacts and package declarations must not self-declare trust** — `safe/verified/original/trusted/authentic` marks are assigned by consumers/registries/reviewers only (G7/P9). *G7/P9 are static exact-lowercase-key approximations: they can be evaded by changing key names or case variation; genuine trust is always a consumer/registry judgment, never a static pass.*
5. **Approval covers only its object** — approving a plan ≠ approving its artifacts; `report.conformant = true` ≠ the plan was ever approved. Two independent status chains; consumers must check both.

## 8. Security — the plan is untrusted input

Generation plans cross trust boundaries (stores, registries, agent-to-agent transfer). Tooling MUST:

1. **Never auto-execute `bindings`** — they are candidate paths requiring independent authorization.
2. **Never auto-download or open `inputs[].source`** URIs; never expand `local://`.
3. **Never trust embedded `sha256` values** — always recompute and compare.
4. **Never generate/publish merely because a plan is valid** — valid means structurally consistent, nothing more.
5. **Treat prompt-injection text, path traversal and oversized fields as data, not instructions.** Reference tools reject files over 10 MB and only `stat()` binding targets.
6. **Parse strictly.** Reject duplicate object keys (parser-differential smuggling: a human reviews one value while a machine acts on the other), non-standard JSON literals (`NaN`/`Infinity`), and nesting deeper than 150 levels — hostile input must yield a controlled finding, never a crash.
7. **Bound your output.** A hostile file must not flood findings without limit (reference tools truncate at 1000 findings with an explicit truncation FAIL) — exhausting memory on untrusted input is a crash, not a verdict.
8. **Never read outside your sandbox.** Any local hash recompute MUST refuse paths that are absolute or escape the active artifact sandbox. This applies to release-mode report artifacts (R3) and generation-space refs (SP2). The default report sandbox is the report's own directory; for a validated AINP project package it may be the package root passed by `tools/ainp_project_check.py`. Implementations SHOULD resolve with real paths and a common-path check so symlinks, junctions and `..` cannot smuggle reads outside the sandbox. An escape path plus hash comparison would otherwise act as a content oracle for arbitrary local files.

This section is normative and mirrored in `SECURITY.md`.

## 9. Feedback and generation space

`*.generationfeedback.json` (FB1): `generation_id / source ∈ FEEDBACK_SOURCE / verdict ∈ VERDICT` (+ issues with `target: plan|artifact|file|point`, `severity ∈ SEVERITY`, optional `file_id` / `point_id`). Closes the plan → content → feedback → revise loop. In standalone file-family use it may be optional; in `approved` or `active` `<name>_ainp/` project packages it is REQUIRED by P6 so content review has a structured path back to the plan and may point to declared content files/points.

`*.ainp.json` generation space (SP1/SP2): an index whose entries carry `ref + sha256`. The hash proves **registration-time** integrity only; consumers must re-hash when the ref is local and inside the space-file sandbox. SP2 MUST NOT read absolute paths or refs that escape that sandbox; external/unresolvable refs are recorded as INFO rather than trusted.

## 10. Conformance rules

### Plan-side (tools/ainp_validate.py)

| Rule | Content | Level |
|---|---|---|
| G1 | `schema == ainp.v1.0.0.generation` and payload key `generation` (strong binding) | FAIL |
| G2 | Required: `id/version/title/summary/status/artifact_type/brief/acceptance_criteria/governance`; `version` is SemVer 2.0.0 (leading zeros rejected; prerelease/build metadata accepted); `status ∈ STATUS`; `source ∈ ORIGIN` if present; `acceptance_criteria` non-empty | FAIL |
| G3 | `artifact_type` non-empty; outside suggested enum → WARN (strict FAIL) | WARN/FAIL |
| G4 | Every input has `source / rights.status / provenance.status`; `consent.required` without evidence or non-proceeding status → FAIL; tag `consent_required` ⇒ ≥1 consent-bearing input; `rights.status=consent_required` ⇒ that input carries `consent.required == true` | FAIL |
| G5 | Every criterion has `id/description/severity/verification{method}`; `static` requires a registered `check_id` (unknown → WARN, strict FAIL) | FAIL |
| G6 | `risk_profile` present and well-formed; high-risk (§7: type/tags/scope/`risk_level ∈ {high,critical}`) ⇒ `governance.approval_required == true`; `risk_tags` ⊆ high_risk_types ids | FAIL |
| G7 | Plan must not self-declare artifact trust (`safe/verified/original/trusted/authentic` keys anywhere) | FAIL |
| G8 | **Every plan** declares `disclosure_policy`; tag `disclosure_required` ⇒ `ai_generated_disclosure_required == true` | FAIL |
| G9 | `bindings` structure legal; `execution_binding.protocol` in enum; local target existence → WARN (strict FAIL) | WARN/FAIL |
| G11 | Every red-line constraint has non-empty `enforced_by[]` with legal `stage/mechanism/assurance` | FAIL |
| G12 | **Version-diff mode only** (`--previous/--current`): acceptance/red-line changes require a MAJOR bump → WARN (strict FAIL); single-file runs emit `AINP_I_G12_REQUIRES_VERSION_DIFF` | WARN/FAIL |
| G13 | `governance.risk_level`, if present, must equal `risk_profile.risk_level` | FAIL |
| G14 | Red line relying on `unverifiable` with no satisfying control point → default WARN, strict/release FAIL | WARN/FAIL |
| G15 | **Release**: every red line needs ≥1 control point with `assurance ∈ {runtime, evidence_recorded, externally_verified}` | FAIL (release) |
| G16 | If `content_architecture` is declared, it must declare a safe relative content root plus non-empty files with unique ids, safe paths, required summaries and ordered points; point `acceptance_refs[]` must reference real `acceptance_criteria[].id` values | FAIL |
| FB1 | Feedback binding + required `generation_id/source/verdict` | FAIL |
| SP1 | Space binding + `generations[].{ref, sha256}` | FAIL |
| SP2 | Space hash recompute mismatch → WARN (strict FAIL); absolute or sandbox-escaping local ref → FAIL; external/unresolvable ref → INFO | WARN/FAIL |

G10 was renumbered to R8 (report side) in plan V3.

### Report-side (tools/ainp_report_check.py)

| Rule | Content | Level |
|---|---|---|
| R1 | Profile/payload binding | FAIL |
| R2 | `generation_id` resolves to the plan | FAIL |
| R3 | `artifacts[]` each carry `id/path/mime/sha256`; release: files exist and hashes recompute | FAIL |
| R4 | `acceptance_results[]` ↔ plan criteria, 1:1 both directions; duplicate results for one criterion rejected | FAIL |
| R5 | Every result carries legal `passed/method/evidence[]/verifier/limitations` shape; malformed method/verifier/evidence is rejected | FAIL |
| R6 | `overall.conformant` required (omission is not an evasion path) and derivable from fail-level results + disclosure/approval gates; never self-set | FAIL |
| R7 | Every true `disclosure_policy.*_required` switch has the matching report-side record; required generator metadata records `provider/system/content_id/generated_at`; required watermarks record at least one present watermark with a scheme; required content credentials must be recorded as externally verified | FAIL |
| R8 | `plan_ref.sha256` matches the current plan or an archived blob findable by hash; archived → historical only (WARN); neither → FAIL, acceptance void for the current plan | FAIL |
| R9 | `governance.approval_required == true` plans require `governance_results.approval_gate` evidence with legal method/evidence/verifier shape and `passed=true` | FAIL |
| R10 | When the plan declares `content_architecture`, every required content file is covered by `generationreport.artifacts[].file_id`; `file_id` values must exist and artifact paths must match the declared file paths | FAIL |

### Project package side (tools/ainp_project_check.py)

| Rule | Content | Level |
|---|---|---|
| P1 | Project root is an existing directory named `<name>_ainp` using snake_case | FAIL |
| P2 | Project root contains uppercase `AINP.md`; lowercase `ainp.md` is rejected | FAIL |
| P3 | Project root contains `ainp/` and `AINP.md.plan_dir == ainp/` | FAIL |
| P4 | Project root contains `<name>/` content directory and `AINP.md.content_dir == <name>/` | FAIL |
| P5 | `AINP.md` frontmatter/body are complete and aligned with directory name and file paths; paths are project-root relative and non-escaping | FAIL |
| P6 | `AINP.md.feedback` is required for `approved`/`active` packages; declared side files (`feedback`, optional `space`) pass bundled JSON Schema and `ainp_validate.py --mode strict`; feedback `generation_id` matches the plan/report generation id; feedback issue `file_id` / `point_id` values bind to declared content files/points | FAIL |
| P7 | Declared `plan` + `report` pass the full release gate with the project root as artifact sandbox; report artifact paths resolve under `AINP.md.content_dir` | FAIL |
| P8 | Release report has `overall.conformant == true` through the delegated release gate; surfaced through release-family findings such as `AINP_E_RELEASE_NOT_CONFORMANT`, not a dedicated P8 code | FAIL |
| P9 | `AINP.md` must not self-declare artifact trust via fields such as `safe/verified/original/trusted/authentic` | FAIL |
| P10 | Complete project packages require `content_architecture`; its `root` and every declared content file path must resolve under `AINP.md.content_dir` | FAIL |
| P11 | Optional `ainp/references/` may contain reference files, templates, briefs and snapshots. If present without a manifest, warn; if a manifest is declared or present, it must pass schema, local paths must stay under `ainp/references/`, and recorded hashes must recompute | WARN/FAIL |

### External verification boundary (normative)

The following are **outside** static validation and are never claimed by conforming tools: truth/validity of rights, consent and provenance; source authenticity; factual accuracy; scanner reliability; provider trust; watermark presence, robustness or detectability; content-credential validity; C2PA manifest/signature/trust-list validity; whether a human approval was truly given by an authorized human. Conforming validators output `PASS structure-valid` / `WARN external-verification-required` and **never** `PASS legally-safe`, `PASS rights-verified`, or `PASS content-trusted`.

Machine-readable finding codes follow `AINP_[EWI]_<CODE>` (E=fail, W=warn, I=info).

## 11. Modes

| Mode | Semantics |
|---|---|
| default | Structural rules FAIL; unverifiable red lines WARN (G14); missing local binding targets WARN |
| strict | \+ unknown static `check_id` (G5), suggested-enum misses, binding-target misses, SP2 mismatches and G12 escalate to FAIL; unverifiable red lines FAIL |
| release | \+ G15 in force; full release gate is `tools/ainp_release_check.py`: bundled JSON Schemas pass for plan/report/high-risk data + plan release-valid + `generationreport` exists + report release-valid + artifact hashes recompute + `overall.conformant == true`; project packages use `tools/ainp_project_check.py`; plan-only release validation is not a complete release gate |

## 12. Family bindings (bidirectional closure)

| Protocol | Companion change | Priority |
|---|---|---|
| AIIP | intent gains optional `ainp_binding` | post-repo |
| AIJP | job/worktree gains optional `generation_ref` ("reference, don't copy") | post-repo |
| AIKP | knowledge entries gain `generated_from` ("never write unverified content as factual knowledge") | later |
| AIAP | creator/package generation may cite AINP `references`, `content_architecture` and lifecycle evidence; see `examples/aikp_navigator_aiap_ainp/` | post-repo |
| AIIP (reverse alignment) | converge AIIP rule 11's dual gate source to the single `governance.approval_required` | low |

## 13. Legal alignment boundary

*AINP provides machine-readable planning/evidence structures that can support governance workflows aligned with transparency and human-oversight obligations, but AINP validation is not legal compliance certification.* References to Reg (EU) 2024/1689 Art. 14 (human oversight) and Art. 50 (transparency), China's AI-generated/synthetic content labeling rules, and California's AI transparency rules are alignment references only.

## 14. Version history

- **v1.0.0** — initial release: file family, complete project package layout with uppercase `AINP.md`, co-equal `ainp/` plan folder and `<name>/` content folder plus an approved/active feedback loop, optional `ainp/references/` reference/template manifest, G1–G16/FB1/SP1/SP2/R1–R10/P1–P11, three modes, high_risk_types data file + schema, reference tools including the schema-aware release gate wrapper and project checker, teeth fixtures. Build-time completions relative to plan V5 and adversarial-audit completions are recorded in CHANGELOG.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
