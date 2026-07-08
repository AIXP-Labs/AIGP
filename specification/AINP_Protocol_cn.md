# AINP — AI Neogenesis Protocol（AI 创生协议）· 规范 v1.0.0

状态:**v1.0.0**(首发版)。本文为 AINP 文件家族、一致性规则、治理门与诚实边界的规范性事实源(与英文版 `AINP_Protocol.md` 同构,节号一致;冲突时以英文版为准)。

---

## 1. 概述与定位

**AINP（AI Neogenesis Protocol，AI 创生协议）标准化完整生成项目**:生成计划书、生成内容本身、把两者绑定起来的证据报告,以及闭合循环的反馈记录。计划书是一份机器可读、可治理的造物蓝图——造什么、按什么约束造、**怎样才算合格**。计划书永远不是内容本身,但完整 AINP 项目包必须同时包含两侧一等组成部分:计划/证据文件夹与生成内容文件夹,并用反馈把内容评审回连到计划。

生态链(全部在 HSAW / Axiom 0 之下):

```
AIIP 意图 ─▶ AINP 生成计划书 ─▶ AIJP 作业 ─▶ 产物 ─▶ AIKP 知识
 (why/what)   (蓝图+验收契约)      (活儿)              (沉淀)
```

边界恒等式:**plan ≠ intent ≠ job ≠ program ≠ artifact。** 包恒等式:**AINP project = declaration + plan/evidence folder + content folder + feedback loop**。计划通过结构、约束与验收标准指导内容;生成内容通过 `*.generationfeedback.json` 反馈计划。区分边界是为了避免把计划当成内容信任证明,不是把生成内容降级为可有可无的附属物。

- 对 **AIIP**:意图说"要什么";AINP 说"要造的东西长什么样 + 何时算合格"。
- 对 **AIJP**:AIJP 排施工;AINP 是施工实现的那张图纸。
- 对 **AISOP/AISP**:它们是执行语言/技能;一份 AINP 计划可由其中任意者实现。
- 计划书是**一等的可评审、可版本化产物**,可以存在而不被执行。
- 在可分发 `<name>_ainp/` 项目包中,生成内容同样是**一等项目组成部分**;report 把 plan 与具体内容 artifact 绑定起来。
- feedback 是反向边:把内容侧评审记录回同一个 generation id,让下一轮 plan 修订有结构化证据可用。

## 2. Axiom 0

AINP 对齐 **Axiom 0:人类主权与福祉**(归 HSAW 所有,非 AINP 所有)。落点:高风险生成必须过人类批准门(G6);需要 consent 的输入必须有记录证据(G4);红线约束必须点名强制者(G11);不可核验的强制在 strict/release 下永不满足红线(G14/G15);产物与包声明不得自报信任(G7/P9);声明或标签要求的披露为强制(G8)。

## 3. 术语——单一真相源

本规范所有规则引用以下枚举。**闭枚举**由 JSON Schema `enum` 强制;**建议枚举**为开放字符串,validator 对未知值 WARN(strict 下 FAIL)。

闭枚举:

```text
REDLINE_TYPES    = { hard, safety, ip, approval, disclosure, privacy }
CONSTRAINT_TYPES = REDLINE_TYPES ∪ { soft }        # soft=风格/偏好,无强制门
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
                   # 允许继续生成的仅: recorded | verified
CONSENT_SCOPE    = { single_generation, project, time_bounded }
VERDICT          = { accept, revise, reject }
SEVERITY         = { fail, warn, info }
VERIFICATION_METHOD = { static, external, human }
EXECUTION_PROTOCOLS = { AISOP, AISP, AIJP, external, none }
MODES            = { default, strict, release }
```

建议枚举(开放,validator 提示):

```text
ARTIFACT_TYPES_SUGGESTED = { document, code, image, audio, video, dataset,
                             design, landing_page, campaign, 3d, mixed }
STRUCTURE_KIND_SUGGESTED = { section, subsection, component, module, scene, asset }
```

已注册 static `check_id`(G5):`structure.sections_nonempty` / `inputs.rights_declared` / `length.within_bounds` / `disclosure.policy_declared`。

## 4. 文件家族、命名与版本纪律

| profile(`schema`,下划线)| payload key | schema 文件(连字符)|
|---|---|---|
| `ainp.v1.0.0.generation` | `generation` | `ainp-generation-v1.0.0.schema.json` |
| `ainp.v1.0.0.generationreport` | `generationreport` | `ainp-generationreport-v1.0.0.schema.json` |
| `ainp.v1.0.0.generationfeedback` | `generationfeedback` | `ainp-generationfeedback-v1.0.0.schema.json` |
| `ainp.v1.0.0.generation_space` | `generation_space` | `ainp-generation-space-v1.0.0.schema.json` |
| `ainp.v1.0.0.reference_manifest` | `reference_manifest` | `ainp-reference-manifest-v1.0.0.schema.json` |
| `ainp.v1.0.0.high_risk_types` | —(数据文件)| `high_risk_types.v1.0.0.json` + `high_risk_types-v1.0.0.schema.json` |

schema 纪律:全部 `additionalProperties: false`;`schema` 串与 payload key **强绑定**(G1/R1/FB1/SP1)。规范性机器可读 schema 实体文件位于顶层 `schemas/`,由 `specification/schemas.md` / `specification/schemas_cn.md` 索引;它们属于本规范,但不复制到 `specification/` 下,避免漂移。这些规范性 schema 使用 Draft 2020-12;完整 Draft 2020-12 行为由测试套件通过 `jsonschema` 验证。`tools/ainp_release_check.py` 内嵌的 stdlib schema 门刻意只覆盖本仓内置 schema 实际使用的关键字子集,包括这些内置 schema 使用的组合/条件关键字,不是通用 JSON Schema validator。完整 release wrapper 在 release 规则检查前,先对 plan/report/high-risk 数据执行该内置 schema 门。家族版本号小写 `v1.0.0`(AISOP `V1.0.0` 为声明的历史例外)。

`specification/standards/` 保存轻量机器可读标准库参考:`AINP_Standard.core.json`、`AINP_Standard.security.json`、`AINP_Standard.ecosystem.json` 与 `ainp-rules-v1.0.0.json`。这些文件为 dashboard 与工具索引核心语义、安全边界、生态/项目包要求和规则族。它们**不是** JSON Schema 镜像,也不是 AISOP flow、AIAP program、runtime extension 或信任证明。

**计划版本纪律**(`generation.version`,必填,semver):

- **MAJOR** —— `acceptance_criteria` 或任一红线(`type ∈ REDLINE_TYPES`)约束的增删改:「什么算合格」谓词翻转,既有 report 对应关系失效。由 G12(version-diff 模式)机器执法、R8(`plan_ref` hash 锁)闭环。
- **MINOR** —— brief/structure/soft 约束调整。**PATCH** —— 错别字/描述。

### 4.1 AINP 项目包

文件家族仍可作为独立文件合法存在,但完整可分发 AINP 项目包 MUST 使用以下结构:

```text
<name>_ainp/
├── AINP.md                 # 项目声明、索引与校验入口
├── ainp/                   # AINP 计划文件夹:plan/report/feedback/generation space
│   └── references/          # 可选:参考材料、模板、brief、spec 快照
└── <name>/                 # 项目内容文件夹:生成内容本身
```

`AINP.md` 刻意沿用 AIAP `AIAP.md` 的大写风格。它是项目声明、索引、人类/AI 自举文档与校验入口,**不是**信任证书。`ainp/` 是 AINP 计划文件夹,保存 generation plan、generation report、feedback、generation-space index,以及可选 reference materials。`<name>/` 是项目内容文件夹,保存真正生成的内容本身。计划文件夹与内容文件夹是项目包的对等组成部分:`ainp/` 说明、约束并记录生成;`<name>/` 承载已生成的内容。frontmatter 必填字段:`protocol`、`authority`、`axiom_0`、`name`、`version`、`summary`、`status`、`plan_dir`、`content_dir`、`plan`、`report`。`feedback` 对 `status ∈ {approved, active}` 的项目包为必填;对 draft/under_review 包可选。推荐字段:`space`、`references`、`artifact_type`、`license`。正文 SHOULD 包含:`Project Declaration`、`Generation Plan`、`Content Artifacts`、`Feedback Loop`、`How To Validate`、`Honesty Boundary`。

`ainp/references/` 为可选目录。它 MAY 保存生成参考材料:协议/spec 快照、模板、brief、style guide、接口说明、政策摘录、研究笔记等。它们不是生成内容,不得被算作 `AINP.md.content_dir` 下的 content artifact。若该目录存在,SHOULD 包含 `reference_manifest.json`,profile 为 `ainp.v1.0.0.reference_manifest`;`AINP.md.references` MAY 指向该 manifest。P11 对"有 references 目录但无 manifest"给 WARN;一旦 manifest 被声明或存在,它必须过 schema、本地 reference/template 路径必须留在 `ainp/references/` 下,记录的本地 hash 必须可重算匹配。`tools/ainp_validate.py` 可校验单个 manifest;`tools/ainp_project_check.py` 校验包内位置与 `AINP.md.references` 布线。`source.type=local_file` 使用 `source.path`,可带 `sha256`;`source.type=external_uri` 使用 `source.uri`,本地工具绝不抓取,也不得带 `sha256`。reference hash 只证明本地完整性,不证明外部权威、最新版本、法律充分性、事实真实性或 runtime trust。

在项目包中,`generationreport.artifacts[].path` 按项目根目录解释。项目检查器可以把包根作为 release artifact sandbox 传入;没有显式 project-root 上下文时,report checker 仍默认以 report 所在目录作为 sandbox。项目包校验还要求每个可在包根内解析的 report artifact 路径必须落在 `AINP.md.content_dir` 声明的内容目录下;畸形或逃逸路径仍由 R3/release 沙箱规则 FAIL。

完整项目包闭环是双向的。plan 经 brief、`content_architecture`、constraints 与 acceptance_criteria 指导内容。`content_architecture` 是声明式内容项目蓝图:点名生成内容根目录、目录、具体文件以及每个文件的 points/requirements。它不是 AISOP 式执行图,不作运行期声明。对 approved/active 项目包,内容经 `AINP.md.feedback` 反馈计划。`AINP.md.feedback` MUST 指向 `ainp/` 下的 `*.generationfeedback.json`,且其 `generation_id` 必须与 plan id 和 report `generation_id` 一致。这只证明闭环布线,不证明反馈明智、完整或外部真实。

## 5. 生成计划书(`*.generation.json`)

规范性机器可读形状见 `schemas/ainp-generation-v1.0.0.schema.json`;schema 索引见 `specification/schemas.md` / `specification/schemas_cn.md`;独立文件家族实例见 `examples/file_family/`,完整文档项目包实例见 `examples/whitepaper_ainp/`,完整程序项目包实例见 `examples/slugify_cli_ainp/`,完整 AIAP package-generation 示例见 `examples/aikp_navigator_aiap_ainp/`。字段组:身份(`id/version/title/summary/status/source`)、`artifact_type(+subtype)`、`brief`、`audience`、`structure[]`(可递归)、`content_architecture`、`inputs[]`(`source/rights/provenance/privacy/consent`)、`rights_policy`、`risk_profile`、`constraints[]`、`acceptance_criteria[]`、`disclosure_policy`、`bindings`、`governance`、`permission`。

关键语义:

- **`risk_profile` 是风险唯一事实源**;`governance.risk_level` 是派生的家族兼容字段,必须一致(G13)。门判定**只读** `governance.approval_required`。
- **`structure[]` 是给人读的建议大纲**。它帮助作者和审查者理解预期产物形状,但不是覆盖率门。机器可绑定的内容锚点位于 `content_architecture.files[].points[]`,这些 points 再通过 `acceptance_refs[]` 绑定到验收标准。
- **`content_architecture` 对独立 plan 可选,对完整项目包必填**。它声明 `root`、可选 `directories[]`、以及具体 `files[]`,每个文件带 `id/path/type/required/summary/points[]`。每个 point 带有序 `requirements[]`,并可通过 `acceptance_refs[]` 指向 `acceptance_criteria`(G16/P10)。这是内容蓝图,不是执行计划;生成可由 AISOP、AISP、AIJP 或其它经授权流水线实现。
- **`intended_audience` 在 v1.0.0 为 advisory 自由文本**——不参与门判定;未成年/弱势受众风险经 `risk_tags`(如 `minor_related`)表达。
- **`consent`**(逐 input):`required=true` 时仅当 `status ∈ {recorded, verified}` **且** `evidence_ref` 非空才可继续(G4)。在 input 上声明 `rights.status = consent_required` 时,该 input 必须同时带 `consent.required == true`(G4)——「需要同意」而无记录,永远不是继续的许可。validator 只证明 consent **带证据引用地被声明了**——不证明 consent 真实有效(须外部/registry/人审)。
- **`provenance`**(逐 input)是申报或证据引用状态,不是完整来源链证明。`provenance.status=externally_verified` 只记录外部核验者被引用;它本身不证明来源真实性,也不是完整 W3C PROV 风格谱系图。input `sha256` 只是重算锚点,不是信任凭证。
- **约束**带 `type ∈ CONSTRAINT_TYPES`。红线约束必须用**控制点数组** `enforced_by[] = {stage, mechanism, assurance, limitations}` 点名强制者(G11)。`soft` 为合法的偏好层,无强制门。
- **`condition` 在 v1.0.0 为说明性文本**:validator 只查存在、绝不求值;机器级门判定由 G6 经 `risk_profile` 承担;受控 `condition_id` 注册表留 a future version。
- **`bindings` 是候选路径,绝不自动执行**(§8)。`execution_binding.protocol ∈ EXECUTION_PROTOCOLS`;plan 合法 ≠ 目标可信。本地非 URI 目标仅 stat 存在性(G9,WARN → strict FAIL);URI 形与 `external/none` 目标属外部核验。
- **`disclosure_policy` 是 report 门映射。** `generator_metadata_required=true` 时,report 必须记录 `generator.{provider, system, content_id, generated_at}`。`watermark_required=true` 时,report 必须在 `disclosure.watermarks[]` 中记录至少一个 `present=true` 且带 `scheme` 的水印证据。这些是给下游透明度使用的证据记录,不证明 provider 可信、水印鲁棒或监管合规。

**assurance 矩阵**——各模式下的控制点效果;最终约束结论仍由 G14/G15 产生:

| assurance | default | strict | release |
|---|---|---|---|
| static | 计入 G14 | 计入 G14 | 计入 G14,但 G15 仍要求至少一个操作性控制点 |
| runtime / evidence_recorded / externally_verified | ✅ | ✅ | ✅ |
| external_required | 计入 G14 | WARN;不能单独满足红线 | 若无操作性控制点同时存在则 FAIL(G15) |
| attested | WARN;不能单独满足红线 | WARN;不能单独满足红线 | 若无操作性控制点同时存在则 FAIL(G15) |
| **unverifiable** | **WARN** | **FAIL** | **FAIL** |

单元格语义是**控制点级**("这个控制点算不算数");**约束级**结论由规则推出。G14 抓在所选模式下没有满足性控制点的红线,并在记录了非操作性证据但仍不足时发出 `AINP_W_G14_NO_SATISFYING_CONTROL`。G15 抓 release 档缺任何操作性(`runtime|evidence_recorded|externally_verified`)控制点的红线,并发出 `AINP_E_G15_NO_OPERATIONAL_CONTROL`。`external_required`、`attested` 与 `unverifiable` 都是诚实记录,永远不是通过凭证。

## 6. 生成报告(`*.generationreport.json`)

验收结论**落 report、永不落 plan**。report 经 `plan_ref.sha256` 锁定它所评判的那份 plan 快照(R8)。每条 `acceptance_results[]` 带合法形状的 `passed/method/evidence[]/verifier/limitations`(R5),与 plan 的 criteria **双向一一对应**(R4)。`overall.conformant` 是**推导值**——所有 fail 级 criteria 通过 ∧ 所有强制门满足——永不可自设(R6)。

强制 report 门必须显式记录,不能从 prose 猜测:每个为 true 的 `disclosure_policy.*_required` 开关,都必须在 report 中记录为满足(R7)。这包括 label、machine-readable metadata、content credential、水印等 `report.disclosure` 记录,以及要求 generator metadata 时的 `report.generator` 记录。任何 `governance.approval_required == true` 的 plan,都必须在 report 中带 `governance_results.approval_gate`,含 method/evidence/verifier/limitations 且 `passed=true`(R9)。这些仍只是证据容器:记录谁/什么声称门已过,不独立证明法律授权、同意有效性、provider 可信、水印可检测性或 credential 真实性。

report 诚实边界:report 是**证据容器,不是绝对真相**。工具 verifier 只证明工具实查的范围;human/external 须记身份/来源/版本/时间。`content_credential.present=true` 只记录存在 credential 或 manifest 引用;`verification_status=externally_verified` 记录外部核验证据,不是本地密码学信任。AINP 参考工具不验证 C2PA manifest、签名、证书链、issuer policy 或 trust list。

若被评判的 plan 声明了 `content_architecture`,report artifacts SHOULD 带 `file_id`,指向 `generation.content_architecture.files[].id`。R10 要求每个 `required=true` 内容文件都被 artifact 覆盖,并要求 `file_id` + `path` 与 plan 一致。这只证明 plan/report 的内容覆盖关系,不证明 artifact 质量或真实性。

## 7. 治理、高风险门与诚实五原则

**高风险定义**:`artifact_type ∈ high_risk_types.artifact_types` ∪ `risk_tags ≠ ∅` ∪ `deployment_scope = mass_public` ∪ `risk_profile.risk_level ∈ {high, critical}` ⇒ `governance.approval_required` 必须为 `true`,且交付必须过 HSAW 人类主权门(G6)。类型归属采用**大小写/分隔符归一化匹配**——忽略空白、`_`、`-` 分隔符,因此 `"Deepfake"` / `"deepfake "` / `"deep fake"` / `"deep-fake"` / `"deep_fake"` 不得靠拼写溜过主权门(risk_tags 保持精确匹配:未知 tag 本就硬 FAIL,fail-closed)。risk_tags 为**申报制**;漏报静态查不出——外部评审兜底。`high_risk_types` 数据文件自身必须保持 `artifact_types[]` 与 `risk_tags[]` 非空;控制数据畸形或为空时 fail closed。

**risk_tag 触发位 → 字段强制映射**(位在 `high_risk_types.v1.0.0.json`):

| 触发位 | 强制字段 | 规则 |
|---|---|---|
| `approval_required: true` | `governance.approval_required == true`;release 前 report 记录 `governance_results.approval_gate` | G6 + R9 |
| `consent_required: true` | ≥1 个 `inputs[]` 带 `consent.required == true` | G4 |
| `disclosure_required: true` | `disclosure_policy.ai_generated_disclosure_required == true` | G8 |

**诚实五原则**(AIXP 家族一贯):

1. **计划 ≠ 产物**——valid/approved 的 plan 只是"要造什么"的声明,不证明产物安全/原创/真实/无害。
2. **自报 ≠ 核验**——rights/consent/provenance/事实为申报制;hash 只证本地完整性。
3. **验收落 report、不落 plan**——plan 立标准,证据落 `*.generationreport.json`。
4. **产物与包声明不得自报信任**——`safe/verified/original/trusted/authentic` 只能由消费方/registry/评审方赋予(G7/P9)。*G7/P9 是精确小写键名的静态近似,可被变更键名/大小写规避;真正的信任判定永远在消费方,不是静态通过。*
5. **approve 只覆盖被 approve 的对象**——批准 plan ≠ 批准其产物;`report.conformant = true` ≠ plan 曾被批准。两条独立状态链,消费方须同时查。

## 8. 安全——plan 是不可信输入

生成计划书跨信任边界传播(store、registry、agent 间)。工具链 MUST:

1. **绝不自动执行 `bindings`**——候选路径需独立授权。
2. **绝不自动下载/打开 `inputs[].source`** URI;绝不展开 `local://`。
3. **绝不信任内嵌 `sha256`**——只重算比较。
4. **绝不因 plan 合法就生成/发布**——valid 只表示结构一致。
5. **把 prompt 注入文本、路径穿越、超大字段当数据、不当指令。** 参考工具拒绝 >10 MB 文件,对 binding 目标仅 `stat()`。
6. **严格解析。** 拒绝重复对象键(解析器差异走私:人审一个值、机器按另一个值执行)、非标准 JSON 字面量(`NaN`/`Infinity`)、以及超过 150 层的嵌套——恶意输入必须得到受控 finding,绝不许 crash。
7. **限定自身输出。** 恶意文件不得无限刷 findings(参考工具在 1000 条处截断并给出显式截断 FAIL)——在不可信输入上耗尽内存是 crash,不是裁决。
8. **绝不读沙箱之外。** 任何本地 hash 重算 MUST 拒绝绝对路径与逃出当前 artifact sandbox 的路径。这同时适用于 release 模式 report artifacts(R3)与 generation-space refs(SP2)。默认 report sandbox 是 report 所在目录;已校验的 AINP 项目包可由 `tools/ainp_project_check.py` 传入包根作为 sandbox。实现 SHOULD 使用 realpath + common-path 检查,避免 symlink、junction 和 `..` 把读取走私到沙箱之外。否则"逃逸路径 + hash 比对"就是任意本地文件的内容预言机。

本节为规范性条款,并镜像于 `SECURITY.md`。

## 9. 反馈与生成空间

`*.generationfeedback.json`(FB1):`generation_id / source ∈ FEEDBACK_SOURCE / verdict ∈ VERDICT`(+ issues 带 `target: plan|artifact|file|point`、`severity ∈ SEVERITY`,可选 `file_id` / `point_id`)。闭合 计划→内容→反馈→修订 环。独立文件家族场景可选;`approved` 或 `active` 的 `<name>_ainp/` 项目包中由 P6 强制必填,让内容评审有结构化路径反馈到计划,并可指向已声明的内容文件/point。

`*.ainp.json` 生成空间(SP1/SP2):索引,条目带 `ref + sha256`。hash 只证**登记时刻**完整性;当 ref 是本地且位于 space 文件沙箱内时,消费方必须重算。SP2 MUST NOT 读取绝对路径或逃出沙箱的 ref;外部/不可解析 ref 只记录 INFO,不能当作已验证。

## 10. 一致性规则

### Plan 侧(tools/ainp_validate.py)

| 规则 | 内容 | 级别 |
|---|---|---|
| G1 | `schema == ainp.v1.0.0.generation` 且 payload key `generation`(强绑定)| FAIL |
| G2 | 必填 `id/version/title/summary/status/artifact_type/brief/acceptance_criteria/governance`;`version` 为 SemVer 2.0.0(拒绝前导零;接受 prerelease/build 元数据);`status ∈ STATUS`;`source ∈ ORIGIN`(若存在);`acceptance_criteria` 非空 | FAIL |
| G3 | `artifact_type` 非空;建议枚举外 → WARN(strict FAIL)| WARN/FAIL |
| G4 | 每 input 有 `source/rights.status/provenance.status`;`consent.required` 无证据或状态不许继续 → FAIL;tag `consent_required` ⇒ ≥1 consent-bearing input;`rights.status=consent_required` ⇒ 该 input 须带 `consent.required == true` | FAIL |
| G5 | 每条 criterion 有 `id/description/severity/verification{method}`;static 须已注册 `check_id`(未知 → WARN,strict FAIL)| FAIL |
| G6 | `risk_profile` 存在且合法;高风险(§7:type/tags/scope/`risk_level ∈ {high,critical}`)⇒ `governance.approval_required == true`;`risk_tags` ⊆ high_risk_types ids | FAIL |
| G7 | plan 不得自报产物信任(任何位置的 `safe/verified/original/trusted/authentic` 键)| FAIL |
| G8 | **所有 plan** 必须声明 `disclosure_policy`;tag `disclosure_required` ⇒ `ai_generated_disclosure_required == true` | FAIL |
| G9 | `bindings` 结构合法;`execution_binding.protocol` 在枚举内;本地目标存在性 → WARN(strict FAIL)| WARN/FAIL |
| G11 | 每条红线约束有非空 `enforced_by[]`,`stage/mechanism/assurance` 值域合法 | FAIL |
| G12 | **仅 version-diff 模式**(`--previous/--current`):验收/红线变更须 MAJOR bump → WARN(strict FAIL);单文件输出 `AINP_I_G12_REQUIRES_VERSION_DIFF` | WARN/FAIL |
| G13 | `governance.risk_level`(若存在)必须等于 `risk_profile.risk_level` | FAIL |
| G14 | 红线只倚 `unverifiable` 且无其它满足档控制点 → default WARN、strict/release FAIL | WARN/FAIL |
| G15 | **release**:每条红线须 ≥1 个 `assurance ∈ {runtime, evidence_recorded, externally_verified}` 控制点 | FAIL(release)|
| G16 | 若声明 `content_architecture`,它必须声明安全相对内容根、非空文件列表、唯一 id、安全路径、必填 summary 与有序 points;point `acceptance_refs[]` 必须引用真实 `acceptance_criteria[].id` | FAIL |
| FB1 | feedback 绑定 + 必填 `generation_id/source/verdict` | FAIL |
| SP1 | space 绑定 + `generations[].{ref, sha256}` | FAIL |
| SP2 | space hash 重算不符 → WARN(strict FAIL);绝对路径或逃出沙箱的本地 ref → FAIL;外部/不可解析 ref → INFO | WARN/FAIL |

G10 已在计划 V3 迁为 report 侧 R8。

### Report 侧(tools/ainp_report_check.py)

| 规则 | 内容 | 级别 |
|---|---|---|
| R1 | profile/payload 绑定 | FAIL |
| R2 | `generation_id` 解析到 plan | FAIL |
| R3 | `artifacts[]` 每项 `id/path/mime/sha256`;release:文件存在且 hash 可重算 | FAIL |
| R4 | `acceptance_results[]` 与 plan criteria 双向一一对应;同一 criterion 的重复 result 拒绝 | FAIL |
| R5 | 每条 result 带合法 `passed/method/evidence[]/verifier/limitations` 形状;畸形 method/verifier/evidence 拒绝 | FAIL |
| R6 | `overall.conformant` 必填(省略不是逃逸路径),且可由 fail 级 results + disclosure/approval 门推导;不许自设 | FAIL |
| R7 | 每个为 true 的 `disclosure_policy.*_required` 开关都有对应 report 侧记录;必需 generator metadata 记录 `provider/system/content_id/generated_at`;必需 watermark 至少记录一个带 scheme 的 present watermark;必需 content credential 须记录为 externally verified | FAIL |
| R8 | `plan_ref.sha256` 匹配当前 plan 或可按 hash 找回的归档 blob;归档 → 仅历史(WARN);都不可得 → FAIL,对当前 plan 验收作废 | FAIL |
| R9 | `governance.approval_required == true` 的 plan 必须带 `governance_results.approval_gate`,且 method/evidence/verifier 形状合法、`passed=true` | FAIL |
| R10 | 当 plan 声明 `content_architecture` 时,每个 required 内容文件必须被 `generationreport.artifacts[].file_id` 覆盖;`file_id` 必须存在,artifact path 必须匹配声明的文件路径 | FAIL |

### Project package 侧(tools/ainp_project_check.py)

| 规则 | 内容 | 级别 |
|---|---|---|
| P1 | 项目根目录存在且命名为 snake_case 的 `<name>_ainp` | FAIL |
| P2 | 项目根必须包含大写 `AINP.md`;小写 `ainp.md` 拒绝 | FAIL |
| P3 | 项目根包含 `ainp/`,且 `AINP.md.plan_dir == ainp/` | FAIL |
| P4 | 项目根包含 `<name>/` 内容目录,且 `AINP.md.content_dir == <name>/` | FAIL |
| P5 | `AINP.md` frontmatter/正文完整,并与目录名和文件路径对齐;路径须为项目根相对且不得逃逸 | FAIL |
| P6 | `approved`/`active` 项目包必须声明 `AINP.md.feedback`;声明的 side files(`feedback`,可选 `space`)须通过内置 JSON Schema 与 `ainp_validate.py --mode strict`;feedback `generation_id` 必须匹配 plan/report generation id;feedback issue 的 `file_id`/`point_id` 必须能绑定到 plan 声明的内容文件/point | FAIL |
| P7 | 声明的 `plan` + `report` 须以项目根为 artifact sandbox 通过完整 release gate;report artifact 路径须落在 `AINP.md.content_dir` 下 | FAIL |
| P8 | 委托 release gate 后,report 的 `overall.conformant == true`;通过 `AINP_E_RELEASE_NOT_CONFORMANT` 等 release 族 finding 表达,不另设专属 P8 码 | FAIL |
| P9 | `AINP.md` 不得通过 `safe/verified/original/trusted/authentic` 等字段自报产物信任 | FAIL |
| P10 | 完整项目包必须声明 `content_architecture`;其 `root` 与每个内容文件路径都必须解析到 `AINP.md.content_dir` 下 | FAIL |
| P11 | 可选 `ainp/references/` 可保存参考文件、模板、brief 与快照;有目录无 manifest 时 WARN;manifest 一旦声明或存在,必须过 schema,本地路径必须留在 `ainp/references/` 下,记录的 hash 必须可重算 | WARN/FAIL |

### 外部核验边界(规范性)

以下**超出**静态校验,合规工具永不声称:rights/consent/provenance 的真实有效性;来源真实性;事实准确性;scanner 可靠性;provider 可信性;watermark 存在性、鲁棒性或可检测性;content credential 有效性;C2PA manifest/signature/trust-list 有效性;人类批准是否真由授权者作出。合规 validator 只输出 `PASS structure-valid` / `WARN external-verification-required`,**绝不**输出 `PASS legally-safe` / `PASS rights-verified` / `PASS content-trusted`。

机器可读码格式 `AINP_[EWI]_<CODE>`(E=fail,W=warn,I=info)。

## 11. 三档模式

| 模式 | 语义 |
|---|---|
| default | 结构规则 FAIL;unverifiable 红线 WARN(G14);本地绑定目标缺失 WARN |
| strict | + 未知 static `check_id`(G5)/建议枚举外/绑定目标缺失/SP2 不符/G12 升 FAIL;unverifiable 红线 FAIL |
| release | + G15 生效;完整 release 门为 `tools/ainp_release_check.py`:内置 JSON Schema 先通过(plan/report/high-risk 数据)+ plan release-valid + `generationreport` 存在 + report release-valid + artifact hash 可重算 + `overall.conformant == true`;项目包使用 `tools/ainp_project_check.py`;只跑 plan release 不是完整 release 门 |

## 12. 家族连带绑定(双向才成闭环)

| 协议 | 连带改动 | 优先级 |
|---|---|---|
| AIIP | intent 增可选 `ainp_binding` | 建仓后 |
| AIJP | job/worktree 增可选 `generation_ref`("引用不复制")| 建仓后 |
| AIKP | 知识条目增 `generated_from`("不把未验证内容写成事实知识")| 后续 |
| AIAP | creator/package generation 可引用 AINP `references`、`content_architecture` 与 lifecycle evidence;见 `examples/aikp_navigator_aiap_ainp/` | 建仓后 |
| AIIP(反向对齐)| AIIP rule 11 的门源双路收敛为单一 `governance.approval_required` | 低 |

## 13. 法律对齐边界

*AINP 提供可支撑透明度/人类监督治理流程的机器可读计划与证据结构,但 AINP 校验不是法律合规认证。* 对 Reg (EU) 2024/1689 Art.14(人类监督)/Art.50(透明度)、中国 AI 生成合成内容标识规则、加州 AI 透明度规则的引用仅为对齐参考。

## 14. 版本史

- **v1.0.0** —— 首发:文件家族、带大写 `AINP.md` 且 `ainp/` 计划文件夹与 `<name>/` 内容文件夹对等、并带 approved/active feedback 闭环的完整项目包结构、可选 `ainp/references/` 参考/模板 manifest、G1–G16/FB1/SP1/SP2/R1–R10/P1–P11、三档、high_risk_types 数据文件 + schema、含 schema-aware release gate wrapper 与 project checker 的参考工具、teeth 反例。相对计划 V5 的建仓期补全与对抗审计补全均记录于 CHANGELOG。

---

Align Axiom 0: Human Sovereignty and Wellbeing. AINP v1.0.0. www.ainp.dev
