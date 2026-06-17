---
name: moke:genre-list
description: List all available genre profiles / 列出所有可用题材配置
---

<objective>
Display all available genre profiles (built-in + project-specific) with their key information.
</objective>

<process>
1. 扫描题材配置文件：
   - 内置题材：`genres/` 目录下的 .md 文件
   - 项目题材：`books/{bookName}/genres/` 目录下的 .md 文件（优先级更高）

2. 解析每个题材配置的 YAML frontmatter：
   - name: 题材名称
   - id: 题材ID
   - language: 语言
   - chapterTypes: 章节类型
   - numericalSystem: 是否有数值系统
   - powerScaling: 是否有战力提升

3. 以表格形式展示所有题材

4. 显示如何查看详细题材配置的方法
</process>

## 输出格式

```
可用题材配置 (Genre Profiles):

题材ID       题材名称      语言    数值系统    战力提升    章节类型数
──────────────────────────────────────────────────────────────────
xuanhuan     玄幻         zh      ✓          ✓          5
urban        都市         zh      ✗          ✗          5
xianxia      仙侠         zh      ✓          ✓          5
horror       恐怖         zh      ✗          ✗          5
other        其他         zh      ✗          ✗          4

总计：5 个题材配置

查看详细配置：
/moke:genre-show <题材ID>

创建新题材：
/moke:genre-create <题材ID> [选项]
```

## 使用方式

```bash
# 列出所有题材
/moke:genre-list

# 查看特定题材的详细配置
/moke:genre-show xuanhuan

# 创建自定义题材
/moke:genre-create scifi --name "科幻" --numerical --power
```
