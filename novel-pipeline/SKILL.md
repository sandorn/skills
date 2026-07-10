---
name: novel-pipeline
version: "3.0.0-lean"
description: "网文写作流水线-精简版：本地 state-files + 两个 stdio MCP（novel-deepseek 初稿 / novel-doubao 润色），逐章顺序执行，无批量后台"
category: writing
tags: [网文, 写作, pipeline, MCP, 逐章润色]
---

# novel-pipeline: 网文写作流水线（精简版）

> 🔴 所有润色请求默认走逐章顺序模式，禁止任何批量/后台运行逻辑
> 📌 详细规则/模板/示例请查看末尾「详细参考」对应跳转文档

---

## 环境与配置（必看）

### 唯一权威 `.env` 位置
`C:\Users\Administrator\.agents\skills\novel-pipeline\.env`

优先级：**Skill 本地 .env → 系统环境变量**。两级都缺则 MCP server 启动即 `sys.exit(1)`。

必需 6 个变量：`DEEPSEEK_{API_KEY,BASE_URL,MODEL}` + `DOUBAO_{API_KEY,BASE_URL,MODEL}`。

### novel-doubao 调用规范
禁止使用 `subprocess.communicate()` 立即关闭 stdin，会触发 `anyio.ClosedResourceError`。必须使用 `hooks/utils.py::BaseMCPClient`（队列+线程读 stdout 模式）。

### MCP 调用超时
| 服务 | 建议 timeout | 说明 |
|------|------------|------|
| novel-doubao polish_chapter | 300s | 大章 9000+ 字需 160s+，可延至 600s |
| novel-deepseek generate_draft | 300s | 一般 30–90s |

### 章节文件命名（强制）
统一三位数补零：`chapters/ch001.md`、`ch010.md`、`ch101.md`。
唯一入口：`hooks/utils.py::chapter_filename(n)`。禁止硬编码 `f"ch{n:02d}.md"`。

### 润色结果处理规则
✅ 自动保留原文的所有剧情/人物/战力设定，仅优化文本表达
⚠️ 检测到章节内容截断（结尾无终结标点、剧情未完成）时，不修改原文，直接返回问题提示

---

## 体系架构
| 角色 | 职责 |
|------|------|
| **调度中枢** | 任务拆解、规则下发、质量校验、状态归档 |
| **初稿生成 (novel-deepseek)** | 产出剧情骨架，禁止文笔修饰 |
| **后置润色 (novel-doubao)** | 仅文字优化，锁定全部剧情/人物/事件 |
| **自动检查** | 参数校验、内容质量分析、RED LINE 审计 |
| **持久化** | 本地 JSON：世界观/人物/伏笔/战力 |

### 状态持久化说明
**本流水线不接任何外部记忆库/知识图谱**。所有跨章上下文（人物、伏笔、战力、世界观）都存 `state-files/*.json` 一份，`load_state.py` 在会话开始读取，`archive_state.py` 在章末写回。若需要多端同步，请自行 git 或云盘同步项目目录。

### 辅助模板（可选，非流水线必需）
`templates/draft_request.py`、`templates/polish_request.py` 是纯请求构建器，供**外部脚本**直接打 API 时参考。**流水线自身不使用**（system prompt 已内嵌在 MCP server），因此改 templates 不影响 pipeline 行为。

---

## Layer 1 规则（最高权重，不可违反）

### 1.1 编排器定位（禁令）
- ⛔ 禁止自行生成长篇正文（>200 字的小说内容）
- ⛔ 禁止自行润色文本
- ⛔ 禁止跳过检查点直接输出
- ⛔ 禁止绕过 MCP 工具直接调用模型 API
- ⛔ 禁止使用任何批量/后台运行的润色模式
- ⛔ 禁止编写任何临时自定义润色脚本，所有润色任务强制使用官方 `scripts/polish_chapter.py` 逐章执行
- ✅ 只做：单章顺序路由 → 调用 MCP → 执行检查 → 单章结果反馈 → 归档

### 1.2 润色执行强制要求
- ✅ 所有润色任务无论章节范围大小，必须逐章执行，完成一章立即向用户反馈该章的字数变化、问题数等结果
- ✅ 润色完成后自动原地覆盖原文件，不生成任何冗余临时文件
- ✅ 禁止任何批量/并行/后台润色操作，避免前端卡顿

### 1.3 审查流程铁律
- ⛔ 禁止跳过深筛直接批量修复
- ⛔ 禁止用脚本扫描结果替代逐章通读审核
- ✅ 审查流程：深筛 → 发现问题 → 批量修复 → 终验

### 1.4 内容红线 & 人设底线
- 禁止现实政治影射、色情/低俗描写、违法犯罪鼓吹、平台违禁内容
- 主角核心人设不可突破，除非细纲标注弧线且有 ≥3 章铺垫

---

## Layer 2 规则（硬性执行）

### 2.1 任务自动路由
| 用户意图 | 触发词 | 处理概要 | 详细参考 |
| --- | --- | --- | --- |
| 初始化设定 | 世界观/设定/力量体系 | 引导填写 state-files | `project-setup.md` |
| 大纲编排 | 大纲/章纲 | 辅助规划 → 写入章纲文件 | `task_routing.md` |
| **写单章** | 写第N章 | 初稿生成 → 3轮自检 → 润色 → 归档 | `quality_check.md` |
| 章节返工 | 重写/修改第N章 | 读现有章 → 初稿重生成 → 自检输出 | `usage-guide.md` |
| **逐章润色** | 润色 + 章节范围 | 单章顺序执行：doubao 润色 → 完整性检查 → 输出结果 → 下一章。**必须调用官方 `scripts/polish_chapter.py`** | `polish-pipeline.md` |
| **纯质量分析** | 分析/质检 + 章节范围 | **仅做检测不修改任何原文**，输出合规结果/质量评分/问题清单 | `quality_check.md` |
| 伏笔审查 | 伏笔/回收 | 读 foreshadowing.json → 输出报告 | `usage-guide.md` |
| **卷审查** | 审查/审核 + 卷/章 | 3轮自检：OOC→伏笔→设定 → 汇总报告 | `volume-audit-protocol.md` |

### 2.2 核心流程概要
- **写单章**：`[0] 读状态 → [1] 参数校验 → [2] 生成初稿 → [3] 3轮自检 → [4] 润色开关判定 → [5] 润色 → [6] 归档`
- **逐章润色**：`[0] 读章节 → [1] doubao 润色 → [2] 完整性检查 → [3] 保存结果 → [4] 下一章`
- **卷审查**：`[0] 确认范围 → [1] 加载基准 → [2] 批量读章 → [3] OOC 检查 → [4] 伏笔检查 → [5] 设定检查 → [6] 汇总报告`

---

## Layer 3 规则（软性优化建议）
- 每 3-4 段一个小转折，每 10 段一个大节奏点，章末 90-95% 埋钩子
- 对话口语化（符合人物性格），感官细节每场景 1-2 处
- 情绪通过身体反应外化（握拳、瞳孔收缩等）
- 拆分"然后…然后…"流水账句式
> 更多写作技巧：`webnovel_triggers.md`

## Layer 4 常见问题处理

### 4.1 工具误报问题
🔍 现象：润色完成后工具返回「篇幅缩水100% (原X→润0)」提示，实际章节字数未发生变化
✅ 处理方案：此为工具检测误报，无需修改原文，直接向用户说明实际情况即可

### 4.2 结尾截断提示
🔍 现象：润色完成后工具返回「结尾无终结标点(可能截断)」提示
✅ 处理方案：
1. 若为章节正常结束（如全书完、卷尾过渡等格式），无需处理，向用户说明内容正常
2. 若为实际内容截断，记录问题告知用户，等待用户确认是否补全内容

---

## 脚本调用速查

### 核心工具（唯一入口）
| 脚本 | 功能 | 示例 |
|------|------|------|
| `scripts/polish_chapter.py` | 官方唯一润色入口（逐章顺序）。⚠️ 禁用任何自定义临时润色脚本 | `python <Skill路径>/scripts/polish_chapter.py 101 D:\\Writer\\novel-project\\chapters` |
| `scripts/verify_env.py` | 环境诊断 | `python <Skill路径>/scripts/verify_env.py [项目根目录]` |

### Hook 脚本（流程内部自动调用）
| 脚本 | 作用 |
|------|------|
| `load_state.py` | 读取最新状态作为上下文 |
| `validate_draft.py` / `validate_polish.py` | 参数预校验 |
| `check_draft_quality.py` | 初稿 3 轮自检 |
| `audit_polish.py` | 润色结果 RED LINE 审计 |
| `polish_independent.py` | 润色核心管线 |
| `archive_state.py` | 状态自动归档 |
| `utils.py` | 共享工具（含 `chapter_filename` / `BaseMCPClient` / `find_state_dir`） |

---

## MCP 集成状态
| 服务 | 位置 | 用途 | 状态 |
|------|------|------|------|
| novel-deepseek | `mcp/novel-deepseek/deepseek_server.py` | 初稿生成 | ✅ 正常 |
| novel-doubao | `mcp/novel-doubao/doubao_server.py` | 章节润色 | ✅ 正常 |

已移除依赖：`firstory` / `uno` / `publishready` / `memory-novel`。所有状态回归本地 `state-files/*.json`。

> 详细配置/故障排查：`mcp-integration-guide.md` / `troubleshooting.md`

---

## 详细参考（按需加载）
| 内容 | 跳转入口 |
|------|---------|
| 部署指南 | `references/deployment-guide.md` |
| 环境变量模板 | `references/env-template.md` |
| 3 轮自检详细协议 | `references/quality_check.md` |
| 任务路由详细规则 | `references/task_routing.md` |
| 项目初始化/配置指南 | `references/project-setup.md` |
| 使用指南/参数模板/示例 | `references/usage-guide.md` |
| 故障排查手册 | `references/troubleshooting.md` |
| MCP 集成详细说明 | `references/mcp-integration-guide.md` |
| 旧版本升级指南 | `references/legacy-project-upgrade.md` |
| 流派适配写作技巧 | `references/genre-adaptation.md` |
| 卷审查完整协议 | `references/volume-audit-protocol.md` |
| 卷审查抽样策略 | `references/volume-review-sampling.md` |
| 批量章节编辑工作流 | `references/mass-edit-workflow.md` |
| 润色管线详细规则 | `references/polish-pipeline.md` |
| 批量格式修复指南 | `references/batch-format-fix.md` |
| 网文写作技巧汇总 | `references/webnovel_triggers.md` |
