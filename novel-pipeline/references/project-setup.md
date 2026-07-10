# 项目设置与隔离机制

## 多项目隔离
每本小说独立存放状态文件，互不干扰。由 `hooks/utils.py` 统一实现查找逻辑：
1. 从当前工作目录向上查找项目标记文件，优先级：`novel.json` > `writer.json` > `novel-pipeline.json`
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
Copy-Item <Skill路径>\state-files\config.example.json .\novel.json
Copy-Item <Skill路径>\state-files\*.json .\state-files\

# 4. 编辑 novel.json，填入书名/作者/体裁
```

## 项目目录结构标准

```
my-novel/
├── novel.json                ← 项目标记（Hook 自动检测；writer.json / novel-pipeline.json 也识别）
├── state-files/              ← 本书专属状态
│   ├── world_setting.json    ← 世界观设定
│   ├── characters.json       ← 人物档案
│   ├── foreshadowing.json    ← 伏笔管理
│   └── power_system.json     ← 力量/战力体系
├── chapters/                 ← 章节文件
└── outline/                  ← 分卷大纲/章纲
```

## 存储模式
所有状态存本地 JSON（`state-files/*.json`），由 `load_state.py` / `archive_state.py` 读写。不依赖任何外部知识图谱或 memory MCP。

## 章节命名规范
统一使用三位数补零 + 下划线：`chapters/ch_001.md`、`ch_010.md`、`ch_101.md`（与 writer skill 一致）。工具入口 `hooks/utils.py::chapter_filename(n)`。

## 老版本升级（v1→v2）
1. 根目录执行 `mkdir outline, state-files`
2. 大纲文件移入 `outline/`，辅助脚本移入 `scripts/`
3. 复制新版状态模板：`Copy-Item <Skill路径>\state-files\*.json .\state-files\`
4. 批量重命名章节：`ch1.md` → `ch_001.md`、`ch01.md` / `ch001.md` → `ch_001.md` 等
5. 验证：`python hooks/load_state.py` → `loaded: true`
