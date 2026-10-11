#!/usr/bin/env python
"""dispatch.py — 主脑给分身派活（Claw 多 agent 调度）

用法:
    python dispatch.py img "出张测试图..."            # 派给 img 分区
    python dispatch.py img "..." --timeout 1800
    python dispatch.py img "..." --resume 20260912_135338_687993

原理: hermes -p <profile> chat -Q -q "<任务>" -Q=quiet，只回最终答复+session id，
所有工具往返、日志、看图输出都留在分身自己的上下文里，主脑只收到一行结果。

返回码: 0 成功 / 1 分身报错 / 2 超时
"""
import argparse
import re
import subprocess
import sys

HERMES = "hermes"


def dispatch(profile: str, task: str, timeout: int = 1800, resume: str | None = None) -> tuple[int, str]:
    cmd = [HERMES, "-p", profile, "chat", "-Q", "-q", task]
    if resume:
        cmd += ["--resume", resume]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return 2, f"[超时 {timeout}s] {profile} 未返回。\n{(e.stdout or '')[-2000:]}"
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if p.returncode != 0 and not out:
        return 1, f"[{profile} 退出码 {p.returncode}]\n{err[-2000:]}"
    # 抽出 session id，方便续聊
    m = re.search(r"Session:\s*(\S+)", out)
    if m:
        out += f"\n(session: {m.group(1)}  --resume {m.group(1)})"
    return 0, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", help="目标分区: img / doc / ana ...")
    ap.add_argument("task", help="任务描述（写完整，一次一个完整任务最省 token）")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--resume", default=None, help="续接某个 session id")
    a = ap.parse_args()
    rc, text = dispatch(a.profile, a.task, a.timeout, a.resume)
    print(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
