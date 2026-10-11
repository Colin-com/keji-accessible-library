# 《可及》· 无障碍科普叙事游戏（网页版）

> 一款像素风分支叙事科普游戏：你扮演工业设计专业的大学生，用自己专业的本事，
> 帮轮椅使用者、视障老人等**当事人**解决图书馆真实的无障碍难题。
> 主题是**社会模式**：障碍来自环境与设计，不来自人。

**在线试玩**：https://&lt;你的用户名&gt;.github.io/keji-accessible-library/web/index.html
（也可离线：直接双击 `web/index.html`，单文件、零依赖）

---

## 一、程序实现的功能（96 字，提交口径）

《可及》是网页像素叙事游戏：你扮演工业设计学生，为学校图书馆做无障碍改造——和轮椅使用者、视障老人一起量台阶、定方案，选择改变进度、信任与受益范围，通向 4 种结局，解锁 14 条可溯源科普档案。

## 二、怎么玩

| 操作 | 作用 |
|-|-|
| 点文字 / 空格 | 跳过打字机动画 |
| 点选项 / 按 1–5 | 做选择 |
| Tab | 打开档案库（14 条科普条目，跨局累积解锁） |
| R | 重开一局 |
| Esc | 关闭面板 |

四条指标：**项目进度 / 当事人信任 / 可疑度 / 受益范围**。
选择不只是解锁剧情，会真的改变后面的人怎么对你、以及最后那笔账算不算得清。

## 三、网页版跑起来

```bash
# 最省事：双击 web/index.html

# 或者本地起个服务（推荐，避免个别浏览器对本地文件的限制）
python -m http.server 8899 -d web
# 然后打开 http://127.0.0.1:8899/index.html
```

改完模板/剧本后重新打包单文件：

```bash
python web/build_web.py      # web/template.html + game/data/*.json → web/index.html
python tools/check_scenes2.py  # 一致性自检：节点/场景/结局/悬空引用
```

## 四、目录地图

| 路径 | 里面是什么 |
|-|-|
| `web/template.html` | **唯一事实来源**：像素素材表、场景驱动、状态机、UI |
| `web/index.html` | 构建产物：单文件可玩版（离线） |
| `web/build_web.py` | 模板 + 数据 → 单文件 |
| `game/data/case_library.json` | 剧情：117 节点 / 9 决策点 / 4 结局 / 正文 4681 字 |
| `game/data/archive_entries.json` | 档案库：14 条科普条目，每条带来源 |
| `research/` | 调研底座：社会模式、GB 50763 等标准、辅助技术、真实案例 |
| `docs/DESIGN.md` | 设计文档：内容红线、玩法支柱、MVP 切片 |
| `docs/JOURNAL.md` | **施工日志**：时间线、决策、踩坑、验收记录 |
| `tasks/` | 派给各 AI agent 的任务书原文 |
| `evidence/` | 证据链：实机截图、与 Trae 的对话记录与截图、核验材料 |
| `tools/` | 自检与取证：`check_scenes2.py`、`trae_vibe.py`、`make_source_zip.py` |
| `dist/` | 交付包（源码 zip） |

## 五、内容与验收

- 每条科普说法都要求**可溯源**（档案库条目带来源链接，见 `research/`）。
- 不自造"更好的人"叙事：残障角色是使用者、是同事、是验收人，不是被拯救对象。
- 自检：`python tools/check_scenes2.py` 必须全绿（0 缺场景 / 0 悬空引用 / 4 结局可达）。
- 无障碍：语义化 HTML、键盘可完成全流程、可见焦点、对比度达标、尊重 `prefers-reduced-motion`。

## 六、这个 demo 是怎么做出来的

统筹（Hermes）负责设计、冻结接口、写任务书、派活与**独立验收**；
工人池：Codex CLI、Trae SOLO、分区 agent 分身。
AI 对话与关键步骤截图在 `evidence/trae_steps/`，完整施工时间线在 `docs/JOURNAL.md`。

赛题：Trae 黑客松 · 90 分钟垂直切片 · 提交口径「网页 demo 能玩就行」。
