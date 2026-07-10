# 记忆体治理规则（v8.3）

> writer skill v8.3 起，小说数据的**统一存储位置**是项目内的四层结构，不使用任何外部记忆 MCP。

## 存储位置总览

| 内容类型 | 位置 | 谁写 | 谁读 |
|---|---|---|---|
| 世界观/角色/战力/势力（静态约束）| `setting/*.md` | 用户手写为主 | 主 Agent + 4 个审查子代理 |
| 大纲（章纲/卷纲/总纲）| `outline/*.md` | 用户 + Agent 协作 | 主 Agent |
| 章节正文 | `chapters/ch_NNN.md` | 主 Agent 主写 | 全部 |
| 原子事实源（当前修为/待回收伏笔/新增势力）| `.writer/state/*.json` | `archive_facts.py` 独写 | 主 Agent + 4 个审查子代理 |
| 人读快照（渲染层）| `tracking/*.md` | `render_tracking.py` 派生 | 用户 + 主 Agent |
| 用户规划意图 | `tracking/*.md` 里的 `<!-- user-edit -->` 块 | 用户手写 | 主 Agent |

## 禁令

- ❌ **禁止**使用任何外部记忆 MCP（memory-novel / memory_official 存放小说内容）—— 小说数据必须在项目目录内
- ❌ **禁止**在 `setting/*.md` 里存"当前状态"（如"苏白当前练气四层"）—— 这是 `.writer/state/*.json` 的职责
- ❌ **禁止**在 `.writer/state/*.json` 里存自由格式描述 —— 只放结构化字段
- ❌ **禁止**在 `tracking/*.md` 手动写 Agent 该派生的表格 —— 由 render_tracking.py 生成；用户只在 `<!-- user-edit -->` 块内补充

## 归档触发

- **每章写完（write.md Step 5）**：主 Agent 构造 JSON payload → `archive_facts.py`
- **审查发现新事实（review-cycle Step 4）**：同上
- **卷末盘点（`references/track-character-state.md`）**：用户/主 Agent 深度校准后手动更新

归档后自动跑 `render_tracking.py` 派生 tracking md，保留用户 user-edit 块。
