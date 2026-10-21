---
name: ai-workflow
description: AI 开发工作流的六阶段导航与避坑知识库（Brainstorm→Design→Plan→Execute→Verify→Ship）。人工触发：由人输入 /ai-workflow 拉起，不参与模型自动路由。
disable-model-invocation: true
---

# AI 工作流 · 六阶段导航

Agent = Model + Harness：模型提供智能，工具/上下文/权限/状态/执行约束这层工程环境决定智能能否被可靠使用。交付失败的根源通常不是模型，而是需求没对齐、边界没落位、任务没拆分、结论没独立验证——全被 AI 顺手补成了默认答案。能运行不代表对，有测试不代表测到关键路径，自称完成不代表没留隐患。

六阶段是一张**风险地图**，不是流水线：每个阶段管一类失控方式，任务在哪个检查点容易失控，就先补哪一段。

> **触发方式**：本 skill 由人显式拉起（`disable-model-invocation`），模型不会也不应自行调起。适合人工拉起的场合：启动非平凡开发需求（跨模块/跨仓库、一个会话难以稳定做完、涉及权限/资金/隐私/迁移兼容、需多人接力或长期维护）、任务中途失控需要诊断补哪一段、挑选或组合工作流工具、做需求复盘与经验沉淀。小任务不必拉起本 skill——直接说清目标动手更快。无人值守模式**只由调用方在提示词中显式声明**进入（见下文「无人值守模式」），交互会话不得自行判定无人而跳过提问。

## 每阶段的三件约束

- **Skill** 规定 Agent 怎样行动（如一次只问一个决策）；
- **Artifact** 保存已确认的事实（如需求边界、决策记录）——写进仓库或文档，不留聊天记录；
- **Gate** 决定什么时候可以继续（如关键取舍未确认就不写实现）。

Artifact 和 Gate 放在不确定性可能失控的位置，而非平均铺满整条流程。

## 第一步：判边界

任务短、低风险、一次性（一次性脚本、临时数据转换、低风险页面调整）→ 直接说清目标动手，跳过本流程；流程成本高过任务本身就是最大的浪费。

命中任一信号 → 按阶段走（同时命中"短、低风险、一次性"也不豁免——风险信号优先，一票升级）：

1. 改动跨多个模块或仓库；
2. 一个会话很难稳定做完；
3. 涉及权限、资金、隐私、迁移或兼容；
4. 需求里有需要人承担后果的取舍；
5. 要多人接力或长期维护；
6. 同类问题在 Review 里反复出现；
7. 代码能跑，却很难判断需求是否做完整。

升级后仍按风险缩放深度：不机械走满六段，Artifact 可以合并成一页，只走会失控的 Gate。

出现**项目级信号**——0→1 新产品、多里程碑、长期多切片推进、多人/多工具接力——指挥层升级为 `/ai-workflow-project` 套件（持久化状态、里程碑与 Wave 调度、跨会话恢复、三轴审计，全部人工触发）；本 skill 继续作为阶段方法论的地图层被套件引用。

## 六阶段地图

| 阶段 | 那一个问题 | 主要 Artifact | 通过 Gate | 详解 |
|---|---|---|---|---|
| 1 Brainstorm 需求澄清 | 我们理解的是同一个问题吗？ | 目标、范围、决策记录 | 关键取舍已确认 | [stage-1](references/stage-1-brainstorm.md) |
| 2 Design 方案设计 | 需求怎样进入现有系统？ | Spec、设计、必要 ADR | 边界和测试入口已确认 | [stage-2](references/stage-2-design.md) |
| 3 Plan 任务规划 | 怎样拆成可独立验证的工作？ | 工单、依赖边、验收标准 | 每项任务能说明完成条件 | [stage-3](references/stage-3-plan.md) |
| 4 Execute 实现执行 | 当前修改有没有短反馈？ | 小步 Diff、测试与运行记录 | 当前切片有新鲜证据 | [stage-4](references/stage-4-execute.md) |
| 5 Verify 验证审查 | 有什么证据证明做对了？ | 测试输出、双轴 Review 报告 | Blocker 已处理 | [stage-5](references/stage-5-verify.md) |
| 6 Ship 交付沉淀 | 系统和下一位接手者准备好了吗？ | PR、发布计划、Handoff、经验回流 | 发布和接续路径闭环 | [stage-6](references/stage-6-ship.md) |

六阶段各掐住一类不确定性：Brainstorm 管目标，Design 管系统边界，Plan 管任务规模与依赖，Execute 管实现过程，Verify 管正确性，Ship 管交付与接续。任何一环松动，问题都会顺链下传，在更贵的地方爆掉。

## 怎么走

1. **定位**：新需求 → 从 Stage 1 进入；中途失控的任务 → 对照上表找到最早一个 Gate 没通过的阶段，从那里补。Gate 是否通过以 Artifact 存在为准：Artifact 丢了（如设计只留在聊天记录里），视同未通过。
2. **进入阶段先读对应详解文件**，按其方法执行、过其坑点清单，调用其指明的本地 skill。本地 skill 统一位于 `<套件根>/<name>/SKILL.md`（`<套件根>` 解析见「安装与定位」节），用户触发 skill 的命令名与其 name 一致（如 `/to-spec`、`/handoff`）。标注"用户触发"的 skill 无法被模型自动拉起：提示用户输入对应命令，或征得同意后读取其 SKILL.md 按流程执行。无人值守/非交互会话（headless，无人在场可确认）按下文「无人值守模式」处理。
3. **阶段收尾核对 Gate**：Artifact 已产出、通过条件已满足，才进入下一阶段。**没有新鲜、可重复的验证证据，不声称完成**——"应该能过""代码已改完""我已经验证过了"都不算证据。
4. **回退是正常动作**，发现证据与原假设冲突仍然向前，才会把小问题拖成大返工：

| 信号 | 回到 |
|---|---|
| 技术假设无法确认 | 先 prototype，再回需求讨论 |
| 设计中发现需求矛盾 | Brainstorm |
| 执行中架构撑不住方案 | Design |
| 审查发现需求遗漏 | Plan |
| 上下文即将跨会话 | 随时 [Handoff](references/stage-6-ship.md)，不必等到 Ship |

### 无人值守模式（headless）

非交互会话里没人回答问题、也没人拍板。此时规则替换如下：

- **决策不再是阻塞点，而是交付物**：需要人拍板的取舍一律写进**待确认清单**（推荐假设 + 理由 + 调整路径），并按推荐假设继续实现；
- **Gate 记"条件通过·待人工拍板"**：Artifact 产出即可进入下一阶段，但必须把待确认项显式列出，供人一次性复核；
- **人工批准环节**（如拆分的拷问）只跳过等待，不跳过记录。**用户触发 skill 的"征得同意后执行"在此同样替换**：直接读取其 SKILL.md 按流程执行，把该决定记入待确认清单（待追认）；被调用的本地 skill 自身写死的"等待用户/确认后才行动"条款，同样以本节替换为准。

本文件与 `references/` 中所有**以人（用户/负责人）为进入下一步前提**的表述——等待回答、批准、拍板、判断、过滤、确认，含"批准……前禁止……"这类硬门禁，含本 skill 指明的本地 skill 流程中的人工环节（等待、判断、过滤、确认）——在无人值守下一律按上面三条替换：记入待确认清单并继续；仅下文"不可豁免"清单不受替换影响。

四条**不可豁免**：没有新鲜、可重复的验证证据不声称完成；Blocker 未清零不进入发布；接口响应即契约（范围外数据不得进入响应）；**发布、灰度、风险接受及项目级人工保留决策**（产品取舍/法务合规/资损逻辑，清单见 ai-workflow-project）必须人工确认——无人值守会话在此停在 blocked，不得代批。这四条与有没有人在现场无关。这是**封闭清单**——今后新增不可豁免规则时，必须并入此列表，不得散落他处；ai-workflow-* 项目模块只允许对条④做项目级具体化并标注出处。

## 安装与定位（跨主机，本套件唯一路径事实源）

本套件 = 主 skill（ai-workflow/）+ 9 个项目模块（ai-workflow-*/），**彼此是兄弟目录**，合称一个"套件包"。套件内所有文档用 `<套件根>` 指代安装位置，其解析规则只在本节定义：

| 主机/环境 | `<套件根>` 的写法 |
|---|---|
| macOS / Linux（任何 shell） | `$HOME/.agents/skills` |
| Windows PowerShell | `$env:USERPROFILE\.agents\skills` |
| Windows cmd | `%USERPROFILE%\.agents\skills` |

规则：
1. **不要用 `~`**——部分调用方（PowerShell/cmd、某些 agent 运行时）不展开它；路径分隔符 `/` 与 `\` 混用可行（Win32 API 与 Python 均接受），套件脚本内部已双向归一；
2. **按自身定位兜底**：套件内引用兄弟模块时，以本文件实际所在目录的父目录为套件根（本文件在 `<任意 skills 根>/ai-workflow/SKILL.md`，则校验器在 `<同一根>/ai-workflow-state/tools/validate_state.py`）——整套件拷到任何 agent 的任何 skills 目录，内部引用自动成立；
3. **Python 命令**统一写 `python3`；Windows 下不可用时用 `python` 或 `py -3`——此回退适用于校验器与 sync.py 的一切调用处；
4. **同步工具**：`python3 <套件根>/ai-workflow-state/tools/sync.py`——跨平台（纯 stdlib），把规范源同步到本机其它 agent 的 skills 目录（自动探测 Claude Code / Codex / omp，目录不存在则跳过）；校验器命令：`python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>`。旧的 rsync/bash 方案废弃。

各 agent 的 skills 根（sync.py 探测目标）：Claude Code `~/.claude/skills`、Codex `~/.codex/skills`、omp `~/.omp/agent/skills`（均按自身定位规则等效）。
**无 skill 系统的 agent**：把整套件放进仓库（如 `vendor/ai-workflow/`），在仓库根 `AGENTS.md` 加一段：`工作流规范见 vendor/ai-workflow/SKILL.md 及其兄弟模块；用户提到"六阶段/ai-workflow/<模块名>"时先读对应 SKILL.md 并遵循`——任何读 AGENTS.md 的 agent 即接入。

## 工具选择与落地

症状诊断（先补哪一站）、按任务规模的决策路径、六套开源工作流对比、与本机已装 skill（Matt Pocock 套件 / OpenSpec / loopforge）的组合建议、落地节奏（先补一个阶段、两周试行与观察指标）：见 [tool-selection.md](references/tool-selection.md)。

## 修订本套件时

规则按类别还是按枚举写、校验脚本如何自证、独立复核如何避免自评、认证后改动即失效——构建本套件时踩过的坑与对策见 [lessons.md](references/lessons.md)。

## 来源

自研。六阶段规则、状态校验器（`validate_state.py`）、同步工具（`sync.py`）与 CLI 安装器都在本仓库内独立编写维护，不依附任何外部课程、专栏或第三方 skill 包。规则来自真实多仓库交付场景（跨仓库、多终端、隐私规则、分批发布）里反复出现的失控方式，浓缩成 skill 后又经三轮独立审计收紧；取舍与反例记录在 [lessons.md](references/lessons.md)。

与本机已装的其他 skill 套件（Matt Pocock 套件 / OpenSpec / Superpowers / Trellis / GSD / BMAD）只做**组合映射**——它们是可选的外部工具，本套件的规定不依赖其存在；哪些阶段可以换用它们、机制重复时怎么取舍，见 [tool-selection.md](references/tool-selection.md)。
