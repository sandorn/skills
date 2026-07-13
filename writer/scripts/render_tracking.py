#!/usr/bin/env python3
# SAFETY: DEPRECATED — v8.4 起停用；调用只打印弃用提示后退出，不修改任何文件。
"""[DEPRECATED · v8.4] tracking/*.md 派生器已停用。

v8.3 时该脚本从 .writer/state/*.json 派生 tracking/{characters,hooks,current_state}.md，
带 <!-- user-edit --> 块保护。v8.4 起小说记忆统一走 novel_project MCP，
tracking/ 派生层整体废除：
  - 结构化状态 → novel_project MCP（用 get_entity_with_relations / search_nodes 查询）
  - 人读快照   → 按需用 report_graph.py 从 MCP + 正文派生
  - 用户规划意图 → 挪到 setting/*.md 的 <!-- user-edit --> 块

保留本 stub 以避免旧路由/文档链接调用时抛 FileNotFoundError；
不再由写章管线（write.md Step 5 / review-cycle.md Step 4）自动触发。

下一步：
- 权威规范    → references/memory-mcp.md
- 治理规则    → references/memory-governance.md
- 归档工具    → scripts/archive_facts.py（生成 MCP tool-call payload）
- 老项目迁移  → scripts/import_state_to_mcp.py
"""
import sys


def main() -> int:
    msg = (
        "[render_tracking.py DEPRECATED · v8.4]\n"
        "  tracking/*.md 派生层已废；小说记忆统一由 novel_project MCP 管理。\n"
        "  - 查询：调 MCP get_entity_with_relations / search_nodes\n"
        "  - 归档：scripts/archive_facts.py 生成 MCP tool-call payload → Agent 调 MCP\n"
        "  - 老项目一次性迁移：scripts/import_state_to_mcp.py\n"
        "  - 权威规范：references/memory-mcp.md\n"
        "本脚本不再做任何文件操作。"
    )
    print(msg, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
