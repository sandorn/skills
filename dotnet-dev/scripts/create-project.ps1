# .NET 项目创建脚本

param(
    [string]$ProjectName,
    [string]$ProjectType = "WpfApp",  # WpfApp, ConsoleApp, ExcelTool, WebScraper
    [string]$OutputPath
)

$basePath = if ($OutputPath) { $OutputPath } else { ".\$ProjectName" }

Write-Host "创建 .NET 项目：$ProjectName"
Write-Host "项目类型：$ProjectType"
Write-Host "输出路径：$basePath"

# 创建项目
dotnet new $ProjectType -n $ProjectName -o $basePath

# 进入项目目录
Set-Location $basePath

# 根据项目类型安装 NuGet 包
switch ($ProjectType) {
    "wpf" {
        dotnet add package HandyControl
        dotnet add package CommunityToolkit.Mvvm
        Write-Host "已安装 HandyControl 和 CommunityToolkit.Mvvm"
    }
    "console" {
        if ($ProjectType -eq "ExcelTool") {
            dotnet add package ClosedXML
        }
        elseif ($ProjectType -eq "WebScraper") {
            dotnet add package HtmlAgilityPack
            dotnet add package AngleSharp
        }
        else {
            dotnet add package ClosedXML
            dotnet add package CsvHelper
            dotnet add package Newtonsoft.Json
        }
        Write-Host "已安装所需 NuGet 包"
    }
}

Write-Host "项目创建完成！"
Write-Host "进入目录：$basePath"
Write-Host "运行：cd $basePath && dotnet build"
