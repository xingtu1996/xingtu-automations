#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xt-scheduler — 行途技术·全局定时任务控制面 (CLI v1)

定位：任何 agent 进入任意 xingtu 仓库都能调用，聚合「全部定时任务来源」，
一眼看全「有哪些任务 / 各自状态 / 产出在哪 / 与平台是否漂移」。

数据来源（聚合）：
  ① registry/AUTOMATIONS.yaml   —— 工具中立的意图快照（SSoT，含 prompt 全文/排期/产出/分类）
  ② ~/.workbuddy/workbuddy.db   —— WorkBuddy automation 运行时真实状态（live/deleted/status）
  ③ 各仓库 .claude/scheduled_tasks.json —— Claude Code 定时任务（T-01/02/03 等）
  ④ */.github/workflows/*.yml   —— GitHub Actions
  ⑤ ~/Library/LaunchAgents/*.plist + crontab -l —— 系统层

v1 范围：list / show / drift（查看 + 漂移纠偏，安全只读）。
        enable/disable/new/run 走文档化流程（见 skills/xt-scheduler/SKILL.md），
        避免脚本越权改平台状态；WB 类操作由 agent 调 automation_update 执行。

用法：
  python3 tools/xt_scheduler.py list [--category 工作|创作|生活|信源] [--platform wb|cc|gh|launchagent|cron]
  python3 tools/xt_scheduler.py show <slug>
  python3 tools/xt_scheduler.py drift
  python3 tools/xt_scheduler.py sources
"""
import argparse, os, sys, yaml, sqlite3

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "registry", "AUTOMATIONS.yaml")
DB = os.path.expanduser("~/.workbuddy/workbuddy.db")
CATS = ["工作", "创作", "生活", "信源"]


def load_registry():
    if not os.path.exists(REGISTRY):
        print(f"[warn] registry 未找到: {REGISTRY}", file=sys.stderr)
        return []
    with open(REGISTRY, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return d.get("automations", []) if isinstance(d, dict) else d


def load_wb_live():
    """返回 {id: {'status','deleted'}} 来自 WorkBuddy DB（仅 live 任务有完整信息）。"""
    out = {}
    if not os.path.exists(DB):
        return out
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        for r in con.execute("SELECT id,status,deleted_at,name FROM automations"):
            out[r["id"]] = {"status": r["status"], "deleted": bool(r["deleted_at"]), "name": r["name"]}
        con.close()
    except Exception as e:
        print(f"[warn] 读 WB DB 失败: {e}", file=sys.stderr)
    return out


def cmd_list(args):
    items = load_registry()
    wb = load_wb_live()
    if args.category:
        items = [i for i in items if i.get("category") == args.category]
    if args.platform:
        items = [i for i in items if (i.get("platform") or "").lower() == args.platform.lower()]
    items.sort(key=lambda i: (i.get("category", ""), i.get("slug", "")))
    print(f"# 定时任务总览（{len(items)} 条）")
    cur = None
    for it in items:
        cat = it.get("category", "未分类")
        if cat != cur:
            cur = cat
            print(f"\n## {cat}")
        slug = it.get("slug", "?")
        st = it.get("status", "?")
        plat = it.get("platform") or "—"
        # 运行时状态 enrichment
        rid = it.get("id")
        live = wb.get(rid) if rid else None
        if live:
            mark = "✅" if not live["deleted"] else "☠️DELETED"
            st = f"{st}(平台:{live['status']}/{mark})"
        sched = (it.get("schedule") or {}).get("human", "?")
        print(f"  - {slug:<32} [{plat:<11}] {st:<22} {sched}")


def cmd_show(args):
    items = load_registry()
    it = next((i for i in items if i.get("slug") == args.slug), None)
    if not it:
        print(f"[err] 未找到 slug: {args.slug}", file=sys.stderr)
        sys.exit(1)
    print(f"# {it.get('name')}  ({it.get('slug')})")
    for k in ("status", "category", "ring", "platform", "id"):
        if it.get(k):
            print(f"  {k}: {it[k]}")
    sc = it.get("schedule") or {}
    if sc:
        print(f"  排期: rrule={sc.get('rrule')} cron={sc.get('cron')} human={sc.get('human')}")
    if it.get("cwd"):
        print(f"  cwd: {it['cwd']}")
    if it.get("artifacts"):
        print(f"  产出:")
        for a in it["artifacts"]:
            print(f"    - {a}")
    if it.get("purpose"):
        print(f"  意图: {it['purpose']}")
    print(f"  prompt(前200字):\n{(it.get('prompt') or '')[:200]}")


def cmd_drift(args):
    items = load_registry()
    wb = load_wb_live()
    print("# 漂移检测：registry 的 id vs WorkBuddy 运行时真实状态")
    problems = 0
    for it in items:
        rid = it.get("id")
        if not rid:
            continue
        if rid.startswith("automation-178") or "T-0" in rid or rid.startswith("cloud:") or rid.startswith("launchagent:") or rid.startswith("workbuddy:"):
            # 这些是非标准 WB-uuid 或外部平台 id，跳过 WB 比对
            continue
        live = wb.get(rid)
        if not live:
            print(f"  [漂移] {it.get('slug')}: registry id={rid} 在 WB DB 中不存在")
            problems += 1
        elif live["deleted"]:
            print(f"  [漂移] {it.get('slug')}: registry 标 {it.get('status')}，但平台已软删(id={rid})")
            problems += 1
        elif live["status"] != it.get("status"):
            print(f"  [漂移] {it.get('slug')}: registry={it.get('status')} 平台={live['status']}")
            problems += 1
    if not problems:
        print("  ✅ 无漂移：所有 registry 标准 WB id 与平台实时状态一致")
    else:
        print(f"\n  共 {problems} 处漂移。修复：改 registry 的 id 为平台当前 live uuid，或回写平台状态到 registry。")


def cmd_sources(args):
    print("# 聚合来源状态")
    print(f"  ① registry : {'OK ' if os.path.exists(REGISTRY) else 'MISSING'} {REGISTRY}")
    print(f"  ② WB DB    : {'OK ' if os.path.exists(DB) else 'MISSING'} {DB}")
    # CC scheduled_tasks
    hits = []
    for root, dirs, files in os.walk(os.path.dirname(REPO)):
        dirs[:] = [d for d in dirs if d in (".claude",) or d not in ("node_modules", ".git")]
        if "scheduled_tasks.json" in files:
            hits.append(os.path.join(root, "scheduled_tasks.json"))
    print(f"  ③ CC scheduled_tasks.json: {len(hits)} 个")
    for h in hits[:10]:
        print(f"      - {h}")


def main():
    ap = argparse.ArgumentParser(description="xt-scheduler 全局定时任务控制面")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("list"); p.add_argument("--category"); p.add_argument("--platform")
    p = sub.add_parser("show"); p.add_argument("slug")
    sub.add_parser("drift")
    sub.add_parser("sources")
    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "show":
        cmd_show(args)
    elif args.cmd == "drift":
        cmd_drift(args)
    elif args.cmd == "sources":
        cmd_sources(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
