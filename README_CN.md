# AINP — AI Neogenesis Protocol（AI 创生协议）

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](VERSION)
[![Protocol](https://img.shields.io/badge/family-AIXP-7c3aed.svg)](https://aixp.dev)

中文文档 | [English](README.md)

[协议规范](specification/AINP_Protocol_cn.md) | [快速开始](#快速开始) | [示例](examples/README.md) | [包维护](docs/guides/package-maintenance.md) | [发布证据](docs/reference/release-evidence-matrix.md) | [Validator Coverage](docs/reference/validator-coverage.md)

**AINP（AI Neogenesis Protocol，AI 创生协议）标准化完整生成项目**:生成计划书、生成内容本身、把两者绑定起来的证据报告,以及闭合循环的反馈记录。计划书是一份机器可读、可治理的造物蓝图,适用于创建*任意*内容(文档、代码、图像、音频、视频、数据集、落地页……):造什么、按什么约束造、**怎样才算合格**。内容是被生成出来的产物本身;在完整 AINP 项目包中,计划与内容不同,但同为一等组成部分。计划指导内容;内容反馈回到计划。

```
AIIP 意图 ─▶ AINP 生成计划书 ─▶ AIJP 作业 ─▶ 产物 ─▶ AIKP 知识
              ▲        │                    全部在 HSAW / Axiom 0 之下
              └────────┴── 内容反馈
```

- **计划 ≠ 产物;二者都属于项目。** 合法的 plan 只证明结构与声明——不证明产物安全、原创、真实或合规。完整项目还必须携带生成内容与 report 侧证据。
- **计划指导内容;内容反馈回到计划。** 独立 plan 可以声明 `content_architecture`;完整项目包必须声明它,让生成内容根目录、具体文件与每个文件的 points/requirements 可机器绑定。`approved`/`active` 项目包还必须声明 `AINP.md.feedback`,并校验 feedback 记录指回同一个 generation id。
- **验收落 report。** plan 立标准;证据落 `*.generationreport.json`,并用 hash 锁定它评判的那份 plan 快照。
- **红线点名强制者。** 每条 hard/safety/ip/approval/disclosure/privacy 约束带 `enforced_by[]` 控制点数组与显式 assurance 等级;`unverifiable` 是诚实记录,永远不是通过凭证。
- **高风险生成必须过人。** 肖像、生物特征、声音克隆、未成年相关、医疗/法律/金融建议、大规模劝服、选举内容、攻击代码、mass-public 分发,以及任何自报 `risk_level ∈ {high, critical}` 的计划,一律要过 HSAW 人类主权门。
- **披露可记录生成系统与水印证据。** plan 可要求 report 记录 generator 身份元数据与 watermark 证据;这些记录支撑透明度,不是信任证书。
- **plan 是不可信输入。** 合规工具绝不自动执行 bindings、绝不自动下载 inputs、绝不信任内嵌 hash。

## 文件家族

规范性 JSON Schema 与版本化高风险控制数据位于顶层 `schemas/`。它们是
AINP 规范的机器可读部分,由 `specification/schemas.md` / `specification/schemas_cn.md` 索引,不在
`specification/` 下复制第二份。

机器可读 standards 位于 `specification/standards/`:`AINP_Standard.core.json`、
`AINP_Standard.security.json`、`AINP_Standard.ecosystem.json` 与
`ainp-rules-v1.0.0.json` 规则索引。它们是标准库参考数据,不是 AISOP flow,
不是 JSON Schema 镜像,也不是 AIAP program 或运行期信任证明。

本地 release wrapper 保持 stdlib-only,校验本仓内置 schema 实际使用的
Draft 2020-12 关键字子集,包括这些 schema 中出现的组合/条件关键字;一致性测试使用
`jsonschema` 执行完整 Draft 2020-12 schema 校验。

AINP 是 v1.0.0 唯一公开标识。参考工具只校验本文档定义的 canonical
AINP 项目包结构、schema profile、CLI 名称与 finding-code 前缀。

| 文件 | profile | 用途 |
|---|---|---|
| `*.generation.json` | `ainp.v1.0.0.generation` | **生成计划书与验收契约** |
| `*.generationreport.json` | `ainp.v1.0.0.generationreport` | 单次生成的验收实证 |
| `*.generationfeedback.json` | `ainp.v1.0.0.generationfeedback` | 内容评审反馈回计划 |
| `*.ainp.json` | `ainp.v1.0.0.generation_space` | 计划索引 |
| `ainp/references/reference_manifest.json` | `ainp.v1.0.0.reference_manifest` | 可选参考文件、模板、brief 与快照索引 |
| `high_risk_types.v1.0.0.json` | `ainp.v1.0.0.high_risk_types` | 版本化高风险清单(单一真相源)|

## 项目包

完整 AINP 项目包命名为 `<name>_ainp/`,同时包含项目声明、AINP 计划文件夹和项目内容文件夹。计划文件夹与内容文件夹地位对等:`ainp/` 说明并记录生成过程;`<name>/` 保存生成内容本身;feedback 记录内容评审如何回到计划。

```text
<name>_ainp/
├── AINP.md                 # 项目声明、索引与校验入口
├── ainp/                   # AINP 计划文件夹:plan/report/feedback/generation space
│   └── references/          # 可选:协议快照、模板、brief、style guide
└── <name>/                 # 项目内容文件夹:生成内容本身
```

`AINP.md` 必须大写(P2 强制),与 AIAP 的 `AIAP.md` 风格一致。它是项目声明、索引、自举说明与校验入口,不是信任证明。

`ainp/` 是 AINP 计划文件夹,保存 generation plan、generation report、feedback 和 generation space。`<name>/` 是项目内容文件夹,保存真正生成的内容本身。完整项目包中,plan 的 `content_architecture` 必须用具体 file id、path 与 points 描述这个内容文件夹;report artifacts 回绑这些 file id,feedback 可指向已声明文件或 point。项目校验要求 release report 中的 artifact 路径与计划内容路径都必须落在 `AINP.md.content_dir` 指定的内容目录下,防止已验收内容被静默塞回计划文件夹;对 `approved`/`active` 项目包,还要求 `AINP.md.feedback` 存在,且其 generation id 与 plan/report 一致。

`ainp/references/` 是可选目录,用于保存生成参考材料,例如协议/spec 快照、模板、brief、style guide、接口说明、政策摘录或研究笔记。若存在,建议包含 `reference_manifest.json`;项目检查会验证本地条目仍位于 `ainp/references/` 下,并重算已记录 hash。hash 只证明本地完整性,不证明外部权威、最新版本、法律充分性或 runtime trust。单个 manifest 也可以用 `tools/ainp_validate.py` 直接校验,但这仍只证明结构与本地完整性。`external_uri` 条目只记录、不抓取,也不能携带本地 `sha256` 锚点。

## 快速开始

```bash
# 快速本地健康检查
python -B tools/ainp.py doctor --json

# 运行本地发布门
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1
# 安装 dev 依赖后,可同时纳入 pytest 发现路径:
python -m pip install "jsonschema>=4" "pytest>=8"
powershell -ExecutionPolicy Bypass -File scripts\release_check.ps1 -IncludePytest

# 校验计划(default | strict | release 三档;whitepaper 示例在 strict/release 下
# 故意 FAIL——G9 缺失绑定演示,见 examples/README.md)
python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json
python -B tools/ainp_validate.py examples/file_family/high_risk_likeness.generation.json --mode release
python -B tools/ainp_validate.py examples/aikp_navigator_aiap_ainp/ainp/references/reference_manifest.json

# 对照 plan 校验 report(hash 锁定)
python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json
python -B tools/ainp_report_check.py examples/file_family/high_risk_likeness.generationreport.json --mode release

# 完整 release 门(JSON Schema + plan + report + artifact hash + conformant report)
python -B tools/ainp_release_check.py examples/file_family/high_risk_likeness.generation.json \
    --report examples/file_family/high_risk_likeness.generationreport.json
python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json \
    --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json \
    --project-root examples/whitepaper_ainp

# 校验完整 AINP 项目包
python -B tools/ainp.py project-check examples/whitepaper_ainp
python -B tools/ainp_project_check.py examples/whitepaper_ainp
python -B examples/slugify_cli_ainp/slugify_cli/tests/test_slugify_cli.py
python -B examples/aikp_navigator_aiap_ainp/aikp_navigator_aiap/tests/test_resolve_topic.py
python -B tools/ainp_rehash.py examples/slugify_cli_ainp --check
python -B tools/ainp_project_check.py examples/slugify_cli_ainp
python -B tools/ainp_project_check.py examples/aikp_navigator_aiap_ainp

# 破坏性变更纪律(G12):改验收标准必须 MAJOR bump
python -B tools/ainp_validate.py --previous old.generation.json --current new.generation.json

# 跑一致性 + teeth 套件
python -B tests/test_ainp.py
```

可选文档站检查:

```powershell
python -m pip install "mkdocs>=1.6" "mkdocs-material>=9"
$env:NO_MKDOCS_2_WARNING = "true"
python -B -m mkdocs build --strict
```

发布门不强制依赖 MkDocs。该命令只安装文档渲染依赖,不会在仓库根生成
`*.egg-info/` 包元数据。`NO_MKDOCS_2_WARNING` 只关闭 Material for MkDocs 的
上游公告,让 strict 模式继续专注于本项目文档 warning。

合规 validator 只输出 `PASS structure-valid` / `WARN external-verification-required`——**绝不**输出 `PASS legally-safe`、`PASS rights-verified` 或 `PASS content-trusted`。内嵌 hash 只证明可重算完整性;content credential、generator、watermark 字段只记录外部证据,参考工具不把它本地验证成密码学信任、provider 信任或 watermark 可检测性。

## 仓库结构

```
AINP-Protocol/
├── specification/       AINP_Protocol.md + _cn.md + schema 索引 + standards/
├── schemas/             规范性机器可读 schema + 高风险控制数据
├── examples/            file_family/、bindings/ 示例 + 完整 <name>_ainp/ 项目包
├── tools/               统一 CLI、validator、release 辅助、文档/链接检查
├── scripts/             release_check.ps1 本地发布门
├── .github/             CI validation workflow
├── tests/               一致性套件 + 36 个 fixture 文件(teeth + G12 正例孪生)
├── adrs/                架构决策记录
└── docs/ docs_cn/       叙事文档(mkdocs)
```

## AIXP Labs [aixp.dev](https://aixp.dev)

AIXP Labs 开发并维护以下核心项目：

| 项目 | 描述 | 网站 |
|------|------|------|
| [HSAW](https://hsaw.dev) | 人类主权与福祉 —— Axiom 0 白皮书（基石） | hsaw.dev |
| [AIZP](https://aizp.dev) | AI Zenith-Zero Protocol —— 运行时行为对齐 | aizp.dev |
| [AINP](https://ainp.dev) | AI Neogenesis Protocol（AI 创生协议）—— 可治理的生成项目：计划 + 内容 + 证据 **（本项目）** | ainp.dev |
| [AILP](https://ailp.dev) | AI List Protocol —— agent 发现与能力广告 | ailp.dev |
| [AIVP](https://aivp.dev) | AI Value Protocol —— 国际商务、加密资产结算 | aivp.dev |
| [AIRP](https://airp.dev) | AI RMB Protocol —— 中国大陆商务、人民币持牌结算 | airp.dev |
| [AIBP](https://aibp.dev) | AI Bot Protocol —— 社交通信与信任 | aibp.dev |
| [AIAP](https://aiap.dev) | AI Application Protocol —— 治理与合规 | aiap.dev |
| [AISP](https://aisp.dev) | AI Skill Protocol —— 单文件技能包，机器强制的契约红线 | aisp.dev |
| [AISOP](https://aisop.dev) | AI Standard Operating Protocol —— 流程程序定义 | aisop.dev |
| [SoulSkill](https://soulskill.dev) | AISP 技能参考库 & 多 CLI 插件分发 | soulskill.dev |
| [SoulAgent](https://soulagent.dev) | 任何 CLI / SDK / IDE 直接调用的 drop-in AI agent | soulagent.dev |
| [SoulBot](https://soulbot.dev) | AI agent 运行时 & 自编排框架（定时、建 agent、agent 间通信） | soulbot.dev |
| [SoulACP](https://soulacp.dev) | 适配库 —— 桥接 CLI 工具与 LLM 提供方 | soulacp.dev |

## 免责声明

本规范与参考工具为**实验性**,仅供研究与教育用途。AINP 校验**不是**法律合规认证;通过校验只证明结构一致。不可信输入规则见 [SECURITY.md](SECURITY.md);许可条款见 [LICENSE](LICENSE)(Apache-2.0)。

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev

<a id="values-philosophy"></a>

## ⚓ 价值观与哲学 (Alignment & Philosophy)

### Axiom 0: [HSAW | Human Sovereignty and Wellbeing](https://hsaw.dev)

- **No HITL, HSAW.**
  *人类主权与福祉是第零公理，无需虚伪的人机协同。*
- **No w.a.s.h, Real h.s.a.w.**
- **人非蝼蚁，人为道。**
- **We are not beggars. We the People.**
