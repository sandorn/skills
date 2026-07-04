# 项目设置与隔离机制

## 多项目隔离
每本小说独立存放状态文件，互不干扰。由 `hooks/utils.py` 统一实现查找逻辑：
1. 从当前工作目录向上查找 `novel-pipeline.json` 项目标记文件
2. 找到 → 使用该项目下的 `state-files/` 目录（读/写）
3. 未找到 → 回退到 Skill 模板目录（只读）

## 新建项目

```powershell
# 1. 创建项目目录
mkdir my-novel
cd my-novel

# 2. 创建必要子目录
mkdir chapters, outline, state-files

# 3. 复制配置模板
Copy-Item <Skill路径>\state-files\config.example.json .\novel-pipeline.json
Copy-Item <Skill路径>\state-files\*.json .\state-files\

# 4. 编辑 novel-pipeline.json，填入书名/作者/体裁
```

## 项目目录结构标准

```
my-novel/
├── novel-pipeline.json       ← 项目标记（Hook 自动检测）
├── state-files/              ← 本书专属状态
│   ├── world_setting.json    ← 世界观设定
│   ├── characters.json       ← 人物档案
│   ├── foreshadowing.json    ← 伏笔管理
│   └── power_system.json     ← 力量/战力体系
├── chapters/                 ← 章节文件
└── outline/                  ← 分卷大纲/章纲
```

## 存储模式切换
| 模式 | 配置值 | 说明 |
|------|--------|------|
| 本地文件（默认） | `state_storage_mode: "local_file"` | 纯本地JSON存储，无需额外服务 |
| MCP记忆体 | `state_storage_mode: "mcp_memory"` | 同步到分布式记忆库，支持多端同步、版本回溯 |

## 老版本升级（v1→v2）
1. 根目录执行 `mkdir outline, state-files`
2. 大纲文件移入 `outline/`，辅助脚本移入 `scripts/`
3. 更新 `novel-pipeline.json`：新增 `state_storage_mode`/`local_state_dir`/`mcp_memory_novel_endpoint`/`outline_dir`
4. 复制新版状态模板：`Copy-Item <Skill路径>\state-files\*.json .\state-files\`
5. 验证：`python hooks/load_state.py` → `loaded: true`
