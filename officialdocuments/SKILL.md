---
name: officialdocuments
version: 2.3.1
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
    - scripts/qa_docx.py
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
| 制度、管理办法、实施细则、管理规定、管理总则 | 内部管理制度 | 内部 | 章/条结构，非公文六要素 |

> **严禁"请示报告"叠用。** 向不相隶属机关禁用"请示"，下行禁用"请示"。

### 不触发场景

网页文章/公众号推文、普通邮件/会议纪要、学术论文/商业计划书、纯文字润色（无文种触发词）、用户明示不用公文格式、仅询问规范知识——以上不触发本 skill。

---

## 核心规则

1. **先建文件再写作** — 创建 `公文_<文种>_<事由简称>.md`，全文写入文件；对话仅输出 ≤5 行摘要
2. **一文一事** — 请示类多个独立事项 → 拆分为多份
3. **待确认项必须列出** — 不确定的数据/人名/日期用 `XX` 占位，列入 `## 待确认事项`
4. **格式不合格必须返工** — 回到 `format-spec.md` 重新生成，不解释
5. **交付前必须质检** — `.docx` 产物必须运行 `scripts/qa_docx.py` 并在回复中报告结果。CRITICAL/ERROR 项必须全部通过。

### 工作流

1. 创建 md 草稿 → 查阅 `references/templates.md` → 用 `references/checklist.md` 自检
2. 导出 docx：`python scripts/gb_gongwen.py "输入.md" "输出.docx" [--author "机关" --date "日期"]`
3. 质检：`python scripts/qa_docx.py "输出.docx" [--format json]`
4. 制度类不传 `--author --date`（内部管理制度不需要落款）

---

## 子文件

| 文件 | 用途 |
|------|------|
| `references/templates.md` | 文种模板 |
| `references/vocabulary.md` | 词汇库、句式 |
| `references/examples.md` | 各文种完整示例 |
| `references/errors.md` | 常见错误与修正、脚本陷阱 |
| `references/workflow.md` | 起草流程与导出 |
| `references/format-spec.md` | GB/T 9704-2012 排版参数 + 质量门 |
| `references/checklist.md` | 发文前自检清单 |
| `scripts/gb_gongwen.py` | Word 排版引擎（纯 XML+zipfile） |
| `scripts/qa_docx.py` | 产物质检工具（26 项自动化检查） |

---

## 脚本已知陷阱

- **`--author` `--date`** 会生成落款——内部管理制度传这两个参数会在末尾插入公司名称和日期，制度类应省略。
- **公司名称行**：md 第一行如果是公司全称标题头（如 `# XX公司`），是标题组成部分而非落款，不应删除。传入 `--title` 时脚本会自动处理。
- **Markdown 残留**：`gb_gongwen.py` 已内置 `_strip_markdown_inline()` 清理 `**` / `__` / `---`，qa_docx.py 会兜底验证。
- **制度编号重置**（2.3.1+）：`_xml_document()` 遇到**行首**"第X条"的正文段落自动重置二级/三级计数器，避免跨条连续编号 bug。
- **标题层级靠中文编号识别，不认 `#` 语法**：`H1_RE`/`H2_RE`/`H3_RE` 匹配的是"一、xxx"/"（一）xxx"/"1. xxx"。喂入 md 时必须保留中文编号（编号值可任意，脚本会重排），**不能只留 `##` 标记**——否则整篇降级为正文，标题样式全部丢失。
- **编号由脚本重排**：无需在 md 中算好编号，写"（一）"占位即可；一级标题会重置二级计数器。
- **Markdown 有序列表会变三级标题**：`1. xxx` 被识别为样式16并参与全局三级编号。正文中的并列说明若不想进标题层级，改用"其一，""第一，"等表述。
- **Windows CRLF**：脚本已用单反斜杠 `\r\n`/`\n` 分割；修改后必须在 Windows 原生 Python 验证 CRLF 输入。
- **质检报错先辨真伪**：`qa_docx.py` 的编号连续性检查曾有三处误报（正文引用"第七条"、一级标题未识别为边界、表格金额被当编号），均已在 2.3.2 修复。若再遇编号类报错，先按 `references/errors.md` 第九节的排查脚本定位，确认是文档问题还是检查器缺陷，**不要为了让质检通过而改动本身正确的文档**。
- **项目特定约束**（如人员规模、部门名称、弹性措辞等）→ 查阅项目工作目录下的 `AGENTS.md`，不在本 skill 内维护。
