# novel-pipeline 故障排查

## MCP 工具未发现
- 执行 `/reload-mcp` 或 `/new` 新会话

## generate_draft 返回错误
- 检查 `~/.litellm/servers/.env` 中对应模型 API Key 是否有效
- 确认 LiteLLM 网关已启动（`http://127.0.0.1:4000/health`）

## polish_chapter 返回错误
- 检查 `.env` 中润色模型 API Key 是否有效

## 检查点脚本报错（ImportError）
- 运行 `python scripts/verify_env.py` 诊断缺失包
- 手动补充：`pip install httpx mcp`

## state-files 加载失败
- 确认 `state-files/` 目录存在且 JSON 格式有效
- 运行 `python hooks/load_state.py` 查看具体错误

## PowerShell stdin BOM 错误
- PowerShell 5.1 管道传 JSON 会自动添加 BOM
- 用写临时文件后重定向代替 `echo` 管道

## publishready 首次调用慢
- `npx -y @veldica/publishready-mcp` 首次运行需下载数百 MB 包
- 提前预热：终端执行 `npx -y @veldica/publishready-mcp --version`
