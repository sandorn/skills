---
name: moke:set-profile
description: Set model profile for agents / 设置代理模型配置
---

<objective>
Configure which Claude model each MoKe agent uses for optimal quality and cost balance.
</objective>

<process>
## 模型 Profile

控制各代理使用哪种 Claude 模型，在质量和 token 成本之间平衡。

### Profile 选项

| Profile | Planner | Writer | Auditor | Reviser | 说明 |
|---------|---------|--------|---------|---------|------|
| `quality` | Opus | Opus | Sonnet | Sonnet | 最高质量，成本较高 |
| `balanced`（默认） | Opus | Sonnet | Sonnet | Sonnet | 质量与成本平衡 |
| `budget` | Sonnet | Sonnet | Haiku | Haiku | 经济实惠，快速完成 |
| `inherit` | Inherit | Inherit | Inherit | Inherit | 使用 Claude Code 默认模型 |

### 切换方式

```bash
# 切换到经济模式
/moke:set-profile budget

# 切换到质量模式
/moke:set-profile quality

# 切换到平衡模式（默认）
/moke:set-profile balanced

# 使用继承模式
/moke:set-profile inherit
```

### 配置保存

配置保存在 `books/<书名>/.moke/config.json` 中的 `modelProfile` 字段。

### 自定义配置

如需为特定 agent 配置不同模型，使用：
```bash
/moke:settings
```

然后手动编辑配置文件的 `agentModels` 部分。
</process>
