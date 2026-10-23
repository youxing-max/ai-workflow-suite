---
name: ai-workflow-plan
description: 项目级规划：里程碑、垂直切片、依赖边与 Wave 并行调度。人工触发 /ai-workflow-plan。
disable-model-invocation: true
---

# AI Workflow Plan · 里程碑与切片调度

切片四规则、blocking edges、Given/When/Then 验收、拆分交人拷问——方法论以 `<套件根>/ai-workflow/references/stage-3-plan.md` 为单一事实源，本 skill 只加**项目级**扩展。

## 项目级扩展

1. **里程碑（milestones.json）**：每个里程碑 = 一个可对外演示的产品能力（如"发布图文→时间线→点赞闭环"），含 `waves` 与 `demo` 验收描述。里程碑按价值排序，第一个必须是最小可演示闭环。
2. **Wave 调度**：同 Wave 内的任务必须 `writeScopes` 互不相交且无依赖边；共享文件、协议/IDL、数据库迁移、发布配置的任务**强制串行**（单独成 Wave 或排前后）。跨仓库契约变更：提供方任务在前，消费方在后。
3. **容量与预重构**：规则见 stage-3 规则 3/4（单一事实源，不在此复述）；项目层只加一个动作——排 Wave 前按"一个全新会话能稳定做完"核对任务大小，写不出端到端行为的任务当场重切。

## 产物

- `roadmap.md`：里程碑 → 切片 → 任务的人读地图（含明确 Out of Scope）；
- `milestones.json` / `tasks.json`：机器可读，字段见 ai-workflow-state 的 schema；
- 每任务必填：`acceptance`（Given/When/Then）、`verify`（可自动执行的命令）、`files`/`writeScopes`、`blockedBy`。
- **风险分档 `riskTier`**：拆任务时按改动本身的风险标 `low`/`medium`/`high`（档位判据见 verify「风险分档决定要几个人签字」），决定该任务需要几名人类签字；判不准就高不就低。
- **契约测试随范围**：任务改变既有响应/接口契约时，锁定该契约的既有测试文件必须一并列入该任务 `writeScopes`——否则实现者被迫在"越界改测试"与"违反新契约"之间二选一（来源：blog-system M1.5 T007 实测）。
- **acceptance 覆盖维度检查**：对照原始需求逐个形容词/维度过一遍——视觉、交互、性能等要求要么拆进 acceptance 断言，要么显式写入 Out of Scope 请用户确认；用户可见行为的验收断言必须落在需求观察面（见 verify 模块"观察面对齐"），不得全部下沉到 HTTP/API 层。

## Gate

拆分清单（里程碑/Wave/任务三层）展示给用户拷问：粒度、依赖边真实性、Wave 冲突、Out of Scope——**批准前所有任务停在 `proposed`**。批准后写入 `decisions.md`（谁批准的、何时），同时置 `gateStatus.slice=conditional`、任务迁 `pending`；slice Gate 由 verify 的里程碑演示通过后置 `passed`。计划改动同样过这道门。
