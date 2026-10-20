#!/usr/bin/env python3
"""validate_state.py — docs/ai-workflow/ 项目状态校验器（机器可判定 Gate）。

用法: python3 validate_state.py <project-root> [--json]
退出码: 0=通过  1=有错误  2=用法错误或状态目录缺失
定位: 防"诚实的错误"，并抬高伪造门槛；防伪的最终防线是 /ai-workflow-review（State 轴）与 Git 历史。
"""
import json
import os
import re
import sys

REQUIRED_FILES = ["project.md", "state.json", "tasks.json", "milestones.json",
                  "decisions.md", "risks.md", "roadmap.md"]
REQUIRED_DIRS = ["evidence", "handoffs", "sessions", "audits"]
STAGES = {"brainstorm", "design", "plan", "execute", "verify", "ship", "project-complete"}
TASK_STATUSES = {"proposed", "pending", "active", "blocked", "ready_for_review",
                 "verified", "shipped", "cancelled", "awaiting_human_evidence"}
MILESTONE_STATUSES = {"planned", "active", "verified", "shipped", "cancelled"}
GATE_STATUSES = {"pending", "conditional", "passed", "blocked"}
GATES = ["project", "slice", "release"]
NEEDS_EVIDENCE = {"verified", "shipped"}
EVIDENCE_DIR = "docs/ai-workflow/evidence/"
# 关联决策未 approved 时，任务只允许停在的状态（主 skill 不可豁免条④的机器化）
DECISION_GATED_STATUSES = {"proposed", "blocked"}


def _depth_exceeded(obj, limit=100):
    """迭代式判断嵌套深度是否超限（避免深对象进入 str()/repr 触发 RecursionError）。"""
    stack = [(obj, 1)]
    while stack:
        o, dep = stack.pop()
        if dep > limit:
            return True
        if isinstance(o, dict):
            stack.extend((v, dep + 1) for v in o.values())
        elif isinstance(o, list):
            stack.extend((v, dep + 1) for v in o)
    return False


def load_json(path, errors):
    """读 JSON：任何异常都转成 error 条目，返回 None；顶层非对象视为损坏。"""
    name = os.path.basename(path)
    try:
        with open(path, encoding="utf-8-sig") as f:  # utf-8-sig：兼容带 BOM 的合法文件（Windows 编辑器产物）
            doc = json.load(f)
    except FileNotFoundError:
        return None  # 缺文件由 REQUIRED_FILES 检查统一报
    except IsADirectoryError:
        errors.append(f"{name}: 是目录而不是 JSON 文件")
        return None
    except UnicodeDecodeError:
        errors.append(f"{name}: 不是合法 UTF-8 文本")
        return None
    except RecursionError:
        errors.append(f"{name}: JSON 嵌套过深（疑似损坏或恶意文件）")
        return None
    except OSError as e:
        errors.append(f"{name}: 读取失败（{e}）")
        return None
    except json.JSONDecodeError as e:
        errors.append(f"{name}: JSON 解析失败（{e}）")
        return None
    if not isinstance(doc, dict):
        errors.append(f"{name}: 顶层必须是对象，实际为 {type(doc).__name__}")
        return None
    if _depth_exceeded(doc):
        errors.append(f"{name}: JSON 嵌套过深（超过 100 层，疑似损坏或恶意文件）")
        return None
    return doc


def read_text(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def _enum(value, allowed, label, errors):
    """枚举字段统一检查（类别守卫）：必须是字符串且在 allowed 内。

    非法时报错并返回 None——调用方用返回值做后续成员判断，unhashable 值不会进入 `in` 运算。
    """
    if not isinstance(value, str):
        errors.append(f"{label}: 必须是字符串，实际为 {type(value).__name__}")
        return None
    if value not in allowed:
        errors.append(f"{label}: 非法值 {value!r}（允许: {sorted(allowed)}）")
        return None
    return value


def parse_decisions(content, errors=None):
    """解析 decisions.md → {决策ID: 状态}。识别 '## D00x' 小节与其后首个 '状态：' 行。

    跳过 fenced 代码块（格式示例不算决策）；重复 ID 报错并以首个为准。
    """
    result, current, in_fence, seen = {}, None, False, set()
    if not content:
        return result
    for line in content.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^##\s+(D\d+)(?![0-9A-Za-z])", line)
        if m:
            did = m.group(1)
            if did in seen:
                if errors is not None:
                    errors.append(f"decisions.md: 决策 ID 重复 {did}（以首个为准，请删除或重编号重复小节）")
                current = None
            else:
                seen.add(did)
                current = did
            continue
        if current:
            m2 = re.match(r"^-\s*状态[：:]\s*([A-Za-z]+)", line.strip())
            if m2:
                result[current] = m2.group(1).lower()
                current = None
    return result


def _strip_fenced(text):
    """剥离 fenced 代码块（``` 围栏），避免块内格式示例误触发文档扫描类检查。

    未闭合的围栏按正文处理（fail-closed）：孤行 ``` 不得隐藏其后的内容。
    """
    out, buf, in_fence = [], [], False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            if in_fence:
                in_fence, buf = False, []  # 围栏正常闭合：块内内容丢弃
            else:
                in_fence = True
            continue
        (buf if in_fence else out).append(line)
    if in_fence:
        out.extend(buf)  # 未闭合：缓冲内容按正文放回
    return "\n".join(out)


def _blocked_list(t):
    """安全取任务的 blockedBy 字符串数组（非法类型返回空表，主流程另行报错）。"""
    bl = t.get("blockedBy")
    return [x for x in bl if isinstance(x, str)] if isinstance(bl, list) else []


def find_cycles(tasks_by_id):
    """迭代式 DFS 查 blockedBy 依赖环（无递归深度问题），返回环路径列表。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in tasks_by_id}
    cycles = []
    for root in tasks_by_id:
        if color[root] != WHITE:
            continue
        color[root] = GRAY
        path = [root]
        stack = [(root, iter(_blocked_list(tasks_by_id[root])))]
        while stack:
            node, it = stack[-1]
            descended = False
            for dep in it:
                if dep not in color:
                    continue  # 悬空引用由主流程单独报
                if color[dep] == GRAY:
                    cycles.append(path[path.index(dep):] + [dep])
                elif color[dep] == WHITE:
                    color[dep] = GRAY
                    path.append(dep)
                    stack.append((dep, iter(_blocked_list(tasks_by_id[dep]))))
                    descended = True
                    break
            if not descended:
                color[node] = BLACK
                path.pop()
                stack.pop()
    return cycles


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    root = args[0]
    d = os.path.join(root, "docs", "ai-workflow")
    errors, warnings = [], []

    if not os.path.isdir(d):
        msg = f"状态目录不存在: {d}（先运行 /ai-workflow-init）"
        print(json.dumps({"ok": False, "errors": [msg]}, ensure_ascii=False) if as_json else f"FAIL {msg}")
        sys.exit(2)  # 未初始化区别于"有错误"（契约见 state-schema.md）

    for f in REQUIRED_FILES:
        if not os.path.isfile(os.path.join(d, f)):
            errors.append(f"缺少必需文件: {f}")
    for sub in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(d, sub)):
            warnings.append(f"缺少目录: {sub}/（进 Git 需 .gitkeep 占位）")

    # ---- state.json ----
    state = load_json(os.path.join(d, "state.json"), errors) or {}
    if state.get("version") != 1:
        warnings.append(f"state.json: version={state.get('version')!r}（约定为 1）")
    proj = state.get("project")
    if not (isinstance(proj, str) and proj.strip()):
        errors.append(f"state.json: project 为空或非字符串（{type(proj).__name__}）")
    stage = _enum(state.get("currentStage"), STAGES, "state.json: currentStage", errors)
    gs = state.get("gateStatus", {})
    if not isinstance(gs, dict):
        errors.append("state.json: gateStatus 必须是对象")
        gs = {}
    for g in GATES:
        if g not in gs:
            errors.append(f"state.json: gateStatus 缺 {g}")
        else:
            _enum(gs[g], GATE_STATUSES, f"state.json: gateStatus.{g}", errors)
    headless = state.get("headless")
    if "headless" in state and not isinstance(headless, bool):
        warnings.append(f"state.json: headless 应为布尔，实际 {headless!r}——按 true（更严格方向）处理")
        headless = True
    if headless is True and gs.get("release") == "passed":
        errors.append("state.json: headless=true 时 release Gate 不得为 passed（发布必须人工确认）")
    cw = state.get("currentWave")
    if cw is not None and (not isinstance(cw, int) or isinstance(cw, bool) or cw < 1):
        errors.append(f"state.json: currentWave 必须是正整数或 null，实际 {cw!r}")
    lu = str(state.get("lastUpdated", ""))
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", lu):
        warnings.append(f"state.json: lastUpdated 缺失或非 ISO 8601（{lu!r}）")

    # ---- tasks.json ----
    tasks_loaded = load_json(os.path.join(d, "tasks.json"), errors)
    tasks_doc = tasks_loaded if tasks_loaded is not None else {}
    if tasks_doc.get("version") != 1:
        warnings.append(f"tasks.json: version={tasks_doc.get('version')!r}（约定为 1）")
    if tasks_loaded is not None and "tasks" not in tasks_doc:
        errors.append("tasks.json: 缺 tasks 字段")
    tasks = tasks_doc.get("tasks", [])
    if not isinstance(tasks, list):
        errors.append("tasks.json: tasks 必须是数组")
        tasks = []
    valid_ids = set()
    for t in tasks:
        if isinstance(t, dict):
            _i = t.get("id")
            if isinstance(_i, str) and _i:
                valid_ids.add(_i)
    tasks_by_id, seen_ids = {}, set()
    for i, t in enumerate(tasks):
        if not isinstance(t, dict):
            errors.append(f"tasks.json: 第 {i} 个任务不是对象（{type(t).__name__}）")
            continue
        tid = t.get("id")
        if not tid or not isinstance(tid, str):
            errors.append(f"tasks.json: 第 {i} 个任务缺合法 id")
            continue
        if tid in seen_ids:
            errors.append(f"tasks.json: 任务 ID 重复 {tid}")
            continue  # 跳过重复条目本身（已报错）；不覆盖首条，避免其依赖边被顶掉导致环漏检
        seen_ids.add(tid)
        tasks_by_id[tid] = t
        st = _enum(t.get("status"), TASK_STATUSES, f"tasks.json[{tid}]: status", errors)
        blocked = t.get("blockedBy")
        blocked = [] if blocked is None else blocked
        if not isinstance(blocked, list):
            errors.append(f"tasks.json[{tid}]: blockedBy 必须是数组，实际为 {type(t.get('blockedBy')).__name__}")
            blocked = []
        for dep in blocked:
            if not isinstance(dep, str) or dep not in valid_ids:
                errors.append(f"tasks.json[{tid}]: blockedBy 引用不存在的任务 {dep!r}")
        if tid in blocked:
            errors.append(f"tasks.json[{tid}]: 不允许自阻塞")
        if st != "cancelled":
            acc = t.get("acceptance")
            if not (isinstance(acc, str) and acc.strip()):
                errors.append(f"tasks.json[{tid}]: acceptance 为空或非字符串（Given/When/Then 断言必填）")
            vf = t.get("verify")
            if not (isinstance(vf, str) and vf.strip()):
                errors.append(f"tasks.json[{tid}]: verify 为空或非字符串（必须是可自动执行的命令）")
        if st in NEEDS_EVIDENCE:
            ev = t.get("evidence")
            evs = ev if isinstance(ev, list) else [ev]
            if not evs:
                errors.append(f"tasks.json[{tid}]: status={st} 但 evidence 为空数组（无证据不得迁移）")
            for e in evs:
                if not isinstance(e, str):
                    errors.append(f"tasks.json[{tid}]: evidence 必须是路径字符串，实际为 {type(e).__name__}")
                    continue
                if not e:
                    errors.append(f"tasks.json[{tid}]: status={st} 但 evidence 为空（无证据不得迁移）")
                    continue
                en = os.path.normpath(e).replace("\\", "/").replace(os.sep, "/")  # 分隔符双向归一：POSIX 上的反斜杠与 Windows 的正斜杠都接受，统一按 / 比较
                bn = os.path.basename(en)
                if not en.startswith(EVIDENCE_DIR) or not (bn == tid or bn.startswith(tid + "-") or bn.startswith(tid + ".")):
                    errors.append(f"tasks.json[{tid}]: evidence 路径 {e!r} 不符合规则（须位于 {EVIDENCE_DIR} 下，文件名等于任务 ID 或以 '{tid}-'/'{tid}.' 开头——防跨任务借证据；不得含路径穿越）")
                    continue
                ep = os.path.join(root, en)
                if not os.path.exists(ep):
                    errors.append(f"tasks.json[{tid}]: evidence 文件不存在 {e!r}")
                elif not os.path.isfile(ep):
                    errors.append(f"tasks.json[{tid}]: evidence {e!r} 不是文件（目录/特殊文件不构成证据）")
                elif os.path.getsize(ep) == 0:
                    errors.append(f"tasks.json[{tid}]: evidence 文件为空 {e!r}（空文件不构成证据）")
    for cyc in find_cycles(tasks_by_id):
        errors.append("tasks.json: blockedBy 存在循环依赖: " + " → ".join(cyc))

    # ---- decisions.md 解析（requiresDecision 与对齐检查共用）----
    dec_path = os.path.join(d, "decisions.md")
    dec_text = read_text(dec_path)
    if os.path.isfile(dec_path) and dec_text is None:
        errors.append("decisions.md 存在但不可读（非 UTF-8 文本或 I/O 错误）")
    decisions = parse_decisions(dec_text, errors)
    for tid, t in tasks_by_id.items():
        req = t.get("requiresDecision")
        if req is None:
            continue
        if not isinstance(req, list) or not all(isinstance(x, str) for x in req):
            errors.append(f"tasks.json[{tid}]: requiresDecision 必须是决策 ID 字符串数组")
            continue
        for did in req:
            if did not in decisions:
                errors.append(f"tasks.json[{tid}]: requiresDecision 引用不存在的决策 {did!r}")
            elif decisions[did] != "approved":
                t_st = t.get("status")
                if not isinstance(t_st, str) or t_st not in DECISION_GATED_STATUSES:
                    errors.append(f"tasks.json[{tid}]: 决策 {did} 状态为 {decisions[did]!r}（非 approved），任务必须停在 {sorted(DECISION_GATED_STATUSES)}，实际为 {t_st!r}（人工保留决策不可代批）")

    # state 与 tasks 交叉
    cs = state.get("currentSlice")
    if cs is not None and (not isinstance(cs, str) or not cs or cs not in tasks_by_id):
        errors.append(f"state.json: currentSlice {cs!r} 非法或在 tasks.json 中不存在")
    actives = [tid for tid, t in tasks_by_id.items() if t.get("status") == "active"]
    if len(actives) > 1 and state.get("currentWave") is None:
        warnings.append(f"state.json: {len(actives)} 个任务同时 active 但未声明 currentWave（并行须同 Wave 且 writeScopes 不相交）")

    # ---- milestones.json ----
    ms_loaded = load_json(os.path.join(d, "milestones.json"), errors)
    ms_doc = ms_loaded if ms_loaded is not None else {}
    if ms_doc.get("version") != 1:
        warnings.append(f"milestones.json: version={ms_doc.get('version')!r}（约定为 1）")
    if ms_loaded is not None and "milestones" not in ms_doc:
        errors.append("milestones.json: 缺 milestones 字段")
    milestones = ms_doc.get("milestones", [])
    if not isinstance(milestones, list):
        errors.append("milestones.json: milestones 必须是数组")
        milestones = []
    ms_ids, wave_task_seen = set(), {}
    for i, m in enumerate(milestones):
        if not isinstance(m, dict):
            errors.append(f"milestones.json: 第 {i} 个里程碑不是对象（{type(m).__name__}）")
            continue
        mid = m.get("id")
        if not mid or not isinstance(mid, str):
            errors.append(f"milestones.json: 第 {i} 个里程碑缺合法 id")
            continue
        if mid in ms_ids:
            errors.append(f"milestones.json: 里程碑 ID 重复 {mid}")
            continue
        ms_ids.add(mid)
        m_st = _enum(m.get("status"), MILESTONE_STATUSES, f"milestones.json[{mid}]: status", errors)
        demo = m.get("demo")
        if not (isinstance(demo, str) and demo.strip()) and m_st != "cancelled":
            errors.append(f"milestones.json[{mid}]: demo 为空或非字符串（里程碑必须能说明演示什么；cancelled 除外）")
        waves = m.get("waves")
        waves = [] if waves is None else waves
        if not isinstance(waves, list):
            errors.append(f"milestones.json[{mid}]: waves 必须是数组")
            waves = []
        for w in waves:
            if not isinstance(w, dict):
                errors.append(f"milestones.json[{mid}]: wave 条目不是对象")
                continue
            wno = w.get("wave")
            if not isinstance(wno, int) or isinstance(wno, bool) or wno < 1:
                errors.append(f"milestones.json[{mid}]: wave 序号必须是正整数，实际 {wno!r}")
            wtasks = w.get("tasks")
            if wtasks is None:
                errors.append(f"milestones.json[{mid}]: wave{wno} 缺 tasks 数组")
                wtasks = []
            if not isinstance(wtasks, list):
                errors.append(f"milestones.json[{mid}]: wave tasks 必须是数组，实际为 {type(w.get('tasks')).__name__}")
                wtasks = []
            for tid in wtasks:
                if not isinstance(tid, str):
                    errors.append(f"milestones.json[{mid}]: wave 任务 ID 必须是字符串，实际为 {type(tid).__name__}")
                    continue
                if tid not in tasks_by_id:
                    errors.append(f"milestones.json[{mid}]: wave 引用不存在的任务 {tid!r}")
                if tid in wave_task_seen:
                    pmid, pwno = wave_task_seen[tid]
                    errors.append(f"milestones.json: 任务 {tid} 同时出现在多个 Wave（{pmid}/wave{pwno} 与 {mid}/wave{wno}）")
                wave_task_seen[tid] = (mid, wno)
    for tid, t in tasks_by_id.items():
        mid = t.get("milestone")
        if mid is not None and (not isinstance(mid, str) or not mid or mid not in ms_ids):
            errors.append(f"tasks.json[{tid}]: milestone {mid!r} 在 milestones.json 中不存在")

    # state 与 milestones 交叉（须在 ms_ids 构建后）
    cm = state.get("currentMilestone")
    if cm is not None and (not isinstance(cm, str) or not cm or cm not in ms_ids):
        errors.append(f"state.json: currentMilestone {cm!r} 非法或在 milestones.json 中不存在")
    shipped = [tid for tid, t in tasks_by_id.items() if t.get("status") == "shipped"]
    if shipped and gs.get("release") != "passed":
        warnings.append(f"tasks.json: {len(shipped)} 个任务已 shipped 但 gateStatus.release={gs.get('release')!r}——若非里程碑收口后的重置，说明 Release Gate 被绕过")
    blockers = state.get("blockers", [])
    if not isinstance(blockers, list):
        errors.append(f"state.json: blockers 必须是数组，实际为 {type(blockers).__name__}")
        blockers = []
    elif not all(isinstance(x, str) for x in blockers):
        errors.append("state.json: blockers 元素必须是字符串")
    if gs.get("release") == "passed" and blockers:
        errors.append(f"state.json: release=passed 但 blockers 非空（{blockers}）——Blocker 未清零不进入发布")
    if gs.get("release") == "passed":
        rel = read_text(os.path.join(d, "release.md"))
        if rel is None:
            errors.append("gateStatus.release=passed 但 release.md 不存在或不可读（发布计划是 Release Gate 的 Artifact）")
        elif not rel.strip():
            errors.append("gateStatus.release=passed 但 release.md 为空文件（空文件不构成发布计划）")
        else:
            body = _strip_fenced(rel)
            if re.search(r"\[\s*\]", body) or re.search(r"［\s*］", body):
                errors.append("gateStatus.release=passed 但 release.md 人工确认清单仍有未勾选框（任何写法：- [ ]、1. [ ]、裸 [ ]、全角［ ］）")
            elif not re.search(r"\[\s*[xX✓✔]\s*\]", body):
                errors.append("gateStatus.release=passed 但 release.md 没有任何已勾选的确认项（空清单不构成人工确认）")

    # decisions.md 与 state 对齐
    proposed = sum(1 for v in decisions.values() if v == "proposed")
    pending = state.get("pendingDecisions", [])
    if not isinstance(pending, list):
        errors.append("state.json: pendingDecisions 必须是数组")
        pending = []
    elif not all(isinstance(x, str) for x in pending):
        errors.append("state.json: pendingDecisions 元素必须是字符串（决策 ID）")
    if proposed != len(pending):
        warnings.append(f"decisions.md 有 {proposed} 条 proposed，state.json.pendingDecisions 有 {len(pending)} 条——请对齐")

    ok = not errors
    if as_json:
        print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings,
                          "counts": {"tasks": len(tasks_by_id), "milestones": len(ms_ids),
                                     "decisions": len(decisions)}},
                         ensure_ascii=False, indent=1))
    else:
        print("PASS 状态校验通过" if ok else "FAIL 状态校验未通过")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  WARN  {w}")
        print(f"  (tasks={len(tasks_by_id)} milestones={len(ms_ids)} decisions={len(decisions)})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
