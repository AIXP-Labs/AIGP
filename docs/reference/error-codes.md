# Error Codes

AINP reference tools use machine-readable codes with this shape:

```text
AINP_<E|W|I>_<RULE_OR_AREA>_<DETAIL>
```

| Prefix | Meaning |
|---|---|
| `AINP_E_` | Failure; command exits non-zero when present |
| `AINP_W_` | Warning; command may still pass, but evidence is incomplete or external |
| `AINP_I_` | Informational evidence |

This page lists important families and representative codes. It is not an
exhaustive dump of every fine-grained validator branch; the executable tools
and tests remain the source of truth for exact emitted codes.

Important families:

| Family | Examples |
|---|---|
| G | `AINP_E_G6_MISSING_APPROVAL`, `AINP_E_G7_SELF_TRUST_CLAIM`, `AINP_E_G16_CONTENT_ARCHITECTURE_BAD_SHAPE`, `AINP_E_G16_FILE_PATH_INVALID` |
| R | `AINP_E_R7_GENERATOR_METADATA_NOT_RECORDED`, `AINP_E_R7_WATERMARK_NOT_RECORDED`, `AINP_E_R8_PLAN_REF_MISMATCH`, `AINP_I_R8_PLAN_REF_MATCHES`, `AINP_E_R10_REQUIRED_FILE_MISSING_ARTIFACT` |
| P | `AINP_E_P2_AINP_MD_MISSING`, `AINP_E_P6_FEEDBACK_REQUIRED`, `AINP_E_P6_FEEDBACK_ID_MISMATCH`, `AINP_E_P6_FEEDBACK_UNKNOWN_POINT_ID`, `AINP_E_P6_VALIDATE_TOOL_EXIT`, `AINP_E_P7_ARTIFACT_OUTSIDE_CONTENT_DIR`, `AINP_E_P7_RELEASE_TOOL_EXIT`, `AINP_E_P9_SELF_TRUST_CLAIM`, `AINP_E_P10_CONTENT_ARCHITECTURE_REQUIRED`, `AINP_E_P10_CONTENT_FILE_OUTSIDE_CONTENT_DIR`, `AINP_W_P11_REFERENCES_MANIFEST_MISSING`, `AINP_E_P11_SCHEMA_INVALID`, `AINP_E_P11_MANIFEST_SCHEMA_INVALID`, `AINP_E_P11_EXTERNAL_REFERENCE_HASH_UNVERIFIABLE`, `AINP_E_P11_REFERENCE_HASH_MISMATCH`, `AINP_E_P11_LOCAL_REFERENCE_OUTSIDE_REFERENCES_DIR` |
| SP | `AINP_E_SP2_PATH_ESCAPES` |
| Hostile input / IO | `AINP_E_CONTAINER_NOT_ARRAY`, `AINP_E_NESTING_TOO_DEEP`, `AINP_E_FILE_TOO_LARGE`, `AINP_E_FINDINGS_TRUNCATED`, `AINP_E_NOT_OBJECT`, `AINP_E_UNREADABLE` |
| Release | `AINP_E_RELEASE_SCHEMA_INVALID`, `AINP_E_RELEASE_JSON_UNREADABLE`, `AINP_E_RELEASE_REPORT_MISSING`, `AINP_E_RELEASE_NOT_CONFORMANT`, `AINP_E_RELEASE_TOOL_OUTPUT`, `AINP_E_RELEASE_TOOL_EXIT` |
| Strict/release escalation | `AINP_E_G5_UNKNOWN_CHECK_ID`, `AINP_E_SP2_HASH_MISMATCH` |
| Boundary | `AINP_W_EXTERNAL_VERIFICATION_REQUIRED` |

The tests pin the currently important failure codes in
`tests/test_ainp.py`.

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
