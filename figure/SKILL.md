---
name: figure
description: 论文图表生成 — 支持数据绘图(paper-figure)、AI插图(paper-illustration)、架构图(figure-spec)、流程图(mermaid-diagram)。触发词：画图、生成图表、generate figures、架构图、workflow 图、mermaid、AI绘图。

tags: [chart,diagram,mermaid,visualization]
category: document
---

# Figure — 论文图表

## 子类型

### 数据图 (paper-figure)
从实验数据生成出版物级折线图/柱状图/热力图。
触发：画图、作图、generate figures、paper figures

### AI 插图 (paper-illustration)
Gemini 生成学术插图，架构/方法示意图，Claude 监督迭代。
触发：AI绘图、paper illustration、generate diagram

### 架构图 (figure-spec)
确定性 SVG 架构图/工作流图/流水线图，JSON → SVG。
触发：架构图、workflow 图、pipeline 图、figure spec

### 流程图 (mermaid-diagram)
Mermaid 语法生成流程图/序列图/类图/甘特图等 18 种。
触发：流程图、sequence diagram、mermaid

## 选择指南
- 数据可视化 → paper-figure
- 方法/架构示意图 → paper-illustration 或 figure-spec
- 纯逻辑流程 → mermaid-diagram
