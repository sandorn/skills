# .NET SDK 自动安装脚本

# 检查 .NET SDK
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 .NET SDK，正在安装..."
    
    # 尝试 winget 安装
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "使用 winget 安装 .NET SDK 8..."
        winget install Microsoft.DotNet.SDK.8 --accept-package-agreements --accept-source-agreements
    }
    else {
        # 回退到官方安装脚本
        Write-Host "未检测到 winget，请手动安装 .NET SDK"
        Write-Host "下载地址：https://dotnet.microsoft.com/download/dotnet/8.0"
    }
}
else {
    Write-Host ".NET SDK 已安装"
    dotnet --version
}
