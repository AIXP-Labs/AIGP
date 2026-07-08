# AINP — AI Neogenesis Protocol（AI 创生协议）

AINP（AI Neogenesis Protocol，AI 创生协议）标准化**完整生成项目**:生成计划书、生成内容本身、把两者绑定起来的证据报告,以及闭合循环的反馈记录。计划书说明造什么、按什么约束造、怎样才算合格;`content_architecture` 声明内容文件与 points;内容目录承载生成出来的产物本身;内容反馈回到计划。

- 规范正文:`specification/AINP_Protocol_cn.md`(以英文版为准)
- 叙事文档:完整叙事树(topics / guides / reference)目前为英文(`docs/`);本页为中文摘要落地页,中文规范正文完整可用
- Schema:`schemas/`(规范性机器可读规范,由 `specification/schemas.md` / `specification/schemas_cn.md` 索引) · 示例:`examples/file_family/`、`examples/whitepaper_ainp/`、`examples/slugify_cli_ainp/` 与 `examples/aikp_navigator_aiap_ainp/` · 参考工具:`tools/`
- Standards:`specification/standards/` 是轻量机器可读参考数据,不是 schema 镜像、AISOP flow、AIAP program 或信任证明
- 发布证据:`docs/reference/release-evidence-matrix.md` · Validator Coverage:`docs/reference/validator-coverage.md`
- 集成路线:`docs/integrations/aixp-generation-lifecycle.md`(英文路线文档;规范仍以 `specification/AINP_Protocol.md` 为准)
- 包维护:`docs/guides/package-maintenance.md`

完整可分发项目使用标准项目包结构:

```text
<name>_ainp/
├── AINP.md                 # 项目声明、索引与校验入口
├── ainp/                   # AINP 计划文件夹
└── <name>/                 # 项目内容文件夹
```

`AINP.md` 必须大写,与 AIAP 的 `AIAP.md` 风格一致。它是项目声明、索引与校验入口,不是信任证书。`ainp/` 保存 plan/report/feedback/space 文件;`<name>/` 保存生成内容本身。项目校验还要求计划内容路径与 report artifact 路径都落在声明的内容目录下,并要求 feedback 指向与 plan/report 相同的 generation id。

项目包校验:

```bash
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp
```

核心理念:计划 ≠ 产物 · 必须声明内容蓝图 · 计划指导内容 · 内容反馈回计划 · 验收证据落在 hash 锁定的 report · 红线点名强制者 · unverifiable 永远不是通过凭证 · 高风险生成必须过人(HSAW / Axiom 0)· 生成器 / 水印记录是证据,不是信任证书 · plan 是不可信输入。

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
