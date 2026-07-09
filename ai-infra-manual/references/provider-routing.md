# 多 Provider 路由配置

当前场景：**主对话直连 DeepSeek**，**辅助任务 + 委派子代理走本地 LiteLLM 网关**。

## 路由域一览

| 路由域 | 用途 | 配置路径 |
|--------|------|----------|
| **主模型** | 当前会话对话 | `model.*` + `providers.*` |
| **辅助任务**（13 个） | 压缩/视觉/网页提取/技能搜索/审批/MCP 采样等 | `auxiliary.<task>.*` |
| **委派子代理** | delegate_task 子会话 | `delegation.*` |

## 配置命令

对每个辅助任务和委派子代理，设置：
```bash
hermes config set auxiliary.<task>.provider openai
hermes config set auxiliary.<task>.base_url   http://127.0.0.1:4000/v1
hermes config set auxiliary.<task>.api_key    sk-1234
hermes config set auxiliary.<task>.model      deepseek-v4-flash
```

`provider` 固定用 `openai`（LiteLLM 兼容 OpenAI 格式）。

## 完整任务列表

```bash
auxiliary.compression.*
auxiliary.vision.*
auxiliary.web_extract.*
auxiliary.skills_hub.*
auxiliary.approval.*
auxiliary.mcp.*
auxiliary.title_generation.*
auxiliary.triage_specifier.*
auxiliary.curator.*
auxiliary.monitor.*
auxiliary.kanban_decomposer.*
auxiliary.profile_describer.*
auxiliary.tts_audio_tags.*
delegation.*
```

## 验证
```bash
hermes config get auxiliary.compression
```

## 生效条件

配置写入后需 `/new` 重启会话生效。辅助任务配置在会话启动时读取，不支持热重载。
