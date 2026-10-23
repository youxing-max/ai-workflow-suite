# ai-workflow-suite

一套把「AI 写代码」变成「AI 走工作流」的 agent skills。六个阶段各管一类失控方式：需求访谈一次只问一个决策、边界落成文件、"做完了"必须有新鲜证据、跨会话靠磁盘上的状态恢复。装进 Claude Code / Codex CLI / omp 就能用。

一句话讲清它干什么：**不是让 AI 更聪明，是让 AI 别自作主张，并且让别人能验收。**

本套件为自研：六阶段规则、状态校验器和 CLI 安装器都在这个仓库里独立维护，不依附任何外部课程、专栏或第三方 skill 包。

---

## 为什么需要这套东西

你大概率遇到过这个场面：

> 你说"给后台加个导出功能"。AI 十分钟写完，跑通了，告诉你完成。你没问"全量导出还是当前页导出"，它也没问，顺手选了"当前页"——因为它得给你一个能跑的东西。测试它写了，但没覆盖你真正在意的权限分支。你三天后上线才发现，需求里那句"只有管理员能导全量"从头到尾没人落实过。

问题不在模型能力，在这几层工程环境没人管：**需求没对齐、边界没落位、任务没拆分、结论没独立验证**。而 AI 会用一个貌似合理的答案把这几处默认填上，填得毫无痕迹。

> Agent = Model + Harness。模型提供智能；工具、上下文、权限、状态、执行约束这一层工程环境，决定智能能不能被可靠地用出来。

所以这套 skill 做的不是"提醒 AI 别作弊"，而是把关键节点变成**能验收的东西**：

- **Skill** 规定 Agent 怎样行动（例如：一次只问一个决策，不许一口气抛五个问题）；
- **Artifact** 保存已经确认的事实（写进仓库的文件，不留聊天记录）；
- **Gate** 决定什么时候可以继续（关键取舍没确认，就不许开始写实现）。

Artifact 和 Gate 只铺在不确定性最容易失控的地方，不是六段平均用力。

**六阶段是一张风险地图，不是流水线：**

| 阶段 | 管住哪类失控 | 主要产物 |
| --- | --- | --- |
| 1 Brainstorm | 需求没对齐、AI 代你拍板 | 决策记录、业务规则清单 |
| 2 Design | 边界含糊、"隐藏"只做前端不渲染 | Spec、测试接缝、必要时 ADR |
| 3 Plan | 任务水平切碎、没有验收断言 | 工单 + 依赖边 + 每单"怎样算完成" + 风险档 |
| 4 Execute | 一次改十几个文件、测试后补自证 | 小步 Diff + 可重复的运行记录 |
| 5 Verify | 自称完成、FAIL 被 PASS 平均掉、审三轮还收不了尾 | 测试输出 + 双轴 Review 报告 + 人类签字名单 |
| 6 Ship | 交接丢失、敏感信息外流、回滚要重新发版 | PR、一页发布计划（含开关与熔断）、Handoff、经验回流 |

---

## 30 秒装上

```bash
npm install -g ai-workflow-suite
ai-workflow-suite
```

第二条命令会自动探测你机器上已经装了哪些工具（`~/.claude`、`~/.codex`、`~/.omp`、`~/.agents`、`~/.qoder-cn`），把 10 个 skill 放进各自的 skills 目录。没装的工具一个字节都不写，不编辑任何配置文件。

只装指定工具：

```bash
ai-workflow-suite claude codex omp
```

装到指定目录（比如某个仓库自带的 `.claude/skills`）：

```bash
ai-workflow-suite --dir ./.claude/skills
```

不想留全局命令，也可以一次性跑：

```bash
npx ai-workflow-suite
```

装完**重启一下你的 agent 工具**让它重新扫描 skills。然后：

```
/ai-workflow-project          # 大项目
/ai-workflow                  # 单个需求
```

> 这套 skill **全部设了 `disable-model-invocation: true`**：只有你显式拉起才会生效，模型不会也不应该自己调过去。如果你的工具没有斜杠命令入口，就直接点名："用 ai-workflow 走这个需求：×××"。这是有意设计——套件里的教训之一就是"自动触发不可靠，实测有一次都没读取过，所以入口交给人显式调用"。

安装位置：

| 工具 | 路径 |
| --- | --- |
| Claude Code | `~/.claude/skills` |
| Codex CLI | `~/.codex/skills` |
| omp | `~/.omp/agent/skills` |
| 通用根 | `~/.agents/skills` |
| Qoder | `~/.qoder-cn/skills` |

---

## 教程 A：一个需求走一遍

适合跨模块、一个会话做不稳、涉及权限/资金/迁移的需求。**一次性脚本、临时数据转换别走这套**——流程成本高于任务本身就是最大的浪费。

### 第 1 步：先判边界，决定要不要走

拉起 `/ai-workflow`，它会先跟你确认命中了哪条风险信号（命中任一条就必须走流程，哪怕任务看起来很小）：

1. 改动跨多个模块或仓库；
2. 一个会话很难稳定做完；
3. 涉及权限、资金、隐私、迁移或兼容；
4. 需求里有需要**人**承担后果的取舍；
5. 要多人接力或长期维护；
6. 同类问题在 Review 里反复出现；
7. 代码能跑，却很难判断需求是否做完整。

升级之后仍按风险缩放深度：Artifact 可以合并成一页，只走会失控的那几个 Gate，不机械走满六段。

### 第 2 步：Brainstorm——它问，你拍板

这一段的规则是**一次只问一个决策**，每个问题带一个推荐答案和理由。你要防的是这两种伪对齐：

- 它一口气抛五个问题、没编号也没推荐，你随手答完，等于什么都没确认；
- 把规则写成形容词（"要快""要安全"），后面没法验收，只能默默砍范围。

产出：决策记录 + 业务规则清单。反直觉的细节必须落纸，例如"全量导出仅限管理员，且审计日志记一条"。

Gate：**关键取舍没确认之前，不许调用任何实现类动作。** 没等到答案就停在显式的待确认状态，不许"先按常见做法写着"。

### 第 3 步：Design——把"要什么"落成 Spec

按七节写 Spec：Problem / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Notes。同时定**测试接缝**（越少越好，理想是 1 个，且要跟你确认）。

这一段最容易翻车的三处，套件里都写明了对策：

- "隐藏"只做了前端不渲染，数据照样返回给用户 → 边界要落在数据层；
- 身份判断散落各层 → 责任归属放进拥有完整上下文的入口；
- 设计只留在聊天记录里 → 必须落文件（仓库里的 Spec / ADR）。

Gate：边界与测试入口确认，没有成型 Spec 不拆任务。

### 第 4 步：Plan——切垂直切片

每个任务必填：

- `acceptance`：给定…当…那么…（可检查的断言，不是形容词）；
- `verify`：一条能自动执行的命令；
- `files` / `writeScopes`：会碰哪些文件；
- `blockedBy`：依赖谁。

切片的四条规矩：**窄而完整地穿层**、**能独立演示**、大小以"一个全新会话能稳定做完"为准（防 context rot）、需要的前置重构先做（prefactoring）。

明确禁止的切法：水平拆分（先全写后端再全写前端）、"v1 先做基础版"这种隐性砍范围、verify 写成人工步骤、工单只有动作没有行为。

Gate：拆分要经过你拷问批准（粒度、依赖、该不该合并），每个任务都能回答"怎样算完成"。

### 第 5 步：Execute——小步 + 当场验证

循环是：读切片 → 建验证入口 → 最小修改 → 立即验证。观察点来自 Spec，不许临场发明。`RED → CHANGE → GREEN` 才算闭合，测试后补等于自证。

一个切片 = 一个可回滚单元。`done` 的含义是"可以送去评审"，不是"完成了"。

Gate：当前切片要有**新鲜、可重复**的证据。

### 第 6 步：Verify——换一个人来判

验证者用全新上下文，**重新跑** verify 命令（引用旧输出不算新鲜）。报告分 Standards（合不合规范）和 Spec（有没有做满、有没有偷做范围外的东西）两轴**分列**，禁止合并重排——合并会让 FAIL 被 PASS 平均掉。

风险接受和误报过滤留给你判断。不可自动化的路径标 `awaiting_human_evidence`，UI 行为必须"观察面对齐"而不是只看 HTTP 200（界面类改动把截图和设计稿一起放进 `evidence/`）。

两条收敛与审批的硬规矩：

- **审查必须会结束**：同一任务最多 3 轮，第 2 轮起只看新增 diff，第 4 轮不许自行打开——满 3 轮转 `blocked` 并把"方案是不是错的"交回给你（`tasks.json.reviewRounds` 由校验器核对）。
- **风险档决定几个人签字**：`riskTier` = `low` / `medium` / `high`，人类签字下限 1 / 2 / 3；分档只看改动本身的风险（计费、隐私、CI 配置、会被全库抄的架构模式属 `high`），不看代码是谁写的。Agent 的"通过"不占名额；签字之后又推了新提交，前面的审批作废（`humanApprovers` / `approvedAtCommit` 由校验器核对）。

人只审机器审不好的事：该不该做、高危区、会被抄的架构模式、合入前核证据、上线后兜底。纯风格挑刺不上桌。

Gate：没有新鲜验证不许称完成；Blocker 没清零、签字不达标或已失效，不许进发布。

### 第 7 步：Ship——收口 + 回流

PR、一页发布计划（依赖顺序、回滚、灰度开关写进仓库）、Handoff、经验回流。交接八件事按模板写，四硬条款：**引用而不是复制**、临时材料不放工作区、带上 suggested skills、脱敏裁剪。

发布计划里的回滚必须是**关开关**，不是重新发版一次：开关位置、关闭步骤、关闭之后退回什么状态，三样都写进 `release.md`；合并后先给内部吃几天狗粮，再放外部流量。

**熔断器**：`release.md` 记了一次回滚或线上事故，下一里程碑的人工审批档位整体上调一级（`low`→`medium`→`high`）并强制一次全量审计；解除收紧要人工确认并记进 `decisions.md`。事故同时写进 `regressions/<日期>-<slug>.md`：现象、最小复现、判定标准、本该拦住它的那道检查。这道保险丝没装上之前，不要把更多改动塞进零人工审批通道。

PRD 末尾留"遗留问题"和"数据复盘"两节。Handoff 不只发布时写，跨会话随时写。

Gate：交接存在、引用有效、敏感信息清零、开关与回滚可执行且熔断器已记录。

---

## 教程 B：一个项目走一遍

0→1 产品、多里程碑、多会话多工具接力——这类**指挥层**换成 `/ai-workflow-project`。它是指挥台，**只调度不亲自写业务代码**，阶段方法论仍然回头引用主 skill 的 `references/stage-*.md`（单一事实源，不复制一份）。

```
init（建状态）→ project.md（目标/非目标/成功指标）→ 切片级 Spec
  → 每条垂直切片循环：plan → execute → verify
  → 里程碑演示 → ship
  → 会话边界随时 recover / handoff
```

### 第 1 步：建状态

```
/ai-workflow-init
```

它在工作仓库里建出 `docs/ai-workflow/`：复制 7 个常驻文件、建 4 个子目录，已存在的文件不覆盖（`release.md`、`handoff.md`、`review-contract.md`、`regression.md` 只作为格式模板，用到时再复制进去）。

```
docs/ai-workflow/
├── project.md        目标 / 非目标 / 成功指标 / 决策 owner 表
├── state.json        当前阶段、里程碑、三类 gate 状态（机器读）
├── roadmap.md        里程碑的人读地图 + 遗留问题 + 数据复盘
├── milestones.json   里程碑清单（机器读）
├── tasks.json        切片任务：acceptance / verify / writeScopes / blockedBy / riskTier
├── decisions.md      D00x 待确认决策（owner + 截止时间）
├── risks.md          风险：触发器 / 缓解 / owner
├── evidence/         验证证据日志：<task-id>-<日期>.log
├── handoffs/         跨会话交接
├── sessions/         会话记录
├── audits/           三轴审计报告
├── review-contracts/ 模块审查契约（可选，用到再建）
└── regressions/      错题本（可选，用到再建）
```

注意 init 完成后**不会宣称"已经可以开发了"**：它的完成条件是校验器退出码 0 且目标/非目标/owner 三节非空。

### 第 2 步：定项目门

把目标、非目标、成功指标、决策 owner 写进 `project.md`，你确认后 `gateStatus.project = passed`；如果还有待确认决策，最高只能置 `conditional`。

### 第 3 步：设计先行，只切第一条垂直切片

按 stage-2 把"要什么"落成**切片级 Spec**（放 `docs/ai-workflow/specs/` 或项目既有规范位置，路径记进 `roadmap.md`）。第一个里程碑只做切片级 Spec，不做全产品 Spec。

然后 `/ai-workflow-plan`：只规划到"能端到端演示"为止，不规划整个产品。

### 第 4 步：逐切片推进

`/ai-workflow-execute` → `/ai-workflow-verify`。

开工四前置（缺一条不许动）：

1. 依赖任务已 `verified`；
2. `decisions.md` 里相关决策已批准；
3. 状态校验器是绿的；
4. `git status` 实测各任务的 `writeScopes` 不相交。

并行 Wave 的硬规则：**同一 Wave 的任务 writeScopes 必须不相交、且彼此无依赖边**；共享文件、契约变更、数据迁移一律串行。要改契约的话，既有测试必须进 `writeScopes`。

证据落在 `evidence/<task-id>-<日期>.log`；`tasks.json` / `state.json` 只由编排者回写，证据日志只追加不改写。作者不审自己的活，做完置 `ready_for_review`。

### 第 5 步：里程碑演示 → ship

Release Gate 全绿才准发布：任务全部 `verified`、`blockers` 为空、`requiresDecision` 全部 `approved`、`release.md` 勾选项齐全（顺序/回滚/灰度开关/监控/值班 + 风险接受/灰度方案/发布窗口三项人工确认）；发布范围内每个任务的风险档位与签字人达标、`approvedAtCommit` 之后没有新提交触及该任务；回滚靠关开关（不重新发版）验证过；本周期若有回滚/事故，档位是否已上调一级。

`/ai-workflow-ship` 收口六步：全量 review（审出新 Blocker 会把 release 回置 `blocked`）→ 规范记忆写回 Spec/ADR、过程材料归档 `archive/<日期>-<里程碑>/` → 写 sessions/handoffs → 回填 roadmap 两节 → 经验回流（只收"会反复影响工程判断"的规则）→ 置 `shipped` 后把 `release` 重置为 pending。项目完结补一份"实际结果 vs 当初指标"的对照。

### 第 6 步：会话断了怎么办

新会话第一句话：

```
/ai-workflow-recover
```

它会：先跑校验器（**状态坏了比没有状态更危险**，红了先修）→ 按序读 `state.json` → 最近的 `handoffs/`（没有就读 `sessions/`）→ 活动任务的 acceptance/verify/evidence → `decisions.md` 里待确认项 → `risks.md` 未关闭项 → 拿 `git status` / `git log` 对照 `tasks.json`（有游离改动说明状态过期，先归属）→ 出一份恢复报告，**等你确认才继续动手**。

一条判断规则值得单独记住：**聊天里说过但文件里没有的，视为未发生**（要么补录并标明来源，要么进待确认）。

预防动作：每个会话结束都写状态、上下文用到七成时写 handoff、状态目录进 Git。

### 第 7 步：定期三轴审计

`/ai-workflow-review` 审的是项目而不是 diff，全新上下文只读文件：

- **Standards 轴**：架构边界、规范、安全实践（证据 = 代码 + ADR）；
- **Spec 轴**：每条功能需求可追溯到切片和验收断言，Out of Scope 有没有被偷做（证据 = `project.md` + Spec + `tasks.json`）；
- **State 轴**：文件说的和实际做的是不是一致、证据链是否完整、有没有伪造状态（证据 = 校验器 + `evidence/` + git）。

三轴**分列**报告，不做合并也不平均，发现项标 Blocker/Major/Minor + 严重/顺手改/存量 + 位置 + 证据，落到 `docs/ai-workflow/audits/<日期>-<slug>.md`，Blocker 同步进 `state.json.blockers`。审计只开 fix 任务不改码，修完重跑到 0 Blocker。

另外两件它也会查：

- **审批链抽查**：随机抽 20% 已签字任务，核对 `riskTier` 档位与 `humanApprovers` 人数是否达标、名单里混进了谁、`approvedAtCommit` 之后有没有新提交；
- **契约与错题本**：`review-contracts/` 里的条目还成立吗（契约过期本身就是发现项，反复误报的改契约而不是改审查者）；改规则、改提示词、换工具或换模型之前，`regressions/` 的历史用例必须全跑一遍，分数不涨的改动不保留。

---

## 机器 Gate：校验器到底拦什么

`validate_state.py` 是这套套件里唯一"机器判定"的门禁。设计目的是**防诚实的错误、抬高伪造门槛**——防伪的最终防线是三轴审计和 Git 历史，不要指望脚本能识破一切。

```bash
python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root> [--json]
```

退出码：`0` 通过 / `1` 有错误 / `2` 用法错误或状态目录缺失。

它检查的具体规则（都是能一句话判定的那种）：

- 7 个必需文件和 4 个必需目录在不在；
- `headless = true` 时 `gateStatus.release` **不得**是 `passed`；
- `blockedBy` 悬空引用、自环、循环依赖；
- 声称 `verified` / `shipped` 的任务，其 evidence 必须落在 `docs/ai-workflow/evidence/` 下、文件名等于任务 ID 或以 `ID-` / `ID.` 开头，且内容非空；
- `requiresDecision` 引用的决策若不是 `approved`，任务只能停在 `proposed` 或 `blocked`；
- `currentSlice` / `currentMilestone` 必须在对应 JSON 里真实存在；
- 同一 Wave 内的任务不得跨 Wave；
- `release = passed` 联动要求：`blockers` 为空、`release.md` 非空且没有未勾选的复选框（含全角 `［ ］`，围栏代码块内会剥离，未闭合则 fail-closed），并且至少有一个 `[x]`；
- **审查轮次封顶**：`reviewRounds > 3` 而任务还没收口（不在 `verified`/`shipped`/`cancelled`）报错；
- **签字人数下限**：标了 `riskTier` 就必须有 `humanApprovers`，去重后 `low` ≥1、`medium` ≥2、`high` ≥3，空白名字和 `agent`/`ai`/`bot`/`llm` 一律不算人类；
- **审批失效**：`approvedAtCommit` 之后仍有提交触及该任务的 `files`（精确）或 `writeScopes`（前缀）时报错；sha 在仓库里不存在也报错，git 不可用则降为 warning 提示人工核对；
- 上述三项**都是可选字段**：字段缺失就不触发，`verified`/`shipped` 缺 `riskTier` 只给 warning——老项目的状态文件升级校验器后照样通过。

`docs/ai-workflow/` 里没有 `specs/` 这个目录——`init` 不建它，它只是 `project.md` 里你可以指定的一个存放路径。

---

## 无人值守模式：谁能进、什么绝不代拍

进入条件是**调用方在提示词里显式声明**无人值守。交互会话不得自行判定"反正没人回答我"然后跳过提问。

进入后三条替换动作：

1. 需要拍板的决策改写成待确认清单（推荐假设 + 理由 + 后续怎么调整），继续推进；
2. Gate 记为"条件通过 · 待人工拍板"；
3. 原本要你触发才执行的 skill 可以直接执行，但必须记进待追认。

四条**不可豁免**（封闭清单，无人值守也不例外）：

1. 没有新鲜、可重复的证据，不许称完成；
2. Blocker 未清零，不许发布；
3. 接口响应即契约（返回了什么就是什么，别猜）；
4. 发布与灰度决定、风险接受、以及项目级人工保留决策（产品取舍、法务/合规/隐私口径、资损相关逻辑）**必须人工确认**——无人值守走到这里就停在 `blocked`，不许代批。

人类签字也不因无人值守而免除：headless 会话里 Agent 的"通过"依旧不占审批名额，`medium` / `high` 档任务到 Release Gate 就停 `blocked` 等人。若这一周期已经记了回滚或事故，下一里程碑档位整体上调一级，收紧解除前不要扩大零人工审批的改动面。

---

## 十个 skill 各管什么

| Skill | 干什么 |
| --- | --- |
| `ai-workflow` | 地图层：六阶段、判边界、无人值守规则、11 条 lessons |
| `ai-workflow-project` | 大项目指挥台，只调度不写业务代码 |
| `ai-workflow-init` | 建 `docs/ai-workflow/`（7 个常驻文件 + 4 个子目录） |
| `ai-workflow-state` | 会话首尾的状态读写协议 + schema + 校验器 |
| `ai-workflow-plan` | 里程碑 / Wave 调度与切片拆分、每任务风险分档 |
| `ai-workflow-execute` | 切片执行调度、四前置、证据回写 |
| `ai-workflow-verify` | 独立验证（fresh 上下文重跑）+ 签字分档 + Release Gate |
| `ai-workflow-recover` | 跨会话 / 崩溃恢复 |
| `ai-workflow-ship` | 发布收口、归档、回滚开关与熔断器、经验回流 |
| `ai-workflow-review` | 三轴项目审计（Standards / Spec / State）+ 模块契约、错题本 |

主 skill 里另带 8 份 references（六个阶段各一份 + `lessons.md` + `tool-selection.md`），`ai-workflow-state` 带 schema 和两个 Python 工具。套件内部引用按"本文件所在目录的父目录"自定位，整套拷到任何 skills 目录都直接成立，不用改路径。

**11 条 lessons 一览**（都是踩出来的，值得先扫一遍）：

1. 枚举式规则一定漏，改成按类别写 + 穷举核对；
2. 环境事实（调用方式、路径）先 grep / ls 实测，别凭印象；
3. 自动触发不可靠（实测一次都没读取过），入口交给人显式调用；
4. 同名异义要加限定词；
5. 认证之后任何一次编辑都会让前面的结论失效；
6. 校验脚本先拿正负样本自证，再去校验别人；
7. `set -e` 配 `[ ] && echo` 会静默截断；
8. 作者自评必然漏项，走 fresh-context 双轴复核；
9. 个人解读不能当硬验收标准；
10. 机器门禁的 fail-open 三件套（空容器 / null / falsy），先归一再判类型再看业务；
11. 形容词式需求必须拆成可检查断言，否则默默砍范围——HTTP 返回 200 不等于 UI 可用。

---

## 更新、卸载，以及 sync.py 是干什么的

**更新套件本身**——重跑安装器，只改有变化的部分：

```bash
npm install -g ai-workflow-suite@latest
ai-workflow-suite                # 原地更新
ai-workflow-suite --list         # 哪个工具、哪个版本、装在哪
ai-workflow-suite --uninstall
```

安装器只重写**它自己装过的**目录（每个 skill 里有个 `.ai-workflow-suite` 标记文件）。同名目录若是你自己放的，会跳过并提示，加 `--force` 才覆盖。

**`sync.py` 是另一件事**，别混淆：它同步的是**套件自己**（`ai-workflow` + 所有 `ai-workflow-*` 兄弟目录）到各工具的 skills 根，供你**改动套件源文件**时用，语义是镜像——源里删掉了，目标端也会清理掉。

```bash
python3 <套件根>/ai-workflow-state/tools/sync.py [--dry-run] [--targets <root1>,<root2>,...]
```

退出码 `0` 成功（含"没探测到目标"）/ `1` 错误。纯标准库、三平台通用，会自动排除 `__pycache__` 与 `*.pyc`。

分工记一句话就够：**从 npm 装/升级用 `ai-workflow-suite`；自己改了 skill 源文件要推到多个工具目录用 `sync.py`。** 项目状态文件（`docs/ai-workflow/`）跟这两个都无关，那是你仓库里的业务产物，进 Git。

---

## CLI 参数参考

```
ai-workflow-suite                     自动探测并安装到全部已存在的工具
ai-workflow-suite claude codex omp    只装指定工具
ai-workflow-suite --dir <path>        装进指定 skills 根（跳过探测）
ai-workflow-suite --list              列出内置 skill 与探测到的目标、版本
ai-workflow-suite --uninstall [目标]   删除本工具装过的 skill
```

| 参数 | 说明 |
| --- | --- |
| `--to`, `--target <ids>` | 指定目标，逗号或空格分隔：`claude`、`codex`、`omp`、`agents`、`qoder`、`all` |
| `--dir <path>` | 显式 skills 根，跳过自动探测 |
| `--force` | 覆盖不是本工具装进去的同名目录 |
| `--list` | 显示状态后退出 |
| `--uninstall`, `--remove` | 删除而不是安装 |
| `--help` / `--version` | 帮助 / 版本 |

零依赖，Node 16+。没有配置文件、不需要 token、不会联网。

---

## 常见问题

**装完了看不到 `/ai-workflow`？**
重启 agent 工具让它重新扫描 skills。仍没有就用自然语言点名（"用 ai-workflow-project 走这个项目"）。

**为什么模型不会自己调用这些 skill？**
故意的。每个 SKILL.md 都带 `disable-model-invocation: true`——这套流程必须人来拉，让模型自己判断"这个任务需要走六阶段"正是它最容易判错的地方。

**小任务也要走完整套吗？**
不。短、低风险、一次性的任务直接说清目标动手。只有命中风险信号才升级，而且升级后仍按风险缩放深度。

**Windows 上路径怎么写？**
套件里 `<套件根>` 的解析规则只写在主 skill 的「安装与定位」一节（那是全套件唯一的路径事实源）：macOS/Linux 用 `$HOME/.agents/skills`，Windows PowerShell 用 `$env:USERPROFILE\.agents\skills`，cmd 用 `%USERPROFILE%\.agents\skills`，**不要写 `~`**——PowerShell/cmd 和某些 agent 运行时不展开它。`/` 与 `\` 混用可行，套件脚本内部双向归一。

**已经装了别的工作流框架，会不会打架？**
`tool-selection.md` 就是为这个写的：先按症状挑工具，六套框架各管一块（规范合同 / 行为门禁 / 项目状态 / 长任务分段 / 角色流程 / 多 Agent 编排）。`ai-workflow-*` 与项目状态、长任务分段类的框架职责重叠，**二选一**，别叠着装。落地节奏建议：先补你最常失控的那一站，连续用两周记录返工次数，再决定要不要加。

**需要 Python 吗？**
只有 `ai-workflow-state` 的两个工具需要（`validate_state.py`、`sync.py`），纯标准库。没装 Python 的话安装器会提示你，其余 9 个 skill 照常可用。

---

## 这套东西不管什么

范围说清楚，免得你按错方向期待它：

- 不是 agent 编排框架，不帮你并行跑多个 agent（那是 OMC 那一类的事）；
- 不是代码生成工具，一行实现都不写；
- 不做自动质量门禁流水线，`validate_state.py` 只校验**状态文件的一致性**，不校验代码对错；
- 防伪不是全自动：校验器抬高门槛，真正的防线是 fresh 上下文的独立验证和三轴审计 + Git 历史；
- 一次性脚本、小改动用它是浪费——它自己第一条就写着"流程成本高于任务本身就是最大的浪费"。

---

## English

Six-stage AI development workflow packaged as agent skills for Claude Code, Codex CLI, omp, and any tool that reads a `skills/` directory of `SKILL.md` files.

```bash
npm install -g ai-workflow-suite
ai-workflow-suite                 # auto-detects installed tools and installs the skills
ai-workflow-suite --list          # what is installed, where, which version
ai-workflow-suite --uninstall
```

Then in your agent tool: `/ai-workflow` for one requirement, `/ai-workflow-project` for a long-running project, `/ai-workflow-recover` when a session dies.

The premise: **Agent = Model + Harness.** Deliveries rarely fail because the model was weak — they fail because the requirement was never aligned, the boundary never landed, the task was never split, and a conclusion was never independently verified, all of which the AI happily filled in with a plausible default. "It runs" is not "it is right"; "there are tests" is not "the critical path is covered"; "I'm done" is not "nothing is missing."

The six stages are a risk map, not a pipeline. Every stage puts a Skill (how the agent must act), an Artifact (confirmed facts, written to disk — not left in chat) and a Gate (when work may continue) exactly where control is most likely to be lost.

Non-negotiable, in any mode: product trade-offs, legal/compliance wording, loss-related logic, release & rollout decisions and accepted risk are **never** decided by the agent. They land in `decisions.md` as open items with an owner, and the related task stays `blocked` — the bundled validator enforces this mechanically.

Reviews have to end. A task gets at most three review rounds before it goes back to a human (`reviewRounds` is checked), and every task carries a risk tier — `low` / `medium` / `high` — that sets the minimum number of **human** approvers (1 / 2 / 3); an agent's "looks good" never counts toward that quota. Approvals are pinned to a commit: `approvedAtCommit` followed by new commits touching that task's files invalidates the sign-off, and the validator catches it. All of these fields are optional, so projects created before this release keep passing.

Rollback means flipping a switch, not shipping again. And if a release rolled back or an incident was recorded, the next milestone's tiers step up one level until a human clears it — no expansion of the zero-human-approval path before that fuse is in place.

`sync.py` mirrors the suite itself across tool roots (for when you edit the skills' source); it does not sync project state, which lives in your repo under `docs/ai-workflow/`.

## Source & license

Self-contained and originally authored: the stage rules, the state validator (`validate_state.py`), the sync tool (`sync.py`) and the CLI installer in `bin/` are all developed in this repository. MIT licensed.

Documentation in this README is taken from the skill files themselves: stage rules from `skills/ai-workflow/references/stage-*.md`, lessons from `references/lessons.md`, validator rules from `skills/ai-workflow-state/tools/validate_state.py` and `references/state-schema.md`, sync semantics from `skills/ai-workflow-state/tools/sync.py`. Command lines are copied verbatim from those files' usage text.
