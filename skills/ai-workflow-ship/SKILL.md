---
name: ai-workflow-ship
description: 里程碑发布、归档与经验回流：发布计划/回滚/Handoff/规范记忆与过程记忆。人工触发 /ai-workflow-ship。
disable-model-invocation: true
---

# AI Workflow Ship · 发布、归档与经验回流

发布计划、最小 Handoff、四硬条款（引用不复制/临时目录或仓库约定/建议 skills/脱敏）、经验回流筛选、PRD 两个固定位置——方法论以 `<套件根>/ai-workflow/references/stage-6-ship.md` 为单一事实源。本 skill 管**项目级收口**。

## 发布前置

Release Gate（见 `/ai-workflow-verify`）全绿；`release.md` 含：发布顺序（跨仓库：协议/提供方先行）、每步回滚路径、灰度开关位置、监控点、值班与联络。

## 里程碑收口清单

1. **全量审计**：跑 `/ai-workflow-review`，Blocker 清零，报告落 `audits/`；若审计产生新 Blocker，先把 `gateStatus.release` 回置 `blocked`，清零后重过 Release Gate（避免与"release=passed 且 blockers 非空"的机器检查互斥）；
2. **归档规范记忆**：本里程碑稳定的能力写回项目 Spec/ADR（当前真相），变更过程材料移入 `archive/<日期>-<里程碑>/`（历史）；
3. **写过程记忆**：`sessions/` 收尾条目 + 若有接力则 `handoffs/`；
4. **PRD 两个固定位置**：`roadmap.md` 末尾登记"本里程碑遗留问题"（没做完的显式留档）与"数据复盘"（上线后跟踪什么指标、何时回看）；
5. **经验回流**：只收"会反复影响工程判断"的规则进项目规范/本套件 lessons——临时字段、具体日期、一次性排期不收；回流条目注明来自哪个里程碑；
6. **状态收口**：确认 `gateStatus.release=passed` 后，里程碑与任务置 `shipped`（有 evidence 才许）；收口完成后把 `release` 重置为 `pending`（防下一里程碑沿用 stale passed），session 记收口条目；`state.json` 指向下一里程碑或 `project-complete`。

## 项目完结（最后一个里程碑后）

- 全量 `validate_state.py（路径见主 skill「安装与定位」节）` + `/ai-workflow-review` 终审一次；
- `project.md` 补"实际 vs 成功指标"对照；
- 待确认清单清零或显式移交（写清移交给谁）；
- 向用户交付：状态目录路径、审计报告、遗留问题与复盘计划。

**交付不是代码合并那一刻结束的，是这些尾巴都被书面接住之后才结束的。**（文章第六站原句）
