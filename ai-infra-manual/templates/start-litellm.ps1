#Requires -Version 5.1
<#
.SYNOPSIS
    LiteLLM 网关启动/停止/重启管理脚本（开机自启版）
.DESCRIPTION
    默认后台守护运行，附带健康检查就绪等待、进程树彻底清理。
    加 -Foreground 切换到前台调试模式查看实时日志。
.PARAMETER Foreground
    前台运行（仅调试用），可看到实时日志输出。
.PARAMETER Stop
    停止正在运行的 LiteLLM（PID 文件 + 端口扫描 + 命令行三路兜底）。
.PARAMETER Restart
    停止旧进程后重新启动（默认后台）。
.EXAMPLE
    .\start-litellm.ps1                     # 后台启动 + 健康检查（开机自启用）
    .\start-litellm.ps1 -Foreground         # 前台调试
    .\start-litellm.ps1 -Stop               # 停止服务
    .\start-litellm.ps1 -Restart            # 重启（后台）
    .\start-litellm.ps1 -Restart -Foreground # 重启（前台调试）
#>
param(
    [switch]$Foreground,
    [switch]$Stop,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

# ========== 配置区（按需修改） ==========
$Host_Bind    = "127.0.0.1"
$Port         = 4000
$ConfigFile   = "config.yaml"
$PidFile      = ".litellm.pid"
$LogDir       = "logs"
$HealthURL    = "http://${Host_Bind}:${Port}/health/readiness"
$HealthWait   = 30  # 最大等待就绪秒数
$HealthRetry  = 2   # 每次轮询间隔秒数
# =====================================

# ⚠️ 以下环境变量在 Background→Hidden 模式下不会自动继承
# 必须在此显式设置，不能依赖父进程传递

# 强制 UTF-8 & 禁用价格拉取
$env:PYTHONUTF8              = "1"
$env:LITELLM_DISABLE_PRICE_FETCH = "1"

# SSL 证书修复（Windows Python 必备）
$certPath = "$env:USERPROFILE\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\certifi\cacert.pem"
$env:SSL_CERT_FILE           = $certPath
$env:REQUESTS_CA_BUNDLE      = $certPath

$env:LITELLM_MASTER_KEY      = "sk-1234"

Set-Location $PSScriptRoot

# ---------- 1. 检查 litellm ----------
if (-not (Get-Command litellm -ErrorAction SilentlyContinue)) {
    Write-Error "❌ litellm 未安装，请先运行: pip install 'litellm[proxy]'"
    exit 1
}

# ---------- 2. 健壮加载 .env ----------
# ⚠️ .env 包含所有上游 API Key（DEEPSEEK_KEY / GLM_KEY / QWEN_KEY / VOLC_ARK_KEY 等）
#    必须在此加载，直接 Start-Process litellm.exe 会丢失所有 Key
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env" -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrEmpty($trimmed) -or $trimmed.StartsWith("#")) { continue }
        if ($trimmed.StartsWith("export ")) { $trimmed = $trimmed.Substring(7).Trim() }
        $eqIdx = $trimmed.IndexOf("=")
        if ($eqIdx -le 0) { continue }
        $key = $trimmed.Substring(0, $eqIdx).Trim()
        $val = $trimmed.Substring($eqIdx + 1).Trim().Trim('"', "'")
        if ($val -match '\s+#') { $val = ($val -split '\s+#', 2)[0].Trim().Trim('"', "'") }
        Set-Item -Path "env:$key" -Value $val
    }
    Write-Host "✅ 已加载 .env 环境变量（含所有 API Key）" -ForegroundColor Green
}

# ---------- 3. MCP 配置预检（已知兼容性问题提示）----------
if (-not $Stop) {
    $yamlPath = Join-Path $PSScriptRoot $ConfigFile
    if (Test-Path $yamlPath) {
        $raw = Get-Content $yamlPath -Raw
        if ($raw -match '(?ms)mcp_servers:\s*\n') {
            if ($raw -match '(?ms)command:\s*((?:npx|uvx|node|python|python3)\S*)') {
                Write-Host "ℹ️  检测到 stdio 型 MCP server（command=$($Matches[1])...）" -ForegroundColor DarkYellow
                Write-Host "   启动时 MCP 连接阶段会打印 HTTP/UnsupportedProtocol 错误，此为 litellm" -ForegroundColor DarkYellow
                Write-Host "   尝试用 HTTP transport 连接 stdio server 的误报，不影响服务正常使用。" -ForegroundColor DarkYellow
            }
        }
    }
}

# ---------- 4. 停止功能 ----------
function Stop-LiteLLM {
    Write-Host "🔍 正在停止 LiteLLM..." -ForegroundColor Yellow
    $stopped = $false

    # 4a) 从 PID 文件停止
    if (Test-Path $PidFile) {
        $savedPid = Get-Content $PidFile -Raw.Trim()
        if ($savedPid -match '^\d+$') {
            $proc = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -match 'litellm|python') {
                Write-Host "   → 终止 PID $savedPid ($($proc.ProcessName)) 进程树..." -ForegroundColor Yellow
                taskkill /T /F /PID $savedPid 2>&1 | Out-Null
                $stopped = $true
            }
        }
    }

    # 4b) 按端口查占用进程
    $portOwners = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $portOwners) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "   → 终止端口占用 PID $pid ($($proc.ProcessName)) 进程树..." -ForegroundColor Yellow
            taskkill /T /F /PID $pid 2>&1 | Out-Null
            $stopped = $true
        }
    }

    # 4c) 兜底：命令行匹配残留
    $litellmProcs = Get-WmiObject Win32_Process | Where-Object {
        $_.CommandLine -match "litellm" -and $_.Name -match "python|litellm"
    }
    foreach ($proc in $litellmProcs) {
        Write-Host "   → 终止残留 PID $($proc.ProcessId) ($($proc.Name))..." -ForegroundColor Yellow
        taskkill /T /F /PID $proc.ProcessId 2>&1 | Out-Null
        $stopped = $true
    }

    # 等待端口释放
    $waited = 0
    while ((Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue) -and $waited -lt 10) {
        Start-Sleep -Seconds 1; $waited++
    }

    if ($stopped) {
        Write-Host "✅ LiteLLM 已停止，端口 $Port 已释放" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  未检测到运行中的 LiteLLM 进程" -ForegroundColor DarkYellow
    }
    if (Test-Path $PidFile) { Remove-Item $PidFile -Force }
}

# ---------- 5. 端口清理 ----------
function Clear-Port {
    param([int]$Port)
    $owners = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    if (-not $owners) { return }
    foreach ($pid in $owners) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "⚠️  端口 $Port 被 PID $pid ($($proc.ProcessName)) 占用，正在终止..." -ForegroundColor Yellow
            taskkill /T /F /PID $pid 2>&1 | Out-Null
        }
    }
    $waited = 0
    while ((Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue) -and $waited -lt 10) {
        Start-Sleep -Seconds 1; $waited++
    }
    if ((Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)) {
        Write-Error "❌ 端口 $Port 在 10 秒内未能释放，请手动排查"
        exit 1
    }
}

# ---------- 6. 健康检查 ----------
function Wait-Health {
    param([string]$Url, [int]$TimeoutSeconds, [int]$RetrySeconds)
    Write-Host "⏳ 等待服务就绪中..." -ForegroundColor Yellow
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -eq 200) {
                Write-Host "✅ 服务就绪！http://${Host_Bind}:${Port}" -ForegroundColor Green
                return $true
            }
        } catch {
            # 服务尚未就绪
        }
        Start-Sleep -Seconds $RetrySeconds
        $elapsed += $RetrySeconds
        Write-Host "   ...已等待 ${elapsed}s / ${TimeoutSeconds}s" -ForegroundColor DarkYellow
    }
    Write-Error "❌ 服务在 ${TimeoutSeconds}s 内未就绪，请检查日志"
    return $false
}

# ========== 主流程 ==========

# -- 停止/重启 --
if ($Stop -or $Restart) {
    Stop-LiteLLM
    if ($Stop -and -not $Restart) {
        Write-Host "🏁 已执行停止操作" -ForegroundColor Cyan
        exit 0
    }
}

# -- 启动准备 --
Write-Host "🔍 检查端口 $Port 占用情况..." -ForegroundColor Yellow
Clear-Port -Port $Port

$litellmArgs = @(
    "--config", $ConfigFile,
    "--host", $Host_Bind,
    "--port", $Port,
    "--detailed_debug"
)

# -- 前台调试模式（显式指定 -Foreground）--
if ($Foreground) {
    Write-Host "🚀 启动 LiteLLM 网关（前台调试）http://${Host_Bind}:${Port}" -ForegroundColor Cyan
    Write-Host "   按 Ctrl+C 停止" -ForegroundColor DarkYellow
    litellm @litellmArgs
    exit $LASTEXITCODE
}

# -- 默认：后台守护模式（开机自启）--
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

Write-Host "🚀 启动 LiteLLM 网关（后台守护）http://${Host_Bind}:${Port}" -ForegroundColor Cyan

$proc = Start-Process -NoNewWindow -FilePath (Get-Command litellm).Source `
    -ArgumentList $litellmArgs `
    -WorkingDirectory $PSScriptRoot `
    -RedirectStandardOutput (Join-Path $LogDir "litellm-stdout.log") `
    -RedirectStandardError (Join-Path $LogDir "litellm-stderr.log") `
    -PassThru

$proc.Id | Out-File -FilePath $PidFile -Encoding ASCII -Force
Write-Host "   PID: $($proc.Id)，已保存到 $PidFile" -ForegroundColor DarkYellow

$ready = Wait-Health -Url $HealthURL -TimeoutSeconds $HealthWait -RetrySeconds $HealthRetry
if (-not $ready) { exit 1 }

Write-Host "📋 日志: $(Join-Path $PSScriptRoot $LogDir)\litellm-*.log" -ForegroundColor Cyan
Write-Host "🏁 LiteLLM 后台守护启动完成" -ForegroundColor Cyan
