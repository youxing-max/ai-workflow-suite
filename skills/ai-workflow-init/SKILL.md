---
name: ai-workflow-init
description: 为项目创建 docs/ai-workflow/ 持久化状态目录（模板见 templates/）。人工触发 /ai-workflow-init。
disable-model-invocation: true
---

# AI Workflow Init · 初始化项目状态

在项目根创建状态目录。**已存在的文件一律不覆盖**，只补缺失项并报告差异。

## 目录结构

```text
docs/ai-workflow/
├── project.md        # 目标、非目标、成功指标、决策 owner
├── state.json        # 机器可读：当前阶段/切片/Wave/Gate/阻塞
├── roadmap.md        # 人读：里程碑与切片地图
├── milestones.json   # 机器可读：里程碑与 Wave
├── tasks.json        # 任务、依赖边、验收断言、证据路径
├── decisions.md      # 决策日志 + 待确认清单（owner/截止）
├── risks.md          # 风险登记：触发器、缓解、owner
├── evidence/         # 命令输出、测试报告、Review 结论
├── handoffs/         # 跨会话交接（引用不复制、脱敏）
├── sessions/         # 会话日志（做了什么/下一步）
├── audits/           # 项目级审计报告
├── review-contracts/ # 模块审查契约（可选，用到再建）
├── regressions/      # 错题本（可选，用到再建）
└── release.md        # 发布计划（顺序/回滚/开关/监控/人工确认）
```

templates/ 中 `handoff.md`、`release.md`、`review-contract.md`、`regression.md` 是**格式模板**：第一份 `handoffs/<时间戳>-<slug>.md` 参照前者，首次发布前复制 `release.md` 填写，`review-contract.md` 与 `regression.md` 在第一次需要审查契约/记录事故时才复制到对应目录——这两个目录用到再建（校验器不强制其存在）。

## 步骤

1. 从本 skill 的 `templates/` 复制 7 个常驻文件（project.md、state.json、tasks.json、milestones.json、decisions.md、risks.md、roadmap.md——逐个检查，已存在则跳过）；创建 `evidence/`、`handoffs/`、`sessions/`、`audits/` 四个子目录并各放一个 `.gitkeep`（进 Git 不丢空目录）。`handoff.md`、`release.md`、`review-contract.md`、`regression.md` 是格式模板，此时不复制（用途见上）。
2. 与用户逐项填 `project.md`：目标、**非目标**（同样重要）、成功指标、每类决策的 owner；填不了的写进 `decisions.md` 待确认，不编造。
3. 把项目名写入 `state.json.project`、`lastUpdated` 填当前 ISO 时间，然后运行校验器确认骨架合法：
   `python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>`
4. 建议将 `docs/ai-workflow/` 纳入版本控制（状态进 Git，换人换会话可恢复）。

## 完成标准

校验器退出码 0；`project.md` 的目标/非目标/owner 三节非空——无人在场或答不了时，节内写"待确认(D00x)"占位视同非空，同时必须在 `decisions.md` 立对应待确认项；向用户报告创建清单与待确认项。**不宣称"项目已准备好开发"**——那只由 Project Gate 判定。
