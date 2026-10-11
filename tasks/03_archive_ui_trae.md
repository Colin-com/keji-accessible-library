# 任务 M1-A · 档案库 UI（由 Trae 完成）

## 先读

`docs/CONTRACT.md`（冻结契约）、`docs/DESIGN.md`（价值红线）。

仓库：`E:\Claw-Data\pixel-sci-game`（Godot 4.7.2）。
Godot 控制台程序：`.tools\godot\Godot_v4.7.2-stable_win64_console.exe`

## 你只写这两个文件（别的一个都别碰）

1. `res://scenes/archive_panel.tscn`
2. `res://game/archive/archive_ui.gd`

## 需求：无障碍档案库（游戏内的科普载体）

- 面板尺寸贴合 640×360：居中，宽约 520、高约 300，深色半透明底（#0e1014 的 0.92 透明度），细边框，像素风（不要圆角阴影等现代感）。
- 标题：`无障碍档案库`；右上角提示 `Tab 关闭`。
- 左侧列表（宽约 180）：一条一行显示条目 `title`。**未解锁的条目显示为 `？？？` 且不可选中**。
- 右侧详情区：显示选中条目的 `title`（大字号）、`one_liner`、`why_it_matters`、以及 `source_url`（以较小字号显示为 `来源：<url>`）。
- 数据来源：`res://game/data/archive_entries.json`（JSON 数组，字段 `id/title/one_liner/why_it_matters/source_url/tags`）。
- 解锁状态：读 autoload 单例 `Story` 的 `Story.state["unlocked"]`（数组 of id）。若 `Story` 不存在或数据文件缺失，面板必须**优雅降级**（显示「暂无条目」而不是崩）。
- 键盘操作：`Tab` 由主场景负责开关（你只实现 `open()/close()/toggle()` 三个方法）；面板内用上下键切换条目。
- 视觉上要一眼看出"这是科普档案库"：条目按 `tags` 分组可选，但分组不是必须。

## 约束

- 不用插件、不引外部素材/字体、默认字体、全中文
- 不修改 `Story`、不修改主场景、不碰 `res://game/data/`（只读它）
- 不执行 `git add` / `git commit`
- gl_compatibility 兼容（不要用 Forward+ 专有特性）

## 自证

在这两条命令下都必须干净运行（把原始输出贴回来）：

```
".tools\godot\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --import
".tools\godot\Godot_v4.7.2-stable_win64_console.exe" --headless --path . --quit-after 3
```

回报：文件清单 + 真实原始输出 + 一句话是否可用。
