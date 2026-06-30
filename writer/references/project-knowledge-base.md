# 项目知识库使用指南

> **适用范围**：已部署外部知识库工具(index-tool)的项目。**不适用**：未部署该工具的标准项目——直接使用 `fact_db.py` + `report_panorama.py` 即可。
> **加载时机**：仅在项目配置了知识库且需要索引级查询时。**非核心管线组件**。
> 如果你的 AI 环境提供了项目索引工具，可参考本文档的使用模式。

## 是什么

将项目目录索引为可查询的知识图谱，通过标准协议暴露给 AI 编码/写作代理。对写作项目的价值：**项目管理而非内容搜索**。

| 能做 | 不能做 |
|------|--------|
| 文件结构总览（architecture） | 搜索章节正文内容 |
| 按文件名查找文件 | 语义搜索散文/对话文本 |
| 文件数量统计 | 全文 BM25 搜索章内文字 |
| 符号搜索（函数/类名） | 索引 .md 文件正文内容 |
| 项目状态监测 | |

## 安装与配置

根据你的 AI 环境选择对应的项目索引工具：

- **通用方案**：使用项目自带的 `scripts/` 下的查询脚本（`fact_db.py`、`report_panorama.py`）替代知识图谱工具的大部分功能
- **外部工具**：可选择任意支持文件索引的命令行工具，将其路径配置到环境设置中

### 环境配置

```yaml
# 示例：在 AI 环境配置中添加外部工具
tools:
  project_index:
    command: /path/to/index-tool
    connect_timeout: 60
    timeout: 120
```

配置后需重启 AI 会话才能注册新工具。

## CLI 回退模式

当项目索引工具未注册到当前会话时（如重启后），使用 CLI 模式直接调用：

```bash
<index-tool> cli <工具名> '<JSON参数>'
```

**注意**：stderr 可能输出日志信息，用 `2>/dev/null` 过滤以获得纯净 JSON。

## 已验证可用的查询模式

> 以下使用 `index-tool` 作为占位符，替换为你实际安装的工具名。

### list_projects — 列出所有已索引项目

```bash
index-tool cli list_projects 2>/dev/null
```

### get_architecture — 项目架构总览

```bash
index-tool cli get_architecture '{"project":"<project-name>"}' 2>/dev/null
```

返回：节点标签分布、边类型、语言分布、入口点、热点、聚类、完整文件树。

### query_graph — 图查询

**已验证的运算符**：`STARTS WITH`、`ENDS WITH`、`AND`、`OR`、`=`（英文值）。
**可能不支持的运算符**：`CONTAINS`、`=~`（正则）、中文值精确匹配 `=`。

```bash
# ✅ 统计文件数
MATCH (f:File) WHERE f.name STARTS WITH "ch" RETURN count(f)

# ✅ 按文件名前缀查找（推荐）
MATCH (f:File) WHERE f.name STARTS WITH "ch18" RETURN f.name ORDER BY f.name LIMIT 10

# ✅ 多条件组合
MATCH (f:File) WHERE f.name STARTS WITH "ch18" OR f.name STARTS WITH "ch2" RETURN f.name

# ✅ 查看节点属性
MATCH (f:File) RETURN f.name, properties(f) LIMIT 5

# ✅ 查看所有标签
MATCH (n) RETURN DISTINCT labels(n) LIMIT 10

# ✅ 函数调用链
MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a.name, b.name
```

### index_status — 索引状态

```bash
index-tool cli index_status '{"project":"<project-name>"}' 2>/dev/null
```

### trace_path — 函数调用路径追踪

```bash
index-tool cli trace_path '{"project":"<project-name>","function_name":"main"}' 2>/dev/null
```

### get_file_snippet — 获取文件片段

```bash
index-tool cli get_file_snippet '{"project":"<project-name>","file_path":"tool/export.py"}' 2>/dev/null
```

⚠️ 对 .md 文件可能返回空（取决于工具实现）。

⚠️ **符号搜索通常仅搜索代码符号**（函数名、类名、变量名），不搜索 .md 正文内容。对写作项目基本无用。

## 已知限制

1. **File 节点可能缺少 path 属性**：查询返回的 File 节点可能只有 `name` 和 `extension`，完整路径需通过 `get_architecture` 的 `file_tree` 获取
2. **语义搜索可能返回空**：对纯 .md 项目可能未生成嵌入向量
3. **不索引 .md 正文**：文件内容通常不进入知识图谱，无法通过图查询搜索章节内文字
4. **CONTAINS 在 WHERE 子句中可能不支持**：替代方案为用 `STARTS WITH` 前缀匹配，或获取全量文件树后本地过滤
5. **中文值精确匹配不可靠**：英文名匹配通常更稳定
6. **stderr 可能输出日志污染 JSON**：建议 `2>/dev/null`

## 对写作项目的实用场景

```bash
# 1. 快速确认章节文件是否存在（前缀匹配）
index-tool cli query_graph '{"project":"<project>","query":"MATCH (f:File) WHERE f.name STARTS WITH \"ch01\" RETURN f.name"}' 2>/dev/null

# 2. 统计所有 md 文件数
index-tool cli query_graph '{"project":"<project>","query":"MATCH (f:File) WHERE f.extension = \".md\" RETURN count(f)"}' 2>/dev/null

# 3. 查看文件树（比 ls 快，且支持跨子项目）
index-tool cli get_architecture '{"project":"<project>"}' 2>/dev/null

# 4. 按命名规律找章节
index-tool cli query_graph '{"project":"<project>","query":"MATCH (f:File) WHERE f.name STARTS WITH \"ch\" RETURN f.name ORDER BY f.name"}' 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d['rows']:
    name=r[0]
    if '通道' in name or '系统' in name or '互通' in name:
        print(f'  {name}')
"

# 5. 函数调用链追踪（对 writer 的 scripts/ 下的脚本）
index-tool cli trace_path '{"project":"<project>","function_name":"main"}' 2>/dev/null
```

⚠️ **内容搜索仍用 grep/全文搜索**：知识图谱工具通常不索引 .md 正文，搜「某概念在哪些章节提过」这类问题必须用全文搜索工具 grep 扫描章节文件。

## 降级方案

如果项目索引工具不可用，使用项目自带的脚本替代：

| 原本需求 | 降级命令 |
|---------|---------|
| 文件结构总览 | `python scripts/report_panorama.py` |
| 章节文件统计 | `ls chapters/ch_*.md \| wc -l` |
| 设定文件状态 | `wc -l setting/*.md` |
| 事实数据查询 | `python scripts/fact_db.py query` |
| 项目健康评分 | `python scripts/report_panorama.py` |
