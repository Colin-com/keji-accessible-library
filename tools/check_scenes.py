"""场景与像素素材一致性检查（改完 template.html 必跑）

检查项：
  1. 每个字符画 map 的行宽必须一致（不等宽 → 像素图会错位）
  2. SCENES 覆盖剧情数据里的每个节点（不多不少）
  3. SCENES 里引用的角色/道具名必须在 ACT / PROP 里定义
  4. 模板里不能残留 "？？？" 之类的占位问号
  5. light 取值必须在 CSS 支持的档位里
用法：python tools/check_scenes.py      # 退出码 0 = 全过
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "web" / "template.html"
CASE = ROOT / "game" / "data" / "case_library.json"
LIGHTS = {"day", "dawn", "dusk", "bright"}

src = TPL.read_text(encoding="utf-8")
fail = []

# 1. 字符画行宽
maps = re.findall(r"map:\[(.*?)\]\}", src, re.S)
total_rows = 0
for i, blk in enumerate(maps):
    rows = re.findall(r'"([^"]*)"', blk)
    total_rows += len(rows)
    widths = sorted({len(r) for r in rows})
    if len(widths) != 1:
        fail.append(f"map#{i} 行宽不一致 {widths}：{rows[:4]}")

# 2. 角色/道具定义
act_names = set(re.findall(r'^\s*"([^"]+)":\{map:\[', src, re.M))
prop_names = set(re.findall(r"^\s*([a-z]+):\{cell:\d+,(?:wall|floor):1,map:\[", src, re.M))
scene_block = re.search(r"const SCENES=\{(.*?)\n\};", src, re.S)
if not scene_block:
    fail.append("没找到 SCENES 表")
    scenes = {}
else:
    scenes = dict(re.findall(r'\n (\w+):\{t:"([^"]*)"', scene_block.group(1)))
    refs = re.findall(r'\["([^"]+)",\s*\d+\]', scene_block.group(1))
    for r in refs:
        if r not in act_names and r not in prop_names:
            fail.append(f"SCENES 引用了未定义的素材：{r}")
    lights = set(re.findall(r'light:"([^"]*)"', scene_block.group(1)))
    for l in lights - LIGHTS:
        fail.append(f"light 档位不支持：{l}")

# 3. 节点覆盖
case = json.loads(CASE.read_text(encoding="utf-8"))
nodes = set((case["nodes"] if isinstance(case, dict) else case).keys())
missing = sorted(nodes - set(scenes))
extra = sorted(set(scenes) - nodes)
if missing:
    fail.append(f"剧情节点没有场景：{missing}")
if extra:
    fail.append(f"场景表有剧情里不存在的节点：{extra}")

# 4. 残留占位问号
for m in re.finditer(r"[？?]{2,}", src):
    line = src[: m.start()].count("\n") + 1
    fail.append(f"第 {line} 行残留占位问号：{m.group(0)}")

print(f"[检查] 字符画 {len(maps)} 块 / {total_rows} 行；场景 {len(scenes)} 个；剧情节点 {len(nodes)} 个")
if fail:
    print("[失败]")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("[通过] 行宽一致 · 节点全覆盖 · 素材引用有效 · 无占位问号")
