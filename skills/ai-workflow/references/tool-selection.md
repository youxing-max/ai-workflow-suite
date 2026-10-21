# 工具选择：先诊断，再挑工具

先看失败发生在哪里，再挑工具；别先比较谁强谁弱。比较时只问三件事：**它强化哪些阶段、靠什么机制、团队要长期维护什么**。

## 症状诊断表

| 你常看到的现象 | 先补哪一站 | 可以看什么 |
|---|---|---|
| AI 一上来就写偏 | Brainstorm / Design | 轻量访谈 skill（grilling）；要设计门禁看 Superpowers，要规范审查看 OpenSpec |
| 设计清楚，任务做一半失控 | Plan + 跨会话状态 | 垂直切片 + 验收标准（to-tickets）；长任务看 GSD（Get Shit Done），要项目级任务与 Journal 看 Trellis |
| 写得快，Review 总发现遗漏 | Execute / Verify | 测试接缝、缩短反馈命令、双轴 Review（code-review）；Superpowers 管纪律，OMC（oh-my-claudecode）编排多 Agent 验证 |
| 接手的人总要翻聊天记录 | Ship | 可引用的 Spec、验证结果和 Handoff；长期跨会话维护再上 Trellis 一类项目闭环 |
| 会话崩溃/中断，材料只留在聊天记录 | 按 Artifact 存在性定位（多为 Design/Plan） | 按 SKILL.md"怎么走"规则 1 定位并抢救材料落仓库；再拆工单，随时 Handoff |
| 复杂新产品从零开始 | 全流程 | 本机 `/ai-workflow-project` 套件（持久化状态 + 里程碑 + Wave 调度 + 恢复 + 审计，方法层复用六阶段）；重型角色化流程看 BMAD（BMAD-METHOD），可只借其 PRD + Architecture 两份产物格式 |

## 按任务规模的决策路径

| 任务特征 | 选择 |
|---|---|
| 短、低风险、一次性 | 直接 Vibe Coding |
| 边界明确，需要基本工程纪律 | 组合几个轻量 Stage Skills（本机 Matt Pocock 套件） |
| 复杂变更，需要规范先行 | OpenSpec |
| 需要严格执行和验证 Gate | Superpowers |
| 长期项目，需要任务状态和项目记忆 | Trellis / Get Shit Done |
| 复杂产品，需要完整角色化流程 | BMAD |
| 需要多 Agent 并行和运行时控制 | OMC |

任务越短、风险越低，越适合直接对话；任务越长、影响越大，越需要显式阶段和持久化材料。

## 六套工作流对比

> **证据边界**：机制一栏来自各项目官方仓库与本机已装的 skill 文件；阶段强弱与适用场景是本表为讲解所做的映射，**不是项目官方评级**。采用前仍需核对当前版本文档。

| 工作流 | 定位 | 更突出的阶段 | 控制方式 | 典型规模 | 跨会话 | 人工介入 | 维护成本 | 更适合解决 |
|---|---|---|---|---|---|---|---|---|
| OpenSpec | spec-first | Design / Plan | Proposal、Spec、Design、Tasks 等变更 Artifact | 中大型变更 | 中 | 审查变更合同 | 中 | 需求容易跑偏，需要先审后做 |
| Superpowers | skill-first | Brainstorm / Execute / Verify | 自动触发 Skill、硬 Gate、TDD、分层 Review | 小到中大型 | 中 | 明确批准设计和计划 | 中高 | Agent 执行随意，验证纪律不足 |
| Trellis | structure-first | Plan / Execute / Verify / Ship | .trellis/ 目录：Spec、Task、Workflow State、Journal | 中型到长期项目 | 强 | 维护任务和稳定规范 | 中高 | 多仓、跨工具、跨会话接续困难 |
| Get Shit Done | phase-first | Plan / Execute / Ship | .planning/ Artifact、Phase 状态、专职 Agent | 中大型长任务 | 强 | 在阶段检查点介入 | 中高 | 长任务 Context Rot（长上下文性能退化）和状态丢失 |
| BMAD | agile-first | Brainstorm 到 Ship | 角色、PRD、架构、Story、Sprint、Retro | 大型产品/复杂新项目 | 强 | 多角色、多轮审查 | 高 | 需要完整产品和敏捷协作流程 |
| OMC | orchestration-first | Execute / Verify | 模式、Hooks、状态、循环权限、多 Agent 编排 | 中大型复杂执行 | 强 | 选择主循环并处理例外 | 高 | 并行执行、持久循环、运行时治理 |

一句话分工：**OpenSpec 管规范和变更合同，Superpowers 管 Agent 行为门禁，Trellis 管项目级状态和记忆，GSD 管长任务分段，BMAD 管角色和完整研发流程，OMC 管执行编排与运行时；Matt Pocock Skills 把工程纪律做成小型可组合 Skill。**

"维护成本"指长期保持 Artifact、状态和 Gate 有效所需的投入，与安装步骤多少无关。对单会话小任务，重型状态系统很可能拖慢交付。

各站的代表做法速查：

- **Brainstorm**：OpenSpec /opsx:explore（探索期不建正式变更，"没聊清楚前不动工"）；OMC /deep-interview（苏格拉底式一次一问，说 "make it a plan" 后 handoff 给 /plan）
- **Design**：OpenSpec /opsx:propose（变更档案 + SHALL/MUST + Scenario 硬格式）；BMAD PRD→Architecture（FR 编号 + ARCHITECTURE-SPINE.md + PRD Reviewer Gate）
- **Plan**：GSD /gsd:plan-phase（researcher→planner→checker 对抗审查最多打回三轮，禁隐性砍范围，verify 必须自动化命令，小任务走 /gsd:quick）；Trellis .trellis/tasks/<日期>-<名>/implement.md + 上下文清单 jsonl（"该读什么"变成计划的一部分）
- **Execute**：Superpowers subagent-driven-development（worktree 隔离 + 每任务全新 implementer + 独立 reviewer + 进度账本）；GSD /gsd:execute-phase（orchestrator 不亲自执行，按 wave 并行，同文件强制串行，绿了才进下一 wave）
- **Verify**：BMAD bmad-code-review（Blind Hunter / Edge Case Hunter / Verification Gap / Acceptance Auditor 并行，发现项分诊路由）；OMC team-verify（exec→verify→fix 循环，超 20 文件或架构变更强制安全+代码审查）
- **Ship**：Trellis /trellis:finish-work（有游离未提交改动就拒绝执行；提交→规范写回→归档→Journal 进 Git）；OpenSpec archive（specs/ 永远当前真相，archive 是变更历史）

## 本机已装工具与组合建议

| 已装 | 定位 | 与六阶段的关系 |
|---|---|---|
| Matt Pocock 全套（grilling、to-spec、to-tickets、implement、code-review、handoff、tdd、prototype、retro、triage、wayfinder 等） | 小型可组合 stage skill | 六站各自的最小 Skill；ask-matt 是它的套件路由 |
| OpenSpec 全套（openspec-*） | spec-first 变更合同 | 主要覆盖 Design / Plan / Ship（规范记忆） |
| loopforge | Goal 门驱动 + 职责隔离交付闭环 | 重型全流程：从零要一个"定门→拷问→SRS→设计→Loop→双轮审计"的闭环时直接用它，不必再拼六站 |
| ai-workflow-* 套件（project / init / state / plan / execute / verify / recover / ship / review） | 大型项目指挥层：持久化状态、里程碑与 Wave 调度、跨会话恢复、三轴审计 | 六阶段方法论的项目级扩展，自研；承担 Trellis"项目状态与记忆"+ GSD"长任务分段"各自的职责；状态与 Gate 可机器判定（validate_state.py）；全部人工触发 |
| web-access | 联网操作 | 辅助能力，非阶段工具 |

**组合原则**：组合前先确认**机制没有重复**，否则只会增加维护面——例如（本机判断）loopforge 的双轮审计与 code-review 的双轴 Review 是重叠机制，同一趟任务二选一；ai-workflow-* 套件承担了 Trellis/GSD 的项目状态与长任务分段职责，若将来引入这两者，同样二选一。也可以一个框架都不装，只把经常出问题的阶段写成自己的 Skill 和 Checklist。

本 skill（ai-workflow）在其中的角色是**地图层**：负责"现在该进哪个阶段、该阶段用谁、有哪些坑"，阶段内的具体执行交给上述工具；大型项目的项目层由 ai-workflow-* 套件承担（同一触发原则：全部人工拉起）。它们都由人显式触发（`disable-model-invocation`，不参与模型自动路由）——因为"要不要为这个任务上流程"本身就是需要人承担后果的取舍。

**安装与同步**：本套件以 `<套件根>/ai-workflow*/`（ai-workflow 与 9 个 ai-workflow-* 模块，`<套件根>` 解析见主 skill「安装与定位」节）为规范源。修改规范源后，用跨平台同步工具一次性同步到本机其它 agent：

```bash
python3 <套件根>/ai-workflow-state/tools/sync.py
```

（纯 stdlib，Windows/macOS/Linux 通用；自动探测 ~/.claude/skills、~/.codex/skills、~/.omp/agent/skills，不存在的跳过；镜像语义——源里删除的文件在拷贝端也会被清理；自动排除 __pycache__。旧 rsync/bash 方案已废弃。）

## 落地节奏

先找到最常失控的阶段，补一个合适的 Skill、Artifact 或 Gate，**连续用两周并记录返工和 Review 遗漏**。没有改善，就删掉或调整；有效，再考虑引入更完整的工作流。省掉的提问、拆分和审查从来不会真正消失，只会推迟到更贵的地方出现：PR 评审、线上事故、下一个人的第一周。

## 参考的外部工作流

本套件自研，下列是它做组合映射时参考过的开源工作流与 Skill 仓库（可替换，不构成依赖）：

六套工作流与一组小 Skill 仓库：[mattpocock/skills](https://github.com/mattpocock/skills) · [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) · [obra/superpowers](https://github.com/obra/superpowers) · [mindfold-ai/Trellis](https://github.com/mindfold-ai/Trellis) · [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) · [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) · [Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode)
