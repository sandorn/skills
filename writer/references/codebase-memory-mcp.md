# codebase-memory-mcp 使用指南

> [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) v0.8.1
> 9000+ ★ | 代码知识图谱 MCP 服务器 | 单二进制文件，零依赖

## 是什么

将代码库索引为持久化知识图谱，通过 MCP 协议暴露给 AI 编码代理。对写作项目的价值：**项目管理而非内容搜索**。

| 能做 | 不能做 |
|------|--------|
| 文件结构总览（architecture） | 搜索章节正文内容 |
| 按文件名查文件（Cypher） | 语义搜索散文/对话文本 |
| 文件数量统计 | 全文 BM25 搜索章内文字 |
| 代码符号搜索（函数/类名） | 索引 .md 文件内容 |
| 项目状态监测（index_status） | |

## 安装与配置

```bash
# 下载安装
curl -fsSL https://github.com/DeusData/codebase-memory-mcp/releases/latest/download/install.sh | bash

# Windows: 手动下载 .exe 到 ~/.local/bin/
```

### Hermes config.yaml 配置

```yaml
mcp_servers:
  codebase-memory-mcp:
    command: C:/Users/<user>/.local/bin/codebase-memory-mcp.exe
    # 可选：指定超时
    connect_timeout: 60
    timeout: 120
```

配置后需重启 Hermes 会话才能注册 MCP 工具。

## CLI 回退模式

当 MCP 工具未注册到当前会话时（如机器重启后），使用 CLI 模式直接调用：

```bash
codebase-memory-mcp.exe cli <工具名> '<JSON参数>'
```

**注意**：stderr 会输出 `level=info` 日志，用 `2>/dev/null` 过滤以获得纯净 JSON。

## 已验证可用的工具（v0.8.1）

### list_projects — 列出所有已索引项目

```bash
codebase-memory-mcp.exe cli list_projects 2>/dev/null
# {"projects":[{"name":"D-Writer","root_path":"D:/Writer","nodes":823,"edges":872,"size_bytes":2228224}]}
```

### get_architecture — 项目架构总览

```bash
codebase-memory-mcp.exe cli get_architecture '{"project":"D-Writer"}' 2>/dev/null
```

返回：节点标签分布、边类型、语言分布、入口点、热点、聚类、完整文件树。

### query_graph — Cypher 图查询

**已验证的运算符**：`STARTS WITH`、`ENDS WITH`、`AND`、`OR`、`=`（英文值）。
**不支持的运算符**：`CONTAINS`、`=~`（正则）、中文值精确匹配 `=`。

```bash
# ✅ 统计文件数
MATCH (f:File) WHERE f.name STARTS WITH "ch" RETURN count(f)

# ✅ 按文件名前缀查找（推荐）
MATCH (f:File) WHERE f.name STARTS WITH "ch18" RETURN f.name ORDER BY f.name LIMIT 10

# ✅ 多条件组合
MATCH (f:File) WHERE f.name STARTS WITH "ch18" OR f.name STARTS WITH "ch2" RETURN f.name

# ❌ CONTAINS 不支持（静默失败/空结果）
# MATCH (f:File) WHERE f.name CONTAINS "通道" RETURN f.name  ← 不工作！

# ✅ 查看节点属性
MATCH (f:File) RETURN f.name, properties(f) LIMIT 5

# ✅ 查看所有标签
MATCH (n) RETURN DISTINCT labels(n) LIMIT 10

# ✅ 函数调用链
MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a.name, b.name
```

### index_status — 索引状态

```bash
codebase-memory-mcp.exe cli index_status '{"project":"D-Writer"}' 2>/dev/null
# {"project":"D-Writer","nodes":823,"edges":872,"status":"ready"}
```

### trace_path — 函数调用路径追踪

```bash
codebase-memory-mcp.exe cli trace_path '{"project":"D-Writer","function_name":"main"}' 2>/dev/null
# 返回：callees（被调函数，含跳数）+ callers（调用者）
```

### get_code_snippet — 获取代码片段

```bash
codebase-memory-mcp.exe cli get_code_snippet '{"project":"D-Writer","file_path":"tool/export-chapters.js"}' 2>/dev/null
```

⚠️ 对 .md 文件可能返回空（v0.8.1）。

⚠️ **仅搜索代码符号**（函数名、类名、变量名），不搜索 .md 正文内容。对写作项目基本无用。

```bash
# 能搜到：JavaScript 函数名
codebase-memory-mcp.exe cli search_graph '{"project":"D-Writer","query":"parseChapterFile"}'
```

## 已知限制

1. **File 节点无 path 属性**：Cypher 查询返回的 File 节点只有 `name` 和 `extension`，路径需通过 `get_architecture` 的 `file_tree` 获取。
2. **search_graph name_pattern 有 bug**：返回 "project not found" 尽管项目存在（v0.8.1）。
3. **semantic_query 返回空**：对纯 .md 项目可能未生成嵌入向量。
4. **不索引 .md 正文**：文件内容不进入知识图谱，无法通过 `search_graph` 搜索章节内文字。
5. **CONTAINS 在 WHERE 子句中不支持**：`WHERE f.name CONTAINS "通道"` 静默失败或返回空。替代方案：用 `STARTS WITH` 前缀匹配，或 `get_architecture` 获取全量文件树后本地过滤。
6. **中文值精确匹配 `=` 不可靠**：`WHERE f.name = "正文"` 或 `WHERE f.name = "大纲"` 静默失败。英文名匹配正常。
7. **多步 MATCH + 中文 WHERE 组合失败**：`MATCH (p)-[:CONTAINS_FOLDER]->(r) WHERE r.name = "重生2001"` 不工作。单步 MATCH 无 WHERE 可以。
8. **get_code_snippet 对 .md 文件返回空**：仅对代码文件（.js/.py）有效（v0.8.1）。
9. **stderr 输出 `level=info` 会污染 JSON**：必须 `2>/dev/null`。

## 对写作项目的实用场景

```bash
# 1. 快速确认章节文件是否存在（STARTS WITH 前缀匹配）
codebase-memory-mcp.exe cli query_graph '{"project":"D-Writer","query":"MATCH (f:File) WHERE f.name STARTS WITH \"ch01\" RETURN f.name"}' 2>/dev/null

# 2. 统计所有 md 文件数
codebase-memory-mcp.exe cli query_graph '{"project":"D-Writer","query":"MATCH (f:File) WHERE f.extension = \".md\" RETURN count(f)"}' 2>/dev/null

# 3. 查看文件树（get_architecture 比 ls 快，且跨子项目）
codebase-memory-mcp.exe cli get_architecture '{"project":"D-Writer"}' 2>/dev/null

# 4. 按命名规律找章节（STARTS WITH 前缀匹配，不能直接用 CONTAINS）
# 先获取全量文件名，再 python 本地过滤中文关键词
codebase-memory-mcp.exe cli query_graph '{"project":"D-Writer","query":"MATCH (f:File) WHERE f.name STARTS WITH \"ch\" RETURN f.name ORDER BY f.name"}' 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d['rows']:
    name=r[0]
    if '通道' in name or '系统' in name or '互通' in name:
        print(f'  {name}')
"

# 5. 函数调用链追踪（对 writer 的 tool/ 下的脚本）
codebase-memory-mcp.exe cli trace_path '{"project":"D-Writer","function_name":"main"}' 2>/dev/null
```

⚠️ **内容搜索仍用 grep/search_files**：`codebase-memory-mcp` 不索引 .md 正文，搜「通道稳定度在哪些章节提过」这类问题必须用 `search_files` grep 全文。
