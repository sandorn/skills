# 写作管线：长篇/短篇/批量

改编自 Moke 9-Agent 管线 + story-long-write 情绪驱动 + webnovel-write 量产流水线。

---

## 模式选择

| 模式 | 命令示例 | 说明 |
|------|---------|------|
| **默认模式** | `write 第5章` | 5 步日更管线：Plan → Architect → Write+Reflect → Audit+Normalize → Revise |
| **完整模式** | `write 第5章 --full` | 展开 Moke 9 步完整管线 |
| **轻量模式** | `write 第5章 --fast` | 跳过 Observer/Reflector/Normalizer |
| **批量模式** | `write --batch 3` | 一次性规划，批量写入 |
| **短篇模式** | `write --short` | 短篇小说写作 |
| **快速短篇** | `write --short --fast` | 情绪驱动 + 快速出稿 |

---

## 执行前预检

在开始任何写章之前：

> **注意：** 以下伪代码是执行逻辑参考，不可直接在 Hermes 环境中运行（Hermes 使用 `read_file`/`search_files`/`patch` 等工具替代 `open()`/`exit()`）。实际执行时按上方工具映射表转换。

```python
import json, os

project_root = "."

# 检查项目：优先 writer.json，兼容旧 project-state.json
state_path = os.path.join(project_root, "writer.json")
if not os.path.exists(state_path):
  legacy_state = os.path.join(project_root, "project-state.json")
  if os.path.exists(legacy_state):
    state_path = legacy_state
  else:
    print("ERROR: 没有找到 writer.json 或 project-state.json，请先运行 project-init")
    exit(1)

with open(state_path, 'r', encoding='utf-8') as f:
    state = json.load(f)

# 检查大纲：新结构 outline/chapter_outline，旧结构 大纲
outline_chapter_dir = os.path.join(project_root, "outline", "chapter_outline")
if not os.path.exists(outline_chapter_dir):
  outline_chapter_dir = os.path.join(project_root, "大纲")
ch = state.get("current_chapter", 0) + 1
ch_outline = os.path.join(outline_chapter_dir, f"ch_{ch:03d}.md")

if not os.path.exists(ch_outline) and state.get("stage") != "planning":
    print(f"WARNING: 第{ch}章章纲不存在。先运行 plan 还是直接写？")
```

如果 stage 为 `scaffold`（刚初始化），提示先运行 plan：

```
项目还在 scaffold 阶段，建议先生成章纲。直接写也可以，但质量可能不如有章纲。
确认直接写吗？ (y/N)
```

---

## 默认模式：5 步日更管线

适用于：日更续写、普通单章写作、用户没有要求全量审计时。

### Step 1：Plan

确认章节号、字数目标、核心事件、情绪目标、必须包含、必须避免、章末钩子。优先读取：

- `outline/chapter_outline/ch_NNN.md` 或 `大纲/` 下对应章纲
- `writer.json` 或 `project-state.json`
- `tracking/current_state.md` 或 `追踪/当前状态.md`

### Step 2：Architect

合并原 Moke Composer + Architect：整理角色、设定、伏笔、时间锚点，并生成章节结构。

### Step 3：Write + Reflect

写正文到 `chapters/ch_NNN.md` 或旧结构 `正文/chNN-标题.md`。写完后提取角色位置、状态、资源、伏笔和章节摘要。

### Step 4：Audit + Normalize

执行 review solo 的核心检查，同时验证字数、段落、硬性禁令和 AI 痕迹。

### Step 5：Revise

只修 blocking 问题、用户明确关注的问题和明显影响可发布的问题。修订后再跑一次关键禁令扫描。

## 完整模式（--full）：9 步完整管线

适用于：长篇单章写作，首次执行某章。

### 准备工作

读取上下文：

- `writer.json` / `project-state.json` — 项目配置
- `outline/chapter_outline/ch_NNN.md` / `大纲/` — 本章章纲
- `tracking/current_state.md` / `追踪/当前状态.md` — 角色位置/状态
- `tracking/hooks.md` / `追踪/伏笔池.md` — 待处理伏笔
- `setting/story_bible.md` / `设定/世界观.md` — 世界观约束
- `setting/characters.md` / `设定/主角.md` — 角色信息

### Step 1：Planner —— 章节规划

在内存中生成章节意图（不写临时文件）：

```
章节号：{N}
字数目标：3000
核心目标：[一句话]
情绪目标：[爽/紧张/反转/温情]
必须保留：[列表中元素的延续]
必须避免：[需要绕开的雷区]
冲突设计：
  - 主冲突：[描述]
  - 次冲突：[描述]
伏笔计划：
  - 新埋：[列表]
  - 推进：[列表]
  - 回收：[列表]
```

来源：Moke moke-planner + story 情绪驱动设计。

### Step 2：Composer —— 上下文编排

从已读取的上下文中整理出写作用实际参考：

- **角色活跃**：本章出现的角色及其当前状态
- **设定约束**：本章涉及的世界观规则
- **待回收伏笔**：需要在或可以本章涉及的伏笔
- **时间锚点**：当前时间线位置

### Step 3：Architect —— 章节结构

基于 Planner 输出，设计本章结构：

```
【第{N}章：{标题}】

开篇（0-500字）：[钩子场景]
发展（500-1500字）：[铺垫/推进]
转折/爽点（1500-2500字）：[核心高潮]
结尾（2500-3000字）：[章末钩子/过渡]
```

### Step 4：Writer —— 正文写作

基于 Architect 结构，写出 3000 字正文。

写作铁则：
- **一句一段**：句号处换行，每段不超过60汉字（对话和内心独白除外）
- **对话独立成行**：用冒号或动作引出对话，禁止「他说」「她道」式对话标签。如：沈栀将茶杯往桌上一顿。「你到底想说什么？」
- **禁止段落间空行**：正文段落之间不加空行，保持紧密节奏
- **禁止大段描写堆砌**：描写必须穿插动作或对话，不连续超过3段纯描写
- **禁止跳出视角**：第一人称或限知第三人称后，不切换到其他角色内心
- **章节标题**：用 `## 第X章 章名` 格式，标题后保留一个空行
- **章节之间**：不使用 `---`、水平分隔线或额外空白行
- **避免元叙事**：不出现「正如前文所述」等跳出句
- **避免「不是…而是…」句式**
- **避免分析术语**：不说「内心挣扎」直接写挣扎的动作
- **角色一致**：性格底色不突变（除非情境驱动）
- **章末必须留钩子**：无论什么类型

保存到 `chapters/ch_{NNN}.md`。若项目是旧中文结构，保存到 `正文/` 并沿用已有命名风格。

### Step 5：Observer —— 事实提取

从写好的章节中提取：

- 角色位置变化
- 角色状态变化
- 新增资源/装备
- 新增伏笔
- 消耗的资源
- 时间推进

### Step 6：Reflector —— 状态更新

基于 Observer 的输出，更新以下文件：

- `tracking/current_state.md` — 角色位置/状态
- `tracking/hooks.md` — 新埋伏笔 / 推进状态
- `tracking/chapter_summaries.md` — 追加本章摘要（3-5句）
- `tracking/resource_ledger.md` — 更新数值

### Step 7：Normalizer —— 字数归一化

检查字数：

- 目标 3000 字，允许范围 2800-3200
- 低于 2800 → 提示补充场景细节
- 高于 3200 → 提示精简冗余描写

确保段落不整段等长（变异系数检查）。

### Step 8：Auditor —— 审计

执行审查（详细见 review.md）。本章默认 solo 模式：

- 检查 27 项基础维度（15 核心 + 12 扩展）
- 检查 AI 痕迹 6 项（含 AI腔红线）
- 检查硬性禁令 3 项
- 对话三功能检验
- 输出审查报告

如有 blocking issue un-resolved → 进入 Step 9。

### Step 9：Reviser —— 修订

定点修复 Auditor 发现的问题：

| 问题类型 | 修复方式 |
|---------|---------|
| 设定冲突 | 修改正文匹配设定 |
| OOC | 改写角色行为 |
| AI 痕迹 | 执行去AI味规则 |
| 硬性禁令 | 删除/替换违规内容 |
| 字数不达标 | 补充场景细节 |
| 章末缺钩子 | 追加或强化钩子 |

修复后重新运行 Step 8（Auditor），通过则继续。

### 完成后

更新 `writer.json`：

```python
state["chapters_done"] += 1
state["current_chapter"] = ch
state["last_action"] = "write"
state["stage"] = "writing"
```

并且执行：
- `tracking/hooks.md` — 标记已回收的伏笔为「已回收」
- `tracking/chapter_summaries.md` — 确保摘要已追加
- `tracking/current_state.md` — 确保状态已更新

---

## 轻量模式（--fast）

适用于：日更续写、用户明确表示不需要全流程。

只执行 Step 1 → Step 2 → Step 3 → Step 4 → Step 8 → 如果 blocking → Step 9

跳过：Observer（Step 5）、Reflector（Step 6）、Normalizer（Step 7）

审计（Step 8）缩减为 solo 模式：
- 只检查 AI 痕迹 6 项（段落等长/套话密度/转折重复/句式重复/AI标记词/AI腔红线）
- 只检查硬性禁令 3 项（破折号/不是而是/元叙事）
- 只检查字数下限

---

## 批量模式（--batch N）

适用于：连续写多章，减少上下文消耗。

优先使用可用的 `moke-batch-writer` subagent。若当前环境无法调用该 agent，主会话按默认 5 步逐章串行执行，并在每章后更新追踪文件，避免批量写作造成状态漂移。

### 流程

```
1. 读取当前状态 → 确认起始章节
2. 读取 N 章的章纲
3. 循环执行（每章对应一次 append）：
   a. Planner（批量版：基于上一章结局自然推断）
   b. Architect → Writer
   c. 文件保存
4. 循环结束后，统一执行 Auditor（每章独立但共享上下文）
5. 如有 blocking，标记对应章节编号让用户手动决策
6. 统一 Reflector（更新状态文件）
```

### 批量模式 vs 默认模式区别

| 维度 | 默认模式 | 批量模式 |
|------|---------|---------|
| Observer | 每章 | 末尾统一 |
| Reflector | 每章 | 末尾统一 |
| Normalizer | 每章 | 末尾统一 |
| Auditor | 每章 | 末尾统一，标记 blocker |
| Reviser | 即时 | 统一标记，用户决策 |
| 交互 | 无 | 仅在 blocker 时暂停 |

### 进度显示

```
[批量写作] 第 N 章完成 ✓
[进度: {done}/{total}] 字数: {N} 字 | 用时: {N}m
```

---

## 短篇模式（--short）

适用于：独立短篇小说（知乎盐选风格）。

### 设计原则

1. **先定情绪，再定故事。** 动笔前必须确定目标情绪（意难平/反转震撼/爽感释放/治愈温暖/细思极恐/共鸣感动）。
2. **一个反转撑一篇。** 所有铺垫为反转服务，所有情绪为反转蓄力。
3. **开头 3 句定生死，结尾定传播。**
4. **默认第一人称。**

### 流程

1. **Phase 1：确定情绪目标** → 用 `clarify` 问用户「你想让读者读完什么感觉？」；若用户已说明则直接采用
2. **Phase 2：构思** → 主角+核心冲突+反转设计
3. **Phase 3：结构** → 铺垫段→升级段→反转段→余韵段
4. **Phase 4：写作** → 2000-5000 字
5. **Phase 5：审查** → 情绪目标是否达成 + 反转是否有力
6. **Phase 6：润色** → 去AI味 + 格式匹配

### 格式

```markdown
###1.

正文……第一段……

###2.

正文……第二段……

（余韵/不需要额外小节）
```

---

## 成功标准

- [ ] 正文文件保存到 `chapters/ch_{NNN}.md` 或旧结构 `正文/` 对应章节文件
- [ ] 字数在目标范围内
- [ ] 审计通过（solo 模式无 blocking issue）
- [ ] 状态文件已更新
- [ ] 追踪文件已更新
- [ ] 章末有钩子
- [ ] 无硬性禁令违规
