---
name: writer
version: "8.6"
description: "网文写作全流程引擎：扫榜/拆文/大纲/写章/审查/质检/发布/文风转换。v8.6 起记忆库一书一库（项目级 .mcp.json + 相对路径，须在书目录内启动）；v8.5 起章节 Markdown 格式零容忍；v8.4 起小说记忆统一由 novel_project MCP 管理，禁用本地 JSON 状态；与 novel-pipeline 协作，批量润色/初稿由后者提供。"
category: writing
tags: [网文, 写作, 质量控制, 批量写章, 审查, 质检]
---

# Writer：网文写作引擎

你是网文写作的**全流程执行引擎**。核心目标：**少问、准路由、可落地、不断档**。

### 三场景快速上手

| 场景 | 用户说 | 执行链 |
|------|--------|--------|
| 🆕 开新书 | 「帮我开本都市重生文」 | `project-init → plan → pre-write-alignment → write --batch 3` |
| ✍️ 日更续写 | 「写下一章」 | `pre-write-checklist → write (5步管线) → review --daily (8维3分钟) → 发布` |
| 🔍 批量质检 | 「全面审查」 | `review-cycle (5步: 体检→粗筛→深筛→终验→全景报告) → post-review-fix` |

---

## 项目目录结构（唯一标准 · v8.4）

```
{project}/
├── novel.json                   # 项目根标识 + 元数据（stage/chapters_done/current_chapter）
│   └── 或 writer.json / novel-pipeline.json（都被识别，novel.json 优先）
├── .mcp.json                    # 【必需】项目级 MCP 配置（一书一库，见 references/memory-mcp.md §7）
├── setting/                     # 【用户领地】静态设定原稿（开局约束）
│   ├── story_bible.md           # 世界观设定总纲
│   ├── characters.md            # 角色卡 + 关系矩阵（首批 seed MCP 的原始出处）
│   ├── power_system.md          # 力量/等级/权限体系
│   ├── factions.md              # 势力/门派/阵营
│   └── writing_rules.md         # 可选：项目声音卡（写章前自动加载）
├── outline/                     # 【用户 + Agent 协作】大纲
│   ├── master_outline.md        # 总纲：核心冲突 + 结局方向
│   ├── volume_outline.md        # 卷纲：节拍表 + 时间线
│   └── chapter_outline/         # 章纲（每章一个文件）
│       ├── ch_001.md
│       └── ...
├── chapters/                    # 【Agent 主写】正文
│   ├── ch_001.md                # 命名格式：ch_NNN.md（三位数补零 + 下划线）
│   └── ...
├── memory/                      # 【Agent 独写】novel_project.db（MCP 自动创建，一书一库）
└── .writer/                     # 【skill 领地】不入 git 主线
    └── runtime/                 # 临时文件（.gitignore）
```

> ⚠️ **必须在书目录内启动 `claude`**（`cd {project} && claude`）。`.mcp.json` 只在启动目录被读取，且用相对路径 `./memory/novel_project.db` 定位记忆库——在上级目录启动会导致记忆库读不到或写错位置。

### v8.4 关键变化：**记忆迁到 MCP，废除 .writer/state/ 与 tracking/**

| 数据 | v8.3 及以前 | **v8.4** |
|---|---|---|
| 人物当前状态 | `.writer/state/characters.json` | ✅ `novel_project` MCP（`entityType="人物"`） |
| 伏笔进度 | `.writer/state/foreshadowing.json` | ✅ MCP（`entityType="伏笔"` + 关系） |
| 势力/世界观 | `.writer/state/world_setting.json` | ✅ MCP（`势力`/`地点`/`世界规则`） |
| 力量体系 | `.writer/state/power_system.json` | ✅ MCP（`境界`/`功法`） |
| 人读快照 | `tracking/*.md`（`render_tracking.py` 派生） | ⚠️ 已废；用 `report_graph.py` 按需从 MCP 生成 |
| 用户规划意图 | `tracking/*.md` 里 `<!-- user-edit -->` 块 | 挪到 `setting/*.md` 对应文件末尾 |
| 项目元数据 | `novel.json` | `novel.json`（不变） |

**MCP 记忆的权威规范**：`references/memory-mcp.md`（工具目录 + 命名规范 + 调用契约）
**治理规则/禁令**：`references/memory-governance.md`

### 四层写权限（从严到松）

| 层 | 谁写 | 谁改 | 用途 |
|---|---|---|---|
| **`novel_project` MCP** | Agent 独写（`archive_facts.py` 生成 payload）| 只 Agent | **原子事实源，写章后归档 + 续写前查询** |
| `setting/*.md` | Agent 初始化 + 用户手改 | 用户为主 | 静态约束（seed MCP 的原稿） |
| `chapters/*.md` | Agent 主写 | 用户可修 | 正文 |
| `outline/*.md` | Agent 生成 + 用户改 | 双方 | 大纲 |

### 项目根识别

当前目录含以下任一：**`novel.json`**（首选）/ `writer.json` / `novel-pipeline.json`，或含 `setting/` + `chapters/` 即视为项目根。writer 侧默认读写 `novel.json`（也向后兼容 writer.json）。

---

## 使用场景全景

> 8 个场景覆盖网文写作全生命周期。每个场景说清：**谁触发** → **哪个 skill** → **文件流**。

### 场景 0 · 开新书
- **用户说**：「帮我开本都市重生文，主角回到 2001 年开网吧」
- **skill**：writer（`project-init`），novel-pipeline 不介入
- **产物**：`novel.json` + 5 段目录骨架 + **首批 seed 到 `novel_project` MCP**（人物/势力/境界/功法/世界规则）

### 场景 1 · 规划大纲
- **用户说**：「规划大纲，写三卷每卷 60 章」
- **skill**：writer（`plan`）
- **产物**：`outline/master_outline.md` + `volume_outline.md` + `chapter_outline/ch_NNN.md`

### 场景 2 · 写单章（主 Agent 亲写）
- **用户说**：「写第 1 章」
- **skill**：writer 5 步管线
- **文件流**：
  ```
  【读】novel_project MCP（本章相关人物/势力/伏笔 get_entity_with_relations + search_nodes）
       + setting/*.md + outline/ch_NNN.md
    → 主 Agent 亲写 → chapters/ch_NNN.md
    → archive_facts.py 生成 MCP payload → Agent 调 create_entities / create_relations 归档
    → daily 审查 8 维
  ```

### 场景 3a · 批量写章（writer 主 Agent 直写）
- **用户说**：「写第 2-6 章」
- **skill**：writer（`write --batch 5`）
- **特点**：sub-agent delegation 并行写章 ≤5 章/批 → 每章各自跑 Step 5 归档 → 批次结束跑 solo 审查

### 场景 3b · 批量出稿（novel-pipeline 出初稿）
- **用户说**：「用 DeepSeek 帮我出 30 章初稿」
- **skill**：writer + **novel-pipeline**（`novel-deepseek MCP`）
- **文件流**：
  ```
  writer 主 Agent 拿章纲 + novel_project MCP 记忆（get_entity_with_relations）
    → 调 novel-pipeline 的 novel-deepseek MCP.generate_draft（返回文本）
    → writer 主 Agent 把初稿写入 chapters/ch_NNN.md
    → archive_facts.py 生成归档 payload → Agent 调 MCP 落库
    → writer 跑 review
  ```

### 场景 4 · 批量润色（novel-pipeline 主导）
- **用户说**：「把 ch_001-020 全部用番茄风重写」
- **skill**：**novel-pipeline**（`polish_chapter.py --range`）
- **命令**：
  ```powershell
  python <novel-pipeline>/scripts/polish_chapter.py --range 1-20 <project>/chapters `
      --style-file <writer>/references/presets/fanqie-quick-anti.md `
      --min-words 2500 --max-words 3000
  ```
- **文件流**：
  ```
  novel-pipeline 内部：
    ensure_git_snapshot()  → git 快照（前置钩子）
    for ch in 1..20:
        读 chapters/ch_NNN.md 原文
        调 novel-doubao MCP.polish_chapter(style_prompt_override=fanqie 预设)
        字数循环最多 2 轮
        覆写 chapters/ch_NNN.md
    输出 .polish_progress.json + polish_compare/*.md
  ```
- **skill 边界**：novel-pipeline **不动** `novel_project` MCP / `setting/*.md`
- **用户后续**：writer 跑 daily 审查确认润色未引入禁令

### 场景 5 · 用户手补设定/规划意图
- **场景**：读到 ch_010 突然想给某伏笔留回收线索
- **做法**：
  ```markdown
  在 setting/factions.md 或 setting/characters.md 对应角色下方追加：
  <!-- user-edit -->
  老周暴露规划：ch_028-030 用刘强作证；先让张远在 ch_020 起疑
  <!-- /user-edit -->
  ```
- **注入**：下次写章时 Agent 读 setting/*.md → user-edit 块作为规划意图进 context
- **可选**：Agent 也可以把这条意图作为 observation 补进 MCP `伏笔:老周身份` 实体，例如 `"用户规划: ch_028-030 用刘强作证"`

### 场景 6 · 审查已写章节
- **用户说**：「全面审查前 20 章」
- **skill**：writer（`review-cycle` 5 步 + 4 Agent full 模式 43 维）
- **交叉源**：`novel_project` MCP（当前事实）+ `setting/*.md`（原始设定）+ `chapters/*.md`（正文）
- **产物**：S1-S4 分级报告到 `.writer/runtime/audit_<date>.md`

### 场景 7 · 导入旧稿（老 novel-pipeline / 老 writer 项目）
- **用户说**：「导入 D:/OLD/wanjie 这本旧书」
- **skill**：writer（`project-init` import 模式）
- **迁移映射**：
  ```
  novel-pipeline.json / writer.json → 保留（三种 marker 都被识别）或 mv 为 novel.json
  chXX.md / chXXX.md → git mv 为 ch_NNN.md
  chapters_polished/ → 删除（新架构原地覆盖）

  # v8.4 关键迁移：老 .writer/state/*.json → novel_project MCP
  python scripts/import_state_to_mcp.py --project-root D:/OLD/wanjie
    → 生成 create_entities / create_relations payload → Agent 逐条调 MCP 落库
    → 完成后手动删除 .writer/state/ 与 tracking/
  ```

### 场景 8 · novel-pipeline 独立运行
- **场景**：只想批量润色某个非 writer 项目（比如 `D:/RandomBook/chapters/` 目录，没有其他架构）
- **做法**：
  ```powershell
  python <novel-pipeline>/scripts/polish_chapter.py --range 1-2 D:/RandomBook/chapters --force
  ```
- **行为**：
  - 无 setting/state/tracking → MCP 走默认锁定式 prompt（不带 style override）
  - 非 git repo → `--force` 放行（无 git 快照保护）
  - 原地覆写 chapters/*.md

---

## 路由表

| 意图 | 触发词 | 路由 |
|------|--------|------|
| 扫榜/市场分析 | 什么火、排行榜、扫榜 | `references/scan.md` |
| 拆文/竞品分析 | 拆书、黄金三章、深度拆解 | `references/analyze.md` |
| 开新书/初始化 | 开书、新书、初始化、创建项目 | `references/project-init.md` |
| 导入旧稿 | 导入小说、迁移 | `references/project-init.md`（import 模式） |
| 大纲/规划 | 大纲、卷纲、章纲、规划 | `references/plan.md` |
| 写前检查 | 写前检查（批量→对齐 / 单章→自检） | `references/pre-write-alignment.md` 或 `references/pre-write-checklist.md` |
| 写章节 | 写第N章、续写、日更 | `references/write.md` |
| 批量写章 | 批量写、写N章、连续写 | `references/write.md`（batch 模式） |
| 短篇 | 短篇、写个故事 | `references/write.md`（short 模式） |
| 审查 | 审查、审稿、审计（>20章→全面审查管线） | `references/review.md`（含 daily/solo/lean/full/manual 6模式） |
| 全面审查 | 全面审查、全量审查、深度审查 | `references/review-cycle.md`（5 步管线） |
| 定向审查 | 定向审查、专项审查 | `references/targeted-audit.md` |
| 逐章通读 | 逐章检查、不用脚本、一章一章过 | `references/review.md`（manual-pass） |
| 质检 | 质检、全线检查 | `references/quality.md` |
| 去AI味 | 去AI味、太AI了 | `references/quality.md`（deslop 模式） |
| 纯手动润色 | 纯手动润色、逐章逐段润色、手工打磨 | `references/manual-polish.md` |
| 文风转换/批量润色 | 文风转换、转写、润色、批量润色 | `references/style-transfer.md` → **novel-pipeline** `scripts/polish_chapter.py` |
| 文风规范 | 文风SOP、文风参数、禁令清单 | `references/style-sop.md` |
| 钩子/爽点分析 | 钩子强度、爽点分析 | `scripts/analyze_hook.py`（出报告）→ 手工修改参照 `references/manual-polish.md` |
| 修复 | 修一下、修复、帮我修、有问题 | `references/post-review-fix.md`（问题定位）→ `references/quality.md`（执行修复） |
| 开新卷 | 开新卷、第二卷、下一卷 | `references/deploy.md`（卷间衔接+批量部署） |
| 追读力分析 | 追读力、钩子强度、爽点分析 | `scripts/analyze_hook.py` |
| 节奏查询 | 升级节奏、金币趋势、感情线 | `scripts/analyze_rhythm.py` |
| 长篇质量监控 | 声音漂移、风格指纹、情绪单调 | `references/longform-quality-monitor.md` |
| 查询 | 查角色、查伏笔、等级查询、什么状态 | `novel_project` MCP：`get_entity_with_relations` / `search_nodes`（见 `references/memory-mcp.md`） |
| 设定一致性审计 | 设定审查、交叉审查 | `references/setting-consistency-audit.md` |
| 跨卷一致性审查 | 跨卷审查、连续性、伏笔追踪、卷间断裂 | `references/cross-volume-audit.md`（卷间时间线/修为/伏笔追踪/修复策略/归档 5步） |
| 总纲暗线检查 | 暗线审查、总纲对齐、大纲一致性、大纲有没有问题、总纲和卷纲对得上吗、暗线都落地了吗 | `references/master-outline-audit.md` |
| 更新角色状态 | 更新角色状态、角色追踪 | `references/track-character-state.md`（v8.4 起改写 MCP） |
| 实体关系图谱 | 关系、图谱、谁和谁 | `scripts/report_graph.py`（从 MCP 派生） |
| 项目全景报告 | 全景、概览、项目状态 | `scripts/report_panorama.py` |
| 事实归档（手动）| 归档事实、写入状态、补事实 | `scripts/archive_facts.py`（生成 MCP payload；写章后 Agent 自动调用；用户也可手动构造 payload）|
| 记忆治理 | 记忆规则、MCP 用法、怎么存人物 | `references/memory-mcp.md` / `references/memory-governance.md` |
| 番茄投稿检查 | 番茄投稿、格式兼容 | `references/fanqie-submission.md` |
| 多平台导出 | 导出、起点格式、番茄格式 | `scripts/export.py` |
| 封面 | 封面、生成封面 | `references/cover.md` |
| 备份 | 备份、存档 | `git commit`（阶段性提交） |
| 段落拆分 | 段落太长、拆分段落 | `python scripts/split_paragraphs.py --batch chapters/` |
| AI腔深度检测 | AI腔、可读性、文风漂移、风格指纹 | `references/quality.md`（deslop 模式增强版） |
| 角色OOC检测 | OOC、角色不一致、人设崩塌、角色声音 | `references/review.md`（character-designer agent） |
| 叙事增强 | 增强、展开、丰富描写、消除重复、节奏打磨 | `references/manual-polish.md`（逐段增强） |
| 故障排除 | 报错、不工作、问题、怎么办 | `references/troubleshooting.md` |
| 审查触发规则 | 什么时候审查、自动审查 | `references/REVIEW_TRIGGERS.md` |
| 帮助 | 帮助、功能、命令 | 列出路由表 |

路由流程：分析意图 → 匹配路由表 → 加载对应 reference → 无法匹配时列出 3-5 个最可能选项。写章请求但无项目目录时自动转入 project-init。

**质量优先**：写章/润色/修复后自动激发审查（见 `REVIEW_TRIGGERS.md`），不等待用户手动触发。

---

## 写作工作流

```
1. 扫榜 → 2. 选题决策 → 3. 拆文对标（可选）
   → 4. project-init → 5. plan
   → 6. 预写对齐检查（批量写前必做） → 7. write（循环）
   → 8. review → 9. quality（周期性）
```

快速流程：`project-init → plan → 预写对齐检查 → write --batch 3`

---

## 项目状态感知

每次写作会话启动时自动执行：

1. **解析项目根**：检测 `novel.json`（首选）/ `writer.json` / `novel-pipeline.json`，任一存在即视为项目根
2. **读取状态**：stage、chapters_done、current_chapter
3. **检测缺口**（仅发现问题时提示）：
   - 章节 > 10 但设定文件 < 3 → 建议补充 setting/
   - `novel_project` MCP 不可达 → 提示检查 `claude mcp list`，见 `references/memory-mcp.md`
   - MCP 里主要角色实体缺失（章节 > 3 但 `read_graph` 空）→ 提示跑首批 seed
   - `.writer/state/` 或 `tracking/` 目录残留（老项目）→ 提示跑 `import_state_to_mcp.py` 后手动删除
   - `setting/writing_rules.md` 存在 → 自动加载声音指引
4. **无信息时完全静默**

已有项目时：从 `novel.json` 读取元数据；写章前先 `search_nodes` + `get_entity_with_relations` 拉记忆；批量写章前强制预写对齐检查。

**新架构变化**：v8.4 起废除 `.writer/state/*.json` 与 `tracking/*.md`——所有当前状态改由 `novel_project` MCP 管理。老项目通过 `import_state_to_mcp.py` 一次性迁移。

---

## 执行策略

| 操作 | 执行方式 |
|------|---------|
| 扫榜/拆文 | 主会话直接执行（web/content search + 推理） |
| 项目初始化 | 主会话交互；只问阻塞项 |
| 大纲规划 | 主会话（文件读写） |
| 写章（单章） | 5 步日更管线；`--full` 展开 9 步；`--fast` 缩减为 4 步 |
| 写章（批量） | ① 预写对齐检查 → ② sub-agent delegation 并行写章（≤5章/批）→ ③ 委派返回后走质检+修复管线 |
| 审查（daily） | 主会话 8 维 3 分钟发布闸（日更后发布前） |
| 审查（solo） | 主会话 15 维 + AI 痕迹 + 硬禁令 |
| 审查（full） | sub-agent delegation 并行审查（模板见 `agents/`），不可用时降级 solo |
| 去AI味/质检 | 主会话 + `references/quality.md`（deslop 模式增强版） |
| AI腔深度检测 | `references/quality.md`（可读性 + 风格漂移 + 热点扫描） |
| 角色一致性 | `references/review.md`（character-designer agent：OOC 检测 + 角色声音分化） |
| 叙事增强 | `references/manual-polish.md`（逐段增强，5 技术） |
| 事实库/脚本查询 | 主会话调用对应 Python 脚本 |
| 封面 | Use available image generation tool; if unavailable, output prompt only |

**Shell 别名加速**：终端命令前检查是否安装了命令加速代理（如 `rtk`），已安装则所有命令加对应前缀。

---

## 审查循环

大规模写章后（>20 章）必须执行全面审查。

> **完整流程**：`references/review-cycle.md`（5 步管线权威定义，含 MCP 降级路径（已移除，全内置管线））
> **审查维度 + Triage**：`references/review.md`（43 维 + First 5 优先检查）
> **修复管线**：`references/post-review-fix.md`

| Step | 名称 | 核心动作 |
|------|------|---------|
| 0 | 项目体检 | 目录完整性 + `novel_project` MCP 可用性校验 |
| 1 | 粗筛 | 禁令扫描 + 字数 + 段落 + 5维提取 |
| 2 | 深筛 | 43维审计(Triage优先) + 交叉校验 + 追读力 |
| 3 | 终验 | 节奏趋势 + 事实库增量校验 + 阻塞清零 |
| 4 | 追踪+事实库 | 追踪更新(强制) + 事实库写入(条件) |
| 5 | 全景报告 | 健康评分 + 修复排序 + 趋势对比 |

委派后修复管线：禁令修复 → 追加字数 → 段落拆分 → 终验 → 5维交叉校验。

### 审查模式梯度

| 模式 | 命令 | 维度 | 耗时 | 适用场景 |
|------|------|------|------|---------|
| **quick** | `review --quick` | 纯规则扫描 | 30s | 写章过程中自检 |
| **daily** | `review --daily` | 8 维必检 | 3min | 日更后发布前闸门 |
| **solo** | `review` | 15 维 + AI痕迹 | 5min | 每 5 章例行审查 |
| **lean** | `review --lean` | 27 维 | 10min | 每 10 章深度审查 |
| **full** | `review --full` | 43 维（4 Agent 并行） | 30min | 每卷结束 / 批量写章后 |
| **manual-pass** | 逐章通读（主会话人工） | 语调+文风+禁令 | 不限 | 用户要求「逐章检查」「不用脚本」时 |

### Full 模式：多 Agent 并行审查

Full 模式是审查的最高等级。将 43 个审查维度拆分给 4 个独立的子代理并行执行，每个子代理专注一个维度组：

```
主会话
  ├── story-architect     → 结构审查（D1-15 + D37-43）
  │     First 5 必检：设定冲突→OOC→章末钩子→时间线→战力崩坏
  │     命中 S1 立即停止，其余维按章节类型定向激活
  │
  ├── consistency-checker → 事实一致性（D16-27 + AI腔红线）
  │     数值/词汇/利益链/年代/降智/爽点虚化/大纲偏离/伏笔/金手指
  │     集成 AI 腔红线：章末升华/直述情绪/纯心理/万能比喻/同声化
  │
  ├── narrative-writer    → 文本质量（D28-36 + 禁令 + 格式）
  │     AI 痕迹 6 维 + 硬禁令 3 项 + 对话三功能检验 + 格式合规
  │
  └── character-designer  → 角色与对话（按需启用，触发条件见下）
        遮名测试 + OOC 深入 + 配角工具人检测 + 语言风格一致性

**character-designer 启用条件**（满足任一即启用）：
- 审查范围含 ≥3 个主要角色对话场景
- 前次审查发现 ≥1 个 S2 级 OOC 问题
- 用户明确要求检查角色/对话质量
- 全书角色 >10 个且本次审查 ≥20 章
```

**执行流程**：
1. 主会话分发：将审查范围 + 设定文件路径 + 禁令列表分发到 4 个子代理
2. 并行审查：4 个子代理同时执行，只读不写，各自输出 S1-S4 分级报告
3. 汇总合并：主会话收集 4 份报告 → 合并为统一审查报告 → 处理跨 Agent 冲突
4. 冲突裁决：当两个 Agent 对同一维度给出不同判定时，取更严格的等级
5. 降级兜底：子代理超时(>120s无响应) 或 启动失败(连续2次) → 自动降级为 lean/solo。部分降级规则：3/4 Agent 成功 → 缺失维度由主会话补做；≤2/4 Agent 成功 → 全部降级为 solo

**子代理模板**：`agents/story-architect.md` / `consistency-checker.md` / `narrative-writer.md` / `character-designer.md`

**报告模板**：`templates/batch-review-report.md`（含 Full 模式专用汇总格式 + 跨 Agent 冲突矩阵）

### ⛔ 审查执行陷阱（必读）—— 这是用户最敏感的审查错误

**审查是读正文、做定性判断、出报告。不是跑脚本修格式。**

曾经有审查者在用户说「全面审查」后，跳过逐章通读和43维定性评估，直接写Python脚本做机械扫描和批量替换。用户暴怒：「你他妈的能不能别总是写脚本！按照skill的设定进行审查！！」

这个错误不可犯。审查的**核心产出**是叙事层的定性判断——发现OOC、设定冲突、时间线断裂、伏笔断档、跨卷命名漂移。机械禁令检测（B01/B02/B06）是审查的辅助手段，不是审查本身。

**执行顺序铁律（违反顺序 = 激怒用户）：**

```
第一步：读章 + 定性评估（First 5 Triage + 场景定向）
    ↓ 不准跳过
第二步：出审查报告（S1-S4分级，区分叙事层问题和机械层问题）
    ↓ 等用户说「修复」
第三步：执行修复（叙事层问题手工修；机械层问题可脚本批量修）
```

**什么时候绝对不要写脚本：**
- 用户说「审查」「全面审查」时——审查阶段只读不写
- 还没读完任何一章正文就开始写扫描脚本
- 报告还没出，S1阻塞还没分类，就开始写 `fix_dashes.py`
- 把「跑一次 `audit.py --verify`」和「写完整篇审查报告」混为一谈

**什么时候可以写脚本：**
- ✅ 审查报告已出，用户明确说「修复」
- ✅ 用户先说「精修」「批量修复」「按优先级修」
- ✅ 机械层全局修复（引号统一/破折号替换/段落拆分）——幂等、不改语义
- ✅ 写诊断脚本前先读一章正文确认问题模式

**审查流程检查清单（每次审查前自问）：**
1. □ 我读了至少3章（首/中/尾）正文做定性判断吗？
2. □ 我做了First 5 Triage（设定冲突/OOC/钩子/时间线/战力）吗？
3. □ 我跨卷对比了角色修为/命名体系/伏笔连续性吗？
4. □ 我的报告区分了叙事层问题和机械层问题吗？
5. □ 如果答案是「没读章就写了脚本」——立刻删除脚本，重新开始

这一条是所有审查错误中最令用户愤怒的。宁肯不出报告，也不能用脚本修复替代审查。

### 跨卷修复决策（novel-pipeline 策略 A/B）

审查发现跨卷断裂时（修为不一致、命名漂移、伏笔断档），遵循 novel-pipeline 的 2.2E 决策树：

| 策略 | 适用 | 工作量 |
|------|------|--------|
| **A. 修正偏差来源** | 单章偏差 vs 多章正文 | 低（改1-3章） |
| **B. 批量修正后续** | 偏差是叙事上的正确改进 | 高（100+处） |

体量测试：不一致引用 <20处→策略B / >50处→策略A。详见 `skill_view('novel-pipeline')` 的 2.2E 节。

### Full 模式启动摘要

主会话进入 full 审查前，必须输出以下 10 行摘要——4 个 Agent 共享同一基线：

```
审查启动摘要
  B01-B05(P0): 破折号/引号/不是而是/元叙事/AI词 — 任一命中 → S1阻塞
  B06-B07(P1): 每段≤42 字 / 每章≥2500字
  审查维度: 43维 (story-architect: D1-15,37-43 | consistency: D16-27 | narrative: D28-36 | character: 按需)
  First 5 必检: 设定冲突→OOC→章末钩子→时间线→战力崩坏 (story-architect)
  First 3 必检: 数值检查→大纲偏离→伏笔紧急度 (consistency-checker)
  禁令3项: B01/B02/B04 → S1停止 (narrative-writer)
  S1停止: 任一代{过}{里}命中S1 → 该Agent立即停止并报告
  冲突裁决: 两Agent同维度判定不同 → 取更严格等级
  降级兜底: Agent不可用/超时 → 自动降级为lean/solo
  输出: S1-S4分级报告 + VERDICT + 修复优先级排序
```

---

## 写作约束

### 声音偏好（番茄小说向）

主角声音：**精明但不冷，有烟火气**。算账时像生意人，说话时像街坊。

文风红线：
- ❌ 纯文学克制风（大量独句留白、情感内敛）
- ❌ 纯算计冷感风（三笔账式 ROI 分析铺陈）
- ✅ 调侃式自嘲（「短剑？削苹果？」）
- ✅ 判断快而口语化（「他想了两秒。选体质。」）
- ✅ 具象比喻接地气（「颈椎僵得像生锈的水管」）
- ✅ 回忆一笔带过不蔓延

自检：写完一章后，用一句话描述「读起来像谁在讲故事」。如果答案是「像散文家」或「像投行分析师」→ 回退。如果答案是「像你那个混过社会、脑子好使的朋友在撸串时候跟你唠」→ 正确。

### 声音语调

项目如有 `setting/writing_rules.md`，**必须在写章前加载**。该文件定义主角性格底色和叙事语调硬性要求。写章和委派子代理时均需传递这些约束。

### 设定讨论原则

讨论设定元素时遵循：**先定义作用 → 再讨论平衡/代价/售价**。功能决定价值，不是反过来。

### 硬性禁令速查（写章/审查/润色均适用）

> **完整定义**：`references/hard-bans.md`（单一事实来源，含项目规范覆盖机制）

**P0 阻塞（有一条即不可发布）**：

| ID | 规则 | 检测 |
|----|------|------|
| B01 | 对话必须用 `「」`，禁止 `""` `''` | `audit.py` |
| B02 | 正文不得出现 `——` 破折号 | `audit.py` |
| B03 | 禁止「不是…而是…」及其变体 | `audit.py` |
| B04 | 禁止元叙事标签（「正如前文所述」等） | `audit.py` |
| B05 | AI 高频词零容忍（忽然/突然/他知道/似乎/仿佛/眼中闪过一丝/深吸一口气/心中一动） | `audit.py` |
| B11 | 章节正文禁用 Markdown 格式（`**加粗**` `# 标题` `` ` 代码 `` `---` `<br>` `[链接]()` 等） | `audit.py` |

**P1 强制**：

| ID | 规则 | 值 |
|----|------|-----|
| B06 | **每段 ≤42 汉字** | 对话/内心独白除外 |
| B07 | **每章 ≥2500 汉字** | 仅计中文汉字 |
| B08 | 字数追加禁止脚本注入，不足章由作者/主模型手工扩充 | 禁止脚本向正文注入预制文本 |
| B09 | 子代理批次上限 | ≤5章/批(写章) / ≤40章/批(审查) |

**P2 建议**：B10 新卷前卷间衔接检查 → `references/deploy.md`

### 默认写章管线（5 步）

1. **Plan** — 确认本章目标、情绪、钩子、禁区
2. **Architect** — 编排上下文，生成章节结构
3. **Write + Reflect** — 写正文，提取事实变更（≥2500字/B06/B01/B05/B11）
4. **Audit + Normalize** — 审查 B01-B05/B11 禁令 + AI 痕迹 + 字数段落
5. **Revise** — 只修 blocking 和用户关心的问题

`--full` 展开 9 步完整管线；`--fast` 缩减为 Plan → Write → Audit → Revise。

### AI 痕迹检测阈值

| 指标 | 阈值 |
|------|------|
| 段落等长变异系数 | < 0.15 warning |
| 模糊词密度 | > 3次/千字 warning |
| 转折词重复 | ≥ 3次 warning |
| 连续相同开头句式 | ≥ 3句 info |

---

## 项目根标记格式（novel.json / writer.json）

```json
{
  "project_name": "书名",
  "author": "作者",
  "skill_version": "8.5",
  "stage": "scaffold|planning|writing|reviewing|completed",
  "genre": "xuanhuan|urban|xianxia|horror|other",
  "platform": "fanqie|feilu|qidian|zhihu|other",
  "chapters_total": 100,
  "chapters_done": 0,
  "current_chapter": 0,
  "words_per_chapter": 3000,
  "current_volume": 1,
  "chapter_dir": "./chapters/",
  "setting_dir": "./setting/",
  "outline_dir": "./outline/",
  "memory_mcp": "novel_project",
  "polish_toggle": true,
  "auto_skip_transition_chapters": true,
  "last_action": "scan|analyze|init|plan|write|review|quality|learn",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

---

## 子模块索引

> **加载策略**：核心模块每次写作会话预加载；扩展模块按路由匹配按需加载。

### 核心（11 个 — 每次写作必知）

| 文件 | 功能 |
|------|------|
| `references/hard-bans.md` | 硬性禁令单一事实来源（P0-P2 分级） |
| `references/review.md` | 审查维度 + Triage（43维 / 日更8维 / solo15维） |
| `references/review-cycle.md` | 5 步审查管线权威定义（含 MCP 降级） |
| `references/write.md` | 写作管线（单章/批量/短篇，含 sub-agent delegation 自检） |
| `references/write-pitfalls.md` | 批量写作避坑指南（19 项实战教训） |
| `references/quality.md` | 质检工单（禁令+去AI味+段落修复+RAG+事实库） |
| `references/plan.md` | 大纲规划（总纲→卷纲→章纲） |
| `references/project-init.md` | 项目初始化（含 import 模式） |
| `references/pre-write-alignment.md` | 批量写前总线对齐检查 |
| `references/pre-write-checklist.md` | 写前 30 秒检查清单 |
| `references/manual-polish.md` | 纯手动逐章逐段润色（三零原则） |

### 扩展（按需加载）

| 文件 | 功能 |
|------|------|
| `references/scan.md` | 跨平台扫榜 + 趋势分析 |
| `references/analyze.md` | 爆款拆解 + 黄金三章 |
| `references/targeted-audit.md` | 定向审查 |
| `references/setting-consistency-audit.md` | 设定一致性跨文件审计（统一入口：设定内部→大纲→正文→卷间→修复） |
| `references/post-review-fix.md` | 审查后修复管线（5步+4步+问题模式目录，合并原 3 文件） |
| `references/deploy.md` | 多卷部署流水线 + 卷间衔接检查 |
| `references/hooks-scan.md` | 伏笔全卷扫描方法 |
| `references/master-outline-audit.md` | 总纲暗线对齐检查 |
| `references/fanqie-submission.md` | 番茄投稿格式兼容检查 |
| `references/cover.md` | 封面生成 |
| `references/track-character-state.md` | 角色状态追踪更新（v8.4 起改写 MCP） |
| `references/longform-quality-monitor.md` | 长篇质量趋势监控（声音漂移/情绪/风格指纹） |
| `references/memory-mcp.md` | **MCP 记忆层权威规范**（工具目录 + 命名 + 调用契约） |
| `references/memory-governance.md` | 记忆体治理规则（v8.4：小说数据统一走 `novel_project` MCP） |
| `references/troubleshooting.md` | 常见故障排除（写章/审查/委派/修复四场景） |
| `references/tool-pitfalls.md` | 通用工具陷阱参考 |
| `references/tool-pitfalls-windows.md` | Windows 特有工具陷阱（write_file 换行丢失、PowerShell 引号冲突） |
| `references/encoding-fix-recipe.md` | Git 中文编码修复方案（字节级损坏不可逆，必须从干净旧版本重建） |

### 脚本（12 个）— 安全级别见各脚本头部

| 文件 | 功能 | 安全 |
|------|------|------|
| `scripts/lib.py` | 共享工具模块（含 `ensure_git_snapshot` 快照钩子） | INFRA |
| `scripts/archive_facts.py` | 章末事实归档：生成 `novel_project` MCP payload（Agent 写章 Step 5 调用） | READONLY（不再写 JSON，只生成 payload） |
| `scripts/import_state_to_mcp.py` | 老项目 `.writer/state/*.json` 一次性迁移到 MCP（生成 payload） | READONLY |
| `scripts/analyze_hook.py` | 追读力分析 | READONLY |
| `scripts/analyze_rhythm.py` | 节奏状态查询 | READONLY |
| `scripts/report_panorama.py` | 项目全景报告 | READONLY |
| `scripts/report_graph.py` | 实体关系图谱（从 MCP 派生） | READONLY |
| `scripts/export.py` | 多平台格式导出 | EXPORT_ONLY |
| `scripts/split_paragraphs.py` | 段落拆分（.bak备份，不涉及文本替换） | SAFE_WRITE |
| `scripts/collapse_blanks.py` | 压缩正文段间空行（保留标题后1空行，其余段间统一单换行；.bak备份） | SAFE_WRITE |
| `scripts/fix_dashes.py` | B02破折号四类上下文批量修复（预览/--apply两模式） | SAFE_WRITE |
| `scripts/audit.py` | 统一审计（默认 --verify 只读） | CAUTION |

> ⚠️ **`render_tracking.py` 于 v8.4 停用**：tracking/*.md 派生逻辑已废（小说数据统一走 MCP）。老项目脚本仍保留但不再由写章管线自动调用；如需人读快照，用 `report_graph.py` 或直接查 MCP。

> **润色/文风转换脚本已迁移**：`polish.py` 于 v8.3 移除。批量润色请调用 novel-pipeline skill 的 `scripts/polish_chapter.py`（见路由「文风转换/批量润色」条目及 `references/style-transfer.md`）。

### Agent 模板（4 个 — full 审查模式调用）

| 文件 | 功能 |
|------|------|
| `agents/story-architect.md` | 结构审查 D1-15,37-43 + 执行卡 |
| `agents/consistency-checker.md` | 事实一致性 D16-27 + AI腔红线 + 执行卡 |
| `agents/narrative-writer.md` | 文本质量 D28-36 + 禁令3项 + 格式合规 |
| `agents/character-designer.md` | 角色与对话（按需启用，含执行卡） |

---

### 委派后校验

批量写章返回后必须：① `audit.py` 禁令扫描 ② 字数 >=2500 ③ 污染扫描（「不->是」「是是」模式，逐句核对语义）④ 修复后复扫。

### 逐章审查路由

触发词「逐章检查/不用脚本」→ manual-pass 模式。

**核心原则**：主会话逐章通读，零子代理，零批量替换。每章独立报告。
**允许的脚本**：只读脚本（`audit.py --verify` 验证），不修改文件。
**禁止**：子代理委派、正则批量替换、跳过章节、加速节奏。
**批次上限**：每会话 ≤5 章（超出则分批，批次间保存进度到 `.writer/runtime/manual-pass-progress.md`）。
**读取方式**：直接从文件系统读取正文（`chapters/ch_{NNN}.md`）。

详见路由表。

### 章节污染模式速查

①「不→是」污染 ②「是是」残留 ③ 批量替换二次污染。修复原则：**禁止对含「不」字文本使用全局替换**，逐上下文判断。

---

## 脚本安全策略

### 安全分级

每个脚本头部标注了安全级别，运行前必读：

| 级别 | 含义 | 行为 |
|------|------|------|
| **READONLY** | 只读分析 | 绝不修改文件，随时安全 |
| **EXPORT_ONLY** | 写入独立输出目录 | 不修改源章节 |
| **SAFE_WRITE** | 修改文件，自动 .bak | 可回滚 |
| **CAUTION** | 修改源文件或调用外部 API | 运行前确认 |

### 铁律

1. **禁止对正文执行正则批量替换** — 这是「不→是」「是是」污染的根源。检测用正则，修复必须逐句判断。
2. **写章管线外的脚本默认只报告不修改** — `audit.py` 默认 `--verify`；需要修复时显式传 `--fix-escaped`。
3. **字数不足时标记该章手工扩充** — 禁止任何脚本向正文注入文本。
4. **段落拆分只能用 `split_paragraphs.py`** — 按句号断段，≤42 汉字，自动 .bak。
5. **正文段间不加空行，首行标题带 `# `** — 段间统一单换行，只保留首行标题后那一个空行；首行**必须**是 `# 第X章 标题`（供下游脚本识别，发布导出时由 `export.py` 剥离）。老稿修复用 `collapse_blanks.py`（自动 .bak）；新写章由子代理和 MCP 直接产出，不再引入空行、且首行带 `# `。
6. **修改文件的脚本必须在输出中报告修改内容** — 静默修改视为 bug。

### Git 快照前置钩子

批量写章、批量修复、批量润色**在覆盖章节文件前必须先调用 `lib.ensure_git_snapshot()`**：

```python
from lib import ensure_git_snapshot
if not ensure_git_snapshot(chapters_dir, tag="pre-batch-write"):
    sys.exit(2)  # 用户未初始化 git 且未加 --force
```

行为：
- 项目非 git repo → 打印警告并返回 False（除非 `force=True`）
- 有未提交变更 → 自动 `git add -A && git commit -m "chore: <tag> snapshot <ts>"`
- 工作区干净 → 跳过

批量润色由 novel-pipeline `polish_chapter.py` 已自带快照，writer 侧无需重复调用。writer 侧需要加钩子的位置：`write --batch`、`quality`（修复阶段）、`post-review-fix`。

---

## 协作 Skill：novel-pipeline

writer 是"编辑/审查/发布" orchestrator；**novel-pipeline** 是"批量出稿/润色"生产线。两者各自可独立使用，也可组合。

### 分工

| 能力 | writer | novel-pipeline |
|---|---|---|
| 大纲规划、状态追踪、审查、发布、封面 | ✅ | — |
| 初稿写章（主 Agent 直写） | ✅ 5/9 步管线 | — |
| 批量豆包润色（`DOUBAO_MODEL`） | 不再自持 | ✅ `polish_chapter.py` |
| DeepSeek MCP 批量出稿 | — | ✅ `generate_draft` |
| 硬禁令 B01-B10、43 维审查 | ✅ | — |
| Git 前置快照、断点续传 | ✅ 自持一份（`lib.ensure_git_snapshot`） | ✅ 内置于 `polish_chapter.py` |

### 项目结构统一

两个 skill 都能识别以下三种项目标记（优先级 novel.json > writer.json > novel-pipeline.json）：

| 标记 | 场景 |
|---|---|
| `novel.json` | 新项目推荐 |
| `writer.json` | 已有 writer 项目 |
| `novel-pipeline.json` | 已有 novel-pipeline 项目（向后兼容） |

章节文件名统一为 `chapters/ch_NNN.md`（三位数补零 + 下划线）。

### 三种协作模式

**A. writer 主导 + novel-pipeline 做润色/出稿**（推荐大批量场景）

```
writer.plan()  → outline/chapter_outline/ch_NNN.md
      ↓
novel-pipeline generate_draft  → chapters/ch_NNN.md（初稿）
      ↓
writer review --daily  (8 维发布闸)
      ↓
novel-pipeline polish_chapter --range 1-30 --style-file <writer>/references/presets/fanqie-quick-anti.md
      ↓
writer review --daily  (确认润色未引入新问题)
```

**B. writer 独立**（默认日更场景）

主 Agent 亲写正文 + writer 审查/发布，不调用 novel-pipeline。

**C. novel-pipeline 独立**（脱离 writer 的纯润色/出稿场景）

直接跑 `polish_chapter.py --range N-M chapters/`；不需要 writer.json、也不需要 preset override，走 MCP 默认锁定式润色。

---


## 变更记录

参见 [CHANGELOG.md](CHANGELOG.md)
