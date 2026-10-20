---
name: ai-workflow-verify
description: 切片级双轴独立验证与项目 Release Gate：Standards/Spec 分列、证据新鲜、Blocker 清零。人工触发 /ai-workflow-verify。
disable-model-invocation: true
---

# AI Workflow Verify · 独立验证与发布门

双轴审查三设计点（钉死比较点/并行独立上下文/报告不合并不重排）、三份证据可互相矛盾、verification-before-completion——方法论以 `<套件根>/ai-workflow/references/stage-5-verify.md` 为单一事实源。本 skill 管**项目级验证编排**。

## 切片验证（每任务 ready_for_review 后）

1. 验证者与实现者不同上下文（fresh subagent / 另一会话）；两条出路都不可用时，任务停在 `ready_for_review` 并记入 `decisions.md` 待确认，不得自审；
2. 对照物：任务的 `acceptance` 断言 + Spec + 项目规范（Standards 来源）；
3. 重跑任务的 `verify` 命令，输出存 `evidence/`——引用实现者留下的旧输出不算新鲜证据；
4. 结论写回 `tasks.json`：通过 → `verified`；不通过 → `blocked` + 生成 fix 任务（保留失败证据）；
5. 无法自动验证的观察点 → `awaiting_human_evidence`，列出人工验证步骤，不得默认通过；人工验证完成后按 evidence 规则留证（注明验证者与日期）再迁 `verified`——出边见 schema 迁移规则。
6. **观察面对齐**：用户可见行为（UI/交互/视觉）的验收必须在需求对应的观察面上取证——HTTP/API 断言证明不了"能点、能看、像不像"；无浏览器级检查手段时，安排显式人工验收步骤（`awaiting_human_evidence`），"测试全绿"不得替代用户观察面。

## Wave / 里程碑验证

- Wave 收口：全量构建 + 测试 + `validate_state.py（路径见主 skill「安装与定位」节）` 三绿；
- 里程碑演示：按 `milestones.json` 的 `demo` 描述实际跑给用户看；headless 时录制证据并在 `decisions.md` 记待人工复核。演示通过后 `gateStatus.slice` 置 `passed`。不是口头宣布。

## Release Gate（发布前逐项过，缺一不发）

- [ ] 发布范围内任务全部 `verified`，Blocker=0 且有处置记录；
- [ ] `state.json.blockers` 为空、`requiresDecision` 关联决策全部 approved、`release.md` 人工确认清单全部勾选（三者均由校验器强制）；
- [ ] 安全/隐私/迁移/兼容有专项证据（涉及即必须）；
- [ ] 发布顺序、回滚路径、开关位置写入 `release.md`（跨仓库时提供方先行）；
- [ ] 监控与告警点已定义；
- [ ] **人工确认**：风险接受、灰度方案、发布窗口——headless 不可代批，未确认则 Gate 停 `blocked`。

## 项目级审计

整体健康度用 `/ai-workflow-review`（三轴：Standards/Spec/State），审计报告落 `audits/`。
