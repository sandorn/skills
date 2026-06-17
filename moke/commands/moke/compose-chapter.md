---
name: moke:compose-chapter
description: Compose chapter context and rules / 编排章节上下文
---

<objective>
Select relevant context from truth files and compile rule stack for chapter writing.
</objective>

<process>
## 编排上下文

### 任务描述

从全量真相文件中按相关性选择上下文，编译规则栈和运行时产物。

### 上下文来源

1. **current_state.md** - 当前状态
   - 角色位置
   - 关系状态
   - 已知信息
   - 当前冲突

2. **pending_hooks.md** - 伏笔池
   - 活跃伏笔
   - 待回收伏笔
   - 优先级排序

3. **summaries.md** - 章节摘要
   - 相关章节摘要
   - 人物关系
   - 关键事件回顾

4. **story_bible.md** - 世界观设定
   - 力量体系
   - 地理环境
   - 势力关系

5. **book_rules.md** - 本书规则
   - 写作禁忌
   - 特殊设定
   - 数值系统

### 输出格式

```markdown
# 写作上下文

## 当前状态
[提取的相关状态]

## 世界观规则
[相关设定]

## 伏笔参考
[需要考虑的伏笔]

## 风格指南
[风格要求]

## 禁忌清单
[必须避免的内容]

## 上下文摘要
[场景前情提要]
```

### 相关性排序

- 高度相关：必须包含
- 中度相关：根据章节意图决定
- 低度相关：可选择性包含

### 规则栈

按优先级组织的写作规则：
1. 题材强制规则（来自 genre profile）
2. 本书特定规则（来自 book_rules）
3. 本章特定约束（来自 chapter intent）

### 输入

- 章节规划（来自 Planner）
- 当前状态文件
- 伏笔池状态

### 输出

- 保存到 `runtime/context.md`
- 为 Writer 提供精简但完整的上下文
</process>
