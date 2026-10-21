---
name: ai-workflow-review
description: 项目级三轴审计（Standards/Spec/State）：fresh 上下文独立审查项目状态与交付物。人工触发 /ai-workflow-review。
disable-model-invocation: true
---

# AI Workflow Review · 项目级审计

对**项目**（不是单个 diff）做独立健康度审计。审计者必须是 fresh 上下文（subagent 或新会话），不读被审者的推导过程，只读文件与实测。代码级双轴 Review 用 `code-review` skill；本 skill 审的是项目层。

## 三轴

| 轴 | 审什么 | 主要证据 |
|---|---|---|
| Standards | 架构边界、项目规范、安全/隐私实践 | 代码 + ADR + 规范文档 |
| Spec | 需求覆盖：每条 FR/规则可追溯到切片与验收断言；Out of Scope 未被偷做 | project.md + Spec + tasks.json |
| State | 状态可信：文件与实际一致、证据链完整、无伪造迁移、待确认项未过期 | validate_state.py（路径见主 skill「安装与定位」节） + evidence/ + git |

（三轴是本套件的设计：Standards 管代码质量、Spec 管需求覆盖、State 管状态可信度——第三轴针对"多会话长任务"才需要，单独校验。对抗审查的执行方式——fresh 上下文、分诊不判决、误报交人过滤——参考 BMAD 的角色分工。）

## 步骤

1. 跑 `validate_state.py（路径见主 skill「安装与定位」节）`，红项直接进报告；
2. 抽样核对（至少）：每个 `verified` 任务的 evidence 文件真实存在且对应命令可重跑；`decisions.md` 每条已确认决策有 owner 与日期；`risks.md` 未关闭风险有缓解动作；
3. 三轴**分列**报告（不合并、不重排、不互相平均），发现项标 Blocker/Major/Minor + 位置 + 证据；
4. 报告落 `docs/ai-workflow/audits/<日期>-<slug>.md`，Blocker 同步写入 `state.json.blockers`；
5. 修复后**重跑审计**（认证后改动即失效），直到 0 Blocker。

## 纪律

- 审计不改业务代码（发现问题开 fix 任务）；
- 对抗式发现是待分诊清单，不是自动判决——误报由人过滤，过滤记录进报告；
- 里程碑收口与项目完结前各至少一次全量审计（见 `/ai-workflow-ship`）。
