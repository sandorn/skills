# 启动流程参考

## SSL 证书修复（Windows Python 必备）

Windows Python OpenSSL 默认找不到 CA 证书链，LiteLLM 启动时在 `get_model_cost_map.py` 报 `[SSL: CERTIFICATE_VERIFY_FAILED]`。

### 方案 A：环境变量（推荐，与 python-certifi-win32 互补）
在 `start.ps1` 添加：
```powershell
$env:SSL_CERT_FILE      = "$env:USERPROFILE\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\certifi\cacert.pem"
$env:REQUESTS_CA_BUNDLE = "$env:SSL_CERT_FILE"
```

### 方案 B：python-certifi-win32
```powershell
python -m pip install python-certifi-win32
```

**组合使用效果最稳定**。如果在 Hermes TUI 中手动重启 LiteLLM（不经 start.ps1），必须同时设置这两个环境变量。

## start.ps1 模板

完整启动管理脚本见 `templates/start-litellm.ps1`，支持四种模式：

| 场景 | 命令 | 说明 |
|------|------|------|
| 开机自启（默认） | `.\start.ps1` | 后台守护 + PID 追踪 + 健康检查 + SSL 修复 |
| 前台调试 | `.\start.ps1 -Foreground` | 实时日志 |
| 停止服务 | `.\start.ps1 -Stop` | 三路兜底（PID→端口→命令行） |
| 重启 | `.\start.ps1 -Restart` | 停旧启新 + 健康检查 |

**部署至开机自启**（VBS + Startup 文件夹）：
```vbscript
' LiteLLM autostart — silent, 30s delay
WScript.Sleep 30000
Set ws = CreateObject("WScript.Shell")
ws.Run "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""C:\Users\Administrator\.litellm\start.ps1""", 0, False
```

## 各客户端 Key 配置速查

所有客户端 Authorization 必须用 `Bearer sk-1234` 格式。

| 客户端 | 配置文件 | Key 字段 |
|--------|----------|---------|
| Continue | `~/.continue/config.yaml` | `apiKey:` + `headers.Authorization` |
| VS Code MCP | `AppData/Roaming/Code/User/mcp.json` | `headers.Authorization` |
| VS Code LiteLLM 扩展 | VS Code 设置 | `litellm.apiKey` |
| Claude Desktop | `~/.claude.json` → mcpServers | `headers.x-litellm-api-key` |
| CodeBuddy | `~/.codebuddy/mcp.json` | `headers.Authorization` |

## Key 迁移

更换 LiteLLM master_key 时，**所有 5 个配置文件**都可能残留旧 Key：

| 配置文件 | 典型旧值 |
|---------|---------|
| `~/.hermes/config.yaml` | `sk-local-litellm-gateway` |
| `~/.continue/config.yaml` | 同上 |
| `~/.codebuddy/mcp.json` | **最容易遗漏** |
| `AppData/Roaming/Code/User/mcp.json` | 通常正确 |
| `~/.claude.json` | `x-litellm-api-key` 格式 |

**检查方法（读原始字节，不看终端显示）：**
```python
with open(path, 'rb') as f:
    raw = f.read()
idx = raw.find(b'Bearer ')
chunk = raw[idx:idx+40]
print(repr(chunk))
```
