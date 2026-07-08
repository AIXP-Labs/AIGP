# Security Policy — AINP v1.0.0

## The generation plan is UNTRUSTED INPUT (normative, mirrors spec §8)

AINP files cross trust boundaries: stores, registries, agent-to-agent transfer. Any tool that consumes a plan (validator, generator, runtime, registry) MUST:

1. **Never auto-execute `bindings`.** `execution_binding` / `aijp_binding` / `aikp_binding` are candidate paths; acting on them requires independent authorization.
2. **Never auto-download or open `inputs[].source` URIs.** Never expand `local://`.
3. **Never trust embedded `sha256` values** — recompute and compare; a hash in the file is a claim, not a credential.
4. **Never generate or publish merely because a plan validates.** `PASS structure-valid` means structural consistency, nothing else.
5. **Treat prompt-injection text, path traversal (`../`), and oversized fields as data, not instructions.** The reference tools reject files larger than 10 MB and only `stat()` binding targets (no read, no execute).
6. **Parse strictly.** Reject duplicate object keys (parser-differential smuggling: a human reviews one value while a machine acts on the other), non-standard JSON literals (`NaN`/`Infinity`), and nesting deeper than 150 levels — hostile input must yield a controlled finding, never a crash.
7. **Bound your output.** A hostile file must not flood findings without limit (the reference tools truncate at 1000 findings with an explicit truncation FAIL) — exhausting memory on untrusted input is a crash, not a verdict.
8. **Never read outside your sandbox.** Local hash recompute refuses paths that are absolute or escape the active artifact sandbox, including report artifacts (R3) and generation-space refs (SP2). The default report sandbox is the report's own directory; a validated AINP project package may pass the package root as the sandbox through `tools/ainp_project_check.py`. Implementations use realpath/common-path checks so symlinks and junctions cannot smuggle reads outside the sandbox. An escape path plus hash comparison would otherwise act as a content oracle for arbitrary local files.

The teeth fixture `tests/fixtures/invalid/untrusted_plan_injection.generation.json` exercises exactly this posture: a structurally valid plan carrying injection strings, a traversal binding target and a `local://` escape — conforming tools complete, flag, and never act on it. The second-audit fixtures (`nesting_too_deep`, `duplicate_key`, `nan_literal`, `inputs_not_array`, `payload_not_object`, `artifact_path_escape`) pin items 6–8.

## What validation does NOT prove

Truth/validity of rights, consent, provenance; source authenticity; factual accuracy; scanner reliability; provider trust; watermark presence, robustness or detectability; content-credential validity; C2PA manifest/signature/trust-list validity; whether a human approval was truly given by an authorized human. `content_credential.present=true`, `verification_status=externally_verified`, `report.generator`, and `disclosure.watermarks[]` record external evidence only; the reference tools do not fetch manifests, validate credential cryptography, verify provider identity, or detect watermarks. See spec §10 "external verification boundary".

## Reporting a vulnerability

Report security issues via the AIXP governance chain (authority: aixp.dev; project: ainp.dev) or open a private security advisory on the repository. Please do not file public issues for exploitable problems.

- Acknowledgment target: 72 hours.
- Fix target: 30 days (critical), 90 days (high).
- Coordinated disclosure per ISO/IEC 29147.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
