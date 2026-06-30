"""Writer Skill 核心纯函数单元测试。

运行: python -m pytest scripts/tests/ -v
或直接: python scripts/tests/test_core.py

环境要求: Python 3.9+, requests (仅 polish.py 测试需要)
"""

import sys
import os
import unittest

# 将 scripts/ 目录加入 path
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPT_DIR)

# 检测可选依赖
try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class TestCountChinese(unittest.TestCase):
    """中文字数统计 — 被多个脚本使用的核心函数"""

    def _count(self, text):
        # 从各个脚本导入（接口略有不同，以 split_paragraphs 为准）
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
        """split_paragraphs.py 的 regex 覆盖基本汉字 + 扩展 CJK-A 区，
        与 polish.py/audit.py 统一使用同一范围。"""
        from split_paragraphs import count_chinese
        self.assertEqual(count_chinese("你好"), 2)
        # 扩展A区字符 (㐀-䶿) 现在被统计
        self.assertEqual(count_chinese("㐀"), 1)

    def test_novel_text_sample(self):
        text = "张远猛地推开房门，走廊里空无一人。"
        self.assertEqual(self._count(text), 15)


class TestSplitParagraphs(unittest.TestCase):
    """段落拆分逻辑"""

    def test_short_line_unchanged(self):
        from split_paragraphs import split_paragraph
        line = "短句。"
        result = split_paragraph(line, 60)
        self.assertEqual(result, [line])

    def test_long_line_split(self):
        from split_paragraphs import split_paragraph, count_chinese
        # 构造一个超过60字的行
        line = "测试。" * 35  # 每个"测试。"2个汉字 × 35 = 70汉字
        result = split_paragraph(line, 60)
        # 每个分段应 ≤60个汉字
        for seg in result:
            self.assertLessEqual(count_chinese(seg), 60)
        # 分段数应 > 1
        self.assertGreater(len(result), 1)

    def test_dialogue_line_skipped(self):
        from split_paragraphs import split_paragraph
        line = "「你到底想干什么？」"
        result = split_paragraph(line, 60)
        self.assertEqual(result, [line])

    def test_mixed_content_preserved(self):
        from split_paragraphs import split_full_text
        text = """# 第一章
「你好。」他说。

这个段落很正常只有十几个字。

这个段落非常非常长""" + "测试内容。" * 30 + """

「知道了。」
"""
        result = split_full_text(text, 60)
        from split_paragraphs import count_chinese
        # 验证标题行保留
        self.assertIn("# 第一章", result)
        # 验证对话行保留
        self.assertIn("「你好。」", result)
        # 验证每行不超过60汉字
        for line in result.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('「'):
                self.assertLessEqual(count_chinese(stripped), 60)


@unittest.skipUnless(HAS_REQUESTS, "需要 requests 库")
class TestWordCountController(unittest.TestCase):
    """polish.py 字数控制器"""

    def _make_ctrl(self, min_wc=2500, max_wc=3000):
        from polish import WordCountController
        return WordCountController(min_wc=min_wc, max_wc=max_wc)

    def test_in_range(self):
        ctrl = self._make_ctrl()
        text = "测" * 2600
        passed, wc, hint = ctrl.check(text)
        self.assertTrue(passed)
        self.assertEqual(wc, 2600)
        self.assertEqual(hint, "")

    def test_below_min(self):
        ctrl = self._make_ctrl()
        text = "测" * 2000
        passed, wc, hint = ctrl.check(text)
        self.assertFalse(passed)
        self.assertEqual(wc, 2000)
        self.assertIn("不足", hint)

    def test_above_max(self):
        ctrl = self._make_ctrl()
        text = "测" * 3500
        passed, wc, hint = ctrl.check(text)
        self.assertFalse(passed)
        self.assertEqual(wc, 3500)
        self.assertIn("超出", hint)

    def test_boundary_lower(self):
        ctrl = self._make_ctrl()
        self.assertTrue(ctrl.check("测" * 2500)[0])

    def test_boundary_upper(self):
        ctrl = self._make_ctrl()
        self.assertTrue(ctrl.check("测" * 3000)[0])


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


@unittest.skipUnless(HAS_REQUESTS, "需要 requests 库")
class TestStylePresetLoading(unittest.TestCase):
    """文风预设加载"""

    def test_load_preset_file(self):
        from polish import load_style_preset
        from pathlib import Path
        skill_dir = Path(SCRIPT_DIR).parent
        result = load_style_preset("fanqie-quick-anti", skill_dir)
        self.assertIn("system_prompt", result)
        self.assertIn("params", result)
        self.assertIn("番茄小说", result["system_prompt"])


@unittest.skipUnless(HAS_REQUESTS, "需要 requests 库")
class TestProgressTracker(unittest.TestCase):
    """断点续传进度管理"""

    def setUp(self):
        import tempfile
        self.tmpfile = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.tmpfile.close()

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_new_tracker(self):
        from polish import ProgressTracker
        from pathlib import Path
        pt = ProgressTracker(Path(self.tmpfile.name))
        self.assertEqual(pt.data, {"completed": [], "failed": {}})

    def test_mark_done(self):
        from polish import ProgressTracker
        from pathlib import Path
        pt = ProgressTracker(Path(self.tmpfile.name))
        pt.mark_done("ch_001")
        self.assertIn("ch_001", pt.data["completed"])

    def test_mark_failed(self):
        from polish import ProgressTracker
        from pathlib import Path
        pt = ProgressTracker(Path(self.tmpfile.name))
        pt.mark_failed("ch_002", "API错误")
        self.assertIn("ch_002", pt.data["failed"])
        self.assertEqual(pt.data["failed"]["ch_002"], "API错误")

    def test_persistence(self):
        from polish import ProgressTracker
        from pathlib import Path
        pt1 = ProgressTracker(Path(self.tmpfile.name))
        pt1.mark_done("ch_001")
        pt1.mark_failed("ch_003", "超时")

        # 重新加载
        pt2 = ProgressTracker(Path(self.tmpfile.name))
        self.assertIn("ch_001", pt2.data["completed"])
        self.assertIn("ch_003", pt2.data["failed"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
