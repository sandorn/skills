# 文风转换 / 批量润色

**激活词:** 文风转换、转写、润色、批量润色、AI润色、豆包润色
**依赖:** `scripts/polish.py`, `references/style-sop.md`
**最低模型:** 需推理能力的 LLM（推荐 doubao-seed / claude-opus / gpt-4 级别）

---

## 适用场景

| 场景 | 说明 | 典型命令 |
|------|------|----------|
| 全卷文风转换 | 将已写章节批量转为目标文风 | `python scripts/polish.py -s chapters/ -o polished/ --style fanqie-quick-anti` |
| 单章测试 | 先用一章验证效果 | `python scripts/polish.py --test` |
| 指定章重润 | 只重新处理特定章节 | `python scripts/polish.py -c ch_015` |
| 更换模型 | 用不同模型对比效果 | `python scripts/polish.py --model gpt-4o --api-base https://api.openai.com/v1` |

---

## 快速开始

### 1. 先跑测试章

```bash
cd {project_root}
python scripts/polish.py --test
```

检查 `chapters_polished/ch_001.md` 效果。效果满意则继续。

### 2. 全量处理

```bash
python scripts/polish.py -s chapters/ -o chapters_polished/
```

### 3. 替换原文并保存版本（确认效果后）

```bash
# 手动确认后替换
cp chapters_polished/*.md chapters/
# 更新 writer.json 版本记录（polished）
```

### 4. 润色后自动审查

API 润色可能引入字数震荡、AI 腔、格式问题。替换完成后自动激发审查：

```bash
python scripts/audit.py chapters/          # 禁令+字数+段落扫描
```

若润色 ≥10 章，升级为 solo 审查（15维）。命中 blocking → 修复后重跑。

---

## 参数速查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--source, -s` | `chapters` | 源目录 |
| `--output, -o` | `chapters_polished` | 输出目录 |
| `--style` | `fanqie-quick-anti` | 文风预设 |
| `--model` | doubao-seed-2-0-lite | AI 模型 |
| `--api-key` | `$ARK_API_KEY` | API 密钥 |
| `--min-words` | 2500 | 中文字数下限 |
| `--max-words` | 3000 | 中文字数上限 |
| `--max-wc-retries` | 2 | 字数不达标最大修正次数 |
| `--delay` | 3 | 章间延迟（秒） |
| `--timeout` | 300 | 单章超时（秒） |
| `--reset` | — | 清除进度重新开始 |
| `--chapter, -c` | — | 只处理指定章 |
| `--test` | — | 测试模式 |

---

## 文风预设切换

当前支持的预设：

| 预设名 | 文件名 | 说明 |
|--------|--------|------|
| `fanqie-quick-anti` | `style-sop.md` (默认) | 番茄爆款轻松逆袭风 |

添加新预设：在 `references/presets/` 目录下创建新文件，包含系统提示词即可。

---

## 字数震荡说明

LLM 无法精确控制字数。约 **67%** 的章节能在首次润色达标（2500-3000 字），约 **24%** 需要 1-2 轮字数修正后达标，约 **9%** 会震荡无法收敛（使用最后一次结果）。

震荡章的特征：原文 3000+ 字的中长章节，AI 难以在"精简"和"扩充"之间找到平衡。这些章节建议手动微调。

---

## 环境变量

```bash
export ARK_API_KEY="your-api-key"  # 豆包 API Key
```

或通过 `--api-key` 参数传入。

---

## 与其他模块的关系

```
style-sop.md          → 文风规范定义（禁令、参数、质检标准）
polish.py            → 执行润色/转换（调用 AI API）
style-transfer.md    → 本文件（使用说明和最佳实践）
quality.md           → 转换后的质检（禁令扫描、AI腔检测）
audit.py             → 对转换结果进行质检
```

---

## 版本历史

- **1.0** (2026-06-30): 从项目级 `polish_chapters.py` 抽象为通用 skill 组件。
