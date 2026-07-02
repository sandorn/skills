# 双记忆 MCP 治理规则

> **铁律**：两套记忆服务严格隔离，禁止交叉读写。违反此规则将导致系统记忆污染或小说数据丢失。
> **每次检索前**：先判断内容归属，选错记忆库视为**严重错误**。

## 内容归属判定（检索前强制执行）

```
检索内容
  ├─ 含角色名/地名/功法名/小说章节号/剧情关键词？
  │    → memory-novel（SQLite）
  ├─ 含工具名称/配置项/运维命令/系统参数/CLI规则？
  │    → memory-offical（JSON）
  └─ 无法判断？
       → 先问用户，不做猜测
```

## 服务定义

### memory-offical（官方 JSON 存储）

| 属性 | 值 |
|------|-----|
| 用途 | 系统维护信息、全局工具规范、固定配置、后台运维记录 |
| 允许 | 查询/新增/更新系统类内容 |
| **禁止** | **绝对不存储任何小说人物、剧情、章节、伏笔、势力设定** |

### memory-novel（SQLite 持久存储）

| 属性 | 值 |
|------|-----|
| 用途 | 全部小说相关内容 |
| 数据范围 | 人物档案、势力门派、修炼体系、章节剧情、时间线、伏笔、人物关系、文风设定 |
| 允许 | 所有写作流程（查人设、记录剧情、新增角色、追踪伏笔） |

## 工具调用硬性约束

### 小说创作相关 → 只用 memory-novel

触发场景：写章、审查、查询角色、记录剧情、新增角色、追踪伏笔、更新关系

```
search_nodes / open_nodes / read_graph
create_entities / add_observations / create_relations
```

### 系统运维相关 → 只用 memory-offical

触发场景：修改系统规则、查询运维配置、更新全局工具说明

```
memory-offical 的记忆工具
```

## 违规示例

| ❌ 错误 | ✅ 正确 |
|--------|--------|
| 把角色「林北」存入 memory-offical | 角色「林北」→ memory-novel `create_entities` |
| 把工具规范写入 memory-novel | 工具规范 → memory-offical |
| 在 memory-offical 中搜索「筑基丹」 | 在 memory-novel 中 `search_nodes("筑基丹")` |
| 用 memory-novel 存储 litellm 配置 | 用 memory-offical 存储系统配置 |

## Writer Skill 集成

writer skill 的所有写章/审查/质检管线只与 memory-novel 交互。memory-offical 不在 writer skill 的路由表中出现。

## 全 MCP 角色一览（仅 Claude Code 侧）

| MCP | 类型 | 归属域 | 用途 |
|-----|------|--------|------|
| `memory-novel` | 记忆存储 | **小说域** | 人物/势力/剧情/伏笔/关系知识图谱 |
| `memory-offical` | 记忆存储 | **系统域** | 系统维护/工具规范/运维配置 |
| `publishready` | 分析工具 | **小说域** | AI腔审计/可读性/风格漂移（不存储数据） |
| `firstory` | 分析工具 | **小说域** | 角色一致性/OOC检测（不存储数据） |
| `uno` | 增强工具 | **小说域** | 叙事增强/重复消除/环境描写（不存储数据） |

> **分析/增强工具（publishready, firstory, uno）不存储数据**——它们只做分析或文本增强，结果由 writer 管线决策是否采纳。小说事实数据始终只写入 memory-novel。
