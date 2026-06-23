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

---

## 核心规则

1. **先建文件再写作** — 创建 `公文_<文种>_<事由简称>.md`，全文写入文件；对话仅输出 ≤5 行摘要
2. **一文一事** — 请示类多个独立事项 → 拆分为多份
3. **待确认项必须列出** — 不确定的数据/人名/日期用 `XX` 占位，列入 `## 待确认事项`
4. **检查报告也按正式公文交付** — 必须套用 `scripts/gb_gongwen.py` 达到可报送的版式要求
5. **格式不合格必须返工** — 用户指出格式问题时，回到 `format-spec.md` 重新生成并按质量门逐项验证，不解释

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

## 快速开始

1. **判断文种**：需批复→请示 / 仅汇报→报告 / 需执行→通知 / 对外商洽→函 / 提建议→建议书
2. **创建文件**：`公文_<文种>_<事由简称>.md`
3. **选择模板**：查阅 `references/templates.md`
4. **填写 + 自检**：替换占位项 → 用 `references/checklist.md` 逐项核验
5. **导出**：需 .docx 时按 `references/workflow.md` 执行
6. **验证**：交付前按 `references/format-spec.md` 质量门逐项检查
