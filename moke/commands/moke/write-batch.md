---
name: moke:write-batch
description: Write multiple chapters in batch / 批量连续写多章
---

<objective>
Write multiple chapters using the full pipeline, delegating to a specialized agent to avoid consuming main conversation context.
</objective>

<process>
## 批量写作流程

### 功能说明

使用专门的 agent 在后台连续执行多个章节的完整写作流程，避免消耗主对话的上下文。

### 使用方式

```bash
# 连续写 3 章
/moke:write-batch --count 3

# 写到指定章节
/moke:write-batch --to-chapter 10

# 无限制连续写（直到手动停止）
/moke:write-batch --continuous

# 带作者意图指导
/moke:write-batch --count 5 --context "主角开始修炼之旅"
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--count` | 写作章节数量 | 1 |
| `--to-chapter` | 写到第几章 | - |
| `--continuous` | 无限制连续写 | false |
| `--context` | 作者意图指导 | - |

### 执行流程

#### 阶段 1：初始化检查

1. **环境验证**
   - 确认书籍项目存在
   - 检查 7 个真相文件是否完整：
     * `story/current_state.md` - 当前状态卡
     * `story/particle_ledger.md` - 资源账本（如有数值系统）
     * `story/pending_hooks.md` - 伏笔池
     * `story/chapter_summaries.md` - 章节摘要
     * `story/subplot_board.md` - 支线进度板
     * `story/emotional_arcs.md` - 角色情感弧线
     * `story/character_matrix.md` - 角色交互矩阵

2. **配置读取**
   - 读取 `.moke/config.json`
   - 获取模式设置（mode: yolo/interactive）
   - 获取模型配置（modelProfile）

3. **进度初始化**
   - 获取当前章节号
   - 创建或读取 `runtime/batch-progress.md`

#### 阶段 2：批量执行循环

对每个章节执行完整的 9 步管线：

**步骤 1/9：规划章节 (moke:planner)**
- 读取作者意图 + 当前焦点 + 记忆检索结果
- 产出本章意图（must-keep / must-avoid）
- 输出：
  - `runtime/chapter-XXXX.intent.md` - 章节意图声明
  - `runtime/chapter-plan.md` - 详细规划

**步骤 2/9：编排上下文 (moke:composer)**
- 从全量真相文件中按相关性选择上下文
- 应用 25 条通用创作规则
- 编译题材专属规则 + 书级规则
- 生成规则优先级栈
- 输出：
  - `runtime/chapter-XXXX.context.json` - 精选上下文数据
  - `runtime/chapter-XXXX.rule-stack.yaml` - 规则优先级层
  - `runtime/context.md` - 人类可读上下文

**步骤 3/9：规划结构 (moke:architect)**
- 规划章节结构：大纲、场景节拍、节奏控制
- 设计场景转换和节奏变化
- 输出：
  - `runtime/chapter-XXXX.trace.json` - 结构规划轨迹
  - `runtime/structure.md` - 人类可读结构

**步骤 4/9：写作正文 (moke:writer)**
- 基于编排后的精简上下文生成正文
- 读取所有 7 个真相文件
- 智能过滤：识别相关角色、支线、位置
- 字数治理 + 对话引导
- 输出：`chapters/第N章-<标题>.md`

**步骤 5/9：提取事实 (moke:observer)**
- 从正文中提取 9 类事实：
  1. 角色行为 - 谁做了什么，对谁，为什么
  2. 位置变化 - 谁去了哪里，从哪里来
  3. 资源变化 - 获得、失去、消耗了什么
  4. 关系变化 - 新相遇、信任转变、结盟、背叛
  5. 情绪变化 - 角色情绪从 X 到 Y
  6. 信息流动 - 谁知道了什么新信息
  7. 剧情线索 - 新埋、推进、回收伏笔
  8. 时间推进 - 过了多长时间
  9. 身体状态 - 受伤、恢复、疲劳、战力变化
- 输出：`runtime/observations.md`

**步骤 6/9：更新状态 (moke:reflector)**
- 将观察结果合并到 7 个真相文件
- 增量更新机制：
  - 新增伏笔 → 添加到 pending_hooks.md
  - 推进伏笔 → 更新 pending_hooks.md 状态
  - 回收伏笔 → 标记已回收，记录解答章节
- 时间戳标注：所有变更标注章节号
- 输出：`runtime/state-changes.md`

**步骤 7/9：字数归一 (moke:normalizer)**
- 单 pass 压缩/扩展
- 将章节字数拉入允许区间（2800-3200 字）
- 目标字数：3000 字
- 输出：更新章节文件

**步骤 8/9：审计质量 (moke:audit)**
- 对照 7 个真相文件验证草稿
- 33 维度检查
- 输出：`runtime/audit-report.md`

**步骤 9/9：修订问题 (moke:revise)**
- 修复审计发现的问题
- 关键问题自动修复
- 其他标记给人工审核
- 循环：如果审计不通过，重复"修订 → 再审计"直到关键问题清零

#### 阶段 3：后写校验

每章完成后执行后写校验：

**校验 1：运行时产物完整性**
- 确认 4 个运行时产物文件已生成：
  - `runtime/chapter-XXXX.intent.md` ✓
  - `runtime/chapter-XXXX.context.json` ✓
  - `runtime/chapter-XXXX.rule-stack.yaml` ✓
  - `runtime/chapter-XXXX.trace.json` ✓

**校验 2：规则栈验证**
- 确认规则优先级无冲突
- 确认书级规则正确覆盖通用规则
- 确认题材规则已应用
- 确认 25 条通用规则全部应用

**校验 3：上下文一致性**
- 确认 context.json 包含必要的角色、位置、支线信息
- 确认与 intent.md 的对齐

**校验 4：轨迹完整性**
- 确认 trace.json 记录了关键决策点
- 确认可追溯性

### 运行时产物详解

#### 1. 章节意图文件（chapter-XXXX.intent.md）

章节意图的机器可读声明，用于控制写作方向。

```yaml
chapter: 5
target_word_count: 3000
core_objective: "主角在试炼中发现隐藏力量，引发势力关注"
must_keep:
  - "主角在试炼中突破"
  - "至少两个势力注意到主角"
  - "埋下主角身世的伏笔"
must_avoid:
  - "直接揭露主角身世"
  - "主角过于轻松获胜"
conflicts:
  primary: "主角 vs 试炼难度"
  secondary: "各方势力对主角的争夺"
foreshadowing:
  plant:
    - "主角的特殊体质"
    - "神秘组织的关注"
  advance:
    - "试炼的真实目的"
  resolve: []
```

#### 2. 上下文数据文件（chapter-XXXX.context.json）

精选的上下文数据，用于精确控制写作所需的背景信息。

```json
{
  "chapter": 5,
  "selected_context": {
    "characters": ["林风", "苏梦", "长老"],
    "locations": ["试炼场", "秘境"],
    "subplots": ["主线-修炼", "支线-身世谜团"],
    "hooks": ["hook-001", "hook-003", "hook-007"]
  },
  "current_state": {
    "character_positions": {
      "林风": "试炼场",
      "苏梦": "观礼台"
    },
    "relationships": {
      "林风-苏梦": "暗中关注",
      "林风-长老": "试探"
    },
    "known_info": {
      "林风": ["自身实力", "试炼规则"],
      "苏梦": ["林风的表现", "部分身世线索"]
    }
  },
  "world_rules": {
    "magic_system": {
      "修炼等级": ["炼气", "筑基", "金丹"],
      "元素类型": ["金", "木", "水", "火", "土"]
    },
    "geography": {
      "试炼场位置": "宗门北部",
      "秘境入口": "试炼场深处"
    }
  }
}
```

#### 3. 规则优先级文件（chapter-XXXX.rule-stack.yaml）

规则优先级层，定义当前章节应用的规则及其优先级。

```yaml
rule_stack:
  # 第一层：通用创作规则（25条）
  - layer: "common"
    priority: 1
    source: "rules/common-25-rules.md"
    rules:
      - id: "R001"
        name: "展示而非讲述"
        weight: 1.0
        active: true
      - id: "R002"
        name: "场景冲突密度"
        weight: 0.9
        active: true
      # ... 共25条

  # 第二层：题材专属规则
  - layer: "genre"
    priority: 2
    source: "rules/genre-xuanhuan.md"
    rules:
      - id: "G001"
        name: "修炼体系清晰"
        weight: 1.0
        active: true
      - id: "G002"
        name: "力量层次分明"
        weight: 0.9
        active: true

  # 第三层：书级规则覆盖
  - layer: "book"
    priority: 3
    source: "story/book_rules.md"
    overrides:
      - "R001"  # 书级规则覆盖通用规则R001
    rules:
      - id: "B001"
        name: "本系列特殊设定"
        weight: 1.0
        active: true
```

#### 4. 输入轨迹文件（chapter-XXXX.trace.json）

记录本章的关键决策点和推理过程，用于可追溯性。

```json
{
  "chapter": 5,
  "planner_decisions": [
    {
      "step": "intent_formulation",
      "decision": "将冲突设置为双重结构",
      "reasoning": "既推进修炼线，又引出身世线"
    }
  ],
  "composer_decisions": [
    {
      "step": "context_selection",
      "decision": "选择3个角色、2个位置",
      "reasoning": "基于场景需要和冲突设计"
    },
    {
      "step": "rule_application",
      "decision": "应用25条通用规则",
      "reasoning": "确保写作质量"
    }
  ],
  "architect_decisions": [
    {
      "step": "scene_division",
      "decision": "将章节分为3个场景",
      "reasoning": "开场-发展-高潮三段式"
    },
    {
      "step": "pacing",
      "decision": "采用慢-快-慢节奏",
      "reasoning": "开场铺垫，冲突加速，结尾沉淀"
    }
  ],
  "writer_decisions": [
    {
      "step": "opening",
      "decision": "从主角进入试炼场开始",
      "reasoning": "直接进入冲突，减少铺垫"
    }
  ]
}
```

### 运行时产物的作用

1. **可追溯性**：记录每章的决策过程，便于回溯和调试
2. **质量控制**：通过规则栈确保写作质量
3. **上下文精确**：通过精选上下文避免信息过载
4. **意图一致**：通过意图文件确保写作方向不偏离
5. **批量执行**：支持批量写作时保持每章独立性和质量


#### 阶段 3：进度跟踪

每章完成后更新进度文件 `runtime/batch-progress.md`：

```markdown
# 批量写作进度

- 开始时间: 2026-03-27 00:00:00
- 目标章节: 5 章
- 当前章节: 3
- 完成章节:
  - [✓] 第1章 - 废材觉醒 (3,124字, 2m30s)
    - 审计: 通过 ✓
    - 状态更新: 完成 ✓
  - [✓] 第2章 - 奇遇 (2,987字, 2m15s)
    - 审计: 通过 ✓
    - 状态更新: 完成 ✓
  - [→] 第3章 - 冲突 (进行中)
```

#### 阶段 4：中断条件

遇到以下情况停止执行：

1. **正常完成**
   - 达到目标章节数
   - 写到指定章节号

2. **异常中断**
   - 审计连续失败 3 次
   - 某个步骤连续重试失败
   - 发生严重错误（如文件读写失败）

3. **手动中断**
   - 用户手动停止

### 配置影响

- `mode: yolo` - 全自动执行，无需确认
- `mode: interactive` - 每章开始前确认

### 创作规则体系

#### 25 条通用创作规则

每章写作时自动应用 25 条通用创作规则（来自 `rules/common-25-rules.md`）：

1. **R001 - 展示而非讲述**：通过行动和对话展现角色特质，而非直接陈述
2. **R002 - 场景冲突密度**：每个场景必须包含冲突或张力
3. **R003 - 对话功能性**：每句对话推动剧情或揭示角色
4. **R004 - 节奏变化**：在快慢节奏间切换，保持阅读兴趣
5. **R005 - 感官细节**：运用五感描写，增强沉浸感
6. **R006 - 角色动机清晰**：每个行动都有明确的动机
7. **R007 - 悬念钩子**：章节结尾设置悬念或转折
8. **R008 - 伏笔布局**：自然埋设伏笔，为后续铺垫
9. **R009 - 情感弧线**：章节内角色情感有变化轨迹
10. **R010 - 信息控制**：精准控制读者和角色知道的信息
11. **R011 - 场景转换**：场景间转换流畅自然
12. **R012 - 结构完整性**：章节结构完整，有开场、发展、高潮、结尾
13. **R013 - 文字流畅性**：文字通顺流畅，无语法错误
14. **R014 - 角色声音独特**：不同角色有独特的说话方式和行为模式
15. **R015 - 节奏递进**：紧张程度递进，避免平铺直叙
16. **R016 - 细节一致性**：细节与之前章节保持一致
17. **R017 - 伏笔回收**：适时回收之前埋设的伏笔
18. **R018 - 情感真实性**：角色情感反应真实可信
19. **R019 - 世界观规则**：遵守已建立的世界观规则
20. **R020 - 时间感知**：清晰传达时间流逝
21. **R021 - 空间感知**：清晰描述空间关系和位置变化
22. **R022 - 主题一致性**：与本书主题保持一致
23. **R023 - 类型特征**：符合所属类型的特征（玄幻/都市/科幻等）
24. **R024 - 读者期待**：满足类型读者的核心期待
25. **R025 - 创新突破**：在满足类型期待的基础上适度创新

#### 规则优先级机制

规则按优先级分层应用：

1. **第一层**：通用创作规则（25条，Priority 1）
2. **第二层**：题材专属规则（Priority 2）
3. **第三层**：书级规则覆盖（Priority 3，来自 `story/book_rules.md`）

#### 规则冲突解决

当规则冲突时，高优先级覆盖低优先级。书级规则可覆盖通用规则和题材规则。

#### 规则应用验证

管线会自动验证：
- 25 条通用规则是否全部应用
- 规则权重是否合法（0-1）
- 规则覆盖是否正确
- 规则栈是否有冲突


### 输出示例

```bash
[批量写作] 🚀 开始批量写作，目标章节: 5
[批量写作] 📋 当前状态检查... ✓
[批量写作] 📖 真相文件检查... ✓ (7/7)

[批量写作] 开始写第 1 章...
[批量写作]   [1/9] 规划章节... ✓ (intent.md)
[批量写作]   [2/9] 编排上下文... ✓ (context.json + rule-stack.yaml, 25条规则)
[批量写作]   [3/9] 规划结构... ✓ (trace.json)
[批量写作]   [4/9] 写作正文... ✓ (3,124字)
[批量写作]   [5/9] 提取事实... ✓ (9类事实)
[批量写作]   [6/9] 更新状态... ✓ (7个文件)
[批量写作]   [7/9] 字数归一... ✓ (2,987字)
[批量写作]   [8/9] 审计质量... ✓ (33维度, 0问题)
[批量写作]   [9/9] 后写校验... ✓ (运行时产物完整, 规则栈验证通过)
[批量写作] 第 1 章完成 ✓ (用时: 2m30s)

[批量写作] 开始写第 2 章...
[批量写作]   [1/9] 规划章节... ✓
...
[批量写作] 第 2 章完成 ✓ (用时: 2m15s)

...
[批量写作] 全部完成！共完成 5 章
[批量写作] 总字数: 15,620 字
[批量写作] 总用时: 12m 45s
[批量写作] 平均速度: 2m 33s/章
```

### 错误处理和重试机制

#### 重试策略

1. **步骤级重试**
   - 单个步骤失败后，自动重试 1 次
   - 如果重试仍失败，记录错误并继续下一章
   - 某些关键步骤（如 Writer）失败则停止整章

2. **章节级重试**
   - 审计不通过时，自动进入"修订 → 再审计"循环
   - 最多循环 3 次
   - 3 次后仍不通过，标记为需要人工介入

3. **批量级中断**
   - 连续 3 章失败后停止批量写作
   - 保存当前进度
   - 生成详细错误报告

#### 错误报告

错误时保存到 `runtime/batch-errors.md`：

```markdown
# 批量写作错误报告

## 第3章 - 冲突

### 错误信息
- 步骤: moke:writer
- 错误: API 请求超时
- 时间: 2026-03-27 00:10:25

### 重试记录
- 第1次重试: 失败 (API 请求超时)
- 第2次重试: 失败 (API 请求超时)

### 建议
- 检查网络连接
- 减少并发请求
- 考虑更换模型配置
```

### 注意事项

- 确保有足够的 API 配额
- 建议先用 yolo 模式测试单章
- 长时间运行请监控进度
</process>
