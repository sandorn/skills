---
name: novelize
description: |
  网文创作全流程 Skill — 覆盖从初始化、扫榜拆文、大纲规划、正文写作、
  去AI味、审查质检到项目体检的完整 pipeline。
  支持长篇/短篇自动判定，统一命令入口。
version: 2.0.0
---

# Novelize — 网文写作工具集

> 统一引擎：从选题到大结局，一个 skill 走完全流程。

---

## 一、命令路由表

| 命令 | 别名 | 说明 |
|------|------|------|
| `/novelize-init` | `/初始化` | 项目初始化（长/短篇自动判定） |
| `/novelize-scan` | `/扫榜` | 扫榜拆文（对标书结构化提取） |
| `/novelize-analyze` | `/拆文` | 深度拆文分析（长/短篇自动判定） |
| `/novelize-plan` | `/大纲` | 大纲规划（卷纲→章纲→细纲） |
| `/novelize-write {N}` | `/写作` | 正文写作（长/短篇自动判定，支持流水线） |
| `/novelize-review` | `/审查` | 多维度审查（4 模式：full/lean/solo/quick） |
| `/novelize-deslop` | `/去AI味` | 6 Gate 去 AI 味 |
| `/novelize-doctor` | `/体检` | 项目诊断（文件完整性/占位符/备份） |

### 流水线模式（内嵌）

`/novelize-write` 支持一键链式调度，替代独立的 pipeline skill：

```bash
/novelize-write --pipeline "简介"    # 全流程：选题→设定→大纲→ch01
/novelize-write --continue           # 续写模式
/novelize-write --stage review       # 跳到审查期
/novelize-write --status             # 查询项目状态
```

---

## 二、Agent 体系（6 个）

| Agent | 模型 | 职责 |
|-------|------|------|
| `architect` | opus | 题材/世界观/大纲/钩子/反转/情绪弧线 |
| `writer` | sonnet | 正文写作/情绪执行/去AI味/格式合规 |
| `designer` | sonnet | 角色设计/语言风格档案/对话创作 |
| `explorer` | haiku | 只读查询（角色/伏笔/设定/进度） |
| `researcher` | sonnet | 外部资料研究（CDP + WebSearch） |
| `checker` | haiku | 一致性检查（S1-S4 分级） |

### Agent 调用关系

```
/novelize-write
  ├── Phase 1-3: Agent(architect) → 选题/设定/大纲
  ├── Phase 4:   Agent(explorer) → context_load
  │              Agent(writer)    → 正文写作
  │              Agent(designer)  → 对话创作（按需）
  │              Agent(researcher) → 资料研究（按需）
  └── Phase 5:   Agent(checker)   → 一致性检查
                 Agent(writer)    → 去AI味 / 格式合规

/novelize-review
  ├── full 模式: Agent(architect) + Agent(designer) + Agent(writer) + Agent(checker)
  ├── lean 模式: Agent(architect) + Agent(checker)
  └── solo 模式: 主 session 单线程审查

/novelize-analyze
  └── Agent(extractor) × N → 并行提取 → 主 session 聚合
```

---

## 三、质检流水线

```
写作完成
    │
    ▼
硬性禁令扫描（破折号/AI句式/元叙事/字数/模板）
    │ 合格
    ▼
/novelize-review（对抗审查 或 solo）
    │
    ▼
/novelize-deslop（去 AI 味，6 Gate）
    │
    ▼
段落修复（一句一段，句号断段）
    │
    ▼
终检（全禁令清零确认）
```

---

## 四、硬性禁令

- 🚫 破折号 `——`（`sed -i 's/——/，/g' 正文/ch*.md`）
- 🚫 `不是……而是……` / `不是……，是……` 句式
- 🚫 元叙事标签（`【情绪】` `【本章完】`）
- 🚫 AI 高频词（忽然 / 深吸一口气 / 眼中闪过 / 他知道）
- 🚫 模板复制（搜索高频起手句）

段落：按句号断段，每段 15-40 汉字。每章 ≥ 2000 汉字。

---

## 五、审查功能详解

### /novelize-review — 多视角对抗审查

| 模式 | 说明 |
|------|------|
| `full` | 4 Agent 并行：结构 + 角色 + 文字 + 事实 |
| `lean` | 2 Agent：architect + checker |
| `solo` | 主 session 单线程基础审查 |
| `quick` | 仅禁令扫描 + 格式检查（bin/ban-check.sh + bin/format-check.sh） |

| 审查维度 | 检查内容 |
|----------|----------|
| 结构 | 主题对齐、大纲完整、钩子/反转质量、范围控制 |
| 角色 | 语言风格一致性、对话质量、人物弧线、关系推进 |
| 文字 | AI 味检测、禁用词、格式合规、节奏均匀度 |
| 事实 | 角色属性一致性、世界规则违反、伏笔状态、时间线自洽 |
| 连续性 | 角色/位置/关系/时间连贯性 |
| 字数 | 是否在允许区间 |

### /novelize-deslop — 6 Gate 去 AI 味

| Gate | 检查内容 | 示例 |
|------|----------|------|
| **A 禁用词** | AI 高频词替换 | `眼中闪过一丝` → `他垂下眼` |
| **B 句式** | AI 惯用句式重写 | `不是…而是…` → 直述句 |
| **C 心理外化** | 情绪用动作展示 | `他很紧张` → `他的手在抖` |
| **D 节奏** | 打断排比，长短交错 | 连续 3+ 排比 → 保留 1-2 个 |
| **E 对话** | 去 AI 腔，加口语化 | 删解释性对话，加 `嗯` `行吧` |
| **F 结尾** | 去升华，用动作收尾 | 删 `他知道…` `这一刻…` |

---

## 六、长/短篇自动判定逻辑

```
项目目录中存在 追踪/ → 长篇模式
项目目录中存在 正文.md（单文件） → 短篇模式
```

各命令根据判定结果自动选择对应的处理策略。

---

## 七、参考文件路径解析（统一规则）

所有 Agent 读取参考文件时，按以下优先级解析：

1. 项目根目录 `.claude/skills/story-setup/references/agent-references/`
2. 项目根目录 `skills/story-setup/references/agent-references/`
3. Glob/Grep 搜索 `*/story-setup/references/agent-references/`

各 Agent 不再各自硬编码此规则。

---

## 八、项目文件结构

```
{书名}/
├── 设定/
│   ├── 世界观/          # 设定详情
│   ├── 角色/            # 角色文件（每个角色一个 .md）
│   ├── 势力/            # 势力/组织文件
│   ├── 关系.md          # 角色关系映射
│   └── 题材定位.md      # 题材定位
├── 大纲/
│   ├── 大纲.md          # 全书卷级结构
│   ├── 卷纲_第X卷.md    # 每卷规划
│   └── 细纲_第XXX章.md  # 每章蓝图
├── 正文/
│   └── 第XXX章_*.md     # 正文章节
├── 追踪/
│   ├── 伏笔.md          # 伏笔状态表
│   ├── 时间线.md        # 故事时间线
│   └── 上下文.md        # 写作进度摘要
└── 参考资料/
    └── {topic}.md       # 研究资料
```

---

## 九、快速硬性禁令扫描

```bash
# 破折号
grep -c '——' 正文/ch*.md
# AI句式
grep -c '不是.*而是' 正文/ch*.md
# 字数
python3 -c "import re,os;[print(f, len(re.findall(r'[\u4e00-\u9fff]',open(f'正文/{f}').read()))) for f in sorted(os.listdir('正文')) if f.endswith('.md')]"
# 模板残留
grep -l '高频起手句' 正文/ch*.md
```
