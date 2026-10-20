---
name: ai-workflow-state
description: 项目状态读写协议：会话首尾如何读/写 docs/ai-workflow/，状态枚举与防伪规则。人工触发 /ai-workflow-state。
disable-model-invocation: true
---

# AI Workflow State · 状态读写协议

状态是唯一事实源：**文件里的才算数，聊天记录里的不算**。协议详细字段见 [references/state-schema.md](references/state-schema.md)。

## 会话开始（读）

1. `python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>`——失败先修状态再干活。
2. 读 `state.json` → `tasks.json`（活动切片与 blockedBy）→ `decisions.md` 待确认项 → `risks.md` 未关闭风险 → 最近一份 `handoffs/`。
3. 向用户报告五件事：当前阶段与 Gate、活动切片、阻塞与待确认、最新证据位置、建议的下一动作。

## 会话结束（写）

只写**真实发生过**的变更：

- `state.json`：`currentStage` / `currentSlice` / `currentWave` / `gateStatus` / `blockers` / `pendingDecisions` / `headless` / `lastUpdated`；
- `tasks.json`：状态迁移 + `evidence` 路径（有输出文件才许迁移到 verified）；
- `decisions.md`：新决策（已确认）或新待确认项（owner + 推荐 + 截止）；
- `sessions/<日期>-<slug>.md`：本次做了什么、证据在哪、下一步；
- 跨会话/换人时另写 `handoffs/`（引用不复制、脱敏、带建议 skills、按用途裁剪；项目级 handoff 存仓库而非临时目录——与 stage-6"存系统临时目录"条款的差异理由见 [references/state-schema.md](references/state-schema.md)）。

## 状态枚举（tasks.json）

`proposed`（待人批准）→ `pending` → `active` → `ready_for_review` → `verified` → `shipped`；旁路：`blocked`（缺依赖/缺决策/缺证据）、`awaiting_human_evidence`（验证无法自动化）、`cancelled`。

## 防伪规则（主 skill 不可豁免条①的项目级延伸）

- 没有对应 `evidence/` 文件，不得写 `verified` / `shipped`；
- 没有 `decisions.md` 里 owner 的确认记录，不得写 `approved`；
- 校验器红着不得开始新任务；
- headless 会话**开始时**立即把 `state.json.headless` 置 `true`——这是发布门禁的武装开关，漏置等于让不可豁免条④失效；恢复交互会话时置回 `false`；
- 状态与实际不符时，以实际为准修状态，并在 session 日志记一笔差异原因（例：`verified` 任务的 evidence 文件丢失 → 降回 `ready_for_review` 重新验证）。
