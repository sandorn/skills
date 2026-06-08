---
name: present
description: 学术演讲与海报 — 涵盖 Beamer 幻灯片(paper-slides)、会议海报(paper-poster)、全流程 talk(paper-talk)、逐页打磨(slides-polish)。触发词：做PPT、做海报、make slides、conference talk、poster。
---

# Present — 演讲与海报

## 子类型

### 幻灯片 (paper-slides)
论文 → Beamer LaTeX → PDF + 可编辑 PPTX + 演讲稿。
触发：做PPT、做幻灯片、make slides、conference talk

### 海报 (paper-poster)
论文 → tcbposter LaTeX → A0/A1 PDF + PPTX + SVG。
触发：做海报、conference poster、生成poster

### 全流程 Talk (paper-talk)
端到端：论文 → 大纲 → Beamer+PPTX → 逐页打磨 → 质量检查 → 导出。
触发：做 talk、做 PPT 全流程、talk pipeline

### 打磨 (slides-polish)
逐页 Codex review + python-pptx/Beamer 修复排版/字体/溢出。
触发：polish slides、PPTX 字体太小、和 Beamer 比一下

## 选择指南
- 已有论文只需幻灯片 → paper-slides
- 只需海报 → paper-poster
- 从头到尾 → paper-talk
- 已有初稿需打磨 → slides-polish
