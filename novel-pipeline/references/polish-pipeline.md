# 润色管线选择指南

## 两条管线

| 管线 | 输入 | 引擎 | 何时用 |
|------|------|------|--------|
| **写单章** (pipeline step [5]) | 初稿 `draft_text` | novel-doubao | 写新章节时自动走 |
| **独立润色** (`polish_independent.py`) | 成品正文 | novel-doubao | 用户说「润色/文笔修饰」 |

## 独立润色管线详解

### 流程

```
① 读取正文
② novel-doubao 润色
③ 完整性检查
④ 输出润色后文本 + 报告
```

### 报告内容构成

| 步骤 | 来源 | 内容 |
|------|------|------|
| ② | novel-doubao | 润色结果字数统计 |
| ③ | 完整性检查 | 结尾标点检查、篇幅变化比率 |

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
    "doubao_result": "成功, 1247字",
    "integrity_check": "PASS"
  },
  "issues": [],
  "passed": true,
  "hook": "polish_independent"
}
```

## 关键限制

### mcp_call 的 I/O 模型
novel-doubao 的 API 响应时间约 60-170 秒（因为通过 `/api/plan/v3` 的 agent plan 链路，推理时间较长）。对 MCP server 进程直接使用 `subprocess.communicate()` 会提前关闭 stdin，导致 `anyio.ClosedResourceError`。

**直接调用 MCP server 时必须使用线程读取 stdout**（见 `hooks/utils.py::BaseMCPClient`），保持 stdin 开着直到收到 id=2 的响应。CLI 对本地 hook 脚本使用一次性 stdin 是允许的，因为 hook 内部仍通过 `BaseMCPClient` 和 MCP server 通信。

**超时设置**：doubao 的 timeout 建议设为 300s（5 分钟）。大章（9000+ 字）可能需 160s+。

### 批量润色注意事项
逐章批量润色时，每章约 80-170s，30 章总计约 60 分钟。建议分批次（3-5 章一批）前台运行，或使用 `timeout=600` 的单次前台批处理。

### doubao 回退降级行为
当 doubao 调用失败（API 超时、key 错误、网络问题）时，`polish_independent.py` 保留原文不变，返回错误信息，不会丢失数据。`passed=False` + `issues=["doubao 失败: ..."]`。

### doubao 环境配置
`.env` 唯一位置：`<Skill路径>\.env`（例：`C:\Users\Administrator\.agents\skills\novel-pipeline\.env`）。

```env
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
DOUBAO_API_KEY=<ark key>
DOUBAO_MODEL=<模型 ID>
```

server 无内置默认，缺任一必需 KEY 即 `sys.exit(1)`。`DOUBAO_BASE_URL` 可含或不含 `/chat/completions`，代码自动判断。

⚠️ **编码陷阱**：PowerShell `Set-Content` 重置 .env 文件时，如果不带 `-Encoding UTF8` 参数，会因为 PS5.1 的默认编码（系统 ANSI）破坏文件内的中文字符和特殊符号。**可靠做法**：用 write_file 工具直接覆写，或用 Python 脚本 `open().write()`。
