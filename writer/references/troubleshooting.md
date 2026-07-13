# 常见故障排除

---

## 写章时

| 症状 | 原因 | 解决 |
|------|------|------|
| 初稿字数不足 | 句短低估了实际字数 | 初稿瞄准 3200+ 字；写到 60% 处检查 |
| 「不是…而是…」反复出现 | 英语 "not X but Y" 思维惯性 | 写完先跑 `audit.py`，命中则逐句改 |
| 子代理返回但质量差 | 迭代预算不够 | 单批 ≤5 章；context 必须含完整禁令 |
| 文件写入后含 `\"` | JSON 转义残留 | 全文用「」不用 `""`；`audit.py --fix-escaped` 自动修复 |

## 审查时

| 症状 | 原因 | 解决 |
|------|------|------|
| audit.py 报 "不是文件也不是目录" | 路径不存在 | 检查 `chapters/` 目录是否存在 |
| `novel_project` MCP `search_nodes` 返回空 | 老项目未迁移 / 新项目未 seed | 跑 `import_state_to_mcp.py`（老项目）或补 `project-init` 首批 seed（新项目） |
| 段落超标 | 手工追加内容未拆分 | `python scripts/split_paragraphs.py --batch chapters/` |
| 字数不足反复出现 | 章末场景单薄 | 手工扩充 1-2 段感官细节/配角反应 |

## 委派时

| 症状 | 原因 | 解决 |
|------|------|------|
| 子Agent 返回"已修复"但实际未修 | patch 静默失败 | 主会话抽样验证；机械修复不委派 |
| 子Agent 违反禁令 | context 未含完整禁令清单 | context 显式列出全部 P0 禁令 |
| 子Agent 超时 | 分配给单 Agent 的章节太多 | 单 Agent ≤5 章(写) / ≤40 章(审) |

## 修复时

| 症状 | 原因 | 解决 |
|------|------|------|
| 批量替换导致语句断裂 | 正则替换不精确 | 禁止对正文使用正则批量替换；逐句手工修复 |
| split_paragraphs 后段落反而更多 | 拆分后未检查连贯性 | 拆分后通读一遍确认 |

## novel_project MCP

| 症状 | 原因 | 解决 |
|------|------|------|
| `claude mcp list` 显示 `✘ Failed to connect` | Node ABI 版本不匹配 / npx 缓存失效 | 参见 `references/memory-mcp.md` §7；清 `%LOCALAPPDATA%\npm-cache\_npx` 后重试 |
| `create_entities` 覆盖了旧观测 | 直接写入而未 merge | 严格走 `archive_facts.py` 生成的 read→merge→write 三段式，见 `memory-mcp.md` §4.1 |
| `search_nodes` 找不到已建的实体 | 查询词与 name/observations 字面差异大 | 用多同义词并列查询；或直接 `get_entity_with_relations` 走精确名字 |
| 传入 `embedding` 字段被忽略 | mcp-memory-sqlite@0.0.4 不支持向量 | 已实测确认；用 FTS 多词组合替代，见 `memory-mcp.md` §4.3 |
| `novel_project.db` 文件损坏 | 写入中断 | 删除 `~/.agents/skills/writer/memory/novel_project.db` → 跑 `import_state_to_mcp.py` 从 setting/*.md 重新 seed |
| 多本书数据混在同一 db | 单 MCP 实例默认共库 | 用 `import_state_to_mcp.py --project-prefix <书名>` 命名空间隔离，或在 `.claude.json` 里为每本书起独立 SQLITE_DB_PATH |
