#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用无头 Edge 给网页版 demo 出界面截图（比赛材料②：AI 生成结果）。

用途：CDP 截图超时时，用浏览器自带的无头模式批量出图。
用法：先起本地服务（python -m http.server 8899 --directory web），再：
    python tools/evidence_shots.py
产物：evidence/ui_menu.png / ui_gameplay.png / ui_help.png / ui_ending.png
"""
import os, struct, subprocess, sys, time

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
BASE = "http://127.0.0.1:8899/index.html"
OUT = r"E:\Claw-Data\pixel-sci-game\evidence"
SHOTS = [
    ("",            "ui_menu.png",     "首界面（标题/立意/入口）"),
    ("?screen=game", "ui_gameplay.png", "游戏中（场景 + HUD 三条 + 选项）"),
    ("?screen=help", "ui_help.png",     "操作说明面板"),
    ("?screen=end",  "ui_ending.png",   "结局结算页（轨迹 + 解锁数）"),
]


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def png_size(path):
    """读 PNG 的 IHDR，返回 (宽, 高)；失败返回 (0, 0)。"""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return (0, 0)
        w, h = struct.unpack(">II", head[16:24])
        return (w, h)
    except Exception:
        return (0, 0)


def main():
    edge = find_edge()
    if not edge:
        print("[错误] 找不到 msedge.exe，请手动指定路径")
        return 2
    os.makedirs(OUT, exist_ok=True)
    profile = os.path.join(os.environ.get("TEMP", "."), "edge_shot_profile")
    ok = 0
    for query, name, desc in SHOTS:
        dst = os.path.join(OUT, name)
        if os.path.exists(dst):
            os.remove(dst)
        cmd = [edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={profile}",
               "--window-size=1180,1460",
               "--virtual-time-budget=7000",
               f"--screenshot={dst}",
               BASE + query]
        subprocess.run(cmd, capture_output=True, timeout=180)
        time.sleep(0.4)
        size = os.path.getsize(dst) if os.path.exists(dst) else 0
        w, h = png_size(dst) if size else (0, 0)
        flag = "OK " if size > 8000 and w > 0 else "!! "
        print(f"{flag}{name:18s} {w}x{h}  {size/1024:6.1f} KB   {desc}")
        if flag == "OK ":
            ok += 1
    print(f"[结果] {ok}/{len(SHOTS)} 张截图成功 → {OUT}")
    return 0 if ok == len(SHOTS) else 1


if __name__ == "__main__":
    sys.exit(main())
