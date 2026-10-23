# 状态 Schema 参考

`docs/ai-workflow/` 下三个机器可读文件的字段定义。校验器：`python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>`（退出码 0=通过，1=有错误，2=用法/目录缺失）。

## state.json（项目当前位置，唯一）

| 字段 | 类型 | 说明 |
|---|---|---|
| version | int | 固定 1 |
| project | string | 项目名，非空 |
| currentStage | enum | `brainstorm` `design` `plan` `execute` `verify` `ship` `project-complete` |
| currentMilestone | string\|null | 活动里程碑 ID，须在 milestones.json 存在 |
| currentWave | int\|null | 活动 Wave 序号 |
| currentSlice | string\|null | 活动任务 ID，须在 tasks.json 存在；Wave 并行时置 null，以 currentWave 定位 |
| gateStatus | object | 三个 Gate 各自状态：`project` `slice` `release`，值 ∈ `pending` `conditional` `passed` `blocked` |
| headless | bool | 本会话是否无人值守（headless 会话**开始时即置 true**——这是发布门禁的武装开关；填非布尔值按 true 处理并给 warning）。**headless=true 时 release 不得为 passed**（校验器强制） |
| pendingDecisions | string[] | decisions.md 中待确认项 ID，与文档内 `状态：proposed` 条目对齐 |
| blockers | string[] | 当前阻塞项（任务 ID 或一句话描述） |
| lastUpdated | string | ISO 8601 带时区，每次写状态刷新 |
| lastHandoff | string\|null | 最近 handoff 文件路径 |

`gateStatus.release=passed` 时的联动检查（校验器强制）：`release.md` 存在、**非空、至少含一个已勾选确认项（`[x]`）**、且无任何写法的未勾选框（`- [ ]`、`1. [ ]`、裸 `[ ]`、全角 `［ ］` 都拦；闭合围栏（``` 或 ~~~）内的内容按代码块剥离，**未闭合**围栏按正文处理，fail-closed）；`blockers` 为空且必须是数组（不可豁免条②的机器化）；`headless` 不为 true（条④的机器化）。

## tasks.json（任务与依赖边）

```json
{ "version": 1, "tasks": [ {
  "id": "T001",
  "title": "普通直播间进场动效端到端",
  "milestone": "M1",
  "wave": 1,
  "status": "pending",
  "blockedBy": [],
  "owner": "agent",
  "files": ["src/..."],
  "writeScopes": ["src/gifts/", "test/gifts/"],
  "acceptance": "Given… When… Then…",
  "verify": "npm test -- gifts",
  "requiresDecision": [],
  "riskTier": "medium",
  "humanApprovers": ["张三", "李四"],
  "approvedAtCommit": "1a2b3c4",
  "reviewRounds": 0,
  "evidence": null,
  "notes": ""
} ] }
```

- **status 枚举**：`proposed`（拆分未获批准）→ `pending` → `active` → `ready_for_review` → `verified` → `shipped`；旁路 `blocked`、`awaiting_human_evidence`、`cancelled`。
- **迁移规则**：`ready_for_review`→`verified` 必须有 `evidence`——路径相对项目根、**必须位于 `docs/ai-workflow/evidence/` 下，文件名等于任务 ID 或以 `任务ID-`/`任务ID.` 开头**（防 T1 借用 T10 的证据）、文件**存在且非空**（均为校验器强制；命名惯例 `<task-id>-<日期>.log`）；`verified`→`shipped` 必须过 Release Gate（出现 shipped 而 release≠passed 时校验器给 warning——可能是里程碑收口后的重置，需人工核对归档记录）；`proposed`→`pending` 必须有 decisions.md 的批准记录（文档规则，校验器不查）。**旁路态出边**：`awaiting_human_evidence` → 人工验证完成、按 evidence 规则留证并注明验证者与日期后，迁 `verified`；`blocked` → 阻塞原因消除后回到进入 blocked 前的状态并重新验证（不得直接跳 verified）。
- **blockedBy**：只允许引用存在的任务 ID；不允许自环与循环依赖（校验器查环）。
- **requiresDecision**：可选，决策 ID 数组（指向 decisions.md 的 D00x）。任一引用决策非 `approved` 时，任务状态只允许 `proposed` 或 `blocked`——人工保留决策的机器门禁（校验器强制）。
- **writeScopes**：同 Wave 并行任务必须互不相交（execute 开工前实测）。
- **reviewRounds**（可选，非负整数）：本任务已被审查的轮次。>3 且状态不在 `verified`/`shipped`/`cancelled` 时报错——审查必须会结束，满 3 轮转 `blocked` 并把方案重审记进 decisions.md；人工批准继续后把该值归零（校验器不查归零的合法性，由 `/ai-workflow-review` 的 State 轴抽查）。
- **riskTier / humanApprovers**（可选，成对使用）：`riskTier` ∈ `low` `medium` `high`，人类签字人数下限依次为 1/2/3；`humanApprovers` 是姓名字符串数组，去重后计数，空白名字与 `agent`/`ai`/`bot`/`llm`/`assistant`/`copilot` 一律不算人类（Agent 的结论不占名额）。标了 `riskTier` 就必须给 `humanApprovers`，人数不足报错；分档判据见 verify 模块「风险分档决定要几个人签字」。
- **approvedAtCommit**（可选，7–40 位十六进制）：人类签字钉住的提交。校验器在该 sha 之后查 `files`（精确）与 `writeScopes`（前缀）是否仍被提交触及——触及即报错（签字已失效，重跑验证与审批）；sha 在仓库中不存在报错；git 不可用/不在仓库中/任务没有改动面时降为 warning 并提示人工核对。
- **向后兼容**：以上四项均为可选字段，**字段缺失即不触发对应检查**（`verified`/`shipped` 缺 `riskTier` 只给 warning）。存量项目升级校验器后仍应通过。
- **acceptance / verify**：除 `cancelled` 外必填；verify 必须是可自动执行的命令（无法自动化的观察点拆出去标 `awaiting_human_evidence`）。

## milestones.json（里程碑与 Wave）

```json
{ "version": 1, "milestones": [ {
  "id": "M1",
  "title": "最小闭环：发布→时间线→点赞",
  "status": "active",
  "demo": "新用户发布图文后，另一账号能在时间线看到并点赞",
  "waves": [ { "wave": 1, "tasks": ["T001","T002"] } ]
} ] }
```

- **status 枚举**：`planned` `active` `verified`（demo 已跑给用户看/留有证据）`shipped` `cancelled`。
- `demo` 必填（cancelled 除外）——说不清"做完能演示什么"的里程碑还没拆到位（垂直切片判据上移到里程碑层）。
- `waves` 每项必须含 `wave`（正整数）与 `tasks`（引用存在的任务 ID）；同一任务不得出现在两个 Wave。

## 人读文档的机器可查约定

- **decisions.md**：每条决策一个小节 `## D00x · 标题`，含 `状态：proposed|approved|rejected|superseded`；校验器统计 `proposed` 条数并与 `state.json.pendingDecisions` 长度比对（不一致给 warning）。fenced 代码块（``` 或 ~~~）内的内容不算决策（格式示例安全）；决策 ID 后紧跟字母数字（如 `## D001x`）不被识别为 D001（fail-closed）；决策 ID 重复报错，以首个为准。状态行必须写成列表形式 `- 状态：xxx`——裸 `状态：` 行不识别（fail-closed 方向，宁可不认也不误认）。
- **risks.md**：表格行含状态列；`accepted` 行必须有 owner 与日期（本条校验器不强制，由 `/ai-workflow-review` 的 State 轴抽查）。
- **sessions/**：`<YYYY-MM-DD>-<slug>.md`，每会话一篇；**handoffs/**：`<YYYY-MM-DDTHHMM>-<slug>.md`；**audits/**：`<YYYY-MM-DD>-<slug>.md`。
- **evidence/**：`<task-id>-<YYYY-MM-DD>.log`（命令+完整输出）或 `.json`/`.png` 等原始产物。
- **review-contracts/**（可选，校验器不强制存在）：`<module>.md` 模块审查契约——这个模块"什么叫出事了"（一句大白话）、跳过哪些目录、挑刺上限、发现必须带文件名与行号；也可用仓库根 `REVIEW.md` 写全局版。契约过期本身是 Standards 发现项。
- **regressions/**（可选，校验器不强制存在）：`<YYYY-MM-DD>-<slug>.md` 错题本——现象、最小复现、判定标准、本该拦住它的那道检查。改规则/提示词/工具/模型前必须全跑历史用例，分数不涨不准保留改动。

## 与既有约定的一致性

- 项目级 handoff 存仓库 `handoffs/`（长期接力、进 Git），**有意区别于** Matt Pocock handoff skill 的"存系统临时目录"条款——那是会话级临时交接的约定；两者都必须遵守引用不复制、脱敏、带建议 skills、按用途裁剪。
- 状态文件全部进版本控制：恢复包即提交历史（Journal 进 Git 是本套件自定的状态落盘约定）。
- 三个 JSON 的 `version` 约定为 1，≠1 时校验器给 warning 不拦截。

## 防伪边界（诚实声明）

校验器防"诚实的错误"，并抬高伪造门槛（证据路径规则、release 清单联动、requiresDecision 决策门禁）；但 `headless` 字段依赖执行 agent 如实申报、证据文件的内容真伪无法自动判定。蓄意伪造由 `/ai-workflow-review` 的 State 轴（重跑 verify 命令、核对 Git 历史）与人工抽查兜底——这正是"不要让 AI 自己证明自己正确"在项目层的延伸。

校验器还包含未在本文档逐条列出的防御性检查（损坏输入报错不崩溃、数组与元素类型、ID 重复、嵌套深度守卫等）；行为以 `validate_state.py` 为准，文档中**对校验器行为的描述**与代码不一致时按文档 bug 处理并修文档（纯流程条款——如批准记录、演示要求——不由校验器强制，不属此条范围）。
