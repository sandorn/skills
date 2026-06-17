# writer.json 状态文件格式

`writer.json` 是项目的**单一事实来源**，位于项目根目录。所有模块必须通过此文件读写项目状态。

## Schema

```json
{
  "project": "书名",
  "author": "作者笔名",
  "stage": "planning|scaffold|writing|reviewing|completed",
  "genre": "xuanhuan|urban|xianxia|horror|other",
  "platform": "fanqie|feilu|qidian|zhihu|other",
  "chapters_total": 100,
  "chapters_done": 0,
  "words_per_chapter": 3000,
  "current_volume": 1,
  "current_chapter": 0,
  "last_action": "",
  "last_action_time": "2026-01-01T00:00:00",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

## 阶段定义

| stage | 含义 | 下一个操作 |
|-------|------|-----------|
| `planning` | 规划阶段，还未开始写 | plan / write |
| `scaffold` | 项目骨架已创建，尚未开始写正文 | plan |
| `writing` | 正在写正文中 | write / review |
| `reviewing` | 正在进行章节审查 | review |
| `completed` | 全书完结 | - |

## 读取/写入方法

### Python（推荐）

```python
import json, os

def read_state(project_root):
    path = os.path.join(project_root, "writer.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def write_state(project_root, data):
    path = os.path.join(project_root, "writer.json")
    data["updated_at"] = "2026-01-01T00:00:00"  # placeholder — use datetime.now().isoformat()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_state(project_root, **kwargs):
    state = read_state(project_root) or {}
    state.update(kwargs)
    write_state(project_root, state)
```

### Shell（使用 jq）

```bash
# 读取
jq -r '.chapters_done' writer.json

# 写入
jq '.chapters_done += 1 | .updated_at = now' writer.json > writer.json.tmp && mv writer.json.tmp writer.json
```
