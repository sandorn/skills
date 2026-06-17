# 记忆/查询：项目查询 + 写作模式学习

改编自 webnovel-learn + webnovel-query。

---

## 功能一：查询（query）

当用户询问关于项目设定、角色、伏笔、力量体系等信息时触发。

### 查询类型表

| 查询类型 | 关键词 | 最窄工具 |
|---------|--------|---------|
| **角色信息** | 谁、角色、人物、状态 | 搜索 `setting/characters.md` 或 `设定/主角.md`/角色文件 |
| **世界观/规则** | 规则、设定、力量体系、等级 | 搜索 `setting/story_bible.md`/`power_system.md` 或 `设定/世界观.md`/`系统设定.md` |
| **伏笔** | 伏笔、埋伏、回收、坑 | 搜索 `tracking/hooks.md` 或 `追踪/伏笔*.md` |
| **当前状态** | 现在、进度、写到哪了 | 读取 `tracking/current_state.md`/`追踪/当前状态.md` + `writer.json`/`project-state.json` |
| **势力关系** | 势力、门派、阵营 | 搜索 `setting/factions.md` 或 `设定/` 下势力相关文件 |
| **章节摘要** | 第几章讲了、内容 | 搜索 `tracking/chapter_summaries.md` 或 `追踪/章节摘要*.md` |
| **综合查询** | 帮我查一下、综合 | 读取 writer.json 定位 stage + 按需加载 |

### 执行策略

1. 识别查询类型
2. 根据类型选择最窄的搜索工具（不预读全部文件）
3. 对复杂查询（跨多类型），搜索相关文件后综合回答

### 禁止

- 不搜索 `.writer/` 目录下的系统文件
- 不搜索 `拆文库/` 下的对标文件（除非用户明确指定）

---

## 功能二：学习（learn）

当用户说「记住这个写法」「学这个」「记一下」时触发。

### 流程

```bash
project_root="."
memory_file="${project_root}/.writer/project_memory.json"
# 旧项目可降级写入 runtime/project_memory.json
```

### 写入格式

```json
{
  "patterns": [
    {
      "id": "pattern_001",
      "type": "hook|pacing|dialogue|payoff|emotion|format|other",
      "description": "用户输入或提炼后的完整描述",
      "chapter": 5,
      "category": "开篇钩子",
      "importance": "high|medium|low",
      "created_at": "2026-01-01T00:00:00"
    }
  ]
}
```

### 执行方式

1. 解析用户输入——提取要记住的写作模式
2. 归类 pattern_type（hook/pacing/dialogue/payoff/emotion/format/other）
3. 检查 `project_memory.json` 中是否已有完全相同的记录（type+description 相同则跳过）
4. 追加到 `patterns` 数组
5. 输出 `status: success`

### 补充字段

如果用户在写章过程中说「这章的这个写法记一下」，自动追加当前章节号到 `chapter` 字段。

---

## 成功标准

### 查询
- [ ] 回答了用户的问题
- [ ] 仅加载了必要的文件
- [ ] 标注了信息来源（哪个文件）

### 学习
- [ ] project_memory.json 存在且格式合法
- [ ] 新 pattern 已追加
- [ ] 无重复记录
- [ ] 输出包含 status: success
