"""
Hook 共享工具
项目隔离查找：优先使用当前项目目录下的 state-files，回退到 Skill 模板。
"""
import os, json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_STATE_DIR = SKILL_DIR / "state-files"


def find_state_dir() -> Path:
    """
    从当前工作目录向上查找 novel-pipeline.json 项目标记文件。
    找到 → 返回项目的 state-files/ 目录
    未找到 → 返回 Skill 模板目录（只读回退）
    """
    cwd = Path.cwd()
    # 向上搜索，最多 5 层
    for parent in [cwd] + list(cwd.parents)[:5]:
        marker = parent / "novel-pipeline.json"
        if marker.exists():
            proj_state = parent / "state-files"
            if proj_state.exists():
                return proj_state
            # 如果标记文件存在但 state-files 不存在，创建它
            proj_state.mkdir(parents=True, exist_ok=True)
            return proj_state

    # 回退到 Skill 模板目录
    return SKILL_STATE_DIR


def load_dotenv(key: str) -> str:
    """
    读取环境变量优先级：
    1. 系统环境变量
    2. ~/.litellm/servers/.env（全局优先，统一配置）
    3. skill目录下的.env（保底兜底）
    """
    val = os.environ.get(key, "")
    if val:
        return val
    # 优先读取全局配置
    global_dotenv = Path.home() / ".litellm" / "servers" / ".env"
    if global_dotenv.exists():
        for line in global_dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")
    # 兜底读取skill本地配置
    skill_dotenv = SKILL_DIR / ".env"
    if skill_dotenv.exists():
        for line in skill_dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")
    return ""
