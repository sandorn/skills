# 记忆体治理规则

> 当前仅保留 **memory_official**（系统级 JSON 存储），小说域专用记忆 MCP 已移除。
> 所有写作相关持久化信息统一由 `tracking/` 目录下的文件管理。

## 服务定义

### memory_official（官方 JSON 存储）

| 属性 | 值 |
|------|-----|
| 用途 | 系统维护信息、全局工具规范、固定配置、后台运维记录 |
| 允许 | 查询/新增/更新系统类内容 |
| **禁止** | **不存储任何小说人物、剧情、章节、伏笔、势力设定** |

## Writer Skill 集成

writer skill 的所有写章/审查/质检管线不再依赖 MCP 记忆服务。
小说事实数据统一由以下文件管理：

- `tracking/current_state.md` — 角色位置/状态快照
- `tracking/hooks.md` — 伏笔池
- `tracking/chapter_summaries.md` — 章节摘要
- `tracking/subplot_board.md` — 支线进度板
- `tracking/emotional_arcs.md` — 情绪弧线追踪
- `tracking/resource_ledger.md` — 资源/金币账本

## 查询方式

| 查询目标 | 方式 |
|---------|------|
| 系统配置/工具规范 | `memory_official` MCP |
| 小说设定/剧情/角色 | 读 `setting/` 和 `tracking/` 目录文件 |
