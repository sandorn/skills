import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from generate_draft_range import (
    build_global_setting,
    count_chinese,
    find_outline_file,
    parse_range,
)
from utils import chapter_filename


class TestGenerateDraftRangeHelpers(unittest.TestCase):
    def test_parse_range(self):
        self.assertEqual(parse_range("3"), (3, 3))
        self.assertEqual(parse_range("3-5"), (3, 5))
        with self.assertRaises(Exception):
            parse_range("5-3")

    def test_chapter_filename_matches_writer_convention(self):
        self.assertEqual(chapter_filename(7), "ch_007.md")

    def test_find_outline_file_prefers_ch_underscore_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "novel.json").write_text("{}", encoding="utf-8")
            outline_dir = root / "outline" / "chapter_outline"
            outline_dir.mkdir(parents=True)
            target = outline_dir / "ch_012.md"
            target.write_text("章纲", encoding="utf-8")

            self.assertEqual(find_outline_file(root, None, 12), target)

    def test_build_global_setting_reads_standard_setting_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setting = root / "setting"
            setting.mkdir()
            (setting / "story_bible.md").write_text("世界观", encoding="utf-8")
            (setting / "characters.md").write_text("角色", encoding="utf-8")

            result = build_global_setting(root, [])
            self.assertIn("story_bible.md", result)
            self.assertIn("世界观", result)
            self.assertIn("characters.md", result)

    def test_count_chinese(self):
        self.assertEqual(count_chinese("abc你好123"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
