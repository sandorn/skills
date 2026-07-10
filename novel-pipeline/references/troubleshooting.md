# novel-pipeline 故障排查

## MCP 服务未加载
1. 执行 `python <Skill路径>/scripts/verify_env.py` 检查环境
2. 手动注册：进入 hermes 会话后执行 `python <Skill路径>/scripts/polish_chapter.py 1 ./chapters` 触发首次自动注册
3. `hermes mcp list` 应能看到 `novel-doubao` / `novel-deepseek`

## generate_draft / polish_chapter 报 "环境变量未配置" 退出
- 检查 Skill 本地 `.env`（`<Skill路径>\.env`）是否存在
- 检查 6 个必需 KEY：`DEEPSEEK_{API_KEY,BASE_URL,MODEL}` + `DOUBAO_{API_KEY,BASE_URL,MODEL}`
- server 无内置默认值，缺一即报错

## polish_chapter 返回 API 错误
- 检查 `.env` 中 `DOUBAO_API_KEY` 是否有效
- `DOUBAO_BASE_URL` 允许含或不含 `/chat/completions`，代码自动判断，不会双拼路径

## 章节文件路径解析失败
- 统一命名格式：`ch001.md`、`ch010.md`、`ch101.md`（三位数补零）
- `hooks/utils.py::chapter_filename(n)` 是唯一入口，禁止硬编码 `f"ch{n:02d}.md"` 类字符串

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
      [sys.executable, r'<Skill路径>\hooks\archive_state.py'],
      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  stdout, stderr = proc.communicate(input=payload, timeout=30)
  print(stdout.decode('utf-8'))
  ```

## patch 工具在中文 .md 章节文件上失败
- **现象**：`patch` 在 `.md` 文件上持续返回 "Could not find a match"，即使文本肉眼可见匹配
- **根因**：`\r\n` 换行符 + 高频中文字符短文本，patch 模糊匹配策略易失效
- **可靠替代**：Python 临时脚本原地替换

  ```python
  with open('target.md', 'r', encoding='utf-8') as f:
      c = f.read()
  assert old_text in c
  c = c.replace(old_text, new_text)
  with open('target.md', 'w', encoding='utf-8') as f:
      f.write(c)
  ```
