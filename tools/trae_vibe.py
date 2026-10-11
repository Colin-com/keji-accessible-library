#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驱动 TRAE SOLO 做「vibe coding 过程」取证。

用法：
  python tools/trae_vibe.py recon                  # 侦察：输入框/按钮/会话状态
  python tools/trae_vibe.py shot <name>            # 截当前窗口
  python tools/trae_vibe.py send <prompt.txt>      # 填入需求并提交，随后自动分步截图
  python tools/trae_vibe.py dump <name>            # 导出当前会话全部可见文字
"""
import base64
import json
import os
import pathlib
import socket
import sys
import time
import urllib.request
from urllib.parse import urlparse

PORT = os.environ.get("TRAE_PORT", "9222")
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "trae_steps"
OUT.mkdir(parents=True, exist_ok=True)


def targets(port=PORT):
    with urllib.request.urlopen("http://127.0.0.1:%s/json" % port, timeout=8) as r:
        return json.loads(r.read().decode("utf-8"))


class Cdp:
    def __init__(self, ws_url, timeout=30):
        u = urlparse(ws_url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((
            "GET %s HTTP/1.1\r\nHost: %s:%s\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n"
            % (u.path, u.hostname, u.port, key)).encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.i = 0

    def _frame(self, payload):
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

    def _read(self):
        d = self.s.recv(2)
        if len(d) < 2:
            return ""
        ln = d[1] & 0x7F
        if ln == 126:
            ln = int.from_bytes(self.s.recv(2), "big")
        elif ln == 127:
            ln = int.from_bytes(self.s.recv(8), "big")
        out = b""
        while len(out) < ln:
            out += self.s.recv(ln - len(out))
        return out.decode("utf-8", "replace")

    def call(self, method, params=None, timeout=40):
        self.i += 1
        mid = self.i
        self.s.sendall(self._frame(json.dumps({"id": mid, "method": method, "params": params or {}})))
        self.s.settimeout(timeout)
        for _ in range(400):
            msg = self._read()
            if not msg:
                continue
            try:
                obj = json.loads(msg)
            except Exception:
                continue
            if obj.get("id") == mid:
                return obj
        return {}

    def ev(self, expr, timeout=40):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, timeout)
        res = r.get("result", {}).get("result", {})
        if "value" in res:
            return res["value"]
        return None

    def shot(self, path):
        r = self.call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        data = r.get("result", {}).get("data")
        if not data:
            return None
        pathlib.Path(path).write_bytes(base64.b64decode(data))
        return pathlib.Path(path).stat().st_size

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def connect():
    tgs = [t for t in targets() if t.get("type") == "page"]
    if not tgs:
        print("[失败] 端口 %s 上没有 page 目标（TRAE 是否开着、是否带调试端口？）" % PORT)
        return None
    solo = next((t for t in tgs if "solo" in (t.get("url", "") + t.get("title", "")).lower()), tgs[0])
    print("[目标]", solo.get("title"), "|", solo.get("url", "")[:80])
    return Cdp(solo["webSocketDebuggerUrl"])


RECON_JS = r"""
(() => {
  const desc = el => ({
    tag: el.tagName, cls: (el.className||'').toString().slice(0,80),
    ph: el.getAttribute('placeholder')||'', aria: el.getAttribute('aria-label')||'',
    text: (el.innerText||'').slice(0,40).replace(/\n/g,' '),
    id: el.id||'', vis: !!(el.offsetWidth||el.offsetHeight)
  });
  const inputs = [...document.querySelectorAll('textarea,[contenteditable="true"],input[type=text]')].map(desc);
  const btns = [...document.querySelectorAll('button,[role="button"]')].map(desc).filter(d=>d.vis).slice(0,40);
  return JSON.stringify({
    title: document.title, url: location.href,
    textLen: (document.body.innerText||'').length,
    editableCount: inputs.length, editables: inputs.filter(d=>d.vis).slice(0,10),
    buttons: btns
  });
})()
"""


def recon(c):
    s = c.ev(RECON_JS)
    (OUT / "recon.json").write_text(s or "", encoding="utf-8")
    print((s or "")[:3000])


def dump(c, name):
    txt = c.ev("document.body.innerText") or ""
    p = OUT / ("%s.txt" % name)
    p.write_text(txt, encoding="utf-8")
    print("[文字]", p, len(txt), "字符")


TYPE_JS = r"""
(() => {
  const t = %s;
  const eds = [...document.querySelectorAll('textarea,[contenteditable="true"],input[type=text]')]
    .filter(el => el.offsetWidth || el.offsetHeight);
  if (!eds.length) return "NO_INPUT";
  const el = eds[eds.length - 1];
  el.focus();
  if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
    el.value = t;
    el.dispatchEvent(new Event('input', {bubbles:true}));
  } else {
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, t);
  }
  return "TYPED:" + (el.value ? el.value.length : (el.innerText||'').length);
})()
"""

SUBMIT_JS = r"""
(() => {
  const eds = [...document.querySelectorAll('textarea,[contenteditable="true"],input[type=text]')]
    .filter(el => el.offsetWidth || el.offsetHeight);
  if (!eds.length) return "NO_INPUT";
  const el = eds[eds.length - 1];
  el.focus();
  const opts = {key:'Enter', code:'Enter', keyCode:13, which:13, bubbles:true, cancelable:true};
  el.dispatchEvent(new KeyboardEvent('keydown', opts));
  el.dispatchEvent(new KeyboardEvent('keypress', opts));
  el.dispatchEvent(new KeyboardEvent('keyup', opts));
  return "ENTER_SENT";
})()
"""


def send(c, prompt_file):
    prompt = pathlib.Path(prompt_file).read_text(encoding="utf-8")
    print("[需求]", len(prompt), "字")
    print(c.ev(TYPE_JS % json.dumps(prompt)))
    time.sleep(1.2)
    n = c.shot(OUT / "step01_需求已填入.png")
    print("[截图] step01 输入框已填入需求", n, "字节")
    print(c.ev(SUBMIT_JS))
    for i, delay in enumerate([6, 12, 20, 30], start=2):
        time.sleep(delay)
        n = c.shot(OUT / ("step%02d_生成中.png" % i))
        txt = c.ev("document.body.innerText") or ""
        print("[截图] %02d 生成中 | 字数 %d | %d 字节" % (i, len(txt), n or 0))
        (OUT / ("step%02d.txt" % i)).write_text(txt, encoding="utf-8")
    dump(c, "对话全量")


SUBMIT_BTN_JS = r"""
(() => {
  const cands = [...document.querySelectorAll('button,[role="button"],div[class*="send"]')].filter(b => b.offsetParent !== null);
  const hit = cands.find(b => {
    const s = (b.className||'').toString() + ' ' + (b.getAttribute('aria-label')||'') + ' ' +
              (b.getAttribute('data-testid')||'') + ' ' + (b.innerText||'');
    return /send|发送|submit/i.test(s);
  });
  if (hit) { hit.click(); return "CLICKED:" + (hit.className||'').toString().slice(0,70); }
  return "NO_BUTTON";
})()
"""


def submit_and_watch(c, name="步"):
    # 先确认输入框里确实有内容
    txt_in = c.ev("(() => { const eds=[...document.querySelectorAll('[contenteditable=\"true\"]')].filter(e=>e.offsetParent!==null); if(!eds.length) return ''; const el=eds[eds.length-1]; el.focus(); return (el.innerText||'').trim(); })()") or ""
    print("[输入框]", len(txt_in), "字：", txt_in[:40].replace("\n", " "))
    if len(txt_in) < 5:
        print("[中止] 输入框是空的，不提交（避免发出空消息）")
        return
    # 用 CDP 真实按键事件提交（JS 合成的 KeyboardEvent 不被信任，contenteditable 会忽略）
    for t in ("rawKeyDown", "char", "keyUp"):
        c.call("Input.dispatchKeyEvent", {"type": t, "key": "Enter", "code": "Enter",
                                          "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
                                          "unmodifiedText": "\r", "text": "\r"})
    print("[发送] 已发真实回车键")
    time.sleep(2)
    base = len(c.ev("document.body.innerText") or "")
    for i, delay in enumerate([8, 12, 18, 25, 30], start=2):
        time.sleep(delay)
        txt = c.ev("document.body.innerText") or ""
        p = OUT / ("step%02d_%s.png" % (i, name))
        sz = c.shot(p)
        (OUT / ("step%02d.txt" % i)).write_text(txt, encoding="utf-8")
        print("[截图] step%02d | 字数 %d (+%d) | %d 字节" % (i, len(txt), len(txt) - base, sz or 0))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    c = connect()
    if not c:
        return
    try:
        cmd = sys.argv[1]
        if cmd == "recon":
            recon(c)
        elif cmd == "shot":
            p = OUT / ("%s.png" % sys.argv[2])
            print("[截图]", p, c.shot(p), "字节")
        elif cmd == "dump":
            dump(c, sys.argv[2])
        elif cmd == "send":
            send(c, sys.argv[2])
        elif cmd == "go":
            submit_and_watch(c, sys.argv[2] if len(sys.argv) > 2 else "生成中")
        else:
            print(__doc__)
    finally:
        c.close()


if __name__ == "__main__":
    main()
