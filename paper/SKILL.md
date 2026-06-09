---
name: paper
description: 论文写作全流程 — 从大纲到PDF，涵盖规划、撰写、编译、润色。触发词：写论文、draft paper、论文规划、编译论文、改论文、improve paper、write LaTeX。

tags: [latex,writing,academic,pdf]
category: document
---

# Paper — 论文写作

## 工作流

### 1. 规划 (paper-plan)
生成结构化论文大纲：章节分配、图表占位、核心论点树。
触发：写大纲、paper outline、论文规划

### 2. 撰写 (paper-write)
逐节生成 LaTeX 内容，从大纲驱动分节产出。
触发：写论文、write paper、draft LaTeX、开始写

### 3. 编译 (paper-compile)
编译 LaTeX → PDF，修复报错，验证输出。
触发：编译论文、compile paper、build PDF

### 4. 润色循环 (auto-paper-improvement-loop)
xhigh review → 修复 → 重编译，默认 2 轮。
触发：改论文、improve paper、论文润色循环

## 注意事项
- 先执行 paper-plan，确认大纲后再 paper-write
- 编译失败时优先看 LaTeX 报错而非盲目重试
