---
name: novel-pipeline
version: "2.4.0-generic"
description: "通用三模型网文写作流水线：初稿生成 → 润色 → Hermes Agent 调度管控"
category: writing
tags: [网文, 写作, pipeline, MCP, hermes]
---

# novel-pipeline: 网文写作流水线（精简版）

## 体系架构

| 角色 | 组件 | 职责 |
|------|------|------|
| **调度中枢** | **Hermes Agent（本 Skill）** | 任务拆解、规则下发、质量校验、伏笔存档 |\n| **初稿生成** | MCP 服务（默认 novel-deepseek） | 产出剧情骨架，禁止文笔修饰 |\n| **后置润色** | MCP 服务（默认 novel-doubao） | 仅文字优化，锁定全部剧情/人物/事件 |\n| **自动检查** | `hooks/*.py` + 质检 MCP | 参数校验、内容质量分析(uno)、RED LINE 审计(publishready) |\n| **持久化** | `state-files/*.json` + memory-novel 知识图谱 | 世界观/人物/伏笔/战力状态管理 |

> 双模型职责完全切割，Hermes Agent 编排全流程。

---

## Layer 1 规则（最高权重，不可违反）

### 1.1 编排器定位（禁令）

⛔ 禁止自行生成长篇正文（>200 字的小说内容）
⛔ 禁止自行润色文本
⛔ 禁止跳过检查点直接输出
⛔ 禁止绕过 MCP 工具直接调用模型 API
✅ 只做：路由任务 → 提取上下文 → 调用 MCP → 执行检查脚本 → 汇总输出 → 归档

### 1.2 可用工具

| 工具 | MCP Server | 参数 |
|------|-----------|------|
| `generate_draft` | 初稿生成 MCP | `global_setting`, `chapter_outline`, `chapter_number`, `revision_instructions` |
| `polish_chapter` | 润色 MCP | `chapter_characters`, `draft_text`, `chapter_mood_tone` |
| `analyze_text` | uno MCP | `text` — 内容质量分析（通过 `check_uno.py` 调用） |
| `store_state` | memory-novel | 钩子自动同步（`archive_state.py`） |
| `search_nodes` | memory-novel | 钩子自动查询（`load_state.py`） |

### 1.3 内容红线
- 禁止：现实政治影射、色情/低俗描写、违法犯罪鼓吹、平台违禁内容

### 1.4 人设底线
主角 `core_values`/`bottom_lines`/`personality_traits` 不可突破，除非细纲标注弧线且有 ≥3 章铺垫。

---

## Layer 2 规则（硬性执行）

### 2.1 任务自动路由

| 用户意图 | 触发词 | 处理链路 |
|---------|--------|---------|
| 初始化设定 | 世界观/设定/力量体系 | 引导填写 state-files |
| 大纲编排 | 大纲/章纲 | 辅助规划 → 写入章纲文件 |
| **写单章** | 写第N章 | **完整流水线**：初稿→自检→[润色开关]→润色→输出→归档 |
| 章节返工 | 重写/修改第N章 | 读现有章 → 初稿(含修订指令) → 自检 → 输出 |
| 独立润色 | 润色/文笔修饰 | 读文本 → 直接调用润色模型 |
| 批量生成 | 批量/第X-Y章 | 逐章循环 + 每章归档 |
| 伏笔审查 | 伏笔/回收 | 读 foreshadowing.json → 报告 |

### 2.2 写单章核心流程

```
[0] 读取状态 → hooks/load_state.py + 读取 state-files/*.json + (补充) memory-novel 知识图谱查询
[1] 参数预校验 → hooks/validate_draft.py（检查点 A）
[2] MCP: generate_draft(global_setting, chapter_outline, chapter_number)
[3] 初稿自检 → hooks/check_draft_quality.py + check_ooc_firstory.py + check_uno.py（检查点 B）
    ├─ passed → 进入 [4]
    └─ failed → 组装 revision_instructions → 回到 [1]（最多重试 2 次）
[4] 润色开关判定（见 2.4）
[5] 润色链路 → validate_polish → MCP: polish_chapter → audit_polish（检查点 D）→ audit_publishready（检查点 E）→ check_uno.py（检查点 F）
[6] 输出 + 归档 → hooks/archive_state.py（state-files + memory-novel 知识图谱同步）
```

> 完整3轮自检协议 → `skill_view('novel-pipeline', 'references/quality_check.md')`

### 2.3 重生成决策
- 第 1 次重试：汇总所有 issues → `revision_instructions` → 调 `generate_draft`（retry=1）
- 第 2 次重试：仅保留 OOC + 逻辑冲突检查，放宽剧情执行检查
- 仍失败：选最优版本 → 标注 `⚠ 需人工介入`

### 2.4 润色开关判定
**任一满足自动跳过润色：**
- 过渡章节关键词命中 ≥ 3 个（前往/赶路/飞行/传送/休整/采购/日常/疗伤）
- 本章字数 < 2500
- 章节 ≤ 3（前期攒设定，后期统一润色）

### 2.5 下发指令标准化协议

**generate_draft 参数：**
```
global_setting:      <从 world_setting.json + power_system.json 提取本章相关摘要>
chapter_outline:     <本章细纲（关键剧情点列表）>
chapter_number:      <整数>
revision_instructions: <首次留空，重试时填入自检反馈>
```

**polish_chapter 参数：**
```
chapter_characters:  <仅本章出场角色状态摘要>
chapter_mood_tone:   <可选: 紧张/爽快/压抑/热血/温情/悬疑/中性>
draft_text:          <原始初稿全文>
```

### 2.6 持久化存档
每章完成后：
1. **伏笔提取** → 识别新增伏笔 → 记录到 `foreshadowing.json`
2. **人物变更** → 能力/位置/情绪更新
3. **势力变动** → 新势力/同盟关系更新
4. **规则更新** → 新设定规则写入

存档格式：`{"foreshadowing": {...}, "characters": [...], "world_setting": {...}}` → 传入 `archive_state.py`

---

## Layer 3 规则（软性优化建议）

- 每 3-4 段一个小转折，每 10 段一个大节奏点，章末 90-95% 埋钩子
- 对话口语化（符合人物性格），感官细节每场景 1-2 处
- 情绪通过身体反应外化（握拳、瞳孔收缩等）
- 拆分"然后…然后…"流水账句式
- ⮕ 详见 `skill_view('novel-pipeline', 'references/webnovel_triggers.md')`

---

## Hook 脚本调用速查

> 调用：`python <Skill路径>\hooks\<script>.py`
> 输入：stdin JSON | 输出：stdout JSON

| 脚本 | 触发点 | 关键输出 | 失败处理 |
|------|--------|---------|---------|
| `validate_draft.py` | generate_draft 前 | `valid`, `errors` | 修复重试 |
| `validate_polish.py` | polish_chapter 前 | `valid`, `errors` | 修复重试 |
| `check_draft_quality.py` | 初稿返回后 | `passed`, `issues` | 重生成 |
| `check_ooc_firstory.py` | 初稿返回后 | `passed`, `issues` | 标记不阻断 |
| **`check_uno.py`** | 初稿/润色返回后 | `passed`, `analysis` | 标记不阻断 |
| `audit_polish.py` | 润色返回后 | `passed`, `violations` | 重新润色 |
| `audit_publishready.py` | 润色返回后 | `passed`, `issues` | 标记不阻断 |
| `load_state.py` | 流水线启动 | `loaded`, `summary` | 不阻断 |
| `archive_state.py` | 每章完成 | `archived`, `message` | 记错 |

---

## MCP 服务器集成状态

详细集成状态见 `skill_view('novel-pipeline', 'references/mcp-integration-guide.md')`。速览：

| MCP 服务 | 类型 | 实际调用 | 状态 |
|---------|------|---------|------|
| novel-deepseek | 原生 stdio | ✅ pipeline step [2] | 正常 |
| novel-doubao | 原生 stdio | ✅ pipeline step [5] | 正常 |
| publishready | 原生 stdio | ✅ `audit_publishready.py` 子进程调用 | 正常 |
| uno | 原生 stdio | ✅ `check_uno.py` 子进程调用(analyze_text) | 正常 |
| memory-novel | 原生 stdio | ✅ `load_state.py` 读取 + `archive_state.py` 写入 | 正常(标准 memory server) |
| firstory | — | 🗑️ 已移除(Windows ESM bug) | OOC 降级本地规则 |

---

## 详细参考（按需加载）

| 内容 | 加载方式 |
|------|---------|
| 部署指南 + MCP 客户端配置 | `skill_view('novel-pipeline', 'references/deployment-guide.md')` |
| 环境变量模板 | `skill_view('novel-pipeline', 'references/env-template.md')` |
| 3 轮自检详细协议 | `skill_view('novel-pipeline', 'references/quality_check.md')` |
| 任务路由决策树 | `skill_view('novel-pipeline', 'references/task_routing.md')` |
| 项目隔离 + 新建项目 + 升级 | `skill_view('novel-pipeline', 'references/project-setup.md')` |
| 使用指引 | `skill_view('novel-pipeline', 'references/usage-guide.md')` |
| 故障排查 | `skill_view('novel-pipeline', 'references/troubleshooting.md')` |
| **MCP 集成现状（推荐先看这个）** | `skill_view('novel-pipeline', 'references/mcp-integration-guide.md')` |
| 旧版升级 | `skill_view('novel-pipeline', 'references/legacy-project-upgrade.md')` |
| 流派适配参考 | `skill_view('novel-pipeline', 'references/genre-adaptation.md')` |
| 项目配置模板 | `state-files/config.example.json` |
| 批量审计脚本 | `scripts/batch_audit.py` |
| 环境诊断脚本 | `scripts/verify_env.py` |
