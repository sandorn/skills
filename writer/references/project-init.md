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

## Step 4：生成项目骨架（新架构 v8.3）

```bash
mkdir -p {project}/setting {project}/outline/chapter_outline {project}/chapters \
         {project}/tracking {project}/.writer/state {project}/.writer/runtime
```

### 四层职责结构

```
{project}/
├── novel.json                # 项目根标记（新架构统一用 novel.json）
├── setting/                  # 用户领地：静态约束（世界观/角色/战力）
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
├── tracking/                 # 【Agent 派生渲染】进度笔记
│   ├── characters.md         # 从 .writer/state/characters.json 渲染
│   ├── hooks.md              # 从 .writer/state/foreshadowing.json 渲染
│   └── current_state.md      # 当前状态快照（派生）
└── .writer/
    ├── state/                # 【Agent 归档写入】原子事实（机读源）
    │   ├── characters.json   # {"version": 1, "characters": []}
    │   ├── foreshadowing.json
    │   ├── power_system.json
    │   └── world_setting.json
    ├── project_memory.json   # skill 学到的项目习惯
    └── runtime/              # 临时文件（.gitignore）
```

### 四层写权限

| 层 | 谁写 | 谁改 | 用途 |
|---|---|---|---|
| `.writer/state/*.json` | Agent 独写（`scripts/archive_facts.py`）| 只 Agent | 原子事实源，程序读 |
| `tracking/*.md` | Agent 派生（`scripts/render_tracking.py`）| 用户可在 `<!-- user-edit -->` 块内增补 | 人读快照 |
| `setting/*.md` | Agent 初始化 + 用户手改 | 用户为主 | 世界观/角色的静态约束 |
| `chapters/*.md` | Agent 主写 | 用户可修 | 正文 |
| `outline/*.md` | Agent 生成 + 用户改 | 双方 | 大纲 |

### 创建以下文件

| 文件 | 初始内容 |
|------|------|
| `novel.json` | 项目状态（stage=scaffold）|
| `setting/story_bible.md` | 世界观基础 |
| `setting/characters.md` | 主角+基础角色卡 |
| `setting/power_system.md` | 力量/等级体系 |
| `setting/factions.md` | 势力关系 |
| `setting/writing_rules.md` | 项目声音卡（可选，从波次 3 主角性格生成）|
| `outline/master_outline.md` | 核心冲突 + 结局方向 |
| `.writer/state/characters.json` | `{"version": 1, "characters": []}` |
| `.writer/state/foreshadowing.json` | `{"version": 1, "active": [], "resolved": []}` |
| `.writer/state/power_system.json` | `{"version": 1, "realms": [], "equipment": [], "combat_rules": []}` |
| `.writer/state/world_setting.json` | `{"version": 1, "factions": [], "geography": [], "special_rules": []}` |
| `.writer/runtime/.gitkeep` | 占位 |

**tracking/ 目录初始为空**——用户第一次写章后由 `render_tracking.py` 自动生成。

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
  "tracking_dir": "./tracking/",
  "state_dir": "./.writer/state/",
  "polish_toggle": true,
  "auto_skip_transition_chapters": true,
  "stage": "scaffold",
  "skill_version": "8.3",
  "last_action": "init",
  "created_at": "{当前时间}",
  "updated_at": "{当前时间}"
}
```

---

## Step 5：填充核心设定

Agent 根据波次 2-3 收集的信息初始化 `setting/*.md` 骨架 + `.writer/state/*.json` 骨架。

**注意**：setting/*.md 是**用户人读源**，写成完整的 markdown 描述（含世界观框架、主角背景、金手指规则）；.writer/state/*.json 保留空数组，等第一次写章由 `archive_facts.py` 自动填充。

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

- [ ] 项目目录结构完整（8 个目录 + 11 个文件）
- [ ] `novel.json` 格式合法，字段齐备（含 state_dir）
- [ ] `setting/story_bible.md` 包含世界观类型和核心规则
- [ ] `setting/characters.md` 包含主角基本信息
- [ ] `outline/master_outline.md` 包含核心冲突和结局方向
- [ ] `.writer/state/*.json` 4 个骨架文件已创建（空数组）
- [ ] `.writer/runtime/` 目录存在

---

## import 模式：导入旧稿

触发词：「导入小说」「把我的书导进来」「迁移」。

**支持的老结构类型**：
- 单个 `.md/.txt` 长文 → 按章节切分
- 一组 `ch_NNN.md` / `chNN.md` / 章节.md → 直接采纳，重命名为标准格式
- 老 novel-pipeline 项目（`state-files/*.json` + `novel-pipeline.json`）→ 迁移到新架构
- 老 writer v8.2 项目（`writer.json` + 无 `.writer/state/`）→ 补建 state 骨架

### 迁移映射表

| 老结构 | 新结构 |
|---|---|
| `novel-pipeline.json` / `writer.json` | 保留（三种 marker 都被识别），或 `git mv` 为 `novel.json` |
| `state-files/*.json` | `git mv` 到 `.writer/state/*.json` |
| `chXX.md` / `chXXX.md` | `git mv` 为 `ch_NNN.md` |
| `chapters_polished/` | 删除（新架构原地覆盖）|

### 流程
1. 识别输入类型
2. 创建 Writer v8.3 标准目录结构（不覆盖已有正文）
3. 迁移映射（如上表）
4. 从正文反推：主角、重要配角、伏笔、章节摘要（可选，交给用户确认后写入 setting/ 与 .writer/state/）
5. 生成导入报告：已识别章节数、缺失设定、疑似断章、下一步建议

---

> **下一步**：[大纲规划](plan.md)（总纲→卷纲→章纲）
