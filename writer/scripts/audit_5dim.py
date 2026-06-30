#!/usr/bin/env python3
"""5维专项审查：权限/等级/金额/属性/感情线 全卷一键扫描

用法：python scripts/audit_5dim.py <chapters目录>
示例：python scripts/audit_5dim.py chapters/

输出：每章5维数据点表格，标记异常（等级回退、属性矛盾等）

项目适配：感情线关键词通过 --love-keys 参数传入，或从 setting/characters.md 自动加载。
"""

import re, os, sys, argparse

from lib import count_chinese, find_setting_dir, load_character_names


def main():
    parser = argparse.ArgumentParser(
        description='5维专项审查：权限/等级/金额/属性/感情线 全卷一键扫描',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python audit_5dim.py chapters/\n'
               '  python audit_5dim.py chapters/ --love-keys "林芷琪,白月光,补习,女朋友,表白"\n'
               '  python audit_5dim.py chapters/ --project-root .',
    )
    parser.add_argument('directory', nargs='?', default='.',
                        help='chapters目录')
    parser.add_argument('--love-keys', default=None,
                        help='感情线关键词（逗号分隔），不指定则自动从项目设定加载')
    parser.add_argument('--project-root', default=None,
                        help='项目根目录（用于自动加载角色名/感情线关键词）')
    args = parser.parse_args()

    d = args.directory
    fs = sorted([f for f in os.listdir(d) if f.startswith('ch') and f.endswith('.md')])

    # 加载感情线关键词
    if args.love_keys:
        love_keywords = [k.strip() for k in args.love_keys.split(',') if k.strip()]
    elif args.project_root:
        char_dict = load_character_names(args.project_root)
        if char_dict:
            # 用角色名作为感情线关键词
            love_keywords = list(char_dict.keys())
        else:
            love_keywords = []
    else:
        # 未提供关键词时使用通用感情线模式
        love_keywords = ['表白', '确定关系', '在一起', '喜欢', '爱', '心动',
                         '女朋友', '男朋友', '恋爱', '感情']

    love_pattern = '|'.join(re.escape(k) for k in love_keywords) if love_keywords else None

    print(f"{'章节':<8} {'等级':<10} {'权限':<8} {'属性':<12} {'金额':<15} {'感情':<4}")
    print("-" * 65)

    prev_level = 0
    issues = []

    for f in fs:
        with open(os.path.join(d, f), 'r', encoding='utf-8') as fh:
            t = fh.read()
        ch = int(re.match(r'ch(\d+)', f).group(1))

        # 等级
        levels = sorted(set(int(x) for x in re.findall(r'(\d+)级', t)))
        lv = f"{min(levels)}-{max(levels)}" if levels else "?"

        # 等级回退检测
        if levels:
            cur_max = max(levels)
            if cur_max < prev_level:
                issues.append(f"⚠️ ch{ch:02d}: 等级从{prev_level}回退到{cur_max}")
            prev_level = max(prev_level, cur_max) if cur_max > prev_level else prev_level

        # 权限
        perms = set(re.findall(r'[Ll](\d)', t))
        perm = ','.join(sorted(perms)) if perms else "?"

        # 属性（攻/防）
        attrs = re.findall(r'攻\D*(\d+)\D*防\D*(\d+)|防\D*(\d+)\D*攻\D*(\d+)', t)
        attr_strs = []
        for a in attrs:
            vals = [v for v in a if v]
            if len(vals) >= 2:
                attr_strs.append(f"{vals[0]}/{vals[1]}")
        atk = re.findall(r'攻(?:击)?\s*\+?\s*(\d+)', t)
        dfs = re.findall(r'防(?:御)?\s*\+?\s*(\d+)', t)
        if atk and dfs:
            attr_strs.append(f"{max(map(int,atk))}/{max(map(int,dfs))}")
        attr = ','.join(set(attr_strs[:3])) if attr_strs else "?"

        # 金额
        money = re.findall(r'(\d+[万百千]?\s*(?:块|元|金币))', t)
        money_str = ','.join(money[:2]) if money else "?"

        # 感情线
        love = "✓" if (love_pattern and re.search(love_pattern, t)) else "-"

        # 属性内部矛盾检测
        if attr_strs and len(attr_strs) >= 2:
            for i in range(len(attr_strs)-1):
                try:
                    a1_atk, a1_dfs = map(int, attr_strs[i].split('/'))
                    a2_atk, a2_dfs = map(int, attr_strs[i+1].split('/'))
                    if a2_atk < a1_atk or a2_dfs < a1_dfs:
                        issues.append(f"🔴 ch{ch:02d}: 属性降级 {attr_strs[i]}→{attr_strs[i+1]}")
                except Exception:
                    pass

        print(f"ch{ch:02d}     {lv:<10} {perm:<8} {attr:<12} {money_str:<15} {love:<4}")

    if issues:
        print(f"\n=== 发现 {len(issues)} 个问题 ===")
        for i in issues:
            print(i)
    else:
        print(f"\n✅ 全{len(fs)}章5维一致")


if __name__ == '__main__':
    main()
