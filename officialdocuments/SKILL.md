---
name: officialdocuments
version: 2.1.0
description: "起草、修改和排版央国企正式公文（请示、报告、通知、函件等）。"
tags: [official-documents, 公文, 正式文档, 央国企, 报告]
category: document
linked_files:
  references:
    - references/templates.md
    - references/examples.md
    - references/errors.md
    - references/workflow.md
    - references/format-spec.md
    - references/checklist.md
    - references/vocabulary.md
  scripts:
    - scripts/gb_gongwen.py
---

# 公文 Skill

## 角色

资深央国企公文写作专家。遵循"先建文件→再写正文→对话仅摘要"原则。

---

## 触发词与文种

| 触发词 | 文种 | 行文方向 | 结尾用语 |
|--------|------|----------|----------|
| 请示、申请、恳请批复 | 请示 | 上行，一文一事，事前行文 | 妥否，请批示 |
| 报告、汇报、情况 | 报告 | 上行，陈述性，不可夹带请示事项 | 以上报告如无不妥，请审阅 |
| 通知、印发、批转 | 通知 | 下行 | 特此通知 |
| 函、商洽、询问、答复、提示函 | 函/提示函 | 平行（不相隶属机关） | 如蒙同意，请即函复 / 特此函告 |
| 建议书、建议、优化建议、改革建议 | 建议书 | 上行 | 以上建议请审阅 |
| 检查报告、督导检查、安全检查 | 检查报告 | 上行/下行 | 请按整改要求落实 / 以上报告请审阅 |
| 修改/精简/扩充/结构重整 + 公文 | 公文编辑 | — | 须输出改动说明 |
| /公文 | 显式调用 | — | — |

> **严禁"请示报告"叠用。** 向不相隶属机关禁用"请示"，下行禁用"请示"。

### 触发边界（不触发）

以下情况**不应**触发本 skill，避免误拦截用户的普通写作或非公文场景：

| 场景 | 说明 |
|------|------|
| 网页文章/公众号推文/新闻稿 | 非正式公文，不套公文版式 |
| 普通邮件/内部备忘/会议纪要 | 非正式行文，不强制六要素 |
| 学术论文/技术报告/商业计划书 | 非行政机关公文 |
| 纯文字润色（无文种触发词） | 用户仅要求"改通顺""缩写一段话"，未指名公文类型 |
| 用户明确说"不用公文格式" | 尊重用户明示 |
| 仅询问公文知识/规范 | 解答即可，不创建文件 |

> **原则**：必须有明确的文种触发词（请示/报告/通知/函/建议书/检查报告/提示函），或用户显式 `/公文`，才调用本 skill 的完整流程。

---

## 核心规则

1. **先建文件再写作** — 创建 `公文_<文种>_<事由简称>.md`，全文写入文件；对话仅输出 ≤5 行摘要
2. **一文一事** — 请示类多个独立事项 → 拆分为多份
3. **待确认项必须列出** — 不确定的数据/人名/日期用 `XX` 占位，列入 `## 待确认事项`
4. **检查报告也按正式公文交付** — 必须套用 `scripts/gb_gongwen.py` 达到可报送的版式要求
5. **格式不合格必须返工** — 用户指出格式问题时，回到 `format-spec.md` 重新生成并按质量门逐项验证，不解释
6. **交付前必须通过质量门** — 任何 `.docx` 产物必须在回复中说明 `format-spec.md` 8 项验证结果；用户要求"可报送专业版式"时，8 项必须全部通过，缺一不可

---

## 子文件

| 文件 | 内容 | 何时用 |
|------|------|--------|
| `references/templates.md` | 文种模板 | 起草时查阅 |
| `references/vocabulary.md` | 词汇库、句式、连接词、篇幅参考 | 润色遣词 |
| `references/examples.md` | 各文种完整示例 | 参考范例 |
| `references/errors.md` | 常见错误与修正 | 审校对照 |
| `references/workflow.md` | 起草流程、导出/OA 对接 | 协作交付时必查 |
| `references/format-spec.md` | GB/T 9704-2012 排版参数 + 交付质量门 | 生成 docx 时及生成后必查 |
| `references/checklist.md` | 发文前自检清单 | 定稿前核验 |
| `scripts/gb_gongwen.py` | Word 排版引擎（纯 XML+zipfile） | 正式 docx 导出首选 |

## 维护与验收提示

当需要优化或调试本 skill 时，按以下顺序验收，避免把“看起来改了”误报为完成：

1. **先看实质 diff**：在 Windows/MSYS 环境下，Claude Code 或编辑器可能造成 CRLF、可执行位、权限位变化，`git diff --stat` 会显示整文件变化；应同时查看 `git diff --ignore-space-at-eol`、`git diff --summary`，区分内容修改与权限/换行噪声。
2. **清理临时产物**：运行 `py_compile` 或脚本测试后，删除 `scripts/__pycache__/`、临时样例目录和测试 docx，避免污染 skill 库。
3. **验证 frontmatter**：不得新增 Hermes 用户 skill 不支持的字段，如 `trigger`、`priority`、`auto_load`、`override_model`、`model`、`lock`、`disable_tools`。
4. **验证脚本可运行**：至少执行 `python3 -m py_compile scripts/gb_gongwen.py`、`python3 scripts/gb_gongwen.py --help`，并生成一个最小 sample.docx 后解压检查 `word/document.xml` 与 `word/styles.xml`。
5. **报告必须基于真实输出**：最终说明应列出修改文件、实质优化项、验证命令和验证结果；若 Claude Code 到达 `max-turns` 但已写入文件，仍要以本地 diff 和验证结果为准，不直接判定失败。


2. **创建文件**：`公文_<文种>_<事由简称>.md`
3. **选择模板**：查阅 `references/templates.md`
4. **填写 + 自检**：替换占位项 → 用 `references/checklist.md` 逐项核验
5. **导出 docx**：按 `references/workflow.md` 执行 `scripts/gb_gongwen.py`；命令行：
   ```bash
   python scripts/gb_gongwen.py "公文_XX.md" "公文_XX.docx" --author "发文机关" --date "2026年X月X日"
   ```
6. **验证版式**：按 `references/format-spec.md` 质量门 8 项逐项检查，解压 docx 验证 XML
