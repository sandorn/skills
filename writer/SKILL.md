---
name: writer
version: "7.5"
description: "网文写作全流程引擎：扫榜/拆文/大纲/写章/审查/质检/发布。"
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

## 项目目录结构（唯一标准）

```
{project}/
├── writer.json                  # 项目状态（唯一状态文件）
├── setting/
│   ├── story_bible.md           # 世界观设定总纲
│   ├── characters.md            # 角色卡 + 关系矩阵
│   ├── power_system.md          # 力量/等级/权限体系
│   └── factions.md              # 势力/门派/阵营
├── outline/
│   ├── master_outline.md        # 总纲：核心冲突 + 结局方向
│   ├── volume_outline.md        # 卷纲：节拍表 + 时间线
│   └── chapter_outline/         # 章纲（每章一个文件）
│       ├── ch_001.md
│       └── ...
├── chapters/
│   ├── ch_001.md
│   └── ...
├── tracking/
│   ├── current_state.md         # 角色位置/状态快照
│   ├── hooks.md                 # 伏笔池（已埋/已回收）
│   ├── chapter_summaries.md     # 章节摘要
│   ├── subplot_board.md         # 支线进度板
│   ├── emotional_arcs.md        # 情绪弧线追踪
│   └── resource_ledger.md       # 资源/金币账本
├── .writer/
│   ├── state.json               # 系统运行时状态
│   ├── project_memory.json      # 写作模式记忆
│   ├── facts.db                 # 结构化事实库（SQLite，可选）
│   └── runtime/                 # 临时文件
├── analysis_lib/                # 对标书分析数据
├── reference/                   # 引用书参考视图
└── cover/                       # 封面输出
```

项目根识别：当前目录含 `writer.json` 或 `setting/` + `chapters/` 即视为项目根。

---

## 路由表

| 意图 | 触发词 | 路由 |
|------|--------|------|
| 扫榜/市场分析 | 什么火、排行榜、扫榜 | `references/scan.md` |
| 拆文/竞品分析 | 拆书、黄金三章、深度拆解 | `references/analyze.md` |
| 开新书/初始化 | 开书、新书、初始化、创建项目 | `references/project-init.md` |
| 导入旧稿 | 导入小说、迁移 | `references/project-init.md`（import 模式） |
| 大纲/规划 | 大纲、卷纲、章纲、规划 | `references/plan.md` |
| 写前对齐检查 | 写前检查、总线对齐 | `references/pre-write-alignment.md` |
| 写前自检 | 写前30秒、下笔前检查 | `references/pre-write-checklist.md` |
| 写章节 | 写第N章、续写、日更 | `references/write.md` |
| 批量写章 | 批量写、写N章、连续写 | `references/write.md`（batch 模式，写前必做预写对齐） |
| 短篇 | 短篇、写个故事 | `references/write.md`（short 模式） |
| 全面审查 | 全面审查、全量审查、深度审查 | 5 步管线 → `references/review-cycle.md` |
| 审查/审计 | 审查、审稿、审计 | `references/review.md` |
| 日更审查 | 日更审查、daily、发布前检查、日更质检 | `references/review.md`（daily 模式 — 8 维 3 分钟发布闸） |
| 定向审查 | 定向审查、专项审查 | `references/targeted-audit.md` |
| 质检 | 质检、全线检查 | `references/quality.md` |
| 去AI味 | 去AI味、太AI了 | `references/quality.md`（deslop 模式） |
| 纯手动润色 | 纯手动润色、逐章逐段润色、手工打磨 | `references/manual-polish.md` |
| 全量优化 | 意象钩子清理、钩子强度提升 | `references/optimize.md` |
| 快速可发布判定 | 能不能发、三问判定 | `references/publishable-check.md` |
| 追读力分析 | 追读力、钩子强度、爽点分析 | `scripts/analyze_hook.py` |
| 节奏状态查询 | 升级节奏、金币趋势、感情线进度 | `scripts/analyze_rhythm.py` |
| 长篇质量监控 | 声音漂移、风格指纹、情绪单调 | `references/longform-quality-monitor.md` |
| 事实库查询 | 事实库、等级查询、伏笔查询 | `scripts/fact_db.py query` |
| 查询设定 | 查角色、查伏笔、什么状态 | `references/memory.md`（query） |
| 设定一致性审计 | 设定审查、交叉审查 | `references/setting-consistency-audit.md` |
| 更新角色状态 | 更新角色状态、角色追踪 | `references/track-character-state.md` |
| 学习/记录 | 记住这个写法、记一下 | `references/memory.md`（learn） |
| 实体关系图谱 | 关系、图谱、谁和谁 | `scripts/report_graph.py` |
| 项目全景报告 | 全景、概览、项目状态 | `scripts/report_panorama.py` |
| 番茄投稿检查 | 番茄投稿、格式兼容 | `references/fanqie-submission.md` |
| 多平台导出 | 导出、起点格式、番茄格式 | `scripts/export.py` |
| 封面 | 封面、生成封面 | `references/cover.md` |
| 自动备份 | 备份、存档 | cronjob daily 03:00 |
| 故障排除 | 报错、不工作、问题、怎么办 | `references/troubleshooting.md` |
| 帮助 | 帮助、功能、命令 | 列出路由表 |

路由流程：分析意图 → 匹配路由表 → 加载对应 reference → 无法匹配时列出 3-5 个最可能选项。写章请求但无项目目录时自动转入 project-init。

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

1. **解析项目根**：检测 `writer.json` + `setting/` + `chapters/`
2. **读取状态**：stage、chapters_done、current_chapter
3. **检测缺口**（仅发现问题时提示）：
   - 章节 > 10 但设定文件 < 3 → 建议补充设定
   - `.writer/` 结构不完整 → 提示修复
   - `analysis_lib/` 有待完成的 `_progress.md` → 提示继续拆解
   - `tracking/` 文件缺失 → 提示重建
4. **无信息时完全静默**

已有项目时：从 `writer.json` 读取状态；写章时自动检查上一章进度；批量写章前强制预写对齐检查。

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
| 去AI味/质检 | 主会话 |
| 事实库/脚本查询 | 主会话调用对应 Python 脚本 |
| 封面 | Use available image generation tool; if unavailable, output prompt only |

**Shell 别名加速**：终端命令前检查是否安装了命令加速代理（如 `rtk`），已安装则所有命令加对应前缀。

---

## 审查循环

大规模写章后（>20 章）必须执行全面审查。

> **完整流程**：`references/review-cycle.md`（5 步管线权威定义，含 facts.db 降级路径）
> **审查维度 + Triage**：`references/review.md`（43 维 + First 5 优先检查）
> **修复管线**：`references/post-review-fix.md`

| Step | 名称 | 核心动作 |
|------|------|---------|
| 0 | 项目体检 | 目录完整性 + RAG + facts.db 降级声明 |
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
  └── character-designer  → 角色与对话（按需启用）
        遮名测试 + OOC 深入 + 配角工具人检测 + 语言风格一致性
```

**执行流程**：
1. 主会话分发：将审查范围 + 设定文件路径 + 禁令列表分发到 4 个子代理
2. 并行审查：4 个子代理同时执行，只读不写，各自输出 S1-S4 分级报告
3. 汇总合并：主会话收集 4 份报告 → 合并为统一审查报告 → 处理跨 Agent 冲突
4. 冲突裁决：当两个 Agent 对同一维度给出不同判定时，取更严格的等级
5. 降级兜底：如果子代理不可用或启动失败，自动降级为 lean/solo

**子代理模板**：`agents/story-architect.md` / `consistency-checker.md` / `narrative-writer.md` / `character-designer.md`

**报告模板**：`templates/batch-review-report.md`（含 Full 模式专用汇总格式 + 跨 Agent 冲突矩阵）

---

## 写作约束

### 设定讨论原则

讨论设定元素时遵循：**先定义作用 → 再讨论平衡/代价/售价**。功能决定价值，不是反过来。

### 硬性禁令

> **单一事实来源**：`references/hard-bans.md`（P0 阻塞 5 条 + P1 强制 4 条 + P2 建议 1 条，含项目规范覆盖机制）

### 默认写章管线（5 步）

1. Plan — 确认本章目标、情绪、钩子、禁区
2. Architect — 编排上下文，生成章节结构
3. Write + Reflect — 写正文，提取事实变更
4. Audit + Normalize — 审查硬禁令、AI 痕迹、字数和一致性
5. Revise — 只修 blocking 和用户关心的问题

`--full` 展开 9 步完整管线；`--fast` 缩减为 Plan → Write → Audit → Revise。

### AI 痕迹检测阈值

| 指标 | 阈值 |
|------|------|
| 段落等长变异系数 | < 0.15 warning |
| 模糊词密度 | > 3次/千字 warning |
| 转折词重复 | ≥ 3次 warning |
| 连续相同开头句式 | ≥ 3句 info |

---

## writer.json 格式

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

---

## 子模块索引

> **加载策略**：核心模块每次写作会话预加载；扩展模块按路由匹配按需加载。

### 核心（12 个 — 每次写作必知）

| 文件 | 功能 |
|------|------|
| `references/hard-bans.md` | 硬性禁令单一事实来源（P0-P2 分级） |
| `references/review.md` | 审查维度 + Triage（43维 / 日更8维 / solo15维） |
| `references/review-cycle.md` | 5 步审查管线权威定义（含 facts.db 降级） |
| `references/write.md` | 写作管线（单章/批量/短篇，含 sub-agent delegation 自检） |
| `references/write-pitfalls.md` | 批量写作避坑指南（13 项实战教训） |
| `references/quality.md` | 质检工单（禁令+去AI味+段落修复+RAG+事实库） |
| `references/plan.md` | 大纲规划（总纲→卷纲→章纲） |
| `references/project-init.md` | 项目初始化（含 import 模式） |
| `references/pre-write-alignment.md` | 批量写前总线对齐检查 |
| `references/pre-write-checklist.md` | 写前 30 秒检查清单 |
| `references/publishable-check.md` | 章节快速可发布性三问判定 |
| `references/manual-polish.md` | 纯手动逐章逐段润色（三零原则） |
| `references/memory.md` | 记忆/查询/学习 |

### 扩展（按需加载）

| 文件 | 功能 |
|------|------|
| `references/scan.md` | 跨平台扫榜 + 趋势分析 |
| `references/analyze.md` | 爆款拆解 + 黄金三章 |
| `references/optimize.md` | 全量优化（意象钩子清理+钩子强度提升） |
| `references/targeted-audit.md` | 定向审查 |
| `references/setting-consistency-audit.md` | 设定一致性跨文件审计（统一入口：设定内部→大纲→正文→卷间→修复） |
| `references/post-review-fix.md` | 审查后修复管线（5步+4步+问题模式目录，合并原 3 文件） |
| `references/deploy.md` | 多卷部署流水线 + 卷间衔接检查 |
| `references/hooks-scan.md` | 伏笔全卷扫描方法 |
| `references/master-outline-audit.md` | 总纲暗线对齐检查 |
| `references/opening-craft.md` | 重生文开篇技巧 |
| `references/fanqie-submission.md` | 番茄投稿格式兼容检查 |
| `references/fix-template-cleanup.md` | 模板复制+乱码清除工作流 |
| `references/project-knowledge-base.md` | 项目知识库工具集成指南 |
| `references/cover.md` | 封面生成 |
| `references/track-character-state.md` | 角色状态追踪更新 |
| `references/longform-quality-monitor.md` | 长篇质量趋势监控（声音漂移/情绪/风格指纹） |
| `references/troubleshooting.md` | 常见故障排除（写章/审查/委派/修复四场景） |
| `references/tool-pitfalls.md` | 通用工具陷阱参考 |
| `references/tool-pitfalls-windows.md` | Windows 特有工具陷阱（write_file 换行丢失、PowerShell 引号冲突） |
| `references/project-review-novel-gaming-manifest.md` | 《网游具现：我能看见卡池》项目审查完成记录与工具教训 |

### 脚本（11 个）

| 文件 | 功能 | 层级 |
|------|------|------|
| `scripts/audit.py` | 统一审计（单章/目录/范围，含 --fix-escaped） | 核心 |
| `scripts/pad_chapter.py` | 安全字数追加（无模板，内建段落拆分） | 核心 |
| `scripts/split_paragraphs.py` | 段落拆分（按句号，≤60汉字） | 核心 |
| `scripts/analyze_hook.py` | 追读力分析（钩子强度/爽点/钩力衰减） | 核心 |
| `scripts/fact_db.py` | SQLite 事实库（init/query/insert/status） | 核心 |
| `scripts/report_panorama.py` | 项目全景报告（健康评分+建议） | 核心 |
| `scripts/audit_5dim.py` | 5维专项审查 | 扩展 |
| `scripts/analyze_rhythm.py` | 节奏状态查询 | 扩展 |
| `scripts/report_graph.py` | 实体关系图谱（Mermaid 输出） | 扩展 |
| `scripts/export.py` | 多平台格式导出 | 扩展 |
| `scripts/backup.py` | 每日自动备份（保留7天） | 扩展 |

### Agent 模板（4 个 — full 审查模式调用）

| 文件 | 功能 |
|------|------|
| `agents/story-architect.md` | 故事结构审查（维度 1-15 + 执行卡） |
| `agents/consistency-checker.md` | 事实一致性审查（维度 16-27 + 执行卡） |
| `agents/narrative-writer.md` | 文本质量审查（AI痕迹+禁令+格式） |
| `agents/character-designer.md` | 角色与对话审查（执行卡） |

---

## 变更记录

| 日期 | 关键变更 |
|------|---------|
| 2026-06-29 | **v7.5 本地改动合并**：新增 references/setting-audit-gaming-manifest.md（设定一致性审查标准流程）；tool-pitfalls-windows.md 陷阱完善；SKILL.md 子模块索引同步更新；merged with remote v7.4 |
| 2026-06-29 | **v7.4 逐章审查加固**：SKILL.md 逐章审查路由大幅扩展（明确禁止脚本/加速/跳过；新增「不用脚本」触发词和五条硬性禁令）；SKILL.md 新增「章节污染模式速查」节（①②③三种污染模式+修复方法）；corruption-fix-bu-shi.md 新增「批量修复脚本二次污染」节（「不不」模式+禁止全局替换铁律） |
| 2026-06-28 | **v7.3 审查+重构+污染**：新增 `references/corruption-fix-bu-shi.md`（「不→是」污染修复权威参考）；委派后校验节重构（外链参考文件 + 逐章审查路由 + 开篇节奏重构指引）；write-pitfalls.md 新增避坑 14-18（Windows路径/文风偏好/开篇重构/声音定调/批量替换污染）；SKILL.md 声音偏好节扩展（番茄小说向） |
| 2026-06-28 | **v7.2 委派后污染校验**：新增「委派后校验」节；状态感知新增 `writing_rules.md` 自动加载 |
| 2026-06-26 | **v7.0 通用化**：移除所有 Claude/Hermes 专用术语（delegate_task→sub-agent delegation, web_search→web/content search, image_generate→image generation tool, search_files→grep/pattern search, Moke/Hermes 移除）；agent YAML 泛化（tools→capabilities, model→advisory_model, maxTurns→max_iterations）；hermes-tool-pitfalls.md→tool-pitfalls.md（通用工具陷阱）；codebase-memory-mcp.md→project-knowledge-base.md（通用知识库指南）；SKILL.md 执行策略与子模块索引同步更新 |
| 2026-06-23 | **v4.0 激进瘦身**：移除所有向后兼容；SKILL.md -62%（530→200行） |
| 2026-06-23 | **v4.1 满分冲刺**：review.md 新增 daily 日更 8 维模式（3分钟发布闸）；子模块索引分层（核心12 + 扩展21 + 脚本核心6/扩展5）；执行策略新增 daily 审查 |
| 2026-06-23 | **v4.2 执行层加固**：audit.py 重写（BANS 同步 hard-bans.md + 新增元叙事/引号/模板复制检测）；project-init.md 移除全部旧引用；write-pitfalls.md 抽离；fact_db.py/analyze_hook.py 文档修复 |
| 2026-06-23 | **v4.3 深度净化**：pad_chapter.py 移除违禁词（对话池含「深吸一口气」→ S1 修复）；4 个 agent 模板增加 TL;DR；清除 6 个 reference 中的旧系统名残余；quality-delegate.md 与 batch-post-delegate-fix.md 明确分工；audit_5dim.py 增加项目适配说明 |
| 2026-06-23 | **v4.4 收尾**：write.md 避坑指南彻底抽离至 write-pitfalls.md（sed 切除 ~150 行）；report_panorama.py 移除 project-state.json 回退；review-cycle.md 旧中文路径→新英文路径；SKILL.md 顶部增加「三场景快速上手」卡片；交叉引用完整性审计 |
| 2026-06-23 | **v4.5 文件合并**：batch-post-delegate-fix + batch-fix-s2s3 + quality-delegate 三合一 → post-review-fix.md（修复决策树 + 5步管线 + 4步精准修复 + 问题模式目录）；quality.md 删除与 hard-bans 重复的禁令表；targeted-audit.md 旧路径→新路径；references 34→31 |
| 2026-06-23 | **v4.6 README 同步**：README 完全重写（31 references + 审查模式梯度表 + 三场景快速上手 + 文件清单与 SKILL.md 一致）；移除旧数据流架构图；脚本示例路径统一 |
| 2026-06-23 | **v4.7 模板+默认值**：batch-review-report.md 禁令表同步 hard-bans.md (P0/P1 分级)；report_graph.py 增加项目适配说明；project-init.md 增加智能默认（平台→番茄/字数→3000/章节→60-300）+ 单轮收集优先 |
| 2026-06-23 | **v5.0 CLI**：创建 `scripts/writer` 统一入口（12 子命令 + fix 一键修复 + check 一键检查） |
| 2026-06-23 | **v5.1 权重**：review.md 15 维加权评分（核心三角: 设定冲突30 + OOC25 + 钩子25 = 40%）；健康度计算公式 |
| 2026-06-23 | **v5.2 管线合并**：write.md 9 步完整管线从 ~155 行压缩为 15 行表格（5 步 + 4 扩展）；删除重复描述 |
| 2026-06-23 | **v5.3 部署分工**：deploy.md 添加指向 plan.md 的节拍表引用，明确分工（plan=设计，deploy=执行） |
| 2026-06-23 | **v5.4 Agent 模板**：write.md delegate context 模板（6 个信息块：任务/禁令/状态/章纲/声音/自检） |
| 2026-06-23 | **v5.5-v5.9 完善**：troubleshooting.md 故障排除指南（写章/审查/委派/修复四场景）；project-init 引用 writing_rules 模板 |
| 2026-06-23 | **v6.0 发布**：版本号；12 轮迭代终态——210 行 SKILL.md · 32 references · 12 scripts(含 CLI) · 4 agents · 11 个模板 · 零旧引用 · 执行层与规则层完全同步 |
