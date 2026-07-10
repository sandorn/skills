# 文风转换 / 批量润色

**激活词：** 文风转换、转写、润色、批量润色、AI 润色、豆包润色
**依赖：** `novel-pipeline` skill 的 `scripts/polish_chapter.py` + `references/style-sop.md` + `references/presets/`

> v8.3 起：本 skill 不再自持润色脚本。所有 API 调用、字数循环、断点续传、git 快照统一由 **novel-pipeline** 提供；writer 只负责下发文风预设。

---

## 前置准备

1. 已安装 novel-pipeline skill（通常与 writer 共处一个 `.agents/skills/` 目录）
2. novel-pipeline 的 `.env` 已配置豆包 API：`DOUBAO_API_KEY / DOUBAO_BASE_URL / DOUBAO_MODEL`
3. 项目根有 git 仓库（`git init`）——润色前会自动做快照

---

## 快速开始

### 1. 测试单章
```powershell
python <novel-pipeline>/scripts/polish_chapter.py 1 <project>/chapters `
    --style-file <writer>/references/presets/fanqie-quick-anti.md `
    --min-words 2500 --max-words 3000 --compare
```
润色结果直接覆盖 `<project>/chapters/ch_001.md`（原文件已经在 git 快照中）；`polish_compare/ch_001_compare.md` 记录字数变化。

### 2. 批量润色
```powershell
python <novel-pipeline>/scripts/polish_chapter.py --range 1-30 <project>/chapters `
    --style-file <writer>/references/presets/fanqie-quick-anti.md `
    --min-words 2500 --max-words 3000
```
- 进度自动落 `<project>/.polish_progress.json`，中断后再次运行会跳过已完成章节
- 章间默认延迟 2 秒（`--delay N` 覆盖）
- 加 `--reset` 清进度重来
- 加 `--compare` 输出所有章的对比报告到 `<project>/polish_compare/`

### 3. 润色后审查

```powershell
python <writer>/scripts/audit.py <project>/chapters   # 禁令+字数+段落
```
若润色 ≥10 章，升级为 solo 审查（15 维）。命中 blocking → 修复后重跑。

---

## 参数速查（novel-pipeline polish_chapter.py）

| 参数 | 默认 | 说明 |
|---|---|---|
| `chapter` | — | 单章章号（如 5）；与 `--range` 二选一 |
| `chapters_dir` | — | 章节目录，如 `<project>/chapters` |
| `--range N-M` | — | 批量模式章节范围 |
| `--style-file <path>` | 无 | 加载 writer 的 preset 覆盖 MCP 内嵌 prompt |
| `--min-words` / `--max-words` | 0 | 字数循环阈值（0 = 禁用循环） |
| `--max-wc-retries` | 2 | 字数不达标最多重试次数 |
| `--compare` | off | 输出润色前后对比 md |
| `--reset` | off | 重置断点进度 |
| `--force` | off | 项目非 git repo 时也放行 |
| `--skip-snapshot` | off | 跳过 git 快照（外层已保证时用） |
| `--delay` | 2 | 章间延迟秒数 |

---

## 文风预设 —— 归属仍在 writer

预设文件放在 `writer/references/presets/*.md`。writer 侧通过 `--style-file` 参数把预设文件路径传给 novel-pipeline；novel-pipeline 读取文件内容作为 MCP `polish_chapter` 工具的 `style_prompt_override` 参数。

| 预设名 | 文件 | 说明 |
|---|---|---|
| `fanqie-quick-anti` | `references/presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风 |

添加新预设：`references/presets/` 下建新文件，写完整的 system prompt 即可（不需要修改代码）。

---

## 字数震荡说明

LLM 无法精确控制字数。约 **67%** 的章节能在首次润色达标（2500-3000 字），约 **24%** 需要 1-2 轮字数修正后达标，约 **9%** 会震荡无法收敛（返回最后一次结果）。

震荡章的特征：原文 3000+ 字的中长章节，AI 难以在"精简"和"扩充"之间找到平衡。这些章节建议手动微调。

---

## 环境变量（novel-pipeline 侧）

配置文件位置：`<novel-pipeline>/.env`

```ini
DOUBAO_API_KEY=<ark-key>
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
DOUBAO_MODEL=doubao-seed-2.0-pro
```

三项缺一即报错退出，无内置默认。

---

## 与其他模块的关系

```
writer/references/style-sop.md          → 文风规范定义（禁令、参数、质检标准）
writer/references/presets/*.md          → 具体文风的 system prompt
novel-pipeline/scripts/polish_chapter.py → 执行润色（前置 git 快照 + 断点续传 + 字数循环）
novel-pipeline/mcp/novel-doubao/         → 豆包 MCP server（接受 style_prompt_override）
writer/scripts/audit.py                  → 润色后质检（禁令扫描、AI 腔检测）
```

---

## 版本历史

- **2.0** (2026-07-10): 迁移到 novel-pipeline。writer 不再自持 polish.py；仅保留 preset 文件与规范文档。
- **1.0** (2026-06-30): 从项目级脚本抽象为 skill 组件（自持 polish.py 时代）。
