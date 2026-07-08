# AINP Schema 索引

本文索引 AINP v1.0.0 的规范性机器可读 schema 文件。
英文对应文件:`specification/schemas.md`。

规范性实体文件位于仓库顶层 `schemas/` 目录。它们属于 AINP 规范的一部分,
但不复制到 `specification/` 目录下,以保持机器可读事实源唯一。

## 规范文件

| 文件 | profile | 用途 |
|---|---|---|
| `schemas/ainp-generation-v1.0.0.schema.json` | `ainp.v1.0.0.generation` | 生成计划书 schema |
| `schemas/ainp-generationreport-v1.0.0.schema.json` | `ainp.v1.0.0.generationreport` | 生成报告 schema |
| `schemas/ainp-generationfeedback-v1.0.0.schema.json` | `ainp.v1.0.0.generationfeedback` | 内容评审反馈 schema |
| `schemas/ainp-generation-space-v1.0.0.schema.json` | `ainp.v1.0.0.generation_space` | generation-space 索引 schema |
| `schemas/ainp-reference-manifest-v1.0.0.schema.json` | `ainp.v1.0.0.reference_manifest` | 可选 `ainp/references/` manifest schema,用于参考文件、模板和快照 |
| `schemas/high_risk_types-v1.0.0.schema.json` | `ainp.v1.0.0.high_risk_types` | 高风险控制数据 schema |
| `schemas/high_risk_types.v1.0.0.json` | `ainp.v1.0.0.high_risk_types` | 版本化高风险控制数据 |

## 权威边界

- `specification/AINP_Protocol.md` 定义规范语义。
- `schemas/` 定义工具和测试使用的规范性机器可读形状。
- `specification/standards/AINP_Standard.core.json`、`AINP_Standard.security.json`、`AINP_Standard.ecosystem.json` 与 `ainp-rules-v1.0.0.json` 为 dashboard 和工具提供轻量标准库参考数据。它们不是 schema 镜像,也不是运行时 flow。
- 本文件只是索引,不得演变成 schema 的第二份副本。

## 维护规则

schema 变更时,只修改 `schemas/` 中的规范实体文件,并同步更新协议文本与测试。
不要在 `specification/` 下添加 schema 镜像。

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
