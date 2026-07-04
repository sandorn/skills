"""
模板A: DeepSeek-V4-PRO 初稿生成请求模板
============================================
模块4 — 脚本可直接调用的标准请求构建器。
MCP Server 内部使用，也可被外部 PowerShell/Python 脚本独立调用。

可插入变量:
  - global_setting: 本章相关的世界观摘要
  - chapter_outline: 本章细纲
  - chapter_number: 章节编号
  - revision_instructions: 修订指令（可选，首次生成留空）
"""

DRAFT_USER_TEMPLATE = """【章节号】第{chapter_number}章

【世界观设定（本章相关）】
{global_setting}

【本章细纲】
{chapter_outline}{revision_section}

【指令】
根据以上大纲和设定，撰写本章完整草稿。
要求：
1. 严格遵循大纲情节线，不自行添加新情节
2. 对话使用「」
3. 段落简短，每段不超过42字
4. 章末必须有悬念/钩子
5. 纯章节文本，不要任何分析或说明"""


def build_draft_request(
    global_setting: str,
    chapter_outline: str,
    chapter_number: int,
    revision_instructions: str = "",
) -> str:
    """
    构建 DeepSeek 初稿生成的用户消息。

    Args:
        global_setting: 本章相关世界观摘要（势力分布/地理/当前局势）
        chapter_outline: 本章细纲（包含关键剧情点/角色行为/伏笔要求）
        chapter_number: 章节编号
        revision_instructions: 修订指令（首次生成留空，重生成时填入自检反馈）

    Returns:
        格式化的用户消息文本，可直接作为 API system message 的 user content
    """
    revision_section = ""
    if revision_instructions.strip():
        revision_section = f"\n\n【修改指示——必须逐条执行】\n{revision_instructions}\n"

    return DRAFT_USER_TEMPLATE.format(
        chapter_number=chapter_number,
        global_setting=global_setting,
        chapter_outline=chapter_outline,
        revision_section=revision_section,
    )


# ── 独立调用示例 ──────────────────────────────────────────
if __name__ == "__main__":
    import sys, json

    if len(sys.argv) >= 3:
        # 命令行调用: python draft_request.py "<setting>" "<outline>" [chapter_number]
        setting = sys.argv[1]
        outline = sys.argv[2]
        chapter = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        revision = sys.argv[4] if len(sys.argv) > 4 else ""

        result = build_draft_request(setting, outline, chapter, revision)
        print(json.dumps({"user_message": result}, ensure_ascii=False))
    else:
        # 交互式演示
        print("=" * 60)
        print("模板A: DeepSeek 初稿生成请求构建器")
        print("=" * 60)
        sample = build_draft_request(
            global_setting="青云宗位于青云山脉，当前与血煞门对峙中。主角林尘练气七层。",
            chapter_outline="1.林尘在后山修炼发现神秘玉佩异动 2.遭遇血煞门探子 3.战斗中玉佩觉醒 4.击退探子但暴露位置",
            chapter_number=5,
            revision_instructions="",
        )
        print(sample)
        print("=" * 60)
        print("模块可被 MCP Server import 或外部脚本独立调用")
