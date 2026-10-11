#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓 TRAE 窗口的过程证据（比赛材料②③）。

做三件事：
  1) 截 TRAE 窗口整屏 → evidence/trae_ui.png   （"提出需求 + AI 生成结果"同框）
  2) 把当前会话的全部文字导出 → evidence/trae_dialogue.txt  （原始记录，可复查）
  3) 正则扫核验码候选（连续 hex / uuid / 大写短码）→ 打印出来，人工挑 2-3 个

用法：python tools/trae_evidence.py [调试端口，默认 9222]
"""
import base64
import json
import pathlib
import re
import sys
import urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else "9222"
ROOT = pathlib.Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
EV.mkdir(exist_ok=True)


def targets(port):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


def cdp(ws_url, method, params=None, timeout=25):
    """最小 WebSocket 客户端（不依赖第三方库）。"""
    import os
    import socket
    from urllib.parse import urlparse

    u = urlparse(ws_url)
    s = socket.create_connection((u.hostname, u.port), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall((
        f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\n"
        f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    ).encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)

    def frame(payload):
        data = payload.encode()
        hdr = bytes([0x81])
        n = len(data)
        mask = os.urandom(4)
        if n < 126:
            hdr += bytes([0x80 | n])
        elif n < 65536:
            hdr += bytes([0x80 | 126]) + n.to_bytes(2, "big")
        else:
            hdr += bytes([0x80 | 127]) + n.to_bytes(8, "big")
        return hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data))

    def read_msg():
        d = s.recv(2)
        if len(d) < 2:
            return ""
        ln = d[1] & 0x7F
        if ln == 126:
            ln = int.from_bytes(s.recv(2), "big")
        elif ln == 127:
            ln = int.from_bytes(s.recv(8), "big")
        out = b""
        while len(out) < ln:
            out += s.recv(ln - len(out))
        return out.decode("utf-8", "replace")

    s.sendall(frame(json.dumps({"id": 1, "method": method, "params": params or {}})))
    for _ in range(60):
        msg = read_msg()
        if not msg:
            continue
        try:
            obj = json.loads(msg)
        except Exception:
            continue
        if obj.get("id") == 1:
            s.close()
            return obj
    s.close()
    return {}


def main():
    tgs = [t for t in targets(PORT) if t.get("type") == "page"]
    if not tgs:
        print(f"端口 {PORT} 上没有 page 目标（TRAE 是否开着？）")
        return
    solo = next((t for t in tgs if "solo" in t.get("url", "")), tgs[0])
    print("[目标]", solo.get("title"), "|", solo.get("url", "")[:90])
    ws = solo["webSocketDebuggerUrl"]

    # 1) 截图
    r = cdp(ws, "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
    data = r.get("result", {}).get("data")
    if data:
        (EV / "trae_ui.png").write_bytes(base64.b64decode(data))
        print("[截图]", EV / "trae_ui.png", (EV / "trae_ui.png").stat().st_size, "字节")
    else:
        print("[截图失败]", str(r)[:200])

    # 2) 文字
    r = cdp(ws, "Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True})
    txt = r.get("result", {}).get("result", {}).get("value", "") or ""
    (EV / "trae_dialogue.txt").write_text(txt, encoding="utf-8")
    print("[文字]", EV / "trae_dialogue.txt", len(txt), "字符")

    # 3) 核验码候选
    cands = set()
    for pat in (r"\b[0-9a-fA-F]{16,}\b", r"\b[0-9A-Z]{8,}-[0-9A-Z]{4,}\b",
                r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"):
        cands.update(re.findall(pat, txt))
    print("[核验码候选]", len(cands))
    for c in sorted(cands)[:15]:
        print("   ", c)


if __name__ == "__main__":
    main()
