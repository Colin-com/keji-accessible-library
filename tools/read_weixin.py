#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Hermes state.db 读取「微信通道」收到的最近消息。

用途：CLI 会话不会自动收到微信消息，用这个脚本把网关收下的话捞出来。
只读打开（mode=ro），不会干扰正在运行的网关。

用法：
    python tools/read_weixin.py            # 最近 8 条
    python tools/read_weixin.py 20         # 最近 20 条
    python tools/read_weixin.py 20 --json  # 原始 JSON
"""
import json
import os
import pathlib
import sqlite3
import sys

DB = pathlib.Path(os.environ["LOCALAPPDATA"]) / "hermes" / "state.db"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8
AS_JSON = "--json" in sys.argv


def cols(cur, table):
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})")]


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    sc, mc = cols(cur, "sessions"), cols(cur, "messages")
    plat = "platform" if "platform" in sc else None

    # 只认微信通道那条会话（session_key 含 weixin/wechat）
    rows = [r for r in cur.execute("SELECT * FROM sessions").fetchall()
            if "weixin" in str(r["session_key"]).lower()
            or "wechat" in str(r["session_key"]).lower()]
    print(f"[db] {DB}\n[命中微信会话] {len(rows)} 条")
    if not rows:
        print("state.db 里没有微信通道的会话")
        return
    if AS_JSON and len(rows) >= 1:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return

    for s in rows:
        sid = s["session_id"] if "session_id" in sc else s["id"]
        print(f"=== 会话 {sid} | key={s['session_key'] if 'session_key' in sc else '?'} "
              f"| updated={s['updated_at'] if 'updated_at' in sc else '?'} ===")
        keycol = "session_id" if "session_id" in mc else "session_key" if "session_key" in mc else None
        if keycol is None:
            print("messages 表结构未知：", mc)
            continue
        msgs = cur.execute(
            f"SELECT * FROM messages WHERE {keycol}=? ORDER BY rowid DESC LIMIT ?",
            (sid, LIMIT),
        ).fetchall()
        for m in reversed(msgs):
            role = m["role"] if "role" in mc else "?"
            ts = m["created_at"] if "created_at" in mc else ""
            body = ""
            for cand in ("content", "text", "message", "body"):
                if cand in mc and m[cand]:
                    body = str(m[cand])
                    break
            body = " ".join(body.split())
            print(f"[{ts}] {role}: {body[:400]}")
        print()
    con.close()


if __name__ == "__main__":
    main()
