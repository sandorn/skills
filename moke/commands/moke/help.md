---
name: moke:help
description: Show MoKe commands and usage / 显示 MoKe 命令和用法
---

<objective>
Display all available MoKe commands with descriptions.
</objective>

<process>
List all /moke:* commands with:
- Command name
- Description
- Usage examples

## 命令列表

### 核心命令
- `/moke:help` - 显示帮助信息
- `/moke:settings` - 配置执行模式（yolo/interactive）
- `/moke:set-profile` - 设置模型配置（quality/balanced/budget）
- `/moke:create-book` - 创建新书籍项目

### 题材命令
- `/moke:genre-list` - 列出所有可用题材
- `/moke:genre-show` - 显示特定题材详细配置
- `/moke:genre-create` - 创建自定义题材

### 创作命令
- `/moke:plan-chapter` - 规划章节意图
- `/moke:compose-chapter` - 编排上下文
- `/moke:draft` - 写章节草稿
- `/moke:audit` - 审计章节质量
- `/moke:revise` - 根据审计修订章节
- `/moke:write-next` - 完整管线写下一章
- `/moke:write-batch` - 批量连续写多章（避免上下文消耗）

### Agents（9个）
1. **Planner** - 规划师：生成章节意图
2. **Composer** - 编排师：选择上下文
3. **Architect** - 建筑师：规划章节结构
4. **Writer** - 写手：生成正文
5. **Observer** - 观察者：提取9类事实
6. **Reflector** - 反射器：更新状态文件
7. **Normalizer** - 归一化器：调整字数
8. **Auditor** - 审计员：33维度质量检查
9. **Reviser** - 修订者：修复问题

### 配置说明

**执行模式**：
- `yolo` - 自动执行所有步骤，无需确认
- `interactive` - 每个步骤都需要确认

**切换模式**：
```bash
/moke:settings --mode yolo
```

### 模型 Profile

| Profile | 说明 |
|---------|------|
| `quality` | Opus + Opus + Sonnet + Sonnet（最高质量） |
| `balanced` | Opus + Sonnet + Sonnet + Sonnet（平衡） |
| `budget` | Sonnet + Sonnet + Haiku + Haiku（经济） |
| `inherit` | 使用 Claude Code 默认模型 |

```bash
/moke:set-profile budget
```
</process>
