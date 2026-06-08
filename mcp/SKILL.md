---
name: mcp
description: MCP 服务器设计/构建/调试 — 支持 stdio 和 HTTP/SSE 传输。触发词：创建MCP、mcp server、debug mcp、mcp tools、mcp validate。

tags: [mcp,server,configuration,stdio,sse]
category: development
---

# MCP — Model Context Protocol 管理

## 设计规则
- 本地工具优先 stdio，远程服务用 HTTP/SSE
- Tool schema 精简、有类型、返回结构化 JSON
- 凭据放环境变量，不硬编码进配置
- HTTP/SSE 客户端默认带 `Accept: application/json, text/event-stream`
- 外部 API 加超时和清晰错误信息

## DeepSeek 命令

```bash
deepseek mcp init
deepseek mcp add my-server --command node --arg server.js
deepseek mcp add remote-server --url http://127.0.0.1:3000/mcp
deepseek mcp list
deepseek mcp validate
deepseek mcp tools
```

HTTP/SSE 条目可在 `~/.deepseek/mcp.json` 中添加 per-server headers。

## 工作流
1. 定义服务边界和最小工具集
2. 选择传输方式和凭据处理方案
3. 用 MCP SDK 实现服务端
4. `deepseek mcp add` 或编辑 `~/.deepseek/mcp.json`
5. `deepseek mcp validate` → `deepseek mcp tools`
6. 测试一条 happy path + 一条 failure path
