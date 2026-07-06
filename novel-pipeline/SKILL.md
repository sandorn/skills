---
name: novel-pipeline
version: "2.8.0-lightweight"
description: "网文写作流水线-轻量化版：核心规则+跳转参考文档结构，主文档仅保留必看内容，详细流程/模板/说明全部分层到references"
category: writing
tags: [网文, 写作, pipeline, MCP, hermes, 逐章润色]
---

# novel-pipeline: 网文写作流水线（轻量化版）
> 🔴 核心说明：所有润色请求默认走逐章顺序模式，100%复用原有独立润色全流程，废弃所有批量/后台运行逻辑，无前端卡顿
> 📌 详细规则/模板/示例请查看末尾「详细参考」对应跳转文档

---

## 重要工程发现（必看）
### novel-doubao MCP 调用规范
禁止使用`subprocess.communicate()`调用，必须使用线程读取stdout模式，避免触发`anyio.ClosedResourceError`崩溃
### novel-doubao 核心配置
| 配置项 | 值 |
|--------|-----|
| `DOUBAO_BASE_URL` | `https://ark.cn-beijing.volces.com/api/plan/v3` |
| `DOUBAO_MODEL` | `ark-code-latest` |
| `.env` 位置 | `C:\Users\Administrator\.litellm\servers\.env` |
| 服务器 cwd | `servers/novel-doubao/`（必须，否则读不到 .env） |
### 润色结果处理规则
✅ 自动保留原文的所有剧情/人物/战力设定，仅优化文本表达
⚠️ 检测到章节内容截断（结尾无终结标点、剧情未完成）时，不修改原文，直接返回问题提示
### MCP 调用超时配置
| 服务 | 建议 timeout | 说明 |
|---------|------------|------|
| publishready | 60s | 小文本即时返回 |
| uno analyze_text | 60s | 即时返回 |
| novel-doubao polish_chapter | 300s | 大章 9000+字 需 160s+ |

---

## 体系架构
| 角色 | 职责 |
|------|------|
| **调度中枢** | 任务拆解、规则下发、质量校验、状态归档 |
| **初稿生成** | 产出剧情骨架，禁止文笔修饰 |
| **后置润色** | 仅文字优化，锁定全部剧情/人物/事件 |
| **自动检查** | 参数校验、内容质量分析、RED LINE 审计 |
| **持久化** | 世界观/人物/伏笔/战力状态管理 |

---

## Layer 1 规则（最高权重，不可违反）
### 1.1 编排器禁令
⛔ 禁止自行生成长篇正文（>200 字的小说内容）
⛔ 禁止自行润色文本
⛔ 禁止跳过检查点直接输出
⛔ 禁止绕过 MCP 工具直接调用模型 API
⛔ 禁止使用任何批量/后台运行的润色模式
⛔ 禁止自行编写临时润色脚本，所有润色任务必须调用官方 `scripts/polish_chapter.py` 入口
✅ 只做：单章顺序路由 → 调用 MCP → 执行检查 → 单章结果反馈 → 归档
### 1.2 审查流程铁律
⛔ 禁止跳过深筛直接批量修复
⛔ 禁止用脚本扫描结果替代逐章通读审核
✅ 审查流程：深筛 → 发现问题 → 批量修复 → 终验
### 1.3 内容红线
禁止现实政治影射、色情/低俗描写、违法犯罪鼓吹、平台违禁内容
### 1.4 人设底线
主角核心人设不可突破，除非细纲标注弧线且有 ≥3 章铺垫

---

## Layer 2 规则（硬性执行）
### 2.1 任务自动路由
| 用户意图 | 触发词 | 处理概要 | 详细参考 |
|---------|--------|----------|----------|
| 初始化设定 | 世界观/设定/力量体系 | 引导填写 state-files | `project-setup.md` |
| 大纲编排 | 大纲/章纲 | 辅助规划 → 写入章纲文件 | `task_routing.md` |
| **写单章** | 写第N章 | 初稿生成 → 3轮自检 → 润色 → 审计 → 归档 | `quality_check.md` |
| 章节返工 | 重写/修改第N章 | 读现有章 → 初稿重生成 → 自检输出 | `usage-guide.md` |
| **逐章润色** | 「润色」「逐章润色」「批量润色」「独立润色」 + 章节范围 | 单章顺序执行：publishready审计→uno分析→doubao润色→二次复检 → 输出结果 → 下一章（所有旧的批量/独立润色模式已废弃，统一走本流程） | `polish-pipeline.md` |
| 伏笔审查 | 伏笔/回收 | 读 foreshadowing.json → 输出报告 | `usage-guide.md` |
| **卷审查** | 审查/审核 + 卷/章 | 3轮自检：OOC一致性→伏笔覆盖→设定冲突 → 汇总报告 | `volume-audit-protocol.md` |

### 2.2 核心流程概要
#### 写单章流程
`[0] 读取状态 → [1] 参数校验 → [2] 生成初稿 → [3] 3轮自检 → [4] 润色开关判定 → [5] 润色+双审计 → [6] 归档`
> 详细规则/参数/模板：`usage-guide.md`
#### 逐章润色流程
`[0] 读取章节 → [1] publishready审计 → [2] uno质量分析 → [3] doubao润色 → [4] 二次publishready复检 → [5] 保存结果 → [6] 下一章`
> 详细规则：`polish-pipeline.md`
#### 卷审查流程
`[0] 确认范围 → [1] 加载基准 → [2] 批量读章 → [3] OOC检查 → [4] 伏笔检查 → [5] 设定检查 → [6] 汇总报告`
> 详细流程/模板：`volume-audit-protocol.md`

---

## Layer 3 规则（软性优化建议）
- 每 3-4 段一个小转折，每 10 段一个大节奏点，章末 90-95% 埋钩子
- 对话口语化（符合人物性格），感官细节每场景 1-2 处
- 情绪通过身体反应外化（握拳、瞳孔收缩等）
- 拆分"然后…然后…"流水账句式
> 更多写作技巧：`webnovel_triggers.md`

---

## 脚本调用速查
### 核心工具（唯一入口）
| 脚本 | 功能 | 示例 | 详细参数 |
|------|------|------|----------|
| `scripts/polish_chapter.py` | 官方唯一润色工具（逐章顺序调度，禁止任何自定义临时润色脚本，所有润色请求必须走此入口） | `cd D:\\Writer\\novel-project; C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe <Skill路径>\\scripts\\polish_chapter.py 101 .\\chapters` ⚠️ 必须使用完整Python绝对路径调用，禁用长绝对路径作为章节参数，避免Windows路径解析失败误判文件不存在 | `usage-guide.md` |
### Hook 脚本（流程内部自动调用，无需手动执行）
| 脚本 | 作用 |
|------|------|
| `load_state.py` | 读取最新状态作为上下文 |
| `validate_draft.py`/`validate_polish.py` | 参数预校验 |
| `check_draft_quality.py`/`check_ooc_firstory.py`/`check_uno.py` | 3轮自检 |
| `audit_polish.py`/`audit_publishready.py` | 润色后双审计 |
| `polish_independent.py` | 润色核心管线 |
| `archive_state.py` | 状态自动归档 |

---

## MCP 集成状态
| 服务 | 状态 |
|------|------|
| novel-deepseek（初稿生成） | ✅ 正常 |
| novel-doubao（润色核心） | ✅ 正常 |
| publishready（合规审计） | ✅ 正常 |
| uno（质量分析） | ✅ 正常 |
| memory-novel（状态管理） | ✅ 正常 |
> 详细配置/故障排查：`mcp-integration-guide.md` / `troubleshooting.md`

---

## 详细参考（按需加载）
| 内容 | 跳转入口 |
|------|---------|
| 部署指南 + MCP 客户端配置 | `skill_view('novel-pipeline', 'references/deployment-guide.md')` |
| 环境变量模板 | `skill_view('novel-pipeline', 'references/env-template.md')` |
| 3 轮自检详细协议 | `skill_view('novel-pipeline', 'references/quality_check.md')` |
| 任务路由详细规则 | `skill_view('novel-pipeline', 'references/task_routing.md')` |
| 项目初始化/配置指南 | `skill_view('novel-pipeline', 'references/project-setup.md')` |
| 使用指南/参数模板/示例 | `skill_view('novel-pipeline', 'references/usage-guide.md')` |
| 故障排查手册 | `skill_view('novel-pipeline', 'references/troubleshooting.md')` |
| MCP 集成详细说明 | `skill_view('novel-pipeline', 'references/mcp-integration-guide.md')` |
| 旧版本升级指南 | `skill_view('novel-pipeline', 'references/legacy-project-upgrade.md')` |
| 流派适配写作技巧 | `skill_view('novel-pipeline', 'references/genre-adaptation.md')` |
| 批量审计脚本/模板 | `skill_view('novel-pipeline', 'references/batch-audit.md')` |
| 卷审查完整协议 | `skill_view('novel-pipeline', 'references/volume-audit-protocol.md')` |
| 卷审查抽样策略 | `skill_view('novel-pipeline', 'references/volume-review-sampling.md')` |
| 批量章节编辑工作流 | `skill_view('novel-pipeline', 'references/mass-edit-workflow.md')` |
| 润色管线详细规则 | `skill_view('novel-pipeline', 'references/polish-pipeline.md')` |
| 批量格式修复指南 | `skill_view('novel-pipeline', 'references/batch-format-fix.md')` |
| 环境诊断脚本 | `skill_view('novel-pipeline', 'references/verify-env.md')` |
| 网文写作技巧汇总 | `skill_view('novel-pipeline', 'references/webnovel_triggers.md')` |
