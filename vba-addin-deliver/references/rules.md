# VBA 插件开发约束规则

## 速查表

| 决策项 | 选 xlam | 选 xlsm |
|--------|---------|---------|
| 使用范围 | 通用工具，与工作簿无关 | 宏与特定数据模板绑定 |
| 分发对象 | 多人使用，隐藏代码 | 自己用或附带数据分发 |
| 入口方式 | Ribbon 功能区（3+ 操作） | Ribbon 或工作表按钮（1-3 操作） |
| 加载方式 | Excel 启动自动加载 | 打开文件时加载 |
| 最低版本 | Excel 2016+（2006/01 customui 命名空间） | 同左；<2016 改用 2009 命名空间 |

## 文件格式选择

### 什么时候用 xlam（加载项）
- 功能与具体工作簿无关，是通用工具
- 需要分发给多个用户使用
- 希望隐藏 VBA 代码，不让用户看到
- 不希望在用户的工作簿里留下宏代码
- 需要随 Excel 启动自动加载

### 什么时候用 xlsm（宏工作簿）
- 宏与特定数据模板绑定
- 用户需要在这个文件里填写数据
- 临时性任务，不需要长期加载
- 简单功能，不超过 3-5 个宏

## Ribbon 与入口选择

### 什么时候用 Ribbon 功能区
- 功能较多（3 个以上操作）
- 需要分类组织（如"数据处理"、"格式美化"）
- 分发给非技术用户，需要直观入口
- 定制 Tab 名称以区分系统功能区

### 什么时候用工作表形状按钮
- 功能简单（1-3 个操作）
- 只在特定工作表有效
- 快速原型验证阶段
- 用 Shapes.AddFormControl 或 ActiveX 按钮

## 编码规范

### 中文文件编码
- 所有 .bas、.cls、.frm 文件保存为 **UTF-8 with BOM**
- 所有 .ps1 脚本保存为 **UTF-8 with BOM**（PowerShell 5.x 兼容）
- Ribbon XML 文件保存为 **UTF-8**
- VBA 代码内的中文字符串确保显示正常

### VBA 代码规范
- 使用 Option Explicit
- 错误处理：On Error GoTo + 统一错误日志
- 避免使用 ActiveWorkbook/ActiveSheet，用显式引用
- 函数名前缀避免与内置函数冲突
- 注释用中文，变量名用英文

### VBA 性能反模式

| 反模式 | 问题 | 正确写法 |
|--------|------|----------|
| `Range.Select` / `Range.Activate` | 每次 Select 触发屏幕重绘，拖慢 5-50x | 直接操作 Range 对象：`Range("A1").Value = 123` |
| 循环内 `Application.ScreenUpdating = True` | 每次更新触发重绘 | 循环前设 `False`，循环后恢复 |
| 循环内逐单元格读写 | Range 对象每次访问有 COM 开销 | 用 Variant 数组批量读写：`arr = Range.Value`，处理后再写回 |
| `Application.WorksheetFunction` 在循环内 | 每次调用跨进程开销大 | 尽量用 VBA 原生函数替代，或先读完数据再处理 |
| 不关闭不再使用的对象 | COM 对象泄漏导致内存压力 | 所有 Workbook/Worksheet/Range 用完设 `Nothing` |
| `On Error Resume Next` 吞所有错误 | 掩盖真实 bug | 精确 `On Error GoTo ErrHandler`，在 ErrHandler 中 Log + 恢复 |

## VBA 代码嵌入方法

`build.ps1` 生成的是 OOXML 骨架（不含 vbaProject.bin）。VBA 代码需额外嵌入，两种方式：

### 方式一：Excel COM 自动化（推荐）
```powershell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open("output.xlam")
$vbe = $wb.VBProject
$module = $vbe.VBComponents.Add(1)  # 1 = vbext_ct_StdModule
$module.CodeModule.AddFromFile("Module1.bas")
$wb.Save()
$excel.Quit()
```
**前提**：Excel → 选项 → 信任中心 → 勾选"信任对 VBA 工程对象模型的访问"。

### 方式二：手动导入
1. 用 `build.ps1` 生成 xlam/xlsm 骨架
2. 在 Excel 中打开，Alt+F11 进入 VBE
3. 文件 → 导入文件 → 选择 .bas/.cls/.frm
4. 保存

## Ribbon XML 规则

### 必须注意
- xmlns 命名空间必须正确：http://schemas.microsoft.com/office/2006/01/customui
- 自定义图标必须 base64 编码或放在 customUI/images/ 下
- 关系文件（.rels）必须正确引用 customUI 路径
- [Content_Types].xml 必须注册 .xml 和 .png 类型

## Office 版本兼容

### 32 位 vs 64 位
- 涉及 Windows API 声明时用 PtrSafe 关键字
- LongPtr 替代 Long 用于指针类型
- 用 #If VBA7 条件编译处理版本差异
- 注意：64 位 Windows 上可安装 32 位 Office（常见于企业环境）。`Application.Version` 只返回 Office 版本号，不返回位数。用 `#If Win64` 判断宿主 Windows 位数，用 `#If VBA7` 判断 VBA 版本

### 非标准安装环境
- **Microsoft Store 版 Excel**：注册表路径在 `HKCU\Software\Microsoft\Office\16.0\Excel` 可能不存在或结构不同。install.bat 生成的注册表键可能无效。检测方法：检查 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe` 的实际路径
- **Click-to-Run / 即点即用版**：Office 安装路径在 `C:\Program Files\Microsoft Office\root\Office16\` 而非传统路径。Excel COM 创建通常不受影响，但手动路径操作需注意
- **多版本 Office 共存**：优先使用 `$ExcelVersion` 对应的版本，用户需在 build.ps1 参数中明确指定

### Excel 版本
- 2016+ 为最低支持版本（低于 2016 的版本不支持当前 Ribbon XML 命名空间）
- 如用户要求支持 2013 或更早版本，需改用 2009 命名空间并降级 Ribbon 功能
- 避免使用 2019/365 独占函数
- 用 Application.Version 检测版本并降级功能

## 安装卸载

### 安装脚本要点
- 写入 HKCU\Software\Microsoft\Office\\<version\>\\Excel\AddIns（HKCU = 用户级，不需管理员权限，但对每个用户需分别安装）
- 子键名为插件名称，值可为默认 REG_SZ（路径）或 Manifest + LoadBehavior 组合
- LoadBehavior 值：3 = 启动时加载，2 = 不加载（用户手动启用），1 = 加载但隐藏，0 = 禁用

### 卸载脚本要点
- 删除注册表键
- 可选删除文件（询问用户）
- 先关闭 Excel 进程再操作（避免文件锁定）

## 踩坑经验

1. **ZIP 打包**：xlam/xlsm 本质是 ZIP，PowerShell Compress-Archive 需注意路径层级
2. **图标格式**：Ribbon 图标推荐 32x32 PNG（大图标），16x16 PNG（小图标）；工作表按钮用 16x16
3. **Ribbon 不显示**：常见原因——关系文件路径错误、XML 命名空间不对、文件未在 \_rels 下
4. **COM 权限**：PowerShell 操作 Excel COM 需要 Excel 已安装且未处于编辑模式
5. **杀毒软件**：含 VBA 的 xlam 可能被误报，建议数字签名或提供源码让用户自行构建
6. **路径空格**：所有文件路径用双引号包裹，避免 Program Files 等路径出错
7. **VBA 密码保护**：若 VBA 工程设置了密码，ZIP 内的 vbaProject.bin 会被加密，直接解压修改将损坏文件。开发阶段不要设密码，交付前再加密
8. **VBA 引用丢失**：若代码引用了外部库（如 Scripting.Dictionary、MSXML），需在 VBE → 工具 → 引用中勾选。分发到其他机器时，对应 DLL 版本不同会导致"无法找到项目或库"错误。**解法**：尽量用 CreateObject 后期绑定替代早期引用
9. **Workbook_Open 副作用**：xlam 的 Workbook_Open 在 Excel 启动时自动执行。若其中包含耗时操作（如网络请求），会拖慢 Excel 启动。**建议**：启动事件只做轻量初始化，重操作延迟到用户首次点击按钮
10. **CustomUI 命名空间版本陷阱**：Office 2007 用 `customui`，2010+ 用 `customui14`，2013+ 用 `customui15`。本脚本默认 2006/01 命名空间兼容 2010+，但 2007 用户会遇到 Ribbon 不显示

## 排错指南

| 症状 | 可能原因 | 检查方法 |
|------|----------|----------|
| 打开文件后 Ribbon 不显示 | .rels 未指向 customUI/customUI.xml 或命名空间版本不对 | 解压检查 `_rels/.rels` 第 2 个 Relationship |
| Ribbon 显示了但按钮点击无反应 | VBA 回调函数名与 onAction 不匹配，或 VBA 工程未嵌入 | 检查 customUI.xml 中 onAction 值与 .bas 中 Public Sub 名称一致 |
| Excel 启动变慢 | Workbook_Open 中有耗时操作 | 注释掉 Open 事件中的代码，逐个排查 |
| "无法找到项目或库" | 引用丢失——外部 DLL 版本不匹配 | VBE → 工具 → 引用，查看是否有"丢失"标记；改用 CreateObject |
| install.bat 运行后 Excel 中看不到加载项 | LoadBehavior 值错误或注册表路径 Office 版本号不对 | regedit 检查 HKCU\...\AddIns 下键值；确认 ExcelVersion 参数与实际一致 |
| COM 自动化报"无法访问 VBA 工程" | 未勾选信任中心 → 信任对 VBA 工程对象模型的访问 | Excel → 选项 → 信任中心 → 宏设置 |
| 文件杀软误报 | xlam/xlsm 含 VBA 宏代码 | 提供源码 + build.ps1 让用户自行构建；或提交企业数字签名 |

---

> 📎 关联文件：[SKILL.md](../SKILL.md) · [build.ps1](../templates/build.ps1) · [checklist](delivery-checklist.md) · [patterns](vba-patterns.md)
