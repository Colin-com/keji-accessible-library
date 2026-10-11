#!/usr/bin/env python3
"""Drive an Electron/VS Code-fork window over CDP (stdlib only).

App must be running with --remote-debugging-port=9222.

  python trae_cdp.py list
  python trae_cdp.py eval "document.title"
  python trae_cdp.py find ".chat-input-v2-input-box-editable"
  python trae_cdp.py click 573 475            # real mouse click (viewport px)
  python trae_cdp.py type "hello"             # real text insert into focused el
  python trae_cdp.py key ctrl+a               # real key combo
  python trae_cdp.py keys ctrl+a Backspace    # sequence
"""
import argparse
import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request

PORT = 9222


def list_targets(port=PORT, timeout=6):
    with urllib.request.urlopen("http://127.0.0.1:%d/json" % port, timeout=timeout) as r:
        return json.load(r)


def ws_connect(ws_url, timeout=20):
    hostport, path = ws_url[5:].split("/", 1)
    host, port = hostport.split(":")
    sock = socket.create_connection((host, int(port)), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode()
    req = ("GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n"
           "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
           "Sec-WebSocket-Version: 13\r\n\r\n" % (path, hostport, key))
    sock.sendall(req.encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("handshake closed")
        buf += chunk
    head, leftover = buf.split(b"\r\n\r\n", 1)
    if b" 101" not in head.split(b"\r\n")[0]:
        raise RuntimeError("handshake failed: %s" % head.decode("utf-8", "replace"))
    return sock, leftover


def ws_send_text(sock, text):
    payload = text.encode("utf-8")
    header = bytearray([0x81])
    n = len(payload)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header += bytes([0x80 | 126]) + struct.pack(">H", n)
    else:
        header += bytes([0x80 | 127]) + struct.pack(">Q", n)
    mask = os.urandom(4)
    header += mask
    sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))


def ws_recv_text(sock, buf=b"", timeout=30):
    sock.settimeout(timeout)

    def need(n):
        nonlocal buf
        while len(buf) < n:
            chunk = sock.recv(65536)
            if not chunk:
                raise EOFError("websocket closed")
            buf += chunk

    out = b""
    while True:
        need(2)
        b1, b2 = buf[0], buf[1]
        fin, opcode, length, pos = b1 & 0x80, b1 & 0x0F, b2 & 0x7F, 2
        if length == 126:
            need(4)
            length = struct.unpack(">H", buf[2:4])[0]
            pos = 4
        elif length == 127:
            need(10)
            length = struct.unpack(">Q", buf[2:10])[0]
            pos = 10
        need(pos + length)
        payload, buf = buf[pos:pos + length], buf[pos + length:]
        if opcode == 0x8:
            raise EOFError("websocket closed by peer")
        if opcode in (0x1, 0x2):
            out += payload
        if fin and opcode in (0x1, 0x2):
            return out.decode("utf-8", "replace"), buf


class Client:
    def __init__(self, ws_url, timeout=30):
        self.sock, self.buf = ws_connect(ws_url)
        self.timeout = timeout
        self.next_id = 0

    def call(self, method, params=None):
        self.next_id += 1
        msg_id = self.next_id
        ws_send_text(self.sock, json.dumps({"id": msg_id, "method": method,
                                            "params": params or {}}))
        while True:
            text, self.buf = ws_recv_text(self.sock, self.buf, self.timeout)
            data = json.loads(text)
            if data.get("id") != msg_id:
                continue
            if "error" in data:
                raise RuntimeError(json.dumps(data["error"], ensure_ascii=False))
            return data.get("result", {})

    def eval(self, expression):
        r = self.call("Runtime.evaluate", {"expression": expression,
                                           "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in r:
            return "EXCEPTION: " + json.dumps(r["exceptionDetails"], ensure_ascii=False)
        inner = r.get("result", {})
        return inner.get("value", inner)

    def mouse_click(self, x, y, button="left"):
        bits = {"left": 1, "right": 2, "middle": 4}[button]
        for ev in ("mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", {
                "type": ev, "x": x, "y": y, "button": button,
                "buttons": bits, "clickCount": 1})
            time.sleep(0.05)

    def insert_text(self, text):
        self.call("Input.insertText", {"text": text})

    def key(self, combo):
        mods = 0
        parts = combo.split("+")
        key = parts[-1]
        for m in parts[:-1]:
            mods |= {"alt": 1, "ctrl": 2, "meta": 4, "cmd": 4, "shift": 8}[m.lower()]
        table = {
            "enter": ("Enter", "Enter", 13), "return": ("Enter", "Enter", 13),
            "backspace": ("Backspace", "Backspace", 8), "delete": ("Delete", "Delete", 46),
            "escape": ("Escape", "Escape", 27), "esc": ("Escape", "Escape", 27),
            "tab": ("Tab", "Tab", 9), "space": (" ", "Space", 32),
            "up": ("ArrowUp", "ArrowUp", 38), "down": ("ArrowDown", "ArrowDown", 40),
            "left": ("ArrowLeft", "ArrowLeft", 37), "right": ("ArrowRight", "ArrowRight", 39),
            "home": ("Home", "Home", 36), "end": ("End", "End", 35),
            "pagedown": ("PageDown", "PageDown", 34), "pageup": ("PageUp", "PageUp", 33),
        }
        if key.lower() in table:
            k, code, vk = table[key.lower()]
        elif len(key) == 1:
            k = key
            code = "Key" + key.upper() if key.isalpha() else (
                "Digit" + key if key.isdigit() else "")
            vk = ord(key.upper()) if key.isalpha() else ord(key)
        else:
            raise SystemExit("unknown key: %s" % key)
        self.call("Input.dispatchKeyEvent", {"type": "rawKeyDown", "modifiers": mods,
                                             "key": k, "code": code,
                                             "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk})
        if len(k) == 1 and not mods & 2:
            self.call("Input.dispatchKeyEvent", {"type": "char", "text": k})
        self.call("Input.dispatchKeyEvent", {"type": "keyUp", "modifiers": mods,
                                             "key": k, "code": code,
                                             "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk})
        time.sleep(0.05)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


FIND_JS = """(() => {
  const sel = %s;
  const out = [];
  document.querySelectorAll(sel).forEach((e, i) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    out.push({i, tag: e.tagName, cls: String(e.className).slice(0, 70),
              text: (e.innerText || e.value || '').trim().slice(0, 90),
              vis: !!e.offsetParent && cs.visibility !== 'hidden',
              box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]});
  });
  return JSON.stringify(out, null, 1);
})()"""


def pick(port, match=None):
    pages = [t for t in list_targets(port) if t.get("type") == "page"] or list_targets(port)
    if match:
        hit = [t for t in pages if match.lower() in (t.get("title", "") + t.get("url", "")).lower()]
        if hit:
            pages = hit
    if not pages:
        raise SystemExit("no page target on port %d" % port)
    return pages[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "eval", "find", "click", "type", "key", "keys"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--match", default=None)
    a = ap.parse_args()

    if a.cmd == "list":
        for t in list_targets(a.port):
            print("%s | %s | %s" % (t.get("type"), t.get("title"), t.get("url")))
        return 0

    c = Client(pick(a.port, a.match)["webSocketDebuggerUrl"])
    try:
        if a.cmd == "eval":
            v = c.eval(a.args[0] if a.args else "document.title")
            print(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        elif a.cmd == "find":
            print(c.eval(FIND_JS % json.dumps(a.args[0])))
        elif a.cmd == "click":
            x, y = int(a.args[0]), int(a.args[1])
            c.mouse_click(x, y)
            print("clicked %d,%d" % (x, y))
        elif a.cmd == "type":
            c.insert_text(" ".join(a.args))
            print("typed")
        elif a.cmd == "key":
            c.key(a.args[0])
            print("key %s" % a.args[0])
        elif a.cmd == "keys":
            for k in a.args:
                c.key(k)
            print("keys %s" % " ".join(a.args))
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
