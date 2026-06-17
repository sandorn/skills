---
name: moke:settings
description: Configure MoKe settings / 配置 MoKe 设置
---

<objective>
Manage MoKe configuration including execution mode and approval behavior.
</objective>

<process>
## 配置选项

### 核心设置

| 设置 | 选项 | 默认值 | 作用 |
|------|------|--------|------|
| `mode` | `yolo`, `interactive` | `interactive` | 自动批准，还是每一步确认 |
| `granularity` | `coarse`, `standard`, `fine` | `standard` | 章节创作粒度 |
| `modelProfile` | `quality`, `balanced`, `budget`, `inherit` | `balanced` | 模型配置 |

### 模式说明

**yolo 模式**：
- 自动执行所有步骤，无需确认
- 规划 → 编排 → 写作 → 审计 → 修订 全自动
- 适合快速创作

**interactive 模式**：
- 每个步骤都需要确认
- 可以在每一步调整或中止
- 适合精细控制

### 模型 Profile

| Profile | Planner | Writer | Auditor | Reviser | 说明 |
|---------|---------|--------|---------|---------|------|
| `quality` | Opus | Opus | Sonnet | Sonnet | 最高质量 |
| `balanced`（默认） | Opus | Sonnet | Sonnet | Sonnet | 平衡 |
| `budget` | Sonnet | Sonnet | Haiku | Haiku | 经济 |
| `inherit` | Inherit | Inherit | Inherit | Inherit | 继承默认 |

切换 profile 使用：`/moke:set-profile <profile>`

### 配置文件

配置保存在 `books/<书名>/.moke/config.json`

### 使用方法

1. 读取当前配置
2. 询问用户要修改的设置
3. 更新配置文件
4. 输出新配置

### 示例

```
/moke:settings
→ 显示当前配置

/moke:settings --mode yolo
→ 切换到自动模式

/moke:settings --granularity fine
→ 切换到精细粒度
</process>
