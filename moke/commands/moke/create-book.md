---
name: moke:create-book
description: Create a new novel project with interactive configuration / 使用交互式配置创建新小说项目
---

<objective>
Create a new book project with all necessary files, genre profile, and initial settings based on InkOS architecture. Features an interactive option-based UI for easy configuration.
</objective>

<process>
1. 使用 AskUserQuestion 收集书籍信息：

   <AskUserQuestion>
   - question: "请输入书名（可选，留空则自动生成）"
     header: "书名配置"
     type: text
     required: false
     description: "可手动输入书名，或留空让系统根据题材自动生成"

   - question: "请选择题材类型"
     header: "题材选择"
     options:
       - label: "玄幻"
         value: "xuanhuan"
         description: "Eastern fantasy, cultivation system, martial arts"
       - label: "都市"
         value: "urban"
         description: "Modern city setting, romance/career focus"
       - label: "仙侠"
         value: "xianxia"
         description: "Immortal cultivation, daoist themes"
       - label: "恐怖"
         value: "horror"
         description: "Horror, suspense, supernatural elements"
       - label: "其他"
         value: "other"
         description: "Custom or mixed genre"
     multiSelect: false
     required: true

   - question: "请选择发布平台"
     header: "平台选择"
     options:
       - label: "番茄小说"
         value: "tomato"
         description: "ByteDance platform, free reading model"
       - label: "飞卢"
         value: "feilu"
         description: "Fast-paced, quick payoff style"
       - label: "起点中文网"
         value: "qidian"
         description: "Traditional web novel platform"
       - label: "其他"
         value: "other"
         description: "Other platforms or self-publishing"
     multiSelect: false
     required: false

   - question: "请输入章节字数（每章目标字数）"
     header: "章节设置"
     type: number
     default: 3000
     required: false

   - question: "请输入目标章节数"
     header: "章节规划"
     type: number
     default: 200
     required: false

   - question: "是否提供创作简报文件？（可选）"
     header: "创作简报"
     type: text
     description: "请输入 .md 或 .txt 文件路径，留空则跳过"
     required: false
   </AskUserQuestion>

   收集的变量：
   - **title** (可选) - 书名，如果为空则根据题材自动生成
   - **genre** (必填) - 题材ID
   - **platform** (可选，默认 "tomato") - 平台ID
   - **chapterWordCount** (可选，默认 3000) - 章节字数
   - **targetChapters** (可选，默认 200) - 目标章节数
   - **brief** (可选) - 创作简报文件路径

   **书名自动生成逻辑**：
   - 如果用户未输入书名（留空或跳过），系统将根据所选题材从预设列表中随机生成书名
   - 预设书名库（每个题材 10+ 个）：

   **玄幻 (xuanhuan)**：
   - 吞天魔帝、逆天废材、万古第一神、破天战神、绝世武魂、九天神皇、太古龙象、混沌剑神、霸武战神、不死武尊、荒古圣体、帝尊、武极天下、凌天战尊、万道龙皇

   **都市 (urban)**：
   - 贴身保镖、绝世高手在都市、重生之商业帝国、首席总裁、都市之神医下山、最强狂兵、豪门天价前妻、重生之财源滚滚、全能大少爷、超级兵王、都市修真高手、首席御医、豪门第一盛婚、重生之都市仙尊、逆天邪神

   **仙侠 (xianxia)**：
   - 仙路争锋、大道争仙、万古仙穹、长生界、仙逆、凡人修仙传、百炼成仙、仙傲、仙葫、我欲封天、一念永恒、三界独尊、无上杀神、踏天、永生

   **恐怖 (horror)**：
   - 午夜凶铃、诡异降临、恐怖复苏、诡秘之主、我有一座冒险屋、神秘复苏、惊悚乐园、地狱公寓、地狱APP、我有一座恐怖屋、从鬼屋开始、深夜书屋、全球崩坏、诡秘地海、恐惧瘟疫

2. 加载题材配置 (GenreProfile)：
   - 从 `genres/{genre}.md` 读取题材配置
   - 如果不存在，使用默认题材配置
   - 题材配置包含：
     - `name`: 题材名称
     - `id`: 题材ID
     - `language`: 语言 (zh/en)
     - `chapterTypes`: 章节类型列表
     - `fatigueWords`: 疲劳词列表
     - `numericalSystem`: 是否有数值系统
     - `powerScaling`: 是否有战力提升
     - `eraResearch`: 是否需要时代考证
     - `pacingRule`: 节奏规则
     - `satisfactionTypes`: 爽点类型
     - `auditDimensions`: 审计维度

3. 创建书籍目录结构：
   ```
   books/{bookId}/
   ├── .moke/
   │   └── config.json           # MoKe 配置
   ├── book.json                 # 书籍配置 (包含题材信息)
   ├── chapters/                 # 章节目录
   │   └── index.json            # 章节索引
   └── story/                    # 故事文件目录
       ├── story_bible.md        # 故事圣经
       ├── volume_outline.md     # 卷大纲
       ├── book_rules.md         # 书籍规则 (带 frontmatter)
       ├── current_state.md      # 当前状态卡
       ├── pending_hooks.md      # 伏笔池
       ├── particle_ledger.md    # 资源账本 (如有数值系统)
       ├── chapter_summaries.md  # 章节摘要
       ├── subplot_board.md      # 支线进度板
       ├── emotional_arcs.md     # 角色情感弧线
       ├── character_matrix.md   # 角色交互矩阵
       ├── author_intent.md      # 长期作者意图
       ├── current_focus.md      # 当前阶段关注点
       ├── style_guide.md        # 风格指南
       └── runtime/              # 运行时产物目录
           ├── chapter-0001.intent.md    # 章节目标 (可读)
           ├── chapter-0001.context.json  # 上下文选择
           ├── chapter-0001.rule-stack.yaml # 优先级层
           └── chapter-0001.trace.json   # 输入轨迹
   ```

   **文件夹命名规则**：
   - 直接使用书名作为文件夹名（中文或英文）
   - 如果书名包含特殊字符，替换为下划线
   - 示例：`books/吞天魔帝/` 或 `books/Sky_Swallowing_Demon_Emperor/`

   **运行时产物说明**：
   - `runtime/` 目录存储每章的运行时产物，由 `plan` 和 `compose` 命令生成
   - `chapter-XXXX.intent.md` - 章节目标文档，供人类阅读，包含本章目标、大纲节点、必须保持/避免的内容、风格强调等
   - `chapter-XXXX.context.json` - 上下文选择包，记录系统实际选择了哪些上下文文件供 LLM 使用
   - `chapter-XXXX.rule-stack.yaml` - 优先级层级，包含硬规则、软规则、诊断规则的分层结构
   - `chapter-XXXX.trace.json` - 输入轨迹，记录规划器的输入来源和选择过程，用于调试

   **控制面文档说明**：
   - `author_intent.md` - 长期作者意图，定义这本书长期想成为什么，可在创作过程中随时编辑
   - `current_focus.md` - 当前阶段关注点，定义最近 1-3 章要把注意力拉回哪里
   - 这两个文档是 InkOS 的输入治理控制面，可在写作前通过 `plan` 命令预编译生成运行时产物

4. 书名自动生成处理：
   - 如果用户未提供书名（title 为空或 null），根据题材从预设列表中随机选择
   - 将生成的书名设置到 title 变量中
   - 在输出中标注是自动生成的书名

5. 初始化配置文件：

   **book.json** 结构：
   ```json
   {
     "id": "书名（用作文件夹名）",
     "title": "书籍标题",
     "genre": "xuanhuan|urban|xianxia|horror|other",
     "platform": "tomato|feilu|qidian|other",
     "targetChapters": 200,
     "chapterWordCount": 3000,
     "language": "zh",
     "createdAt": "ISO_DATE",
     "updatedAt": "ISO_DATE",
     "genreProfile": {
       "name": "题材名称",
       "id": "题材ID",
       "chapterTypes": ["章节类型列表"],
       "fatigueWords": ["疲劳词列表"],
       "numericalSystem": true/false,
       "powerScaling": true/false,
       "eraResearch": true/false,
       "pacingRule": "节奏规则",
       "satisfactionTypes": ["爽点类型"],
       "auditDimensions": [维度编号]
     }
   }
   ```

6. 处理创作简报（可选）：
   - 如果提供了 `--brief <file>` 参数
   - 读取简报内容
   - 传递给 Architect 作为 externalContext
   - 用于生成初始世界观设定

7. 创建运行时目录和控制面文档：
   - 创建 `story/runtime/` 目录（用于存储章节运行时产物）
   - 初始化 `author_intent.md` 模板（长期作者意图）
   - 初始化 `current_focus.md` 模板（当前阶段关注点）
   - 生成带 frontmatter 的 `book_rules.md` 模板

8. 创建 `.moke/config.json` 配置文件：

   **重要**：使用正确的格式！

   ```json
   {
     "mode": "interactive",
     "granularity": "standard",
     "modelProfile": "balanced"
   }
   ```

   **mode 选项**：
   - `yolo` - 自动执行，无需确认（推荐用于批量写作）
   - `interactive` - 每步确认（默认）

8. 从 templates/ 复制并初始化真相文件：
   - current_state.md
   - pending_hooks.md
   - chapter_summaries.md
   - subplot_board.md
   - emotional_arcs.md
   - character_matrix.md
   - particle_ledger.md (仅当题材有数值系统时)

   **book_rules.md 模板结构**：
   ```markdown
   ---
   # 书籍规则配置 (Frontmatter)
   protagonist_archetype: "hero"  # 主角原型
   power_cap: "immortal"          # 战力上限
   custom_bans:                   # 自定义禁令
     - "time_travel"
     - "modern_technology_in_ancient"
   narrative_voice: "third_person_limited"  # 叙事视角
   pacing_style: "fast"           # 节奏风格
   ---

   # 书籍级创作规则

   ## 主角人设约束
   - 主角性格特征
   - 行为模式限制

   ## 数值上限
   - 战力体系说明
   - 等级划分规则

   ## 自定义禁令
   - 禁止出现的设定
   - 避免使用的桥段
   ```

9. 生成初始世界观设定（可选）

10. 输出创建结果和下一步指引
   - 如果书名是自动生成的，在输出中特别标注
</process>

## 使用方式

### 交互式创建（推荐）

```bash
/moke:create-book
```

执行后，系统将通过选项式交互引导你完成配置：
1. 📝 **输入书名（可选）** - 可手动输入，或留空自动生成
2. 🎭 **选择题材** - 从选项中选择（玄幻/都市/仙侠/恐怖/其他）
3. 🌐 **选择平台** - 从选项中选择（番茄/飞卢/起点/其他）
4. 📊 **设置章节字数** - 数字输入（默认 3000）
5. 📚 **设置目标章节数** - 数字输入（默认 200）
6. 📋 **创作简报** - 可选，输入文件路径或留空

#### 命令行参数模式（快速创建）

```bash
# 基本用法（自动生成书名）
/moke:create-book

# 指定书名
/moke:create-book "书名"

# 指定题材和平台
/moke:create-book "书名" --genre urban --platform qidian

# 指定章节参数
/moke:create-book "书名" --chapter-words 2500 --target-chapters 300

# 使用创作简报
/moke:create-book "书名" --brief ./brief.md

# 完整示例
/moke:create-book "废材逆天：从零开始" \
  --genre xuanhuan \
  --platform tomato \
  --chapter-words 3000 \
  --target-chapters 200 \
  --brief ./story-idea.md
```

> **提示**：交互式模式提供更好的用户体验，推荐使用！

## 题材列表

内置题材（从 `genres/` 目录加载）：
- `xuanhuan` - 玄幻
- `urban` - 都市
- `xianxia` - 仙侠
- `horror` - 恐怖
- `other` - 其他

使用 `/moke:genre-list` 查看所有可用题材。

## 平台列表

- `tomato` - 番茄小说（默认）
- `feilu` - 飞卢
- `qidian` - 起点中文网
- `other` - 其他平台

## 创作规则体系

MoKe 基于 InkOS 架构，采用三层创作规则体系：

### 1. 通用创作规则（25条）
内置的核心规则，适用于所有题材：
- **人物塑造**：角色记忆连续性、行为一致性、成长轨迹合理性
- **叙事技法**：视角稳定性、场景转换自然度、对话驱动引导
- **逻辑自洽**：世界观设定冲突检测、战力体系一致性、时间线逻辑
- **语言约束**：去AI味规则、词汇疲劳检测、句式多样性
- **去AI味**：高频词规避、禁用句式、文风指纹注入

### 2. 题材专属规则
从题材配置文件（`genres/{genre}.md`）加载：
- **禁忌规则**：特定题材禁止出现的设定或桥段
- **疲劳词表**：该题材高频滥用的词汇，需避免重复
- **章节类型**：定义该题材支持的各种章节类型（如战斗、升级、日常等）
- **节奏规则**：该题材的推荐节奏模式和爽点分布

### 3. 书级规则（book_rules.md）
每本书独有的规则，通过 frontmatter 配置：
```yaml
---
protagonist_archetype: "hero"    # 主角原型
power_cap: "immortal"            # 战力上限
custom_bans:                     # 自定义禁令
  - "time_travel"
narrative_voice: "third_person_limited"  # 叙事视角
pacing_style: "fast"             # 节奏风格
---
```

书级规则优先级最高，可以覆盖题材规则和通用规则。

## 控制面与运行时产物

### 控制面文档（长期可编辑）
- **author_intent.md**：这本书长期想成为什么
  - 定义核心创作理念
  - 设定长期叙事目标
  - 可在创作过程中随时编辑

- **current_focus.md**：最近 1-3 章要把注意力拉回哪里
  - 短期创作重点
  - 需要特别关注的支线或冲突
  - 临时调整的叙事方向

### 运行时产物（每章生成）
在 `story/runtime/` 目录下，每章生成四个文件：
- **chapter-XXXX.intent.md**：章节目标（人类可读）
  - 本章具体目标
  - 大纲节点对齐
  - 必须保持/避免的内容
  - 风格强调要求

- **chapter-XXXX.context.json**：上下文选择（系统使用）
  - 记录系统实际选择了哪些上下文文件
  - 权重分配信息
  - 供调试和分析使用

- **chapter-XXXX.rule-stack.yaml**：优先级层级（规则执行）
  - 硬规则（hard）：必须遵守的约束
  - 软规则（soft）：建议性指导
  - 诊断规则（diagnostic）：审计维度

- **chapter-XXXX.trace.json**：输入轨迹（调试用）
  - 记录规划器的输入来源
  - 选择过程和决策依据
  - 用于问题诊断和优化

### 工作流程
```bash
# 1. 更新控制面（可选）
/moke:set-author-focus "本章先把注意力拉回师徒矛盾"

# 2. 规划章节（生成运行时产物）
/moke:plan-chapter

# 3. 创作章节
/moke:compose-chapter

# 4. 审计和修订
/moke:audit
/moke:revise
```

控制面文档可以在写作前先编辑，`plan` 和 `compose` 命令会编译这些文档生成运行时产物，即使没有配置好 API Key 也可以预览系统将如何工作。
