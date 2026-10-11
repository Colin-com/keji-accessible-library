# 任务 M0：搭出可 headless 运行 + 可导出 Web 的最小 Godot 工程

## 背景（你看不到我们的对话，所以这里自洽）

项目：剧情向像素科普游戏（物理/力学），交付形态**网页版优先**（浏览器打开即玩）。
引擎：Godot **4.7.2-stable**（已就位）。仓库根目录 = 本文件所在仓库 `E:\Claw-Data\pixel-sci-game`。

引擎可执行文件（**用 console 版**，stdout 干净）：
```
E:\Claw-Data\pixel-sci-game\.tools\godot\Godot_v4.7.2-stable_win64_console.exe
```
（同目录另有 GUI 版 `..._win64.exe`，别用它跑 CLI。）

## 目标

搭出最小可运行工程，把「headless 导入 → 启动不崩 → 导出 Web」这条技术链打通。**不要做游戏内容**，M0 只验证链路。

## 必须产出的文件

1. `project.godot`
   - `config_version=5`
   - 名称 `PixelPhysics`，主场景 `res://scenes/main.tscn`
   - 窗口 640x360，stretch mode `canvas_items`，aspect `keep`
   - 渲染方式 `gl_compatibility`（Web 兼容性最好）
   - 像素风设置：纹理过滤用 nearest（`rendering/textures/canvas_textures/default_texture_filter=0`）
   - 保留默认 `ui_*` 输入映射即可，不新增
2. `scenes/main.tscn`
   - `Node2D` 根节点 + `ColorRect`（深色背景 #14161c，铺满视口）+ `Label`
   - Label 文本：`M0 OK · Godot 4.7.2 · Web 导出链路`
   - Label 居中，字体大小 16，浅色，用默认字体（不要引入外部字体文件）
   - 场景必须能被 headless 加载，不允许引用任何外部资源
3. `export_presets.cfg`
   - 一个 preset，名称 `Web`，`platform="Web"`
   - 导出路径 `exports/web/index.html`
   - `variant/thread_support=false`（避免 SharedArrayBuffer 要求 COOP/COEP 响应头，方便本地直接开）
   - 其他保持安全默认；`exclude_filter` 排除 `.tools/`、`docs/`、`tasks/`
4. `scripts/build_web.ps1`
   - 取引擎路径：优先环境变量 `GODOT_BIN`，否则用上面的默认绝对路径
   - 步骤：`--headless --path <repo> --import` → `--headless --path <repo> --export-release "Web" exports/web/index.html`
   - 任何一步非 0 退出码都要打印清晰中文报错并 exit 1
   - 顺带检查 `exports/web/index.html` 是否生成，打印产物大小
5. `docs/DEV.md`：怎么 headless 导入、怎么导出 Web、怎么本地起静态服务器预览（`python -m http.server`）、已知坑

## 硬性约束

- **不要执行 `git commit` / `git add`**（提交由统筹方统一做；沙箱里 .git 也只读）
- 不要碰 `.git/`、`.tools/`
- 不要引入任何插件、外部素材、字体文件
- 不要创建 `art_placeholder/` 之外的新顶层目录（`exports/` 已在 .gitignore）

## 你必须自己跑过并把原始输出贴回来

```
"<console exe>" --headless --path . --import
"<console exe>" --headless --path . --quit-after 2
```
（第二条能起来且不报错即视为通过。导出模板可能还在下载，若导出失败，原样贴报错，不要假装成功。）

## 回报格式（只回这些，不要长篇解释）

1. 新建/修改的文件路径清单
2. 上面两条命令的**真实原始输出**（截取关键行即可）
3. 报错原文（若有）与你判断的原因
4. 一句话：链路是否打通
