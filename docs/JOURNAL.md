# 施工日志（复盘用）

> 规则：只记**真实发生过**的事；命令写原文，结果写原始输出要点；失败也记（失败比成功更值钱）。

## 0. 项目定位

- 形态：像素风剧情向科普游戏《可及》，底特律式分支叙事。
- 主题：**无障碍**——大学生用自己专业的本事，帮残障人士解决真实难题；玩家自选专业、自选解法。
- 约束：Trae 黑客松，**90 分钟出网页可玩 demo**。

## 1. 关键决策（含被推翻的）

| 时间 | 决策 | 理由 / 结果 |
|-|-|-|
| 15:17 | 项目落 `E:\Claw-Data\pixel-sci-game`（E 盘大盘，C 盘只放系统） | 环境约定 |
| 15:19 | 引擎 Godot **4.7.2** + 网页导出优先 | 全文本工程（.tscn/.gd/.json），agent 可写可测可自证；对比 RPG Maker 需 GUI 手点，agent 产能差一个数量级 |
| 15:20 | **不用 Dialogic 2**，自研极简剧情引擎 | Dialogic 最新为 2.0-alpha-20，配 Godot 4.7 有兼容风险，且其配置依赖编辑器 GUI——正是要避开的东西 |
| 15:2x | ~~力学知识解谜~~ → **无障碍 + 分支叙事** | **用户转向**：原 v1（物理力学）作废，改做无障碍帮助题材 |
| 15:2x | 专业=**工业设计**、案例=**图书馆无障碍改造**、游戏名《**可及**》 | 用户拍板 |
| 15:2x | Codex 不只写代码，**兼作设计顾问**（审美/视觉规范） | 用户明确要求"和 codex 沟通获得更客观有审美的设计" |
| 15:3x | 一个文件夹装下全部（工具/调研/日志都进项目根） | 用户要求：赛后复盘沉淀 |

## 2. 价值红线（内容侧，先于一切）

写无障碍题材最容易翻车的地方，也是本项目的自检项：
1. **社会模式**优先：障碍来自环境与设计，不来自人的缺陷。
2. **Nothing about us without us**：残障角色有主体性，会拒绝"好意"，不是等待被拯救的道具。
3. **拒绝怜悯叙事与说教**：价值观只通过后果、关系、生活变化呈现。
4. **事实可溯源**：每条知识/法规/技术都有出处。科普游戏讲错事实比不讲更糟。

## 3. 环境搭建（可复现）

| 项 | 做法 | 结果 |
|-|-|-|
| Godot 4.7.2 编辑器 | GitHub release 直连（86MB），`dl_fast2.py` 分段并发 8 线程 | <25 秒，约 4MB/s |
| 导出模板 | 同名 release `export_templates.tpz` | 1221MB，`.ok` 完整标记；解包到 `%APPDATA%\Godot\export_templates\4.7.2.stable`，35 个文件，含 `web_nothreads_release.zip` |
| 国内镜像 | 清华/中科大/NJU 的 github-release 镜像 | **全部 404 或不索引 godot** → 结论：本项目直接走 GitHub，不走镜像 |
| 引擎 CLI | 用 `_console.exe` 变体跑命令行 | 输出干净，适合自动化 |

## 4. 多 agent 编制与分工

| 工人 | 主职 | 本切片任务 | 任务书 |
|-|-|-|-|
| Codex CLI | 代码主力 + 设计顾问 | M0 工程与导出链、M1 剧情引擎+主场景、视觉规范咨询 | `tasks/01_M0_toolchain.md`、`tasks/02_slice_engine.md` |
| Trae SOLO | 并行模块（赛制关联） | 档案库 UI（`archive_panel.tscn` + `archive_ui.gd`） | `tasks/03_archive_ui_trae.md` |
| doc 分区分身 | 内容写作 | 剧本 `case_library.json` + 档案库 `archive_entries.json` + 校验脚本 | `tasks/04_story_data.md` |
| ana 分区分身 | 事实调研 | 无障碍事实底座 6 份（社会模式/法规/辅助技术/真实案例/误区/档案库条目） | 直接派活 |
| Hermes 统筹（我） | 设计、冻结接口、派活、**独立验收**、集成、提交 | `docs/DESIGN.md`、`docs/CONTRACT.md`、README、JOURNAL | — |

**并行纪律**：先冻结接口（`docs/CONTRACT.md`）再分头施工，各方文件集互不重叠；统一由统筹方 `git commit`，工人禁止碰主干。

## 5. 踩坑记录

| 坑 | 现象 | 处理 |
|-|-|-|
| 国内镜像不索引 Godot | 三个镜像站 404/空 | 直接 GitHub 直连，实测 4MB/s，够用 |
| Codex 沙箱内 `.git` 只读 | 提交失败 | **git 提交归统筹方**，工人只写代码（写进派活纪律） |
| Trae SOLO 的第二实例 | 隔离 `--user-data-dir` 实例约 20s 自退，端口不监听 | 放弃隔离实例；改为用用户原 profile 带 `--remote-debugging-port=9222` 启动 |
| Trae 调试口生命周期 | 只对**本次启动的进程**有效，用户自重启即失效 | 记录为约束：需重新带参启动 |
| SOLO 的"项目"与编辑器工作区不是一个概念 | `trae-solo-cn.cmd -a` 挂上了文件夹，但会话仍显示"项目/默认" | 见第 7 节后续 |

## 6. 验收记录（统筹方独立跑，只认产物）

M0 验收（**已通过**，日志见 `logs/`）：
```
.tools/godot/Godot_v4.7.2-stable_win64_console.exe --headless --path . --import      # OK
.tools/godot/Godot_v4.7.2-stable_win64_console.exe --headless --path . --quit-after 2  # 打印版本号，不崩
.tools/godot/Godot_v4.7.2-stable_win64_console.exe --headless --path . --export-release "Web" exports/web/index.html  # savepack DONE
strings exports/web/index.pck | grep -c "M0 OK"   # =1  → 场景文本真的进了包
```

## 7. 时间线（施工中，边做边记）

- 15:17 建仓（git init）
- 15:19-15:23 引擎与模板下载、安装
- 15:23-15:31 Codex 完成 M0；统筹方独立验收通过并提交 `7a6000c`
- 15:25-15:32 ana 分身产出调研底座 6 份（合计 ~142KB，全部带来源）
- 15:32 冻结 `docs/CONTRACT.md`，写三方任务书
- 15:33 三方开工：Codex(M1 引擎) / doc(剧本数据) / Trae(档案库 UI)
- 15:36 用户指示：Codex 兼设计顾问 → 派视觉规范咨询（只读沙箱，不改文件）
- 15:40 用户指示：全部文件工具收进一个文件夹 → 建 `research/ tools/ logs/`，本日志立起

## 8. 重大转向：砍 Godot，改纯网页（承用户"赛程已经过半"）

| 时间 | 事 | 结果 |
|-|-|-|
| 15:45 | 用户："赛程已经过半了" | 判断：90 分钟窗口内，Godot 导出链（1.2GB 模板刚下完）性价比不划算 → **改纯网页** |
| 15:46 | 杀 Godot 线的 codex 进程 | 剩余 codex 进程 = 0 |
| 15:47 | 自建 `web/template.html`（像素 UI + 数据驱动剧情引擎），留 `__CASE_JSON__` / `__ARCHIVE_JSON__` 注入占位符 | 279 行 |
| 15:52 | `web/build_web.py` 一次性构建 | `web/index.html` 20,541 字节；自检"剧情文本可搜到 True / 档案来源可搜到 True" |
| 15:45 派 / 16:00 回 | **Trae 接新需求并交付**（自己写 build_web.py + 自检） | 产物 26,297 字节；统筹方独立复验通过（**关键步骤由 Trae 完成** = 赛制关联） |
| 16:2x | 补全游戏外壳 | 首界面 / 操作说明 / HUD 工具条 / 结局结算 / 解锁提示 |

## 9. 验收记录（纯网页版，统筹方独立跑，只认产物）

- **真实浏览器（CDP）点着走完两条路径**：
  - 路径A（每步选第一项）→ 结局《能动用了》，档案解锁 5/10
  - 路径B（每步选最后一项）→ 结局《半程》，解锁 3/10
- **数据侧**：doc 分身校验器 exit 0（30 节点 / 39 条引用 0 悬空 / 2 结局 / 10 条档案 `source_url` 逐字命中调研底座）
- **事实对表**（拿 ana 事实底座逐条验）：第四十条低位服务台、第三十条同步字幕、第四十六条服务犬、GB 50763 表 3.4.4（1:12 → 限高 0.75m、水平长 9.00m；本项目 0.45m×12 = 5.4m 落在表内）——全部一致，无需返工
- **界面四屏**：无头 Edge 出图 1180×1460（`ui_menu` / `ui_gameplay` / `ui_help` / `ui_ending`）

## 10. 踩坑（含统筹方自己的验收错误）

| 坑 | 现象 | 处理 |
|-|-|-|
| `#menu` 是 `position:fixed` 且默认 `display:flex`，隐藏只移了 class | 点"开始游戏"后**标题页一直盖在游戏上** | 改 `#menu{display:none}` + `#menu.on{display:flex}` |
| **用 `offsetParent` 判断可见性** | `fixed` 元素 `offsetParent` 恒为 `null` → 误判"已隐藏"，上面那个 bug 被我自己放过一次 | 改用 `getComputedStyle(el).display` + `rect.width>0` + `elementFromPoint()` 判最上层元素 |
| `capture_screenshot()` 写同一路径 | 四张"不同界面"实际互相覆盖、全是同一页（尺寸几乎一样，102KB） | 每张单独落盘 + `md5sum` 校验；改用无头 Edge 出图后尺寸区分明显（102/26/47/47KB） |
| 后台标签页定时器降频 | 固定等 9 秒判定 `?screen=end`「卡住」，实际 15 秒才到结局 | 验收改成轮询 + 每步打印状态 |
| `.tools/`（1.5GB）被 `git add -A` 提交 | `.git` 膨胀到 **1.4GB**，源码包与推送都会炸 | 补 `.gitignore` → `reset --soft` 撤销 → `git rm -r --cached` → 重提交 → `gc`；`.git` 降到 **375K** |

## 11. 证据流水线（比赛材料②③）

- `tools/trae_evidence.py`：TRAE 窗口截图 + 会话文字导出 + 核验码候选扫描
- `tools/evidence_shots.py`：无头 Edge 出四张界面图（页面支持 `?screen=game|help|end` 直达）
- **核验码排查（七处全空）**：会话正文 / 元素属性 / shadow DOM / iframe / 回答操作区 / **TRAE 程序文件 `resources/` 内字符串** / 复制出的 54KB 文本 → 本版本无该字段
- 误抓的 `6acb34f92196c87c6c631d84` 实为 TRAE 沙箱工作目录 ID，**已标红禁用**（误提交会被判诚信问题）

## 12. 交付物与赛后清理

- 源码包：`dist/keji_source_1011_1607.zip`（54 文件 / 压缩后 482KB，自检含成品页与两份数据）
- `提交清单.md`（三份材料对照 + 演示命令 + 不可提交项）
- `docs/路演稿.md`（2 分钟卡点 + 3 个备答）
- `docs/赛后待办.md`：Godot 线 **3.5GB** 精确删除清单（`.tools` 1.5GB + `%APPDATA%\Godot\export_templates` 2.0GB）
