---
name: writer
description: |-
  Use when: writing web novels or managing a webnovel project. Unified toolkit for /writer, /story, /novel, /webnovel, 写书, 网文, 开书, 续写, 日更, 扫榜, 拆文, 黄金三章, 大纲, 章纲, 审查, 质检, 去AI味, 导入小说, 查询设定, 伏笔, 封面生成. Routes old story-*, webnovel-*, novel-pipeline, and moke-style requests into one workflow.
---

# Writer：统一网文写作工具箱

你是网文写作的**全流程执行引擎**。融合 story-*、webnovel-*、novel-pipeline、Moke 四套系统的长处，用一个入口完成扫榜、拆文、初始化、大纲、写章、审查、质检、查询、记忆和封面。

核心目标：**少问、准路由、可落地、不断档**。用户给出明确动作时直接执行；信息不足且会阻塞下一步时才追问。

---

## 单一事实来源与目录兼容

优先识别现有项目结构，避免强制迁移旧项目。

**新项目创建时，目录名全部使用英文。** 旧项目的中文目录（设定/大纲/正文/追踪）提供读取兼容，但不应用于新项目。

### 现有中文结构（优先兼容，只读不写）

```
{project}/
├── project-state.json        # 旧 story/webnovel 状态
├── README.md
├── 设定/
├── 大纲/
├── 正文/
├── 追踪/
└── runtime/
```

### Writer 新结构（新项目默认）

```
{project}/
├── writer.json              # Project config / state
├── setting/
│   ├── story_bible.md        # Worldview/setting bible
│   ├── characters.md         # Character cards / relationship matrix
│   ├── power_system.md       # Levels / realms / abilities
│   └── factions.md           # Factions / sects / camps
├── outline/
│   ├── master_outline.md     # Core conflict / ending
│   ├── volume_outline.md     # Volume beats / timeline
│   └── chapter_outline/      # Per-chapter detailed outline
│       ├── ch_001.md
│       └── ...
├── chapters/
│   ├── ch_001.md
│   └── ...
├── tracking/
│   ├── current_state.md      # Character positions / states
│   ├── hooks.md              # Pending foreshadowing
│   ├── chapter_summaries.md  # Chapter summaries
│   ├── subplot_board.md      # Subplot progress
│   ├── emotional_arcs.md     # Emotion arcs
│   └── resource_ledger.md    # Power / resource ledger
├── .writer/
│   ├── state.json            # System state
│   ├── project_memory.json   # Writing patterns memory
│   └── runtime/              # Runtime files
├── analysis_lib/             # Benchmark analysis data
│   └── {ref_book}/
├── reference/                # Current project reference view
│   └── {ref_book}/
└── cover/                    # Cover image output dir
```

### 路径解析规则

| 语义 | 优先路径 | 兼容路径 |
|------|----------|----------|
| 状态 | `writer.json` | `project-state.json`, `.webnovel/state.json` |
| 设定 | `setting/` | `设定/`, `.story-system/` |
| 大纲 | `outline/` | `大纲/` |
| 正文 | `chapters/` | `正文/` |
| 追踪 | `tracking/` | `追踪/` |
| 运行态 | `.writer/` | `runtime/`, `.webnovel/` |
| 对标库 | `analysis_lib/` | `拆文库/` |
| 封面 | `cover/` | `封面/` |

执行任何读写前先解析项目根：当前目录若包含上述任一状态文件或 `设定/正文/追踪`，即视为项目根；否则在工作区一级目录中寻找最近更新或用户点名的项目。

---

## 路由表

根据用户请求进行意图识别，路由到对应子模块：

| 用户意图 | 关键词示例 | 路由到 |
|---------|-----------|--------|
| **扫榜/市场分析** | 什么火、排行榜、起点排行、番茄排行、扫榜 | `references/scan.md` |
| **拆文/竞品分析** | 拆这本书、分析、黄金三章、深度拆解 | `references/analyze.md` |
| **导入旧稿/旧项目** | 导入小说、反向解析、把我的书导进来、迁移 | `references/project-init.md`（import模式） |
| **开新书/初始化** | 开书、新书、初始化、创建项目 | `references/project-init.md` |
| **大纲/规划** | 大纲、卷纲、章纲、规划、写大纲 | `references/plan.md` |
| **写章节** | 写第N章、续写、日更、写下一章 | `references/write.md` |
| **批量写章** | 批量写、写5章、连续写、write-batch | `references/write.md`（batch模式） |
| **短篇** | 短篇、写个故事、写一篇 | `references/write.md`（short模式） |
| **审查** | 审查、审稿、审计、review | `references/review.md` |
| **去AI味** | 去AI味、太AI了、去味 | `references/quality.md`（deslop） |
| **质检** | 质检、全线检查、完整质检 | `references/quality.md` |
| **查询设定** | 查角色、查伏笔、查设定、什么状态 | `references/memory.md`（query） |
| **学习/记录** | 记住这个写法、记一下、学这个 | `references/memory.md`（learn） |
| **封面** | 封面、生成封面、封面图 | `references/cover.md` |
| **旧命令兼容** | /story-*、/webnovel-*、/novel、moke | 映射到对应 writer reference |
| **帮助** | 帮助、功能、命令 | 列出路由表 |

### 旧系统命令映射

| 旧入口 | Writer 路由 |
|--------|-------------|
| `/story-long-scan`, `/story-short-scan` | `scan.md`，按长/短篇参数分流 |
| `/story-long-analyze`, `/story-short-analyze` | `analyze.md`，按长/短篇参数分流 |
| `/story-long-write`, `/story-short-write` | `project-init.md` / `plan.md` / `write.md`，按阶段分流 |
| `/story-review`, `/webnovel-review` | `review.md` |
| `/story-deslop` | `quality.md` 的 deslop 模式 |
| `/story-cover` | `cover.md` |
| `/story-import` | `project-init.md` 的 import 模式 |
| `/webnovel-init` | `project-init.md` |
| `/webnovel-plan` | `plan.md` |
| `/webnovel-write` | `write.md` |
| `/webnovel-query`, `/webnovel-learn` | `memory.md` |
| `/webnovel-doctor` | `quality.md` 的 doctor/preflight 模式 |
| `/novel-pipeline --full` | `project-init → plan → write` 链式执行 |
| `/novel-pipeline --stage writing` | `write.md` |
| `/novel-pipeline --stage review` | `review.md` / `quality.md` |
| Moke batch/agent 命令 | `write.md` 的 batch/full 管线 |

### 路由流程

1. 分析用户请求，提取意图关键词
2. 解析项目根和目录风格（中文旧结构或 Writer 新结构）
3. 匹配路由表，加载对应 references 文件
4. 如无法匹配，列出 3-5 个最可能选项让用户选择
5. 如匹配到"写章节"但无项目目录，自动转入 project-init；如有旧项目结构，直接兼容读取

---

## 写作工作流

### 完整流程（推荐顺序）

```
1. 扫榜 → 2. 选题决策 → 3. 拆文对标（可选）
   → 4. project-init → 5. plan
   → 6. write（循环） → 7. review → 8. quality（周期性）
```

### 快速流程

```
project-init → plan → write --batch 3
```

### 质检工单（周期性执行）

```
quality（禁令扫描 → review → deslop → 段落修复）
```

---

## 项目状态感知

每次会话启动时（检测到用户意图为写作相关时），自动执行：

1. **解析项目根**：检测 writer.json / project-state.json / 设定/ 或 setting/
2. **读取当前状态**：stage、chapters_done、current_chapter
3. **检测缺口**（以下项仅在发现问题时提示）：
   - 正文多但设定少（>10章但<3个设定文件 → 建议补充设定）
   - 部署完整性检查（.writer/ 结构是否完整）
   - 拆文库/ 有未完成的 _progress.md → 提示继续拆解
   - 追踪/ 文件是否存在
4. **无信息时完全静默**，不输出无意义的占位内容

### 基于状态的动作建议

- **无项目目录**（不存在包含 `设定/` 和 `正文/` 的目录，也非 setting/ + chapters/）：
  - 用户想写作 → 提示先运行 project-init
  - 用户想扫榜/拆文 → 直接路由
- **已有项目**：
  - 从 `writer.json` 读取 stage/chapters_done 等状态
  - 基于当前 stage 提供上下文感知的建议
  - 写章时自动检查上一章进度

---

## 执行策略

| 操作类型 | 执行方式 |
|---------|---------|
| 扫榜/拆文 | 主会话直接执行（web_search + web_extract + 推理） |
| 项目初始化 | 主会话交互；只问阻塞项；用 `clarify` 收集结构化答案 |
| 大纲规划 | 主会话执行（文件读写） |
| 写章（单章） | 默认执行 5 步日更管线；`--full` 时展开 9 步管线 |
| 写章（批量） | 优先 delegate_task spawn 子Agent；不可用时主会话逐章串行执行 |
| 审查（solo） | 主会话执行规则检查 |
| 审查（full） | 优先 delegate_task spawn 多个审查Agent（模板见 `agents/` 目录）；不可用时降级 solo 并说明 |
| 去AI味 | 主会话执行（文本改写） |
| 质检工单 | 串行执行各质检步骤 |
| 查询 | 主会话执行（文件搜索） |
| 学习 | 主会话追加 memory |
| 封面 | 优先调用 image_generate；无图像工具时产出可执行封面提示词和封面规格文件 |

### 当前环境工具适配

旧文档中的工具名按以下方式替换：

| 旧工具名 | 当前执行方式 |
|----------|--------------|
| `clarify`, `AskUserQuestion` | `clarify`（Hermes 标准工具） |
| `delegate_task`, `Agent` | `delegate_task`，指定可用 agent；无合适 agent 则主会话执行 |
| `web_search`, `web_extract` | `web_search` / `web_extract`、浏览器工具，或要求用户提供来源文本 |
| `Read/Write/Edit/Grep/Bash` | `read_file`、`write_file`、`patch`、`search_files`、`terminal` 等 Hermes 工具 |
| `image_generate` | 使用 `image_generate`；若当前会话无图像生成工具，输出提示词与落盘说明，不伪造图片 |

---

## 设计演进记录（变更日志）

### 已确认决策

| 日期 | 决策 | 影响 |
|------|------|------|
| 2026-06-17 | 新项目目录默认英文，旧项目中文目录优先兼容 | setting/outline/chapters/tracking/analysis_lib/reference/cover 与 设定/大纲/正文/追踪 并存适配 |
| 2026-06-17 | 长短篇合并，`--short` 参数分流 | write.md 统一入口 |
| 2026-06-17 | 旧系统联结从 Hermes 断开，保留原始文件 | story-*/webnovel-* 的目录联结已移除，原始文件仍在 ~/.claude/skills/；novel-pipeline 移入 ~/.claude/skills/；Moke 保留在 ~/.agents/skills/moke/ |

### 待确认决策

| 议题 | 状态 | 说明 |
|------|------|------|
| 默认管线粒度为 5 步还是 9 步 | 已收敛 | 默认 5 步，`--full` 才展开 9 步 |
| 子 Agent spawn 实现 | 已适配 | 当前环境使用 `delegate_task`；不可用时主会话降级 |

---

## 写作约束（硬性规则）

### 硬性禁令（质检环节必检，最高优先级）

1. **破折号清零**：正文中不得出现「——」（用作强调的破折号对）。允许出现在角色对话中表示被打断的「——」（单个在半角水平），但必须在 review 阶段标注。
2. **「不是…而是…」句式禁用**：不得用否定→肯定结构推动论点，直接陈述。
3. **元叙事标签禁用**：「正如前文所述」「正如我们所知」「这个场景……」「这一幕……」等跳出故事的解释性插入语。
4. **分析术语禁用**：「内心挣扎」「表面……实则……」等分析性描述。
5. **段落按句号断段**：在「。」处换行，一句一段。对话独立成段。标题与正文间空一行。
6. **每章≥2000汉字**：低于此数的章节视为不合格。

### 默认写章管线

默认采用 5 步，降低日更摩擦：

1. Plan：确认本章目标、情绪、钩子、禁区
2. Architect：生成章节结构，并内联完成上下文编排
3. Write + Reflect：写正文并提取事实变更
4. Audit + Normalize：审查硬禁令、AI 痕迹、字数和一致性
5. Revise：只修 blocking 和用户关心的问题

`--full` 时展开 Moke 9 步；`--fast` 时只执行 Plan → Write → Audit → Revise。

### AI 痕迹检测阈值

| 指标 | 阈值 |
|------|------|
| 段落等长变异系数 | < 0.15 warning |
| 模糊词密度（似乎/可能/或许） | > 3次/千字 warning |
| 转折词重复（然而/不过/与此同时） | ≥ 3次 warning |
| 连续相同开头句式 | ≥ 3句 info |
| 套话密度 | 按 moke 37 维规则 |

---

## 状态文件格式

### writer.json

```json
{
  "project": "书名",
  "author": "作者",
  "stage": "planning|writing|reviewing|completed",
  "genre": "xuanhuan|urban|xianxia|horror|other",
  "platform": "fanqie|feilu|qidian|zhihu|other",
  "chapters_total": 100,
  "chapters_done": 0,
  "words_per_chapter": 3000,
  "current_volume": 1,
  "last_action": "scan|analyze|init|plan|write|review|quality|learn",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

### project-state.json 兼容

如项目只有 `project-state.json`，不要强制创建 `writer.json`；先读取并映射字段。只有在用户要求迁移或新建 Writer 项目时，才补写 `writer.json`。

---

## 子模块索引

| 引用文件 | 功能 | 来源 |
|---------|------|------|
| `references/scan.md` | 跨平台扫榜 + 趋势分析 | story-long-scan |
| `references/analyze.md` | 爆款拆解 + 黄金三章 | story-long-analyze |
| `references/project-init.md` | 深度交互式项目初始化 | webnovel-init + moke |
| `references/plan.md` | 总纲→卷纲→章纲 | webnovel-plan |
| `references/write.md` | 写作管线（长/短/批） | moke + story + webnovel |
| `references/review.md` | 统一审查（43维） | moke + story + webnovel + novelize |
| `references/quality.md` | 质检工单（去AI味+禁令） | story-deslop + 硬规则 |
| `references/memory.md` | 记忆/查询/学习 | webnovel-learn + query |
| `references/cover.md` | 封面生成 | story-cover |
| `references/state-format.md` | writer.json schema + 读写方法 | writer skill |
| `references/integration-notes.md` | 集成记录 | 设计决策 + 来源说明 |

加载子模块语法：阅读对应的 references 文件后，按照其中的流程执行。若 reference 与本入口冲突，以本入口的工具适配、目录兼容和默认 5 步管线为准。
