# MCP 端点探针（经 LiteLLM HTTP 代理）
# 用途：完整握手序列 initialize -> notifications/initialized -> tools/list
#       判定某 MCP server 经代理是否真的暴露工具（避免裸 tools/list 的假阳性）
# 用法：pwsh -NoProfile -File probe_mcp_endpoint.ps1 -Name officecli
#       pwsh -NoProfile -File probe_mcp_endpoint.ps1 -Name officecli -Call "--version"

param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Base   = "http://127.0.0.1:4000",
    [string]$Key    = "sk-1234",
    [string]$Call   = ""          # 可选：额外执行一次 tools/call，值为传给工具的 command 参数
)

$ErrorActionPreference = 'Continue'
$u   = "$Base/mcp/$Name"
$hdr = @{
    Authorization  = "Bearer $Key"
    'Content-Type' = 'application/json'
    'Accept'       = 'application/json, text/event-stream'   # 缺此头会 406
}

# SSE 响应剥离 "data: " 前缀
function Get-DataLine($content) {
    ($content -split "`n" | Where-Object { $_ -like 'data:*' }) -join "`n" -replace '^data: ', ''
}

$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession

Write-Host "=== [$Name] 1/3 initialize ==="
$init = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}'
try {
    $r1 = Invoke-WebRequest -Uri $u -Method Post -Headers $hdr -Body $init -WebSession $s -UseBasicParsing -TimeoutSec 30
    Write-Host "HTTP $($r1.StatusCode)"
    Write-Host (Get-DataLine $r1.Content)
} catch {
    Write-Host "FAIL initialize: $($_.Exception.Message)"
    exit 1
}

$sid = $r1.Headers['mcp-session-id']
Write-Host "session-id: [$sid]"

$h2 = @{}
foreach ($k in $hdr.Keys) { $h2[$k] = $hdr[$k] }
if ($sid) { $h2['mcp-session-id'] = $sid }

Write-Host "`n=== [$Name] 2/3 notifications/initialized ==="
try {
    Invoke-WebRequest -Uri $u -Method Post -Headers $h2 -Body '{"jsonrpc":"2.0","method":"notifications/initialized"}' -WebSession $s -UseBasicParsing -TimeoutSec 30 | Out-Null
    Write-Host "sent"
} catch { Write-Host "warn: $($_.Exception.Message)" }

Write-Host "`n=== [$Name] 3/3 tools/list ==="
try {
    $r2  = Invoke-WebRequest -Uri $u -Method Post -Headers $h2 -Body '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' -WebSession $s -UseBasicParsing -TimeoutSec 40
    $txt = Get-DataLine $r2.Content
    Write-Host $txt
    if ($txt -match '"tools":\[\]') {
        Write-Host "`n>>> 判定: tools 为空 -> 工具未加载（服务器问题或代理缺陷，需进一步定位）" -ForegroundColor Yellow
    } elseif ($txt -match '"tools":\[\{') {
        Write-Host "`n>>> 判定: tools 非空 -> 代理链路正常" -ForegroundColor Green
    }
} catch { Write-Host "FAIL tools/list: $($_.Exception.Message)" }

if ($Call -ne "") {
    Write-Host "`n=== [$Name] 附加 tools/call: $Call ==="
    $body = (@{ jsonrpc = '2.0'; id = 9; method = 'tools/call'
                params = @{ name = $Name; arguments = @{ command = $Call } } } |
             ConvertTo-Json -Depth 6 -Compress)
    try {
        $r3 = Invoke-WebRequest -Uri $u -Method Post -Headers $h2 -Body $body -WebSession $s -UseBasicParsing -TimeoutSec 60
        Write-Host (Get-DataLine $r3.Content)
    } catch { Write-Host "FAIL tools/call: $($_.Exception.Message)" }
}
