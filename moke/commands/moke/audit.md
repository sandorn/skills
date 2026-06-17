---
name: moke:audit
description: Audit chapter quality / 审计章节质量
---

<objective>
Review the latest chapter for quality issues across 37 audit dimensions (including AI-tell detection).
</objective>

<process>
1. 读取最新章节
   - 路径：`books/<书名>/chapters/第N章-<标题>.md`
   - 按文件名排序找到最新章节

2. 读取上下文文件
   - `story/current_state.md` - 当前状态卡
   - `story/particle_ledger.md` - 资源账本
   - `story/pending_hooks.md` - 伏笔池
   - `story/chapter_summaries.md` - 章节摘要（用于节奏检查）
   - `story/subplot_board.md` - 支线进度板
   - `story/emotional_arcs.md` - 情感弧线
   - `story/character_matrix.md` - 角色交互矩阵
   - `story/volume_outline.md` - 卷纲（用于大纲偏离检测）
   - `story/style_guide.md` - 文风指南
   - `story/parent_canon.md` - 正典参照（番外专用，可选）
   - `story/fanfic_canon.md` - 同人正典（同人专用，可选）

3. 执行质量审计（37维度）
   - **基础维度（1-27）**：OOC、时间线、设定冲突、战力崩坏、数值检查、伏笔、节奏、文风、信息越界、词汇疲劳、利益链、年代考据、配角降智、配角工具人、爽点虚化、台词失真、流水账、知识库污染、视角一致性、段落等长、套话密度、公式化转折、列表式结构、支线停滞、弧线平坦、节奏单调、敏感词
   - **番外维度（28-31）**：仅当parent_canon.md存在时启用
   - **通用维度（32-33）**：读者期待管理、大纲偏离检测（始终启用）
   - **同人维度（34-37）**：仅当fanfic_canon.md存在时启用

4. AI痕迹检测（纯规则，无LLM）
   - dim 20: 段落等长（变异系数<0.15）
   - dim 21: 套话密度（>3次/千字）
   - dim 22: 公式化转折（转折词≥3次）
   - dim 23: 列表式结构（连续相同开头≥3句）
   - AI标记词：仿佛/不禁/宛如/竟然/忽然/猛地（每3000字≤1次）

5. 生成审计报告
   - 输出JSON格式到`runtime/audit-report.md`

6. 输出问题清单
   - 按严重程度（critical/warning/info）分类
   - 只有critical问题导致审计不通过
</process>
