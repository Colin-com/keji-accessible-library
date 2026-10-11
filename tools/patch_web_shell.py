#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网页版外壳补丁：把 Godot 默认 index.html 改成《可及》的样子。

为什么用补丁而不是 custom_html_shell：改 shell 模板要写对一堆 $GODOT_* 占位符，
改错了整个导出会失败；补丁脚本是确定性的、可重复运行（幂等），零风险。
注意：每次 --export-release 都会覆盖 index.html，所以导出后必须再跑一次本脚本。

用法：python tools/patch_web_shell.py [exports/web/index.html]
"""
import pathlib
import re
import sys

P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                 r"E:\Claw-Data\pixel-sci-game\exports\web\index.html")
if not P.exists():
    sys.exit(f"找不到 {P}（先跑 web 导出）")

s = P.read_text(encoding="utf-8")
before = len(s)

s = s.replace('<html lang="en">', '<html lang="zh-CN">')
s = re.sub(r"<title>.*?</title>", "<title>《可及》 · 无障碍科普叙事 Demo</title>",
           s, count=1, flags=re.S)
s = s.replace("background-color: black;", "background-color: #12141a;")

if "zd-sub" not in s:
    # 1) 加载文案（在进度条下方）
    s = s.replace(
        '<progress id="status-progress"></progress>',
        '<progress id="status-progress"></progress>\n'
        '\t\t\t<div id="zd-sub">正在载入《可及》……'
        '<br><span>一个大学生用工业设计的本事，让图书馆对轮椅真正可用</span></div>',
        1,
    )
    # 2) 样式
    s = s.replace(
        "#status-progress {\n\tbottom: 10%;",
        '#zd-sub {\n'
        '\tposition: absolute;\n'
        '\tleft: 0;\n'
        '\tright: 0;\n'
        '\tbottom: 3.5%;\n'
        '\ttext-align: center;\n'
        '\tcolor: #8d93a3;\n'
        '\tfont-family: -apple-system, "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;\n'
        '\tfont-size: 13px;\n'
        '\tline-height: 1.8;\n'
        '\tletter-spacing: 0.04em;\n'
        '}\n'
        '#zd-sub span {\n'
        '\tcolor: #575d6b;\n'
        '\tfont-size: 11px;\n'
        '}\n'
        '#status {\n\tbackground-color: #12141a;\n}\n'
        '#status-progress {\n\tbottom: 10%;',
        1,
    )

P.write_text(s, encoding="utf-8")
print(f"[ok] 已打补丁 {P}  ({before} -> {len(s)} 字节)")
for k in ["<title>", "zd-sub", 'lang="zh-CN"']:
    print(f"  · {k}: {'在' if k in s else '缺失!'}")
