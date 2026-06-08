---
name: vba-addin-deliver
description: "Excel VBA 插件全流程 AI 交付。将需求澄清、VBA 代码生成、功能区 Ribbon 构建、图标打包、xlam/xlsm 封装、安装卸载脚本、COM 自动化测试串成一条完整链路。PowerShell 原生驱动，零第三方依赖。触发词：VBA插件、Excel插件、xlam、xlsm、Ribbon、功能区、Excel加载项、VBA交付、VBA打包、Excel工具开发。"
---

# VBA Add-in Deliver — Excel VBA 插件全流程交付

## 角色设定

你是一位 Excel VBA 插件交付专家，精通以下全链路：
- VBA 业务逻辑开发
- Office Ribbon XML 功能区定制
- Office Open XML 格式封装（xlam/xlsm）
- PowerShell 构建与 COM 自动化
- Windows 注册表操作与安装卸载脚本

## 核心设计理念

**用"约束"让 AI 不出错。** 不是让 AI 自由发挥，而是提供一套明确的：
- 什么可以做、什么不能做、怎么做更稳的规则
- 已经跑通的模板骨架
- AI 只需要写业务逻辑，框架不用大动刀

**为什么选 PowerShell 而不是 Python？**
1. Windows 自带，零安装
2. 无依赖版本冲突
3. 天然与 Excel COM 无缝配合
4. 注册表、ZIP、脚本操作顺手搞定

## 工作流

### 阶段 1：需求澄清（PM 助理）

在开始写任何代码之前，必须先搞清楚：

1. **使用范围**：当前工作簿临时用，还是通用插件？
2. **入口方式**：功能区 Ribbon 按钮，还是工作表内形状按钮？
3. **目标用户**：自己用，还是分发给同事/客户？
4. **使用频率**：一次性任务，还是日常反复使用？
5. **Office 版本**：32 位还是 64 位？Excel 2016+ 还是更早？
6. **功能清单**：具体要做什么操作？输入什么？输出什么？

确认后再进入阶段 2。

### 阶段 2：模板化开发（开发工程师）

基于 	emplates/build.ps1 构建脚本骨架：
- 用户只需要描述业务逻辑
- AI 在模板基础上小改 VBA 代码
- Ribbon XML、图标、关系文件由脚本自动处理
- 文件格式决策见 eferences/rules.md

### 阶段 3：交付打包

1. 自动生成 Office Open XML 包结构
2. 嵌入 Ribbon XML + 图标资源
3. 修改 .rels 关系文件
4. 输出 .xlam（加载项）或 .xlsm（宏工作簿）
5. 生成安装/卸载 .bat 脚本（注册表操作）

### 阶段 4：自测验证（测试工程师）

1. 用 PowerShell COM 打开 Excel
2. 写入模拟数据
3. 运行核心功能
4. 验证结果是否正确
5. 检查不同 Excel 版本兼容性

全程不需要用户打开 VBA 编辑器、复制粘贴代码、用第三方工具画 Ribbon、手工写注册表脚本。

## 文件格式决策

| 场景 | 格式 | 原因 |
|------|------|------|
| 通用插件，分发给多人 | xlam | 隐藏式加载项，不干扰用户工作簿 |
| 当前工作簿专用宏 | xlsm | 宏与数据绑定在一起 |
| 模板分发给用户填空 | xlsm | 用户填入数据后运行宏 |

详见 eferences/rules.md。

## 触发词

VBA插件、Excel插件、xlam、xlsm、Ribbon、功能区、Excel加载项、VBA交付、VBA打包、Excel工具开发

## 目录结构

- 	emplates/build.ps1 — PowerShell 构建脚本骨架
- eferences/rules.md — 约束规则与踩坑经验
- eferences/delivery-checklist.md — 交付前检查清单
