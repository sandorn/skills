# MCP 工具发现验证（判定"代理问题"还是"服务器问题"）

> 适用：Hermes 里某个 `*_LL` 工具连不上 / `tools/list` 返回空 / 报 `Tool 'X' not found` 时，
> 定位问题归属并给出修复路径。

---

## 一、⚠️ 最容易踩的假阳性

**裸发 `tools/list` 必然返回 `tools=[]`——哪怕服务器完全正常。**

MCP 是有状态协议，工具清单只在完成握手后才可得：

```
initialize  →  notifications/initialized  →  tools/list
```

跳过前两步直接 `tools/list`，任何服务器都回空列表。
**把这当成"代理 Bug"是最常见的误诊。**

---

## 二、正确验证：三步定归属

### 第 1 步：经代理测（完整握手）

必须按顺序发三个请求，且**保持 session**（server 会下发 `mcp-session-id`，后续请求要带上）：

```
POST http://127.0.0.1:4000/mcp/<name>
Headers:
  Authorization: Bearer sk-1234
  Content-Type: application/json
  Accept: application/json, text/event-stream     ← 缺这个会 406 Not Acceptable

① {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"h","version":"1"}}}
   → 记下响应头 mcp-session-id

② {"jsonrpc":"2.0","method":"notifications/initialized"}
   → 带 mcp-session-id

③ {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
   → 带 mcp-session-id
```

**响应是 SSE 格式**，取值要剥掉 `data: ` 前缀，不是裸 JSON。

判定：
- `tools` 非空 → 正常，问题在调用姿势
- `tools: []` → 可疑，进第 2 步

### 第 2 步：直连原生 stdio（绕过代理）

这一步是**分水岭**——它决定问题在服务器还是代理。

```powershell
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | <server-executable> mcp
```

判定（看两个字段）：

| 观察 | 结论 |
|------|------|
| `tools=[{...}]` 非空，且 `serverInfo.version` **与本地二进制版本一致** | 服务器正常 → **问题在 LiteLLM 代理** |
| `tools=[{...}]` 非空，但 `serverInfo.version` **与本地二进制不一致** | 代理拉起的**不是你以为的那个进程** → 查 command/args 是否指向了别处 |
| `tools=[]` 或进程报错 | 服务器自身问题 → 查该服务器的依赖/路径 |

### 第 3 步：日志定量

```powershell
Get-Content "C:\Users\Administrator\.litellm\logs\litellm-stderr.log" -Encoding UTF8 |
  Select-String -Pattern "Successfully fetched (\d+) tools from server (\w+)$" |
  Select-Object -Last 20 | ForEach-Object { $_.Line }
```

**关键判据：看是"一个 server 是 0"还是"所有 server 都是 0"。**

- 只有目标 server 是 0 → 该 server 的问题
- **所有 server 都是 0** → LiteLLM 代理层整体缺陷，与具体 server 无关

---

## 三、常见错误信息对照

| 信息 | 性质 | 处理 |
|------|------|------|
| `Request URL is missing an 'http://' or 'https://' protocol` | LiteLLM 对 stdio server 误用 HTTP transport | **不是可忽略的误报**。错误本身无害，但伴随的 `0 tools` 是真实故障 |
| `Successfully fetched 0 tools from server X` | ⚠️ **故障信号** | 不要当成正常现象放过 |
| `Tool 'X' not found`（tools/call 返回） | 工具未注册 | 工具清单为空的下游表现 |
| `406 Not Acceptable` | 缺 `Accept: application/json, text/event-stream` 头 | 补头重试 |
| `successfully fetched 0 tools` 仅出现一次且在启动期 | 启动预取阶段 | 需与运行期调用结果交叉验证，不能只看启动日志 |

### ⚠️ 一条需要纠正的旧认知

`start.ps1` 里印有一句提示，说明 stdio 型的 `HTTP/UnsupportedProtocol` 错误是
"litellm 内部误报，**不影响服务正常使用**"。

**这句话只对了一半，照单全收会误事：**

- 错误的**进程启动**确实不受影响 —— 服务能起来，健康端点能通
- 但**工具确实没加载** —— `tools/list` 为空，客户端所有 MCP 工具不可见，**功能层面是实打实的故障**

**行动准则**：看到该错误时，**必须继续追查 `Successfully fetched N tools` 的 N 是否为 0**。
服务起得来 ≠ 你要的工具可用。

---

## 四、修复路径

| 情形 | 修复 |
|------|------|
| 单个 server 工具为 0，服务器本身正常 | 在 Hermes `config.yaml` 把该项从 HTTP 代理改为**原生 stdio 直连**；不动其余 server |
| 全部 server 工具为 0 | LiteLLM 代理层缺陷。逐个改 stdio 直连可恢复功能；整体修复需排查/升降级 LiteLLM，单独立项 |
| `serverInfo.version` 与本地不一致 | 检查代理配置的 `command`/`args` 是否指向了非预期的进程（如 npm 同名包 ≠ 本地二进制） |

### 修复选型原则

**优先外科手术式修复**：只改出问题的那一个条目，不顺手重构整段配置、
不批量改动其余 server。网关是全局单点，大面积改动风险远高于收益。

若确需整体修复，先与用户确认，作为独立任务排期。

---

## 五、可复用探针脚本

完整握手探针见同目录 `scripts/probe_mcp_endpoint.ps1`（代理侧，含 session 保持）。
直连 stdio 探针见 `scripts/probe_stdio_mcp.ps1`。
