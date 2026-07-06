# novel-pipeline 故障排查

## MCP 工具未发现
- 执行 `/reload-mcp` 或 `/new` 新会话

## generate_draft 返回错误
- 检查 `~/.litellm/servers/.env` 中对应模型 API Key 是否有效
- 确认 LiteLLM 网关已启动（`http://127.0.0.1:4000/health`）

## polish_chapter 返回错误
- 检查 `.env` 中润色模型 API Key 是否有效
- 如果 DOUBAO_BASE_URL 包含完整路径（如 `/api/plan/v3/chat/completions`），doubao_server.py 的代码会额外追加 `/chat/completions` 导致双路径（`.../chat/completions/chat/completions` → 404）。
  - **修复**：在 `doubao_server.py` 第136行改为 `f"{DOUBAO_BASE_URL}" if DOUBAO_BASE_URL.endswith("chat/completions") else f"{DOUBAO_BASE_URL}/chat/completions"`
  - 或确保 `.env` 中 `DOUBAO_BASE_URL` 为基础URL（不含 `chat/completions` 后缀）

## 检查点脚本报错（ImportError）
- 运行 `python scripts/verify_env.py` 诊断缺失包
- 手动补充：`pip install httpx mcp`

## state-files 加载失败
- 确认 `state-files/` 目录存在且 JSON 格式有效
- 运行 `python hooks/load_state.py` 查看具体错误

## archive_state.py JSON 解析失败（UTF-8 BOM）

- **现象**：用 PowerShell `Get-Content file.json -Raw | python archive_state.py` 时返回 `JSON 解析失败: Unexpected UTF-8 BOM`
- **根因**：PowerShell 5.1 管道会自动给 JSON 添加 UTF-8 BOM，Python `json.loads` 默认拒收 BOM 前缀
- **解决**：不用管道，改用临时文件 + Python subprocess 方式：

  ```python
  # 在 Agent 会话中调用
  import subprocess, sys
  with open('payload.json', 'rb') as f:
      payload = f.read()
  proc = subprocess.Popen(
      [sys.executable, r'C:\...\hooks\archive_state.py'],
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  stdout, stderr = proc.communicate(input=payload, timeout=30)
  print(stdout.decode('utf-8'))
  ```

  或写入临时文件后直接重定向：
  ```powershell
  Get-Content payload.json | python hooks\archive_state.py
  ```
  但注意 `Get-Content` 的 `-Raw` 参数会产生 BOM，去掉 `-Raw` 则无 BOM。

## publishready 首次调用慢
- `npx -y @veldica/publishready-mcp` 首次运行需下载数百 MB 包
- 提前预热：终端执行 `npx -y @veldica/publishready-mcp --version`

## patch 工具在中文 .md 章节文件上失败
- **现象**：`patch` 在 `.md` 文件上持续返回 "Could not find a match"，即使文本肉眼可见匹配
- **根因**：`\r\n` 换行符 + 高频中文字符短文本，patch 模糊匹配策略易失效
- **可靠替代**：Python 临时脚本原地替换

  ```python
  # .tmp_fix.py 模板
  with open('target.md', 'r', encoding='utf-8') as f:
      c = f.read()
  assert old_text in c
  c = c.replace(old_text, new_text)
  with open('target.md', 'w', encoding='utf-8') as f:
      f.write(c)
  ```
  工作流：write_file写.tmp_fix.py → python执行 → Remove-Item清理

- **替代方案 B**：write_file 整体重写（适合大段改动）
