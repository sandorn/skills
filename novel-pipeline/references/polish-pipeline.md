# 润色管线选择指南

## 两条管线

| 管线 | 输入 | 引擎 | 何时用 |
|------|------|------|--------|
| **写单章** (pipeline step [5]) | 初稿 `draft_text` | novel-doubao | 写新章节时自动走 |
| **独立润色** (`polish_independent.py`) | 成品正文 | publishready→uno→novel-doubao | 用户说「润色/文笔修饰」 |

## 独立润色管线详解

### 流程

```
① 读取正文
② publishready 审计：analyze_text + audit_ai_sounding_prose + find_hotspots + suggest_revision_levers
③ uno 分析：analyze_text（叙事结构 + 感官丰富度）
④ 综合评估 → 生成摘要报告
⑤ novel-doubao 润色（携带双报告摘要作为上下文，让 doubao 知道 AI 腔风险点和感官缺失点）
⑥ publishready 复检：compare_text_versions
⑦ 输出润色后文本 + 完整审计报告
```

### 报告内容构成

| 步骤 | 来源 | 内容 |
|------|------|------|
| ② | publishready | 文本可读性、AI腔风险、热点段落、修改建议方向 |
| ③ | uno | 叙事位置、场景类型、角色焦点、情绪基调、感官丰富度(0-4)、句长分布 |
| ④ | 综合 | 摘要：AI风险等级、感官缺失标记、建议方向 |
| ⑥ | publishready | 修改前后对比评分、内容完整性指标 |

### 命令

```bash
# 逐章（stdin 传入文本）
python hooks/polish_independent.py

# 或按章节号
echo '{"chapter": 123}' | python hooks/polish_independent.py
```

### 输入格式

```json
{"text": "完整正文..."}
{"chapter": 123}          # 自动读 chapters/ch123.md
{"text": "...", "ch": 1}  # 同时指定
```

### 输出格式

```json
{
  "polished": "润色后正文...",
  "report": {
    "pr_analyze": "...",
    "pr_ai_audit": "...",
    "pr_hotspots": "...",
    "pr_suggestions": "...",
    "uno_analyze": "...",
    "assessment": {"publishready": {...}, "uno": {...}},
    "doubao_result": "成功, 1247字",
    "pr_verification": "..."
  },
  "issues": [],
  "passed": true,
  "hook": "polish_independent"
}
```

## 关键限制

### uno 的 enhance_text 不可用
uno 的 `enhance_text` / `custom_enhance_text` 是**英文工具**，内部硬编码了英文环境描写模板（光的过滤、声音纹理、触感描述等），注入中文文本会造成**英文段落污染**，且无法恢复。

**中文润色/扩写**：走 novel-doubao（`polish_chapter`），只做文字优化不改剧情。
**uno 在中文场景的定位**：仅 `analyze_text`（叙事结构分析），不启用 `enhance_text`。

### mcp_call 的 I/O 模型
novel-doubao 的 API 响应时间约 60-170 秒（因为通过 `/api/plan/v3` 的 agent plan 链路，推理时间较长）。`subprocess.communicate()` 会提前关闭 stdin 导致 `anyio.ClosedResourceError`。

**必须使用线程读取 stdout**（见 `polish_independent.py` 的 `mcp_call` 实现），保持 stdin 开着直到收到 id=2 的响应。

**超时设置**：doubao 的 timeout 建议设为 300s（5 分钟）。大章（9000+ 字）可能需 160s+。publishready 和 uno 可设为 60s。

### 批量润色注意事项
逐章批量润色时，每章约 80-170s，30 章总计约 60 分钟。建议分批次（3-5 章一批）前台运行，或使用 `timeout=600` 的单次前台批处理。

### doubao 回退降级行为
当 doubao 调用失败（API 超时、key 错误、网络问题）时，`polish_independent.py` 保留原文不变，并返回完整的 publishready+uno 审计报告，不会丢失数据。`passed=False` + `issues=["doubao 失败: ..."]`。

### doubao 环境配置
```env
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
DOUBAO_API_KEY=<ark key>
DOUBAO_MODEL=ark-code-latest
```

`.env` 位于 `C:\\Users\\Administrator\\.litellm\servers\\.env`。doubao_server.py 启动时**必须设置 cwd** 为该目录，否则读不到 .env。

⚠️ **编码陷阱**：PowerShell `Set-Content` 重置 .env 文件时，如果不带 `-Encoding UTF8` 参数，会因为 PS5.1 的默认编码（系统 ANSI）破坏文件内的中文字符和特殊符号。即使加了 `-Encoding UTF8`，如果用 `(Get-Content ...) -replace ... | Set-Content ...` 的管道模式，可能产生 UTF-8（无 BOM）但中间行被 BOM 破坏的问题。**可靠做法**：用 `write_file` 工具直接覆写，或用 Python 脚本 `open().write()`。