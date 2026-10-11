# -*- coding: utf-8 -*-
"""
M1-B 剧情数据包校验器（内容方自证）
用法: python validate_case.py
校验项（对应任务 04_story_data.md 自证 1-5，另加结构与排版附加检查）:
  1. 两个 JSON 可解析
  2. 所有 next / fallback_next 指向的节点都存在（无悬空引用）
  3. 从 start 出发穷举所有选择组合，可抵达 >= 2 个不同 ending_id
  4. "被过滤空且无 fallback_next" 的 choice 节点数 = 0（按可达状态枚举）
  5. 所有 unlock 引用的 id 都在 archive_entries.json 里存在
附加: 节点数 18-30 / say 文本 <=2 行且每行 <=28 字 / choice >=2 / 至少 1 处三选一 /
      至少 1 个 require 条件选项 / type 取值合法 / end 节点有 ending_id / 所有节点可达
退出码: 0 通过, 1 失败
"""
import json
import os
import sys

BASE = r"E:\Claw-Data\pixel-sci-game"
CASE_PATH = os.path.join(BASE, "game", "data", "case_library.json")
ARCH_PATH = os.path.join(BASE, "game", "data", "archive_entries.json")

VALID_TYPES = {"say", "choice", "end"}
MAX_LINES = 2
MAX_LINE_CHARS = 28
MIN_NODES, MAX_NODES = 18, 30

fails = []


def ok(msg):
    print("  [PASS] " + msg)


def bad(msg):
    print("  [FAIL] " + msg)
    fails.append(msg)


def main():
    print("=" * 72)
    print("剧情数据包校验  case_library.json + archive_entries.json")
    print("=" * 72)

    # ---------- 1. JSON 可解析 ----------
    print("\n[1] JSON 解析")
    try:
        with open(CASE_PATH, "r", encoding="utf-8") as fp:
            case = json.load(fp)
        ok("case_library.json 解析成功  (%d bytes)" % os.path.getsize(CASE_PATH))
    except Exception as exc:  # noqa: BLE001
        bad("case_library.json 解析失败: %s" % exc)
        return finish()
    try:
        with open(ARCH_PATH, "r", encoding="utf-8") as fp:
            archive = json.load(fp)
        ok("archive_entries.json 解析成功  (%d bytes)" % os.path.getsize(ARCH_PATH))
    except Exception as exc:  # noqa: BLE001
        bad("archive_entries.json 解析失败: %s" % exc)
        return finish()

    nodes = case.get("nodes", {})
    start = case.get("start")
    for key in ("case_id", "title", "major", "start", "nodes"):
        if key not in case:
            bad("case_library.json 缺字段: %s" % key)
    if not isinstance(archive, list):
        bad("archive_entries.json 顶层必须是数组")

    # ---------- 结构合法性 ----------
    print("\n[附加] 结构合法性")
    if start not in nodes:
        bad("start=%r 不在 nodes 里" % start)
        return finish()
    ok("start = %s" % start)
    for nid, node in nodes.items():
        if node.get("type") not in VALID_TYPES:
            bad("节点 %s 的 type=%r 非法" % (nid, node.get("type")))
    for nid, node in nodes.items():
        if node.get("type") == "end" and not node.get("ending_id"):
            bad("end 节点 %s 缺 ending_id" % nid)
    n_say = sum(1 for n in nodes.values() if n.get("type") == "say")
    n_choice = sum(1 for n in nodes.values() if n.get("type") == "choice")
    n_end = sum(1 for n in nodes.values() if n.get("type") == "end")
    ok("节点总数 %d（say %d / choice %d / end %d）" % (len(nodes), n_say, n_choice, n_end))
    if not (MIN_NODES <= len(nodes) <= MAX_NODES):
        bad("节点总数 %d 不在 %d-%d 区间" % (len(nodes), MIN_NODES, MAX_NODES))

    # ---------- 2. 悬空引用 ----------
    print("\n[2] 悬空引用检查（next / fallback_next / option.next）")
    refs = []
    for nid, node in nodes.items():
        if "next" in node:
            refs.append((nid, "next", node["next"]))
        if "fallback_next" in node:
            refs.append((nid, "fallback_next", node["fallback_next"]))
        for i, opt in enumerate(node.get("options", []) or []):
            refs.append((nid, "options[%d].next" % i, opt.get("next")))
    dangling = [(a, b, c) for a, b, c in refs if c not in nodes]
    if dangling:
        for a, b, c in dangling:
            bad("悬空引用: 节点 %s 的 %s -> %r" % (a, b, c))
    else:
        ok("%d 条指向全部命中现有节点（0 悬空）" % len(refs))
    for nid, node in nodes.items():
        if node.get("type") == "say" and "next" not in node:
            ok("say 节点 %s 无 next（视为结束）" % nid)
        if node.get("type") == "choice":
            if not node.get("options"):
                bad("choice 节点 %s 没有 options" % nid)
            if "fallback_next" not in node:
                # 只有当存在选项无条件可见时才算安全，交给第 4 项状态枚举判定
                if not any(not o.get("require") for o in (node.get("options") or [])):
                    bad("choice 节点 %s 所有选项都有 require 且无 fallback_next" % nid)

    # ---------- say 文本排版 ----------
    print("\n[附加] say / end 文本排版（<=2 行，每行 <=28 字）")
    over = []
    for nid, node in sorted(nodes.items()):
        if node.get("type") not in ("say", "end"):
            continue
        text = node.get("text", "")
        lines = text.split("\n")
        if len(lines) > MAX_LINES:
            over.append("%s 有 %d 行" % (nid, len(lines)))
        for ln in lines:
            if len(ln) > MAX_LINE_CHARS:
                over.append("%s 有一行 %d 字: %r" % (nid, len(ln), ln))
    if over:
        for item in over:
            bad("排版超限: " + item)
    else:
        longest = max(
            (len(ln) for n in nodes.values() if n.get("type") in ("say", "end")
             for ln in n.get("text", "").split("\n")),
            default=0,
        )
        ok("全部 %d 个 say/end 文本合规（最长行 %d 字）" % (n_say + n_end, longest))

    # ---------- choice 结构附加 ----------
    print("\n[附加] choice 结构")
    if n_choice < 2:
        bad("choice 节点只有 %d 个（要求 >=2）" % n_choice)
    else:
        ok("共有 %d 处 choice" % n_choice)
    tri = [nid for nid, n in nodes.items() if n.get("type") == "choice" and len(n.get("options", [])) >= 3]
    if tri:
        ok("三选一节点: %s" % ", ".join(sorted(tri)))
    else:
        bad("没有三选一的 choice 节点")
    req_opts = ["%s.options[%d]" % (nid, i)
                for nid, n in nodes.items()
                for i, o in enumerate(n.get("options", []) or []) if o.get("require")]
    if req_opts:
        ok("%d 个受 require 门控的选项: %s" % (len(req_opts), ", ".join(req_opts)))
    else:
        bad("没有任何 require 条件选项")

    # ---------- 3./4. 穷举状态空间 ----------
    print("\n[3][4] 穷举所有选择组合（状态空间搜索）")
    endings = set()
    empty_no_fallback = set()
    visited = set()
    reached_nodes = set()
    stack = [(start, frozenset(), 0, 0)]
    guard = 0
    while stack:
        nid, flags, progress, depth = stack.pop()
        guard += 1
        if guard > 200000:
            bad("状态空间搜索超过 200000 步，疑似死循环")
            break
        key = (nid, flags)
        if key in visited:
            continue
        visited.add(key)
        reached_nodes.add(nid)
        node = nodes.get(nid)
        if node is None:
            continue
        ntype = node.get("type")
        if ntype == "end":
            endings.add(node.get("ending_id"))
            continue
        effects = node.get("set") or {}
        new_flags = set(flags)
        for k, v in effects.items():
            if v:
                new_flags.add(k)
        new_flags = frozenset(new_flags)
        nprog = progress + (node.get("progress") or 0)
        if ntype == "say":
            nxt = node.get("next")
            if nxt:
                stack.append((nxt, new_flags, nprog, depth + 1))
            else:
                bad("say 节点 %s 无 next，路径在此意外终止" % nid)
            continue
        if ntype == "choice":
            visible = []
            for i, opt in enumerate(node.get("options", []) or []):
                req = opt.get("require") or {}
                if all((k in new_flags) == bool(v) for k, v in req.items()):
                    visible.append(opt)
            if not visible:
                fb = node.get("fallback_next")
                if fb:
                    stack.append((fb, new_flags, nprog, depth + 1))
                    continue
                empty_no_fallback.add(nid)
                continue
            for opt in visible:
                oflags = set(new_flags)
                for k, v in (opt.get("set") or {}).items():
                    if v:
                        oflags.add(k)
                stack.append((opt["next"], frozenset(oflags),
                              nprog + (opt.get("progress") or 0), depth + 1))
            continue

    if len(endings) >= 2:
        ok("从 start 可达 %d 个不同 ending_id: %s" % (len(endings), ", ".join(sorted(endings))))
    else:
        bad("从 start 只可达 %d 个 ending_id: %s（要求 >=2）" % (len(endings), sorted(endings)))
    if empty_no_fallback:
        bad("被过滤空且无 fallback_next 的 choice 节点 %d 个: %s"
            % (len(empty_no_fallback), ", ".join(sorted(empty_no_fallback))))
    else:
        ok("被过滤空且无 fallback_next 的 choice 节点数 = 0")
    ok("搜索覆盖 %d 个状态、%d 个节点" % (len(visited), len(reached_nodes)))
    unreachable = sorted(set(nodes) - reached_nodes)
    if unreachable:
        bad("从 start 不可达的节点: %s" % ", ".join(unreachable))
    else:
        ok("所有节点从 start 可达")

    # ---------- 5. unlock 引用 ----------
    print("\n[5] unlock 引用 ↔ archive_entries.json")
    ids = [e.get("id") for e in archive]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        bad("archive 条目 id 重复: %s" % ", ".join(sorted(dup)))
    used = set()
    for nid, node in nodes.items():
        for eid in node.get("unlock", []) or []:
            used.add(eid)
            if eid not in ids:
                bad("节点 %s 的 unlock 引用不存在的条目: %s" % (nid, eid))
    missing = [e for e in ids if e is None]
    if missing:
        bad("有 archive 条目缺 id")
    for e in archive:
        for f in ("id", "title", "one_liner", "why_it_matters", "source_url", "tags"):
            if f not in e or e[f] in ("", None, []):
                bad("条目 %s 缺字段/为空: %s" % (e.get("id"), f))
        if not str(e.get("source_url", "")).startswith("http"):
            bad("条目 %s 的 source_url 不是 URL: %r" % (e.get("id"), e.get("source_url")))
    if not fails:
        ok("archive 条目 %d 条，全部有 id/title/one_liner/why_it_matters/http source_url" % len(archive))
    ok("剧本 unlock 引用 %d 个不同 id，全部存在: %s" % (len(used), ", ".join(sorted(used))))
    unused = sorted(set(ids) - used)
    if unused:
        print("  [note] 未被任何节点解锁的条目: %s" % ", ".join(unused))
    if not (8 <= len(archive) <= 10):
        bad("archive 条目数 %d 不在 8-10 区间" % len(archive))
    else:
        ok("archive 条目数 %d 在 8-10 区间" % len(archive))

    # ---------- 6. 可溯源：source_url 必须能在调研底座里找到 ----------
    print("\n[6] 溯源：source_url 是否出现在调研底座 E:\\Claw-Data\\learn\\accessibility\\")
    learn_dir = r"E:\Claw-Data\learn\accessibility"
    corpus = ""
    if os.path.isdir(learn_dir):
        for fn in sorted(os.listdir(learn_dir)):
            fp = os.path.join(learn_dir, fn)
            if os.path.isfile(fp):
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        corpus += fh.read() + "\n"
                except Exception:  # noqa: BLE001
                    pass
    if not corpus:
        bad("调研底座目录读不到内容: %s" % learn_dir)
    else:
        miss = [e["id"] for e in archive
                if str(e.get("source_url", "")) and str(e["source_url"]) not in corpus]
        if miss:
            for e in archive:
                if str(e.get("source_url", "")) not in corpus:
                    bad("条目 %s 的 source_url 在调研底座里找不到: %s"
                        % (e.get("id"), e.get("source_url")))
        else:
            ok("全部 %d 条 source_url 均能在调研底座中逐字命中（无自造来源）" % len(archive))

    return finish()


def finish():
    print("\n" + "=" * 72)
    if fails:
        print("结果: 失败  %d 项不合规" % len(fails))
        for f in fails:
            print("  - " + f)
        print("=" * 72)
        return 1
    print("结果: 全部通过（契约自证 1-5 + 附加检查）")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
