# 既有公文草稿「完整优化」工作流（请示类实战）

> 触发：用户甩来一份既有公文草稿（docx），要求「完整优化 / 润色 / 改一版」，
> **包括文件名、标题、正文**。不同于从零起草——优化稿必须逐条对照原文，
> 最终交付「成品 docx + 改动说明表 + 待确认事项」。

## 一、工作流（顺序不可颠倒）

1. **前置审计**（先读后写，禁止凭草稿自称的信息下手）
   - 同目录/相邻目录检索：配套的**需求单/立项单**、**同类先例请示/报告**、**所涉制度及其版本谱系**。
   - 命令：`search_files(target='files', pattern='*关键词*')` + `search_files(target='content', pattern='关键词1\|关键词2')`。
   - 价值：草稿里含糊的「大厦」「此合同」「相关规定」都能被先例文件坐实为**具体名称、日期、文号**。
2. **取佐证**：历史请示/合同多为 PDF（有些是 UTF-16BE 伪 docx）。
   - PDF 文本：写 .py 落地脚本，`uv run --with pymupdf python x.py`（本机 pip 被 PEP 668 禁用）。
   - .doc 旧格式：Word/WPS COM 转 txt 后再检索。
3. **逐项优化**（见第二节清单与第三节语病对照）。
4. **排版落地**：md → `gb_gongwen.py` → `qa_docx.py`，31 项全过才算完。
5. **交付**：文件名与标题同名；原稿**移入 `历史版本备份\`**（命名为 `<原名>_原稿<YYYYMMDD>.docx`），不删除；回复给**改动说明表**（序号/位置/原文/改后/理由）+ **待确认事项**。

## 二、请示要素补齐清单（草稿缺项 = 审批无据）

实战中用户草稿常只有 3 个方案要点，缺下列**硬要素**：

| 要素 | 缺失后果 | 数据出处 |
|---|---|---|
| 标题**具名标的** | 「关于采购大厦……」不知是哪座大厦 | 先例文件名/合同名 |
| 引据段：**相对方全称、签约日期、合同全称、到期日** | 无法判断合同状态 | 历史请示 PDF、合同归档目录 |
| 一、**项目基本情况**（地址/面积/业态/服务范围） | 审批人不知道买的是什么 | 采购需求单 |
| **服务/技术模式** | 无法判断方案合理性 | 需求单「特殊事项说明」 |
| **采购方式 + 是否委托招标代理** | 与需求单口径脱节 | 需求单「申请采购方式」 |
| **期限的起止日期 + 续约条件** | 只写「3年、1+1+1」等于没说 | 需求单「项目实施时间」 |
| **预算总额**（不只单价） | 看不出金额规模、无法判断审批层级 | 需求单「项目预算」 |
| **执行段**（获批后谁办、按什么程序、是否上会） | 请示事项不闭环 | 采购管理办法分级审批条款 |
| **附件** | 立项材料不齐 | 需求单文件实体 |

> 补齐属「标配要素补全」，**不是新增决策内容**——每一个补进去的数字都要能在既有材料里指出来，
> 并在改动说明表中标注出处。拿不到出处的数值一律用 `XX` 占位并列入待确认事项。

## 三、常见语病对照（央国企请示）

| 原文 | 改后 | 理由 |
|---|---|---|
| 为了保障……的品质 | 为保障……品质 | 公文用「为」，「为了…的」口语化 |
| 此合同于2022年签订，以补充协议延长至2026年底 | 于X年X月X日与XX公司签订《合同全称》，其后多次签订补充协议，期限至X年X月X日届满 | 补主体/日期/全称；「年底」改确切日期 |
| 具体工作**汇报**如下 | 现将有关情况**请示**如下 | 请示不得自称「汇报」（那是报告用语） |
| 采购**服务期限** | **服务期限** | 采购是一次行为，服务期才是标的口径 |
| 拟定**以**公开招标的**方式**进行采购 | 拟定**采用**公开招标**方式**实施采购 | 动宾搭配 |
| 根据……**相关规定** | 根据《制度全称》及公司授权管理有关规定 | 依据须可追溯；版本未定则用不带版本的弹性表述 + 列入待确认 |
| 达到产权方对于物业服务方的有效监督及管控 | 满足产权方对物业服务单位的有效监督及管控要求 | 「及」→「和/与」；指代不明的「产权方」保留原词但列入待确认 |

## 四、gb_gongwen.py 落款只支持两行 —— 三行落款的外科补行

**问题**：`--author`/`--date` 只生成「机关 / 日期」两行。但不少单位的**部门请示**惯例是**三行**：
`机关` / `部门` / `成文日期`（同目录多个先例 PDF 均为此格式）。

**做法**：先用引擎正常生成，再对 `word/document.xml` 做**定点正则补行**（不改其它任何部件）。

```python
import re, zipfile, sys
SKILL = r"C:/Users/Administrator/AppData/Roaming/cn.org.hermesagent.desktop/runtime/hermes-home/skills/officialdocuments/scripts"
sys.path.insert(0, SKILL)
import gb_gongwen

AUTHOR, DEPT, DATE = "XX公司", "XX部", "2026年10月14日"
parts = gb_gongwen.markdown_to_parts(md_text, None, AUTHOR, DATE)   # 尾部自动带 sign 段
parts[-1] = ("sign", AUTHOR, DATE)
gb_gongwen.generate(parts, OUT, author=AUTHOR)

with zipfile.ZipFile(OUT) as z:
    items = {n: z.read(n) for n in z.namelist()}
doc = items["word/document.xml"].decode("utf-8")
sign_re = re.compile(
    r'(<w:p><w:pPr><w:pStyle w:val="19"/><w:jc w:val="center"/><w:ind w:left="\d+"/>'
    r'<w:spacing[^/]*/></w:pPr><w:r><w:t xml:space="preserve">)'
    + re.escape(AUTHOR) + r'(</w:t>)<w:br/>'
    + r'(<w:t xml:space="preserve">)' + re.escape(DATE) + r'(</w:t></w:r></w:p>)')
new, n = sign_re.subn(
    lambda m: m.group(1) + AUTHOR + m.group(2) + '<w:br/>'
    + '<w:t xml:space="preserve">' + DEPT + '</w:t><w:br/>'
    + m.group(3) + DATE + m.group(4), doc)
assert n == 1, "落款段替换失败，命中 %d 次" % n     # 命中数必须断言，防静默改错
items["word/document.xml"] = new.encode("utf-8")
... 重新打包 zip → 覆盖 OUT → 跑 qa_docx.py
```

**要点**
- 落款段缩进由引擎按 `max(机关,日期)` 宽度算，加一行较短的部门名**不影响**对齐，无需重算。
- 正则必须用 `subn` 取命中数并断言 = 1，避免「改了个别的地方」却毫无察觉。
- 补行后必须回读 `document.xml` 逐段打印确认 `br` 数（三行落款 = 该段 `<w:br/>` 计数为 2）。

## 五、陷阱

- **两份同名 `officialdocuments`**：`skills\officialdocuments\`（带 `scripts\gb_gongwen.py`、`qa_docx.py`、完整 references）与
  `skills\document\officialdocuments\`（仅 SKILL.md + 部分 references）。
  `skill_view(name='officialdocuments')` 会因歧义**直接拒绝**——用 `skill_view('document/officialdocuments')`，
  或直接 `read_file` 绝对路径。要用脚本时必须走**前者**的路径。
- **`gb_gongwen.py` 标题层级只认中文编号**（`一、`/`（一）`/`1.`），不认 `#`。md 里喂中文编号，编号值随便写，脚本会重排。
- **`（一）小标题。正文……` 写在同一行会让整段变成楷体二级标题**。小标题要么单独成行，要么干脆不用二级、改用「一是/二是」写在正文段里。
- **主送机关顶格**：引擎把 md 所有正文段都加了 `firstLine=640` 缩进，「XX：」也会被缩进。需在补行脚本里顺手把主送机关段的 `<w:ind .../>` 去掉。
- 交付前跑 `qa_docx.py`（31 项），并在回复中报告结果；CRITICAL/ERROR 必须全过。
