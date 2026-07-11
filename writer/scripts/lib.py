#!/usr/bin/env python3
# SAFETY: INFRA — 共享工具模块。safe_write() 提供统一的 .bak 备份写入。
"""Writer Skill 共享工具模块 — 所有脚本的单一依赖源。

提取各脚本中重复定义的函数：
  - count_chinese(text)        统一中文计数（唯一定义）
  - extract_body(text)         跳过标题行提取正文
  - scan_chapter_files(directory, ch_start, ch_end)  章节文件扫描+过滤
  - find_chapters_dir(project_root)                   项目正文目录检测
  - find_setting_dir(project_root)                    项目设定目录检测
  - find_tracking_dir(project_root)                   项目追踪目录检测
  - load_writer_json(project_root)                    加载项目状态
  - is_dialogue_line(line)      对话行检测

用法：
    from lib import count_chinese, extract_body, scan_chapter_files, ...
"""

import re
import os
import json
from pathlib import Path
from typing import Optional, Callable


# ============================================================================
# 中文计数（唯一定义 — 所有脚本均应从本模块导入）
# ============================================================================

def count_chinese(text: str) -> int:
    """统计文本中中文字符数。

    覆盖范围：CJK 统一表意文字基本区 (U+4E00–U+9FFF) +
              CJK 扩展 A 区 (U+3400–U+4DBF)。

    与旧版 [一-鿿㐀-䶿] 字符字面量写法等价，
    统一使用 Unicode 转义形式以确保跨编辑器兼容。
    """
    return len(re.findall(r'[一-鿿㐀-䶿]', text))


# ============================================================================
# 正文提取
# ============================================================================

def extract_body(text: str) -> tuple[int, str]:
    """从章节文本中跳过标题行（# / ##），返回 (body_start_line_index, body_text)。

    标题识别规则：
      - 以 '#' 开头的行视为标题
      - 标题行后的第一个空行视为标题与正文的分界
    """
    lines = text.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('#') and i == 0:
            body_start = i + 1
            while body_start < len(lines) and lines[body_start].strip() == '':
                body_start += 1
            break
        elif s == '' and i > 0 and lines[i - 1].strip().startswith('#'):
            body_start = i + 1
            break
    return body_start, '\n'.join(lines[body_start:])


# ============================================================================
# 目录检测
# ============================================================================

def find_chapters_dir(project_root: str) -> Optional[str]:
    """检测项目中的正文章节目录。

    按优先级尝试：chapters/ → 正文/
    返回绝对路径或 None。
    """
    for d in ['chapters', '正文']:
        path = os.path.join(project_root, d)
        if os.path.isdir(path):
            return path
    return None


def find_setting_dir(project_root: str) -> Optional[str]:
    """检测项目中的设定目录。

    按优先级尝试：setting/ → 设定/
    返回绝对路径或 None。
    """
    for d in ['setting', '设定']:
        path = os.path.join(project_root, d)
        if os.path.isdir(path):
            return path
    return None


def find_tracking_dir(project_root: str) -> Optional[str]:
    """检测项目中的追踪目录。

    按优先级尝试：tracking/ → 追踪/
    返回绝对路径或 None。
    """
    for d in ['tracking', '追踪']:
        path = os.path.join(project_root, d)
        if os.path.isdir(path):
            return path
    return None


# ============================================================================
# 章节文件扫描
# ============================================================================

def extract_chapter_number(filename: str) -> int:
    """从文件名中提取章节号。如 'ch_042.md' → 42, 'ch001.md' → 1。

    无数字时返回 0。
    """
    digits = ''.join(c for c in filename if c.isdigit())
    return int(digits) if digits else 0


def scan_chapter_files(
    directory: str,
    ch_start: Optional[int] = None,
    ch_end: Optional[int] = None,
    *,
    sort_key: Optional[Callable[[str], int]] = None,
) -> list[str]:
    """扫描目录下的 .md 章节文件，返回排序后的文件名列表。

    参数：
      directory: 章节目录路径
      ch_start:  起始章节号（含），None 表示不限
      ch_end:    结束章节号（含），None 表示不限
      sort_key:  排序键函数，默认按 extract_chapter_number

    返回：文件名列表（仅文件名，不含路径前缀）。
    """
    if not os.path.isdir(directory):
        return []

    if sort_key is None:
        sort_key = extract_chapter_number

    files = sorted(
        [f for f in os.listdir(directory) if f.endswith('.md')],
        key=sort_key,
    )

    if ch_start is not None:
        ch_end = ch_end if ch_end is not None else 9999
        files = [
            f for f in files
            if ch_start <= extract_chapter_number(f) <= ch_end
        ]

    return files


# ============================================================================
# 项目状态
# ============================================================================

PROJECT_JSON_MARKERS = ('novel.json', 'writer.json', 'novel-pipeline.json')


def load_writer_json(project_root: str) -> Optional[dict]:
    """加载项目状态文件，优先 novel.json，兼容 writer.json / novel-pipeline.json。"""
    for marker in PROJECT_JSON_MARKERS:
        path = os.path.join(project_root, marker)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None


# ============================================================================
# 对话行检测
# ============================================================================

def is_dialogue_line(line: str) -> bool:
    """判断是否为对话行（以「『开头）——项目标准引号。"""
    return bool(line.strip() and line.strip().startswith(('「', '『')))


# ============================================================================
# 安全文件覆写（自动 .bak）
# ============================================================================

def safe_write(filepath: str, content: str, *, backup: bool = True) -> None:
    """安全写入文件。backup=True 时自动创建 .bak 备份。

    用法：
        safe_write('chapters/ch_001.md', new_content)
    """
    if backup and os.path.exists(filepath):
        bak = filepath + '.bak'
        # 仅在 .bak 不存在或内容不同时创建
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                old = f.read()
            if old != content:
                with open(bak, 'w', encoding='utf-8') as f:
                    f.write(old)
        except OSError:
            pass  # 备份失败不阻塞写入

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


# ============================================================================
# 项目角色名加载（供分析类脚本共用）
# ============================================================================

def load_character_names(project_root: str) -> dict[str, dict]:
    """从项目设定文件中加载角色名及其分类。

    加载优先级：
      1. setting/characters.md 或 设定/characters.md 中 ## 角色列表 节
      2. novel.json / writer.json 中 characters 字段
      3. 空字典

    返回格式：{角色名: {"type": "主角", "faction": "主角方", "aliases": []}}
    """
    chars: dict[str, dict] = {}

    # 尝试从 characters.md 解析
    setting_dir = find_setting_dir(project_root)
    if setting_dir:
        char_file = os.path.join(setting_dir, 'characters.md')
        if os.path.exists(char_file):
            with open(char_file, 'r', encoding='utf-8') as f:
                text = f.read()
            # 简单解析：匹配 ## 角色名 格式的节标题
            for m in re.finditer(r'^##\s+(.+?)(?:\s*$|\s*[（(])', text, re.MULTILINE):
                name = m.group(1).strip()
                if name and len(name) >= 2:
                    chars[name] = {'type': '其他', 'faction': '其他', 'aliases': [name]}

    # 回退：从项目 JSON 加载
    if not chars:
        state = load_writer_json(project_root)
        if state and 'characters' in state:
            for entry in state['characters']:
                if isinstance(entry, dict) and 'name' in entry:
                    name = entry['name']
                    chars[name] = {
                        'type': entry.get('type', '其他'),
                        'faction': entry.get('faction', '其他'),
                        'aliases': entry.get('aliases', [name]),
                    }

    return chars


# ============================================================================
# Git 快照前置钩子（与 novel-pipeline 保持功能一致的独立实现）
# ============================================================================

def _run_git(args, cwd):
    """薄封装：返回 (returncode, stdout, stderr)。"""
    import subprocess
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def find_git_root(start):
    """从 start 向上找 .git 目录（最多 5 层）。找不到返回 None。"""
    start = Path(start).resolve()
    for p in [start, *start.parents][:6]:
        if (p / ".git").exists():
            return p
    return None


def ensure_git_snapshot(target_dir, force=False, tag="pre-op"):
    """
    覆盖类操作前的 git 快照：
    - 非 git repo → 除非 force=True，否则返回 False 阻断
    - 有未提交变更 → 自动 `git add -A && git commit`
    - 工作区干净 → 跳过

    使用场景：
      - 批量写章前  (tag="pre-write")
      - 修复管线前  (tag="pre-fix")
      - 润色替换前  (tag="pre-polish")

    :param target_dir: 项目内任意目录（会向上找 .git）
    :param force: 非 repo 时是否放行
    :param tag: 快照 commit message 前缀
    :return: True 可继续，False 应中止
    """
    import sys
    from datetime import datetime

    target_dir = Path(target_dir).resolve()
    git_root = find_git_root(target_dir)

    if git_root is None:
        print("⚠️  项目目录不是 git 仓库，无法自动快照。", file=sys.stderr)
        if force:
            print("   已指定 force=True，跳过快照继续执行。", file=sys.stderr)
            return True
        print("   建议：先在项目根执行 `git init && git add . && git commit -m init`", file=sys.stderr)
        return False

    code, out, err = _run_git(["status", "--porcelain"], git_root)
    if code != 0:
        print(f"⚠️  git status 失败: {err[:200]}", file=sys.stderr)
        return force

    if not out:
        print(f"✅ git 工作区干净（{git_root.name}），跳过快照")
        return True

    print(f"🗂️  发现未提交变更，创建 {tag} 快照...")
    code, _, err = _run_git(["add", "-A"], git_root)
    if code != 0:
        print(f"⚠️  git add 失败: {err[:200]}", file=sys.stderr)
        return force
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"chore: {tag} snapshot {stamp}"
    code, _, err = _run_git(["commit", "-m", msg], git_root)
    if code != 0:
        print(f"⚠️  git commit 失败（不阻断）: {err[:200]}", file=sys.stderr)
        return True
    print(f"✅ 快照已提交：{msg}")
    return True
