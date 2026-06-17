---
name: novelize-deslop
description: 去AI味 — 6 Gate 逐项清除，支持轻度/中度/重度三级
skill: novelize
---

# /novelize-deslop — 去 AI 味

对正文执行 6 Gate 去 AI 味处理，支持三级力度。

## 用法

```bash
/novelize-deslop              # 自动检测级别 + 逐项清除
/novelize-deslop --level 轻度  # 仅 Gate A+B
/novelize-deslop --level 中度  # Gate A-D
/novelize-deslop --level 重度  # Gate A-F 全量
```

## 6 Gate 详解

| Gate | 检查内容 | 处理方式 |
|------|----------|----------|
| **A 禁用词** | AI 高频词替换 | 查 banned-words.md，逐词替换 |
| **B 句式** | AI 惯用句式重写 | 打散排比/对称/空洞抒情 |
| **C 心理外化** | 情绪用动作展示 | 情绪词 → 身体状态 |
| **D 节奏** | 打断排比，长短交错 | 连续 3+ 排比 → 保留 1-2 个 |
| **E 对话** | 去 AI 腔，加口语化 | 删解释性对话，加口语词 |
| **F 结尾** | 去升华，用动作收尾 | 删哲理收尾，改用细节定格 |

## 系统性去AI三遍法

- **Pass 1：去泛化** — 抽象词替换为具体细节
- **Pass 2：去书面化** — 书面腔替换为口语/动作
- **Pass 3：回自然感** — 注入停顿、犹豫、矛盾和口语感

## 执行
1. 读取目标章节正文
2. 调用 Agent(writer) 执行指定级别的去AI味
3. 输出修改后的正文 + 变更说明
4. 可选：自动执行禁令扫描验证

## 禁止
- 去AI味过程中不得新增原文没有的情节、设定、关系
- 只能改写表达方式，不能改变故事内容
