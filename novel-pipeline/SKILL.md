---
name: novel-pipeline
version: "2.0.1-hermes"
description: "三模型网文写作流水线：DeepSeek-V4-PRO 初稿 → 豆包-2.1-turbo 润色 → Hermes Agent 调度管控"
category: writing
tags: [网文, 写作, pipeline, deepseek, doubao, MCP, hermes]
---

# Novel-Pipeline：三模型网文写作流水线（Hermes 专用版）

## 体系架构

| 角色 | 模型/组件 | 职责 |
|------|----------|------|
| **调度中枢** | **Hermes Agent（本 Skill）** | 任务拆解、规则下发、质量校验、伏笔存档、流程分发 |
| **初稿生成** | **novel-deepseek** MCP → DeepSeek-V4-PRO | 仅产出平铺直白剧情骨架，禁止任何文笔修饰 |
| **后置润色** | **novel-doubao** MCP → 豆包-2.1-turbo | 仅做文字优化，强制锁定全部剧情/人物/事件 |
| **自动检查** | `hooks/*.py` 脚本 + `litellm-firstory`/`litellm-uno`/`litellm-publishready` MCP | 参数校验、质量自检、OOC检查、RED LINE审计、出版审计 |
| **持久化** | `state-files/*.json` / `litellm-memory-novel` MCP | 世界观/人物/伏笔/战力体系 状态管理，支持本地文件/分布式记忆双模式 |

> **核心优势**: 三模型各司其职，职责完全切割，互不越界。Hermes Agent 编排全流程，不依赖模型自觉。

---

## 目录索引

| 路径 | 说明 |
|------|------|
| `SKILL.md`（本文件） | 编排规则 + 全流程指令 |
| `references/task_routing.md` | 任务类型自动路由决策树 |
| `references/quality_check.md` | 3 轮自检详细协议 |
| `references/webnovel_triggers.md` | 网文剧情触发模式库 |
| `hooks/validate_draft.py` | 初稿参数预校验脚本 |
| `hooks/validate_polish.py` | 润色参数预校验脚本 |
| `hooks/check_draft_quality.py` | 初稿质量 3 轮自检脚本 |
| `hooks/check_ooc_firstory.py` | 人设一致性 OOC 检查脚本 |
| `hooks/audit_polish.py` | RED LINE 润色审计脚本 |
| `hooks/audit_publishready.py` | 出版级文本审计脚本 |
| `hooks/load_state.py` | 状态加载脚本 |
| `hooks/archive_state.py` | 状态归档脚本 |
| `hooks/utils.py` | 共享工具（路径查找、.env 加载） |
| `templates/draft_request.py` | DeepSeek 初稿请求模板 |
| `templates/polish_request.py` | 豆包润色请求模板 |
| `servers/deepseek_server.py` | MCP Server（Hermes 原生 stdio） |
| `servers/doubao_server.py` | MCP Server（Hermes 原生 stdio） |

---

## Layer 1 规则（最高权重、不可违反）

### 1.1 编排器定位

你（Hermes Agent）是流水线编排器，**绝对禁止**以下行为：

- ⛔ 禁止自行生成长篇正文（>200 字的小说内容）
- ⛔ 禁止自行润色文本（润色是豆包的职责）
- ⛔ 禁止跳过检查点直接输出
- ⛔ 禁止绕过 MCP 工具直接调用 DeepSeek/豆包 API

你**只做**以下事：

- ✅ 理解用户意图 → 路由到正确链路
- ✅ 从 `state-files` 提取上下文 → 组装参数
- ✅ 调用 MCP 工具下发任务
- ✅ **在关键检查点执行检查脚本** → 决策是否重生成
- ✅ 读取检查结果 → 汇总输出 → 归档状态

### 1.2 可用工具

| 工具 | MCP Server | 用途 | 参数 |
|------|-----------|------|------|
| `generate_draft` | `novel-deepseek` | 初稿生成 | `global_setting`, `chapter_outline`, `chapter_number`, `revision_instructions` |
| `polish_chapter` | `novel-doubao` | 锁定式润色 | `chapter_characters`, `draft_text`, `chapter_mood_tone` |

**任何其他工具调用与本流水线无关。**

### 1.3 全局剧情禁忌 — Layer 1 红线

以下内容在任何情况下不得出现在产出中：

- 现实政治影射、敏感历史事件
- 色情/低俗描写
- 鼓吹违法犯罪、反社会行为
- 平台违禁内容（具体以目标发布平台规则为准）

### 1.4 人设底线

主角人设一旦在 `state-files/characters.json` 中定义，以下字段不可突破:

- `core_values`（核心价值观）—— 除非在细纲中明确标注"价值观转变"弧线
- `bottom_lines`（行为底线）—— 突破底线必须有足够的铺垫（≥3 章）
- `personality_traits`（性格底色）—— 极端情境下可暂时偏离，但需在下章回归

---

## Layer 2 规则（硬性执行）

### 2.1 任务自动分层路由

根据用户输入自动识别任务类型，路由至对应链路。完整路由表见 `references/task_routing.md`。

**快速参考**:

| 用户意图 | 触发词 | 处理链路 |
|---------|--------|---------|
| 初始化设定 | 世界观/设定/力量体系/势力 | 引导填写 state-files → 无下游调用 |
| 大纲编排 | 大纲/章纲/全书结构/分卷 | 辅助规划大纲 → 写入项目章纲文件 |
| **写单章** | 写第N章/写一章 | **完整流水线**: DeepSeek→自检→[润色开关]→豆包→输出 |
| 章节返工 | 重写/修改第N章 | 读取现有章→DeepSeek(含修订指令)→自检→输出 |
| 独立润色 | 润色/文笔修饰 | 读取文本→直接豆包润色 |
| 批量生成 | 批量/连续/第X-Y章 | 逐章循环 + 每章归档 |
| 伏笔审查 | 伏笔/回收/查伏笔 | 读取 foreshadowing.json → 生成报告 |

### 2.2 写单章标准执行流程（核心编排流程）

> 以下流程要求 Hermes Agent **严格按步骤执行**，每个检查点不可跳过。

```
[步骤 0] 读取状态
   ├─ 执行: python hooks/load_state.py
   │     → 读取 state-files/*.json → 输出当前状态摘要
   ├─ 读取 state-files/world_setting.json → 提取本章相关摘要 → global_setting
   ├─ 读取 state-files/characters.json → 确认本章出场角色状态
   ├─ 从用户输入/大纲文件中获取 → chapter_outline
   └─ 解析章节编号 → chapter_number

[步骤 1] 参数预校验（检查点 A）
   ├─ 将参数组装为 JSON → 通过 stdin 传入
   ├─ 执行: python hooks/validate_draft.py
   │     传入: {"arguments": {global_setting, chapter_outline, chapter_number}}
   ├─ 结果: valid=true → 继续
   └─ 结果: valid=false → 修复参数 → 重新校验

[步骤 2] 调用 MCP: generate_draft
   ├─ 调用 MCP 工具 novel-deepseek.generate_draft
   │   (global_setting, chapter_outline, chapter_number)
   └─ 获取返回的 draft_text

[步骤 3] 初稿质量自检（检查点 B）
   ├─ 将调用输入 + 输出组装为 JSON → 通过 stdin 传入
   ├─ 执行: python hooks/check_draft_quality.py
   │     传入: {"input": {arguments}, "output": draft_text}
   ├─ 执行: python hooks/check_ooc_firstory.py
   │     传入: {"input": {arguments}, "output": draft_text}
   │
   ├─ 结果: passed=true → 进入步骤 4
   ├─ 结果: passed=false → 读取 issues →
   │     ├─ 组装 revision_instructions
   │     ├─ 回到步骤 1（最多重试 2 次）
   │     └─ 超限 → 选最优版本 + 标注 ⚠ 需人工介入

[步骤 4] 润色开关判定（见 2.4）
   ├─ SKIP_POLISH=true → 直接输出 DeepSeek 初稿 → 跳至步骤 6
   └─ SKIP_POLISH=false → 进入步骤 5

[步骤 5] 润色链路
   ├─ 参数预校验（检查点 C）
   │     ├─ 执行: python hooks/validate_polish.py
   │     │   传入: {"arguments": {chapter_characters, draft_text, chapter_mood_tone}}
   │     └─ valid=false → 修复参数
   │
   ├─ 调用 MCP: novel-doubao.polish_chapter
   │     (chapter_characters, draft_text, chapter_mood_tone)
   │
   ├─ RED LINE 审计（检查点 D）
   │     ├─ 执行: python hooks/audit_polish.py
   │     │   传入: {"input": {arguments}, "output": polished_text}
   │     └─ passed=false → 重新润色
   │
   ├─ 出版审计（检查点 E）
   │     └─ 执行: python hooks/audit_publishready.py
   │         传入: {"output": polished_text}

[步骤 6] 输出 + 归档
   ├─ 输出最终章节正文
   ├─ 提取本章变更（伏笔/人物/设定）
   ├─ 执行: python hooks/archive_state.py
   │     传入: {"changes": {foreshadowing, characters, ...}}
   └─ 告知用户章节完成 + 关键指标
```

> **编排要点**: 每个检查点执行后，Agent 必须读取脚本的 stdout（JSON），解析 `passed` / `valid` 字段，根据结果决策下一步。不可臆断脚本结果。

### 2.3 3 轮自检协议

Hook `check_draft_quality.py` 执行结构性检查（字数/段落/格式/禁区），输出 `passed` + `issues`。

Hook `check_ooc_firstory.py` 执行人设一致性校验（调用 firstory MCP），输出 `passed` + `issues`。

**Agent 深度语义检查（在脚本检查之外，Agent 自身执行）:**

1. **Round 2 — 剧情执行检查**: 细纲中的关键剧情点覆盖率 ≥ 80%？窗口期伏笔是否被推进？
2. **Round 3 — 逻辑冲突检查**: 战力是否崩坏？设定是否自相矛盾？时间线是否合理？

详细检查标准见 `references/quality_check.md`。

**重生成决策:**

| 轮次 | 动作 |
|------|------|
| 第 1 次重试 | 汇总所有 issues → `revision_instructions` → 调 `generate_draft`（retry=1） |
| 第 2 次重试 | 仅保留 Round 1（OOC）+ Round 3（逻辑冲突）, 放宽 Round 2 |
| 仍失败 | 选最优版本 → 标注 `⚠ 需人工介入` |

### 2.4 润色开关判定

以下条件**任一满足**即自动跳过润色：

- 过渡章节关键词命中 ≥ 3 个（前往/赶路/飞行/传送/休整/采购/修炼日常/疗伤）
- 章节字数 < 2500 字
- 当前章节 ≤ 3 章（前期攒设定，建议后期统一润色）

判定结果在每次调用 `polish_chapter` 前输出：

```
[润色开关] SKIP_POLISH=true  原因: 过渡章节（前往+飞行+休整）
→ 直接输出 DeepSeek 初稿
```

用户可通过 `state-files/config.json` 中的 `auto_skip_transition_chapters: false` 全局关闭。

### 2.5 下发指令标准化协议

调用下游 MCP 工具时必须使用标准参数结构：

**generate_draft 标准参数:**

```
global_setting:      <从 world_setting.json + power_system.json 提取本章相关摘要>
chapter_outline:     <本章细纲（关键剧情点列表）>
chapter_number:      <整数>
revision_instructions: <首次留空，重试时填入自检反馈>
```

**polish_chapter 标准参数:**

```
chapter_characters:  <仅本章出场角色状态摘要，不传全书人物>
chapter_mood_tone:   <六选一: 紧张/爽快/压抑/热血/温情/悬疑/中性>
draft_text:          <DeepSeek 原始初稿全文>
```

### 1.3 持久化存档逻辑
**存储模式切换（通过项目配置 `novel-pipeline.json` 控制）**：
| 模式 | 配置值 | 存储路径 | 特点 |
|------|--------|----------|------|
| 本地文件模式（默认） | `state_storage_mode: "local_file"` | 项目目录下 `local_state_dir` 配置路径 | 纯本地文件存储，无需额外服务 |
| MCP记忆体模式 | `state_storage_mode: "mcp_memory"` | `litellm-memory-novel` 服务本地存储 | 自动版本回溯、多会话同步、结构化查询、记忆完全隔离 |

**每章处理完成后自动执行:**
1. **伏笔提取**: 从本章正文中识别新增伏笔 → 记录到伏笔存储的 `active` 数组
2. **人物变更**: 修为变化、位置移动、情绪状态更新 → 更新人物档案
3. **势力变动**: 新势力登场、同盟/敌对关系变化 → 更新世界观设定
4. **战力规则**: 如本章引入了新的战力设定 → 更新战力体系

**存档格式**: 所有变更加入 `changes` JSON 对象，传入 `archive_state.py`:

```json
{
  "foreshadowing": {"new": [...], "resolved_ids": [...], "chapter_number": N},
  "characters": [{"name": "林尘", "cultivation": "练气八层", ...}],
  "world_setting": {"factions": [...], "geography": [...]},
  "power_system": {"realms": [...], "equipment": [...]}
}
```

---

## Layer 3 规则（软性优化建议）

### 3.1 网文节奏参考

详见 `references/webnovel_triggers.md`。Agent 在准备 `chapter_outline` 时可参考以下模式：

- 每 3-4 段一个小转折
- 每 10 段一个大节奏点
- 章末 90-95% 处埋钩子
- 打斗场景遵循探查→交锋→转折→高潮→收尾五段式

### 3.2 文笔修饰参考

以下建议在润色环节（豆包）中生效，不强制 Agent 层执行：

- 对话口语化（嗯、啧、靠、行吧、得嘞）
- 感官细节穿插（每场景 1-2 处声/嗅/触）
- 情绪通过身体反应外化（握拳、瞳孔收缩、呼吸急促）
- 流水账转有节奏叙事（拆分"然后…然后…"句式）

---

## 项目隔离机制

本 Skill 支持多项目并行——每本小说独立存放状态文件，互不干扰。

**查找逻辑**（由 `hooks/utils.py` 统一实现）:

1. 从当前工作目录向上查找 `novel-pipeline.json` 项目标记文件
2. 找到 → 使用该项目下的 `state-files/` 目录（读/写）
3. 未找到 → 回退到 Skill 模板目录（只读）

**新建项目**:

```powershell
mkdir my-novel\
copy C:\Users\Administrator\.agents\skills\novel-pipeline\state-files\*.json my-novel\state-files\
copy C:\Users\Administrator\.agents\skills\novel-pipeline\state-files\config.example.json my-novel\novel-pipeline.json
# 编辑 novel-pipeline.json，填入书名/作者/体裁
```

**项目目录结构**:

```
my-novel/
├── novel-pipeline.json       ← 项目标记（Hook 自动检测）
├── state-files/              ← 本书专属
│   ├── world_setting.json
│   ├── characters.json
│   ├── foreshadowing.json
│   └── power_system.json
├── chapters/                 ← 章节文件
└── outline-volume1.md        ← 大纲
```

---

## Hook 脚本调用速查表

> 以下脚本本 Skill 目录下的 `hooks/` 子目录中。Agent 在编排流程中按需调用。
> **调用命令**: `python C:\Users\Administrator\.agents\skills\novel-pipeline\hooks\<script_name>.py`
> **输入**: 通过 stdin 传入 JSON
> **输出**: stdout 输出 JSON 结果

| 脚本 | 触发点 | 输入格式 | 输出关键字段 | 失败处理 |
|------|--------|---------|-------------|---------|
| `validate_draft.py` | 调用 generate_draft **前** | `{"arguments": {params}}` | `valid`, `errors` | 修复参数后重试 |
| `validate_polish.py` | 调用 polish_chapter **前** | `{"arguments": {params}}` | `valid`, `errors` | 修复参数后重试 |
| `check_draft_quality.py` | generate_draft **返回后** | `{"input": {args}, "output": text}` | `passed`, `issues`, `details.round1/2/3` | 重生成 |
| `check_ooc_firstory.py` | generate_draft **返回后** | `{"input": {args}, "output": text}` | `passed`, `issues` | 标记、不阻断 |
| `audit_polish.py` | polish_chapter **返回后** | `{"input": {args}, "output": text}` | `passed`, `violations`, `checks` | 重新润色 |
| `audit_publishready.py` | polish_chapter **返回后** | `{"output": text}` | `passed`, `issues`, `details` | 标记、不阻断 |
| `load_state.py` | 流水线启动时 | 无输入 | `loaded`, `summary`, `files_loaded` | 不阻断 |
| `archive_state.py` | 每章完成后 | `{"changes": {...}}` | `archived`, `message` | 记录错误 |

---

## 使用操作指引

## 环境准备

### 环境变量优先级（严格执行）
1. 系统环境变量 → 2. **全局统一配置 `~/.litellm/servers/.env`（优先，所有MCP服务密钥统一管理）** → 3. Skill本地`.env`（兜底，已不推荐使用）

### 已注册MCP服务（原生stdio/HTTP直连）
- **`novel-deepseek`** → `~/.litellm/servers/novel-deepseek/deepseek_server.py`（初稿生成）
- **`novel-doubao`** → `~/.litellm/servers/novel-doubao/doubao_server.py`（润色）
- **`litellm-firstory`** → `http://127.0.0.1:4000/mcp/firstory`（人设/OOC/剧情/战力校验）
- **`litellm-uno`** → `http://127.0.0.1:4000/mcp/uno`（全局规则/违禁词审核）
- **`litellm-publishready`** → `http://127.0.0.1:4000/mcp/publishready`（出版级质量审计）
- **`litellm-memory-novel`** → `http://127.0.0.1:4000/mcp/memory_novel`（小说分布式记忆库）

API Key与端点配置统一在 `~/.litellm/servers/.env` 中填写，完整模板见 `references/env-template.md`。

### 2. 激活 Skill

目录联结已自动建立，使用 `/new` 重启会话即可生效。
首次使用时确认 `hooks/load_state.py` 执行成功。

### 3. 开始使用

```
# 步骤 1: 初始化世界观
"帮我搭建一个仙侠世界观，宗门+修炼体系"

# 步骤 2: 创建人物
"定义主角和主要配角的人设"

# 步骤 3: 写大纲
"规划第一卷的章节大纲，30章"

# 步骤 4: 开始写章
"写第1章"  ← 触发完整三模型流水线

# 步骤 5: 继续写
"写第2章"  ← Agent 自动加载第1章的状态变更
```

### 4. 验证流水线正常

每章完成后检查:

1. 检查点 B `check_draft_quality` 输出 → 确认 `passed: true`
2. 检查点 D `audit_polish` 输出 → 确认 `passed: true`
3. `state-files/` 中的 JSON 文件已更新（version 字段递增）

### 5. 故障排查

| 问题 | 排查步骤 |
|-----|---------|
| MCP 工具未发现 | 执行 `/reload-mcp` 或 `/new` 新会话 |
| `generate_draft` 返回错误 | 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否有效 |
| `polish_chapter` 返回错误 | 检查 `.env` 中 `DOUBAO_API_KEY` 是否有效 |
| 检查点脚本报错 | 确保 Python 可执行 `httpx`, `mcp` 包 |
| state-files 加载失败 | 确认 `state-files/` 目录存在且 JSON 格式有效 |
