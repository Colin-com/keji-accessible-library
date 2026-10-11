# -*- coding: utf-8 -*-
"""hf-mirror 分段并发下载器（带 ok 标记，防假完整）
用法: python dl_fast2.py <url> <outfile> [threads]
"""
import os, sys, math, threading, time, urllib.request, json

MIRROR = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
# 部分镜像(清华/南大)对 Range+浏览器 UA 直接 403/302，可用 DL_UA 覆盖
UA = os.environ.get("DL_UA") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def head_size(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.headers.get("Content-Length", 0)), r.headers.get("Accept-Ranges", "")


def part(url, start, end, path, idx, results):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes={start}-{end}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
                got = 0
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    got += len(chunk)
            results[idx] = got
            return
        except Exception as e:
            if attempt == 3:
                results[idx] = -1
                print(f"part{idx} fail: {e}")
            time.sleep(2 * (attempt + 1))


def main():
    url, out = sys.argv[1], sys.argv[2]
    threads = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    if not url.startswith("http"):
        url = MIRROR.rstrip("/") + "/" + url.lstrip("/")
    size, ar = head_size(url)
    print("size:", size, "ranges:", ar)
    if size == 0:
        print("HEAD failed")
        return 1
    if os.path.exists(out + ".ok") and os.path.getsize(out) == size:
        print("already complete")
        return 0
    n = threads
    step = math.ceil(size / n)
    tmp = out + ".parts"
    os.makedirs(tmp, exist_ok=True)
    results = [0] * n
    ths = []
    t0 = time.time()
    for i in range(n):
        s = i * step
        e = min(size - 1, s + step - 1)
        if s > e:
            results[i] = 0
            continue
        t = threading.Thread(target=part, args=(url, s, e, f"{tmp}/p{i}", i, results))
        t.start()
        ths.append(t)
    last = 0
    while any(t.is_alive() for t in ths):
        time.sleep(3)
        done = sum(os.path.getsize(f"{tmp}/p{i}") for i in range(n) if os.path.exists(f"{tmp}/p{i}"))
        sp = done / max(1e-6, time.time() - t0) / 1024
        print(f"  {done/1e6:.1f}/{size/1e6:.1f} MB  {sp:.0f} KB/s", flush=True)
        if done == last and time.time() - t0 > 120 and done < size * 0.02:
            print("stalled, abort")
            return 2
        last = done
    for t in ths:
        t.join()
    if any(r == -1 for r in results):
        print("some parts failed")
        return 3
    with open(out, "wb") as f:
        for i in range(n):
            p = f"{tmp}/p{i}"
            if os.path.exists(p):
                f.write(open(p, "rb").read())
    got = os.path.getsize(out)
    print("final:", got, "expected:", size, "match:", got == size)
    if got == size:
        open(out + ".ok", "w").write("ok")
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        return 0
    return 4


if __name__ == "__main__":
    sys.exit(main())
