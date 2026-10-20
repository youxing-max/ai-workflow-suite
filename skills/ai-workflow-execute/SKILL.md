---
name: ai-workflow-execute
description: 按已批准的任务/Wave 执行实现，短反馈循环 + 证据落盘 + 并行安全。人工触发 /ai-workflow-execute。
disable-model-invocation: true
---

# AI Workflow Execute · 切片执行

短反馈循环、TDD 防自证、RED→CHANGE→GREEN、regularly/once 验证节奏——方法论以 `<套件根>/ai-workflow/references/stage-4-execute.md` 为单一事实源。本 skill 管**项目级执行调度**。

## 开工前置检查（任一不满足就停）

1. 任务状态是 `pending` 且全部 `blockedBy` 已 `verified`/`shipped`；
2. 计划已被用户批准（`decisions.md` 有记录，任务不是 `proposed`）；
3. `validate_state.py（路径见主 skill「安装与定位」节）` 通过；
4. Wave 内并行任务的 `writeScopes` 实测不相交（`git status` / 文件清单核对）。

## 每任务循环

1. 只读任务声明的 `files` 上下文（Trellis 式按需注入，防 Context Rot）；
2. 跑基线测试确认可运行起点；
3. 按任务的 `verify` 命令先建 RED，再最小修改到 GREEN；
4. 命令与输出存入 `docs/ai-workflow/evidence/<task-id>-<日期>.log`；
5. 完成 → 任务置 `ready_for_review`（**不是 verified**——验证归 ai-workflow-verify，作者不审自己）；
6. 更新 `state.json` 与 session 日志。

## 并行纪律（多 agent / 多 worktree）

- 编排者协调、不亲自写码；每任务一个干净上下文（subagent 或 worktree）；
- **状态文件集中管理**：tasks.json / state.json 只由编排者回写，实现与验证子代理只产出代码、测试和 evidence——避免多代理并发写冲突；
- **证据日志只追加**：发现注解错误用追加更正记录，不原地修改本体（原地改动会被独立验证按证据篡改复核）；
- 同 Wave 任务互不读写对方 `writeScopes`；违反即停整个 Wave 排查；
- Wave 收口：全部任务 `ready_for_review` + 全量构建/测试绿 → 才开下一 Wave；跨 Wave 有依赖边时，下一 Wave 任务开工还需上游已 `verified`（见前置检查 1）——收口不等于跳过验证。

## 失败回退

同一切片连续失败且指向方案 → 回 Design（任务置 `blocked`，在 `decisions.md` 记录回退原因）；发现需求遗漏 → 回 `/ai-workflow-plan` 补切片；`blockedBy` 含 `cancelled` 任务 → 回 `/ai-workflow-plan` 重排依赖边（删除该边或更换上游），不得原地死等；上下文将满 → 先写 handoff 再停。
