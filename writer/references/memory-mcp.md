# Memory MCP：小说记忆层权威规范（v8.4）

> 本文档是 writer + novel-pipeline 两个 skill 关于**记忆存储**的**唯一事实来源**。
> writer v8.4 起，小说的人物 / 势力 / 剧情节点 / 伏笔 / 世界观**统一存入 `novel_project` MCP**，
> 禁止再向 `.writer/state/*.json` 或任何本地 JSON 写入这些数据。

---

## 1. MCP 概述

- **服务名**：`novel_project`
- **底层包**：`mcp-memory-sqlite`（stdio）
- **数据库落盘**：`{project}/memory/novel_project.db` —— **每本书一个独立库**，由该书目录下的 `.mcp.json` 配置（见 §7）
- **检索能力**：SQLite FTS 文本关键词相关性检索（**非向量语义**）
- **写入模型**：实体 (`entity`) + 观测 (`observations[]`) + 有向关系 (`relations`)
- **限制**：不支持 embedding 字段（传入会被静默丢弃，见 CHANGELOG）

---

## 2. 工具总目录（8 个）

| 工具 | 参数 | 幂等 | 用途 |
|---|---|---|---|
| `create_entities` | `{entities: [{name, entityType, observations[]}]}` | ⚠️ 覆盖式 | 新建/更新实体；**存在则会用新 observations 替换旧的** |
| `add_observations` | — | — | **未提供**（观测追加只能通过 `create_entities` 覆盖式重写） |
| `delete_entity` | `{name}` | ✅ | 删实体及其所有观测/关系 |
| `create_relations` | `{relations: [{source, target, type}]}` | ✅ | 建关系（有向；source/target 需为已存在的 entity name） |
| `delete_relation` | `{source, target, type}` | ✅ | 删单条关系 |
| `search_nodes` | `{query, limit?}` | ✅ | FTS 文本相关性检索，`limit` 默认 10，最大 50 |
| `read_graph` | `{}` | ✅ | 近期实体 + 关系（默认视图，用于 sanity check） |
| `get_entity_with_relations` | `{name}` | ✅ | 单实体 + 其所有关系邻居（做续写前上下文最常用） |

### 2.1 ⚠️ `create_entities` 覆盖式陷阱

源码行为：
```
DELETE FROM observations WHERE entity_name = ?
-- 然后逐条 INSERT 新的 observations
```

**含义**：`create_entities` 传入 `observations=["A"]` 会先删掉这个实体已有的所有观测，再插入 `"A"`。
不是追加。

**正确追加流程**：
```
1. get_entity_with_relations({name: "苏白"})  → 得到当前 observations 列表 old_obs
2. new_obs = old_obs + ["ch012: 突破练气四层"]
3. create_entities({entities: [{name: "苏白", entityType: "人物", observations: new_obs}]})
```

`archive_facts.py`（v8.4 版本）会自动生成上述先读后写的 payload——Agent 不应手工做这一步。

---

## 3. 实体命名与分类规范

### 3.1 `entityType`（受控词表）

| entityType | 何时用 | name 示例 |
|---|---|---|
| `人物` | 任何有名字的角色（主角/配角/一次性反派） | `苏白`、`老周`、`临水城守将` |
| `势力` | 门派/公司/家族/组织 | `青云门`、`血刃门`、`长安分局` |
| `地点` | 城市/山脉/秘境/关键场所 | `青云门`、`落月山`、`临水城` |
| `功法` | 术法/技能/装备/血脉 | `破空剑诀`、`焚天决`、`血月血脉` |
| `境界` | 修炼等级/职业阶数/等级体系 | `练气四层`、`筑基后期`、`S级冒险者` |
| `伏笔` | 待回收/部分回收的埋线（**id 用 `伏笔:xxx` 前缀命名**） | `伏笔:老周身份`、`伏笔:神秘玉佩` |
| `剧情节点` | 卷内关键转折/大事件 | `剧情:入门试炼`、`剧情:第一次血月` |
| `世界规则` | 大陆通用规则/物理规律/特殊禁忌 | `世界规则:魂气不可反哺`、`世界规则:血月周期` |

> 若一个名字在两个 type 都合理（如"青云门"既是势力又是地点），**优先建为 `势力`**，然后通过 `create_relations` 与地点关联。

### 3.2 `observations` 内容规范

- 每条观测**一句话一个事实**，形如 `"ch012: 突破练气四层"`、`"ch028: 与老周订立死约"`
- 章节前缀 `chNNN:` **强制** — 便于按章节回溯、审查时定位
- 长设定文字（人设/背景故事）拆成多条观测，不是一条 500 字长文
- 关系事实（"苏白是青云门弟子"）**不写在 observations**，改用 `create_relations`

### 3.3 `relations.type`（受控词表）

| type | 语义 | source → target |
|---|---|---|
| `所属` | 隶属关系 | `苏白` → `青云门` |
| `敌对` | 敌对/仇怨 | `苏白` → `血刃门` |
| `盟友` | 结盟/合作 | `青云门` → `太一宗` |
| `亲属` | 血亲/收养/婚姻 | `苏白` → `苏母` |
| `师承` | 师徒/传承 | `苏白` → `青云剑君` |
| `位于` | 地理归属 | `青云门` → `落月山` |
| `修习` | 人物 → 功法 | `苏白` → `破空剑诀` |
| `包含` | 势力 → 分支/剧情 → 章节段 | `血刃门` → `血刃分舵` |
| `伏笔于` | 伏笔 → 首次埋线的剧情节点 | `伏笔:老周身份` → `剧情:入门试炼` |
| `回收于` | 伏笔 → 回收章节的剧情节点 | `伏笔:老周身份` → `剧情:第七卷决战` |
| `触发` | 剧情 A → 剧情 B（因果） | `剧情:第一次血月` → `剧情:苏白入邪` |

未列入的关系类型**新增前需要在本文档追加**，避免同义漂移（如"隶属"vs"归属"）。

---

## 4. 调用契约（Agent 必须遵守）

### 4.1 写入契约（新增/更新记忆）

**触发时机**：
- 写完一章正文（`references/write.md` Step 5 Reflect）
- 全面审查发现新事实（`references/review-cycle.md` Step 4）
- 用户手动补充设定（"帮我把老周的背景补进记忆"）

**执行动作**（按顺序）：
1. Agent 从本章正文 / 用户输入中提取原子事实（人物变化 / 新势力 / 新伏笔 / 伏笔回收）
2. 对每个受影响的**已存在实体**，先调 `get_entity_with_relations` 拿 old observations
3. 合并 old + new，调 `create_entities` 一次性写回
4. 对新出现的**关系**，调 `create_relations`
5. 对**已回收伏笔**：调 `create_relations` 加 `回收于` 边，再更新伏笔实体的 observations 补一句 `chNNN: 已回收（<回收方式>）`

**绝对禁止**：
- ❌ 直接 `create_entities` 覆盖已有实体的 observations（会丢历史）
- ❌ 把关系事实塞进 observations 文本（如 `"苏白师父是李道人"` 应建 `师承` 关系而不是写入观测）
- ❌ 用不同 entityType 建同名实体（`人物:苏白` 和 `角色:苏白` 视为两个）

### 4.2 检索契约（写章前查询）

**触发时机**：
- 每次写新章节前
- 每次审查跨章一致性时
- 用户问 "苏白当前修为？"、"老周还有什么伏笔？"

**执行动作**（按需要选择）：

| 需求 | 首选工具 | 备用 |
|---|---|---|
| 查单个已知实体全貌 | `get_entity_with_relations({name})` | — |
| 查"和苏白有关的所有事" | `get_entity_with_relations({name: "苏白"})` | — |
| 模糊/关键词搜索（不确定名字） | `search_nodes({query: "临水城 守将", limit: 20})` | 逐词多次搜 |
| 查所有未回收伏笔 | `search_nodes({query: "伏笔", limit: 50})` 后过滤 `entityType == "伏笔"` 且未含 `回收于` 关系 | — |
| 项目全景速览 | `read_graph()` | `report_graph.py` |

### 4.3 FTS 检索最佳实践（因为不支持向量）

FTS 只匹配字面字符串，不匹配同义词。为提高召回率，Agent 应：

1. **同义词并列查询**：查"少年剑客"时用 `search_nodes({query: "少年 剑 剑客 持剑"})`，MCP 会用 OR 逻辑合并
2. **多次窄查询合并**：查"苏白 vs 老周关系"时先 `get_entity_with_relations("苏白")` 再 `get_entity_with_relations("老周")`，取两个 relations 集合的交集
3. **善用 name 前缀**：伏笔用 `伏笔:xxx`、剧情用 `剧情:xxx`，`search_nodes({query: "伏笔:"})` 即可批量捞
4. **不要指望语义匹配**：查"和权谋有关的势力"是查不到的；只能查具体名字/词

---

## 5. 数据组织建议（新项目开工前）

### 5.1 首批 seed 实体

`project-init` 完成后，Agent 应根据 `setting/*.md` 一次性 seed 以下实体：

```
setting/characters.md      → 每个角色一个 entityType="人物" 实体
setting/factions.md        → 每个势力一个 entityType="势力" 实体
setting/power_system.md    → 境界体系每层一个 entityType="境界" 实体
                              功法每种一个 entityType="功法" 实体
setting/story_bible.md     → 世界通则每条一个 entityType="世界规则" 实体
                              主要地点每处一个 entityType="地点" 实体
```

seed 时用 `create_entities`（此时是首次创建，覆盖不损失历史）。
seed 完成后同时用 `create_relations` 建立首批关系（人物-势力隶属、地点-势力位于、人物-功法修习、人物-人物亲属/敌对）。

### 5.2 seed 完成的 sanity check

```
read_graph()  → 应至少返回：
                主要角色 5+、势力 3+、地点 3+、境界体系 1 套（≥3 层）
```

若数量明显不足，回去补 setting/*.md 后重跑 seed。

---

## 6. 常见错误与陷阱

| 错误 | 后果 | 正确做法 |
|---|---|---|
| `create_entities` 追加时只传新观测 | 旧观测全丢 | 先 `get_entity_with_relations` 拿旧观测再合并写回 |
| 传入 `embedding` 字段 | 静默丢弃（MCP 不支持向量） | 不要传；语义查询靠 FTS 多词组合 |
| 关系写在 observations 里 | 无法用 `read_graph` 可视化，查询漏 | 用 `create_relations` |
| 同一实体多次覆盖章节前缀不一致 | 无法按章节回溯 | 所有观测强制 `chNNN: <事实>` 格式 |
| entityType 混用（`角色` vs `人物`） | 同名实体分裂 | 严格用 §3.1 受控词表 |
| 关系 source/target 用了不存在的 name | `create_relations` 会失败 | 先 `create_entities` 建两端，再建边 |

---

## 7. MCP 配置方法与存储位置

### 7.1 一书一库（标准做法）

数据库**落在书自己的目录里**，每本书一个独立库：

```
{project}/
├── .mcp.json                     # 项目级 MCP 配置（入 git）
├── memory/
│   ├── novel_project.db          # 记忆库本体（入 git）
│   ├── novel_project.db-wal      # WAL 伴生文件（.gitignore）
│   └── novel_project.db-shm      # 共享内存伴生文件（.gitignore）
├── novel.json
├── setting/
└── chapters/
```

### 7.2 `.mcp.json` 内容（照抄即可）

在**书目录根**创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "novel_project": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-memory-sqlite"],
      "env": {
        "SQLITE_DB_PATH": "./memory/novel_project.db"
      }
    }
  }
}
```

**必须用相对路径 `./memory/novel_project.db`**，不要写绝对路径。这样开新书时把 `.mcp.json` 复制进新目录即可，零改动就是独立的库。

### 7.3 关键前提：在书目录内启动

`mcp-memory-sqlite` 解析路径的源码逻辑是：

```js
const db_path = process.env.SQLITE_DB_PATH || './sqlite-memory.db';
```

相对路径基于**进程 cwd**，而 `.mcp.json` 只在**启动 Claude Code 的那个目录**被读取。因此：

```bash
cd {project}          # 必须先进书目录
claude                # 再启动
```

在书目录的上级（如多书共存的 `writer/` 根）启动，这份 `.mcp.json` 不生效。

首次在新书目录启动时，Claude Code 会提示**信任该项目的 MCP 配置**，approve 一次即可。

### 7.4 不要用全局配置

**禁止**把 `novel_project` 写进 `~/.claude.json` 的顶层 `mcpServers`。原因：那里只能填绝对路径，会导致所有书共写同一个文件——写第二本书时新旧剧情图谱混在一起。

若已存在全局配置，先移除，再改用项目级 `.mcp.json`：

```bash
# 检查全局是否有残留（应输出空）
python -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude.json'),encoding='utf-8'));print(list(d.get('mcpServers',{}).keys()))"
```

同名 server 同时存在于全局和项目级会冲突。

### 7.5 `.gitignore`

WAL/SHM 是运行时副产物，不入库；`.db` 本体建议入库（记忆随书走）：

```gitignore
*.db-shm
*.db-wal
*.db.bak-*
```

⚠️ gitignore **管不到已跟踪的文件**。若 `-wal`/`-shm` 之前已被提交，需 `git rm --cached <file>` 才能脱离版本控制。

### 7.6 备份与验证

复制 `.db` 前**必须先 checkpoint**，否则 WAL 里未落盘的数据不在副本中：

```python
import sqlite3, shutil
c = sqlite3.connect('memory/novel_project.db')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()
shutil.copy2('memory/novel_project.db', 'memory/novel_project.db.bak-YYYYMMDD')
```

⚠️ **备份后必须独立校验**，不要相信复制操作的返回值：

```python
import os, sqlite3
p = 'memory/novel_project.db.bak-YYYYMMDD'
print('size:', os.path.getsize(p))                    # 不能是 0
c = sqlite3.connect(p)
print('integrity:', c.execute('PRAGMA integrity_check').fetchone()[0])
print('rows:', [c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                for t in ('entities','observations','relations')])
```

（`ls` 在部分终端代理下会显示过滤后的失真大小，用 `os.stat` / `os.path.getsize` 复核。）

### 7.7 重置为空库（开新书复用旧文件时）

保留 schema、只清数据：

```python
import sqlite3
c = sqlite3.connect('memory/novel_project.db')
c.execute('PRAGMA foreign_keys=OFF')
for t in ('relations', 'observations', 'entities'):
    c.execute(f'DELETE FROM {t}')
c.execute('DELETE FROM sqlite_sequence')
c.commit(); c.execute('VACUUM'); c.close()
```

清空前**先备份并按 §7.6 校验**。完成后用 `read_graph()` 确认返回空图谱。

---

## 8. 与旧 `.writer/state/*.json` 的关系

v8.4 起：

| 数据 | v8.3 及以前 | v8.4 及以后 |
|---|---|---|
| 人物当前状态 | `.writer/state/characters.json` | **novel_project MCP，entityType="人物"** |
| 伏笔进度 | `.writer/state/foreshadowing.json` | **MCP，entityType="伏笔" + 关系** |
| 势力/世界观 | `.writer/state/world_setting.json` | **MCP，entityType="势力"/"地点"/"世界规则"** |
| 力量体系 | `.writer/state/power_system.json` | **MCP，entityType="境界"/"功法"** |
| 项目元数据（stage / chapters_done / current_chapter） | `novel.json` | **仍在 `novel.json`（不迁移）** |
| tracking/*.md 人读快照 | 从 JSON 派生 | 从 MCP 派生（`report_graph.py --render-tracking`）或废除 |

**迁移工具**：`scripts/import_state_to_mcp.py`
- 读取旧项目的 `.writer/state/*.json`
- 生成对应的 `create_entities` / `create_relations` 调用序列（stdout JSON）
- Agent 依此逐条调 MCP
- 完成后手动删除 `.writer/state/`

---

## 9. 相关文件

- `scripts/archive_facts.py` — 写章 Step 5 归档（v8.4 版：只生成 MCP payload，不写 JSON）
- `scripts/import_state_to_mcp.py` — 一次性历史数据迁移
- `scripts/report_graph.py` — 从 MCP 派生实体关系图
- `references/memory-governance.md` — 治理规则（禁令清单）
- `references/write.md` Step 5 — 归档触发点
- `references/review-cycle.md` Step 4 — 事实增量校验触发点
