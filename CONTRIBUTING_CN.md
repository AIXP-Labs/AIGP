# 如何贡献 AINP

感谢您有兴趣为 AI 创生协议（AINP）做出贡献！本文档提供贡献指南。

> ⚠️ **当前阶段的贡献政策**
>
> 我们欢迎通过 **GitHub Issues 进行讨论**。
>
> **当前不接受外部 Pull Request。** 如果您有任何建议 — bug 报告、功能想法、规范澄清、一致性规则或风险标签建议 — 请通过 Issue 描述。如果我们认为有价值，由维护者实现并在 commit/release notes 中署名感谢您。
>
> 此政策未来会重新审视。

> **阶段状态（v1.0.0）**
>
> AINP v1.0.0 是初始稳定规范版本。下方流程描述的是当前仓库治理模型；在贡献规模仍较小时，决策由 AIXP Labs 核心维护者基于 Issue 讨论做出，社区评审窗口会随贡献者基数增长而扩大。英文 `specification/AINP_Protocol.md` 为权威规范；中文 `specification/AINP_Protocol_cn.md` 为忠实镜像（冲突时以英文版为准）。

## 如何贡献

### 报告 Issue

- 使用 [GitHub Issues](https://github.com/AIXP-Labs/AINP/issues) 报告 bug、提议功能或建议规范变更
- 规范变更请使用 `spec-change` issue 模板
- 提供清晰描述，尽可能附带示例 — 最好附一份能复现问题的最小 `*.generation.json`

### 讨论驱动开发

请勿直接提交 PR，而是：

1. **打开 Issue**，描述您的提议、Bug 或想法
2. **与维护者讨论** — 明确范围、设计和方法
3. **等待审核** — 重要提议遵循下方[规范变更](#规范变更)流程
4. **若被采纳**，维护者将实现该变更并在 commit/release notes 中署名感谢您

### 规范变更

影响规范性内容（`specification/` 或 `schemas/` 中任何文件）的提议遵循以下流程：

1. 带 `spec-change` 标签的 Issue，描述提议变更
2. 非平凡变更需要至少 14 天的讨论期（目标治理模型；当前讨论窗口随贡献者基数调整）
3. 重大决策需要在 `adrs/` 中记录架构决策记录（ADR），遵循 ADR-001 纪律：先磁盘核实、再定夺、记录依据
4. 维护者进行 Axiom 0 合规审查（高风险人类批准门、红线 assurance 上限、不可信输入规则、披露要求与自报信任禁令为不可动约束 — 见 [GOVERNANCE.md](GOVERNANCE.md)）
5. 实证准入：新增必填字段、规则族或发布级门须有实证失败案例、teeth 反例或有据可查的外部互操作/合规驱动；便利字段先从可选/advisory 起步
6. 同步更新反映变更的文档

### 工程铁律

1. **先读规范**：`specification/AINP_Protocol.md` 为规范正文；工具 1:1 实现；teeth 反例证明。只改其一不合并。
2. **新规则必须带牙**：至少一个 `tests/fixtures/invalid/` 反例，以文档化的 `AINP_E_*` 码 FAIL。
3. **诚实边界不可谈判**：绝不新增超出 `structure-valid` 的安全/权利/信任声称输出。
4. **不可信输入姿态**：工具改动绝不执行 bindings、下载 inputs、信任内嵌 hash。
5. **工具零依赖**：`tools/*.py` 仅用标准库；`jsonschema` 仅限测试。
6. **Schema 单一事实源**：JSON Schema 与高风险控制数据只放在顶层 `schemas/`；`specification/` 可以索引，不得镜像复制。
7. **跑门**：`python -B tests/test_ainp.py`（全套必须通过），或先安装 `python -m pip install "jsonschema>=4" "pytest>=8"`，再用 `powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest` 跑完整本地发布门。发布检查前避免 editable install，因为它会生成被发布门拒绝的 `*.egg-info/` 残留。
8. **文档站改动**：安装 `python -m pip install "mkdocs>=1.6" "mkdocs-material>=9"`，设置 `NO_MKDOCS_2_WARNING=true`，再运行 `python -B -m mkdocs build --strict`。发布门不强制依赖 MkDocs。
9. **仓库任何位置不得出现本机绝对路径**。

### 文档变更

非规范性内容（topics、guides、reference）的建议通过 Issue 提交即可 — 错别字修正、澄清、补充示例尤其受欢迎。英文（`docs/`）与中文（`docs_cn/`）版本应保持同步。维护者将实现被采纳的建议。

## 写作规范

### RFC 2119 关键词

撰写规范性内容时，请使用 [RFC 2119](https://tools.ietf.org/html/rfc2119) 定义的关键词：

- **MUST** / **MUST NOT** — 绝对要求
- **SHOULD** / **SHOULD NOT** — 强烈建议（允许有据可循的例外）
- **MAY** — 真正可选

这些关键词在规范意义上**必须**大写。

### 术语规范

- 使用 "AINP 项目包" 指代 `<name>_ainp/` 目录，"计划文件夹" 指代其 `ainp/`，"内容文件夹" 指代其 `<name>/`
- 使用 "生成计划书" 指代 `*.generation.json`，"生成报告" 指代 `*.generationreport.json`，"生成反馈" 指代 `*.generationfeedback.json`，"生成空间" 指代 `*.ainp.json`
- 使用 "红线约束" 指代 `type ∈ {hard, safety, ip, approval, disclosure, privacy}`，"控制点" 指代 `enforced_by[]` 条目
- 规则编号为 **G1–G16 / R1–R10 / P1–P11 / FB1 / SP1–SP2**；机器码遵循 `AINP_[EWI]_<CODE>`
- "Axiom 0" 大写（专有名词）；HSAW 是 AINP 对齐的上游公理，不归 AINP 所有 — 绝不在本仓写姊妹协议的闭合签名
- 绝不用 "Claude" 或 "Anthropic" 作为品牌；项目包后缀始终是 `_ainp`

### 文档结构

- 每个主题文档以一段简介开头
- 字段与规则规范用表格
- 示例代码块标注语言
- 文档之间用相对链接互相引用（本地链接由 `python -B tools/check_markdown_links.py --root .` 检查）

### 闭合签名

所有规范文档**必须**以下行结尾：

```
Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
```

## 行为准则

所有贡献者必须遵守 [行为准则](CODE_OF_CONDUCT.md)。Axiom 0 承诺适用于所有贡献。

## 贡献的许可

提交 Issue 或任何其他内容（包括规范建议、Issue 中的代码片段或设计建议）即表示您同意维护者可以在 [Apache License 2.0](LICENSE) 条款下使用您提交的内容，与本项目使用相同的许可证。

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
