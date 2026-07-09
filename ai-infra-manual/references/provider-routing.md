# 多 Provider 路由配置

## 常用 Provider 清单
| 名称 | API Base |
|------|----------|
| DeepSeek | https://api.deepseek.com/v1 |
| 智谱 GLM | https://open.bigmodel.cn/api/paas/v4 |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 豆包 (Volc Ark) 后付费 | https://ark.cn-beijing.volces.com/api/v3 |
| 豆包 (Volc Ark) Plan 预付费 | https://ark.cn-beijing.volces.com/api/plan/v3 |
| apikey.fun | https://api.apikey.fun/v1 |

### ⚠️ 豆包 (Volcengine Ark) 配置要点
豆包模型通过 OpenAI 兼容 API 接入，关键约束：**model 字段必须加 `openai/` 前缀**，否则 litellm 无法识别路由。

**配置模板：**
```yaml
# 后付费模式
- model_name: doubao-turbo
  litellm_params:
      model: openai/<endpoint-id>          # ← 必须 openai/ 前缀
      api_base: https://ark.cn-beijing.volces.com/api/v3
      api_key: os.environ/VOLC_ARK_KEY

# Plan 预付费模式（auto）
- model_name: doubao-evolving
  litellm_params:
      model: openai/<endpoint-id>          # ← 同样必须 openai/ 前缀
      api_base: https://ark.cn-beijing.volces.com/api/plan/v3
      api_key: os.environ/VOLC_ARK_PLAN_KEY
```

**常见错误：** `model: ark-code-latest` 或 `model: doubao-seed-...` 裸写 endpoint ID 不加前缀 → litellm 返回 "model not recognized"。加 `openai/` 前缀即可修复。

---

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