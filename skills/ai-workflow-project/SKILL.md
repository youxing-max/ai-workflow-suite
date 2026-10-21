---
name: ai-workflow-project
description: 大型项目（0→1 / 长期多切片）指挥入口：建立项目状态、路线与切片调度。人工触发 /ai-workflow-project。
disable-model-invocation: true
---

# AI Workflow Project · 大型项目指挥入口

单需求走 `ai-workflow`（地图层）；**跨多里程碑、多切片、多会话、多人接力的项目**走本套件。本 skill 是指挥台：只调度，不亲自写业务代码。

## 何时用

- 0→1 新产品（如一个 App 的核心闭环）；
- 跨多仓库/多团队的长期演进；
- 需要里程碑、Wave 并行、跨会话恢复的项目。

不适用：单个需求、一次性脚本——用 `ai-workflow` 或直接动手。

## 指挥循环

```
init（建状态）→ project.md（目标/非目标/成功指标）→ 切片级 Spec（design）
  → 每条垂直切片循环：plan → execute → verify
  → 里程碑演示 → ship（发布/归档/回流）
  → 会话边界随时 recover / handoff
```

1. **建状态**：无 `docs/ai-workflow/` 时先走 `/ai-workflow-init`。
2. **定项目门**：目标、非目标、成功指标、决策 owner 写入 `project.md`，经用户确认（Project Gate）；确认后 `gateStatus.project=passed`，仍有待确认决策时最高只置 `conditional`。
3. **设计先行**：按主 skill stage-2 把"要什么"落成**切片级 Spec**（存 `docs/ai-workflow/specs/` 或项目既有规范位置，路径记入 roadmap.md），并定测试接缝；第一个里程碑只需切片级 Spec，不做全产品 Spec。
4. **切第一条垂直切片**：走 `/ai-workflow-plan`——只规划到"能端到端演示"为止，不规划整个产品。
5. **逐切片推进**：`/ai-workflow-execute` → `/ai-workflow-verify`；每切片证据落 `evidence/`。
6. **里程碑收口**：`/ai-workflow-ship`；会话中断/换人用 `/ai-workflow-recover`。
7. **每会话首尾**：按 `/ai-workflow-state` 读写状态——状态只认文件，不认聊天记忆。

## 人工保留决策（任何模式不可代拍）

（本节是主 skill「不可豁免」条④的项目级具体化，不是独立清单。）

产品取舍与优先级、法务/合规/隐私口径、资损相关逻辑、发布与灰度决定、风险接受。这些只能写入 `decisions.md` 待确认（owner + 截止时间），未确认前相关任务停在 `blocked` 或 `proposed`——相关任务标注 `requiresDecision: ["D00x"]`，由校验器机器强制这条规则。

**无人值守边界**：headless 只允许推进"已批准切片"内的工作并记录假设；上述保留决策、Release Gate、风险接受**一律停在待确认**，不适用"按推荐假设继续"。

## 各阶段方法论

不重复造轮子：阶段方法、坑点清单以 `ai-workflow/references/stage-*.md` 为单一事实源（本机 `<套件根>/ai-workflow/`），本套件只加项目级扩展（状态、里程碑、Wave、恢复、审计）。

## 项目 Gate（可机器判定）

`python3 <套件根>/ai-workflow-state/tools/validate_state.py <project-root>` 通过，且：Project Gate（目标与 owner 确认）→ Slice Gate（切片可演示 + 依赖边齐全）→ Release Gate（证据 + Blocker=0 + 回滚 + 人工发布确认）。

---

来源：本套件自研，是 ai-workflow 六阶段的项目级扩展（方法论见主 skill「来源」节）。状态目录与 Journal、Wave 与计划工件、三轴审计、对抗审查这些**形态**在开源工作流（Trellis / GSD / BMAD）里各有近亲，本套件按自己的机制重新定义：机器可判定 Gate（`validate_state.py`）、State 轴、验收面规则（verify「观察面对齐」与 plan「acceptance 维度检查」）为本套件自有设计，其中验收面规则来自本套件实测经验（见 lessons #11）。
