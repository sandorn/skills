# 原生 stdio MCP 探针（绕过 LiteLLM 代理）
# 用途：直连被测 MCP 服务器，判定"服务器本身正常"还是"代理有问题"
#       —— 这是问题归属的分水岭
# 用法：pwsh -NoProfile -File probe_stdio_mcp.ps1 -Exe "C:\...\officecli.exe" -ExeArgs "mcp"
#       pwsh -NoProfile -File probe_stdio_mcp.ps1 -Exe "npx" -ExeArgs "-y @modelcontextprotocol/server-memory"

param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ExeArgs = "",
    [int]$TimeoutSec = 60
)

$ErrorActionPreference = 'Continue'

# MCP stdio 协议：请求 = 一行 JSON + 换行
$reqInit = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}'
$reqList = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
$payload = $reqInit + "`n" + $reqList + "`n"

$argList = @()
if ($ExeArgs -ne "") { $argList = $ExeArgs -split '\s+' }

Write-Host "=== 直连: $Exe $ExeArgs ==="
Write-Host "(绕过 LiteLLM，判定服务器本身是否正常)`n"

try {
    $out = $payload | & $Exe @argList 2>&1 | Out-String
} catch {
    Write-Host "FAIL 启动服务器: $($_.Exception.Message)"
    exit 1
}

Write-Host $out

Write-Host "`n=== 判定 ==="
if ($out -match '"serverInfo":\{"name":"([^"]+)","version":"([^"]+)"\}') {
    Write-Host "serverInfo: $($Matches[1]) v$($Matches[2])" -ForegroundColor Cyan
    Write-Host "  -> 与本地二进制版本对比：不一致 = 代理拉起的不是你以为的那个进程" -ForegroundColor Cyan
}
if ($out -match '"tools":\[\{') {
    Write-Host "tools 非空 -> 服务器正常；若代理侧为空，则问题在 LiteLLM 代理" -ForegroundColor Green
} elseif ($out -match '"tools":\[\]') {
    Write-Host "tools 为空 -> 服务器自身问题，检查依赖/路径" -ForegroundColor Yellow
} else {
    Write-Host "未解析到 tools 字段，检查上面的原始输出" -ForegroundColor Yellow
}

Write-Host "`n提示：若首次运行 npx 需下载包，请加大 -TimeoutSec。"
