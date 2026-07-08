# Cross-Protocol Binding Examples

These examples show how AINP can reference adjacent AIXP-family artifacts
without importing their runtime semantics.

They are **non-normative** examples. They intentionally use `example_profile`
instead of the top-level AINP `schema` field, so they cannot be mistaken for
schema-backed AINP file-family documents.

| Folder | Demonstrates |
|---|---|
| `aiip_to_ainp/` | An intent-side record that points to an AINP generation plan |
| `ainp_to_aijp/` | A job-side record derived from an AINP plan and report target |
| `ainp_to_aikp/` | A knowledge-side ingestion record that cites AINP evidence |
| `aiap_creator_with_ainp/` | How an AIAP Creator run can be governed by AINP |

Boundary:

- These examples are references, not executable programs.
- AINP tools never auto-execute bindings.
- Hashes and ids are integrity/evidence anchors, not trust proofs.
- External provenance, approvals and domain compliance remain external checks.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
