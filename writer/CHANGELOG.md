# Writer Skill 变更日志

> 从 SKILL.md 外移，避免每次加载消耗上下文。

| 日期 | 版本 | 关键变更 |
|------|------|---------|
| 2026-06-30 | **v7.7 基础设施重构** | 创建 `scripts/lib.py` 共享工具模块（统一 count_chinese/extract_body/scan_chapter_files 等 8 个重复函数）；修复 `pad_chapter.py` 硬编码 15 个角色名+固定随机种子（→动态加载+内容哈希种子，加 .bak 备份）；修复 `report_graph.py` MAIN_CHARACTERS/RELATION_VERBS 空字典（→自动检测+项目文件加载）；修复 `polish.py` .format() 崩溃风险（→try/except KeyError）；修复 `analyze_hook.py`/`audit_5dim.py` 硬编码角色名（→参数化）；修复 `audit.py` 模板检测硬编码语义关键词（→通用指纹匹配）；修复 `split_paragraphs.py` 换行不一致 bug（→统一 \n 处理+备份）；`export.py` 三格式函数去重（→_export_base 共用）；SKILL.md 变更日志外移为 CHANGELOG.md；清理 10+ .pyc 残留文件；修复 CLI wrapper FIX_ALIASES 死代码 |
| 2026-06-30 | **v7.6 文风系统** | 新增 `references/style-sop.md`（可扩展文风SOP模块，6维接口+番茄预设）；新增 `references/style-transfer.md`（文风转换/批量AI润色管线）；新增 `scripts/polish.py`（模型无关通用润色脚本，支持断点续传+字数控制）；SKILL.md 路由表新增文风转换/转写/文风规范条目；修复 `audit.py` template_issues NameError；清理 `report_panorama.py` 死代码 run_script()+unused import；清理 `report_graph.py` 死代码 count_chinese()；`pad_chapter.py`/`audit_5dim.py` 增加项目适配警告；`00-index.md` 补全文风系统文件和缺失引用 |
| 2026-06-29 | **v7.5 manual-polish 闸门加固** | manual-polish.md Step 3 新增「逐章闸门」（三问自检，任一否禁入下一章）；⑦ 报告格式强制维度表+改前→改后例句，列四类退化报告为禁止形式；陷阱四「润色降级为禁令修复」判例；hard-bans.md B03 扩展覆盖「不是…是…」短式变体 |
| 2026-06-29 | **v7.4 逐章审查加固** | SKILL.md 逐章审查路由大幅扩展（明确禁止脚本/加速/跳过；新增「不用脚本」触发词和五条硬性禁令）；SKILL.md 新增「章节污染模式速查」节（①②③三种污染模式+修复方法）|
| 2026-06-28 | **v7.3 审查+重构+污染** | 新增 `references/corruption-fix-bu-shi.md`（「不→是」污染修复权威参考）；委派后校验节重构（外链参考文件 + 逐章审查路由 + 开篇节奏重构指引）；write-pitfalls.md 新增避坑 14-18（Windows路径/文风偏好/开篇重构/声音定调/批量替换污染）；SKILL.md 声音偏好节扩展（番茄小说向） |
| 2026-06-28 | **v7.2 委派后污染校验** | 新增「委派后校验」节；状态感知新增 `writing_rules.md` 自动加载 |
| 2026-06-26 | **v7.0 通用化** | 移除所有 Claude/Hermes 专用术语（delegate_task→sub-agent delegation, web_search→web/content search, image_generate→image generation tool, search_files→grep/pattern search, Moke/Hermes 移除）；agent YAML 泛化（tools→capabilities, model→advisory_model, maxTurns→max_iterations）；hermes-tool-pitfalls.md→tool-pitfalls.md（通用工具陷阱）；codebase-memory-mcp.md→project-knowledge-base.md（通用知识库指南）；SKILL.md 执行策略与子模块索引同步更新 |
| 2026-06-23 | **v4.0-v6.0** | 激进瘦身（v4.0 -62%）；日更审查模式（v4.1）；执行层加固（v4.2-4.4）；文件合并（v4.5-4.7）；CLI 统一入口（v5.0）；管线压缩（v5.1-5.9）；v6.0 发布——210 行 SKILL.md · 32 references · 12 scripts(含 CLI) · 4 agents · 11 个模板 · 零旧引用 |
