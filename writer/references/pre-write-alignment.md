# 预写总线对齐检查（Pre-Write Alignment Check）

> 批量写章前，逐层验证总纲 → 卷纲 → 细纲 → 追踪 的传递一致性，确保总线不偏离、前后能衔接。

---

## 触发时机

任何批量写章前（主会话直接写 / 子代理委派写），**必须先执行此检查**。单章日更可酌情跳过，但新卷首章或新批首章必做。

---

## 执行流程（5层递进）

### Layer 1：加载总纲（Master Outline）

读取 `outline/master_outline.md` 或 `大纲/总纲.md`，确认：

| 检查项 | 目的 |
|--------|------|
| 当前写的是第几卷？ | 定位到对应卷范围 |
| 本卷在全书弧线的位置？ | 暗线推进进度 |
| 创意约束是否仍适用？ | 如「智谋取胜」「转化而非消灭」——若当前区间不再适用，应主动识别并记录 |
| 是否有未回收的总纲级伏笔到期？ | 防止主线伏笔过期 |

**预期**：明确当前卷名 + 全卷目标。

### Layer 2：加载卷纲（Volume Outline / 节拍表）

读取 `outline/volume_outline.md` 或 `大纲/卷纲_vX.md`，确认：

| 检查项 | 目的 |
|--------|------|
| 当前处在节拍表的哪个区间？ | 启/承/转/合 哪一段 |
| 本批章节的核心事件是什么？ | 确认写作目标 |
| 情绪弧线走向？ | 爽→紧张→反转→释放 当前落在哪 |
| 时间线范围？ | 章→章时间跨度是否合理 |

**预期**：当前批次的起止章号 + 对应节拍阶段。

### Layer 3：加载细纲（Chapter Outline / 章纲）

读取批次的每章章纲（`outline/chapter_outline/ch_{NNN}.md` 或 `大纲/章纲/ch_{NNN}.md`）：

| 检查项 | 目的 |
|--------|------|
| 章纲中的核心事件与卷纲节拍表一致？ | 不跑偏 |
| 章纲数量 = 计划写章数？ | 无缺漏 |
| 每章的情绪变化不与相邻章完全相同？ | 不单调 |
| 章首钩子类型 + 章末钩子类型齐全？ | 钩子不空 |

**预期**：章纲完整，与卷纲对齐，无缺失章节。

### Layer 4：加载追踪（Tracking Files）

读取以下追踪文件，构建「当前世界快照」：

| 文件 | 检查内容 |
|------|---------|
| `tracking/current_state.md` / `追踪/角色状态.md` | 主角等级/权限/金币/装备/位置、各配角状态 |
| `tracking/hooks.md` / `追踪/伏笔.md` | 待回收伏笔列表、已回收状态 |
| `tracking/chapter_summaries.md` / `追踪/章节摘要.md` | 上一章摘要（确认停靠点） |
| `tracking/resource_ledger.md` / `追踪/资源账本.md` | 金币余额/资产总额（如有） |

**交叉校验**：

| 校验对 | 检查什么 | 不通过处理 |
|--------|---------|-----------|
| 追跟踪状态 vs 细纲起始 | 等级/权限/位置是否匹配细纲起始条件 | 修正细纲或追踪 |
| 追踪伏笔 vs 细纲伏笔操作 | 细纲中要回收的伏笔在追踪中是否标记为「已埋」 | 补充伏笔登记 |
| 追踪摘要 vs 细纲时间线 | 上一章结束时间点与下一章起始时间点连续 | 修正细纲时间 |

### Layer 5：加载文风预设（Style Preset）

若项目有 `writing_rules.md` 或显式声明的文风偏好（如"番茄爆款风"），加载对应的文风预设参数：

| 检查项 | 来源 | 目的 |
|--------|------|------|
| 当前文风预设 | `writing_rules.md` 或用户声明 | 确定目标文风（默认 `fanqie-quick-anti`） |
| 禁令/句式参数 | `references/style-sop.md` | 写章时同步应用文风约束 |
| 字数要求 | 预设中的 `sentence_params` | 每章目标字数范围 |

**若项目级 `writing_rules.md` 包含 style_override 块，以项目覆盖为准。**

> 文风预设的完整定义见 `references/style-sop.md`，文风转换流程见 `references/style-transfer.md`。

### 总线一致性声明

5 层全部加载并校验后，输出一条**总线一致性声明**：

```
═══════════════════════════════════════
总线对齐检查通过
═══════════════════════════════════════

当前卷：第{N}卷 — {卷名}
节拍阶段：{启/承/转/合}
本批范围：ch{START} → ch{END}
文风预设：{preset_name}

总纲对齐：✅ / ❌ {问题简述}
卷纲对齐：✅ / ❌ {问题简述}
细纲完整：✅ / ❌ {问题简述}
追踪连续：✅ / ❌ {问题简述}
文风加载：✅ / ❌ {问题简述}

核心事件：{一句话描述}
主角起点：{等级/权限/位置}
章末锚点：{上一章结束场景}

潜在风险：
- {如：时间跳跃需标注 / 新角色引入需登场 / 伏笔到期}
═══════════════════════════════════════
```

### 发现不一致时的处理

| 场景 | 处理方式 |
|------|---------|
| 细纲与卷纲节拍表不一致 | **以节拍表为准重写细纲**。节拍表是全书节奏的权威来源 |
| 追踪状态与细纲出入 | 若细纲更准确 → 更新追踪；若追踪更准确 → 更新细纲 |
| 细纲缺失某章 | 先补细纲再动笔，禁止无章纲写章 |
| 追踪文件完全缺失 | 从最新一章提取状态，重建追踪（至少写 `current_state.md` + 章末摘要） |
| 总纲与卷纲冲突 | 阻断，标记 BLOCKER，等待用户裁决 |

---

## 与 SKILL.md 状态感知的关系

状态感知（Skill 启动时的自动检测）提供**触发时点**：检测到用户意图为写作时，自动执行 Layer 4。而本文件是**正式流程**：在批量写章前，显式执行 4 层完整检查。状态感知不替代本检查。

## 与 write.md 执行前预检的关系

write.md 的「执行前预检」侧重于**检查项目结构完整性**（writer.json存在/大纲目录存在）。本文件是**内容对齐检查**（大纲vs追踪vs正文的状态一致）。两者互补——先跑预写对齐，再跑 write.md 预检，再写章。

---

## 实用命令

### 读大纲（获取当前卷目标）
```bash
cat "outline/master_outline.md"
cat "outline/volume_outline.md"
```

### 读追踪（获取当前世界快照）
```bash
cat "tracking/current_state.md"
cat "tracking/hooks.md"
cat "tracking/chapter_summaries.md"
```

### 读细纲（获取批次的章纲）
```bash
cat "outline/chapter_outline/ch_{NNN}.md"
```

### 5维状态校验（内联脚本）
```python
import re, os

ch_dir = '正文'
state = {
    'level': None,
    'perm': None,
    'gold': None,
    'location': None,
    'prev_ch_event': None
}

# 读最近2章
recent = sorted([f for f in os.listdir(ch_dir) if f.endswith('.md')])[-2:]
for f in recent:
    text = open(os.path.join(ch_dir, f), encoding='utf-8').read()
    levels = re.findall(r'(\d+)级', text)
    if levels: state['level'] = max(int(x) for x in levels)
    perms = re.findall(r'[Ll](\d)', text)
    if perms: state['perm'] = max(perms)
    golds = re.findall(r'(\d+)\s*万?(?:金币|金)', text)
    if golds: state['gold'] = max(int(x) for x in golds)

print(f"最新状态：等级={state['level']} 权限=L{state['perm']} 金币={state['gold']}")
```

---

> **下一步**：[写章](write.md) --batch N（对齐通过后批量写章）
