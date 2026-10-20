#!/usr/bin/env python3
"""sync.py — ai-workflow 套件跨平台同步器（纯 stdlib，Windows/macOS/Linux 通用）。

用法: python3 <套件根>/ai-workflow-state/tools/sync.py [--dry-run] [--targets <root1>,<root2>,...]
默认: 以本文件所在位置按自身定位规则推断套件根（兄弟目录 ai-workflow* 为规范源），
      同步到自动探测的各 agent skills 目录（~/.claude/skills、~/.codex/skills、~/.omp/agent/skills），
      不存在的跳过。镜像语义：源里删除的文件在拷贝端也清理；排除 __pycache__ 与 *.pyc。
退出码: 0=成功（含无可同步目标）  1=错误
"""
import argparse
import os
import shutil
import sys

EXCLUDES = {"__pycache__"}
EXCLUDE_SUFFIXES = (".pyc",)
# 自动探测的 agent skills 根（相对于用户主目录）；--targets 可覆盖
DEFAULT_TARGET_SUBDIRS = [
    os.path.join(".claude", "skills"),
    os.path.join(".codex", "skills"),
    os.path.join(".omp", "agent", "skills"),
]


def suite_root():
    """按自身定位规则推断套件根：本文件位于 <根>/ai-workflow-state/tools/sync.py。"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def suite_members(root):
    """规范源成员：ai-workflow 主 skill + 全部 ai-workflow-* 兄弟模块（按存在性收集，不猜未来名）。"""
    members = []
    for name in sorted(os.listdir(root)):
        if name == "ai-workflow" or name.startswith("ai-workflow-"):
            p = os.path.join(root, name)
            if os.path.isdir(p):
                members.append(p)
    return members


def sync_tree(src, dst, dry=False):
    """把 src 目录镜像到 dst：复制新增/变更、删除源里已消失的文件；返回 (copied, removed)。"""
    copied = removed = 0
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        rel = os.path.relpath(base, src)
        target_dir = os.path.join(dst, rel) if rel != "." else dst
        src_files = {f for f in files if not f.endswith(EXCLUDE_SUFFIXES)}
        if not dry:
            os.makedirs(target_dir, exist_ok=True)
        # 删除源里已消失的文件（含模块根的顶层文件）
        for f in os.listdir(target_dir) if os.path.isdir(target_dir) else []:
            if f not in src_files and f not in EXCLUDES and not f.endswith(EXCLUDE_SUFFIXES):
                p = os.path.join(target_dir, f)
                if os.path.isfile(p):
                    if not dry:
                        os.remove(p)
                    removed += 1
        for f in src_files:
            s_p, d_p = os.path.join(base, f), os.path.join(target_dir, f)
            if not os.path.isfile(d_p) or os.path.getmtime(s_p) > os.path.getmtime(d_p):
                if not dry:
                    shutil.copy2(s_p, d_p)
                copied += 1
    # 删除源里已消失的目录（自底向上）
    src_dirs = set()
    for base, dirs, _ in os.walk(src):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        rel = os.path.relpath(base, src)
        if rel != ".":
            src_dirs.add(rel)
    for base, dirs, _ in os.walk(dst, topdown=False):
        rel = os.path.relpath(base, dst)
        if rel != "." and rel not in src_dirs and base != dst:
            if not dry:
                shutil.rmtree(base, ignore_errors=True)
            removed += 1
    return copied, removed


def main():
    ap = argparse.ArgumentParser(description="ai-workflow 套件跨平台同步器")
    ap.add_argument("--dry-run", action="store_true", help="只报告将要发生的复制/删除，不落盘")
    ap.add_argument("--targets", default="", help="逗号分隔的目标 skills 根目录列表（覆盖自动探测）")
    args = ap.parse_args()

    root = suite_root()
    members = suite_members(root)
    if not members:
        print(f"FAIL 未在 {root} 发现任何 ai-workflow* 目录（套件根推断失败？）")
        sys.exit(1)

    if args.targets:
        targets = [os.path.expanduser(t.strip()) for t in args.targets.split(",") if t.strip()]
    else:
        home = os.path.expanduser("~")
        targets = [os.path.join(home, sub) for sub in DEFAULT_TARGET_SUBDIRS]

    print(f"套件根: {root}")
    print(f"规范源成员: {', '.join(os.path.basename(m) for m in members)}")
    total_c = total_r = 0
    synced = 0
    for t in targets:
        if not os.path.isdir(t):
            print(f"-- 跳过（不存在）: {t}")
            continue
        c = r = 0
        for m in members:
            mc, mr = sync_tree(m, os.path.join(t, os.path.basename(m)), dry=args.dry_run)
            c += mc
            r += mr
        total_c += c
        total_r += r
        synced += 1
        print(f"-- 同步到 {t}: 复制 {c} / 删除 {r}" + ("（dry-run）" if args.dry_run else ""))
    print(f"完成: {synced} 个目标，共复制 {total_c} / 删除 {total_r}" + ("（dry-run 未落盘）" if args.dry_run else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
