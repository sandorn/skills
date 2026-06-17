# 项目初始化：深度交互式创建新书

改编自 webnovel-init（lingfengQAQ）+ moke create-book + story-long-write Phase 1-2。

---

## 执行原则

1. **先收集，再生成。** 未过充分性闸门，不创建任何项目文件。
2. **分波次提问，每轮只问当前缺失且会阻塞下一步的信息。** 用户已明确的不重复问。
3. **从扫榜结果出发。** 如果已有 `选题决策.md`，直接读取作为初始依据。

---

## Step 1：预检

检查当前目录/工作空间：

- 是否有 `选题决策.md` → 读取作为开书依据
- 是否有已有项目（检测 `writer.json`、`project-state.json`、`设定/正文/追踪`）→ 默认兼容，不覆盖
- 确认项目输出目录（默认当前目录/工作目录）

---

## Step 2：收集基础信息

用 `clarify` 分波次收集，不要一次问完。若用户已在自然语言中给出答案，不重复追问。

### 波次 1：书籍定位

1. **书名**（可选，留空则自动生成）
2. **题材**：玄幻 / 都市 / 仙侠 / 科幻 / 恐怖 / 历史 / 悬疑 / 其他
3. **目标平台**：番茄小说 / 飞卢 / 起点中文网 / 晋江 / 知乎盐选 / 其他

### 波次 2：写作目标

4. **作者笔名**（默认从 writer.json 或上次记录自动读取）
5. **目标总字数或章节数**
6. **每章字数**（默认 3000）
7. **一句话梗概**（这本书的核心是什么）

### 波次 3：核心人设（只问关键，不强求完整）

7. **主角名字 + 性格底色**（如：林北，隐忍但有底线）
8. **金手指/核心设定**（如：签到系统、重生、系统商城）
9. **对标书（可选）**：有没有想参考的书？

---

## Step 3：充分性闸门

在创建任何文件之前，确认以下信息齐备：

- [ ] 题材已确认
- [ ] 平台已确认
- [ ] 核心设定已确认（主角+金手指）
- [ ] 目标规模（章节数或字数）已确认

**缺失任何一项 → 阻断，追问，不跳过。**

---

## Step 4：生成项目骨架

创建目录结构：

```
{project}/
├── writer.json              # Project config
├── setting/
│   ├── story_bible.md        # 世界观基础（模板：templates/project-skeleton/story_bible.md）
│   ├── characters.md         # MC + 基础角色（模板：templates/project-skeleton/characters.md）
│   ├── power_system.md       # 力量体系，如适用（模板：templates/project-skeleton/power_system.md）
│   └── factions.md           # 势力关系，如适用（模板：templates/project-skeleton/factions.md）
├── outline/
│   └── master_outline.md     # Core conflict + ending direction
├── tracking/
│   ├── current_state.md
│   ├── hooks.md
│   ├── chapter_summaries.md
│   ├── subplot_board.md
│   ├── emotional_arcs.md
│   └── resource_ledger.md
├── chapters/                 # Empty dir
└── .writer/
    └── state.json
```

如果用户要求兼容旧 story/webnovel 项目，或当前工作区已有中文结构，则创建/沿用：

```
{project}/
├── project-state.json
├── README.md
├── 设定/
├── 大纲/
├── 正文/
├── 追踪/
└── runtime/
```

不要在旧项目中强制复制一套英文目录，除非用户明确要求迁移。

### writer.json 初始化

```json
{
  "project": "{书名}",
  "author": "{作者}",
  "stage": "scaffold",
  "genre": "{题材}",
  "platform": "{平台}",
  "chapters_total": {目标章节数},
  "chapters_done": 0,
  "words_per_chapter": {每章字数},
  "current_volume": 1,
  "current_chapter": 0,
  "last_action": "init",
  "created_at": "{当前时间}",
  "updated_at": "{当前时间}"
}
```

---

## Step 5：填充核心设定

基于收集的信息，填充以下文件：

### story_bible.md —— 世界观基础

从题材推导基本世界观设定：

| 题材 | 默认世界观 |
|------|-----------|
| 玄幻 | 异世界 + 修炼体系 + 多势力 |
| 都市 | 现代都市 + 异能/系统/重生 |
| 仙侠 | 修真界 + 师徒/宗门 + 飞升体系 |
| 科幻 | 未来/星际 + 科技/超能力 |
| 恐怖 | 现实世界 + 超自然元素 |
| 历史 | 特定朝代 + 权谋/战争 |
| 悬疑 | 现实/封闭环境 + 谜团 |

### power_system.md —— 等级设计（如适用）

| 等级名称 | 描述 | 战力参照 |
|---------|------|---------|
| 入门 | | |
| 进阶 | | |
| 高阶 | | |
| 巅峰 | | |

### characters.md —— 角色卡

填写主角信息，其他角色留空后续补充。

### master_outline.md —— 核心冲突 + 结局方向

```markdown
# 总纲

## 核心冲突

一句话概括全书核心冲突：

## 主角弧线

从\_\_\_\_到\_\_\_\_（性格变化方向）

## 结局方向

- 喜剧/悲剧/开放式
- 主角最终状态：

## 第一卷核心目标

## 全书主要情节线（可选）
```

---

## Step 6：确认 + 收尾

向用户展示已创建的项目结构。

关键文件内容摘要：

- **story_bible**：世界观类型+核心规则
- **characters**：主角姓名+底色+金手指
- **master_outline**：核心冲突+结局方向

提示用户下一步可以做什么：
```
项目骨架已创建。下一步：
1. 完善设定 → 扩展/修改 设定/ 目录下的文件
2. 规划大纲 → 运行 /writer（plan）
3. 直接开写 → 运行 /writer（write --help）
```

---

## 成功标准

- [ ] 项目目录结构完整
- [ ] writer.json 格式合法，字段齐备
- [ ] 故事圣经包含世界观类型和核心规则 -> story_bible
- [ ] 角色矩阵包含主角基本信息 -> characters
- [ ] 总纲包含核心冲突和结局方向 -> master_outline
- [ ] 7个追踪文件已创建（可空的骨架）-> tracking/*.md

---

## import 模式：导入旧稿/旧项目

当用户说「导入小说」「反向解析」「把我的书导进来」「迁移旧项目」时触发。

流程：

1. 识别输入：单个 `.md/.txt`、一组章节文件、或已有项目目录
2. 判断篇幅：短篇走单篇结构化；长篇按章节切分
3. 创建或补齐项目骨架，不覆盖已有正文
4. 从正文反推：主角、重要配角、世界观、力量/系统、伏笔、章节摘要
5. 写入 `设定/`、`大纲/`、`追踪/` 或对应英文目录
6. 生成导入报告：已识别章节数、缺失设定、疑似断章、下一步建议

导入模式默认保守：只新增缺失文件，不改用户原稿。
