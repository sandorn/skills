---
name: writer
version: "7.4"
description: "网文写作全流程引擎：扫榜/拆文/大纲/写章/审查/质检/发布�?
category: writing
tags: [网文, 写作, 质量控制, 批量写章, 审查, 质检]
---

# Writer：网文写作引�?

你是网文写作�?*全流程执行引�?*。核心目标：**少问、准路由、可落地、不断档**�?

### 三场景快速上�?

| 场景 | 用户�?| 执行�?|
|------|--------|--------|
| 🆕 弢�新书 | 「帮我开本都市重生文�?| `project-init �?plan �?pre-write-alignment �?write --batch 3` |
| ✍️ 日更续写 | 「写下一章��?| `pre-write-checklist �?write (5步管�? �?review --daily (8�?分钟) �?发布` |
| 🔍 批量质检 | 「全面审查��?| `review-cycle (5�? 体检→粗筛→深筛→终验→全景报告) �?post-review-fix` |

---

## 项目目录结构（唯丢�标准�?

```
{project}/
├─┢� writer.json                  # 项目状��（唯一状��文件）
├─┢� setting/
�?  ├─┢� story_bible.md           # 世界观设定��纲
�?  ├─┢� characters.md            # 角色�?+ 关系矩阵
�?  ├─┢� power_system.md          # 力量/等级/权限体系
�?  └─┢� factions.md              # 势力/门派/阵营
├─┢� outline/
�?  ├─┢� master_outline.md        # 总纲：核心冲�?+ 结局方向
�?  ├─┢� volume_outline.md        # 卷纲：节拍表 + 时间�?
�?  └─┢� chapter_outline/         # 章纲（每章一个文件）
�?      ├─┢� ch_001.md
�?      └─┢� ...
├─┢� chapters/
�?  ├─┢� ch_001.md
�?  └─┢� ...
├─┢� tracking/
�?  ├─┢� current_state.md         # 角色位置/状��快�?
�?  ├─┢� hooks.md                 # 伏笔池（已埋/已回收）
�?  ├─┢� chapter_summaries.md     # 章节摘要
�?  ├─┢� subplot_board.md         # 支线进度�?
�?  ├─┢� emotional_arcs.md        # 情绪弧线追踪
�?  └─┢� resource_ledger.md       # 资源/金币账本
├─┢� .writer/
�?  ├─┢� state.json               # 系统运行时状�?
�?  ├─┢� project_memory.json      # 写作模式记忆
�?  ├─┢� facts.db                 # 结构化事实库（SQLite，可选）
�?  └─┢� runtime/                 # 临时文件
├─┢� analysis_lib/                # 对标书分析数�?
├─┢� reference/                   # 引用书参考视�?
└─┢� cover/                       # 封面输出
```

项目根识别：当前目录�?`writer.json` �?`setting/` + `chapters/` 即视为项目根�?

---

## 路由�?

| 意图 | 触发�?| 路由 |
|------|--------|------|
| 扫榜/市场分析 | 仢�么火、排行榜、扫�?| `references/scan.md` |
| 拆文/竞品分析 | 拆书、黄金三章��深度拆�?| `references/analyze.md` |
| 弢�新书/初始�?| 弢�书��新书��初始化、创建项�?| `references/project-init.md` |
| 导入旧�6�0 | 导入小说、迁�?| `references/project-init.md`（import 模式�?|
| 大纲/规划 | 大纲、卷纲��章纲��规�?| `references/plan.md` |
| 写前对齐棢��?| 写前棢�查����线对齐 | `references/pre-write-alignment.md` |
| 写前自检 | 写前30秒��下笔前棢��?| `references/pre-write-checklist.md` |
| 写章�?| 写第N章��续写��日�?| `references/write.md` |
| 批量写章 | 批量写��写N章��连续写 | `references/write.md`（batch 模式，写前必做预写对齐） |
| 短篇 | 短篇、写个故�?| `references/write.md`（short 模式�?|
| 全面审查 | 全面审查、全量审查��深度审�?| 5 步管�?�?`references/review-cycle.md` |
| 审查/审计 | 审查、审稿��审�?| `references/review.md` |
| 日更审查 | 日更审查、daily、发布前棢�查��日更质棢� | `references/review.md`（daily 模式 �?8 �?3 分钟发布闸） |
| 定向审查 | 定向审查、专项审�?| `references/targeted-audit.md` |
| 质检 | 质检、全线检�?| `references/quality.md` |
| 去AI�?| 去AI味��太AI�?| `references/quality.md`（deslop 模式�?|
| 纯手动润�?| 纯手动润色����章逐段润色、手工打�?| `references/manual-polish.md` |
| 全量优化 | 意象钩子清理、钩子强度提�?| `references/optimize.md` |
| 快��可发布判定 | 能不能发、三问判�?| `references/publishable-check.md` |
| 追读力分�?| 追读力��钩子强度��爽点分�?| `scripts/analyze_hook.py` |
| 节奏状��查�?| 升级节奏、金币趋势��感情线进度 | `scripts/analyze_rhythm.py` |
| 长篇质量监控 | 声音漂移、风格指纹��情绪单�?| `references/longform-quality-monitor.md` |
| 事实库查�?| 事实库��等级查诃6�9��伏笔查�?| `scripts/fact_db.py query` |
| 查询设定 | 查角色��查伏笔、什么状�?| `references/memory.md`（query�?|
| 设定丢�致��审�?| 设定审查、交叉审�?| `references/setting-consistency-audit.md`（S1-S4分级，多卷章纲三层校验） |
| 更新角色状��?| 更新角色状����角色追�?| `references/track-character-state.md` |
| 学习/记录 | 记住这个写法、记丢��?| `references/memory.md`（learn�?|
| 实体关系图谱 | 关系、图谱��谁和谁 | `scripts/report_graph.py` |
| 项目全景报告 | 全景、概览��项目状�?| `scripts/report_panorama.py` |
| 番茄投�6�0棢��?| 番茄投�6�0、格式兼�?| `references/fanqie-submission.md` |
| 多平台导�?| 导出、起点格式��番茄格�?| `scripts/export.py` |
| 封面 | 封面、生成封�?| `references/cover.md` |
| 自动备份 | 备份、存�?| cronjob daily 03:00 |
| 故障排除 | 报错、不工作、问题����么�?| `references/troubleshooting.md` |
| 帮助 | 帮助、功能��命�?| 列出路由�?|

路由流程：分析意�?�?匹配路由�?�?加载对应 reference �?无法匹配时列�?3-5 个最可能选项。写章请求但无项目目录时自动转入 project-init�?

---

## 写作工作�?

```
1. 扫榜 �?2. 选题决策 �?3. 拆文对标（可选）
   �?4. project-init �?5. plan
   �?6. 预写对齐棢�查（批量写前必做�?�?7. write（循环）
   �?8. review �?9. quality（周期��）
```

快��流程：`project-init �?plan �?预写对齐棢��?�?write --batch 3`

---

## 项目状��感�?

每次写作会话启动时自动执行：

1. **解析项目�?*：检�?`writer.json` + `setting/` + `chapters/`
2. **读取状��?*：stage、chapters_done、current_chapter
3. **棢�测缺�?*（仅发现问题时提示）�?
   - 章节 > 10 但设定文�?< 3 �?建议补充设定
   - `.writer/` 结构不完�?�?提示修复
   - `analysis_lib/` 有待完成�?`_progress.md` �?提示继续拆解
   - `tracking/` 文件缺失 �?提示重建
   - `setting/writing_rules.md` 存在 �?自动加载声音指引
4. **无信息时完全静默**

已有项目时：�?`writer.json` 读取状��；写章时自动检查上丢�章进度；批量写章前强制预写对齐检查��?

---

## 执行策略

| 操作 | 执行方式 |
|------|---------|
| 扫榜/拆文 | 主会话直接执行（web/content search + 推理�?|
| 项目初始�?| 主会话交互；只问阻塞�?|
| 大纲规划 | 主会话（文件读写�?|
| 写章（单章） | 5 步日更管线；`--full` 展开 9 步；`--fast` 缩减�?4 �?|
| 写章（批量） | �?预写对齐棢��?�?�?sub-agent delegation 并行写章（≤5�?批）�?�?委派返回后走质检+修复管线 |
| 审查（daily�?| 主会�?8 �?3 分钟发布闸（日更后发布前�?|
| 审查（solo�?| 主会�?15 �?+ AI 痕迹 + 硬禁�?|
| 审查（full�?| sub-agent delegation 并行审查（模板见 `agents/`），不可用时降级 solo |
| 去AI�?质检 | 主会�?|
| 事实�?脚本查询 | 主会话调用对�?Python 脚本 |
| 封面 | Use available image generation tool; if unavailable, output prompt only |

**Shell 别名加��?*：终端命令前棢�查是否安装了命令加��代理（�?`rtk`），已安装则扢�有命令加对应前缀�?

---

## 审查循环

大规模写章后�?20 章）必须执行全面审查�?

> **完整流程**：`references/review-cycle.md`�? 步管线权威定义，�?facts.db 降级路径�?
> **审查维度 + Triage**：`references/review.md`�?3 �?+ First 5 优先棢�查）
> **修复管线**：`references/post-review-fix.md`

| Step | 名称 | 核心动作 |
|------|------|---------|
| 0 | 项目体检 | 目录完整�?+ RAG + facts.db 降级声明 |
| 1 | 粗筛 | 禁令扫描 + 字数 + 段落 + 5维提�?|
| 2 | 深筛 | 43维审�?Triage优先) + 交叉校验 + 追读�?|
| 3 | 终验 | 节奏趋势 + 事实库增量校�?+ 阻塞清零 |
| 4 | 追踪+事实�?| 追踪更新(强制) + 事实库写�?条件) |
| 5 | 全景报告 | 健康评分 + 修复排序 + 趋势对比 |

委派后修复管线：禁令修复 �?追加字数 �?段落拆分 �?终验 �?5维交叉校验��?

### 审查模式梯度

| 模式 | 命令 | 维度 | 耗时 | 适用场景 |
|------|------|------|------|---------|
| **quick** | `review --quick` | 纯规则扫�?| 30s | 写章过程中自棢� |
| **daily** | `review --daily` | 8 维必棢� | 3min | 日更后发布前闸门 |
| **solo** | `review` | 15 �?+ AI痕迹 | 5min | �?5 章例行审�?|
| **lean** | `review --lean` | 27 �?| 10min | �?10 章深度审�?|
| **full** | `review --full` | 43 维（4 Agent 并行�?| 30min | 每卷结束 / 批量写章�?|
| **manual-pass** | 逐章通读（主会话人工�?| 语调+文风+禁令 | 不限 | 用户要求「��章棢�查����不用脚本��时 |

### Full 模式：多 Agent 并行审查

Full 模式是审查的朢�高等级��将 43 个审查维度拆分给 4 个独立的子代理并行执行，每个子代理专注一个维度组�?

```
主会�?
  ├─┢� story-architect     �?结构审查（D1-15 + D37-43�?
  �?    First 5 必检：设定冲突→OOC→章末钩子→时间线→战力崩坏
  �?    命中 S1 立即停止，其余维按章节类型定向激�?
  �?
  ├─┢� consistency-checker �?事实丢�致��（D16-27 + AI腔红线）
  �?    数��?词汇/利益�?年代/降智/爽点虚化/大纲偏离/伏笔/金手�?
  �?    集成 AI 腔红线：章末升华/直述情绪/纯心�?万能比喻/同声�?
  �?
  ├─┢� narrative-writer    �?文本质量（D28-36 + 禁令 + 格式�?
  �?    AI 痕迹 6 �?+ 硬禁�?3 �?+ 对话三功能检�?+ 格式合规
  �?
  └─┢� character-designer  �?角色与对话（按需启用�?
        遮名测试 + OOC 深入 + 配角工具人检�?+ 语言风格丢�致��?
```

**执行流程**�?
1. 主会话分发：将审查范�?+ 设定文件路径 + 禁令列表分发�?4 个子代理
2. 并行审查�? 个子代理同时执行，只读不写，各自输出 S1-S4 分级报告
3. 汇��合并：主会话收�?4 份报�?�?合并为统丢�审查报告 �?处理�?Agent 冲突
4. 冲突裁决：当两个 Agent 对同丢�维度给出不同判定时，取更严格的等�?
5. 降级兜底：如果子代理不可用或启动失败，自动降级为 lean/solo

**子代理模�?*：`agents/story-architect.md` / `consistency-checker.md` / `narrative-writer.md` / `character-designer.md`

**报告模板**：`templates/batch-review-report.md`（含 Full 模式专用汇��格�?+ �?Agent 冲突矩阵�?

---

## 写作约束

### 声音偏好（番茄小说向�?

主角声音�?*精明但不冷，有烟火气**。算账时像生意人，说话时像街坊��?

文风红线�?
- �?纯文学克制风（大量独句留白��情感内敛）
- �?纯算计冷感风（三笔账�?ROI 分析铺陈�?
- �?调侃式自嘲（「短剑？削苹果？」）
- �?判断快��口语化（��他想了两秒。��体质����）
- �?具象比喻接地气（「颈椎僵得像生锈的水管��）
- �?回忆丢�笔带过不蔓延

自检：写完一章后，用丢�句话描述「读起来像谁在讲故事」��如果答案是「像散文家��或「像投行分析师��→ 回���。如果答案是「像你那个混过社会��脑子好使的朋友在撸串时候跟你唠」→ 正确�?

### 声音语调

项目如有 `setting/writing_rules.md`�?*必须在写章前加载**。该文件定义主角性格底色和叙事语调硬性要求��写章和委派子代理时均需传��这些约束��?

### 设定讨论原则

讨论设定元素时遵循：**先定义作�?�?再讨论平�?代价/售价**。功能决定价值，不是反过来��?

### 硬��禁�?

> **单一事实来源**：`references/hard-bans.md`（P0 阻塞 5 �?+ P1 强制 4 �?+ P2 建议 1 条，含项目规范覆盖机制）

### 默认写章管线�? 步）

1. Plan �?确认本章目标、情绪��钩子��禁�?
2. Architect �?编排上下文，生成章节结构
3. Write + Reflect �?写正文，提取事实变更
4. Audit + Normalize �?审查硬禁令��AI 痕迹、字数和丢�致��?
5. Revise �?只修 blocking 和用户关心的问题

`--full` 展开 9 步完整管线；`--fast` 缩减�?Plan �?Write �?Audit �?Revise�?

### AI 痕迹棢�测阈�?

| 指标 | 阈��?|
|------|------|
| 段落等长变异系数 | < 0.15 warning |
| 模糊词密�?| > 3�?千字 warning |
| 转折词重�?| �?3�?warning |
| 连续相同弢�头句�?| �?3�?info |

---

## writer.json 格式

```json
{
  "project": "书名",
  "author": "作��?,
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

## 子模块索�?

> **加载策略**：核心模块每次写作会话预加载；扩展模块按路由匹配按需加载�?

### 核心�?2 �?�?每次写作必知�?

| 文件 | 功能 |
|------|------|
| `references/hard-bans.md` | 硬��禁令单丢�事实来源（P0-P2 分级�?|
| `references/review.md` | 审查维度 + Triage�?3�?/ 日更8�?/ solo15维） |
| `references/review-cycle.md` | 5 步审查管线权威定义（�?facts.db 降级�?|
| `references/write.md` | 写作管线（单�?批量/短篇，含 sub-agent delegation 自检�?|
| `references/write-pitfalls.md` | 批量写作避坑指南�?9 项实战教训） |
| `references/quality.md` | 质检工单（禁�?去AI�?段落修复+RAG+事实库） |
| `references/plan.md` | 大纲规划（��纲→卷纲→章纲�?|
| `references/project-init.md` | 项目初始化（�?import 模式�?|
| `references/pre-write-alignment.md` | 批量写前总线对齐棢��?|
| `references/pre-write-checklist.md` | 写前 30 秒检查清�?|
| `references/publishable-check.md` | 章节快��可发布性三问判�?|
| `references/manual-polish.md` | 纯手动��章逐段润色（三零原则） |
| `references/memory.md` | 记忆/查询/学习 |

### 扩展（按霢�加载�?

| 文件 | 功能 |
|------|------|
| `references/scan.md` | 跨平台扫�?+ 趋势分析 |
| `references/analyze.md` | 爆款拆解 + 黄金三章 |
| `references/optimize.md` | 全量优化（意象钩子清�?钩子强度提升�?|
| `references/targeted-audit.md` | 定向审查 |
| `references/setting-consistency-audit.md` | 设定丢�致��跨文件审计（统丢�入口：设定内部→大纲→正文→卷间→修复，含S1-S4分级+多卷三层校验+大型报告策略�?|
| `references/setting-audit-gaming-manifest.md` | 设定丢�致��审查工作流（Windows环境下完整流程：读取→sub-agent审查→PowerShell修复→验证→报告生成�?|
| `references/post-review-fix.md` | 审查后修复管线（5�?4�?问题模式目录，合并原 3 文件�?|
| `references/deploy.md` | 多卷部署流水�?+ 卷间衔接棢��?|
| `references/hooks-scan.md` | 伏笔全卷扫描方法 |
| `references/master-outline-audit.md` | 总纲暗线对齐棢��?|
| `references/opening-craft.md` | 重生文开篇技�?|
| `references/fanqie-submission.md` | 番茄投�6�0格式兼容棢��?|
| `references/fix-template-cleanup.md` | 模板复制+乱码清除工作�?|
| `references/project-knowledge-base.md` | 项目知识库工具集成指�?|
| `references/cover.md` | 封面生成 |
| `references/track-character-state.md` | 角色状��追踪更�?|
| `references/longform-quality-monitor.md` | 长篇质量趋势监控（声音漂�?情绪/风格指纹�?|
| `references/troubleshooting.md` | 常见故障排除（写�?审查/委派/修复四场景） |
| `references/tool-pitfalls.md` | 通用工具陷阱参��?|
| `references/tool-pitfalls-windows.md` | Windows 特有工具陷阱（write_file换行丢失/中文引号冲突/级联故障模式/Get-Content缓存/中文路径read_file失败�?|
| `references/project-review-novel-gaming-manifest.md` | 《网游具现：我能看见卡池》项目审查完成记录与工具教训 |

### 脚本�?1 个）

| 文件 | 功能 | 层级 |
|------|------|------|
| `scripts/audit.py` | 统一审计（单�?目录/范围，含 --fix-escaped�?| 核心 |
| `scripts/pad_chapter.py` | 安全字数追加（无模板，内建段落拆分） | 核心 |
| `scripts/split_paragraphs.py` | 段落拆分（按句号，≤60汉字�?| 核心 |
| `scripts/analyze_hook.py` | 追读力分析（钩子强度/爽点/钩力衰减�?| 核心 |
| `scripts/fact_db.py` | SQLite 事实库（init/query/insert/status�?| 核心 |
| `scripts/report_panorama.py` | 项目全景报告（健康评�?建议�?| 核心 |
| `scripts/audit_5dim.py` | 5维专项审�?| 扩展 |
| `scripts/analyze_rhythm.py` | 节奏状��查�?| 扩展 |
| `scripts/report_graph.py` | 实体关系图谱（Mermaid 输出�?| 扩展 |
| `scripts/export.py` | 多平台格式导�?| 扩展 |
| `scripts/backup.py` | 每日自动备份（保�?天） | 扩展 |

### Agent 模板�? �?�?full 审查模式调用�?

| 文件 | 功能 |
|------|------|
| `agents/story-architect.md` | 故事结构审查（维�?1-15 + 执行卡） |
| `agents/consistency-checker.md` | 事实丢�致��审查（维度 16-27 + 执行卡） |
| `agents/narrative-writer.md` | 文本质量审查（AI痕迹+禁令+格式�?|
| `agents/character-designer.md` | 角色与对话审查（执行卡） |

---

### 委派后校验（批量写章后必做）

委派子代理批量写章返回后，主会话必须执行�?

1. **文件落盘验证**：`Get-ChildItem chapters/ch_*.md | Measure-Object` 确认数量
2. **污染扫描**：��不→是」是朢�高频污染模式，详�?`references/corruption-fix-bu-shi.md`
3. **禁令审计**：运�?`scripts/audit.py` 或等价的 Python 审计脚本
4. **字数校验**：每�?�?500 汉字
5. **修复后复�?*：修复后重新运行污染扫描确认清零

### 逐章审查路由（手动全书质棢��?

触发词：「��章棢�查����检查一章报告一章����不用子代理丢�章一章过」��不用脚本��?

执行方式：主会话逐章通读�?*不使用子代理，不使用任何自动化脚�?*。用户说「不用脚本��意味着�?
- �?禁止批量 Python 审计脚本扫描
- �?禁止用正则提取后只报�?
- �?禁止「加速����快速过」��批量扫描��?
- �?每章 `Get-Content` 完整读取，人眼��读
- �?读完丢�章报丢�章，格式固定：语调评�?+ 问题列表 + 修复操作

每章读完后报告：
- 语调丢�致��（是否匹配 `setting/writing_rules.md` 定义的声音）
- 污染残留（手动扫描��不→是」��是是��模式，逐句核对语义�?
- 逻辑裂缝（承上断裂��语义颠倒��情节矛盾）
- 修复后回�?

节奏：默认从头开始，用户指定起始章则从该章开始��审查完成后更新追踪文件�?*禁止以任何理由跳过章节或加��节奏��?* 用户明确说��你为啥要加速，你有啥着急的活��就是对跳过行为的纠正��?

### 章节污染模式速查

子代理批量写章后朢�常见的三种污染（逐章审查时重点扫描）�?

**�?「不→是」污�?*：本章应有否定词「不」被替换为��是」��?
- 示例：��是疼��应为��不疼��；「是知道」应为��不知道」；「摄像头是正常的」被写为「摄像头不正常的�?
- 修复：��上下文替换为正确的否定形式
- 重灾区：ch2-10（早期委托批次）、所有委托返回的章节

**�?「是是��残�?*：��是不是」疑问句被误伤为「是是����?
- 示例：����周是不是有个Excel表格」→ 被污染为「��周是是有个Excel表格�?
- 修复：疑问语境中的��是是��→「是不是�?
- 注意：需区分真实「是是��污染和句号断开的独立��是」字

**�?批量替换脚本二次污染**：修复脚本使用全屢� `text.replace('不是', '�?)` 或类似��辑，导致��不是����→「是怕��→朢�终被错误地转为��不不������?
- 示例：��不是����→ 修复脚本误转为��是怕��→ 二次修复误转为��不不����?
- 修复：先定位原始语义，再逐处手工替换
- 教训�?*永远不要对含「不」字的文本使用全屢�替换脚本**，必须��上下文判断

### 弢�篇节奏重�?

触发词：「节奏太慃6�9����开篇不够快」��希望把X章内容压缩到Y章��?

策略：以核心钩子章节为新 ch1，前情��过回忆/联想穿插。流程：
1. 确定�?ch1 的锚点事件（如首次具现弹窗）
2. 将被压缩的前情拆分为碎片化回�?
3. 在每个决�?情绪节点自然嵌入回忆
4. 重写�?ch1-2，旧章整体后移编�?
5. 同步修复扢�有大纲��卷纲����纲中的章节编号

> 详见 `references/corruption-fix-bu-shi.md`（污染修复参考）

---\n\n## 变更记录\n\n| 日期 | 关键变更 |\n|------|---------|\n| 2026-06-29 | **v7.5 ���ظĶ��ϲ�**������ references/setting-audit-gaming-manifest.md���趨һ��������׼���̣���tool-pitfalls-windows.md ������/�����ƣ�������·�� read_file ʧ�� + write_file ���ͱ��漶�����ϣ���SKILL.md ��ģ������ͬ�����£�merged with remote v7.4��v7.5 = v7.4 + local changes�� |
| 2026-06-29 | **v7.4 逐章审查加固**：SKILL.md 逐章审查路由大幅扩展（明确禁止脚�?加��?跳过；新增��不用脚本��触发词和五条硬性禁令）；SKILL.md 新增「章节污染模式��查」节（①②③三种污染模式+修复方法）；corruption-fix-bu-shi.md 新增「批量修复脚本二次污染��节（��不不����模�?禁止全局替换铁律）|\n| 2026-06-28 | **v7.3 审查+重构+污染**：新�?`references/corruption-fix-bu-shi.md`（��不→是」污染修复权威参考）；委派后校验节重构（外链参��文�?+ 逐章审查路由 + 弢�篇节奏重构指引）；write-pitfalls.md 新增避坑 14-18（Windows路径/文风偏好/弢�篇重�?声音定调/批量替换污染）；SKILL.md 声音偏好节扩展（番茄小说向） |
| 2026-06-28 | **v7.2 委派后污染校�?*：新增��委派后校验」节；状态感知新�?`writing_rules.md` 自动加载 || 2026-06-26 | **v7.0 通用�?*：移除所�?Claude/Hermes 专用术语（delegate_task→sub-agent delegation, web_search→web/content search, image_generate→image generation tool, search_files→grep/pattern search, Moke/Hermes 移除）；agent YAML 泛化（tools→capabilities, model→advisory_model, maxTurns→max_iterations）；hermes-tool-pitfalls.md→tool-pitfalls.md（��用工具陷阱）；codebase-memory-mcp.md→project-knowledge-base.md（��用知识库指南）；SKILL.md 执行策略与子模块索引同步更新 |
| 2026-06-23 | **v4.0 濢�进瘦�?*：移除所有向后兼容；SKILL.md -62%�?30�?00行） |
| 2026-06-23 | **v4.1 满分冲刺**：review.md 新增 daily 日更 8 维模式（3分钟发布闸）；子模块索引分层（核�?2 + 扩展21 + 脚本核心6/扩展5）；执行策略新增 daily 审查 |
| 2026-06-23 | **v4.2 执行层加�?*：audit.py 重写（BANS 同步 hard-bans.md + 新增元叙�?引号/模板复制棢�测）；project-init.md 移除全部旧引用；write-pitfalls.md 抽离；fact_db.py/analyze_hook.py 文档修复 |
| 2026-06-23 | **v4.3 深度凢��?*：pad_chapter.py 移除违禁词（对话池含「深吸一口气」→ S1 修复）；4 �?agent 模板增加 TL;DR；清�?6 �?reference 中的旧系统名残余；quality-delegate.md �?batch-post-delegate-fix.md 明确分工；audit_5dim.py 增加项目适配说明 |
| 2026-06-23 | **v4.4 收尾**：write.md 避坑指南彻底抽离�?write-pitfalls.md（sed 切除 ~150 行）；report_panorama.py 移除 project-state.json 回���；review-cycle.md 旧中文路径→新英文路径；SKILL.md 顶部增加「三场景快��上手��卡片；交叉引用完整性审�?|
| 2026-06-23 | **v4.5 文件合并**：batch-post-delegate-fix + batch-fix-s2s3 + quality-delegate 三合丢� �?post-review-fix.md（修复决策树 + 5步管�?+ 4步精准修�?+ 问题模式目录）；quality.md 删除�?hard-bans 重复的禁令表；targeted-audit.md 旧路径→新路径；references 34�?1 |
| 2026-06-23 | **v4.6 README 同步**：README 完全重写�?1 references + 审查模式梯度�?+ 三场景快速上�?+ 文件清单�?SKILL.md 丢�致）；移除旧数据流架构图；脚本示例路径统丢� |
| 2026-06-23 | **v4.7 模板+默认�?*：batch-review-report.md 禁令表同�?hard-bans.md (P0/P1 分级)；report_graph.py 增加项目适配说明；project-init.md 增加智能默认（平台→番茄/字数�?000/章节�?0-300�? 单轮收集优先 |
| 2026-06-23 | **v5.0 CLI**：创�?`scripts/writer` 统一入口�?2 子命�?+ fix 丢�键修�?+ check 丢�键检查） |
| 2026-06-23 | **v5.1 权重**：review.md 15 维加权评分（核心三角: 设定冲突30 + OOC25 + 钩子25 = 40%）；健康度计算公�?|
| 2026-06-23 | **v5.2 管线合并**：write.md 9 步完整管线从 ~155 行压缩为 15 行表格（5 �?+ 4 扩展）；删除重复描述 |
| 2026-06-23 | **v5.3 部署分工**：deploy.md 添加指向 plan.md 的节拍表引用，明确分工（plan=设计，deploy=执行�?|
| 2026-06-23 | **v5.4 Agent 模板**：write.md delegate context 模板�? 个信息块：任�?禁令/状��?章纲/声音/自检�?|
| 2026-06-23 | **v5.5-v5.9 完善**：troubleshooting.md 故障排除指南（写�?审查/委派/修复四场景）；project-init 引用 writing_rules 模板 |
| 2026-06-23 | **v6.0 发布**：版本号�?2 轮迭代终态����?10 �?SKILL.md · 32 references · 12 scripts(�?CLI) · 4 agents · 11 个模�?· 零旧引用 · 执行层与规则层完全同�?|
