# Writer Skill 集成记录

本 skill 是融合 4 套系统的产物。以下记录设计决策、来源和边界。

---

## 来源系统

| 系统 | 作者/来源 | 文件位置 | 集成方式 |
|------|----------|---------|---------|
| story-* (13个skill) | worldwonderer | ~/.claude/skills/story-*/ | 方法论提取：扫榜/拆文/情绪驱动写作/对抗审查/去AI味哲学/封面 |
| webnovel-* (8个skill) | lingfengQAQ | ~/.claude/skills/webnovel-*/ | 管线提取：深度初始化/增量规划/量产写章/审查落库/记忆学习/查询/体检 |
| novel-pipeline | 自编 | ~/.claude/skills/novel-pipeline/ | 链式调度思路 + 数据传递协议 |
| Moke | ihengya (npm) | ~/.agents/skills/moke/ | 9-Agent管线设计/37维审计框架/批量写章 |
| novelize | 其他AI | ~/.agents/skills/novelize/ | 局部提取：6 Gate去AI味/AI高频词黑名单/quick审查模式/format+narrative+outline rules |

## 设计决策

### 目录命名（2026-06-17 确认）
- 新项目：全英文（setting/outline/chapters/tracking/）
- 旧项目：兼容中文（设定/大纲/正文/追踪）
- 新创建时默认英文，读取时双路径解析

### 模板文件（2026-06-17 修复）
- character_matrix.md → characters.md（重命名匹配 project-init.md 引用）
- 补充 power_system.md + factions.md 模板
- state-format.md 从 templates/project-skeleton/ 移至 references/（属于参考文档而非模板）

### Agent 模板（2026-06-17 新增，来自 novelize 借鉴）
- agents/story-architect.md — 结构审查 Agent 指令
- agents/consistency-checker.md — 设定/事实审查 Agent 指令
- agents/narrative-writer.md — 文本/AI痕迹审查 Agent 指令
- agents/character-designer.md — 角色/对话审查 Agent 指令
- review.md full 模式改为引用 agents/ 目录下的模板文件

### 审查分级 S1-S4（2026-06-17 新增，来自 novelize 借鉴）
- S1=Critical 直接矛盾，S2=Major 隐性矛盾，S3=Minor 细节不一致，S4=Advisory 潜在风险
- 所有审查报告按此分级输出

### writer.json 增加 author 字段（2026-06-17 修复）
- 封面生成和项目初始化时使用
- 同步更新 SKILL.md、project-init.md、state-format.md 中的 schema

### 默认写作管线（2026-06-17 确认）
- 默认 5 步：Plan → Architect → Write+Reflect → Audit+Norm → Revise
- `--fast`：Plan → Write → Audit → Revise
- `--full`：Moke 9 步完全展开

### 长短篇合并（2026-06-17 确认）
- 同一 write.md 入口，`--short` 参数切换
- 短篇：情绪驱动、第一人称、单个反转、不启动追踪
- 长篇：章节连续、卷级规划、可批量

### 工具适配（2026-06-17 修正另一AI的修改）
- 所有工具名统一为 Hermes 标准：clarify / delegate_task / web_search / web_extract / image_generate
- 拒绝 VS Code/Copilot 原生工具名（vscode_askQuestions / runSubagent / fetch_webpage）

## 边界

### 不包括的旧系统能力
- Claude Code hook 机制（session-start/detect-gaps/validate-commit → 已转化为文档）
- Claude Code rules 目录（→ 已转化为规则内嵌）
- moke 的 JS 安装脚本（→ 不需要，纯 skill）
- webnovel-dashboard Web 面板（→ 没有 Hermes 前端集成方案，暂放）
- 其他 AI 的 novelize 完整 skill（→ 只取其精华模块）

### 未解决的问题
- full 审查的子 Agent spawn 需要用户确认 delegate_task 配置
- 短篇模板库（盐选风格专用）尚未独立
