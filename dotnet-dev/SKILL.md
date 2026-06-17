---
name: dotnet-dev
description: 用户完全不需要懂编程，全程由 AI 充当"需求分析师 + 开发工程师 + 环境管理员 + 测试工程师 + 打包交付人员"。内置 WPF + HandyControl + CommunityToolkit.Mvvm 完整模板，支持 CLI 批处理、WPF 桌面应用、Excel 批量处理、网页数据抓取四套蓝图。自动安装 .NET SDK、NuGet 包管理、编译测试、打包交付。触发词：.NET 开发、WPF 应用、桌面软件、C# 开发、dotnet、WPF 界面、桌面工具、exe 打包、.NET 项目、C# 项目、WPF 窗口、桌面小工具

tags: [dotnet,wpf,csharp,desktop]
category: development
---

# .NET WPF 桌面应用

## 核心理念

**用户不需要懂编程**，全程由 AI 代劳。你只需要告诉 AI 你想做什么，剩下的全部自动完成。

## 铁律

- **全程只读项目文件**，除非用户明确要求修改。
- **编译失败必须修复**，不能跳过错误交付。
- **打包前必须测试**，用样例数据跑一遍验证输出。
- **交付物必须是可执行的 exe**，附带使用说明。

## 执行流程

### Step 1: 需求澄清

用户提出需求后，AI 先问清楚以下问题：

1. **功能需求**：具体要做什么？输入是什么？输出是什么？
2. **数据格式**：Excel 格式是什么样的？按什么分类？
3. **输出要求**：要不要导出 PDF？要不要生成图表？
4. **使用场景**：自己用还是给团队用？单人还是多人？
5. **界面要求**：要不要窗口界面？要不要进度条？要不要日志显示？
6. **交付要求**：要不要打包成单文件 exe？要不要自包含运行时？

### Step 2: 环境检查与安装

AI 自动检查并安装所需环境：

```powershell
# 检查 .NET SDK 是否安装
dotnet --version

# 如果未安装，自动安装
winget install Microsoft.DotNet.SDK.8
# 或回退到官方安装脚本
```

**NuGet 包管理**：
- NuGet 国内直连下载，不需要配置镜像源
- AI 自动执行 `dotnet add package` 安装依赖
- 不会出现版本冲突问题

### Step 3: 项目创建

根据用户选择的项目蓝图创建项目：

#### 蓝图一：CLI 批处理工具

```powershell
dotnet new console -n MyTool -o ./MyTool
cd MyTool
dotnet add package ClosedXML  # Excel 处理
dotnet add package CsvHelper   # CSV 处理
```

适用场景：文件整理、数据处理、接口调用，命令行运行

#### 蓝图二：WPF 桌面应用

```powershell
dotnet new wpf -n MyWpfApp -o ./MyWpfApp
cd MyWpfApp
dotnet add package HandyControl
dotnet add package CommunityToolkit.Mvvm
```

适用场景：窗口、按钮、文件选择器、进度条，适合长期使用

#### 蓝图三：Excel 批量处理

```powershell
dotnet new wpf -n ExcelTool -o ./ExcelTool
cd ExcelTool
dotnet add package ClosedXML
dotnet add package CommunityToolkit.Mvvm
dotnet add package HandyControl
```

适用场景：用 ClosedXML 读写 Excel，不依赖 Office 安装

#### 蓝图四：网页数据抓取

```powershell
dotnet new console -n WebScraper -o ./WebScraper
cd WebScraper
dotnet add package HtmlAgilityPack
dotnet add package AngleSharp
```

适用场景：HttpClient + HtmlAgilityPack，高效稳定

### Step 4: 代码生成

AI 按照 MVVM 架构生成代码：

**项目结构**：
```
MyWpfApp/
├── MyWpfApp.csproj
├── App.xaml
├── App.xaml.cs
├── MainWindow.xaml
├── MainWindow.xaml.cs
├── ViewModels/
│   └── MainViewModel.cs
├── Models/
│   └── DataModel.cs
└── Services/
    └── DataService.cs
```

**MainWindow.xaml**（HandyControl 现代化 UI）：
- 圆角按钮
- 毛玻璃导航栏
- 渐变进度条
- 流畅的窗口缩放
- 高分屏完美适配

**MainViewModel.cs**（CommunityToolkit.Mvvm）：
- 遵循 MVVM 分层架构
- 支持主题切换
- 属性变更通知
- 命令绑定

### Step 5: 编译测试

```powershell
dotnet build  # 编译检查
dotnet run    # 运行测试
```

**编译型语言优势**：
- 语法错误、类型不匹配、空引用风险，全部在编译阶段拦截
- 只要编译通过，代码质量就已经过了一道硬门槛
- 对 AI 编程来说，编译型语言天然比解释型语言更可靠

### Step 6: 打包交付

```powershell
# 发布为自包含单文件 exe
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o ./publish

# 发布为框架依赖 exe（更小，依赖系统 .NET Runtime）
dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o ./publish
```

**打包大小对比**：
- Python + PyInstaller：80-120MB
- .NET 框架依赖：几 MB 到十几 MB
- .NET 自包含：几十 MB（比 Python 小得多）

### Step 7: 交付说明

AI 告诉用户：
- exe 文件在哪
- 如何使用
- 附带使用说明文档

## 四套项目蓝图详细说明

### 蓝图一：CLI 批处理工具

**模板代码**：
```csharp
using System;
using System.IO;
using System.Threading.Tasks;

namespace MyTool
{
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("=== 批处理工具 ===");
            Console.WriteLine("正在处理...");
            
            // 业务逻辑在这里
            
            Console.WriteLine("处理完成！");
        }
    }
}
```

**常用 NuGet 包**：
- `ClosedXML`：Excel 读写
- `CsvHelper`：CSV 处理
- `Newtonsoft.Json`：JSON 处理
- `SixLabors.ImageSharp`：图像处理

### 蓝图二：WPF 桌面应用

**MainWindow.xaml 模板**：
```xml
<Window x:Class="MyWpfApp.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:hc="https://handyorg.github.io/handycontrol"
        Title="我的工具" Height="450" Width="800">
    <hc:SimpleWindow Title="我的工具" Height="450" Width="800"
                     WindowStartupLocation="CenterScreen">
        <Grid Margin="20">
            <StackPanel>
                <TextBlock Text="欢迎使用" FontSize="24" Margin="0,0,0,20"/>
                <Button Content="选择文件" Command="{Binding SelectFileCommand}"
                        Margin="0,0,0,10" Padding="20,10"/>
                <Button Content="开始处理" Command="{Binding StartProcessCommand}"
                        Margin="0,0,0,10" Padding="20,10"/>
                <ProgressBar Value="{Binding Progress}" 
                             Minimum="0" Maximum="100" Height="20" Margin="0,10"/>
                <TextBox Text="{Binding LogText}" Height="150" 
                         TextWrapping="Wrap" AcceptsReturn="True"
                         VerticalScrollBarVisibility="Auto" Margin="0,10"/>
            </StackPanel>
        </Grid>
    </hc:SimpleWindow>
</Window>
```

**MainViewModel.cs 模板**：

> 完整代码详见 `references/code-templates.md`

### 蓝图三：Excel 批量处理

**Excel 处理服务模板**：

> 完整代码详见 `references/code-templates.md`

### 蓝图四：网页数据抓取

**网页抓取服务模板**：

> 完整代码详见 `references/code-templates.md`

## .NET SDK 自动安装

所有环境操作由 AI 代执行：

```powershell
# 检查 .NET SDK
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 .NET SDK，正在安装..."
    
    # 尝试 winget 安装
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install Microsoft.DotNet.SDK.8
    }
    else {
        # 回退到官方安装脚本
        Write-Host "请手动安装 .NET SDK: https://dotnet.microsoft.com/download"
    }
}

dotnet --version
```

## 技术选型参考

| 场景 | 推荐方案 | 核心理由 |
|------|---------|---------|
| Excel 内部数据处理、报表 | VBA | 原生嵌入，随文件走 |
| 需要 Ribbon 的专业 Excel 插件 | VBA + xlam | Office 生态最自然 |
| 快速脚本、数据抓取、原型验证 | Python | 生态丰富，上手极快 |
| 通用桌面小工具 | Python GUI | 够用，比 VBA 窗体强 |
| 需要专业级界面的桌面软件 | .NET WPF | 原生控件，漂亮稳定 |
| 要发给客户/团队的正式工具 | .NET WPF | 编译型更可靠，打包小 |
| 高性能数据处理、大规模 Excel | .NET | 静态编译，性能碾压 |
| 跨平台需求 | Python | .NET 目前聚焦 Windows |

## .NET 的编译型优势

1. **编译器拦截错误**：语法/类型/空引用在编译阶段拦截
2. **强类型防错**：参数/返回值类型错误编译不过
3. **项目结构清晰**：`.csproj` 定义依赖，Views/ViewModels/Services 分层明确
4. **NuGet 依赖整洁**：`dotnet add package` 避免版本冲突

