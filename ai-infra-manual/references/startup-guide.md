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

### 部署至开机自启（VBS + Startup 文件夹）

**脚本位置：** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\LiteLLM_Gateway.vbs`

**VBS 模板（加固版，含自启审计日志 + 子进程生命周期解耦）：**
```vbscript
' LiteLLM Gateway autostart - silent, delayed
Option Explicit
Dim ws, fso, logDir, logFile, ts
Set ws  = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

logDir  = "C:\Users\Administrator\.litellm\logs"
logFile = logDir & "\autostart.log"
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)

' 记录触发时刻
On Error Resume Next
Set ts = fso.OpenTextFile(logFile, 8, True)
ts.WriteLine Now & "  [VBS] triggered by Startup"
ts.Close
On Error Goto 0

WScript.Sleep 30000

' cmd /c start 解耦子进程生命周期：wscript 退出后 powershell 继续运行
ws.Run "cmd /c start """" /min powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File ""C:\Users\Administrator\.litellm\start.ps1""", 0, False

' 再记一次成功派发
On Error Resume Next
Set ts = fso.OpenTextFile(logFile, 8, True)
ts.WriteLine Now & "  [VBS] dispatched start.ps1"
ts.Close
```

**关键改动对比旧版：**
1. 增加 `autostart.log` 写入：每次开机在 `logs\` 下留痕，排查是否被 Startup 触发
2. 改用 `cmd /c start """" /min powershell.exe ...`：wscript.exe 退出后子进程不会跟着终结
3. start.ps1 内 `chcp` / `[Console]::OutputEncoding` 等调用已加 try/catch 兜底，避免无控制台场景中止

### 桌面手动重启文件

**位置：** `C:\Users\Administrator\Desktop\重启LiteLLM网关.vbs`

**用途：** 双击即可重启 LiteLLM 网关（无窗口、气泡提示结果）

**行为：**
1. 记录 `[MANUAL] restart requested` 到 `logs\manual.log`
2. 隐藏窗口调用 `start.ps1 -Restart`（停旧启新 + 健康检查）
3. 等待完成后记录退出码到 `logs\manual.log`
4. 弹出 5 秒自动消失的气泡通知结果

**AI 等效重启命令：**
```powershell
Start-Process wscript.exe -ArgumentList '"C:\Users\Administrator\Desktop\重启LiteLLM网关.vbs"'
```
或直接：
```powershell
Start-Process -WindowStyle Hidden powershell.exe -ArgumentList '-ExecutionPolicy Bypass -File "C:\Users\Administrator\.litellm\start.ps1" -Restart'
```

### 开机自启故障排查

1. 开机 1 分钟后检查 `logs\autostart.log` 是否有新时间戳
2. 若无日志 → VBS 未被 Startup 触发（Defender / SmartScreen / 快速启动干扰）
3. 有日志但无 4000 端口 → 检查 `logs\litellm-stderr.log` 是否有启动错误
4. 后备：手动执行 `Start-Process -WindowStyle Hidden powershell.exe -ArgumentList '-ExecutionPolicy Bypass -File "C:\Users\Administrator\.litellm\start.ps1"'`

### 注意事项

- **VBS 文件必须以 GBK 编码保存**（Windows Script Host 按系统 ANSI 解析）。`write_file` 默认 UTF-8 会导致 VBS 中文注释乱码。正确做法：`write_file` 写 UTF-8 到中间路径 → Python 转 GBK 写到目标路径。
- **start.ps1 无控制台场景**：VBS → Hidden PowerShell 时，`[Console]::OutputEncoding` / `chcp` 会抛异常，必须用 `try/catch` 包裹（否则 `$ErrorActionPreference="Stop"` 会让脚本提前中止）。

## 各客户端 Key 配置速查

所有客户端 Authorization 必须用 `Bearer sk-1234` 格式。

| 客户端 | 配置文件 | Key 字段 |
|--------|----------|---------|
| Continue | `~/.continue/config.yaml` | `apiKey:` + `headers.Authorization` |
| VS Code MCP | `AppData/Roaming/Code/User/mcp.json` | `headers.Authorization` |
| VS Code LiteLLM 扩展 | VS Code 设置 | `litellm.apiKey` |
| Claude Desktop | `~/.claude.json` → mcpServers | `headers.x-api-key` |
| CodeBuddy | `~/.codebuddy/mcp.json` | `headers.Authorization` |

## Key 迁移

更换 LiteLLM master_key 时，**所有 5 个配置文件**都可能残留旧 Key：

| 配置文件 | 典型旧值 |
|---------|---------|
| `~/.hermes/config.yaml` | `sk-local-gateway` |
| `~/.continue/config.yaml` | 同上 |
| `~/.codebuddy/mcp.json` | **最容易遗漏** |
| `AppData/Roaming/Code/User/mcp.json` | 通常正确 |
| `~/.claude.json` | `x-api-key` 格式 |

**检查方法（读原始字节，不看终端显示）：**
```python
with open(path, 'rb') as f:
    raw = f.read()
idx = raw.find(b'Bearer ')
chunk = raw[idx:idx+40]
print(repr(chunk))
```