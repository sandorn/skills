---
name: officialdocuments
version: 2.2.2
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
    - references/internal-management-systems.md
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
| 制度、管理办法、实施细则、管理规定、管理总则 | 内部管理制度 | 内部 | 依据本制度执行（可附带印发通知） | 适用于甲方对委托运营方的管理制度，采用章/条结构而非公文六要素 |

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
7. **内部管理制度（甲方视角）** — 为甲方起草对委托运营方的管理制度时，遵循"定标准不定操作、管结果不管过程"原则。每项制度须回答：①甲方做什么（监督/考核/结算）②乙方做什么（运营方自己的事）③日常落地动作量（人员少时必须极小）。制度正文用章/条结构，非公文六要素。参见 `references/internal-management-systems.md`。
    - **交叉引用自检**：在写"具体在XX协议/合同中约定"之前，先确认该协议/合同**确实包含该内容**。如果不存在，不可假性委托——要么直接写入制度，要么写"另行协商确定"。
    - **微型团队陷阱**：如果甲方只有2-3人、没有部门划分，制度中**一律不得出现"综合管理部门""财务部门"等具体部门名称**，统一用"分公司""公司"替代。检查考核的频次、时限等严禁写死，用"定期""适时""按需"等弹性表述。参见 `references/internal-management-systems.md` 的 2a 节。
    - **评分细节下沉**：得分计算方式、等级区间、具体扣分标准等机械性细节，**不得写入制度正文**，统一放入附件量化表（如"违规处罚量化表"）。正文仅保留框架性管理逻辑。参见 `references/internal-management-systems.md` 的 4 节。
   - **边界越界自检**：起草时如果自我怀疑"这个制度是不是太细了"，用 reference 中的边界自检表快速判断——≥2个YES=走考核标准路线而非单独发文。

### Windows 环境坑点（CRLF 兼容性）

在本 Windows 主机上，`patch` 工具对 `.md` 文件（CRLF 换行符）的模糊匹配偶尔失败。如果 `skill_manage(action='patch')` 连续失败 2 次以上，改用 `skill_manage(action='edit')` 提供完整文件内容重新写入，而非重复尝试同一匹配模式。

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
| `references/internal-management-systems.md` | 甲方视角内部管理制度起草指导 | 用户需求为内部管理制度时必查 |
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

### gb_gongwen.py 使用陷阱

**P0 双反斜杠 bug（Windows CRLF 换行符导致 parts=1，内容全丢）**：

`markdown_to_parts()` 第 350 行的字符串分割逻辑中，如果写成 `text.replace("\\r\\n", "\\n").split("\\n")`（双反斜杠），Python 会将其解析为**字面量字符串** `\n`（反斜杠+n 两个字符）而非换行符，导致 `split()` 不按换行分割，整个文本变成一行。结果 `markdown_to_parts()` 只识别出标题（第一条 line），**正文全部丢失**。

✅ 正确写法：`text.replace("\r\n", "\n").split("\n")`（单反斜杠，Python 将其解析为真正的回车换行和换行符）

```python
# ❌ BUG：双反斜杠，split 不按换行分割 → parts=1
lines = text.replace("\\r\\n", "\\n").split("\\n")

# ✅ 正确：单反斜杠，split 按换行符分割
lines = text.replace("\r\n", "\n").split("\n")
```

**症状诊断**：生成 docx 后只有标题、无正文、文件仅 2KB。解压 docx 检查 `word/document.xml` 中内容字符总数 <20 即命中此 bug。

**自检**：每次修改 `gb_gongwen.py` 后，用包含 CRLF 换行符的测试文件运行 `markdown_to_parts()` 并断言 `len(parts) >= 10`。仅验证非 CRLF 环境（如 WSL/Linux）的测试不够，必须在 Windows 原生 Python 中验证。

---

**`--author` `--date` 标志不可用于内部管理制度**：

`gb_gongwen.py` 的 `--author` 和 `--date` 标志会在 docx 末尾添加落款（发文机关署名+成文日期）。内部管理制度（非正式上行/下行公文）**不需要落款**，传入这两个标志会在制度正文末尾空两行后插入公司名称和日期。

✅ 在 Python API 调用时不传 `author`/`date` 参数；或在命令行中省略 `--author` `--date`。

---

**公司名称行规则**：

如果 md 文件第一行是 `# 北京中言房地产开发有限公司商业管理分公司`（公司全称作为标题头），这是制度标题的组成部分而非落款，不应删除。

当传入 `title` 参数时，`markdown_to_parts()` 会跳过第一行（`lines[1:]`），第二行作为标题写入 `style="13"`，第一行的公司名称则作为正文（`style="19"`）出现在 docx 中。

---

**Markdown 内联标记残留**：当输入 .md 文件包含 `**加粗**` 语法时（内部管理制度中常见，如 `**第一条**`），`markdown_to_parts()` 在 2.2.1 版本及之前会将 `**` 原封不动写入 docx。

- ✅ 2.2.2+ 版本已在 `markdown_to_parts()` 入口自动调用 `_strip_markdown_inline()` 清理 `**`、`__` 和 `---` 分隔线。
- 🔄 调用脚本生成 docx 后，须解压验证 `word/document.xml` 中不含有 `**` 字符串。
- ⚠️ 如仍出现残留，在调用前手动执行 `re.sub(r'\\*\\*(.*?)\\*\\*', ...)` 预清洗。
