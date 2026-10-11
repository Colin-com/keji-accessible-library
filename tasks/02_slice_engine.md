# 任务 M1 · 剧情引擎 + 主场景（Codex）

## 先读

`docs/CONTRACT.md`（冻结契约，接口不可改）、`docs/DESIGN.md`（项目价值与红线）。

仓库：`E:\Claw-Data\pixel-sci-game`（Godot 4.7.2 已就位，M0 链路已验证通过）。
Godot 控制台程序：`.tools\godot\Godot_v4.7.2-stable_win64_console.exe`

## 你要产出的

1. `res://game/story/story_player.gd` —— autoload 单例 `Story`，按契约实现全部 API 与信号。数据驱动，**不得硬编码任何具体剧情名/flag 名**。
2. `res://scenes/dialogue_panel.tscn` + `res://game/story/dialogue_ui.gd` —— 打字机效果的对话面板：显示说话人 + 文本；有选项时列出选项（键盘上下 + Enter 或数字键 1/2/3 选择，鼠标点亦可）；对话结束后关闭并把控制权交回主场景。
3. `res://scenes/library.tscn` + `res://game/world/player.gd`、`res://game/world/interactable.gd` —— 主场景：
   - 640×360，深色底，用 ColorRect/Label **占位**画一个图书馆：入口台阶、服务台、阅览区书架、公告板、一扇门。不许引入外部素材。
   - 玩家是一个 ColorRect（工业设计学生，色块即可），WASD/方向键移动，被画面边界和几个静态障碍挡住即可（不需要物理引擎，简单的矩形碰撞判断就够）。
   - 4 个交互点（Area2D + 提示「按 E 交互」）：小舟（轮椅学生，在服务台旁）、馆长（服务台后）、学姐（阅览区）、公告板。按 E 触发对应剧情节点的跳转/对话。
   - 剧情入口：`Story.load_case("res://game/data/case_library.json")`；交互点触发时 `Story.goto(node_id)`（自行按契约语义实现，或直接 load_case 后跳到指定节点）。
4. `res://game/archive/` 下的东西**不要动**（Trae 负责档案库 UI）。你只需在主场景里预留：按 `Tab` 时实例化 `res://scenes/archive_panel.tscn`（若该文件还不存在，用 `ResourceLoader.exists()` 判断后跳过，不要报错崩掉）。
5. `res://tests/test_paths.tscn` + 脚本 —— 穷举剧情图全部选择组合的自动测试（见契约验收）。若 `res://game/data/case_library.json` 尚未就位，先写内置 fixture `res://tests/fixture_case.json` 自测，数据到位后要对正式数据再跑一次。
6. `docs/DEV.md` 追加一节：怎么跑测试、怎么看结局覆盖。
7. 把 `project.godot` 的 `config/name` 改成 `可及`（游戏名），其余配置不要动。

## 约束

- 不碰 `res://game/data/`（内容方在写）、不碰 `res://game/archive/`（Trae 在写）、不改 `docs/CONTRACT.md`
- 不执行 `git add` / `git commit`
- 全程中文 UI 文本；默认字体；不用插件；gl_compatibility 兼容（不要用 Forward+ 专有特性）

## 回报（只回这些）

1. 新建/修改文件清单
2. 上面 4 条验收命令的**真实原始输出**（含 test_paths 的结果）
3. 报错原文 + 你的判断
4. 一句话：引擎是否可用
