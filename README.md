# ai-workflow-suite

Six-stage AI development workflow as installable **agent skills**: a map layer (`ai-workflow`) for a single requirement, plus a project command layer (`ai-workflow-*`) for long-running, multi-slice projects.

Works with any tool that reads a `skills/` directory containing `SKILL.md`: **Claude Code**, **Codex CLI**, **omp**, and the universal `~/.agents/skills` root.

> 中文说明见下方 [中文](#中文)。

## Install

One command, no global install, no config files to edit:

```bash
npx ai-workflow-suite
```

It detects which tools you already have (`~/.claude`, `~/.codex`, `~/.omp`, `~/.agents`, `~/.qoder-cn`) and drops the skills into each one's skills directory. Nothing is written for tools you do not have.

Target specific tools only:

```bash
npx ai-workflow-suite claude codex omp
```

Install into an explicit directory (a repo-local `.claude/skills`, for example):

```bash
npx ai-workflow-suite --dir ./skills
```

Restart the tool, then invoke a skill by name — every skill in this suite is **human-triggered**, the model will not route to them on its own.

## Update / uninstall

Re-run the same command to update in place:

```bash
npx ai-workflow-suite            # updates only what changed
npx ai-workflow-suite --list     # what is installed, where, which version
npx ai-workflow-suite --uninstall
```

The CLI only rewrites directories it installed itself (marked by a `.ai-workflow-suite` file inside each skill). If a same-named directory is yours, it is skipped unless you pass `--force`.

## What you get

| Skill | What it does |
| --- | --- |
| `ai-workflow` | Map layer: the six stages, when to enter the flow at all, unattended mode, 11 hard-won lessons |
| `ai-workflow-project` | Command entry for 0→1 / long-running projects: schedules slices, does not write business code itself |
| `ai-workflow-init` | Scaffold the project state directory (`docs/ai-workflow/`) with 9 templates |
| `ai-workflow-state` | State read/write protocol + machine gates: `validate_state.py`, cross-tool `sync.py` |
| `ai-workflow-plan` | Milestone / Wave scheduling |
| `ai-workflow-execute` | Slice execution dispatch |
| `ai-workflow-verify` | Independent verification + Release Gate |
| `ai-workflow-recover` | Cross-session / crash recovery |
| `ai-workflow-ship` | Release, archive, feedback loop |
| `ai-workflow-review` | Three-axis project audit |

## How to use it

- **One requirement** — `/ai-workflow`, or say "use ai-workflow for this requirement: …".
- **A real project** — `/ai-workflow-project` → `plan` → `execute` → `verify` → `ship`; `/ai-workflow-recover` when a session dies.
- **State across agents** — `python3 <install root>/ai-workflow-state/tools/sync.py`.

The small print that actually matters:

- **Skip the flow for short, low-risk, one-off tasks.** Process cost larger than the task is the biggest waste available.
- Risk signals override that: cross-module/cross-repo, more than one session, money/permissions/privacy/migration, a trade-off someone must own, handoffs, the same defect recurring in review.
- Product trade-offs, legal/compliance wording, loss-related logic, release & rollout decisions and accepted risk **are never decided by the agent**. They go into `decisions.md` as open items with an owner, and the related task stays `blocked` — the validator enforces this mechanically, not by good intentions.

## The idea

Agent = Model + Harness. The model supplies intelligence; the tooling, context, permissions and state layer decide whether that intelligence can be used reliably. Deliveries rarely fail because the model was weak — they fail because the requirement was never aligned, the boundary never landed, the task was never split, and a conclusion was never independently verified, all of which the AI happily filled in with a plausible default. "It runs" is not "it is right"; "there are tests" is not "the critical path is covered"; "I'm done" is not "nothing is missing".

The six stages are a **risk map**, not a pipeline: put artifacts and gates where control is most likely to be lost, not spread evenly across the flow.

## 中文

czm《从 AI 写代码到 AI 工作流 · 六阶段》的 skill 套件：主 skill（`ai-workflow`，单需求导航地图）+ 9 个项目模块（`ai-workflow-*`，大型项目指挥层）。全部人工触发，不参与模型自动路由。

```bash
npx ai-workflow-suite              # 自动检测并安装到已存在的工具目录
npx ai-workflow-suite claude codex omp
npx ai-workflow-suite --uninstall
```

安装位置：Claude Code `~/.claude/skills`、Codex `~/.codex/skills`、omp `~/.omp/agent/skills`、通用 `~/.agents/skills`。内部引用按各自目录自定位解析，无需改路径。

- 单需求：说"用 ai-workflow 走这个需求：×××"
- 大项目：`/ai-workflow-project`（入口）→ plan → execute → verify → ship
- 崩溃恢复：`/ai-workflow-recover`
- 多 agent 同步：`python3 <套件根>/ai-workflow-state/tools/sync.py`

## License

MIT
