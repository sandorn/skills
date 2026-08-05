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
- 是否有已有项目（检测 `novel.json` / `writer.json` / `setting/` + `chapters/`）→ 不覆盖
- 确认项目输出目录（默认当前工作目录）
- **确认 `novel_project` MCP 可达**（未连通时提示先修复；见 `references/memory-mcp.md`）

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

## Step 4：生成项目骨架（v8.4 精简架构）

```bash
mkdir -p {project}/setting {project}/outline/chapter_outline {project}/chapters \
         {project}/.writer/runtime
```

### 三层职责结构（v8.4 去除 tracking/ 与 .writer/state/）

```
{project}/
├── novel.json                # 项目根标记（含 memory_mcp: novel_project）
├── .mcp.json                 # 项目级 MCP 配置（一书一库，见 memory-mcp.md §7.2）
├── setting/                  # 用户领地：静态设定原稿（seed MCP 的原始出处）
│   ├── story_bible.md
│   ├── characters.md
│   ├── power_system.md
│   ├── factions.md
│   └── writing_rules.md      # 可选：项目声音卡
├── outline/                  # 用户领地：大纲
│   ├── master_outline.md
│   ├── volume_outline.md
│   └── chapter_outline/      # 章纲（每章一个）
├── chapters/                 # 产出：正文（ch_NNN.md 三位数补零）
├── memory/                   # novel_project.db（Agent 独写，MCP 自动创建）
└── .writer/
    └── runtime/              # 临时文件（.gitignore）
```

> **当前状态数据（人物/势力/伏笔/剧情节点）不落在 setting/ 里**，统一存 `novel_project` MCP，落盘本书自己的 `memory/novel_project.db`（一书一库，配置见 `memory-mcp.md` §7）。

### 三层写权限

| 层 | 谁写 | 谁改 | 用途 |
|---|---|---|---|
| **`novel_project` MCP** | Agent 独写（`archive_facts.py` 生成 payload → Agent 调 MCP）| 只 Agent | 原子事实源 + 关系图谱，续写前查询 |
| `setting/*.md` | Agent 初始化 + 用户手改（含 `<!-- user-edit -->` 块） | 用户为主 | 世界观/角色的静态约束（seed MCP 的原稿） |
| `chapters/*.md` | Agent 主写 | 用户可修 | 正文 |
| `outline/*.md` | Agent 生成 + 用户改 | 双方 | 大纲 |

### 创建以下文件

| 文件 | 初始内容 |
|------|------|
| `novel.json` | 项目状态（stage=scaffold，含 `"memory_mcp": "novel_project"`）|
| `.mcp.json` | 项目级 MCP 配置，照抄 `memory-mcp.md` §7.2（`SQLITE_DB_PATH` 必须是相对路径 `./memory/novel_project.db`）|
| `setting/story_bible.md` | 世界观基础 |
| `setting/characters.md` | 主角+基础角色卡 |
| `setting/power_system.md` | 力量/等级体系 |
| `setting/factions.md` | 势力关系 |
| `setting/writing_rules.md` | 项目声音卡（可选，从波次 3 主角性格生成）|
| `outline/master_outline.md` | 核心冲突 + 结局方向 |
| `.writer/runtime/.gitkeep` | 占位 |

> **无需创建 `.writer/state/*.json` 骨架**（v8.4 起该层已废，数据全走 MCP）。
> **无需创建 tracking/ 目录**（人读快照按需用 `report_graph.py` 从 MCP 派生）。

### novel.json 初始化

```json
{
  "_comment": "writer + novel-pipeline 统一项目根标记",
  "project_name": "{书名}",
  "author": "{作者}",
  "genre": "{题材}",
  "platform": "{平台}",
  "chapters_total": {目标章节数},
  "chapters_done": 0,
  "current_chapter": 0,
  "current_volume": 1,
  "words_per_chapter": {每章字数},
  "chapter_dir": "./chapters/",
  "setting_dir": "./setting/",
  "outline_dir": "./outline/",
  "memory_mcp": "novel_project",
  "polish_toggle": true,
  "auto_skip_transition_chapters": true,
  "stage": "scaffold",
  "skill_version": "8.4",
  "last_action": "init",
  "created_at": "{当前时间}",
  "updated_at": "{当前时间}"
}
```

---

## Step 5：填充核心设定 + 首批 MCP seed

Agent 根据波次 2-3 收集的信息初始化 `setting/*.md` 骨架，**并同步 seed `novel_project` MCP**：

```
setting/characters.md 里每个人物   → create_entities(entityType="人物")
setting/factions.md 里每个势力     → create_entities(entityType="势力")
setting/power_system.md 每层境界   → create_entities(entityType="境界")
                        每种功法   → create_entities(entityType="功法")
setting/story_bible.md 关键地点    → create_entities(entityType="地点")
                       世界规则   → create_entities(entityType="世界规则", name="世界规则:xxx")
```

然后用 `create_relations` 建立首批关系：
- 主角/配角 → 所属势力（`所属`）
- 势力 → 位于地点（`位于`）
- 主角 → 师父（`师承`）、修习功法（`修习`）
- 主角 → 已知敌对/盟友势力

**注意**：`setting/*.md` 是**用户人读源**，写成完整的 markdown 描述（含世界观框架、主角背景、金手指规则）；MCP 里存的是**结构化实体 + chSEED 前缀观测**（如 `chSEED: 修为 练气一层`）。

seed 完成后调 `read_graph` 抽查：应至少返回主角+配角 3-5 个人物、2-3 个势力、3+ 层境界、若干地点。

---

## Step 6：确认 + 收尾

展示已创建的项目结构 + 关键文件摘要 + MCP seed 统计。

```
项目骨架已创建：
  - 5 个 setting/*.md
  - novel.json（stage=scaffold）
  - novel_project MCP 已 seed：{N}实体 + {M}关系

下一步：
1. 完善设定 → 扩展 setting/ 目录下的文件（记得同步补 MCP 实体）
2. 规划大纲 → plan
3. 直接开写 → write 第1章（写前会自动查 MCP 拉主要角色状态）
```

---

## 成功标准

- [ ] 项目目录结构完整（5 个 setting/*.md + outline/ + chapters/ + .writer/runtime/）
- [ ] `novel.json` 格式合法，字段齐备（含 `memory_mcp`）
- [ ] `.mcp.json` 已创建，`SQLITE_DB_PATH` 为相对路径；`~/.claude.json` 顶层无同名 `novel_project` 残留
- [ ] `setting/story_bible.md` 包含世界观类型和核心规则
- [ ] `setting/characters.md` 包含主角基本信息
- [ ] `outline/master_outline.md` 包含核心冲突和结局方向
- [ ] `novel_project` MCP 已 seed（**在书目录内**启动 claude 后 `read_graph` 返回主角+主要势力+境界体系）

---

## import 模式：导入旧稿

触发词：「导入小说」「把我的书导进来」「迁移」。

**支持的老结构类型**：
- 单个 `.md/.txt` 长文 → 按章节切分
- 一组 `ch_NNN.md` / `chNN.md` / 章节.md → 直接采纳，重命名为标准格式
- 老 novel-pipeline 项目（`state-files/*.json` + `novel-pipeline.json`）→ 迁移到新架构
- 老 writer v8.2 / v8.3 项目（`.writer/state/*.json`）→ 一次性迁移到 MCP

### 迁移映射表

| 老结构 | 新结构 |
|---|---|
| `novel-pipeline.json` / `writer.json` | 保留（三种 marker 都被识别），或 `git mv` 为 `novel.json` |
| `state-files/*.json` (老 novel-pipeline) | 用 `import_state_to_mcp.py` 灌入 MCP 后删除 |
| `.writer/state/*.json` (v8.3 writer) | 用 `import_state_to_mcp.py` 灌入 MCP 后删除 |
| `tracking/*.md` (v8.3 writer) | 用户手抄的 `<!-- user-edit -->` 块挪到 `setting/*.md` 对应文件；派生表格丢弃 |
| `chXX.md` / `chXXX.md` | `git mv` 为 `ch_NNN.md` |
| `chapters_polished/` | 删除（新架构原地覆盖）|

### 流程
1. 识别输入类型
2. 创建 Writer v8.4 标准目录结构（不覆盖已有正文）
3. 迁移映射（如上表）
4. **一次性 MCP 迁移**：
   ```bash
   python <writer>/scripts/import_state_to_mcp.py --project-root <path>
   # 输出 tool_calls → Agent 按顺序调 create_entities/create_relations
   # 完成后调 read_graph 抽查实体数是否与 stats.total_entities 相符
   ```
5. 从正文反推补充：主角、重要配角、伏笔、章节摘要（可选，交给用户确认后写入 setting/ 与 MCP）
6. 生成导入报告：已识别章节数、缺失设定、疑似断章、MCP 导入统计、下一步建议

---

> **下一步**：[大纲规划](plan.md)（总纲→卷纲→章纲）；写第一章前用 `references/memory-mcp.md` 复核 MCP seed 是否合理
