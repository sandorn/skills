#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B02 破折号批量修复脚本（四类上下文分类替换）

用法：
  python scripts/fix_dashes.py chapters/           # 预览，不修改
  python scripts/fix_dashes.py chapters/ --apply   # 实际修复

规则（见 references/hard-bans.md B02）：
  拟声词("嗡——"等)   -> 句号
  对话中断("——」")   -> 省略号
  解释说明(句中——B)  -> 句号/逗号断开
  行首转折(\n——XXX) -> 直接删除破折号
"""
import os, re, sys, glob

ONOMATOPOEIA_CHARS = r'[嗡咔咚当哐哗吱呀呵啦嘿哗啦咔嚓轰隆噼啪咯吱]'

def fix_dashes_in_text(text):
    """逐处替换破折号，按上下文分类处理。返回(new_text, count_by_type)"""
    result = []
    i = 0
    n = len(text)
    counts = {"onomatopoeia": 0, "dialogue_trail": 0, "explanation": 0, "turn": 0}

    while i < n:
        if i + 1 < n and text[i:i+2] == '——':
            before = text[max(0,i-20):i]
            after = text[i+2:min(n,i+2+30)]
            after_first = after[0] if after else ''
            before_tail = before[-3:] if before else ''

            replaced = False

            # 1. 拟声词：前是拟声字，后是闭合引号或换行
            if re.search(ONOMATOPOEIA_CHARS + r'\s*$', before) and after_first in '"\r\n”」':
                result.append('。')
                counts["onomatopoeia"] += 1
                replaced = True
            elif re.search(ONOMATOPOEIA_CHARS + r'\s*$', before) and re.match(ONOMATOPOEIA_CHARS, after):
                # 连续拟声：咚——咚——
                result.append('。')
                counts["onomatopoeia"] += 1
                replaced = True

            # 2. 对话中断：后紧跟闭合引号
            elif after_first in '」"”':
                result.append('……')
                counts["dialogue_trail"] += 1
                replaced = True

            # 3. 行首独立转折：前面是换行+空白
            elif re.search(r'[\r\n]+\s*$', before):
                counts["turn"] += 1
                replaced = True  # 不追加，直接删除破折号

            # 4. 解释说明
            else:
                prev_char = before[-1] if before else ''
                if prev_char in '。！？：':
                    # 前已断句，直接接（删破折号）
                    pass
                elif prev_char in '，；':
                    pass
                else:
                    result.append('。')
                counts["explanation"] += 1
                replaced = True

            i += 2
        else:
            result.append(text[i])
            i += 1

    return ''.join(result), counts

def main():
    if len(sys.argv) < 2:
        print("用法: python fix_dashes.py <目录或文件> [--apply]")
        sys.exit(1)

    target = sys.argv[1]
    apply = '--apply' in sys.argv

    if os.path.isdir(target):
        files = sorted(glob.glob(os.path.join(target, 'ch*.md')))
    else:
        files = [target]

    total_counts = {"onomatopoeia":0,"dialogue_trail":0,"explanation":0,"turn":0}
    total = 0

    for f in files:
        with open(f, 'rb') as fp:
            raw = fp.read()
        text = raw.decode('utf-8-sig')
        has_bom = raw.startswith(b'\xef\xbb\xbf')

        new_text, counts = fix_dashes_in_text(text)
        total += sum(counts.values())
        for k,v in counts.items():
            total_counts[k] += v

        if counts:
            print(f"  {os.path.basename(f)}: 拟声{counts['onomatopoeia']} 对话{counts['dialogue_trail']} 解释{counts['explanation']} 转折{counts['turn']}")

        if apply and sum(counts.values()) > 0:
            output = (b'\xef\xbb\xbf' if has_bom else b'') + new_text.encode('utf-8')
            with open(f, 'wb') as fp:
                fp.write(output)

    print(f"\n总计: {total} 处破折号")
    print(f"  拟声词: {total_counts['onomatopoeia']}")
    print(f"  对话中断: {total_counts['dialogue_trail']}")
    print(f"  解释说明: {total_counts['explanation']}")
    print(f"  行首转折: {total_counts['turn']}")
    if not apply:
        print("\n(预览模式，加 --apply 实际修改)")

    # 验证：检查剩余破折号
    remaining = 0
    for f in files:
        with open(f, 'rb') as fp:
            text = fp.read().decode('utf-8-sig')
        c = len(re.findall(r'——', text))
        if c:
            remaining += c
            if apply:
                print(f"  ⚠ {os.path.basename(f)} 剩余 {c} 处破折号（需手动检查）")
    if apply and remaining:
        print(f"\n剩余 {remaining} 处未处理，请手动检查")
    elif apply and not remaining:
        print("\n✅ 全量破折号已清零")

if __name__ == '__main__':
    main()
