# Writer Skill 参考文件索引

> 版本：v7.0 | 最后更新：2026-06-26

## 用途

本文件是 `references/` 目录的全局索引。列出每个文件的功能、加载策略和依赖关系。

## 加载策略

| 策略 | 说明 |
|------|------|
| **预加载** | 每次写作会话自动加载（核心工作流文件） |
| **按需加载** | 根据用户意图匹配路由表后加载 |
| **参考** | 仅在特定场景或深入阅读时加载 |

---

## 核心工作流（预加载 — 14 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `hard-bans.md` | 硬性禁令单一事实来源（P0-P2 分级） | — |
| `review.md` | 43 维审查 + Triage（5 种模式：quick/daily/solo/lean/full） | hard-bans.md, agents/ |
| `review-cycle.md` | 5 步审查管线权威定义（含 facts.db 降级） | review.md, quality.md, post-review-fix.md |
| `write.md` | 写作管线（单章/批量/短篇，含 sub-agent delegation 自检） | pre-write-alignment.md, write-pitfalls.md |
| `write-pitfalls.md` | 批量写作避坑指南（13 项实战教训） | setting-consistency-audit.md |
| `quality.md` | 质检工单（禁令扫描+去AI味+段落修复+RAG+事实库） | hard-bans.md, audit.py |
| `plan.md` | 大纲规划（总纲→卷纲→章纲） | deploy.md |
| `project-init.md` | 项目初始化（含 import 模式） | templates/project-skeleton/ |
| `pre-write-alignment.md` | 批量写前 4 层总线对齐检查 | write.md |
| `pre-write-checklist.md` | 写前 30 秒检查清单 | hard-bans.md |
| `publishable-check.md` | 章节快速可发布性三问判定 | hard-bans.md |
| `manual-polish.md` | 纯手动逐章逐段润色（三零原则：零脚本/零子代理/零批量） | optimize.md |
| `memory.md` | 记忆/查询/学习 | — |
| `tool-pitfalls.md` | AI 写作环境中的工具交互陷阱（通用，不限于特定平台） | — |

---

## 审查与审计（按需加载 — 5 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `targeted-audit.md` | 用户指定维度的定向审查（vs. review.md 的规则驱动） | review.md |
| `post-review-fix.md` | 审查后修复管线（修复决策树 + 5步/4步管线） | hard-bans.md, audit.py, pad_chapter.py |
| `hooks-scan.md` | 伏笔全卷扫描方法（5 级阅读优先级策略） | — |
| `longform-quality-monitor.md` | 长篇质量趋势监控（声音漂移/情绪/风格指纹） | — |
| `master-outline-audit.md` | 总纲暗线对齐检查 | — |

---

## 一致性校验（按需加载 — 2 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `setting-consistency-audit.md` | 设定一致性跨文件审计（统一入口：内部→大纲→正文→卷间→修复） | — |
| `track-character-state.md` | 角色状态追踪更新 | — |

---

## 文风规范与转换（按需加载 — 2 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `style-sop.md` | 可扩展文风SOP模块（番茄风默认，预留多文风接口） | — |
| `style-transfer.md` | 文风转换/批量AI润色管线 | `scripts/polish.py`, `style-sop.md` |

---

## 场景化工作流（按需加载 — 7 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `scan.md` | 跨平台扫榜 + 趋势分析 | — |
| `analyze.md` | 爆款拆解 + 黄金三章 | — |
| `deploy.md` | 多卷部署流水线 + 卷间衔接检查 | plan.md, review-cycle.md |
| `fanqie-submission.md` | 番茄投稿格式兼容检查 | — |
| `cover.md` | 封面生成（含多平台尺寸表） | — |
| `optimize.md` | 全量优化（意象钩子清理+钩子强度提升） | analyze_hook.py |
| `fix-template-cleanup.md` | 模板复制+乱码清除工作流 | pad_chapter.py |

---

## 参考资料（按需加载 — 3 个）

| 文件 | 功能 | 关键依赖 |
|------|------|---------|
| `opening-craft.md` | 开篇技巧（重生文为主，含多类型通用原则） | — |
| `project-knowledge-base.md` | 项目知识库工具集成指南（通用，不限于特定平台） | fact_db.py, report_panorama.py |
| `troubleshooting.md` | 常见故障排除（写章/审查/委派/修复四场景） | — |

---

## 文件依赖关系图

```
hard-bans.md (单一事实来源)
  ├── quality.md → audit.py, split_paragraphs.py
  ├── review.md → agents/ (4 agent templates)
  ├── review-cycle.md → review.md, quality.md, post-review-fix.md
  ├── write.md → pre-write-alignment.md, write-pitfalls.md
  ├── pre-write-checklist.md
  ├── publishable-check.md
  └── post-review-fix.md → pad_chapter.py, audit.py

plan.md → deploy.md → review-cycle.md
project-init.md → templates/project-skeleton/ (11 templates)
setting-consistency-audit.md (合并 cross-validation + cross-setting-consistency)

style-sop.md → style-transfer.md → scripts/polish.py  (文风系统)
style-sop.md → quality.md (禁令/参数映射到质检管线)
```

---

## 脚本速查

| 脚本 | 功能 | 层级 |
|------|------|------|
| `scripts/polish.py` | AI润色/文风转换（模型无关） | 核心 |
| `scripts/audit.py` | 统一审计（单章/目录/范围） | 核心 |
| `scripts/pad_chapter.py` | 安全字数追加 | 核心 |
| `scripts/split_paragraphs.py` | 段落拆分（≤60汉字） | 核心 |
| `scripts/analyze_hook.py` | 追读力分析 | 核心 |
| `scripts/fact_db.py` | SQLite 事实库 | 核心 |
| `scripts/report_panorama.py` | 项目全景报告 | 核心 |
| `scripts/writer` | 统一 CLI 入口（12 子命令） | 核心 |
| `scripts/audit_5dim.py` | 5维专项审查 | 扩展 |
| `scripts/analyze_rhythm.py` | 节奏状态查询 | 扩展 |
| `scripts/report_graph.py` | 实体关系图谱 | 扩展 |
| `scripts/export.py` | 多平台格式导出 | 扩展 |
| `scripts/backup.py` | 每日自动备份 | 扩展 |
| `scripts/tests/test_core.py` | 核心函数单元测试（14用例） | 测试 |

---

## 文风预设速查

| 预设文件 | 说明 |
|----------|------|
| `references/presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风 — 系统提示词预设 |

---

## Agent 模板速查

| 模板 | 功能 | 推荐模型级别 |
|------|------|---------|
| `agents/story-architect.md` | 故事结构审查（维度 1-15） | sonnet-class |
| `agents/consistency-checker.md` | 事实一致性审查（维度 16-27） | haiku-class |
| `agents/narrative-writer.md` | 文本质量审查（维度 28-36） | haiku-class |
| `agents/character-designer.md` | 角色与对话审查 | sonnet-class |

---

## 版本兼容性

| Skill 版本 | 脚本 API | 项目格式 | 平台兼容 |
|-----------|---------|---------|---------|
| 5.x | sys.argv-based | writer.json v1 | Claude 专用 |
| 6.x | 混合 (argparse + sys.argv) | writer.json v1 | Claude 专用 |
| 7.6 (当前) | 统一 argparse | writer.json v1 | **通用** |
