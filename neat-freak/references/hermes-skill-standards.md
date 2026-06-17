# Hermes 技能库维护标准

> 基于 2026-06-17 审查 ~/.agents/skills + ~/.hermes/skills 的实践经验。

## 硬性标准

### description ≤ 60 字符

Hermes 要求 `description` 字段 ≤ 60 字符。超标技能在发现和路由时表现异常。

**违规常见模式**：将 Anthropic/Claude Code 风格的超长 description（300-900 字符）直接用于 Hermes。

**修复方法**：批量扫描 → 逐条精简为中文关键词句 → 脚本 patch。

```python
# 扫描示例
import os, re, yaml
for root, dirs, files in os.walk(skills_root):
    if "SKILL.md" in files:
        desc = extract_description(os.path.join(root, "SKILL.md"))
        if len(desc) > 60:
            print(f"超标: {len(desc)}c — {os.path.basename(root)}")
```

### tags 和 category 不能为空

- `tags: []` → H-23 FAIL
- `category:` 缺失 → H-23 FAIL
- description 应包含触发关键词作为路由信号

### 禁止空壳目录

只有 DESCRIPTION.md 无 SKILL.md 的目录是旧版标签遗留，Hermes 无法加载：
- 分类占位 → 删除（如 `diagramming/`、`gifs/`）
- 有效内容 → 重命名 DESCRIPTION.md → SKILL.md（如 `domain/`）

### SKILL.md body 应 > 10 行

12 行的骨架（如 pptx 旧版）是 AP-23 反模式——路由存根不能让 agent 理解技能能力。至少应包含：核心能力概述 + 决策树 + 快速参考。

## 符号联结注意事项

`~/.hermes/skills/` → `~/.agents/skills/` 的符号联结：
- `skill_manage(action='delete')` **无法处理符号联结**，必须用 `rm -rf` 同时删除源和联结
- 修改源文件自动反映到联结（`patch`、`write_file` 直接操作源路径即可）

## 功能重叠检测

- 两技能来自同一来源（如 obra/superpowers）→ 高度怀疑重叠
- 用 `diff` 比较 SKILL.md body 部分：
  ```bash
  diff <(sed '1,/^---$/d' skill-a/SKILL.md) <(sed '1,/^---$/d' skill-b/SKILL.md) | grep "^[<>]" | wc -l
  ```
- 80%+ 重叠 → 合并，保留超集

## 审查流程

```
1. 扫描全部 description 长度 → 超标名单
2. 检查 tags + category 完整性
3. ls 空目录 → 分类（占位删 / 内容转）
4. 同源技能 diff 对比 → 重叠检测
5. 批量修复 → 验证 → 提交
```
