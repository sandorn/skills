#!/usr/bin/env python3
"""
Doubao Text Polisher MCP Server (stdio transport)
模块3: 豆包锁定式润色 + 字数控制 + 风格覆盖

配置来源（无内置默认值）：
  1. Skill 本地 .env（SKILL_DIR/.env）
  2. 系统环境变量
两级读取均缺失时立即报错退出。

Tool `polish_chapter` 参数说明：
  - draft_text                     章节原文（必填）
  - style_prompt_override          自定义 system prompt（可选；由 writer skill 传递预设内容，
                                   覆盖 MCP 内嵌的通用锁定式 prompt）
  - min_words / max_words          字数循环下限/上限（可选；0 表示禁用循环）
  - max_wc_retries                 字数不达标时最多重试次数（默认 2）
  - chapter_characters             本章出场角色信息（可选，作为额外上下文）
  - chapter_mood_tone              情绪基调（可选，默认"中性"）

返回：
  - 成功：润色后的完整正文
  - 失败：以 "ERROR:" 前缀开头的错误说明
"""
import os
import sys
import json
import re
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# Skill 根目录
SKILL_DIR = Path(__file__).resolve().parent.parent.parent


def _read_skill_env() -> dict[str, str]:
    env_path = SKILL_DIR / ".env"
    if not env_path.exists():
        return {}
    result: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        result[k.strip()] = v.strip().strip("\"'")
    return result


def require_env(key: str, skill_env: dict[str, str]) -> str:
    val = skill_env.get(key, "").strip()
    if not val:
        val = os.environ.get(key, "").strip()
    if not val:
        msg = (
            f"ERROR: 环境变量 {key} 未配置。\n"
            f"请在以下任一位置提供该值（优先 skill .env）：\n"
            f"  1) {SKILL_DIR / '.env'}\n"
            f"  2) 系统环境变量"
        )
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": msg},
        }), file=sys.stderr)
        sys.exit(1)
    return val


# ── 加载配置 ──────────────────────────────────────────────
_skill_env = _read_skill_env()
DOUBAO_API_KEY = require_env("DOUBAO_API_KEY", _skill_env)
DOUBAO_BASE_URL = require_env("DOUBAO_BASE_URL", _skill_env).rstrip("/")
DOUBAO_MODEL = require_env("DOUBAO_MODEL", _skill_env)


# ── 默认 System Prompt（MCP 内嵌通用锁定式；可被 style_prompt_override 覆盖） ──
DEFAULT_POLISH_SYSTEM_PROMPT = """你是网文润色师。你收到的正文剧情已锁定，你只能做文字层面的优化。
【最高优先级红线——违反即失败】
1. 绝对不能修改剧情、人设、伏笔、战力体系、世界观设定，所有修改仅针对文字表达、流畅度、节奏感、爽感
2. 不能增减剧情内容，原文的对话、动作、场景、情节必须100%保留
3. 不能修改原文的专有名词、人名、地名、功法名、物品名等
4. 绝对不能出现AI写作的生硬套话、空洞描写
【润色规则】
1. 保持原文的叙事风格、语气、节奏不变
2. 优化语句通顺度，修正错别字、语病、不通顺的句子
3. 拆分过长的句子和段落，适配手机阅读，每段控制在2-5行最佳
4. 优化对话的自然度，符合人物身份和性格
5. 适当增加细节描写提升代入感，但不能新增剧情
6. 提升爽点的感染力，强化情绪表达
7. 删除冗余的修饰词、重复的表述
8. 调整语序让读起来更流畅，符合中文阅读习惯
【输出要求】
1. 只输出润色后的完整正文，不需要任何解释、说明、标记
2. 保持原文的段落结构，不要合并或拆分大的段落
3. 原文的标点符号、换行、格式尽量保留，除非明显错误
4. **段落间只用单换行（\\n）分隔，禁止插入空行（\\n\\n）**——网站富文本编辑器按回车分段，空行会导致粘贴后段落被双倍分隔。若原文含空行，一并压缩为单换行。
"""


mcp = FastMCP("novel-doubao")


def _count_chinese(text: str) -> int:
    return len(re.findall(r"[一-鿿㐀-䶿]", text))


def _call_doubao(system_prompt: str, user_content: str) -> tuple[bool, str]:
    """返回 (success, content_or_error_str)。"""
    try:
        headers = {
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": DOUBAO_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            "max_tokens": 16000,
        }
        endpoint = DOUBAO_BASE_URL if DOUBAO_BASE_URL.endswith("chat/completions") else f"{DOUBAO_BASE_URL}/chat/completions"
        response = httpx.post(endpoint, headers=headers, json=payload, timeout=300)
        if response.status_code == 200:
            data = response.json()
            return True, data["choices"][0]["message"]["content"].strip()
        return False, f"API返回错误，状态码：{response.status_code}，内容：{response.text[:300]}"
    except Exception as e:
        import traceback
        return False, f"异常：{str(e)}\n{traceback.format_exc()[:300]}"


@mcp.tool()
def polish_chapter(
    draft_text: str,
    style_prompt_override: str = "",
    min_words: int = 0,
    max_words: int = 0,
    max_wc_retries: int = 2,
    chapter_characters: str = "",
    chapter_mood_tone: str = "中性",
) -> str:
    """
    润色网文章节。默认锁定剧情仅优化文字表达。

    可选：
      - style_prompt_override 传入自定义 system prompt（例如 writer skill 的番茄风预设）
      - min_words/max_words > 0 时启用字数循环，超出范围最多重试 max_wc_retries 次

    返回：润色后正文（成功）或 "ERROR: ..." 字符串（失败）
    """
    system_prompt = style_prompt_override.strip() or DEFAULT_POLISH_SYSTEM_PROMPT

    # 组装用户消息
    base_user = f"请严格遵守润色规则，润色以下章节正文，只输出润色后的内容："
    if chapter_characters.strip():
        base_user += f"\n\n【本章角色】{chapter_characters.strip()}"
    if chapter_mood_tone.strip() and chapter_mood_tone.strip() != "中性":
        base_user += f"\n【情绪基调】{chapter_mood_tone.strip()}"
    base_user += f"\n\n{draft_text}"

    extra_hint = ""
    last_result = ""

    for attempt in range(max_wc_retries + 1):
        ok, content = _call_doubao(system_prompt, base_user + extra_hint)
        if not ok:
            return f"ERROR: {content}"
        last_result = content

        # 未启用字数循环
        if min_words <= 0 and max_words <= 0:
            return last_result

        wc = _count_chinese(last_result)

        # 检查是否达标
        low = min_words if min_words > 0 else None
        high = max_words if max_words > 0 else None
        below = low is not None and wc < low
        above = high is not None and wc > high

        if not below and not above:
            return last_result

        # 已达最大重试
        if attempt >= max_wc_retries:
            return last_result

        # 构造修正提示
        if below:
            extra_hint = (
                f"\n\n【字数修正指令】上一次输出 {wc} 中文字，"
                f"不足下限 {low}（差 {low - wc} 字）。请扩充细节、心理反应、"
                f"感官描写或爽点刻画，确保达到 {low}-{high or low + 500} 字。"
            )
        else:
            extra_hint = (
                f"\n\n【字数修正指令】上一次输出 {wc} 中文字，"
                f"超出上限 {high}（多 {wc - high} 字）。请精简冗余描写和铺垫，"
                f"控制在 {low or high - 500}-{high} 字。"
            )

    return last_result


if __name__ == "__main__":
    mcp.run()
