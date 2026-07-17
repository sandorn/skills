"""Writer Skill 核心纯函数单元测试。

运行: python -m pytest scripts/tests/ -v
或直接: python scripts/tests/test_core.py

环境要求: Python 3.9+

注：v8.3 起润色能力已迁移到 novel-pipeline skill，
    writer/scripts/polish.py 已删除；文风预设仍在 writer/references/presets/。
"""

import sys
import os
import unittest

# 将 scripts/ 目录加入 path
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)


class TestCountChinese(unittest.TestCase):
    """中文字数统计 — 被多个脚本使用的核心函数"""

    def _count(self, text):
        from split_paragraphs import count_chinese
        return count_chinese(text)

    def test_pure_chinese(self):
        self.assertEqual(self._count("你好世界"), 4)

    def test_mixed_with_english(self):
        self.assertEqual(self._count("Hello世界ABC"), 2)

    def test_punctuation_not_counted(self):
        self.assertEqual(self._count("你好！世界？"), 4)

    def test_numbers_not_counted(self):
        self.assertEqual(self._count("第123章 测试"), 4)

    def test_empty(self):
        self.assertEqual(self._count(""), 0)

    def test_extended_chinese(self):
        """split_paragraphs.py 的 regex 覆盖基本汉字 + 扩展 CJK-A 区。"""
        # 基本区: 一(U+4E00) 到 鿿(U+9FFF)
        self.assertEqual(self._count("一鿿"), 2)


class TestSplitParagraphs(unittest.TestCase):
    """段落拆分核心逻辑"""

    def test_split_long_paragraph(self):
        from split_paragraphs import split_full_text, count_chinese
        text = "这是一段。这是第二句。这是第三句需要拆分。这是第四句以便超过限制。这是第五句让它更长一些。"
        result = split_full_text(text, max_chars=15)
        for line in result.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("「"):
                self.assertLessEqual(count_chinese(stripped), 42)


class TestIsDialogueLine(unittest.TestCase):
    """对话行检测"""

    def test_corner_bracket(self):
        from split_paragraphs import is_dialogue_line
        self.assertTrue(is_dialogue_line("「你好。」"))

    def test_double_corner(self):
        from split_paragraphs import is_dialogue_line
        self.assertTrue(is_dialogue_line("『注意！』"))

    def test_normal_line(self):
        from split_paragraphs import is_dialogue_line
        self.assertFalse(is_dialogue_line("这是一个普通的句子。"))


class TestAuditB11(unittest.TestCase):
    """B11 Markdown 格式零容忍"""

    def test_markdown_bold_is_blocking(self):
        from audit import audit_text
        text = "# 第1章\n\n这是正文。\n\n**这里不该加粗**。"
        passed, issues, _cn, _fixed = audit_text(text)
        self.assertFalse(passed)
        self.assertTrue(any("MD加粗" in issue for issue in issues))

    def test_body_heading_is_blocking_but_first_title_is_allowed(self):
        from audit import audit_text
        text = "# 第1章\n\n这是正文。\n\n## 正文里不该有二级标题\n\n继续正文。"
        passed, issues, _cn, _fixed = audit_text(text)
        self.assertFalse(passed)
        self.assertTrue(any("MD正文标题" in issue for issue in issues))


class TestArchiveFactsPayload(unittest.TestCase):
    """archive_facts.py 只生成 MCP tool call，不写本地 JSON。"""

    def test_character_calls_use_read_before_write(self):
        from archive_facts import build_character_calls
        reads, writes = build_character_calls([
            {
                "name": "苏白",
                "cultivation": "练气四层",
                "current_location": "青云门",
                "recent_changes": ["遇到老周"],
                "factions": ["青云门"],
            }
        ], chapter=12)

        self.assertEqual(reads[0]["phase"], "read")
        self.assertEqual(reads[0]["tool"], "get_entity_with_relations")
        self.assertEqual(writes[0]["phase"], "write")
        self.assertEqual(writes[0]["tool"], "create_entities")
        entity = writes[0]["args"]["entities"][0]
        self.assertEqual(entity["name"], "苏白")
        self.assertIn("<merge_with_old>", entity["observations"])
        self.assertIn("ch012: 修为 练气四层", entity["observations"])
        self.assertEqual(writes[1]["tool"], "create_relations")


if __name__ == "__main__":
    unittest.main(verbosity=2)
