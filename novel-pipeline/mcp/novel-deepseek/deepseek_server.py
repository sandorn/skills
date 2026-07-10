#!/usr/bin/env python3
"""
DeepSeek Draft Generator MCP Server (stdio transport)
模块2: DeepSeek 专属初稿生成
Tool Description = 模块2全部规则，Claude CLI 读取即加载规则

配置来源（无内置默认值）：
  1. Skill 本地 .env（SKILL_DIR/.env）
  2. 系统环境变量
两级读取均缺失时，立刻报错退出，避免打错误端点。
"""
import os
import sys
import json
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

# Skill 根目录
SKILL_DIR = Path(__file__).resolve().parent.parent.parent


def _read_skill_env() -> dict[str, str]:
    """一次性读取 Skill 本地 .env，返回 dict；文件不存在则返回空 dict。"""
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
    """
    读取环境变量，优先级：skill .env → 系统环境变量。
    两级都缺或值为空 → 立刻退出，不允许使用兜底默认。
    """
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
            "error": {"code": -32000, "message": msg}
        }), file=sys.stderr)
        sys.exit(1)
    return val


# ── 加载配置 ──────────────────────────────────────────────
_skill_env = _read_skill_env()
DEEPSEEK_API_KEY = require_env("DEEPSEEK_API_KEY", _skill_env)
DEEPSEEK_BASE_URL = require_env("DEEPSEEK_BASE_URL", _skill_env).rstrip("/")
DEEPSEEK_MODEL = require_env("DEEPSEEK_MODEL", _skill_env)


# ── System Prompt（发给 DeepSeek 的 system message）─────────
DRAFT_SYSTEM_PROMPT = """你是网文章节草稿生成器。你只产出剧情骨架，不做任何文字润色。

【核心指令】
1. 仅产出平铺直白的剧情叙述。禁止文学修饰、景物描写渲染、心理活动展开。
2. 禁止自主增加爽点、反转、原创细节——严格遵循下发的大纲和设定。
3. 对话用「」括起，每段对话不超过2句。
4. 段落简短，单段不超过42字。
5. 章末必须有悬念/钩子——用一句话暗示下一章的冲突。
6. 纯正文输出，不包含任何分析、总结、建议、元叙事。
7. 字数要求: 严格控制在 2500-4500 字之间，目标 2800-3600 字。低于 2500 字视为不合格，超过 4500 字需截断。

【长线约束】
- 多角色并行推进：每个场景至少涉及2个角色互动。
- 伏笔回收意识：如果大纲中有伏笔标记，必须在正文中体现。
- 修炼/势力体系统一：所有战力描述必须与下发设定一致。

【网文节奏要求】
- 每 3-4 段一个小转折（信息差、实力差、立场差）。
- 每 10 段一个大节奏点（战斗、突破、反转、登场）。
- 章末 90%-95% 位置埋钩子。

【输出格式】
纯章节正文文本。无标题、无编号、无注释。"""

# ── MCP Server ─────────────────────────────────────────────
server = FastMCP(
    name="novel-deepseek",
    instructions="DeepSeek webnovel draft generator. Tool description contains full generation constraints.",
)


@server.tool(
    name="generate_draft",
    description="""[DRAFT GENERATOR — DeepSeek 专属初稿生成]

## 模型定位
你是剧情骨架生成器，不是小说家。产出平铺直白的剧情初稿，所有文笔优化交给后置润色模型。

## 强制行为约束（不可违反）
1. 仅产出平铺直白剧情骨架，禁止修饰词句、景物渲染、心理描写展开
2. 禁止自主增加爽点、反转、新增原创细节——严格遵循下发的大纲
3. 所有文笔优化交给后置润色模型，你只负责情节推进和悬念设置
4. 对话用「」，段落简短（≤42字/段），章末必须有钩子
5. 字数: 2500-4500 字（目标 2800-3600），低于 2500 不合格，超 4500 截断

## 长线剧情逻辑权重
- 优先保证多角色并行推进（每场景≥2角色互动）
- 跨章节伏笔回收意识（大纲中伏笔标记必须体现）
- 修炼/势力体系统一（战力描述必须与设定一致）

## 网文剧情触发库（按需选用）
- 升级冲突: 突破场景、系统通知、战力等级揭示
- 反转铺垫: 看似落败实则布局、隐藏底牌揭示
- 人物登场: 新角色带辨识度特质亮相
- 打斗场面: 明确赌注、回合制推进、环境互动
- 章节收尾: 90-95%处悬念/死亡提问/威胁逼近
- 情绪过渡: 快速胜利→损失、牺牲→觉悟

## 输出格式
纯章节正文文本。无分析、无总结、无建议、无元叙事。直接返回可用正文。

## 输入参数
- global_setting: 本章相关的世界观摘要（势力/地理/规则）
- chapter_outline: 本章细纲（关键剧情点/伏笔要求/角色行为）
- chapter_number: 章节编号
- revision_instructions: 修订指令（空=首次生成，非空=根据反馈重新生成）""",
)
async def generate_draft(
    global_setting: str,
    chapter_outline: str,
    chapter_number: int,
    revision_instructions: str = "",
) -> str:
    """Generate a webnovel chapter draft."""
    revision_section = ""
    if revision_instructions.strip():
        revision_section = f"\n\n【修改指示——必须逐条执行】\n{revision_instructions}\n"

    user_message = f"""【章节号】第{chapter_number}章

【世界观设定（本章相关）】
{global_setting}

【本章细纲】
{chapter_outline}{revision_section}

【指令】
根据以上大纲和设定，撰写本章完整草稿。
严格遵循大纲情节线，不自行添加新情节。
纯章节文本，不要任何分析或说明。"""

    endpoint = DEEPSEEK_BASE_URL if DEEPSEEK_BASE_URL.endswith("chat/completions") else f"{DEEPSEEK_BASE_URL}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.75,
                    "max_tokens": 8192,
                    "thinking": {"type": "disabled"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        return f"ERROR: DeepSeek API 返回错误 {e.response.status_code}: {e.response.text[:500]}"
    except httpx.RequestError as e:
        return f"ERROR: 网络请求失败: {str(e)}"
    except Exception as e:
        return f"ERROR: 未知错误: {str(e)}"


if __name__ == "__main__":
    server.run(transport="stdio")
