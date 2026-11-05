---
name: officialdocuments
version: 2.4.2
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
    - references/diff_docx_parts.md
    - references/gongwen-draft-optimization.md
  scripts:
    - scripts/gb_gongwen.py
    - scripts/qa_docx.py
    - scripts/fix_theme_fonts.py
    - scripts/make_gongwen_dotx.py
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
| `references/diff_docx_parts.md` | 包级修复后的「内容零影响」验证脚本与判定标准 |
| `references/gongwen-draft-optimization.md` | **既有草稿「完整优化」工作流**（文件名/标题/正文）：前置审计→佐证提取→请示要素补齐清单→语病对照表→三行落款外科补行脚本→改动说明表交付 |
| `scripts/gb_gongwen.py` | Word 排版引擎（纯 XML+zipfile） |
| `scripts/qa_docx.py` | 产物质检工具（31 项自动化检查） |
| `scripts/fix_theme_fonts.py` | 存量 docx 主题字体修复（MS 明朝/ja-JP/裸 Courier） |
| `scripts/make_gongwen_dotx.py` | 由 Normal.dotm 派生无宏公文模板 `.dotx`（绕开 WPS 内置日文主题底子）|

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
- **二级标题 >10 项必须验证编号**（2.3.2+）：脚本 `cn_num()` 支持 1-99 中文序号。生成后 grep `^\（\d+\）` 检查标题行，确认无 `（11）（12）` 残留（正文款项 `（1）` 属正常）。详见 `references/errors.md` 第九节缺陷4。
- **MS 明朝是包级污染**（2.4.0+）：`gb_gongwen.py` 已显式输出 settings.xml/theme1.xml，东亚 ea 槽位非空、`themeFontLang=zh-CN`。**存量带雷 docx**（原文件自带，不只新增段）用 `python scripts/fix_theme_fonts.py "稿件.docx"` 原地修复（自动留 .bak）；qa_docx 新增「第三·五层」6 项拦截。详见 `references/errors.md` 第九节缺陷5。
- **裸 Courier 缺字弹窗**（2.4.0+）：同一类包级字体污染——`styles.xml`/`fontTable.xml` 引用系统不存在的裸名 `Courier`（macro 样式），打开弹「是否替换为 Courier New」。`fix_theme_fonts.py` 已内置 `LEGACY_FONT_MAP` 一并消除（负向前瞻保护 `Courier New` 不被误改）。详见 `references/errors.md` 第九节缺陷5附带的雷。
- **修复稿必须验证内容零影响**：对存量 docx 做任何包级修复前，先产出 `-o` 测试稿，用 `references/diff_docx_parts.md` 的比对脚本验证「非目标部件字节一致 + 正文段落逐字 diff 一致」，结果报告给用户、经目检确认后才原地修复原件。文件被 Word/WPS 占用时 zip 打开会报 "used by another process"，需先关闭。
- **损坏/异常 docx 抢救**：批量扫描须捕获 `zipfile.BadZipFile`；按文件头 8 字节甄别空壳、macOS 资源叉、WPS 私有封装（`F1 03 F2 03 F3 03 F4 03`，需 COM 转档后补跑 `fix_theme_fonts.py`）、半截 zip（扫 `PK\x03\x04` 逐条重打包抢救）。详见 `references/errors.md` 第九节缺陷6。
- **落款只支持两行，三行需外科补行**：`--author/--date` 生成「机关 / 日期」两行；不少单位的**部门请示**惯例是三行「机关 / 部门 / 日期」。对 `document.xml` 落款段做定点正则补 `<w:br/>`，`subn` 的命中数**必须断言 = 1**（防静默改错位置），补行后回读该段确认 `<w:br/>` 计数为 2。完整脚本见 `references/gongwen-draft-optimization.md`。
- **主送机关会被缩进**：引擎给所有正文段加 `firstLine=640`，md 里的「公司领导：」也会被缩进；公文主送机关应**顶格**，需在补行脚本里一并去掉该段 `<w:ind>`。
- **qa 按样式名解析，不认 styleId 编号**（2.4.1+）：`STYLE_SPEC` 的 `id` 只是 gb_gongwen 产物的固有编号，实际按 `aliases` 里的样式名（`标题/公文标题`、`一级标题/公文1级`、`正文/公文正文/Normal`…）定位，并沿 `basedOn` 链补齐字体字号。此前硬编码 13/14/15/19 会把 **WPS 宏产物**（套装名「公文标题/公文1级/…」、编号 18/13/15/16）判成大面积不合格——那是检查器误报，不是文档问题。
- **主题拦截可被「惰性主题」豁免**（2.4.1+）：当 `document.xml`+`styles.xml` 的 `w:*Theme` 引用数为 0，且 `docDefaults` 已显式锁定 `eastAsia` 字体时，`theme1.xml` 的空 `a:ea` 槽与 `Jpan` 日文回退**永不参与渲染**，第三·五层降为 WARNING 不阻断；真依赖主题的文档（`refs>0` 或 docDefaults 无东亚字体）仍照常拦截。判定函数 `_theme_inert()`。
- **宏产物主题脏 ≠ 版式错**：`word.bas` 的公文宏（`自动格式化文档`）产物 `*Theme` 引用为 0、字体全显式，实际渲染正确；仅 `theme1.xml` 底子来自 WPS 内置日文主题。根治只能换新建载体——用 **`中言公文模板.dotx`**（`%APPDATA%\kingsoft\office6\templates\`，由 Normal.dotm 剥离 VBA 派生，主题干净）新建文档后再跑宏，产物 31/31 全绿。详见 `references/errors.md` 第九节缺陷7。
- **二级标题不可与正文同行**：`（一）小标题。正文……` 写在一行会让**整段**套上楷体二级标题样式。小标题要么单独成行，要么不用二级、改用「一是/二是」写在正文段内。
- **起草/优化前先找「配套材料」**：同目录往往已有**采购需求单、先例请示、所涉制度**。草稿里的「大厦」「此合同」「相关规定」等含糊指代，能从这些材料坐实为具体名称/日期/文号/金额。请示缺**预算总额**、缺**标的概况**是硬伤——照需求单补齐，每个数字都要能在既有材料里指出来并在改动说明表中标注出处；拿不到出处的用 `XX` 占位并列入待确认。
- **起草前先检索目标目录**：制度类任务开工前，先 `search_files` 目标目录下是否已有同名/近似制度稿（含"待审定""清洁版"等后缀）。用户既有稿件可能基于同一上位制度改写，先发现才能避免产出平行冲突稿。
