# VBA 插件开发约束规则

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

### Excel 版本
- 2016+ 为最低支持版本
- 避免使用 2019/365 独占函数
- 用 Application.Version 检测版本并降级功能

## 安装卸载

### 安装脚本要点
- 写入 HKCU\Software\Microsoft\Office\<version>\Excel\AddIns
- REG_SZ 类型，值可以是路径或 LoadBehavior + Manifest 组合
- LoadBehavior 值：3 = 加载，2 = 不加载，0 = 禁用

### 卸载脚本要点
- 删除注册表键
- 可选删除文件（询问用户）
- 关闭 Excel 进程后再操作

## 踩坑经验

1. **ZIP 打包**：xlam/xlsm 本质是 ZIP，PowerShell Compress-Archive 需注意路径层级
2. **图标格式**：Ribbon 图标推荐 32x32 PNG，大图标 64x64；工作表按钮用 16x16
3. **Ribbon 不显示**：常见原因——关系文件路径错误、XML 命名空间不对、文件未在 \_rels 下
4. **COM 权限**：PowerShell 操作 Excel COM 需要 Excel 已安装且未处于编辑模式
5. **杀毒软件**：含 VBA 的 xlam 可能被误报，建议数字签名或提供源码让用户自行构建
6. **路径空格**：所有文件路径用双引号包裹，避免 Program Files 等路径出错
