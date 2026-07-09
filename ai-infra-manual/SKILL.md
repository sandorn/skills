---
name: ai-infra-manual
description: "本地 AI 基础架构运维手册：Hermes 环境、Skill 管理、模型配置、MCP 网关"
version: 2.3.1
---

# 本地 AI 基础架构运维手册

> ⚠ **前置要求**：进行任何 MCP 同步、配置变更、客户端清理前，**必须先加载本 skill**（`skill_view(name="ai-infra-manual")`）。

## 核心架构
```
【唯一源码】~/.agents/skills/  → git: gitee.com/sandorn/skills
【物理存储】AppData\Local\hermes\skills\  → 所有skill通过junction映射到源码目录
【全局共享】CLI/Desktop/Web三个版本的skills目录均联结指向物理存储
```
**目录联结断裂检测：**
```python
for name in os.listdir(skills_dir):
    full = os.path.join(skills_dir, name)
    if os.path.lexists(full) and not os.path.exists(full):
        print(f"Broken: {name}"); os.rmdir(full)
```

---

## 🔴 LiteLLM 高频操作
> 端口: 4000 | 认证: Bearer sk-1234 | v1.90.3 | 核心文件: ~/.litellm/*

### 重启唯一正确命令
```powershell
# 完整重启
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Administrator\.litellm\start.ps1" -Restart
# 仅启动
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Administrator\.litellm\start.ps1"
```
**禁止操作（多次踩坑）：** ❌ 自行写脚本 ❌ 绕WSL ❌ 内联后台 ❌ background=true启动 ❌ 手动安装litellm
**验证就绪：** `curl.exe -s http://127.0.0.1:4000/health/readiness` → 返回 `{"status":"healthy"}`

---

## 核心运维警告
1. **⚠️ LiteLLM必须走start.ps1启动**：直接启动会导致.env未加载，所有模型认证失败
2. **⚠️ 禁止全局search_files扫描**：所有配置路径已明确写在reference中，直接read_file对应路径
3. **⚠️ Hermes config.yaml缩进必须精确**：patch工具会拒绝格式不匹配的写入，编辑后用`python -c "import yaml; yaml.safe_load(open(r'~/.hermes/config.yaml'))"`验证
4. **⚠️ Skill维护操作准则**：进行Skill维护/修改前，必须先完整审计现有Skill目录结构、代码库、入口点，禁止在未了解现有结构的前提下反复要求用户执行手动操作，避免冗余提醒。

---

## 常见错误诊断
### "No connected db" 认证错误
API返回400时，根因为API Key与master_key不匹配：
```bash
# 正确Key → 200 | 错误Key → 400 | 无Key → 401
curl -H "Authorization: Bearer *** http://localhost:4000/v1/models
```
> 注意：`disable_auth: true` 不是v1.90.3有效配置项，无法绕过认证

---

## 📚 详细参考导航（按需加载）
| 分类 | 内容 | 加载方式 |
|------|------|---------|
| **Provider配置** | 所有厂商API地址、豆包特殊配置、多环境路由规则 | `skill_view('ai-infra-manual', 'references/provider-routing.md')` |
| **MCP运维** | MCP命名规则、4客户端同步表、全量同步脚本、排错指南 | `skill_view('ai-infra-manual', 'references/mcp-debugging.md')` |
| **MCP最佳实践** | Skill专属MCP分类规范、动态加载模板、迁移标准流程 | `skill_view('ai-infra-manual', 'references/skill-mcp-best-practices.md')` |
| **MCP自包含改造** | LiteLLM耦合改造、动态注册、零全局依赖打包指南 | `skill_view('ai-infra-manual', 'references/mcp-self-contained-guide.md')` |
| **MCP自包含迁移模板** | 业务专属MCP迁移到Skill内部标准流程、代码模板、坑点规避 | `skill_view('ai-infra-manual', 'references/mcp-self-contained-migration-pattern.md')` |
| **发布流程** | 模型/MCP变更、全量同步、下线标准操作流 | `skill_view('ai-infra-manual', 'references/publishing-workflow.md')` |
| **启动配置** | 多配置策略、SSL证书、环境变量加载、后台启动避坑 | `skill_view('ai-infra-manual', 'references/startup-guide.md')` |
| **配置审计** | 模型清单、MCP服务器清单、一致性验证脚本 | `skill_view('ai-infra-manual', 'references/config-audit.md')` |
| **自定义开发** | FastMCP开发模板、注册流程、.env规范 | `skill_view('ai-infra-manual', 'references/custom-mcp-dev.md')` |
| **工具脚本** | 同步/审计/连通性验证等所有脚本 | `scripts/` 目录 |

---

## 🔧 Skill 维护标准（强制遵守）
1. **单源同步规则**：唯一源码为 `~/.agents/skills/ai-infra-manual/`（gitee仓库托管），本地Hermes技能目录通过Junction软链接指向该路径，禁止直接修改本地路径下的文件
2. **主文件轻量化规则**：`SKILL.md` 仅保留高频操作、核心警告、导航入口，总大小控制在4KB以内，所有详细配置、分步指南、专项说明全部归入 `references/` 目录下对应文件
3. **版本迭代规则**：修改后升级版本号，大变更（结构调整、新增核心规则）升级次版本号，小修正（补充说明、修复笔误）升级修订版本号
