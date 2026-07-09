# Skill专属MCP自包含改造指南
## 改造背景
原MCP服务存放在LiteLLM全局`servers/`目录下，和Skill强耦合，迁移/升级/共享不便，依赖全局配置，卸载/迁移容易漏删残留文件，版本不同步。
## 改造方案
1. **目录迁移**：在Skill根目录下创建`mcp/`目录，将所有Skill专属MCP服务整体迁移到该目录下
2. **路径适配**：所有硬编码的MCP路径改为Skill相对路径，使用`Path(__file__)`动态适配根目录，避免硬编码全局路径
3. **动态注册**：开发通用`mcp_utils.py`工具库，实现MCP按需自动注册，仅当前Hermes会话生效，无全局配置污染
4. **环境隔离**：将MCP专属环境变量从全局`.env`移动到Skill根目录的`.env`，MCP自动读取上级目录配置
## 适配要点
### Hermes MCP注册参数坑点
Hermes `mcp add`命令不支持`--cwd`、`--env-file`、`--session-only`参数，需要用PowerShell封装启动命令切换工作目录：
```powershell
hermes mcp add <mcp-name> --command powershell.exe --args -Command 'cd "<mcp-dir>" & python "<server-script.py>"'
```
### 路径适配示例
```python
# 错误：硬编码全局路径，无法迁移
DOUBAO = Path(r"C:\Users\Administrator\.litellm\servers\novel-doubao\doubao_server.py")
# 正确：动态适配Skill相对路径，任意环境可用
SKILL_ROOT = Path(__file__).parent.parent
DOUBAO = SKILL_ROOT / "mcp" / "novel-doubao" / "doubao_server.py"
```
## 最终收益
- 100% Skill自包含，迁移/共享仅需复制Skill目录，无额外配置，开箱即用
- 按需启动，闲置MCP进程被Hermes自动回收，零资源浪费
- 环境完全隔离，和其他全局MCP配置无冲突
- 版本完全同步，MCP代码随Skill一起提交Git，无版本不匹配问题