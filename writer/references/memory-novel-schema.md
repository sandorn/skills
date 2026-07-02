# memory-novel 知识图谱 Schema

> MCP 服务器: `@pepk/mcp-memory-sqlite` (v1.1.0)
> 配置: Claude Code stdio MCP，`MEMORY_DB_DIR=./novel_memory_db`

## 数据模型

### Entity

```
Entity
├── name: string          (唯一标识符)
├── entityType: string    (分类标签)
└── observations: string[] (关于该实体的事实陈述)
```

### Relation

```
Relation
├── from: string          (源实体名称)
├── to: string            (目标实体名称)
└── relationType: string  (主动语态关系类型)
```

## 可用工具

| 工具 | 类型 | 用途 |
|------|------|------|
| `create_entities` | 写入 | 批量创建实体（幂等：同名跳过） |
| `delete_entities` | 写入 | 删除实体及关联数据 |
| `open_nodes` | 只读 | 按名称检索实体 |
| `add_observations` | 写入 | 向已有实体追加观察 |
| `delete_observations` | 写入 | 删除实体的观察 |
| `create_relations` | 写入 | 创建实体间关系（幂等：重复跳过） |
| `delete_relations` | 写入 | 删除关系 |
| `read_graph` | 只读 | 读取完整知识图谱 |
| `search_nodes` | 只读 | 搜索实体（名称/类型/观察内容） |

## Writer 项目 Schema

### 实体类型

| entityType | name 格式 | 示例 | 说明 |
|---|---|---|---|
| `Character` | 角色名 | `林北`, `苏瑶` | 人物实体 |
| `Chapter` | `ch_NNN` | `ch_001`, `ch_015` | 章节实体 |
| `Hook` | `hook_N` 或 `伏笔: {描述}` | `伏笔: 系统来源之谜` | 伏笔实体 |
| `Project` | 书名 | `都市重生之网吧之王` | 项目元数据 |

### 关系类型

| relationType | from → to | 含义 |
|---|---|---|
| `loves` | Character → Character | 恋爱关系 |
| `friends_with` | Character → Character | 朋友/同盟 |
| `hostile_to` | Character → Character | 敌对/竞争 |
| `family_of` | Character → Character | 亲属关系 |
| `mentors` | Character → Character | 师徒关系 |
| `appears_in` | Character → Chapter | 角色在章节出场 |
| `planted_in` | Hook → Chapter | 伏笔埋入章节 |
| `recovered_in` | Hook → Chapter | 伏笔回收章节 |

### Observation 格式约定

角色状态快照（追加到 Character 实体）:
```
chNNN: 等级=N, 位置=xxx, 权限=LvN
chNNN: 金币变动 ±N (余额: M) — 原因
chNNN: 关系里程碑 — 事件描述
```

章节元数据（追加到 Chapter 实体）:
```
标题: {章节标题}
字数: {CJK字符数}
状态: draft | reviewed | polished | final
创建时间: YYYY-MM-DDTHH:MM
```

伏笔状态（追加到 Hook 实体）:
```
planted: chNNN
category: plot | character | power | mystery
status: planted | recovered | abandoned
```

## 写章管线使用

### 写前读取 (Step 1)
```
search_nodes("主角")                    → 获取主角最新状态
search_nodes(entityType="Character")    → 获取所有角色最近状态
search_nodes(entityType="Hook")         → 获取待回收伏笔
read_graph()                            → 获取完整关系图
```

### 写后写入 (Step 3)
```
create_entities([...])      → 创建新角色/新伏笔实体
add_observations([...])     → 追加等级/金币/状态观察
create_relations([...])     → 创建关系/伏笔关联
```

### 查询
```
open_nodes(["林北", "苏瑶"])           → 精确检索角色
search_nodes("等级")                    → 搜索所有等级相关观察
search_nodes("ch_015")                  → 搜索章节相关数据
```

## 降级策略

MCP 不可用时：
- 角色状态 → `tracking/current_state.md`
- 伏笔 → `tracking/hooks.md`
- 等级/金币趋势 → 章节文件直接解析（脚本 grep）
- 关系 → `setting/characters.md` + 章节文件扫描
- 审查报告标注 「MCP 离线，知识图谱未更新」
