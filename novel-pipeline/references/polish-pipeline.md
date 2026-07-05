# 润色管线说明

novel-pipeline 有两条润色管线，适用不同场景。

## 管线一：写单章润色（novel-doubao）

写单章流程中的 [5] 润色链路：
  validate_polish → MCP: polish_chapter (novel-doubao)
  → audit_polish (检查点 D)
  → audit_publishready (检查点 E) ← 链式调用 check_uno.py

- 润色引擎: novel-doubao（仅优化文字，不改剧情/人物/事件）
- 审计: audit_publishready.py 在完成 publishready 的 3 项审计后，末尾自动链式调用 check_uno.py
- 输出: 1 次执行产出 4 份报告（AI腔 + 热点 + 模板合规 + uno 内容质量）
- 适用: 刚写完的章节需要文字润色

## 管线二：独立润色（uno）

独立润色入口：hooks/polish_independent.py

流程：
  ① 读文本
  ② publishready 检查（analyze + audit_ai + hotspots + suggest）
  ③ uno 检查（analyze_text）
  ④ 综合评估 → 确定修复方向
  ⑤ uno 修复（custom_enhance_text，按需开启技巧）
  ⑥ publishready 复检（compare_text_versions）
  ⑦ 输出润色后文本 + 完整审计报告

- 审计在前，修复在后，复检验证
- publishready 发现问题（AI腔/热点），uno 分析质量，综合评估后 uno 执行修复，publishready 再验证修复效果
- 适用: 已有正文但需要增强（扩写环境/动作/消除重复）
- 调用方式: python hooks/polish_independent.py < chapter_text.json
- 输入格式: {"text": "..."} 或 {"chapter": 123}（自动读取章节文件）

## 管线选择规则

| 场景 | 用哪条 | 原因 |
|------|--------|------|
| 刚写完一章，文字需要打磨 | 写单章管线（doubao） | doubao 保留剧情骨架，只优化表达 |
| 已有正文但感觉描写不够 | 独立润色（uno） | uno 会扩写，增强环境/动作/感官细节 |
| 需要审计已有文本质量 | 任意管线都行 | publishready+uno 审计都包含在内 |
| 不想改变字数 | 写单章管线（doubao） | doubao 基本不改变原文长度 |
| 需要扩写 | 独立润色（uno） | uno 的 expansionTarget 控制目标倍数 |
