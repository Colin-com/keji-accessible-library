#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建单文件网页小游戏：web/template.html + 剧情数据 + 档案数据 -> web/index.html。

- 剧情与档案只维护在 game/data/ 下，脚本把 JSON 注入模板的 __CASE_JSON__ /
  __ARCHIVE_JSON__ 占位符，保证网页里显示的文本与数据文件逐字一致。
- ensure_ascii=False 保留中文；字符串内的换行由 json.dumps 转义成 \n，注入安全。
- 输出为无外部依赖的单文件，双击即可离线运行。
"""
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "web" / "template.html"
CASE_PATH = ROOT / "game" / "data" / "case_library.json"
ARCHIVE_PATH = ROOT / "game" / "data" / "archive_entries.json"
OUTPUT_PATH = ROOT / "web" / "index.html"

CASE_MARK = "__CASE_JSON__"
ARCHIVE_MARK = "__ARCHIVE_JSON__"


def fail(msg: str):
    print("[失败] " + msg)
    sys.exit(1)


def dumps_for_html(data) -> str:
    """ensure_ascii=False 保留中文；再把 `</` 转义成 `<\\/`（\\/ 是合法 JSON 转义），
    即使数据里出现 `</script>` 也不会提前截断模板里的 <script> 块。"""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail("找不到文件：" + str(path))
    except json.JSONDecodeError as e:
        fail(str(path) + " 不是合法 JSON：" + str(e))


def main():
    case = load_json(CASE_PATH)
    archive = load_json(ARCHIVE_PATH)
    if not isinstance(case, dict) or "nodes" not in case or "start" not in case:
        fail("case_library.json 缺少顶层 nodes/start，不符合契约")
    if not isinstance(archive, list) or not archive:
        fail("archive_entries.json 应为非空 JSON 数组")

    template = TEMPLATE.read_text(encoding="utf-8-sig")
    for mark in (CASE_MARK, ARCHIVE_MARK):
        if mark not in template:
            fail("模板 " + TEMPLATE.name + " 缺少占位符 " + mark)

    out = (template.replace(CASE_MARK, dumps_for_html(case))
                   .replace(ARCHIVE_MARK, dumps_for_html(archive)))
    OUTPUT_PATH.write_text(out, encoding="utf-8", newline="\n")

    # ── 自检：重新读回磁盘上的成品再检查 ──────────────────────────
    back = OUTPUT_PATH.read_text(encoding="utf-8")
    back_bytes = len(back.encode("utf-8"))
    first_say_line = next(
        (n["text"].splitlines()[0] for n in case["nodes"].values()
         if n.get("type") == "say" and n.get("text")),
        None,
    )
    checks = [
        ("文件已生成", OUTPUT_PATH.exists()),
        ("大小合理（成品大于模板）", back_bytes > len(template.encode("utf-8"))),
        ("占位符已全部替换", CASE_MARK not in back and ARCHIVE_MARK not in back),
        ("能搜到剧情标题", case["title"] in back),
        ("能搜到剧情文本", bool(first_say_line) and first_say_line in back),
        ("能搜到档案条目", any(e.get("title", "") in back for e in archive)),
        ("能搜到来源链接", any(e.get("source_url", "") in back for e in archive)),
    ]
    print("[输出] " + str(OUTPUT_PATH))
    print("[大小] " + str(back_bytes) + " 字节（模板 " + str(len(template.encode('utf-8'))) + " 字节）")
    ok = True
    for name, passed in checks:
        print("[自检] " + ("通过" if passed else "不通过") + " - " + name)
        ok = ok and passed
    if not ok:
        fail("自检未全部通过")
    print("[结果] index.html 构建成功，双击即可离线运行")


if __name__ == "__main__":
    main()
