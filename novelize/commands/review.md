---
name: novelize-review
description: 多维度审查 — 4 模式（full/lean/solo/quick）
skill: novelize
---

# /novelize-review — 多维度审查

统一审查入口，支持 4 种审查模式。

## 模式选择

```bash
/novelize-review          # full 模式：4 Agent 并行审查
/novelize-review full     # 同上
/novelize-review lean     # lean 模式：architect + checker
/novelize-review solo     # solo 模式：单线程基础审查
/novelize-review quick    # quick 模式：仅禁令扫描 + 格式检查
```

## Full 模式（4 Agent 并行）

| Agent | 审查维度 | 检查内容 |
|-------|---------|----------|
| architect | 结构 | 主题对齐、大纲完整、钩子/反转质量、范围控制 |
| designer | 角色 | 语言风格一致性、对话质量、人物弧线、关系推进 |
| writer | 文字 | AI 味检测、禁用词、格式合规、节奏均匀度 |
| checker | 事实 | 角色属性一致性、世界规则违反、伏笔状态、时间线自洽 |

## Lean 模式（2 Agent）

| Agent | 审查维度 |
|-------|---------|
| architect | 结构 + 范围控制 |
| checker | 事实一致性 + 伏笔状态 + 格式合规 |

## Solo 模式（单线程）

主 session 直接执行基础审查，不 spawn agent：
- 禁令扫描
- 格式检查
- 连续性检查
- 字数统计

## Quick 模式

执行 bin/ban-check.sh + bin/format-check.sh，仅输出违规清单。

## 附加维度（所有模式）

| 维度 | 说明 |
|------|------|
| 连续性 | 角色/位置/关系/时间连贯性 |
| OOC | 角色行为是否与性格标签一致 |
| 逻辑 | 行为动机、信息边界合理性 |
| 字数 | 是否在允许区间 |
| 伏笔 | 推进/回收状态 |
| 规则 | 通用 + 题材 + 书级规则 |
| 敏感词 | 敏感内容检测 |

## 输出

审查报告格式：
```
VERDICT: APPROVE / CONCERNS / REJECT
SUMMARY: {一句话摘要}
FINDINGS:
  [结构] ...
  [角色] ...
  [文字] ...
  [事实] ...
  [连续性] ...
RECOMMENDATIONS:
  1. ...
  2. ...
```
