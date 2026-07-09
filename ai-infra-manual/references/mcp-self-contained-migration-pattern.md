# MCP 自包含迁移标准模式
## 适用场景
LiteLLM 托管的业务专属 MCP 迁移到 Skill 内部，实现零全局依赖、按需加载、全自包含打包。
## 迁移标准流程
### 1. 目录结构改造
```
<skill-root>/
├─ mcp/                  # Skill专属MCP根目录
│  ├─ <service-1>/       # 单个MCP服务目录
│  │  └─ server.py       # 服务入口
│  └─ <service-2>/
│     └─ server.py
├─ .env                  # Skill专属环境变量，所有MCP共享
├─ scripts/
│  └─ mcp_utils.py       # 通用动态注册工具
└─ SKILL.md
```
### 2. MCP 代码适配
#### 环境变量加载方案（优先读取Skill本地.env）
```python
from pathlib import Path
# 自动定位Skill根目录
SKILL_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = SKILL_DIR / ".env"
# 强制读取本地.env优先级最高
if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().strip("\\\"'")
            os.environ[k] = v
```
#### 路径修正
所有硬编码的 `~/.litellm/servers/` 路径替换为 Skill 内相对路径：
```python
# 旧写法
DOUBAO_PATH = Path(r"C:\Users\Administrator\.litellm\servers\novel-doubao\doubao_server.py")
# 新写法
SKILL_ROOT = Path(__file__).parent.parent
DOUBAO_PATH = SKILL_ROOT / "mcp" / "novel-doubao" / "doubao_server.py"
```
### 3. 动态注册工具模板 (scripts/mcp_utils.py)
```python
import subprocess
import sys
import time
from pathlib import Path
SKILL_ROOT = Path(__file__).parent.parent
def load_env():
    """加载Skill根目录.env到环境变量"""
    env = {}
    env_path = SKILL_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\\\"'")
    return env
def check_mcp_registered(mcp_name: str) -> bool:
    """检查MCP是否已注册到当前Hermes会话"""
    try:
        res = subprocess.run(["hermes", "mcp", "list"], capture_output=True, text=True, timeout=10)
        return mcp_name in res.stdout
    except:
        return False
def register_mcp(mcp_name: str, server_dir: str, script_name: str) -> bool:
    """动态注册MCP，仅当前会话有效，重启自动清理"""
    server_path = SKILL_ROOT / "mcp" / server_dir / script_name
    cwd = SKILL_ROOT / "mcp" / server_dir
    env = load_env()
    # Windows下通过cmd封装环境变量
    env_str = " && ".join([f"set {k}={v}" for k, v in env.items()])
    start_cmd = f"{env_str} && \"{sys.executable}\" \"{server_path}\""
    try:
        subprocess.run(
            [
                "hermes", "mcp", "add",
                mcp_name,
                "--command", "cmd.exe",
                "--args", "/c", start_cmd
            ],
            check=True,
            capture_output=True,
            timeout=30
        )
        time.sleep(3)
        return True
    except Exception as e:
        print(f"⚠️ MCP {mcp_name} 注册失败: {str(e)}", file=sys.stderr)
        return False
def ensure_mcps_ready(required_mcps: list) -> bool:
    """入口调用前确保所有依赖MCP已注册"""
    all_ready = True
    for name, dir_name, script in required_mcps:
        if not check_mcp_registered(name):
            print(f"🔧 自动注册依赖MCP服务：{name}")
            if not register_mcp(name, dir_name, script):
                print(f"❌ 依赖MCP {name} 注册失败", file=sys.stderr)
                all_ready = False
    return all_ready
```
### 4. 入口脚本集成
在所有需要调用MCP的入口脚本开头添加：
```python
# 导入动态注册工具
sys.path.insert(0, str(Path(__file__).parent))
from mcp_utils import ensure_mcps_ready
# 启动前检查注册
if not ensure_mcps_ready([
    ("novel-doubao", "novel-doubao", "doubao_server.py"),
    ("novel-deepseek", "novel-deepseek", "deepseek_server.py")
]):
    sys.exit(1)
```
### 5. 清理旧配置
删除 LiteLLM config.yaml 中对应的 MCP 节点，重启 LiteLLM 避免冲突。
## 迁移后收益
1. ✅ 完全自包含：所有代码、配置、服务均在Skill目录内
2. ✅ 零全局污染：不需要修改任何Hermes/LiteLLM全局配置
3. ✅ 按需加载：仅调用时启动MCP，闲置自动回收不占资源
4. ✅ 易迁移：复制Skill目录即可在其他环境开箱即用
## 常见坑点规避
1. ❌ 禁止使用hermes mcp add的--session-only参数（部分版本不支持）
2. ❌ 禁止依赖系统环境变量，所有配置均写入Skill内.env
3. ❌ 禁止在MCP代码中使用硬编码的绝对路径，全部使用相对Skill根目录的路径
4. ❌ 禁止修改全局公共MCP代码，业务专属MCP全部收敛到Skill内部
