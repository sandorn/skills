#!/usr/bin/env python3
"""5维专项审查：权限/等级/金额/属性/感情线 全卷一键扫描

⚠️ 项目适配：感情线关键词（第64行）包含示例项目角色名（林芷琪、白月光等）。
   使用前请修改为当前项目角色/感情线关键词。

用法：python scripts/audit_5dim.py <chapters目录>
示例：python scripts/audit_5dim.py chapters/

输出：每章5维数据点表格，标记异常（等级回退、属性矛盾等）

⚠️ 项目适配：感情线关键词（林芷琪/白月光等）和角色名需按项目修改。
   本脚本为通用框架，项目特定模式硬编码在正则中，使用前检查是否匹配当前项目。
"""

import re, os, sys, argparse

def main():
    parser = argparse.ArgumentParser(
        description='5维专项审查：权限/等级/金额/属性/感情线 全卷一键扫描',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('directory', nargs='?', default='.', help='chapters目录')
    args = parser.parse_args()
    d = args.directory
    fs = sorted([f for f in os.listdir(d) if f.startswith('ch') and f.endswith('.md')])

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
        # Also match standalone
        atk = re.findall(r'攻(?:击)?\s*\+?\s*(\d+)', t)
        dfs = re.findall(r'防(?:御)?\s*\+?\s*(\d+)', t)
        if atk and dfs:
            attr_strs.append(f"{max(map(int,atk))}/{max(map(int,dfs))}")
        attr = ','.join(set(attr_strs[:3])) if attr_strs else "?"

        # 金额
        money = re.findall(r'(\d+[万百千]?\s*(?:块|元|金币))', t)
        money_str = ','.join(money[:2]) if money else "?"

        # 感情线
        love = "✓" if re.search(r'林芷琪|白月光|补习|女朋友|表白|确定关系', t) else "-"

        # 属性内部矛盾检测
        if attr_strs and len(attr_strs) >= 2:
            for i in range(len(attr_strs)-1):
                try:
                    a1_atk, a1_dfs = map(int, attr_strs[i].split('/'))
                    a2_atk, a2_dfs = map(int, attr_strs[i+1].split('/'))
                    if a2_atk < a1_atk or a2_dfs < a1_dfs:
                        issues.append(f"🔴 ch{ch:02d}: 属性降级 {attr_strs[i]}→{attr_strs[i+1]}")
                except: pass

        print(f"ch{ch:02d}     {lv:<10} {perm:<8} {attr:<12} {money_str:<15} {love:<4}")

    if issues:
        print(f"\n=== 发现 {len(issues)} 个问题 ===")
        for i in issues:
            print(i)
    else:
        print(f"\n✅ 全{len(fs)}章5维一致")

if __name__ == '__main__':
    main()
