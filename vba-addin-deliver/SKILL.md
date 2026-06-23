---
name: vba-addin-deliver
version: 2.0.0
description: Excel VBA 插件全流程：代码/Ribbon/打包/测试。

tags: [vba, excel, ribbon, addin, xlam]
category: development
linked_files:
  templates:
    - templates/build.ps1
  references:
    - references/rules.md
    - references/delivery-checklist.md
    - references/vba-patterns.md
---

# VBA Add-in Deliver

## 角色

Excel VBA 插件交付专家。全程不需要用户打开 VBA 编辑器、手工写 Ribbon XML、操作注册表。

**核心理念**：用约束让 AI 不出错——提供已验证的规则 + 跑通的模板骨架，AI 只写业务逻辑，不动框架。

**技术选型**：PowerShell（Windows 自带，零依赖，COM 天然配合），不引入 Python 依赖链。

---

## 触发词

| 触发词 | 场景 |
|--------|------|
| VBA插件、Excel插件、xlam、Excel加载项 | 通用加载项开发 |
| xlsm、VBA交付、VBA打包 | 宏工作簿交付 |
| Ribbon、功能区 | 功能区 UI 定制 |
| Excel工具开发 | 完整工具开发 |

---

## 工作流

### 阶段 1：需求澄清

1. **使用范围**：临时用还是通用插件？
2. **入口方式**：Ribbon 按钮还是工作表形状按钮？
3. **目标用户**：自己用还是分发？
4. **Office 版本**：32/64 位？Excel 2016+？
5. **功能清单**：输入什么？输出什么？

**产出**：确认文种（xlam/xlsm）+ Ribbon 布局清单 + 功能点列表。格式决策见 [`rules.md`](references/rules.md) 速查表。

### 阶段 2：模板化开发

1. 运行 `build.ps1 -ProjectName "XXX" -OutputFormat "xlam"` 生成 OOXML 骨架
2. 编写 VBA 业务模块（.bas），按 [`rules.md`](references/rules.md) 编码规范
3. 通过 COM 自动化或 VBE 手动导入 VBA 代码到骨架

**产出**：含 VBA 代码的 `.xlam` / `.xlsm`，Ribbon 按钮已绑定到 VBA 过程。

### 阶段 3：交付打包

1. 运行 `build.ps1` 重新打包（确保 VBA 嵌入后结构完整）
2. 自动生成 `install.bat` + `uninstall.bat`
3. 编写 `README.txt`（安装步骤 + 使用说明 + 版本号）

**产出**：dist/ 目录含 `.xlam`/`.xlsm` + `install.bat` + `uninstall.bat` + `README.txt`。

### 阶段 4：自测验证

1. `install.bat` 安装到当前用户注册表
2. 启动 Excel，验证 Ribbon 出现且按钮可点击
3. 用模拟数据跑核心功能，检查输出正确
4. 测试错误路径（空输入、异常数据）有提示
5. `uninstall.bat` 卸载，确认注册表清除

**产出**：全部 🔴 项通过的 [`delivery-checklist.md`](references/delivery-checklist.md)。

---

## 子文件

| 文件 | 内容 | 何时用 |
|------|------|--------|
| `templates/build.ps1` | OOXML 构建脚本骨架 | 项目创建 / 打包 |
| `references/rules.md` | 约束规则 + 踩坑经验 | 开发全程查阅 |
| `references/delivery-checklist.md` | 交付前检查清单 | 定稿前核验 |
| `references/vba-patterns.md` | VBA 可复用代码模板 | 写 VBA 时复制粘贴 |

---

> 📎 关联文件：[build.ps1](templates/build.ps1) · [rules.md](references/rules.md) · [checklist](references/delivery-checklist.md) · [patterns](references/vba-patterns.md)

### 速查卡

| 想做什么 | 去哪 |
|----------|------|
| 创建新插件项目 | `build.ps1 -ProjectName "XXX" -OutputFormat "xlam"` |
| 选 xlam 还是 xlsm | [rules.md 速查表](references/rules.md) |
| 写 VBA 代码 | [vba-patterns.md](references/vba-patterns.md) 复制模板 |
| 嵌入 VBA 到骨架 | [rules.md VBA 嵌入方法](references/rules.md) |
| Ribbon 不显示 | [rules.md 排错指南](references/rules.md) |
| 交付前检查 | [delivery-checklist.md](references/delivery-checklist.md) 逐项 🔴→🟡→○ |
