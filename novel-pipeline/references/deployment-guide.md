# novel-pipeline 部署指南
---
## 一、前置依赖
- LiteLLM网关已部署（默认端口4000，可自定义）
- 按需部署MCP服务：初稿生成/润色/质检/记忆类服务
- 全局环境变量配置文件`~/.litellm/servers/.env`已配置所有API Key，参考`env-template.md`

---
## 二、Skill部署步骤
1. **放置Skill文件**
   将novel-pipeline目录放置到Hermes技能目录下，默认路径：
   - 用户级：`C:\Users\<用户名>\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home\skills\`
   - 或传统路径：`C:\Users\<用户名>\.agents\skills\`
2. **验证加载**
   执行`/new`开启新会话，调用`skill_view(name="novel-pipeline")`确认加载正常

---
## 三、MCP客户端配置规则
| 客户端 | 小说MCP保留策略 |
|--------|----------------|
| Hermes | ✅ 全部保留，流水线正常运行 |
| Claude Desktop | ✅ 按需保留，支持Claude端写作 |
| Continue/VS Code/CodeBuddy等开发客户端 | ❌ 按需移除，精简开发场景配置 |

---
## 四、项目初始化
1. 新建小说项目目录
2. 复制模板配置：`copy <Skill路径>\state-files\config.example.json ./novel-pipeline.json`
3. 编辑配置文件，选择存储模式：
   - 本地文件模式：`"state_storage_mode": "local_file"`
   - MCP记忆体模式：`"state_storage_mode": "mcp_memory"`
4. 复制状态模板文件到项目`state-files/`目录
5. 执行`python <Skill路径>\hooks\load_state.py`验证状态加载正常
