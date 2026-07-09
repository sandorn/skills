# Skill专属MCP最佳实践
## 一、MCP分类管理规范
| 分类 | 存放路径 | 适用场景 |
|------|----------|----------|
| 通用公共MCP | `~/.litellm/servers/` | 系统级、多Skill共用的服务（如browser、windows-admin、通用文件处理等） |
| Skill专属MCP | `对应Skill根目录/mcp/` | 仅为单个Skill服务的业务逻辑类MCP（如网文写作服务、特定领域处理服务等） |
## 二、专属MCP部署原则
1. ✅ 100%自包含：所有MCP代码、环境变量、依赖完全封闭在Skill目录内，与全局环境零耦合
2. ✅ 版本同步：MCP代码与Skill代码一起提交Git，避免版本不匹配问题
3. ✅ 环境隔离：专属MCP使用Skill根目录下的`.env`配置，不与全局配置冲突
4. ❌ 禁止：专属MCP存放在LiteLLM全局servers目录，导致迁移/卸载困难
## 三、加载方案对比
| 方案 | 适用场景 | 优势 | 劣势 |
|------|----------|------|------|
| 静态全局注册 | 高频使用的MCP | 调用无感知，无需额外逻辑 | 需要修改Hermes全局配置，后台常驻占用资源 |
| 动态按需加载 | 低频次使用/开发调试场景 | 完全按需启动，零全局配置依赖，修改后自动重载 | 需要在Skill入口添加自动注册逻辑 |
## 四、动态加载实现模板（Python）
在Skill核心入口脚本开头添加以下逻辑，实现首次调用自动注册MCP，仅当前会话生效：
```python
import subprocess
import sys
import time
from pathlib import Path
SKILL_ROOT = Path(__file__).parent.parent
def _check_mcp_registered(mcp_name: str) -> bool:
    """检查MCP是否已注册"""
    try:
        res = subprocess.run(
            ["hermes", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return mcp_name in res.stdout if res.returncode == 0 else False
    except Exception:
        return False
def _register_mcp(mcp_name: str, server_dir: str, script_name: str) -> bool:
    """动态注册MCP到当前会话"""
    server_path = SKILL_ROOT / "mcp" / server_dir / script_name
    cwd = SKILL_ROOT / "mcp" / server_dir
    env_path = SKILL_ROOT / ".env"
    try:
        subprocess.run(
            [
                "hermes", "mcp", "add",
                "--name", mcp_name,
                "--command", sys.executable,
                "--args", str(server_path),
                "--cwd", str(cwd),
                "--env-file", str(env_path),
                "--session-only"
            ],
            check=True,
            capture_output=True,
            timeout=30
        )
        time.sleep(2)
        return True
    except Exception as e:
        print(f"⚠️ MCP {mcp_name} 注册失败：{str(e)}", file=sys.stderr)
        return False
# 前置检查注册
REQUIRED_MCPS = [
    ("mcp-name", "mcp-dir-name", "server_script.py")
]
for name, dir_name, script in REQUIRED_MCPS:
    if not _check_mcp_registered(name):
        print(f"🔧 自动注册依赖MCP：{name}")
        if not _register_mcp(name, dir_name, script):
            print(f"❌ 依赖MCP {name} 注册失败", file=sys.stderr)
            sys.exit(1)
```
## 五、从LiteLLM迁移到Skill内的标准步骤
1. 在Skill根目录创建`mcp/`目录，将专属MCP服务整体移入
2. 提取全局.env中该MCP的专属配置，写入Skill根目录的`.env`
3. 修改MCP代码的.env加载路径，适配Skill内的相对路径
4. 在Skill核心入口脚本添加上述自动注册逻辑
5. 删除LiteLLM配置中对应的MCP节点，重启LiteLLM避免冲突
6. 测试功能验证正常
