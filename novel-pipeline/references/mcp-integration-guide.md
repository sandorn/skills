# novel-pipeline MCP 集成现状

> 最后更新: 2026-07-04
> 基于实地验证，非理论规划。

---

## 一、实际 MCP 服务器清单

所有 MCP 都是 **Hermes 原生 stdio** 模式（非 LiteLLM HTTP 代理）。Hook 脚本通过 **子进程 stdio** 直接调用，不经过 LiteLLM 网关。

### 1.1 已集成（pipeline 实际调用）

| MCP | 配置方式 | Hook 调用方式 | 工具数 | 状态 |
|-----|---------|--------------|--------|------|
| **novel-deepseek** | Hermes config → python deepseek_server.py | pipeline step [2] generate_draft | — | ✅ 正常 |
| **novel-doubao** | Hermes config → python doubao_server.py | pipeline step [5] polish_chapter | — | ✅ 正常 |
| **publishready** | Hermes config → npx @veldica/publishready-mcp | `audit_publishready.py` → `subprocess.Popen(["npx","-y","@veldica/publishready-mcp"])` | 16 tools | ✅ 正常 |

### 1.2 已配置但未接入 pipeline

| MCP | 配置方式 | 问题 | 建议处理 |
|-----|---------|------|---------|
| **uno** | Hermes config → node uno-mcp/dist/index.js | 3 tools(analyze/enhance/custom_enhance) 无 hook 引用 | 创建 `check_uno.py` hook 或从 config 移除 |
| **memory-novel** | Hermes config → npx @pepk/mcp-memory-sqlite | `better-sqlite3` 需 C++ 编译（本机无 VS Build Tools），实际走本地 JSON 文件 | 改用 `@modelcontextprotocol/server-memory` 或自建 Python 版 |

### 1.3 已移除

| MCP | 移除原因 |
|-----|---------|
| **firstory** | Windows ESM bug: `import()` 不接受裸 Windows 路径；且包通过 junction 安装 + pnpm monorepo，修复成本高。OOC 检查降级为 `check_ooc_firstory.py` 的本地规则检查。 |

---

## 二、publishready 调用示例（Hook 调用 MCP 的标准模式）

`audit_publishready.py` 的调用方式可作为其他 hook 调用 stdio MCP 的模板：

```python
import subprocess, json, time

def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    proc = subprocess.Popen(
        ["npx", "-y", "@veldica/publishready-mcp"],   # 命令
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    # 1. 初始化会话
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", ...}})
    proc.stdin.write(init + "\n"); proc.stdin.flush(); time.sleep(0.5)

    # 2. 通知就绪
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush(); time.sleep(0.3)

    # 3. 调用工具
    call = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                       "params": {"name": tool_name, "arguments": arguments}})
    proc.stdin.write(call + "\n"); proc.stdin.flush()

    # 4. 读取响应
    stdout, stderr = proc.communicate(timeout=60)
    # 解析 stdout 中的 JSON-RPC 响应行
    for line in stdout.split("\n"):
        if line.strip().startswith("{"):
            msg = json.loads(line)
            if "result" in msg:
                return {"success": True, "data": msg["result"]}
    return {"success": False, "error": stderr[:200]}
```

### 关键要点

- **npx.cmd** 在 Windows 上需 `shell=True`（批处理文件）；纯 Node/Python 脚本不需要
- stdio MCP 协议：**先 `initialize`，再 `notifications/initialized`，再 `tools/call`**
- 每次调用都启动新进程（Hook 是独立脚本），无连接池
- publishready 的 16 tools 均已验证可用：`analyze_text`, `audit_ai_sounding_prose`, `find_hotspots`, `analyze_against_template` 等

---

## 三、uno：可用但未接入

**已确认的工具（3个）：**

| 工具 | 参数 | 用途 |
|------|------|------|
| `analyze_text` | text | 分析故事页，返回质量报告 |
| `enhance_text` | text, expansionTarget | 全技巧润色扩展 |
| `custom_enhance_text` | text, expansionTarget, enable* flags | 选择性技巧润色 |

**建议接入点：**
- 润色链路末尾（`audit_publishready` 之后或之前）
- 调用 `analyze_text` 返回内容质量报告
- 不阻断流程，只标记

---

## 四、memory-novel：方案待定

### 现状
- `@pepk/mcp-memory-sqlite` 依赖 `better-sqlite3`（需 C++ 编译），本机无 VS Build Tools，无法安装
- pipeline 实际使用本地 `state-files/*.json` 文件，由 `load_state.py` / `archive_state.py` 管理
- `utils.py` 的 `find_state_dir()` 通过查找 `novel-pipeline.json` 标记文件定位项目目录

### 可行替代方案

| 方案 | 说明 | 工作量 |
|-----|------|--------|
| **A** `@modelcontextprotocol/server-memory` | 知识图谱模型，已全局安装，9 tools | ✅ 零配置，但 schema 与 JSON 文件不匹配 |
| **B** 自建 Python sqlite3 MCP 服务器 | 用 stdlib sqlite3（无编译），schema 与现有 JSON 一致 | ~200 行 Python 代码 + Hermes config 配置 |

知识图谱方案的工具：`create_entities`, `create_relations`, `add_observations`, `search_nodes`, `read_graph` 等。

---

## 五、为什么要区分「LiteLLM HTTP 代理」和「Hermes 原生 stdio」

| | LiteLLM HTTP 代理 | Hermes 原生 stdio |
|---|---|---|
| 工具可见性 | 通过 `/mcp/{name}` SSE 端点暴露 | Hermes 启动时自动发现，注册为 `mcp_{name}_{tool}` |
| 调用端 | 任何 HTTP 客户端 | 仅 Hermes Agent 会话内可用 |
| Hook 脚本能否调用 | ✅ 可 POST JSON-RPC 到 LiteLLM | ❌ 需另起子进程 |
| 典型用途 | 开发工具(playwright, github, filesystem) | 专属服务(publishready, uno, memory) |

**现状**：novel-pipeline 的 MCP 全部走 **Hermes 原生 stdio**。Hook 脚本通过 **子进程** 直接调用 stdio 方式，不依赖 LiteLLM 代理。

---

## 六、Hermes config.yaml 中的 memory-novel 配置说明

```yaml
memory-novel:
    command: npx
    args: [-y, '@pepk/mcp-memory-sqlite']
    env:
        MEMORY_DB_DIR: './novel-project/.memory'   # 相对路径，以 Hermes workspace 为根
        MEMORY_PROJECT: novel
    enabled: true
```

- `MEMORY_DB_DIR` 使用相对路径，指向小说项目目录内
- 切换项目时只需修改 `./novel-project/` 部分
- 当前 Hermes workspace 在 `D:\Writer` 时，数据库建在 `D:\Writer\novel-project\.memory\`
