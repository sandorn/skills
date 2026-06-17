---
name: pptx
description: "创建、读取、编辑和合并 PowerPoint 演示文稿 (.pptx)。"
license: Proprietary. LICENSE.txt has complete terms

tags: [powerpoint,presentation,slides]
category: document
---

# PPTX 演示文稿处理

## 两种工作模式

| 模式 | 适用场景 | 入口 |
|------|---------|------|
| **模板编辑** | 基于已有模板修改内容 | `editing.md` — 解包 XML → 编辑 → 重打包 |
| **从零创建** | 无模板，新建演示文稿 | `pptxgenjs.md` — PptxGenJS 编程式生成 |

## 决策树

```
.pptx 文件操作
├─ 读内容/提取文本 → python -m markitdown file.pptx
├─ 基于模板编辑 → editing.md（unpack→编辑XML→repack）
├─ 从零新建 → pptxgenjs.md（Node.js PptxGenJS）
└─ 生成缩略图预览 → python scripts/thumbnail.py file.pptx
```

## 快速参考

| 任务 | 命令 |
|------|------|
| 读取内容 | `python -m markitdown presentation.pptx` |
| 模板编辑工作流 | 见 [editing.md](editing.md) |
| 从零创建 | 见 [pptxgenjs.md](pptxgenjs.md) |
| 生成缩略图 | `python scripts/thumbnail.py file.pptx` |
| 添加幻灯片 | `python scripts/add_slide.py` |
| 清理模板残留 | `python scripts/clean.py` |

## 模板编辑要点（editing.md）

1. 先分析模板幻灯片布局（thumbnail + markitdown）
2. 选模板幻灯片 → 规划内容映射 → 避免重复同一布局
3. 解包 → 编辑 XML → 重打包

**布局多样性**：多列、图文混排、全图+文字遮罩、引用/数字突出页 → 避免单调的标题+要点重复。

## PptxGenJS 创建要点（pptxgenjs.md）

Node.js 库，编程式生成。详见 `pptxgenjs.md`（含完整 API 参考与代码示例）。
