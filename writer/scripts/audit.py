#!/usr/bin/env python3
"""统一审计脚本：单章/目录/范围 三模式。

用法：
    python audit.py <file.md>                    # 单章
    python audit.py <目录>                        # 批量（全部 .md）
    python audit.py <目录> 21 60                  # 批量（ch21-ch60）
    python audit.py <目录> --fix-escaped          # 同上 + 自动修复转义引号
    python audit.py --verify <目录>                # 仅检测不修改

禁令与 hard-bans.md 保持同步（单一事实来源）。
"""
import re, os, sys, argparse

# === 禁令规则（与 references/hard-bans.md 同步） ===

# P0 阻塞禁令（B01-B05）
BANS = {
    # B02: 破折号
    '——破折号': r'——',
    # B03: 不是…而是… 句式
    '不是…而是': r'不是.*而是',
    # B04: 元叙事标签
    '元叙事': r'正如前文所述|正如我们所知|这个场景|这一幕|如前所述|读者可能|在此补充|言归正传',
    # B05: AI高频词（基础清单，项目规范可扩展）
    '忽然/突然': r'突然|忽然',
    '他知道': r'他知道',
    '似乎/仿佛': r'似乎|仿佛',
    '眼中闪过一丝': r'眼中闪过一丝',
    '深吸一口气': r'深吸一口气',
    '心中一动': r'心中一动',
}

# B01: 对话引号检测（分 ASCII 和 Unicode 弯引号）
QUOTE_CHECKS = {
    'ASCII引号': r'"[^"]*[一-鿿][^"]*"',
    'Unicode弯引号': r'“|”',
}

# P1: 字数/段落阈值
CHARS_THRESHOLD = 2500
PARA_THRESHOLD = 60

# 模板复制检测相似度阈值
TEMPLATE_SIMILARITY = 0.85
TEMPLATE_FINGERPRINT_LEN = 200


def count_chinese(text):
    return len(re.findall(r'[一-鿿]', text))


def extract_body(text):
    """跳过标题行（# 或 ##），返回 (body_start_line, body_text)"""
    lines = text.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('#') and i == 0:
            body_start = i + 1
            while body_start < len(lines) and lines[body_start].strip() == '':
                body_start += 1
            break
        elif s == '' and i > 0 and lines[i - 1].startswith('#'):
            body_start = i + 1
            break
    return body_start, '\n'.join(lines[body_start:])


def scan_bans(body):
    """禁令扫描（B02-B05）"""
    violations = {}
    for name, pat in BANS.items():
        matches = re.findall(pat, body)
        if matches:
            violations[name] = len(matches)
    return violations


def scan_quotes(body):
    """B01: 对话引号检测"""
    violations = {}
    for name, pat in QUOTE_CHECKS.items():
        matches = re.findall(pat, body)
        if matches:
            violations[name] = len(matches)
    return violations


def scan_paragraphs(lines, body_start):
    """段落超长扫描（B06）"""
    long_lines = []
    for i, line in enumerate(lines[body_start:], start=body_start + 1):
        s = line.strip()
        if not s:
            continue
        lcn = count_chinese(s)
        if lcn > PARA_THRESHOLD:
            long_lines.append(f'L{i}({lcn}字)')
    return long_lines


def detect_template_copy(text, prev_texts):
    """模板复制检测：章首+章末 200 字指纹匹配"""
    issues = []
    body_start, body = extract_body(text)
    clean_body = body.strip()

    # 章首指纹
    opening = clean_body[:TEMPLATE_FINGERPRINT_LEN]
    # 章末指纹
    ending = clean_body[-TEMPLATE_FINGERPRINT_LEN:] if len(clean_body) >= TEMPLATE_FINGERPRINT_LEN else clean_body

    for pi, prev_text in enumerate(prev_texts[:3]):
        if not prev_text:
            continue
        _, prev_body = extract_body(prev_text)
        prev_clean = prev_body.strip()

        if prev_clean[:TEMPLATE_FINGERPRINT_LEN] == opening:
            issues.append(f'章首模板复制：与近{pi+1}章相同')
            break

        if len(prev_clean) >= TEMPLATE_FINGERPRINT_LEN:
            if prev_clean[-TEMPLATE_FINGERPRINT_LEN:] == ending:
                issues.append(f'⚠️ 章末模板复制：与近{pi+1}章相同 → S1阻塞')

    # 章末语义模板检测
    semantic_keywords = ['他靠在椅背上', '闭上眼睛', '窗外的风', '沙沙地响',
                         '一步一步来', '今天的事做完了']
    end_region = clean_body[-500:]
    hit_count = sum(1 for kw in semantic_keywords if kw in end_region)
    if hit_count >= 4:
        issues.append(f'章末语义模板：命中{hit_count}/{len(semantic_keywords)}个关键词 → S2')

    return issues if issues else None


def audit_text(text, prev_texts=None, fix_escaped=False):
    """执行审计，返回 (passed, issues, cn, fixed_text_or_None)"""
    body_start, body = extract_body(text)
    cn = count_chinese(body)
    issues = []
    fixed_text = None

    # 字数（B07）
    if cn < CHARS_THRESHOLD:
        issues.append(f'字数{cn}(缺{CHARS_THRESHOLD - cn})')

    # 禁令扫描（B02-B05）
    violations = scan_bans(body)
    if violations:
        issues.append('违禁:' + ','.join(f'{k}({v})' for k, v in violations.items()))

    # 引号检测（B01）
    quote_violations = scan_quotes(body)
    if quote_violations:
        issues.append('引号:' + ','.join(f'{k}({v})' for k, v in quote_violations.items()))

    # 段落超长（B06）
    lines = text.split('\n')
    long_lines = scan_paragraphs(lines, body_start)
    if long_lines:
        issues.append('段落超标:' + ','.join(long_lines[:5]))

    # 模板复制检测
    template_issues = None
    if prev_texts:
        template_issues = detect_template_copy(text, prev_texts)
        if template_issues:
            issues.extend(template_issues)

    # 转义引号修复
    if '\\"' in text:
        issues.append('含转义引号(\\")')
        if fix_escaped:
            fixed_text = text.replace('\\"', '"')

    passed = (cn >= CHARS_THRESHOLD and not violations and not quote_violations
              and not long_lines and not (template_issues if prev_texts else False))

    return passed, issues, cn, fixed_text


def audit_file(filepath, prev_texts=None, fix_escaped=False, dry_run=False):
    """审计单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    passed, issues, cn, fixed_text = audit_text(text, prev_texts, fix_escaped)

    if fixed_text and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_text)

    return passed, issues, cn, fixed_text is not None


def main():
    parser = argparse.ArgumentParser(
        description='统一审计脚本：单章/目录/范围 三模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('target', help='目标文件或目录')
    parser.add_argument('start', nargs='?', type=int, default=None, help='起始章节号')
    parser.add_argument('end', nargs='?', type=int, default=None, help='结束章节号')
    parser.add_argument('--verify', action='store_true', help='仅检测不修改')
    parser.add_argument('--fix-escaped', action='store_true', help='自动修复转义引号')
    parser.add_argument('--dump-bans', action='store_true',
                        help='输出当前禁令规则（供与 hard-bans.md 对比校验）')
    args = parser.parse_args()

    if args.dump_bans:
        import json as _json
        ban_data = {
            "source": "audit.py BANS (应与 references/hard-bans.md 同步)",
            "p0_blocking": {k: v for k, v in BANS.items()},
            "p1_forced": {
                "chars_min": CHARS_THRESHOLD,
                "para_max": PARA_THRESHOLD,
            },
            "template_similarity": TEMPLATE_SIMILARITY,
            "template_fingerprint_len": TEMPLATE_FINGERPRINT_LEN,
        }
        print(_json.dumps(ban_data, ensure_ascii=False, indent=2))
        sys.exit(0)

    target = args.target
    verify_only = args.verify
    fix_escaped = args.fix_escaped

    # 单文件模式
    if os.path.isfile(target):
        if fix_escaped:
            passed, issues, cn, fixed = audit_file(target, fix_escaped=fix_escaped, dry_run=verify_only)
        else:
            with open(target, 'r', encoding='utf-8') as f:
                text = f.read()
            passed, issues, cn, _ = audit_text(text)

        name = os.path.basename(target)
        status = '✅' if passed else '❌'
        print(f"{name}: {cn}字 {status}" + (' (已修复转义引号)' if fixed and not verify_only else ''))
        for iss in issues:
            print(f"  {iss}")
        sys.exit(0 if passed else 1)

    # 目录模式
    if not os.path.isdir(target):
        print(f"错误：{target} 不是文件也不是目录")
        sys.exit(2)

    files = sorted([f for f in os.listdir(target) if f.endswith('.md')])

    # 范围过滤
    ch_start = args.start
    ch_end = args.end

    if ch_start is not None:
        ch_end = ch_end or ch_start + 999
        files = [f for f in files if
                 ch_start <= int(''.join(c for c in f if c.isdigit()) or '0') <= ch_end]

    # 预加载最近章节用于模板复制检测
    prev_texts = []
    for f in files[:3]:
        with open(os.path.join(target, f), 'r', encoding='utf-8') as fh:
            prev_texts.append(fh.read())

    ok = bad = 0
    total_cn = 0
    fixed_count = 0
    print(f'{"章节":<25} {"字数":>6} {"状态":<4}')
    print('-' * 45)

    for i, f in enumerate(files):
        fp = os.path.join(target, f)
        passed, issues, cn, fixed = audit_file(fp, prev_texts[:3], fix_escaped, verify_only)
        total_cn += cn
        if fixed:
            fixed_count += 1
        if passed and not issues:
            ok += 1
            print(f'{f:<25} {cn:>6} ✅')
        else:
            bad += 1
            first_issue = issues[0] if issues else ''
            print(f'{f:<25} {cn:>6} ❌ {first_issue}')

    total = ok + bad
    print('-' * 45)
    print(f'合计: {total}章 | {total_cn}字 | 通过: {ok}/{total}', end='')
    if fixed_count > 0:
        print(f' | 修复转义引号: {fixed_count}章')
    else:
        print()
    sys.exit(0 if bad == 0 else 1)


if __name__ == '__main__':
    main()
