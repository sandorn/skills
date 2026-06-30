#!/usr/bin/env python3
"""
AI 润色/文风转换脚本 — Writer Skill 组件
============================================
用途: 将小说章节批量提交远程 AI 模型进行润色或文风转换。
特性: 模型无关(OpenAI兼容API) | 文风预设可切换 | 字数控制 | 断点续传 | 自动重试

激活词: 文风转换、转写、润色
依赖: requests, re, json, pathlib (均为 Python 标准库或常见依赖)

用法:
  python polish.py --source <dir> --output <dir> [options]
  python polish.py --test                          # 测试单章
  python polish.py --style fanqie-quick-anti       # 选择文风预设
"""

import os
import sys
import re
import json
import time
import argparse
import requests
from pathlib import Path


# ============================================================================
# 通用工具函数
# ============================================================================

def count_chinese(text: str) -> int:
    """统计文本中中文字符数（含扩展区）"""
    return len(re.findall(r'[一-鿿㐀-䶿]', text))


def ensure_utf8_stdout():
    """Windows 下强制 UTF-8 输出，避免 GBK 编码异常"""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ============================================================================
# 文风预设加载
# ============================================================================

def load_style_preset(preset_name: str, skill_dir: Path) -> dict:
    """
    从 references/style-sop.md 加载文风预设，提取系统提示词。
    也可以加载 presets/ 目录下的独立预设文件。
    返回 {"system_prompt": str, "params": dict}
    """
    # 优先从独立预设文件加载
    preset_file = skill_dir / "references" / "presets" / f"{preset_name}.md"
    if preset_file.exists():
        text = preset_file.read_text(encoding="utf-8")
        return {"system_prompt": text, "params": {}}

    # 默认：加载 style-sop.md 并提取番茄风作为默认
    sop_file = skill_dir / "references" / "style-sop.md"
    if not sop_file.exists():
        raise FileNotFoundError(f"文风文件不存在: {sop_file}")

    # 使用内置的番茄文风提示词
    return {"system_prompt": build_default_system_prompt(), "params": {}}


def build_default_system_prompt() -> str:
    """构建默认番茄文风系统提示词"""
    return """你是一位资深的番茄小说网文编辑，专门负责都市游戏锚点、单人隐秘机缘、草根逆袭题材的章节精修。

请对以下小说章节进行润色改写，严格遵守以下规则：

【文风节奏】
- 短句密集、节奏轻快、无冗长文艺描写
- 口语化高网感，松弛不刻意燃炸
- 贴合番茄爆款轻松逆袭文风

【内容侧重】
- 强化独家秘密、独有特权、实测验证、细节爽点
- 弱化多余场景铺垫
- 聚焦男主独有系统优势、心理博弈、规则试探
- 突出"全世界唯我独有"的核心爽点

【人物塑造】
- 男主心态冷静理智、沉稳隐忍、善于实测复盘
- 不浮夸不中二
- 主打低调发育、手握信息差、掌控全局的草根逆袭人设

【情节处理】
- 测试、验证、铺垫剧情不拖沓
- 每段测试对应明确结论
- 强化安全感、优势感、成长性
- 收尾留期待、埋后续升级伏笔

【细节优化】
- 删除冗余抒情，保留画面基础场景
- 重点放大系统隐蔽性、身体蜕变、规则唯一性等核心设定
- 上下文衔接顺滑

【输出要求】
- 直接输出润色后的完整章节正文
- 不要添加任何前言、后记、说明或评价
- 保持原章节的标题和段落结构
- 保持原文的 Markdown 格式
- 润色后中文字数严格控制在 {min_wc}-{max_wc} 字之间"""


# ============================================================================
# API 客户端
# ============================================================================

class PolishAPIClient:
    """通用 AI API 客户端，兼容 OpenAI Chat Completions 格式"""

    def __init__(self, api_key: str, api_base: str, model: str,
                 timeout: int = 300, max_tokens: int = 16384,
                 temperature: float = 0.7):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature

    def chat(self, system_prompt: str, user_content: str,
             max_retries: int = 3, retry_delay: int = 10) -> tuple:
        """
        发送聊天请求，返回 (success: bool, content: str)
        """
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        for attempt in range(1, max_retries + 1):
            try:
                label = f"[API {attempt}/{max_retries}]"
                print(f"  {label} 请求中...", end=" ", flush=True)
                t0 = time.time()
                resp = requests.post(url, headers=headers, json=payload,
                                     timeout=self.timeout)
                elapsed = time.time() - t0

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    print(f"OK ({elapsed:.0f}s, "
                          f"in={usage.get('prompt_tokens','?')}t, "
                          f"out={usage.get('completion_tokens','?')}t)")
                    return True, content
                else:
                    print(f"FAIL HTTP {resp.status_code}")
                    print(f"     {resp.text[:200]}")
                    if attempt < max_retries:
                        print(f"     {retry_delay}s 后重试...")
                        time.sleep(retry_delay)

            except requests.exceptions.Timeout:
                print(f"FAIL 超时 ({self.timeout}s)")
                if attempt < max_retries:
                    time.sleep(retry_delay)
            except requests.exceptions.ConnectionError as e:
                print(f"FAIL 连接: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"FAIL {type(e).__name__}: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)

        return False, f"API 调用失败 (已重试 {max_retries} 次)"


# ============================================================================
# 字数控制
# ============================================================================

class WordCountController:
    """字数校验 + 修正提示生成"""

    def __init__(self, min_wc: int = 2500, max_wc: int = 3000,
                 max_corrections: int = 2):
        self.min_wc = min_wc
        self.max_wc = max_wc
        self.max_corrections = max_corrections

    def check(self, text: str) -> tuple:
        """返回 (达标: bool, 中文字数: int, 修正提示: str)"""
        wc = count_chinese(text)
        if self.min_wc <= wc <= self.max_wc:
            return True, wc, ""
        if wc < self.min_wc:
            hint = (f"\n\n【字数修正指令】上一次输出 {wc} 字，"
                    f"不足 {self.min_wc} 字下限（差 {self.min_wc - wc} 字）。"
                    f"请扩充细节、心理活动或爽点刻画，确保达到 {self.min_wc}-{self.max_wc} 字。")
            return False, wc, hint
        else:
            hint = (f"\n\n【字数修正指令】上一次输出 {wc} 字，"
                    f"超出 {self.max_wc} 字上限（多 {wc - self.max_wc} 字）。"
                    f"请精简冗余描写和多余铺垫，控制在 {self.min_wc}-{self.max_wc} 字。")
            return False, wc, hint


def generate_compare_report(chapter_name, original_text, polished_text, min_wc, max_wc):
    """生成原文与润色后的对比报告"""
    orig_wc = count_chinese(original_text)
    polished_wc = count_chinese(polished_text)
    wc_met = min_wc <= polished_wc <= max_wc

    delta = polished_wc - orig_wc
    delta_pct = (delta / orig_wc * 100) if orig_wc > 0 else 0

    orig_lines = len([l for l in original_text.split('\n') if l.strip()])
    polished_lines = len([l for l in polished_text.split('\n') if l.strip()])

    lines = []
    lines.append(f"# 润色对比报告: {chapter_name}")
    lines.append("")
    lines.append(f"| 指标 | 原文 | 润色后 |")
    lines.append(f"|------|------|--------|")
    lines.append(f"| 中文字数 | {orig_wc} | {polished_wc} |")
    lines.append(f"| 有效行数 | {orig_lines} | {polished_lines} |")
    lines.append(f"| 字数目标 | {min_wc}-{max_wc} | {'已达成' if wc_met else '未达成'} |")
    lines.append("")
    lines.append("## 变更摘要")
    lines.append("")
    lines.append(f"- 字数变化: {delta:+d}字 ({delta_pct:+.1f}%)")
    if delta > 0:
        lines.append(f"- 内容增加: {delta_pct:.1f}%")
    elif delta < 0:
        lines.append(f"- 内容精简: {abs(delta_pct):.1f}%")
    else:
        lines.append(f"- 字数无变化")
    lines.append("")
    if not wc_met:
        if polished_wc < min_wc:
            lines.append(f"- 字数不足: 差 {min_wc - polished_wc} 字 (目标 {min_wc}-{max_wc})")
        else:
            lines.append(f"- 字数超出: 多 {polished_wc - max_wc} 字 (目标 {min_wc}-{max_wc})")
    lines.append("")

    return '\n'.join(lines)


# ============================================================================
# 进度管理
# ============================================================================

class ProgressTracker:
    """断点续传进度管理"""

    def __init__(self, progress_file: Path):
        self.file = progress_file
        self.data = self._load()

    def _load(self) -> dict:
        if self.file.exists():
            return json.loads(self.file.read_text(encoding="utf-8"))
        return {"completed": [], "failed": {}}

    def save(self):
        self.file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def is_done(self, name: str, output_path: Path) -> bool:
        return name in self.data["completed"] and output_path.exists()

    def mark_done(self, name: str):
        self.data["completed"].append(name)
        self.data["failed"].pop(name, None)
        self.save()

    def mark_failed(self, name: str, reason: str):
        self.data["failed"][name] = reason
        self.save()

    def reset(self):
        self.data = {"completed": [], "failed": {}}
        self.save()


# ============================================================================
# 主处理流程
# ============================================================================

def process_chapter(client: PolishAPIClient, system_prompt: str,
                    chapter_text: str, chapter_name: str,
                    wc_ctrl: WordCountController) -> tuple:
    """
    处理单章：润色 + 字数校验循环
    返回 (success: bool, result_text: str, final_wc: int)
    """
    extra = ""
    result = ""

    for wc_round in range(wc_ctrl.max_corrections + 1):
        if wc_round > 0:
            print(f"  [字数修正 第{wc_round}轮] ", end="")

        ok, result = client.chat(system_prompt, chapter_text + extra)
        if not ok:
            return False, result, 0

        wc = count_chinese(result)
        passed, _, hint = wc_ctrl.check(result)

        status = "OK" if passed else ("LO" if wc < wc_ctrl.min_wc else "HI")
        print(f"  -> {wc} 中文字 [{status}]")

        if passed:
            return True, result, wc

        if wc_round >= wc_ctrl.max_corrections:
            print(f"  (已达最大修正次数，接受当前结果)")
            return True, result, wc

        extra = hint
        time.sleep(2)

    return True, result, count_chinese(result)


def run(args):
    """主入口"""
    ensure_utf8_stdout()

    # ---- 定位 skill 目录 ----
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent  # scripts/ -> writer skill root

    # ---- 加载文风 ----
    style = load_style_preset(args.style, skill_dir)
    system_prompt = style["system_prompt"]

    # ---- 字数控制 ----
    wc_ctrl = WordCountController(
        min_wc=args.min_words,
        max_wc=args.max_words,
        max_corrections=args.max_wc_retries,
    )

    # 将字数要求注入提示词
    system_prompt = system_prompt.format(
        min_wc=wc_ctrl.min_wc, max_wc=wc_ctrl.max_wc
    )

    # ---- 目录校验 ----
    source_dir = Path(args.source).resolve()
    output_dir = Path(args.output).resolve()
    if not source_dir.exists():
        print(f"[ERROR] 源目录不存在: {source_dir}")
        sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- 章节列表 ----
    all_files = sorted(
        [f for f in source_dir.iterdir() if f.suffix.lower() == ".md"],
        key=lambda x: x.name
    )
    if args.chapter:
        target = args.chapter.replace(".md", "")
        chapter_files = [f for f in all_files if f.stem == target]
        if not chapter_files:
            print(f"[ERROR] 未找到章节: {args.chapter}")
            sys.exit(1)
    else:
        chapter_files = all_files

    # ---- 进度 ----
    progress_file = output_dir / ".polish_progress.json"
    progress = ProgressTracker(progress_file)

    # ---- API 客户端 ----
    client = PolishAPIClient(
        api_key=args.api_key,
        api_base=args.api_base,
        model=args.model,
        timeout=args.timeout,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    # ---- 打印配置 ----
    print(f"文风预设: {args.style}")
    print(f"模型: {args.model}")
    print(f"源: {source_dir} -> 输出: {output_dir}")
    print(f"字数要求: {wc_ctrl.min_wc}-{wc_ctrl.max_wc} (修正上限{wc_ctrl.max_corrections}轮)")
    print(f"章间延迟: {args.delay}s | 超时: {args.timeout}s")
    print(f"章节: {len(chapter_files)} 章 (共 {len(all_files)} 章可用)")
    print(f"已完成: {len(progress.data['completed'])} 章")
    print("-" * 50)

    ok_count = len(progress.data["completed"])
    skip_count = 0
    fail_count = 0

    for i, chap_path in enumerate(chapter_files, 1):
        name = chap_path.stem
        out_path = output_dir / f"{name}.md"

        if progress.is_done(name, out_path):
            print(f"[{i}/{len(chapter_files)}] {name} - 跳过(已完成)")
            skip_count += 1
            continue

        print(f"[{i}/{len(chapter_files)}] {name} ", end="", flush=True)

        # 读取
        try:
            text = chap_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"READ FAIL: {e}")
            progress.mark_failed(name, str(e))
            fail_count += 1
            continue

        if not text.strip():
            print("空章节，跳过")
            progress.mark_done(name)
            skip_count += 1
            continue

        orig_wc = count_chinese(text)
        print(f"(原文 {orig_wc} 字) ", end="", flush=True)
        sys.stdout.flush()

        # 处理
        ok, result, final_wc = process_chapter(
            client, system_prompt, text, name, wc_ctrl
        )

        if ok:
            try:
                out_path.write_text(result, encoding="utf-8")
                print(f" -> 已保存 ({final_wc} 字)")
                progress.mark_done(name)
                if args.compare:
                    compare_path = output_dir / f"{name}_compare.md"
                    report = generate_compare_report(name, text, result, args.min_words, args.max_words)
                    compare_path.write_text(report, encoding="utf-8")
                    print(f"         对比报告已保存")
                ok_count += 1
            except Exception as e:
                print(f"WRITE FAIL: {e}")
                progress.mark_failed(name, f"写入: {e}")
                fail_count += 1
        else:
            print(f" -> FAIL: {result}")
            progress.mark_failed(name, result)
            fail_count += 1

        if i < len(chapter_files):
            time.sleep(args.delay)

    # ---- 汇总 ----
    print("\n" + "=" * 50)
    print(f"完成: OK={ok_count} 跳过={skip_count} 失败={fail_count}")
    fails = progress.data.get("failed", {})
    if fails:
        print("失败列表:")
        for k, v in fails.items():
            print(f"  {k}: {v}")
    print(f"输出: {output_dir}")
    print("=" * 50)

    return 0 if fail_count == 0 else 1


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI 润色/文风转换 — 批量处理小说章节",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python polish.py --source chapters/ --output polished/
  python polish.py --test
  python polish.py -s chapters/ -o polished/ --style fanqie-quick-anti --chapter ch_005
  python polish.py -s chapters/ -o polished/ --reset
        """,
    )

    # 路径
    parser.add_argument("--source", "-s", default="chapters",
                        help="源章节目录 (默认: chapters)")
    parser.add_argument("--output", "-o", default="chapters_polished",
                        help="输出目录 (默认: chapters_polished)")

    # 模式
    parser.add_argument("--test", action="store_true",
                        help="测试模式：只处理第一章")
    parser.add_argument("--chapter", "-c", default="",
                        help="只处理指定章节 (如 ch_005)")
    parser.add_argument("--reset", action="store_true",
                        help="重置进度重新开始")
    parser.add_argument("--compare", action="store_true",
                        help="输出原文/润色后对比报告")

    # API
    parser.add_argument("--api-key", default=os.environ.get("ARK_API_KEY", ""),
                        help="API Key (或设置 ARK_API_KEY 环境变量)")
    parser.add_argument("--api-base", default="https://ark.cn-beijing.volces.com/api/v3",
                        help="API Base URL")
    parser.add_argument("--model", default="doubao-seed-2-0-lite-260428",
                        help="模型名称")
    parser.add_argument("--timeout", type=int, default=300,
                        help="请求超时秒数 (默认: 300)")
    parser.add_argument("--max-tokens", type=int, default=16384,
                        help="最大输出 tokens (默认: 16384)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="生成温度 (默认: 0.7)")

    # 文风
    parser.add_argument("--style", default="fanqie-quick-anti",
                        help="文风预设名称 (默认: fanqie-quick-anti)")

    # 字数
    parser.add_argument("--min-words", type=int, default=2500,
                        help="中文字数下限 (默认: 2500)")
    parser.add_argument("--max-words", type=int, default=3000,
                        help="中文字数上限 (默认: 3000)")
    parser.add_argument("--max-wc-retries", type=int, default=2,
                        help="字数不达标最大修正次数 (默认: 2)")

    # 节奏
    parser.add_argument("--delay", type=int, default=3,
                        help="章间延迟秒数 (默认: 3)")

    args = parser.parse_args()

    # --test: 快捷测试模式
    if args.test:
        args.chapter = "ch_001"
        if not args.api_key:
            args.api_key = "ark-b2d0ca10-77a4-4fbb-9f6a-fdfb811ce8f8-528aa"

    # --reset
    if args.reset:
        out_dir = Path(args.output).resolve()
        pf = out_dir / ".polish_progress.json"
        if pf.exists():
            pf.unlink()
            print("进度已重置")

    # 必须提供 API Key
    if not args.api_key:
        print("[ERROR] 未提供 API Key。请设置 ARK_API_KEY 环境变量或使用 --api-key")
        sys.exit(1)

    sys.exit(run(args))


if __name__ == "__main__":
    main()
