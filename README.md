# 《可及》· 项目总目录（一个文件夹装下全部）

> 像素风剧情向科普游戏：大学生用自己专业的本事，帮残障人士解决真实的无障碍难题。
> **本目录是唯一的项目根**：代码、任务书、调研、工具、日志、产物全在这里，赛后按本文件即可完整复盘。

## 一、目录地图

| 路径 | 里面是什么 | 复盘时看什么 |
|-|-|-|
| `project.godot` `scenes/` `game/` `tests/` | Godot 4.7.2 工程本体 | 游戏怎么实现的 |
| `docs/DESIGN.md` | 设计文档：价值红线、玩法支柱、MVP 切片范围 | **最重要**：为什么这么做 |
| `docs/CONTRACT.md` | 冻结契约：三方并行开发的接口约定 | 多 agent 怎么不互相踩 |
| `docs/JOURNAL.md` | **施工日志**：时间线、决策、踩坑、验收记录 | 复盘主线 |
| `docs/DEV.md` | 怎么跑、怎么测、怎么导出（工程侧说明） | 复现步骤 |
| `tasks/0X_*.md` | 派给各 agent 的任务书（原文） | 派活的写法 |
| `research/` | 调研底座：社会模式、法规标准、辅助技术、真实案例、误区、档案库条目（每条带来源 URL） | 内容准确性来源 |
| `tools/` | 复用工具：`trae_cdp.py`(驱动 Trae 界面) / `dl_fast2.py`(分段下载) / `dispatch.py`(给分区 agent 派活) / `validate_case.py`(剧情数据校验) | 怎么遥控 agent |
| `logs/` | 施工期原始输出：agent 回报、验收命令原始日志 | 证据链 |
| `exports/web/` | 交付产物：网页版（index.html + wasm + pck） | 交付物 |
| `.tools/godot/` | Godot 4.7.2 引擎本体（含 console 版，命令行用） | 环境复现 |
| `.tools/export_templates/` | 导出模板包（1221MB，网页导出必需） | 环境复现 |

## 二、怎么跑（复盘时最快的路径）

```bash
cd /e/Claw-Data/pixel-sci-game
G=".tools/godot/Godot_v4.7.2-stable_win64_console.exe"

# 1) 导入资源
"$G" --headless --path . --import

# 2) 自动测试：穷举剧情全部选择组合（无死节点、至少 2 结局可达）
"$G" --headless --path . res://tests/test_paths.tscn

# 3) 导出网页版
"$G" --headless --path . --export-release "Web" exports/web/index.html

# 4) 本地起服务预览（然后浏览器打开 http://127.0.0.1:8899/）
python -m http.server 8899 -d exports/web
```

## 三、这个东西是怎么做出来的（一句话版）

我（Hermes 统筹）负责：设计、冻结接口、写任务书、派活、**独立验收**；
工人池：Codex CLI（代码主力 + 设计顾问）、Trae SOLO（并行模块）、doc 分区分身（剧本数据）、ana 分区分身（事实调研）。
详细时间线与决策见 `docs/JOURNAL.md`。

## 四、赛道定位

Trae 黑客松 · 90 分钟垂直切片。提交口径：**网页 demo 可玩**。
