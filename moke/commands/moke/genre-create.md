---
name: moke:genre-create
description: Create a new custom genre profile / 创建自定义题材配置
---

<objective>
Create a new genre profile in the project's `genres/` directory with customizable settings.
</objective>

<process>
1. 收集题材信息：
   - 题材ID (必填，如 scifi、wuxia、romance)
   - 题材名称 (可选，默认使用ID)
   - 是否有数值系统 (默认否)
   - 是否有战力提升 (默认否)
   - 是否需要时代考证 (默认否)

2. 创建 `genres/{题材ID}.md` 文件

3. 使用模板生成初始内容，包含：
   - YAML frontmatter 配置
   - 题材禁忌部分
   - 题材规则部分
   - 节奏指导部分
   - 语言风格部分

4. 输出创建成功信息和编辑指引
</process>

## 使用方式

```bash
# 基本用法
/moke:genre-create scifi

# 指定题材名称
/moke:genre-create scifi --name "科幻"

# 启用数值系统和战力提升
/moke:genre-create scifi --numerical --power

# 启用时代考证
/moke:genre-create wuxia --name "武侠" --era

# 完整示例
/moke:genre-create litrpg \
  --name "游戏系统流" \
  --numerical \
  --power
```

## 选项说明

- `--name <name>`: 题材显示名称（默认使用ID）
- `--numerical`: 启用数值系统（如等级、积分）
- `--power`: 启用战力提升
- `--era`: 启用时代考证

## 创建后的步骤

1. 编辑 `genres/{题材ID}.md` 文件
2. 根据题材特点调整配置项：
   - `chapterTypes`: 定义章节类型
   - `fatigueWords`: 添加常见的滥用词汇
   - `pacingRule`: 定义节奏规则
   - `satisfactionTypes`: 定义爽点类型
   - `auditDimensions`: 选择审计维度

3. 在"题材禁忌"部分添加该题材的写作禁忌
4. 在"题材规则"部分添加该题材的特定规则
5. 在"节奏指导"部分添加该题材的节奏建议
6. 在"语言风格"部分添加该题材的语言要求

## 示例

创建科幻题材配置：

```bash
/moke:genre-create scifi --name "科幻" --numerical --power
```

然后编辑 `genres/scifi.md`，自定义：
- 章节类型：["探索章", "发现章", "危机章", "解决章"]
- 疲劳词：["黑科技", "降维打击", "量子", "全息"]
- 节奏规则：科技发现与危机解决交替，每5-8章有一个重大发现
- 爽点类型：["科技突破", "发现外星文明", "解决危机", "时空穿越"]
