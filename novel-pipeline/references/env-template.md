# 环境变量模板
# 统一配置路径：~/.litellm/servers/.env （所有小说类MCP服务共享）
# 优先级：系统环境变量 > 此全局配置 > Skill本地兜底配置

```ini
# ------------------------------
# 1. DeepSeek（初稿生成）
# ------------------------------
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_MODEL=deepseek-v4-flash
# 可选模型：deepseek-v4-pro / deepseek-v4-flash

# ------------------------------
# 2. 豆包/火山引擎方舟（润色）
# ------------------------------
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_API_KEY=ark-your-key-here
# 可选模型（推荐按场景选择）
# DOUBAO_MODEL=doubao-seed-evolving      # 长文本优化版
# DOUBAO_MODEL=doubao-seed-2-1-pro-260628 # 高质量润色
DOUBAO_MODEL=doubao-seed-2-0-pro-260215   # 平衡速度与质量
# DOUBAO_MODEL=doubao-seed-2-1-turbo-260628 # 高速润色

# ------------------------------
# 3. 小说专用MCP服务（本地LiteLLM网关部署）
# ------------------------------
# OOC/人设/剧情/战力校验服务
MCP_FIRSTORY_ENDPOINT=http://127.0.0.1:4000/mcp/firstory
MCP_FIRSTORY_API_KEY=sk-1234

# 全局规则/违禁词/内容审核服务
MCP_UNO_ENDPOINT=http://127.0.0.1:4000/mcp/uno
MCP_UNO_API_KEY=sk-1234

# 出版级质量审计/AI去重/格式标准化服务
MCP_PUBLISHREADY_ENDPOINT=http://127.0.0.1:4000/mcp/publishready
MCP_PUBLISHREADY_API_KEY=sk-1234

# 小说分布式记忆库（状态/人设/伏笔/战力存储）
MCP_MEMORY_NOVEL_ENDPOINT=http://127.0.0.1:4000/mcp/memory_novel
MCP_MEMORY_NOVEL_API_KEY=sk-1234

# ------------------------------
# 4. 流水线全局开关配置
# ------------------------------
# 自动跳过过渡章节润色（true/false）
AUTO_SKIP_TRANSITION_CHAPTERS=true
# 初稿最低字数要求（默认2500）
DRAFT_MIN_LENGTH=2500
# 初稿最高字数限制（默认4500）
DRAFT_MAX_LENGTH=4500
# 最大重试次数（默认2次）
MAX_RETRY_COUNT=2
# 输出章节自动保存到本地文件（true/false）
AUTO_SAVE_CHAPTER=true
```
