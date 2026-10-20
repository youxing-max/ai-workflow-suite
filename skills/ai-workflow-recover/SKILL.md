---
name: ai-workflow-recover
description: 会话崩溃/换人/换工具后的项目恢复：从状态文件重建上下文，不考古聊天记录。人工触发 /ai-workflow-recover。
disable-model-invocation: true
---

# AI Workflow Recover · 跨会话恢复

对应文章症状"接手的人总要翻聊天记录"；"会话崩溃、材料只留在聊天记录"为主 skill 补充的诊断行（非文章原文）。恢复的目标：**新 Agent 不读旧聊天，也能接着干**。

## 恢复步骤

1. `python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>`——红了先修（状态坏了比没有更危险）。
2. 读恢复包（按序）：`state.json` → 最近 `handoffs/`（没有就读最近 `sessions/`）→ 活动任务的 `acceptance`/`verify`/`evidence` → `decisions.md` 待确认项 → `risks.md` 未关闭项。
3. 核对现场与状态是否一致：`git status`/`git log` 对照 `tasks.json`（非 git 项目：以文件清单与 lastUpdated/evidence 时间线对照，并在恢复报告中注明核验受限）——**工作区有游离改动而状态没记录，视为状态过期**，先把改动归属到任务或记入 session 日志。
4. 聊天里说过但文件里没有的一切（决策、结论、承诺）＝未发生：要么补录进对应文件（标注"补录+来源"），要么进 `decisions.md` 待确认。
5. 产出恢复报告：当前位置、已完成且有证据的、状态与现场的差异、待人工确认项、建议的下一动作——**经用户确认后**才继续执行。

## 预防（比恢复更重要）

- 每会话结束按 `/ai-workflow-state` 写状态，不等"做完再说"；
- 上下文用到约七成即写 handoff（本套件经验阈值；文章原则是"跨会话随时 Handoff，不必等到 Ship"）；
- `docs/ai-workflow/` 进 Git——恢复包本身就是提交历史的一部分。

## 完成标准

恢复报告发出且用户确认下一动作；`state.json.lastUpdated` 刷新；发现的状态缺口全部补录或显式列为待确认。
