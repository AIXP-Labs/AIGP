# Contributing to AINP

Thank you for your interest in contributing to the AI Neogenesis Protocol! This document provides guidelines for contributing to the project.

> ⚠️ **Contribution Status (Current Stage)**
>
> We welcome **discussion through GitHub Issues** at this stage of development.
>
> **External Pull Requests are not currently accepted.** If you have a proposal — bug report, feature idea, specification clarification, conformance rule or risk-tag suggestion — please open an issue describing it. If we agree it adds value, maintainers will implement it and credit you.
>
> This policy may be revisited in the future.

> **Stage Status (v1.0.0)**
>
> AINP v1.0.0 is the initial stable specification release. The processes below describe the repository governance model while contribution volume is still small. Decisions are made by AIXP Labs core maintainers after issue-based discussion; community review windows scale as the contributor base grows. The English `specification/AINP_Protocol.md` is authoritative; the Chinese `specification/AINP_Protocol_cn.md` is a faithful mirror (on conflict, English wins).

## How to Contribute

### Reporting Issues

- Use [GitHub Issues](https://github.com/AIXP-Labs/AINP/issues) to report bugs, suggest features, or propose specification changes
- For specification changes, use the `spec-change` issue template
- Provide clear descriptions with examples where possible — ideally a minimal `*.generation.json` that demonstrates the problem

### Discussion-Driven Development

Instead of submitting PRs directly:

1. **Open an issue** describing your proposal, bug, or idea
2. **Discuss** with maintainers — clarify scope, design, and approach
3. **Wait for review** — significant proposals follow the [Specification Changes](#specification-changes) process below
4. **If accepted**, maintainers will implement the change and credit you in commit/release notes

### Specification Changes

Proposals affecting normative content (anything in `specification/` or `schemas/`) follow this process:

1. An issue with the `spec-change` label describing the proposed change
2. A minimum 14-day discussion period for non-trivial changes (target governance model; current discussion windows scale with contributor count)
3. An Architecture Decision Record (ADR) in `adrs/` for significant decisions, following the ADR-001 discipline: verify on disk, then decide, then record the evidence
4. Axiom 0 compliance review by maintainers (the high-risk human approval gate, red-line assurance limits, untrusted-input rules, disclosure requirements and self-trust prohibition are immovable — see [GOVERNANCE.md](GOVERNANCE.md))
5. Evidence-gated admission: new required fields, rule families or release-blocking gates require a demonstrated failure case, a teeth fixture, or a documented external interoperability/compliance driver; convenience fields start optional or advisory
6. Updated documentation reflecting the change

### Engineering Ground Rules

1. **Read the spec first**: `specification/AINP_Protocol.md` is normative; the tools implement it 1:1; the teeth fixtures prove it. A change to one without the others will not merge.
2. **Every new rule ships with teeth**: at least one negative fixture in `tests/fixtures/invalid/` that FAILs with the documented `AINP_E_*` code.
3. **Honesty boundaries are non-negotiable**: never add output that claims safety/rights/trust beyond `structure-valid`.
4. **Untrusted-input posture**: tool changes must never execute bindings, download inputs, or trust embedded hashes.
5. **Zero-dependency tools**: `tools/*.py` stay stdlib-only. `jsonschema` is allowed in tests only.
6. **Schema single source**: JSON Schemas and high-risk control data live only in top-level `schemas/`; `specification/` may index them but must not mirror them.
7. **Run the gates**: `python -B tests/test_ainp.py` (the whole suite must pass), or install `python -m pip install "jsonschema>=4" "pytest>=8"` and run the full local gate `powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest`. Avoid editable installs before release checks because they create `*.egg-info/` residue.
8. **Docs-site changes**: install `python -m pip install "mkdocs>=1.6" "mkdocs-material>=9"`, set `NO_MKDOCS_2_WARNING=true`, and run `python -B -m mkdocs build --strict`. The release gate does not require MkDocs.
9. **No machine-specific absolute paths** anywhere in the repository.

### Documentation Changes

Suggestions for non-normative content (topics, guides, reference) are welcome via issues — typo fixes, clarifications, additional examples are particularly valued. English (`docs/`) and Chinese (`docs_cn/`) versions should be kept in parity. Maintainers will implement accepted suggestions.

## Writing Guidelines

### RFC 2119 Keywords

When writing normative specification text, use the keywords defined in [RFC 2119](https://tools.ietf.org/html/rfc2119):

- **MUST** / **MUST NOT** — Absolute requirements
- **SHOULD** / **SHOULD NOT** — Strong recommendations with documented exceptions
- **MAY** — Truly optional behavior

These keywords MUST be capitalized when used in their normative sense.

### Terminology

- Use "AINP project package" for a `<name>_ainp/` directory, "plan folder" for its `ainp/`, and "content folder" for its `<name>/`
- Use "generation plan" for `*.generation.json`, "generation report" for `*.generationreport.json`, "generation feedback" for `*.generationfeedback.json`, and "generation space" for `*.ainp.json`
- Use "red-line constraint" for `type ∈ {hard, safety, ip, approval, disclosure, privacy}` and "control point" for an `enforced_by[]` entry
- Rule ids are **G1–G16 / R1–R10 / P1–P11 / FB1 / SP1–SP2**; machine codes follow `AINP_[EWI]_<CODE>`
- Capitalize "Axiom 0" (it is a proper noun); HSAW is the upstream axiom AINP aligns to, not one AINP owns — never write a sibling protocol's closing seal here
- Never use "Claude" or "Anthropic" as branding; the package suffix is always `_ainp`

### Document Structure

- Begin each topic document with a one-paragraph introduction
- Use tables for field and rule specifications
- Use code blocks with language annotations for examples
- Cross-reference between documents using relative links (local links are checked by `python -B tools/check_markdown_links.py --root .`)

### Closing Seal

All specification documents MUST end with:

```
Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
```

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md). The Axiom 0 pledge applies to all contributions.

## License of Contributions

By submitting an issue or any other content (including specification proposals, code snippets in issues, or design suggestions), you agree that your submitted content may be used by maintainers under the terms of the [Apache License 2.0](LICENSE), the same license as the project.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
