# Writer Skill 文件索引与依赖图

> SKILL.md 是权威入口。本文件仅补充 SKILL.md 未覆盖的**依赖关系**信息。

## 文件→脚本依赖

| 文件 | 依赖脚本 |
|------|---------|
| `quality.md` | audit.py, split_paragraphs.py |
| `review.md` | agents/ (4 templates), audit.py |
| `review-cycle.md` | audit.py, report_panorama.py, archive_facts.py |
| `post-review-fix.md` | audit.py, split_paragraphs.py |
| `style-transfer.md` | **novel-pipeline** `polish_chapter.py`, style-sop.md, presets/ |
| `deploy.md` | audit.py, split_paragraphs.py |
| `write.md` | audit.py, archive_facts.py |
| `hard-bans.md` | audit.py (--dump-bans 校验) |
| `manual-polish.md` | 无（三零原则禁止脚本） |
| `project-init.md` | 无（seed MCP 直接调工具） |
| `memory-mcp.md` | archive_facts.py, import_state_to_mcp.py |

## 文件→MCP 依赖

| 文件 | 依赖 MCP |
|------|---------|
| `memory-mcp.md` | `novel_project`（权威规范） |
| `memory-governance.md` | `novel_project`（治理规则） |
| `write.md` Step 1/3 | `novel_project`（写章前查 + 写章后归档） |
| `review-cycle.md` Step 0/3b/4 | `novel_project`（体检 + 增量校验 + 归档） |
| `pre-write-alignment.md` Layer 4 | `novel_project`（当前世界快照） |
| `pre-write-checklist.md` | `novel_project`（快速角色/伏笔查询） |
| `cross-volume-audit.md` | `novel_project`（跨卷修为/命名/伏笔追踪） |
| `targeted-audit.md` | `novel_project`（定向审查交叉源） |
| `track-character-state.md` | `novel_project`（卷末盘点写入） |
| `style-transfer.md` | **novel-pipeline** `novel-doubao MCP` |
| DeepSeek 出稿模式 | **novel-pipeline** `novel-deepseek MCP` |

## 文风预设

| 文件 | 说明 |
|------|------|
| `presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风（novel-pipeline `polish_chapter.py --style-file` 消费）|

## 状态归档链（v8.4）

```
写章前 → get_entity_with_relations / search_nodes  ── 查 novel_project MCP
写章 → chapters/ch_NNN.md 落盘
     → archive_facts.py 读 stdin JSON → 输出 MCP tool_calls 序列（read→merge→write）
     → Agent 按 phase 顺序调 novel_project MCP：
       1. get_entity_with_relations（拿旧观测 old_obs）
       2. 合并 old_obs + new_obs（替换 <merge_with_old>）
       3. create_entities（覆盖式写回）
       4. create_relations（有向边幂等）
```

## 已移除

- `scripts/polish.py` (v8.3) → 迁至 novel-pipeline skill 的 `scripts/polish_chapter.py`
- `references/memory-novel-schema.md` (v8.3) → memory-novel MCP 已废弃，短暂用过 `.writer/state/*.json`，v8.4 迁到 `novel_project` MCP
- `.writer/state/*.json` 4 份 JSON (v8.4) → 迁到 `novel_project` MCP；老项目用 `import_state_to_mcp.py` 一次性迁移
- `tracking/*.md` 派生层 (v8.4) → 废除；人读快照按需用 `report_graph.py` 从 MCP 生成；用户 `<!-- user-edit -->` 块挪到 `setting/*.md`
- `scripts/render_tracking.py` (v8.4) → deprecated stub，不再由写章管线调用
- `pad_chapter.py` (v7.8) → 字数注入器已废弃，改为手工扩充
- `audit_5dim.py` (v7.8) → 功能已集成到 audit.py
- `backup.py` → 改用 git commit
- `publishable-check.md` → 被 review daily 吸收
- `memory.md` → v8.0 之前的旧记忆管理，历经 memory-novel MCP → `.writer/state/*.json` → v8.4 novel_project MCP
- `opening-craft.md` / `project-knowledge-base.md` / `corruption-fix-bu-shi.md` / `optimize.md` / `fix-template-cleanup.md` / 两个 gaming-manifest 项目遗留文件（v7.8 一并清理）
