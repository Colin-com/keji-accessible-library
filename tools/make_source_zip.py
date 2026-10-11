#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打一个干净的源码压缩包（比赛材料①：源码链接）。

包含：web/ game/ docs/ evidence/ tools/ tasks/ research/ README.md
排除：.tools/（1.5GB Godot 线）、.git/、__pycache__、*.pyc
用法：python tools/make_source_zip.py
产物：dist/可及_源码_<日期>.zip
"""
import os, sys, zipfile, datetime

ROOT = r"E:\Claw-Data\pixel-sci-game"
INCLUDE_DIRS = ["web", "game", "docs", "evidence", "tools", "tasks", "research"]
INCLUDE_FILES = ["README.md", ".gitignore"]
SKIP_DIRS = {".tools", ".git", "__pycache__", ".godot", "exports", ".venv", "dist"}


def main():
    stamp = datetime.datetime.now().strftime("%m%d_%H%M")
    outdir = os.path.join(ROOT, "dist")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"keji_source_{stamp}.zip")
    n = 0
    total = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in INCLUDE_DIRS:
            base = os.path.join(ROOT, d)
            if not os.path.isdir(base):
                print(f"  [跳过] 不存在: {d}")
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
                for fn in filenames:
                    if fn.endswith((".pyc", ".tmp", ".bak")):
                        continue
                    p = os.path.join(dirpath, fn)
                    try:
                        z.write(p, os.path.relpath(p, ROOT))
                        n += 1
                        total += os.path.getsize(p)
                    except OSError as e:
                        print(f"  [跳过] {p}: {e}")
        for f in INCLUDE_FILES:
            p = os.path.join(ROOT, f)
            if os.path.isfile(p):
                z.write(p, f)
                n += 1
                total += os.path.getsize(p)
    size = os.path.getsize(out)
    print(f"[结果] {out}")
    print(f"       文件 {n} 个，原始 {total/1024:.0f} KB，压缩后 {size/1024:.0f} KB")
    # 自检：包里必须有成品页面与数据
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        for must in ["web/index.html", "game/data/case_library.json",
                     "game/data/archive_entries.json", "web/build_web.py"]:
            print(f"  [{'PASS' if must in names else 'FAIL'}] 包内含 {must}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
