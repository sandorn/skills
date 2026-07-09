# MCP 服务迁移最佳实践（Skill自包含改造）
## 适用场景
Skill依赖自定义MCP服务，当前MCP托管在LiteLLM全局servers目录，需要实现Skill 100%自包含、零全局依赖、按需加载。

## 迁移步骤
1. **目录结构调整**
   - 在Skill根目录下新建`mcp/`子目录
   - 将对应MCP服务的完整目录整体移动到`mcp/`下
   
2. **环境变量隔离**
   - 从全局`~/.litellm/servers/.env`中提取该MCP专属的环境变量
   - 在Skill根目录新建`.env`文件存放专属配置
   - 修改MCP代码，将.env加载路径改为相对Skill根目录的路径：
     ```python
     SKILL_ROOT = Path(__file__).resolve().parent.parent
     load_dotenv(SKILL_ROOT / ".env")
     ```

3. **通用注册工具开发**
   - 在Skill的`scripts/`目录下新增`mcp_utils.py`通用工具，封装MCP检查、注册逻辑
   - 注册时使用`--session-only`参数，仅当前Hermes会话生效，重启自动清理，无全局配置残留

4. **入口适配**
   - 在所有Skill Python入口脚本开头添加自动注册逻辑：
     ```python
     from scripts.mcp_utils import ensure_mcps_ready
     ensure_mcps_ready()
     ```
   - 修正所有脚本中硬编码的旧MCP路径为Skill内相对路径

5. **全局清理**
   - 删除LiteLLM `config.yaml`中对应MCP的旧配置节点
   - 重启LiteLLM避免注册冲突

## 核心原则
✅ 完全自包含：所有依赖封闭在Skill目录内，迁移/共享仅需复制单个目录
✅ 零全局配置：无需修改Hermes/LiteLLM任何全局配置，开箱即用
✅ 按需加载：仅调用功能时自动注册MCP，闲置自动回收进程，零资源浪费
✅ 兼容原有体验：调用方式、参数、输出结果与迁移前100%一致
