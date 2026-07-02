# 项目初始化：创建新书

---

## 执行原则

1. **先收集，再生成。** 未过充分性闸门，不创建任何项目文件。
2. **智能默认 + 仅问阻塞项。** 以下自动推定，用户不说才问：
   - 平台 → 番茄小说
   - 每章字数 → 3000
   - 目标章节数 → 60（一卷）/ 300（标准长篇）
   - 书名 → 从用户描述中提取关键词组合
3. **从扫榜结果出发。** 如果已有 `选题决策.md`，直接读取。
4. **单轮收集优先。** 用户一句话给了书名+题材+梗概 → 不再追问波次 1-3，直接进入充分性闸门。

---

## Step 1：预检

- 是否有 `选题决策.md` → 读取作为开书依据
- 是否有已有项目（检测 `writer.json` + `setting/` + `chapters/`）→ 不覆盖
- 确认项目输出目录（默认当前工作目录）

---

## Step 2：收集基础信息

分波次收集，用户已在自然语言中给出的答案不再追问。

### 波次 1：书籍定位
1. **书名**（可选，留空则自动生成）
2. **题材**：玄幻 / 都市 / 仙侠 / 科幻 / 恐怖 / 历史 / 悬疑 / 其他
3. **目标平台**：番茄小说 / 飞卢 / 起点中文网 / 晋江 / 知乎盐选 / 其他

### 波次 2：写作目标
4. **作者笔名**
5. **目标总字数或章节数**
6. **每章字数**（默认 3000）
7. **一句话梗概**

### 波次 3：核心人设
8. **主角名字 + 性格底色**（如：林北，隐忍但有底线）
9. **金手指/核心设定**—— 仅确认类型和名称。涉及跨界物品时触发波次 4
10. **对标书（可选）**

### 波次 4：金手指细化（跨界物品时触发）

**先定义作用，再讨论价格。**

1. 代价机制：身体代价 vs 资源代价 — 二选一
2. 权限体系：等级/每日额度/首次解锁费
3. 物品作用逐类：药水→装备→首饰→特殊物品→材料→属性同步
4. 汇总确认
5. 最后讨论售价

每轮只问一个决策点，给出 2-4 个候选方案。

---

## Step 3：充分性闸门

- [ ] 题材已确认
- [ ] 平台已确认
- [ ] 核心设定已确认（主角+金手指）
- [ ] 目标规模已确认

**缺失任何一项 → 阻断，追问。**

---

## Step 4：生成项目骨架

```bash
mkdir -p {project}/setting {project}/outline/chapter_outline {project}/chapters \
         {project}/tracking {project}/.writer/runtime {project}/analysis_lib \
         {project}/cover
```

创建以下文件（模板见 `templates/project-skeleton/`）：

| 文件 | 内容 |
|------|------|
| `writer.json` | 项目状态（stage=scaffold） |
| `setting/story_bible.md` | 世界观基础 |
| `setting/characters.md` | 主角+基础角色卡 |
| `setting/power_system.md` | 力量/等级体系 |
| `setting/factions.md` | 势力关系 |
| `outline/master_outline.md` | 核心冲突 + 结局方向 |
| `tracking/current_state.md` | 角色初始状态 |
| `tracking/hooks.md` | 伏笔池（空） |
| `tracking/chapter_summaries.md` | 章节摘要（空） |
| `tracking/subplot_board.md` | 支线进度板（空） |
| `tracking/emotional_arcs.md` | 情绪弧线（空） |
| `tracking/resource_ledger.md` | 资源账本（空） |

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
  "skill_version": "8.1",
  "last_action": "init",
  "created_at": "{当前时间}",
  "updated_at": "{当前时间}"
}
```

知识图谱就绪：
```
memory-novel MCP 在首次调用时自动创建知识图谱（npx @pepk/mcp-memory-sqlite）。
无需手动 init。数据库文件位于 ./novel_memory_db/。
初始实体：从 setting/characters.md 提取角色 → create_entities
```

---

## Step 5：填充核心设定

| 文件 | 内容 |
|------|------|
| `setting/story_bible.md` | 世界观类型 + 核心规则（从题材推导默认框架） |
| `setting/power_system.md` | 等级体系（入门→进阶→高阶→巅峰，如适用） |
| `setting/characters.md` | 主角信息（姓名+底色+金手指），配角留空后续补充 |
| `outline/master_outline.md` | 核心冲突 + 主角弧线 + 结局方向 + 第一卷目标 |

---

## Step 6：确认 + 收尾

展示已创建的项目结构 + 关键文件摘要。

```
项目骨架已创建。下一步：
1. 完善设定 → 扩展 setting/ 目录下的文件
2. 规划大纲 → plan
3. 直接开写 → write 第1章
```

---

## 成功标准

- [ ] 项目目录结构完整
- [ ] `writer.json` 格式合法，字段齐备
- [ ] `setting/story_bible.md` 包含世界观类型和核心规则
- [ ] `setting/characters.md` 包含主角基本信息
- [ ] `outline/master_outline.md` 包含核心冲突和结局方向
- [ ] `tracking/` 下 6 个追踪文件已创建

---

## import 模式：导入旧稿

触发词：「导入小说」「把我的书导进来」「迁移」。

流程：
1. 识别输入：单个 `.md/.txt`、一组章节文件、或已有项目目录
2. 判断篇幅：短篇走单篇结构化；长篇按章节切分
3. 创建 Writer 标准目录结构，不覆盖已有正文
4. 从正文反推：主角、重要配角、世界观、力量/系统、伏笔、章节摘要
5. 写入 `setting/`、`outline/`、`tracking/`
6. 生成导入报告：已识别章节数、缺失设定、疑似断章、下一步建议

---

> **下一步**：[大纲规划](plan.md)（总纲→卷纲→章纲）
