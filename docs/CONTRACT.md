# 冻结契约 v1 · 垂直切片（三方并行）

> 90 分钟黑客松。**本文件是唯一接口约定，任何一方不得擅自改动**；需要变更告诉统筹方。
> 目标产物：网页可玩 demo（图书馆无障碍改造 · 工业设计专业）。

## 责任划分（互不越界，避免互相踩）

| 路径 | 负责方 |
|-|-|
| `res://game/story/story_player.gd`（autoload 单例 `Story`） | Codex |
| `res://game/story/dialogue_ui.gd`、`res://scenes/dialogue_panel.tscn` | Codex |
| `res://scenes/library.tscn`（主场景）、`res://game/world/*.gd` | Codex |
| `res://tests/test_paths.*` | Codex |
| `res://game/archive/archive_ui.gd`、`res://scenes/archive_panel.tscn` | Trae |
| `res://game/data/case_library.json` | 内容方 |
| `res://game/data/archive_entries.json` | 内容方 |

Godot 控制台程序（**用 console 版**）：
`E:\Claw-Data\pixel-sci-game\.tools\godot\Godot_v4.7.2-stable_win64_console.exe`

## 数据契约

### `res://game/data/case_library.json`

```json
{
  "case_id": "library_access",
  "title": "图书馆无障碍改造",
  "major": "工业设计",
  "start": "n_start",
  "nodes": {
    "n_start": {
      "type": "say",
      "speaker": "小舟",
      "text": "……",
      "next": "n_2",
      "set": {"met_zhou": true},
      "relation": {"zhou": 1},
      "progress": 1,
      "unlock": ["entry_social_model"]
    },
    "n_choice": {
      "type": "choice",
      "prompt": "你打算怎么做？",
      "options": [
        {"text": "先量台阶，画一条 1:12 的缓坡方案", "next": "n_a", "set": {"solution": "ramp"}, "progress": 2},
        {"text": "找学姐组志愿者代借送书", "next": "n_b", "set": {"solution": "volunteer"}}
      ]
    },
    "n_end": {"type": "end", "ending_id": "good_project", "title": "立项", "text": "……"}
  }
}
```

规则：
- `type` 只能是 `say` / `choice` / `end`
- 指向一律用 `next`；`next` 必须指向存在的节点（测试会查悬空引用）
- `say` 可用 `next` 直接串；也可省略 `next` 表示结束
- `choice` 的每个 option 可带 `require`（`{"flag名": true/false}`）；不满足则该选项**不显示**；若过滤后无选项，必须回落到 `fallback_next` 指向的节点（若你没写 `fallback_next`，测试视为死节点=失败）
- 效果字段（都可选）：`set` 写 flags、`relation` 关系值加减、`progress` 项目进度整数加减、`unlock` 解锁档案库条目 id 数组
- 条件/效果里的 flag 名、档案 id 由内容方定义，引擎**不要硬编码任何具体剧情名**

### `res://game/data/archive_entries.json`

```json
[{"id":"entry_ramp_slope","title":"坡道坡度 1:12","one_liner":"……","why_it_matters":"……","source_url":"https://…","tags":["标准"]}]
```

## 运行时接口（名字不可改）

`Story` 是 autoload 单例，名字必须是 `Story`：

- `Story.load_case(path: String) -> void`
- `Story.current() -> Dictionary`（当前节点，含 `type`）
- `Story.visible_options() -> Array`（已按 `require` 过滤）
- `Story.choose(i: int) -> void`
- `Story.is_finished() -> bool`
- `Story.state -> Dictionary`（键：`flags` / `relation` / `progress` / `unlocked`）
- 信号：`node_changed(node)`、`ended(ending_id)`、`archive_unlocked(entry_id)`

主场景：`res://scenes/library.tscn`，640×360，占位色块（不许引入外部图片/字体）。
移动：`ui_left/right/up/down` + WASD；靠近交互点显示「按 E 交互」；按 E 进对话。
档案库：任意时刻按 `Tab` 开关；读 `res://game/data/archive_entries.json`，已解锁集合取 `Story.state.unlocked`，未解锁显示「？？？」。

## 硬性约束

- 不用任何插件、不引入外部素材/字体、不改本文件
- 不执行 `git add` / `git commit`（提交由统筹方统一做）
- 全部中文文本，默认字体
- 代码里不要写死 640×360 之外的坐标假设，占位美术要保证在 640×360 内可读

## 验收命令（统筹方会跑，你也要自己跑过并把原始输出贴回）

```
"<godot console>" --headless --path . --import
"<godot console>" --headless --path . --quit-after 3
"<godot console>" --headless --path . res://tests/test_paths.tscn     # 穷举全部选择组合
"<godot console>" --headless --path . --export-release "Web" exports/web/index.html
```

`test_paths` 必须断言：① 所有路径都能抵达 `end`；② 无悬空 `next`；③ 至少 2 个不同 `ending_id` 可达；④ 不存在"选项被过滤光且无 `fallback_next`"的死节点。通过退 0，失败退非 0 并打印失败路径。
