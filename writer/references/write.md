# 写作管线：长篇/短篇/批量

---

## 模式选择

| 模式 | 命令示例 | 说明 |
|------|---------|------|
| **默认模式** | `write 第5章` | 5 步日更管线：Plan → Architect → Write+Reflect → Audit+Normalize → Revise |
| **完整模式** | `write 第5章 --full` | 展开 9 步完整管线 |
| **轻量模式** | `write 第5章 --fast` | 跳过 Observer/Reflector/Normalizer |
| **批量模式** | `write --batch 3` | 一次性规划，主 Agent 亲写批量写入 |
| **DeepSeek 出稿** | `write --batch 30 --use-deepseek` | 委托 novel-pipeline `novel-deepseek MCP` 生成骨架（30+ 章大批量适用）|
| **短篇模式** | `write --short` | 短篇小说写作 |
| **快速短篇** | `write --short --fast` | 情绪驱动 + 快速出稿 |

---

## 执行前预检

在开始任何写章之前：

```python
import json, os

project_root = "."
state_path = os.path.join(project_root, "novel.json")
if not os.path.exists(state_path):
    # 向后兼容：writer.json / novel-pipeline.json 都识别
    for alt in ("writer.json", "novel-pipeline.json"):
        if os.path.exists(os.path.join(project_root, alt)):
            state_path = os.path.join(project_root, alt)
            break
    else:
        print("ERROR: 没有找到项目根标记（novel.json / writer.json / novel-pipeline.json），请先运行 project-init")
        exit(1)

with open(state_path, 'r', encoding='utf-8') as f:
    state = json.load(f)

outline_chapter_dir = os.path.join(project_root, "outline", "chapter_outline")
ch = state.get("current_chapter", 0) + 1
ch_outline = os.path.join(outline_chapter_dir, f"ch_{ch:03d}.md")

if not os.path.exists(ch_outline) and state.get("stage") != "planning":
    print(f"WARNING: 第{ch}章章纲不存在。先运行 plan 还是直接写？")
```

如果 stage 为 `scaffold`（刚初始化），提示先运行 plan。

**同时确认 `novel_project` MCP 可达**（写章前必须先查记忆，见 `references/memory-mcp.md`）：

```bash
# Agent 通过 tools/list 探测 novel_project 是否连通
# 不可达 → 提示用户 claude mcp list 检查，或退回 --fast 模式（放弃续写前查询）
```

---

## 默认模式：5 步日更管线

适用于：日更续写、普通单章写作、用户没有要求全量审计时。

### Step 1：Plan

确认章节号、字数目标、核心事件、情绪目标、必须包含、必须避免、章末钩子。加载当前状态：

**续写前必查（v8.4 硬性要求）**：调 `novel_project` MCP 拉取相关记忆。

```
# 对本章预计出场的每个角色/势力/伏笔：
- 主要角色：get_entity_with_relations({name: "苏白"})
             → 拿到当前修为/位置/最近观测 + 关系网（所属势力/敌友/师承）
- 主要势力：get_entity_with_relations({name: "青云门"})
- 未回收伏笔：search_nodes({query: "伏笔:", limit: 50})
             → 过滤未含"回收于"关系的伏笔实体
- 章纲提到的新地点/新术法：先 search_nodes 确认是否已存在同名实体
```

同时对照以下**静态文件**确认一致性：
- `outline/chapter_outline/ch_NNN.md`（本章计划）
- `novel.json`（项目元数据）
- `setting/*.md`（世界观/角色的静态约束——用户改过之后的最新版；含用户 `<!-- user-edit -->` 里的规划意图）

> 适用禁令：B09（批次上限）/ B10（如是新卷首章，卷间衔接检查）

### Step 2：Architect

合并 Composer + Architect：整理角色、设定、伏笔、时间锚点，并生成章节结构。**以 Step 1 从 MCP 拉回的最新观测为基准**（这是已写章节的精确事实源，比 `setting/*.md` 的开局设定更贴近"当前"）。

> 适用禁令：B04（避免在结构中使用元叙事标签）

### Step 3：Write + Reflect

写正文到 `chapters/ch_{NNN}.md`。写完后自动归档事实到 `novel_project` MCP：

```bash
# 1. 读刚写完的章节 → Agent 分析人物/势力/伏笔/世界观变更
# 2. 构造 JSON payload 调用 archive_facts.py：
#    {
#      "chapter_number": {NNN},
#      "changes": {
#        "characters": [{"name": ..., "cultivation": ..., "current_location": ...,
#                        "factions": [...], "recent_changes": [...]}],
#        "foreshadowing": {"new": [{"name": ..., "description": ...}],
#                          "resolved": [{"name": ..., "resolution": ...}]},
#        "factions": [{"name": ..., "type": ...}],
#        "power":    {"realms": [...], "techniques": [...]},
#        "world":    {"geography": [...], "special_rules": [...]},
#        "relations":[{"source": ..., "target": ..., "type": "所属|师承|盟友|敌对|修习"}]
#      }
#    }
#    → archive_facts.py 生成 MCP tool-call 序列（read → merge → write 三段式）
#
# 3. Agent 按 tool_calls 顺序调 novel_project MCP：
#    a. 先执行所有 phase=read 的 get_entity_with_relations，拿到旧观测 old_obs
#    b. 把 create_entities payload 里的 "<merge_with_old>" 占位符替换为对应 old_obs
#    c. 依次执行 phase=write 的 create_entities → create_relations
#
# 4. 无需回写任何本地 JSON（v8.4 起 .writer/state/*.json 已废弃）
```

#### archive_facts.py payload 完整示例

主 Agent 写完 ch_012 后，如果本章发生了「苏白突破练气四层 + 埋新伏笔"神秘老者身份"+ 首次揭示血刃门」，payload 应长这样：

```json
{
  "chapter_number": 12,
  "changes": {
    "characters": [
      {
        "name": "苏白",
        "cultivation": "练气四层",
        "current_location": "青云门后山",
        "emotional_state": "紧张但兴奋",
        "recent_changes": ["突破练气四层", "初见神秘老者"]
      }
    ],
    "foreshadowing": {
      "new": [
        {
          "name": "老周身份",
          "description": "神秘老者身份未知",
          "hints_placed": ["ch012 结尾对视片段"]
        }
      ],
      "resolved": []
    },
    "factions": [
      {"name": "血刃门", "type": "邪修势力", "note": "首次揭示"}
    ],
    "power": {},
    "relations": [
      {"source": "苏白", "target": "血刃门", "type": "敌对"}
    ]
  }
}
```

调用方式（在主 Agent 会话内）：

```bash
cat <<'EOF' | python <writer>/scripts/archive_facts.py
{...上面的 JSON...}
EOF
```

archive_facts 返回：
```json
{
  "ok": true,
  "chapter": 12,
  "tool_calls": [
    {"phase":"read","tool":"get_entity_with_relations","args":{"name":"苏白"},"purpose":"..."},
    {"phase":"write","tool":"create_entities","args":{"entities":[{"name":"苏白","entityType":"人物","observations":["<merge_with_old>","ch012: 修为 练气四层",...]}]}},
    {"phase":"write","tool":"create_relations","args":{"relations":[{"source":"苏白","target":"血刃门","type":"敌对"}]}}
  ],
  "instructions": "..."
}
```

字段规则：
- `characters[].name` 是 MCP 实体名（entityType="人物"）；追加观测需**先 read 后 merge**（archive_facts 已自动生成 read 步骤）
- `foreshadowing.new[]` 自动加前缀 `伏笔:xxx`；观测强制 `chNNN:` 前缀
- `foreshadowing.resolved[]` 把 `<merge_with_old> + "ch012: 已回收 - <resolution>"` 追加到伏笔实体；若填了 `resolved_plot` 还会建 `回收于` 边
- `factions[]` 单独 create_entities（entityType="势力"）
- `relations[]` 有向边；type 必须在受控词表内（见 `references/memory-mcp.md` §3.3）

> 详细契约：`references/memory-mcp.md`（工具目录 + entityType/relations 受控词表 + 覆盖式陷阱说明）

> 适用禁令：B01（对话「」）/ B02（禁止 ——）/ B03（禁止「不是…而是…」）/ B05（AI高频词）/ B06（每段 ≤42 汉字）

### Step 4：Audit + Normalize

**4a. 禁令扫描**：
```bash
python scripts/audit.py chapters/
```

**4b. 修复 + 补归档**：
```bash
# 1. 根据 audit.py 结果逐句修复
# 2. 修复后重跑 audit.py 确认禁令清零
# 3. Step 3 已归档一次；若修复涉及事实变更（不只是文字层）需再走一次 archive_facts.py
```

> 适用禁令：B01-B07 全部 / AI 痕迹 6 维

### Step 5：Revise

只修 blocking 问题、用户明确关注的问题和明显影响可发布的问题。修订后再跑一次关键禁令扫描。

> 适用禁令：B07（字数 ≥2500，不足则手工扩充场景描写/感官细节） / B08（禁止脚本注入文本）

## 完整模式（--full）：9 步 = 5 步 + 4 扩展

在 5 步默认管线基础上展开。新增步骤标 ★：

| # | 步骤 | 说明 |
|---|------|------|
| ★1 | Planner | 内存生成章节意图（章号/目标/情绪/冲突/伏笔计划） |
| ★2 | Composer | 从 MCP 拉活跃角色 + 关系网 + 待回收伏笔；对照 setting/*.md 与时间锚点 |
| 3 | Architect | 章节四段结构（开篇→发展→爽点→结尾），60%处检查爽点 |
| 4 | Writer | 写正文到 `chapters/ch_{NNN}.md`，一句一段≤42 字，「」引号，章末钩子 |
| ★5 | Observer | 提取事实变更（角色状态/资源/伏笔/时间/新势力） |
| ★6 | Reflector | 生成 archive_facts payload → 调 novel_project MCP 落库（含 relations） |
| 7 | Normalizer | 字数 3000±200，段落变异系数检查 |
| 8 | Auditor | solo 审查：15 维核心 + AI 痕迹 + 硬禁令 → blocking 则进 Step 9 |
| 9 | Reviser | 定点修复 blocking；修后重跑 Step 8 |

完成后：`novel.json` 更新 `chapters_done` / `current_chapter`。验证：调 `get_entity_with_relations` 抽查 Step 6 归档的主角，`observations` 里应能看到 `ch{NNN}:` 前缀的新条目。

### 写后自动审查（质量闸门，每章必跑）

> 本项目**质量优先于速度**。写章完成后自动激发审查，不等待用户手动触发。
>
> **审查层级是嵌套的**（quick ⊂ daily ⊂ solo ⊂ lean ⊂ full），高层级包含低层级的全部检查。因此采用**替代升级**而非叠加——只运行当前适用的最高层级。

```
写后按章节数自动升级审查深度（替代，非叠加）：

每章:     daily(8维)                      ← 包含 quick 自检
每5章:    solo(15维)                      ← 替代 daily（包含 daily 全部 8 维）
每10章:   lean(27维)                      ← 替代 solo
每卷/>20章: full(43维,4Agent)+review-cycle ← 替代 lean
每100章:  full + longform-quality-monitor  ← longform 独立于审查层级，叠加运行

任一级别命中 blocking → 立即停止 → 修复 → 重跑该级 → 通过后继续
```

详见 `references/REVIEW_TRIGGERS.md`。

## 轻量模式（--fast）

适用于：日更续写、用户明确表示不需要全流程。

只执行 Step 1 → Step 2 → Step 3 → Step 4 → Step 8 → 如果 blocking → Step 9

跳过：Observer（Step 5）、Reflector（Step 6）、Normalizer（Step 7）

> ⚠️ 跳过 Reflector 意味着**本章事实不入 MCP**——下一章续写前查询会看不到本章变化。仅用于用户明确不想归档的一次性场景（如实验性草稿）。

审计（Step 8）缩减为 solo 模式：
- 只检查 AI 痕迹 6 项（段落等长/套话密度/转折重复/句式重复/AI标记词/AI腔红线）
- 只检查硬性禁令 3 项（破折号/不是而是/元叙事）
- 只检查字数下限

---

### 批量模式（--batch N）

适用于：连续写多章，减少上下文消耗。

**⚠️ 批量写前必须先执行预写总线对齐检查**（详见 `references/pre-write-alignment.md`）：加载总纲→卷纲→细纲，从 MCP 拉主要角色状态，确保总线不偏离、前后能衔接。

优先使用可用的批量写作 subagent。若当前环境无法调用，主会话按默认 5 步逐章串行执行，每章后归档 MCP 避免状态漂移。

### 批量写前：声音内化（Voice Internalization）

**批量写章前必须读最近 4-6 章已写正文**，不能只读大纲和设定。这是决定批量产出质量的关键步骤——跳过它会产出符合大纲但声音完全不对的章节。

**为什么需要**：大纲定义"写什么"，而已写正文定义"怎么写"。每个作者/项目有独特的句长、节奏、感官密度、对话模式——这些无法从大纲中推断，只能从已写正文中吸收。

**操作**：
1. 按逆序读最近 4-6 章（如写 ch121-135，先读 ch116-120）
2. 注意以下维度，在心里建立声音模板：
   - **句长**：平均每句多少字？有无长句穿插短句的节奏模式？
   - **感官密度**：每段有几层感官细节（视觉/听觉/触觉/嗅觉）？细节是粗线还是工笔？
   - **对话模式**：对话用冒号引出还是独立成段？对话中穿插多少动作？对话平均多长？
   - **心理描写**：是否直接写内心？还是通过动作外化？用「他知道」还是省略主语？
   - **结尾风格**：章节怎么收尾？哲理/动作定格/场景淡出/钩子？
   - **段落呼吸**：段落间空行节奏如何？有无连续短段制造紧迫感？

3. **不要分析，要吸收。** 不用在笔记里写总结——读 4-6 章后声音会自然进入肌肉记忆。写第一章时如果前几段读起来像已写章节，就对齐了。

**⚠️ 子代理批量写章限制**：单个子代理最多分配 5 章（≤5）。超过 5 章会导致子代理的迭代预算不够完成全部章节的写→审→修循环。实测：6 章任务在预算耗尽后退出，只完成 2 章。拆成 4+3 或 5+5 即可。

### delegate 写后三步自检（嵌入 delegate prompt）

委派写章时，delegate prompt 中必须包含以下自检指令。delegate 每写完一章后立即执行，不合格就地修改，**不留到主会话返工**：

```
【写完每章后立即自检——不可跳过】

自检 1：禁令扫描（10秒目测）
  □ 全文无「——」
  □ 全文无「不是…而是…」
  □ 对话全用「」
  □ 无「他知道」「忽然」「似乎」「仿佛」
  任一命中 → 就地替换修改

自检 2：字数 + 段落（30秒估算）
  □ 按行数×每行平均字数估算，≥2500？
    <2500 → 找该章最薄弱的场景，展开 1-2 段画面描写
  □ 目测每段 ≤42 汉字？
    超标段 → 在句号处拆分

自检 3：章末钩子（10秒确认）
  □ 读章末最后一段 → 读者读完会想翻下一章吗？
    无钩子 → 加一句悬念/反转/威胁/期待收尾
```

完成后在每章末尾追加一行标记：`<!-- 自检通过 -->`

### delegate context 模板

委派 prompt 必须包含以下信息块：

```
【写章任务】
- 章节范围：ch{N} - ch{M}（共 {K} 章）
- 每章字数：≥2500 汉字
- 章节命名：chapters/ch_{NNN}.md

【硬性禁令（不可违反）】
- 对话用「」/ 禁止「——」/ 禁止逗号连接的「不是…是/而是…」
- AI高频词禁用：他知道/忽然/突然/似乎/仿佛/眼中闪过一丝/深吸一口气/心中一动
- 每句≤42 汉字，句号处换行

【当前状态】（写前必须调 novel_project MCP + 读 setting/*.md）
- 主角修为：{level}（来源: MCP get_entity_with_relations("苏白") 里最近的 "ch{X}: 修为 xxx" 观测）
- 位置/资源：{loc/gold}（来源: 同上 + setting/*.md 用户 user-edit 块）
- 待回收伏笔：{hooks_summary}（来源: MCP search_nodes("伏笔:") 过滤未回收）
- 用户规划意图：{user_planning}（来源: setting/*.md 中 <!-- user-edit --> 块）
- 上一章结尾：{prev_chapter_ending}

【章纲摘要】
{chapter_outline_summary}

【声音语调】（如项目有 writing_rules.md，必须加载并传递给子代理）
- 主角性格：{protagonist_traits}
- 叙事语调：{tone_summary}（如：轻松+幽默+烟火气，日常化决策，禁止冷分析/三笔账式段落）
- 回忆轻量化：≤5行
- 独白节制：≤3句
- 章末余味：期待/笑意，不是沉重

【声音参考】
已读最近 4 章正文（ch{N-4}-ch{N-1}），匹配句长/感官密度/对话模式/结尾风格。
不足4章时，明确传递声音描述替代。

【写后三步自检】
每章写完后立即执行：①禁令扫描→②字数+段落→③章末钩子+声音自查。不合格就地修改。
```

### 流程

```
1. 读取项目状态（novel.json）→ 确认起始章节
2. 读取 N 章的章纲
3. 从 novel_project MCP 拉主要角色/势力/未回收伏笔（一次拉全批次上下文，不是每章重拉）
4. 循环执行（每章对应一次 append）：
   a. Planner（批量版：基于上一章结局自然推断）
   b. Architect → Writer
   c. 文件保存
   d. archive_facts.py → 生成 MCP tool_calls → Agent 调 MCP 归档
5. 循环结束后，统一执行 Auditor（每章独立但共享上下文）
6. 如有 blocking，标记对应章节编号让用户手动决策
```

### 批量模式 vs 默认模式区别

| 维度 | 默认模式 | 批量模式 |
|------|---------|---------|
| Observer | 每章 | 末尾统一 |
| Reflector (MCP 归档) | 每章 | **每章仍需归档**（不能延后到末尾——续写会看不到前章状态） |
| Normalizer | 每章 | 末尾统一 |
| Auditor | 每章 | 末尾统一，标记 blocker |
| Reviser | 即时 | 统一标记，用户决策 |
| 交互 | 无 | 仅在 blocker 时暂停 |

### 子代理批次上限

**≤5 章/批次安全**，6-7 章大概率完成但可能超时，8+ 章高风险。所有批量写章应拆为 ≤5 章的子任务。详见上方「批量写章限制」。

### 进度显示

```
[批量写作] 第 N 章完成 ✓
[进度: {done}/{total}] 字数: {N} 字 | 用时: {N}m
```

---

## DeepSeek 出稿模式（--use-deepseek）

适用于：**大批量初稿生成**（30+ 章一次性出稿）。委托 novel-pipeline 的 `novel-deepseek` MCP 生成剧情骨架，主 Agent 只负责编排 payload + 落盘 + 归档。

### 使用场景

- 已有完整章纲（`outline/chapter_outline/ch_NNN.md`），只需机械转成正文骨架
- 主 Agent 上下文预算紧张，不适合亲写
- 后续会走 novel-pipeline 的 `polish_chapter.py` 做番茄风润色（三段流水线）

### 前置

1. novel-pipeline skill 已装好，`.env` 已配 `DEEPSEEK_{API_KEY,BASE_URL,MODEL}` 三项
2. 运行环境已注册 `novel-deepseek` MCP（Hermes 会话自动，Claude Desktop 需手动配置 `.mcp.json`）
3. 项目已跑过 `pre-write-alignment` 检查

### 单章调用流程

主 Agent 在会话内构造：

```python
# Step 1: 拉本章上下文
setting_summary = <从 setting/*.md 抽取本章相关的世界观/角色>
mcp_context     = <novel_project MCP 拉本章出场角色 get_entity_with_relations 结果的精简版>
chapter_outline = <读 outline/chapter_outline/ch_NNN.md>

# Step 2: 调 novel-deepseek MCP generate_draft
draft_text = mcp__novel_deepseek__generate_draft(
    global_setting=setting_summary + mcp_context,   # 本章世界观 + MCP 当前状态摘要（约 500-1500 字）
    chapter_outline=chapter_outline,                # 本章细纲全文
    chapter_number=NNN,                             # 章号 int
    revision_instructions="",                       # 首次生成留空；重生成时填自检反馈
)

# Step 3: 检查 draft_text 首字符
#   若以 "ERROR:" 开头 → 打印错误，中止本章
#   否则 → 写入 chapters/ch_NNN.md

# Step 4: 触发 write.md Step 4 Audit + Step 3 归档（同亲写路径）
```

### 批量调用流程

```
for ch in range(start, end+1):
    outline = read(outline/chapter_outline/ch_{ch:03d}.md)
    setting = <setting/*.md 相关切片> + <MCP 拉本章角色最新观测>
    draft   = mcp__novel_deepseek__generate_draft(setting, outline, ch)
    write(chapters/ch_{ch:03d}.md, draft)
    run audit.py
    run archive_facts.py → 生成 tool_calls → 调 novel_project MCP 落库
```

**批次上限**：与 `--batch` 一致（≤5 章一批）。DeepSeek 单次调用约 30-90s，5 章约 5-8 分钟。

### 与主 Agent 亲写的差异

| 维度 | 主 Agent 亲写 | DeepSeek 出稿 |
|---|---|---|
| 输入 | outline + setting + MCP 记忆 + user-edit 块 | outline + setting（切片）+ MCP 精简摘要 |
| 文笔 | 主模型语调（Claude/主项目风格）| DeepSeek 骨架风格（平铺直白）|
| 声音一致性 | ✅ 从 `writing_rules.md` 拿 | ❌ 需后续 polish_chapter.py 用番茄预设润色 |
| 字数控制 | 主 Agent 判断 | MCP prompt 硬约束 2500-4500 |
| 上下文成本 | 每章 5-15k tokens | 每章 0.5k tokens |
| 适用规模 | 日更（≤5 章/次）| 大批量（30-100 章一波）|

**推荐用法**：DeepSeek 出稿 → 走一遍 `polish_chapter.py --style-file fanqie-quick-anti.md` 上番茄风 → daily 审查 → 发布。三段流水线一次跑完 30 章约 60-90 分钟。

### 错误处理

MCP 返回以 `ERROR:` 开头的字符串时：
- `ERROR: DEEPSEEK_API_KEY 未配置` → 查 novel-pipeline `.env`
- `ERROR: API 返回错误 4xx/5xx` → API 端 rate limit 或余额，暂停 60s 重试
- `ERROR: 网络请求失败` → 检查 `DEEPSEEK_BASE_URL` 连通性


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

> 短篇模式**不做 MCP 归档**（一次性作品，无续写需求）。

---

---

## 批量写作避坑指南

> 详见 `references/write-pitfalls.md`（13 项实战教训）。

## 成功标准

- [ ] 正文文件保存到 `chapters/ch_{NNN}.md`
- [ ] 字数在目标范围内
- [ ] 审计通过（solo 模式无 blocking issue）
- [ ] MCP 已归档本章事实（可用 `get_entity_with_relations` 抽查主角）
- [ ] 章末有钩子
- [ ] 无硬性禁令违规

---

> **下一步**：[日更审查](review.md) --daily（8维3分钟发布闸）；批量写章后跑 [审查循环](review-cycle.md)
