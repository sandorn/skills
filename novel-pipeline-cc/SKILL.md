---
name: novel-pipeline
version: "1.0"
description: "三模型网文写作流水线：DeepSeek-V4-PRO 初稿 → 豆包-2.1-turbo 润色 → Claude CLI 调度管控"
category: writing
tags: [网文, 写作, pipeline, deepseek, doubao, MCP]

# === 工具白名单（Layer 1 权限锁定）===
allowed-tools:
  - "MCP:novel-deepseek.generate_draft"
  - "MCP:novel-doubao.polish_chapter"

# === 全生命周期 Hooks（Layer 1 底层拦截）===
hooks:
  PreToolUse:
    - matcher: "MCP:novel-deepseek.generate_draft"
      hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/validate_draft.py"
    - matcher: "MCP:novel-doubao.polish_chapter"
      hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/validate_polish.py"
  PostToolUse:
    - matcher: "MCP:novel-deepseek.generate_draft"
      hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/check_draft_quality.py"
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/check_ooc_firstory.py"
    - matcher: "MCP:novel-doubao.polish_chapter"
      hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/audit_polish.py"
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/audit_publishready.py"
  SessionStart:
    - hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/load_state.py"
  Stop:
    - hooks:
        - type: "command"
          command: "python C:/Users/Administrator/.claude/skills/novel-pipeline/hooks/archive_state.py"
---

# Novel-Pipeline：三模型网文写作流水线

## Skill 整体说明

本 Skill 是一套完整的网文写作自动化流水线调度系统，基于**三模型分工隔离**架构：

| 角色 | 模型 | 职责 |
|------|------|------|
| **调度中枢** | Claude CLI（本 Skill） | 任务拆解、规则下发、质量校验、伏笔存档、流程分发 |
| **初稿生成** | DeepSeek-V4-PRO | 仅产出平铺直白剧情骨架，禁止任何文笔修饰 |
| **后置润色** | 豆包-2.1-turbo | 仅做文字优化，强制锁定全部剧情/人物/事件 |

**核心优势**:
- 三模型各司其职，职责完全切割，互不越界
- Hooks 底层拦截 + 工具白名单，确定性执行，不依赖模型自觉
- 全生命周期自动化: 会话启动自动加载设定 → 写章自动校验 → 会话结束自动归档
- 润色开关 + 简单章跳过，节约 token 成本
- 统一标准透传：全书设定由 Claude 统一管理，下发时同步携带

**适用场景**: 长篇网文连载、批量章节生成、已有设定体系的系列写作。

---

## 模块1：Claude CLI 主调度核心

### Layer 1 规则（最高权重、不可修改）

#### 1.1 流水线指挥官定位

你（Claude CLI）是流水线指挥官，**绝对禁止**以下行为：
- 禁止自行生成长篇正文（>200 字的小说内容）
- 禁止自行润色文本（润色是豆包的职责）
- 禁止跳过自检流程直接输出
- 禁止绕过 MCP 工具直接调用 DeepSeek/豆包 API

你**只做**以下事：
- 理解用户意图 → 路由到正确链路
- 从 state-files 提取上下文 → 组装参数
- 调用 MCP 工具下发任务
- 读取 Hook 返回的校验结果 → 决策是否重生成
- 汇总输出 → 归档状态

#### 1.2 工具白名单

仅允许调用以下 MCP 工具（由 `allowed-tools` 元配置锁定）：
- `novel-deepseek.generate_draft` — 初稿生成
- `novel-doubao.polish_chapter` — 润色

任何其他工具调用与本流水线无关。

#### 1.3 全局剧情禁忌

以下内容在任何情况下不得出现在产出中（Layer 1 红线）：
- 现实政治影射、敏感历史事件
- 色情/低俗描写
- 鼓吹违法犯罪、反社会行为
- 平台违禁内容（具体以目标发布平台规则为准）

#### 1.4 人设底线

主角人设一旦在 `state-files/characters.json` 中定义，以下字段不可突破:
- `core_values`（核心价值观）—— 除非在细纲中明确标注"价值观转变"弧线
- `bottom_lines`（行为底线）—— 突破底线必须有足够的铺垫（≥3 章）
- `personality_traits`（性格底色）—— 极端情境下可暂时偏离，但需在下章回归

---

### Layer 2 规则（硬性执行）

#### 1.5 任务自动分层路由

根据用户输入自动识别任务类型，路由至对应链路。完整路由表见 `references/task_routing.md`。

**快速参考**:

| 用户意图 | 触发词 | 处理链路 |
|---------|--------|---------|
| 初始化设定 | 世界观/设定/力量体系/势力 | Claude 引导填写 state-files → 无下游调用 |
| 大纲编排 | 大纲/章纲/全书结构/分卷 | Claude 辅助规划 → 写入项目章纲文件 |
| **写单章** | 写第N章/写一章 | **完整流水线**: DeepSeek→自检→[润色开关]→豆包→输出 |
| 章节返工 | 重写/修改第N章 | 读取现有章→DeepSeek(含修订指令)→自检→输出 |
| 独立润色 | 润色/文笔修饰 | 读取文本→直接豆包润色 |
| 批量生成 | 批量/连续/第X-Y章 | 逐章循环 + 每章归档 |
| 伏笔审查 | 伏笔/回收/查伏笔 | 读取 foreshadowing.json → 生成报告 |

#### 1.6 写单章标准执行流程

```
1. Claude 准备参数:
   ├─ 读取 state-files/world_setting.json → 提取本章相关摘要 → global_setting
   ├─ 读取 state-files/characters.json → 确认本章出场角色状态
   ├─ 从用户输入/大纲文件中获取 → chapter_outline
   └─ 解析章节编号 → chapter_number

2. 调用 MCP: generate_draft(global_setting, chapter_outline, chapter_number)
   ├─ PreToolUse Hook: validate_draft.py 校验参数完整性
   ├─ PostToolUse Hook: check_draft_quality.py 执行结构自检
   └─ PostToolUse Hook: check_ooc_firstory.py 执行人设一致性校验（firstory MCP）

3. Hook 返回结果评估:
   ├─ passed=true → 进入步骤 4
   └─ passed=false → 读取 issues → 组装 revision_instructions
       └─ 调用 generate_draft(..., revision_instructions) → 返回步骤 2
       └─ 最多重试 2 次 → 超限则选最优版本 + 标注问题

4. 润色开关判定（见 1.8）:
   ├─ SKIP_POLISH=true → 直接输出 DeepSeek 初稿 → 跳至步骤 6
   └─ SKIP_POLISH=false → 进入步骤 5

5. 调用 MCP: polish_chapter(chapter_characters, chapter_mood_tone, draft_text)
   ├─ PreToolUse Hook: validate_polish.py 校验参数完整性
   ├─ PostToolUse Hook: audit_polish.py 执行 RED LINE 审计
   └─ PostToolUse Hook: audit_publishready.py 执行出版级文本审计（publishready MCP）

6. 输出最终章节 + 执行归档:
   └─ 提取本章新增伏笔/人物变动 → 写入 state-files
```

#### 1.7 3 轮自检协议（Claude 端语义检查）

Hook `check_draft_quality.py` 执行结构性检查后，Claude 需要执行深层语义检查。详见 `references/quality_check.md`。

**检查清单**:
1. **Round 1 — OOC 检查**（已自动化）: Hook `check_ooc_firstory.py` 调用 firstory MCP 执行人设一致性校验。Claude 仅需复核标记的可疑项。
2. **Round 2 — 剧情执行检查**: 细纲中的关键剧情点覆盖率 ≥ 80%？窗口期伏笔是否被推进？
3. **Round 3 — 逻辑冲突检查**: 战力是否崩坏？设定是否自相矛盾？时间线是否合理？
4. **Round 4 — 出版审计**（已自动化）: Hook `audit_publishready.py` 调用 publishready MCP 执行 AI 腔检测、可读性打分、热点定位。

**重生成决策**:
- 任一 round 不通过 → 汇总 issues → `revision_instructions` → 重新调用 `generate_draft`
- 第 2 次重试 → 仅保留 Round 1 + Round 3，放宽 Round 2
- 第 3 次仍失败 → 选最优版本 + 标注 `⚠ 需人工介入`

#### 1.8 润色开关分支判断

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

#### 1.9 持久化存档逻辑

**每章处理完成后自动执行**（Stop Hook `archive_state.py` 辅助）:

1. **伏笔提取**: 从本章正文中识别新增伏笔 → 记录到 `foreshadowing.json` 的 `active` 数组
2. **人物变更**: 修为变化、位置移动、情绪状态更新 → 更新 `characters.json`
3. **势力变动**: 新势力登场、同盟/敌对关系变化 → 更新 `world_setting.json`
4. **战力规则**: 如本章引入了新的战力设定 → 更新 `power_system.json`

**存档格式**: 所有变更加入 `changes` JSON 对象，传入 `archive_state.py`:
```json
{
  "foreshadowing": {"new": [...], "resolved_ids": [...], "chapter_number": N},
  "characters": [{"name": "林尘", "cultivation": "练气八层", ...}],
  "world_setting": {"factions": [...], "geography": [...]},
  "power_system": {"realms": [...], "equipment": [...]}
}
```

下一轮生成时，SessionStart Hook `load_state.py` 自动加载最新状态。

#### 1.10 下发指令标准化协议

调用下游 MCP 工具时必须使用标准参数结构：

**generate_draft 标准参数**:
```
global_setting:  <从 world_setting.json + power_system.json 提取本章相关摘要>
chapter_outline: <本章细纲（关键剧情点列表）>
chapter_number:  <整数>
revision_instructions: <首次留空，重试时填入自检反馈>
```

**polish_chapter 标准参数**:
```
chapter_characters: <仅本章出场角色状态摘要，不传全书人物>
chapter_mood_tone:  <六选一: 紧张/爽快/压抑/热血/温情/悬疑/中性>
draft_text:         <DeepSeek 原始初稿全文>
```

---

### Layer 3 规则（软性优化建议）

#### 1.11 网文节奏参考

详见 `references/webnovel_triggers.md`。Claude 在准备 `chapter_outline` 时可参考以下模式：
- 每 3-4 段一个小转折
- 每 10 段一个大节奏点
- 章末 90-95% 处埋钩子
- 打斗场景遵循探查→交锋→转折→高潮→收尾五段式

#### 1.12 文笔修饰参考

以下建议在润色环节（豆包）中生效，不强制 Cluade 层执行：
- 对话口语化（嗯、啧、靠、行吧、得嘞）
- 感官细节穿插（每场景 1-2 处声/嗅/触）
- 情绪通过身体反应外化（握拳、瞳孔收缩、呼吸急促）
- 流水账转有节奏叙事（拆分"然后…然后…"句式）

---

## 模块2：DeepSeek-V4-PRO 专属初稿生成子 Skill

> 本模块规则已完整嵌入 MCP Tool `generate_draft` 的 description 字段。
> Claude CLI 调用该工具时，规则自动生效。此处为概要参考。

**核心规则摘要**:
- 仅产出平铺直白剧情骨架，禁止修饰词句
- 禁止自主增加爽点、反转、原创细节
- 对话用「」，段落 ≤ 42 字，章末必须有钩子
- 优先保证多角色并行、跨章节伏笔回收
- 纯章节文本输出，无分析/总结/建议
- 全 token 仅服务剧情约束，无多模型兼容冗余
- **字数要求**: 期望 2800-3600 字，最低 2500 字（硬底线），最高 4500 字（超限截断）

**System Prompt**: 见 `servers/deepseek_server.py` 中的 `DRAFT_SYSTEM_PROMPT` 常量。

---

## 模块3：豆包-2.1-turbo 锁定式润色子 Skill

> 本模块规则已完整嵌入 MCP Tool `polish_chapter` 的 description 字段。
> RED LINE 规则在 Tool Description 中以 `⛔` 标记，Hook `audit_polish.py` 独立执行审计。

**RED LINE 摘要**:
- 不得修改/删除/新增/调换任何剧情事件
- 不得修改人物对话核心内容、立场、态度
- 不得增删角色选择、行为、伏笔点位

**仅开放权限**:
- 短句拆分、口语化对话、感官细节补充
- 情绪张力放大、爽点强化、消除流水账

**轻量化设计**: 仅接收本章角色状态摘要 + 情绪基调，不加载全书世界观。

**System Prompt**: 见 `servers/doubao_server.py` 中的 `POLISH_SYSTEM_PROMPT` 常量。

---

## 模块4：自动化脚本调用标准模板

两套可复用模板位于 `templates/` 目录。

### 模板A：DeepSeek 初稿请求

**文件**: `templates/draft_request.py`
**函数**: `build_draft_request(global_setting, chapter_outline, chapter_number, revision_instructions="")`
**返回**: 格式化的用户消息文本

**外部脚本调用示例** (Python):
```python
from templates.draft_request import build_draft_request
msg = build_draft_request(
    global_setting="青云宗位于青云山脉...",
    chapter_outline="1.林尘发现玉佩异动 2.遭遇探子 3.战斗突破",
    chapter_number=5
)
# msg 可直接作为 API user message
```

**外部脚本调用示例** (PowerShell):
```powershell
$msg = python templates/draft_request.py "设定..." "大纲..." 5
$body = @{model="deepseek-v4-pro"; messages=@(@{role="user"; content=$msg})} | ConvertTo-Json
```

### 模板B：豆包润色请求

**文件**: `templates/polish_request.py`
**函数**: `build_polish_request(chapter_characters, draft_text, chapter_mood_tone="中性")`
**返回**: 格式化的用户消息文本

---

## 项目隔离机制

本 Skill 支持多项目并行——每本小说独立存放状态文件，互不干扰。

**查找逻辑**（由 `hooks/utils.py` 统一实现）:
1. 从当前工作目录向上查找 `novel-pipeline.json` 项目标记文件
2. 找到 → 使用该项目下的 `state-files/` 目录（读/写）
3. 未找到 → 回退到 Skill 模板目录（只读）

**新建项目**:
```
mkdir my-novel/
cp ~/.claude/skills/novel-pipeline/state-files/*.json my-novel/state-files/
cp ~/.claude/skills/novel-pipeline/state-files/config.example.json my-novel/novel-pipeline.json
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

## 使用操作指引

### 1. 环境准备

```bash
# 安装 MCP Server 依赖
pip install mcp httpx

# 配置 API 密钥
cd ~/.claude/skills/novel-pipeline
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 和 DOUBAO_API_KEY
```

### 2. 注册 MCP Server

在 `~/.claude/settings.json` 的 `mcpServers` 中添加:

```json
"novel-deepseek": {
  "command": "C:/Users/Administrator/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe",
  "args": [
    "C:/Users/Administrator/.claude/skills/novel-pipeline/servers/deepseek_server.py"
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
},
"novel-doubao": {
  "command": "C:/Users/Administrator/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe",
  "args": [
    "C:/Users/Administrator/.claude/skills/novel-pipeline/servers/doubao_server.py"
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

### 3. 激活 Skill

重启 Claude CLI，Skill 自动被发现（`~/.claude/skills/` 目录下的所有 Skill 自动注册）。

首次使用时确认 SessionStart Hook 执行成功（输出状态加载摘要）。

### 4. 开始使用

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
"写第2章"  ← SessionStart Hook 自动加载第1章的状态变更
```

### 5. 验证流水线正常

每章完成后检查:
1. Hook `check_draft_quality` 输出 → 确认 `passed: true`
2. Hook `audit_polish` 输出 → 确认 `passed: true`
3. `state-files/` 中的 JSON 文件已更新（version 字段递增）

### 6. 故障排查

| 问题 | 排查步骤 |
|-----|---------|
| MCP 工具未发现 | 检查 settings.json 中 command 路径是否正确，Python 是否可执行 |
| generate_draft 返回错误 | 检查 .env 中 DEEPSEEK_API_KEY 是否有效 |
| polish_chapter 返回错误 | 检查 .env 中 DOUBAO_API_KEY 是否有效 |
| Hook 未执行 | 检查 settings.json 中是否启用了 hooks，hook 脚本路径是否正确 |
| state-files 加载失败 | 确认 state-files/ 目录存在且 JSON 格式有效 |
