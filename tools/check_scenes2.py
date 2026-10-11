import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

t = open("web/template.html", encoding="utf-8").read()
d = json.load(open("game/data/case_library.json", encoding="utf-8"))
ids = list(d["nodes"].keys())


def block(name):
    i = t.index("const " + name + "={")
    j = t.index("\n};", i)
    return t[i:j]


sc = {}
for line in block("SCENES2").splitlines():
    m = re.match(r'\s*(n_\w+):\{t:"([^"]*)"', line)
    if not m:
        continue
    sid = m.group(1)
    lm = re.search(r'light:"(\w+)"', line)
    sc[sid] = {"t": m.group(2), "light": lm.group(1) if lm else "?",
               "names": re.findall(r'\["([^"]+)"', line)}

def resolve(i, keys):
    """与模板 sceneFor() 同语义：精确 → 去掉 _bN 后缀 → 最长前缀继承"""
    if i in keys:
        return i
    b = re.sub(r"_b\d+$", "", i)
    if b != i and b in keys:
        return b
    cands = [k for k in keys if k != "__last" and i.startswith(k)]
    return max(cands, key=len) if cands else None


missing = [i for i in ids if resolve(i, set(sc)) is None]
inherit = [i for i in ids if i not in sc and resolve(i, set(sc))]
extra = [k for k in sc if k not in ids]
print("节点", len(ids), "| 场景条目", len(sc), "| 缺场景", missing, "| 继承取景", len(inherit), "| 多余", extra)
chs = sum(len(re.sub(r"\s+", "", n.get("text") or n.get("prompt") or "")) for n in d["nodes"].values())
dec = sum(1 for n in d["nodes"].values() if n["type"] == "choice")
print("正文字数", chs, "| 决策点", dec, "| 节点", len(ids))

ACTK = set(re.findall(r'\n  "?([\w\u4e00-\u9fa5]+)"?:\{map:', block("ACT")))
PROPK = set(re.findall(r'\n  "?([\w\u4e00-\u9fa5]+)"?:\{cell:', block("PROP")))
print("角色", len(ACTK), "道具", len(PROPK))
badA = sorted({n for s in sc.values() for n in s["names"]} - ACTK - PROPK)
badP = []
badL = sorted({s["light"] for s in sc.values()} - {"day", "dawn", "dusk", "bright", "rain"})
print("场景里出现的角色/道具全部已定义:", not badA, badA, "| 非法光线", badL)

bad = {}
for name in ("ACT", "PROP"):
    for m in re.finditer(r'"([\w\u4e00-\u9fa5]+)":\{(?:cell:\d+,(?:wall|floor):1,)?map:\[(.*?)\]\}', block(name), re.S):
        ws = {len(r) for r in re.findall(r'"([^"]*)"', m.group(2))}
        if len(ws) > 1:
            bad[m.group(1)] = sorted(ws)
print("行宽不一致", bad)

# 引用完整性
dangle = []
for nid, n in d["nodes"].items():
    nxt = n.get("next")
    if nxt and nxt not in d["nodes"]:
        dangle.append((nid, "next->" + nxt))
    for o in n.get("options", []):
        if o.get("next") not in d["nodes"]:
            dangle.append((nid, "opt->" + str(o.get("next"))))
ends = [i for i, n in d["nodes"].items() if n["type"] == "end"]
print("悬空引用", dangle, "| 结局", ends)

archive = json.load(open("game/data/archive_entries.json", encoding="utf-8"))
arcs = archive if isinstance(archive, list) else archive.get("entries", archive)
aid = {e["id"] for e in arcs}
unl = []
for nid, n in d["nodes"].items():
    for u in (n.get("unlock") or []):
        if u not in aid:
            unl.append((nid, u))
    for o in n.get("options", []):
        for u in (o.get("unlock") or []):
            if u not in aid:
                unl.append((nid, u))
print("档案 id 悬空", unl, "| 档案条数", len(arcs))

ok = not (missing or extra or badA or badP or badL or bad or dangle or unl)
print("[自检]", "通过" if ok else "有问题")
