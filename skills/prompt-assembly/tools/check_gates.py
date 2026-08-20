#!/usr/bin/env python3
"""提示词表十道门禁 —— 每次改完必跑。物件流转是第十一道，在 check_props.py。

用法：
  python3 check_gates.py 提示词表.md
"""
import re, sys, io

# ⚠️ 判据只认这五个词。曾试过加「不能|无|不会|别」，12 处命中全是假阳性：
#    「景别」「别处」「差别」「无人称」「等一个不会来的声音」。
#    skill 原文管的是「以不/没有/禁止/不许开头的**画面要求**」，不是任意出现这些字。
NEG   = r'不要|不许|不得|没有|禁止'
LAZY  = r'(?:脸|面部|表情|五官)[^，。]{0,4}(?:保持原样|保持不变|不变|如常|同前|一样)'
# 允许：具体部件 + 状态（眉毛停在原来的高度）；禁止：整张脸一句话带过

def blocks(src):
    """切出每个块：(标题, 正文含分栏, 控制词)"""
    out = []
    for blk in re.split(r'\n## ', src):
        if not re.match(r'块 \d+\w? ｜', blk):
            continue
        c = re.search(r'```\n(.*?)```', blk, re.S)
        if not c:
            continue
        out.append((blk.split('\n')[0].strip(), blk, c.group(1)))
    return out


def gate(name, hits, detail_fn=None):
    if hits:
        print(f"🔴 {name}：{len(hits)} 处")
        for h in hits[:8]:
            print(f"     {h}")
        if len(hits) > 8:
            print(f"     …另 {len(hits)-8} 处")
    else:
        print(f"✅ {name} 0")
    return len(hits)


def main(path):
    src = io.open(path, encoding='utf-8').read()
    bs = blocks(src)
    print(f"════ 共 {len(bs)} 块\n")
    total = 0

    # ① 负向词（只查控制词，正文分栏是给人看的）
    h = []
    for t, _, c in bs:
        body = re.sub(r'\{[^}]*\}', '', c)          # 台词里可以有「不」
        for m in re.finditer(NEG, body):
            ln = body[max(0, m.start()-16):m.start()+14].replace('\n', ' ')
            h.append(f"{t[:14]} …{ln}…")
    total += gate("负向词", h)

    # ② 偷懒面部
    h = [f"{t[:14]}  {m.group(0)}" for t, _, c in bs for m in re.finditer(LAZY, c)]
    total += gate("偷懒面部", h)

    # ③ 镜头视角
    h = [t[:20] for t, _, c in bs if '【镜头视角】' not in c]
    total += gate("缺【镜头视角】", h)

    # ④ 光与脸
    #    豁免：控制词里一个面部部件都没提 = 画面里没有脸（花店摇镜、空镜、物件镜）
    FACE = r'脸|面部|眼|眉|嘴|唇|颧|下颌|表情|瞳孔|睫毛'
    h = []
    for t, b, c in bs:
        if '【光与脸】' in c:
            continue
        if re.search(FACE, c):
            h.append(f"{t[:20]}  （控制词里有面部部件，不是空镜）")
        else:
            print(f"   ⚪ 豁免 {t[:20]} — 控制词无任何面部部件，画面里没有脸")
    total += gate("缺【光与脸】", h)

    # ⑤ 运动元素清单（两行都要）
    h = []
    for t, _, c in bs:
        if not re.search(r'【这[\d.]+秒里一直在动的东西】', c):
            h.append(f"{t[:20]}  缺「一直在动」")
        if not re.search(r'【这[\d.]+秒里一直不动的东西】', c):
            h.append(f"{t[:20]}  缺「一直不动」")
    total += gate("缺运动元素清单", h)

    # ⑥ 每镜配额 + ⑧ 配额合计 = 块长 + ⑨ 镜号连续且在行首
    hq, hs, hn = [], [], []
    for t, _, c in bs:
        shots = list(re.finditer(r'【镜头(\d+)：([^】]*?)([\d.]+)秒】', c))
        if not shots:
            # 豁免：块长 = 平台单块下限 4 秒，物理上切不出两个镜头
            m4 = re.search(r'([\d.]+)\s*秒', t)   # 块头里的「N 秒」，不限位置
            if m4 and float(m4.group(1)) <= 4:
                print(f"   ⚪ 豁免 {t[:20]} — {m4.group(1)}″ 已是平台单块下限，无法再切")
            else:
                hq.append(f"{t[:20]}  一个镜头配额也没有")
            continue
        # 镜号
        nums = [int(s.group(1)) for s in shots]
        if nums != list(range(1, len(nums)+1)):
            hn.append(f"{t[:20]}  镜号 {nums}")
        for s in shots:
            if s.start() != c.rfind('\n', 0, s.start()) + 1:
                hn.append(f"{t[:20]}  镜{s.group(1)} 标记夹在正文中间")
        # 合计 vs 块长
        m = re.search(r'([\d.]+)\s*秒', t)
        if m:
            want, got = float(m.group(1)), round(sum(float(s.group(3)) for s in shots), 2)
            if abs(want - got) > 0.01:
                hs.append(f"{t[:20]}  块头 {want}″ ≠ 配额合计 {got}″")
    total += gate("缺镜头配额", hq)
    total += gate("配额≠块长", hs)
    total += gate("镜号乱", hn)

    # ⑦ 音频不得为空
    h = [t[:20] for t, _, c in bs if not re.search(r'<[^>]{2,}>', c)]
    total += gate("音频为空", h)

    # ⑩ 单一景别 ≥6 秒（模型在长单一景别下表现差）
    h = []
    for t, _, c in bs:
        shots = re.findall(r'【镜头\d+：([^：】]*?)\s*([\d.]+)秒】', c)
        if not shots:
            continue
        # 累计完整连续段再判定（早期版本一到 6 就 reset，报出来的数字不是真实长度）
        runs, cur = [], None
        for size, sec in shots + [('§', '0')]:
            size = size.strip()
            if cur and cur[0] == size:
                cur[1] += float(sec)
            else:
                if cur:
                    runs.append(cur)
                cur = [size, float(sec)]
        for size, ln in runs:
            if ln >= 6:
                h.append(f"{t[:20]}  「{size}」连续 {ln}″")
    total += gate("单一景别≥6秒", h)

    print(f"\n{'✅ 十道门禁全绿' if total == 0 else f'🔴 合计 {total} 处'}")
    print("⚠️  第十一道（物件流转）另跑：python3 check_props.py " + path)
    return total


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1]) else 0)
