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
5. **轮次封顶**：同一任务审查满 3 轮仍不通过，不得再开第 4 轮——转 `blocked` 并记入 `decisions.md`，由人重审方案（收敛纪律见 `stage-5-verify.md`；`validate_state.py` 按 `reviewRounds` 强制）；
6. 无法自动验证的观察点 → `awaiting_human_evidence`，列出人工验证步骤，不得默认通过；人工验证完成后按 evidence 规则留证（注明验证者与日期）再迁 `verified`——出边见 schema 迁移规则。
7. **观察面对齐**：用户可见行为（UI/交互/视觉）的验收必须在需求对应的观察面上取证——HTTP/API 断言证明不了"能点、能看、像不像"；无浏览器级检查手段时，安排显式人工验收步骤（`awaiting_human_evidence`），"测试全绿"不得替代用户观察面。界面类改动按此留证：截图与设计稿比对，两者一并进 `evidence/`。

## 风险分档决定要几个人签字

分档只看**改动本身的风险**，不看代码是人写的还是 Agent 写的——AI 产出既不加重也不减轻审批要求。

| 档 | 典型改动 | 机器检查全绿之后还需 |
|---|---|---|
| `low` | 文档、文案、纯内部小工具；改动全程藏在特性开关后面 | 法定审查员 1 人（即下指令的人），不需额外同事 |
| `medium` | 常规产品逻辑；动到缓存、自动更新器这类敏感部位 | 法定审查员 + 1 人 |
| `high` | 计费/隐私/安全等核心高危路径、CI 配置、会被整个代码库抄作业的架构模式 | 法定审查员 + 2 人 |

- **谁负责**：给 Agent 下指令的人就是法定审查员之一，对结果负责；**Agent 的"通过"不占人类审批名额**，也不能替人签字；
- **审批会过期**：签字之后 Agent 又推了新 commit，或有人手动解过合并冲突——前面的审批作废，重跑验证与审批（`approvedAtCommit` 之后不得有触及该任务 `files`/`writeScopes` 的提交，校验器核对）；
- **档位与签字人写进 `tasks.json`**：`riskTier` + `humanApprovers`（人名数组），`validate_state.py` 机器核对人数下限、名单里不得混进 `agent`/`ai`；
- **收紧是单向的**：`release.md` 记了回滚或事故，下一里程碑整体上调一级档位，解除收紧需人工确认并记入 `decisions.md`；这道熔断器没装上之前，不要把更多改动放进零人工通道。

## 人只审机器审不好的事

机器负责读代码，人把力气省下来盯这五件：

1. **该不该做**——跨模块、跨团队递过来的需求，先问一句"我们真有必要做这个吗"；
2. **高危区**——计费、自动更新器、CI 配置这类一出事就是大雷的地方；
3. **会被抄的架构模式**——全库都会照着写的决定，必须由人点头；
4. **合入前核证据**——测试输出、命令返回值、截图。谁说不出自动检查会漏掉什么，他负责的那部分就人工深审；
5. **兜底**——上线后的结果由人负责，不由 Agent 负责。

不要求任何人脑子里装着整个系统的完整心智模型，也没必要装：动手改某模块前，让 Agent 针对那块代码**当天**的现状写一份局部切片说明（explainer），复杂逻辑再配一个可视化构件辅助理解。逐行盯着别人改一行文案、调一个参数的 diff，学不到架构。

## Wave / 里程碑验证

- Wave 收口：全量构建 + 测试 + `validate_state.py（路径见主 skill「安装与定位」节）` 三绿；
- 里程碑演示：按 `milestones.json` 的 `demo` 描述实际跑给用户看；headless 时录制证据并在 `decisions.md` 记待人工复核。演示通过后 `gateStatus.slice` 置 `passed`。不是口头宣布。

## Release Gate（发布前逐项过，缺一不发）

- [ ] 发布范围内任务全部 `verified`，Blocker=0 且有处置记录；
- [ ] `state.json.blockers` 为空、`requiresDecision` 关联决策全部 approved、`release.md` 人工确认清单全部勾选（三者均由校验器强制）；
- [ ] 安全/隐私/迁移/兼容有专项证据（涉及即必须）；
- [ ] 发布顺序、回滚路径、开关位置写入 `release.md`（跨仓库时提供方先行）；
- [ ] 监控与告警点已定义；
- [ ] 每个发布范围内任务的风险档位与签字人已核（`riskTier`/`humanApprovers` 达标，签字后无失效提交）；
- [ ] 回滚不用重新发版：特性开关位置与关闭步骤写清，合并后先给内部吃狗粮再放外部流量；
- [ ] 收紧状态已核对：本周期若发生过回滚/事故，档位是否已整体上调一级；
- [ ] **人工确认**：风险接受、灰度方案、发布窗口——headless 不可代批，未确认则 Gate 停 `blocked`。

## 项目级审计

整体健康度用 `/ai-workflow-review`（三轴：Standards/Spec/State），审计报告落 `audits/`。
