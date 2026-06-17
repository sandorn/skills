# MoKe (墨客) - AI 小说写作系统

<div align="center">

**让 AI 辅助创作更高效**

一个基于 InkOS 构建的智能小说写作系统，专为中文网小说设计。

[功能特性](#功能特性) • [快速开始](#快速开始) • [命令列表](#命令列表) • [工作流程](#工作流程)

</div>

---

## 项目简介

MoKe (墨客) 是一个 AI 驱动的小说写作辅助系统，通过多个专业 Agent 协作，实现从规划、写作到审校的全流程自动化。系统特别针对中文网小说的创作特点进行了优化，支持玄幻、仙侠、都市等多种题材。

### 核心优势

- **多 Agent 协作**：Planner、Composer、Writer、Auditor、Reviser 五大 Agent 分工协作
- **状态管理完善**：追踪角色位置、关系、伏笔、冲突等关键信息
- **质量保证体系**：自动化审计和修订流程，确保剧情连贯性和角色一致性
- **模板化工作流**：开箱即用的模板系统，快速启动新项目

## 功能特性

### 1. 智能章节规划
- 基于卷纲自动生成章节规划
- 智能伏笔管理（埋设、推进、回收）
- 冲突设计和节奏控制

### 2. 上下文编排
- 自动提取相关角色信息
- 智能构建写作规则栈
- 世界观和伏笔关联

### 3. 高质量写作
- 3000 字标准章节生成
- 角色一致性保证
- 题材风格适配

### 4. 质量审计
- 连续性检查（时间、空间、状态、知识）
- 角色行为一致性验证
- 逻辑合理性审查
- 格式规范检查

### 5. 智能修订
- 多种修订模式（定点修复、润色、改写、重构）
- 基于审计反馈的精准修订
- 字数和风格保持

## 安装

### 环境要求

- Claude Code 已安装
- Node.js 14+
- 支持 Markdown 编辑器

### 全局安装（推荐）

全局安装后，所有项目都可以使用 MoKe：

```bash
npx moke-novel --global
```

### 本地安装

仅在当前项目中安装 MoKe：

```bash
npx moke-novel --local
```

### 交互式安装

不指定选项时，会提示你选择安装方式：

```bash
npx moke-novel
```

### 卸载

```bash
# 卸载全局安装
npx moke-novel --global --uninstall

# 卸载本地安装
npx moke-novel --local --uninstall
```

### 查看帮助

```bash
npx moke-novel --help
```

## 快速开始

### 创建新书籍

```bash
# 使用 Claude Code 创建新书籍项目
/moke:create-book
```

系统会引导你输入：
- 书名
- 题材（玄幻/都市/仙侠/恐怖/其他）
- 目标平台（番茄/飞卢/起点/其他）
- 目标章节数
- 每章字数

### 书籍目录结构

创建完成后，会生成以下目录结构：

```
books/[书名]/
├── moke.json              # 核心配置文件
├── story/
│   ├── bible.md           # 世界观设定
│   ├── current_state.md   # 当前状态
│   ├── hooks.md           # 伏笔管理
│   ├── summaries.md       # 章节摘要
│   └── volume_outline.md  # 卷纲规划
├── chapters/              # 章节内容
│   ├── chapter-0001.md
│   ├── chapter-0002.md
│   └── ...
└── runtime/               # 运行时文件
    └── plan.md            # 章节规划
```

**文件夹命名**：
- 直接使用书名：`books/吞天魔帝/`
- 特殊字符替换为下划线：`books/Sky_Swallowing_Demon_Emperor/`

### 初始化设定

1. **完善世界观设定** (story/bible.md)
   - 世界类型和力量体系
   - 主要势力
   - 力量等级体系
   - 特殊规则和禁忌

2. **规划第一卷大纲** (story/volume_outline.md)
   - 核心目标和主要冲突
   - 章节范围和规划
   - 关键情节
   - 伏笔规划

3. **初始化当前状态** (story/current_state.md)
   - 角色初始位置
   - 关系状态
   - 已知信息分布
   - 初始冲突

## 命令列表

### 核心命令

| 命令 | 描述 | 使用场景 |
|------|------|----------|
| `moke:help` | 显示所有命令和用法 | 查看帮助 |
| `moke:settings` | 配置 MoKe 设置（模式、粒度） | 调整执行方式 |
| `moke:set-profile` | 设置模型配置（quality/budget） | 调整模型/成本 |
| `moke:create-book` | 创建新书籍项目 | 开始新项目 |
| `moke:plan-chapter` | 规划章节意图 | 每章写作前 |
| `moke:draft` | 写章节草稿 | 生成章节内容 |
| `moke:audit` | 审计章节质量 | 检查章节质量 |
| `moke:revise` | 根据审计修订章节 | 修复质量问题 |
| `moke:write-next` | 完整管线写下一章 | 一键完成全流程 |
| `moke:write-batch` | 批量连续写多章 | 避免上下文消耗 |

### 命令详解

#### moke:settings
配置 MoKe 的核心设置。

```bash
/moke:settings
```

**核心设置**：

| 设置 | 选项 | 默认值 | 作用 |
|------|------|--------|------|
| `mode` | `yolo`, `interactive` | `interactive` | 自动批准，还是每一步确认 |
| `granularity` | `coarse`, `standard`, `fine` | `standard` | 章节创作粒度 |

**模式说明**：

- **yolo**：自动执行所有步骤，无需确认。规划 → 编排 → 写作 → 审计 → 修订 全自动完成
- **interactive**：每个步骤都需要确认，可以随时调整或中止

**示例**：
```bash
# 切换到自动模式
/moke:settings --mode yolo

# 查看当前配置
/moke:settings

# 切换到交互模式
/moke:settings --mode interactive
```

**配置文件位置**：`books/<书名>/.moke/config.json`

#### moke:create-book
创建新书籍项目，初始化所有必要的文件和配置。

```bash
moke:create-book
```

#### moke:plan-chapter
规划章节意图，包括目标、冲突、约束条件。

```bash
moke:plan-chapter
```

**输入**：卷纲、当前状态、伏笔池、作者意图
**输出**：runtime/plan.md

#### moke:draft
基于章节规划生成 3000 字章节草稿。

```bash
moke:draft
```

**输入**：章节规划、当前状态、世界观设定
**输出**：chapters/chapter-XXXX.md

#### moke:audit
审计最新章节的质量，检查连续性、一致性、逻辑性等。

```bash
moke:audit
```

**审计维度**（37个）：
- 基础维度（1-27）：OOC检查、时间线、设定冲突、战力崩坏、数值检查、伏笔、节奏、文风、信息越界、词汇疲劳、利益链、年代考据、配角降智、配角工具人、爽点虚化、台词失真、流水账、知识库污染、视角一致性、段落等长、套话密度、公式化转折、列表式结构、支线停滞、弧线平坦、节奏单调、敏感词
- AI痕迹检测（纯规则）：段落等长、套话密度、公式化转折、列表式结构、AI标记词限频
- 番外维度（28-31）：正传事件冲突、未来信息泄露、世界规则跨书一致性、番外伏笔隔离
- 通用维度（32-33）：读者期待管理、大纲偏离检测
- 同人维度（34-37）：角色还原度、世界规则遵守、关系动态、正典事件一致性
- 硬性禁令：禁止句式、破折号、分析术语、元叙事、账本数据

#### moke:revise
根据审计报告修订章节，解决质量问题。

```bash
moke:revise
```

**修订模式**：
- spot-fix: 定点修复
- polish: 润色
- rewrite: 改写
- rework: 重构

#### moke:write-next
执行完整的写作流程：规划 → 编排 → 写作 → 审计 → 修订。

```bash
moke:write-next
```

这是最常用的命令，一键完成从规划到成稿的全流程。

#### moke:write-batch
批量连续写作多个章节，使用专门的 agent 执行，避免消耗主对话上下文。

```bash
# 连续写 3 章
/moke:write-batch --count 3

# 写到第 10 章
/moke:write-batch --to-chapter 10

# 无限制连续写
/moke:write-batch --continuous

# 带作者意图指导
/moke:write-batch --count 5 --context "主角开始修炼之旅"
```

**参数说明**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count` | 写作章节数量 | 1 |
| `--to-chapter` | 写到第几章 | - |
| `--continuous` | 无限制连续写 | false |
| `--context` | 作者意图指导 | - |

**输出示例**：
```
[批量写作] 开始写第 1 章...
[批量写作] 第 1 章完成 ✓
[进度: 1/3] 字数: 3,124 字 | 审计: 通过 | 用时: 2m 30s
[批量写作] 开始写第 2 章...
...
[批量写作] 全部完成！共完成 3 章
```

**注意事项**：
- 建议先用 `yolo` 模式测试单章
- 长时间运行请确保有足够 API 配额
- 进度保存在 `runtime/batch-progress.md`

#### moke:set-profile
设置各代理使用的模型配置，平衡质量与成本。

```bash
/moke:set-profile quality   # 最高质量模式
/moke:set-profile balanced  # 平衡模式（默认）
/moke:set-profile budget    # 经济模式
/moke:set-profile inherit   # 继承 Claude Code 默认模型
```

**模型配置对照表**：

| Profile | Planner | Writer | Auditor | Reviser |
|---------|---------|--------|---------|---------|
| `quality` | Opus | Opus | Sonnet | Sonnet |
| `balanced` | Opus | Sonnet | Sonnet | Sonnet |
| `budget` | Sonnet | Sonnet | Haiku | Haiku |
| `inherit` | 继承 | 继承 | 继承 | 继承 |

## 工作流程

### 标准写作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    1. 准备阶段                                │
├─────────────────────────────────────────────────────────────┤
│  • 完善 story/bible.md（世界观设定）                          │
│  • 规划 story/volume_outline.md（卷纲）                       │
│  • 更新 story/current_state.md（当前状态）                    │
│  • 检查 story/hooks.md（伏笔管理）                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    2. 规划阶段                                │
├─────────────────────────────────────────────────────────────┤
│  moke:plan-chapter                                           │
│  • 生成章节规划（目标、冲突、约束）                            │
│  • 保存到 runtime/plan.md                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    3. 写作阶段                                │
├─────────────────────────────────────────────────────────────┤
│  moke:draft                                                   │
│  • 读取章节规划和相关上下文                                    │
│  • 生成 3000 字章节内容                                       │
│  • 保存到 chapters/chapter-XXXX.md                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    4. 审计阶段                                │
├─────────────────────────────────────────────────────────────┤
│  moke:audit                                                   │
│  • 检查连续性、一致性、逻辑性                                  │
│  • 生成审计报告                                               │
│  • 标记问题严重程度                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    有问题？
                    ↙      ↘
                  是        否
                  ↓         ↓
┌─────────────────────────┐  ┌─────────────────────────────────┐
│     5. 修订阶段          │  │      6. 完成阶段                 │
├─────────────────────────┤  ├─────────────────────────────────┤
│ moke:revise              │  │ • 添加章节摘要到 summaries.md   │
│ • 修复审计问题           │  │ • 更新 hooks.md（伏笔）          │
│ • 保持字数和风格         │  │ • 更新 current_state.md（状态）  │
│ • 保存修订版本           │  │ • 准备下一章                     │
└─────────────────────────┘  └─────────────────────────────────┘
           ↓
           └──→ 返回审计阶段，直到通过
```

### 快速工作流

使用 `moke:write-next` 命令一键完成步骤 2-5，系统会自动循环直到审计通过。

```bash
moke:write-next
```

### 状态管理最佳实践

1. **写作前**：
   - 更新 `current_state.md` 确认角色位置和状态
   - 检查 `hooks.md` 是否有需要回收的伏笔

2. **写作中**：
   - 参考 `story_bible.md` 保持世界观一致
   - 参考 `volume_outline.md` 按大纲推进

3. **写作后**：
   - 在 `summaries.md` 添加本章摘要
   - 如埋下新伏笔，在 `hooks.md` 中记录
   - 如回收伏笔，更新 `hooks.md` 状态
   - 更新 `current_state.md` 记录新状态

## 架构说明

MoKe 基于 InkOS 的多 Agent 架构构建，通过专业化分工实现高效的协作创作。

### 完整管线（9 个 Agent）

每一章由多个 Agent 接力完成，全程零人工干预：

```
┌──────────────┐
│   Planner    │  1. 规划章节意图
│  (moke-      │  • 章节目标 (must-keep/must-avoid)
│   planner)   │  • 冲突设计
└──────┬───────┘  • 伏笔计划
       │
       ↓
┌──────────────┐
│  Composer    │  2. 编排上下文和规则
│  (moke-      │  • 相关状态提取
│   composer)  │  • 规则栈构建
└──────┬───────┘  • 上下文选择
       │
       ↓
┌──────────────┐
│  Architect   │  3. 规划章节结构
│  (moke-      │  • 大纲、场景节拍
│  architect)  │  • 节奏控制
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   Writer     │  4. 生成正文
│  (moke-      │  • 3000字内容
│   writer)    │  • 角色一致性
└──────┬───────┘  • 风格适配
       │
       ↓
┌──────────────┐
│  Observer    │  5. 提取 9 类事实
│  (moke-      │  • 角色、位置、资源
│   observer)  │  • 关系、情绪、信息
└──────┬───────┘  • 伏笔、时间、身体
       │
       ↓
┌──────────────┐
│  Reflector   │  6. 更新状态文件
│  (moke-      │  • 合并到 7 个真相文件
│   reflector)  │  • JSON delta 输出
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  Normalizer  │  7. 字数归一化
│  (moke-      │  • 压缩/扩展
│ normalizer)  │  • 拉入 2800-3200 字
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   Auditor    │  8. 质量审计
│  (moke-      │  • 37 维度检查
│   auditor)   │  • 连续性、一致性、AI痕迹
└──────┬───────┘  • 逻辑审查
       │
       ↓
   有问题？
   ↙      ↘
 是        否
 ↓         ↓
┌──────────────┐  ┌──────────────┐
│  Reviser     │  │   完成       │
│  (moke-      │  └──────────────┘
│   reviser)   │
└──────────────┘
```

### 7 个真相文件

| 文件 | 内容 |
|------|------|
| `current_state.md` | 当前状态卡 |
| `particle_ledger.md` | 资源账本 |
| `pending_hooks.md` | 伏笔池 |
| `chapter_summaries.md` | 章节摘要 |
| `subplot_board.md` | 支线进度板 |
| `emotional_arcs.md` | 情感弧线 |
| `character_matrix.md` | 角色交互矩阵 |

### 数据流

```
templates/          →  初始化
├── moke.json
├── story_bible.md
├── current_state.md
├── hooks.md
├── summaries.md
└── volume_outline.md

         ↓

story/              →  持续维护
├── bible.md        ←  世界观设定
├── current_state.md ←  状态追踪
├── hooks.md        ←  伏笔管理
├── summaries.md    ←  摘要记录
└── volume_outline.md ←  大纲规划

         ↓

runtime/            →  临时文件
└── plan.md         ←  章节规划

         ↓

chapters/           →  最终输出
├── chapter-0001.md
├── chapter-0002.md
└── ...
```

## 常见问题

### Q: 如何调整大纲？

A: 随时可以调整 `story/volume_outline.md`，同时在 `story/current_state.md` 中记录变更原因。

### Q: 伏笔可以废弃吗？

A: 可以，在 `story/hooks.md` 中将状态改为"废弃"并记录原因。

### Q: 摘要应该多详细？

A: 3-5 句话概括主要事件即可，详细内容看正文。

### Q: 如何保证角色一致性？

A: 系统通过 `current_state.md` 追踪角色位置、关系、状态等信息，Writer 和 Auditor 会自动检查一致性。

### Q: 可以同时写多本书吗？

A: 可以，每本书有独立的 `[book-id]` 目录和完整的状态文件。

### Q: 字数不达标怎么办？

A: Auditor 会检查字数（3000±200字），如不达标会在审计报告中标记，Reviser 会自动调整。

### Q: 如何修改章节内容？

A: 可以直接编辑 `chapters/chapter-XXXX.md` 文件，或使用 `moke:revise` 命令进行修订。

### Q: 支持哪些题材？

A: 系统支持玄幻、仙侠、都市、恐怖等多种题材，会根据题材调整写作风格。

### Q: 可以导出为其他格式吗？

A: 章节文件是 Markdown 格式，可以使用 Pandoc 等工具转换为 EPUB、PDF 等格式。

### Q: 如何备份我的作品？

A: 建议使用 Git 进行版本控制，定期提交到远程仓库。`books/` 目录包含所有重要数据。

---

## 安装使用流程

```
1. 安装 MoKe
   └──> npx moke-novel --global

2. 在 Claude Code 中使用命令
   └──> /moke:create-book

3. 开始创作
   └──> /moke:write-next
```

---

## 与 InkOS 的关系

MoKe 是基于 InkOS 构建的应用级系统。InkOS 提供了底层的 Agent 框架、命令系统和工作流引擎，MoKe 在此基础上实现了专门针对小说写作的 Agent 协作模式和状态管理机制。

**InkOS** = 底层框架（通用）
**MoKe** = 应用系统（小说写作专用）

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**MoKe - 让 AI 辅助创作更高效**
