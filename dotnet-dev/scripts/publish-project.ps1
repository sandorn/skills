# .NET 项目发布脚本

param(
    [string]$ProjectPath,
    [string]$OutputDir = "./publish",
    [switch]$SelfContained = $true,
    [switch]$SingleFile = $true
)

$publishArgs = @("-c", "Release", "-r", "win-x64")

if ($SelfContained) {
    $publishArgs += "--self-contained", "true"
}
else {
    $publishArgs += "--self-contained", "false"
}

if ($SingleFile) {
    $publishArgs += "-p:PublishSingleFile=true"
    if ($SelfContained) {
        $publishArgs += "-p:IncludeNativeLibrariesForSelfExtract=true"
    }
}

$publishArgs += "-o", $OutputDir

Write-Host "发布 .NET 项目..."
Write-Host "参数：$publishArgs"

dotnet publish $publishArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "发布成功！"
    Write-Host "输出目录：$OutputDir"
    Get-ChildItem $OutputDir | ForEach-Object {
        Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1MB, 2)) MB)"
    }
}
else {
    Write-Host "发布失败！"
}
