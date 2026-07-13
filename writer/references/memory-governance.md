# 记忆体治理规则（v8.4）

> writer skill v8.4 起，小说的**人物 / 势力 / 剧情节点 / 伏笔 / 世界观 / 力量体系**统一存入 `novel_project` MCP。
> 项目目录只保留：**setting/**（人手写静态约束）、**outline/**（大纲）、**chapters/**（正文）、**novel.json**（元数据）。
> **禁止**任何脚本或 Agent 向 `.writer/state/*.json` 写入这些数据。

**权威工具契约**：见 `references/memory-mcp.md`（8 个工具目录 + 写入/检索/命名规范）。

---

## 存储位置总览

| 内容类型 | 存储位置 | 谁写 | 谁读 |
|---|---|---|---|
| 世界观/角色/战力/势力（**静态设定原稿**）| `setting/*.md` | 用户手写为主 | 主 Agent + 4 个审查子代理 |
| 大纲（章纲/卷纲/总纲）| `outline/*.md` | 用户 + Agent 协作 | 主 Agent |
| 章节正文 | `chapters/ch_NNN.md` | 主 Agent 主写 | 全部 |
| **当前状态（修为/待回收伏笔/新势力/剧情节点）** | **`novel_project` MCP** | Agent 每章末调 `create_entities` / `create_relations` | Agent 写章前 `search_nodes` / `get_entity_with_relations` |
| 用户规划意图 | `setting/*.md` 里的 `<!-- user-edit -->` 块（若保留 tracking 派生） | 用户手写 | 主 Agent |
| 项目元数据（stage / chapters_done） | `novel.json` | Agent 更新 | Agent |

---

## 禁令（v8.4 强制）

- ❌ **禁止**向 `.writer/state/*.json` 写入任何数据。这些文件在 v8.4 已废弃。老项目应跑一次 `import_state_to_mcp.py` 完成迁移后删除。
- ❌ **禁止**使用其他记忆 MCP（memory-novel / memory_official）存放小说内容。**唯一记忆 MCP 是 `novel_project`**。
- ❌ **禁止**在 `setting/*.md` 里存"当前状态"（如"苏白当前练气四层"）—— 这是 MCP 的职责。setting 只放**开局静态设定**。
- ❌ **禁止**在 MCP 里存自由格式长文（背景故事 500 字塞成一条观测）—— 拆成多条 `chNNN: xxx` 格式的原子观测。
- ❌ **禁止**通过 `create_entities` 直接覆盖已有实体（会删掉全部旧观测）。追加必须先 `get_entity_with_relations` 再合并写回。见 `memory-mcp.md` §4.1。
- ❌ **禁止**在 observations 里描述关系（"苏白师父是李道人"应建 `师承` 关系，不写入观测）。
- ❌ **禁止**给实体传入 `embedding` 字段（MCP 底层不支持向量，会被静默丢弃）。

---

## 归档触发

| 触发时机 | 执行流程 |
|---|---|
| **每章写完（write.md Step 5）** | Agent 提取本章原子事实 → 对每个受影响实体先 `get_entity_with_relations` → 合并旧+新观测 → `create_entities` 写回 → 新关系用 `create_relations` |
| **审查发现新事实（review-cycle Step 4）** | 同上；额外检查伏笔状态是否需要建 `回收于` 关系 |
| **卷末盘点** | 用户/主 Agent 手动补充遗漏事实；参考 `references/track-character-state.md` |
| **新增角色/势力/剧情** | 必须**先**建 MCP 实体，**后**才能在正文中出现。禁止先写章节后补记忆。 |

归档后**不再**跑 `render_tracking.py`（v8.4 起 tracking 派生已废，人读快照由 `report_graph.py` 按需生成）。

---

## 续写前检索（写章前必做）

写新章节前，Agent **必须**先查询相关记忆，防止 OOC / 设定漂移：

1. 主要出场角色：对每人调 `get_entity_with_relations({name})`，读回当前状态 + 关系网
2. 涉及势力：同上
3. 相关伏笔：`search_nodes({query: "伏笔:", limit: 50})` 后过滤未回收的
4. 若章纲提及新地点/新术法，先 `search_nodes` 确认是否已存在同名实体（避免重复建）

**未做上述检索直接写章 → 视为违反 v8.4 写章契约，需要重写**。

---

## 相关文档

- `references/memory-mcp.md` — MCP 工具目录 + 命名规范 + 调用契约（权威）
- `references/write.md` — 写章管线 Step 5 归档
- `references/review-cycle.md` — 审查 Step 4 事实增量校验
- `scripts/archive_facts.py` — Step 5 归档辅助（生成 MCP payload）
- `scripts/import_state_to_mcp.py` — 老项目一次性迁移
