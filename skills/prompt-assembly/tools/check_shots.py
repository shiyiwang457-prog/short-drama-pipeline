#!/usr/bin/env python3
"""成品块门禁 —— 检查唯一交付格式（cNN 镜头串）写对没有。

用法：
  python3 check_shots.py 块.txt          # 查文件
  pbpaste | python3 check_shots.py -     # 查剪贴板

查七道：
  ① 参考图行存在      ② 全局头三件套（无文字/无BGM/画幅）
  ③ 镜号连续 c01,c02… ④ 四括号齐全且顺序对
  ⑤ 情绪打分 N/10     ⑥ 时长 ≥4 秒（平台下限）
  ⑦ 动作正文负向词    （护栏句豁免，见 WHITELIST）
"""
import re, sys, io

# 护栏句：格式固定件，负向词门禁对它们豁免
# 护栏句用正则，覆盖「不X／不能X／不得X／绝不X」等变体（实测：白名单写死会漏「不能切换外部机位」）
GUARD = re.compile(
    r'(?:画面)?不要出现任何文字|不出现任何文字字幕|生成视频无BGM'
    r'|(?:绝)?不(?:能|得)?(?:加入|出现|切换|新增|重复|再次|换脸|变装|中断|黑场|夸张|突然变焦|无意义晃动)[^，。；]*'
    r'|取景框、时间码、录制标志[^，。；]*'
    r'|不(?:能|得)?(?:向上移动|停下来休息|洒落|掉落|抢走|触碰镜头)[^，。；]*'
)
NEG = r'不要|不许|不得|没有|禁止|不能|绝不|不出现|不加入|不切换|不新增|不重复|不再次'
BRACKETS = ['空间', '姿态', '位置', '情绪']


def check(text):
    errs, ok = [], []

    # ① 参考图行
    if re.search(r'\{\{Image[^}]*\}\}', text):
        ok.append('参考图绑定')
    else:
        errs.append('① 缺参考图行（场景=/角色={{Image …}}）')

    # ② 全局头三件套
    head = text.split('c01,')[0]
    miss = [k for k, pat in [('无文字', r'不要出现任何文字'), ('无BGM', r'无BGM'),
                             ('画幅', r'\d+:\d+')] if not re.search(pat, head)]
    (ok.append('全局头三件套') if not miss else errs.append(f'② 全局头缺：{"、".join(miss)}'))

    # ③ 镜号连续
    shots = list(re.finditer(r'c(\d{2}),\s*([\d.]+)s,', text))
    if not shots:
        errs.append('③ 一个 cNN 镜头串都没有')
        return errs, ok
    nums = [int(s.group(1)) for s in shots]
    (ok.append(f'镜号连续 c01–c{nums[-1]:02d}') if nums == list(range(1, len(nums) + 1))
     else errs.append(f'③ 镜号不连续：{nums}'))

    # ④⑤⑥ 逐镜查
    bad_br, bad_em = [], []
    for i, s in enumerate(shots):
        seg = text[s.end():(shots[i + 1].start() if i + 1 < len(shots) else len(text))]
        head_seg = seg[:220]
        got = re.findall(r'\((空间|姿态|位置|情绪):', head_seg)
        if got != BRACKETS:
            bad_br.append(f'c{s.group(1)}（{"→".join(got) or "无"}）')
        if not re.search(r'\d+\s*/\s*10\)', head_seg):
            bad_em.append(f'c{s.group(1)}')

    (errs.append(f'④ 四括号缺失/乱序：{"、".join(bad_br)}') if bad_br else ok.append('四括号齐全有序'))
    (errs.append(f'⑤ 情绪未打分：{"、".join(bad_em)}') if bad_em else ok.append('情绪均已打分'))
    # ⑥ 4–30 秒是**整块**的平台限制；cNN 是块内镜头分段，单镜可以短于 4 秒
    total = round(sum(float(s.group(2)) for s in shots), 1)
    if total < 4:
        errs.append(f'⑥ 整块 {total}s 低于平台下限 4 秒')
    elif total > 30:
        errs.append(f'⑥ 整块 {total}s 超出平台上限 30 秒，需拆块')
    else:
        ok.append(f'整块 {total}s 在平台 4–30 秒内')

    # ⑦ 负向词（挖掉护栏句后再查）
    body = GUARD.sub(lambda m: '　' * len(m.group(0)), text)
    hits = []
    for m in re.finditer(NEG, body):
        ctx = body[max(0, m.start() - 14):m.start() + 12].replace('\n', ' ').strip()
        hits.append(f'「{m.group(0)}」…{ctx}…')
    (errs.append(f'⑦ 动作正文有 {len(hits)} 处负向词：\n     ' + '\n     '.join(hits[:5]))
     if hits else ok.append('动作正文负向词 0'))
    return errs, ok


if __name__ == '__main__':
    src = sys.stdin.read() if (len(sys.argv) > 1 and sys.argv[1] == '-') \
        else io.open(sys.argv[1], encoding='utf-8').read()
    errs, ok = check(src)
    for o in ok:
        print(f'  ✅ {o}')
    for e in errs:
        print(f'  🔴 {e}')
    print(f"\n{'✅ 成品块门禁通过' if not errs else f'🔴 {len(errs)} 项待修'}")
    sys.exit(1 if errs else 0)
