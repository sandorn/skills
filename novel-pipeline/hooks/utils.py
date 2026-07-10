"""
Hook 共享工具（v3.4 精简版）

职责收窄：novel-pipeline 只做生成/润色，不再持有状态。
本模块只保留：
  - 环境变量加载 (load_dotenv / get_path)
  - 章节文件命名 (chapter_filename)
  - 项目根查找 (find_project_root，只识别，不管 state)
  - MCP 调用基类 (BaseMCPClient)
"""
import sys
import os
import json
import subprocess
import time
import logging
import queue
import threading
from pathlib import Path
from typing import Any, Optional, Dict, List, Union

# ==================== 基础配置 ====================
SKILL_DIR = Path(__file__).resolve().parent.parent

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("novel-pipeline")


# ==================== 环境变量加载 ====================
def load_dotenv(key: str) -> str:
    """
    读取环境变量，优先级：skill本地.env → 系统环境变量
    :param key: 环境变量名
    :return: 环境变量值，不存在则返回空字符串
    """
    # 优先级 1: Skill 本地 .env
    skill_dotenv = SKILL_DIR / ".env"
    if skill_dotenv.exists():
        for line in skill_dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")

    # 优先级 2: 系统环境变量（兜底）
    return os.environ.get(key, "")


def get_path(key: str, default: str) -> Path:
    """
    获取配置路径，优先级：skill本地.env → 系统环境变量 → 默认值
    """
    val = load_dotenv(key)
    if val:
        return Path(val)
    return Path(default)


# ==================== 共享路径配置 ====================
# MCP 子进程 Python 解释器（优先 PIPELINE_PYTHON，兼容旧变量名 HERMES_PYTHON，最后回退当前解释器）
_python_env = load_dotenv("PIPELINE_PYTHON") or load_dotenv("HERMES_PYTHON") or sys.executable
PIPELINE_PYTHON = Path(_python_env)
# 默认小说项目章节目录
DEFAULT_CHAPTERS_DIR = get_path("CHAPTERS_DIR", str(Path.cwd() / "chapters"))


# ==================== 章节文件命名 ====================
# 统一使用三位数补零 + 下划线格式：ch_001.md, ch_010.md, ch_101.md
# （与 writer skill 一致，两个 skill 可读写同一 chapters/ 目录）
CHAPTER_FILENAME_FORMAT = "ch_{:03d}.md"


def chapter_filename(chap_num: int) -> str:
    """返回统一的三位数补零章节文件名（ch_NNN.md）。"""
    return CHAPTER_FILENAME_FORMAT.format(int(chap_num))


# ==================== 项目根目录查找 ====================
# 项目根标识优先级：
#   1. novel.json          — 新版统一标识（推荐）
#   2. writer.json         — writer skill 项目（协作场景）
#   3. novel-pipeline.json — 老版兼容
PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")


def find_project_root() -> Optional[Path]:
    """
    从当前工作目录向上查找项目标记文件（最多 5 层）。
    命中任一 PROJECT_MARKERS 即视为项目根，返回该目录；未命中返回 None。

    v3.4 起本 skill 不再维护项目状态（writer skill 负责），因此不再提供
    find_state_dir() / SKILL_STATE_DIR 等 API。
    """
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents)[:5]:
        for marker in PROJECT_MARKERS:
            if (parent / marker).exists():
                return parent
    return None


# ==================== MCP 调用基类 ====================
class BaseMCPClient:
    """
    MCP 客户端基类，统一处理初始化协议、错误处理、资源管理。
    所有 MCP 调用都应该使用这个基类，避免代码重复。

    使用示例:
        with BaseMCPClient(["python", "server.py"], timeout=60) as client:
            result = client.call_tool("tool_name", {"arg": "value"})
    """

    def __init__(
        self,
        command: List[Union[str, Path]],
        timeout: int = 60,
        cwd: Optional[Path] = None,
        client_name: str = "novel-pipeline",
        client_version: str = "2.0"
    ):
        self.command = [str(c) for c in command]
        self.timeout = timeout
        self.cwd = str(cwd) if cwd else None
        self.client_name = client_name
        self.client_version = client_version
        self.proc: Optional[subprocess.Popen] = None
        self._initialized = False

    def _read_line_with_timeout(self, timeout: float) -> Optional[str]:
        """带超时读取一行输出，使用队列+线程避免死锁"""
        if not self.proc or not self.proc.stdout:
            return None

        q: queue.Queue[Optional[str]] = queue.Queue(maxsize=1)

        def _reader():
            try:
                line = self.proc.stdout.readline()
                q.put(line)
            except Exception:
                q.put(None)

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if not q.empty():
            return q.get()
        return None

    def _wait_for_response(self, request_id: int, timeout: Optional[int] = None) -> Dict[str, Any]:
        """等待指定 ID 的 JSON-RPC 响应"""
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            line = self._read_line_with_timeout(0.5)
            if not line:
                continue
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                msg = json.loads(line)
                if msg.get("id") == request_id:
                    return msg
            except json.JSONDecodeError:
                continue
        return {"error": {"code": -32000, "message": f"Timeout waiting for response id={request_id}"}}

    def start(self) -> bool:
        """
        启动 MCP 服务并执行初始化握手。
        :return: 初始化成功返回 True，失败返回 False
        """
        if self.proc is not None:
            return True

        try:
            self.proc = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=self.cwd,
                encoding="utf-8",
                errors="replace"
            )

            # 发送 initialize 请求
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": self.client_name, "version": self.client_version}
                }
            }
            self.proc.stdin.write(json.dumps(init_req) + "\n")
            self.proc.stdin.flush()

            # 等待 initialize 响应
            init_resp = self._wait_for_response(1, timeout=15)
            if "error" in init_resp:
                logger.error(f"MCP initialize failed: {init_resp['error']}")
                self.close()
                return False

            # 发送 initialized 通知
            initialized = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            self.proc.stdin.write(json.dumps(initialized) + "\n")
            self.proc.stdin.flush()

            time.sleep(0.3)  # 给服务一点时间准备
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"MCP start exception: {e}")
            self.close()
            return False

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        :param tool_name: 工具名称
        :param arguments: 工具参数字典
        :return: 响应字典，包含 success/data 或 error
        """
        if not self._initialized and not self.start():
            return {"success": False, "error": "MCP initialization failed"}

        if not self.proc or not self.proc.stdin:
            return {"success": False, "error": "MCP process not running"}

        try:
            call_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }
            self.proc.stdin.write(json.dumps(call_req) + "\n")
            self.proc.stdin.flush()

            resp = self._wait_for_response(2, timeout=self.timeout)

            if "error" in resp:
                return {"success": False, "error": str(resp["error"])}

            if "result" in resp and "content" in resp["result"]:
                for c in resp["result"]["content"]:
                    if c.get("type") == "text":
                        return {"success": True, "data": c["text"]}
                return {"success": True, "data": resp["result"]}

            return {"success": False, "error": "Unexpected response format", "raw": resp}

        except Exception as e:
            logger.error(f"MCP call_tool exception: {e}")
            return {"success": False, "error": str(e)}

    def close(self) -> None:
        """
        关闭 MCP 进程，确保资源正确释放。
        总是可以安全调用，即使进程已经关闭。
        """
        if self.proc is None:
            return

        try:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass

            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=2)
        except Exception as e:
            logger.debug(f"Error closing MCP process (harmless): {e}")
        finally:
            self.proc = None
            self._initialized = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
