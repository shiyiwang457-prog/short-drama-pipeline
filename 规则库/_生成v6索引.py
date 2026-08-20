#!/usr/bin/env python3
"""生成 _索引/v6装配.md —— v6 关键帧工作流的专属索引页（派生·勿手改）。

映射逻辑全在本脚本（站点标签 → v6 字段栏），一张卡都不改。
重算：python3 ~/Desktop/11/_规则库/_生成v6索引.py
"""
import os, re, io

R = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(R, '_索引', 'v6装配.md')

# 每栏的核心卡集（手定 · 依据《纪念日》v7 与沙滩实战的真实引用）
CORE = {
    '戏核与动作拐点':      ['FRAME-42', 'FRAME-35', 'BODY-21'],
    '【动作+情绪】部件级':  ['BODY-35', 'BODY-29', 'BODY-32', 'FACE-11', 'BODY-40'],
    '一直在动的（运动清单）': ['EDIT-02', 'BODY-26'],
    '景别与构图':          ['FRAME-08', 'FRAME-09', 'FRAME-28', 'FRAME-12', 'FACE-01'],
    '光线':               ['FRAME-47', 'FRAME-48', 'FRAME-50', 'FRAME-01', 'FRAME-23'],
    '空间与场景':          ['FRAME-06', 'FRAME-44', 'FRAME-31'],
    '多人与站位':          ['FRAME-11', 'FRAME-18', 'FRAME-22', 'BODY-36'],
}
# 情境追加：按站点标签归栏（核心集之外的卡）
STATION2COL = {
    '站6-可见状态': '【动作+情绪】部件级',
    '站0-形体卡':   '【动作+情绪】部件级',
    '站2-人物基线': '【动作+情绪】部件级',
    '站3-景别机位': '景别与构图',
    '站5-光色':     '光线',
    '站1-场景卡':   '空间与场景',
    '站4-关系轴线': '多人与站位',
    '站2-拆镜':     '戏核与动作拐点',
}


def parse(fp):
    t = io.open(fp, encoding='utf-8', errors='ignore').read()
    fm = t.split('---')[1] if t.startswith('---') else ''
    g = lambda k: (re.search(r'^' + k + r':\s*(.+)$', fm, re.M) or [None, ''])[1] if re.search(r'^' + k + r':', fm, re.M) else ''
    st = re.findall(r'站\d+-[^,\]\s]+|通用', g('站点'))
    fail = g('失败模式').strip()
    if not fail or fail.startswith('实测'):
        fail = '—'
    return st, fail


def main():
    cards = {}
    kd = os.path.join(R, '卡')
    for fn in sorted(os.listdir(kd)):
        if not fn.endswith('.md'):
            continue
        m = re.match(r'([A-Z]+-\d+)\s+(.+)\.md$', fn)
        if not m:
            continue
        cid, title = m.group(1), m.group(2)
        st, fail = parse(os.path.join(kd, fn))
        cards[cid] = {'title': title, 'st': st, 'fail': fail}

    used = set()
    L = ['# v6 装配索引（派生·勿手改）', '',
         '> 重算：`python3 ~/Desktop/11/_规则库/_生成v6索引.py` ｜ 映射在脚本里，卡未做任何改动',
         '> 用法：写 v6 块前 Read 本页 → 核心卡集每块必过脑 → 情境命中再 Read 那几张全卡',
         '> 硬规矩：输出块必须在 `_装配日志.jsonl` 落一条（援引卡号写日志，不进成品）', '']
    for col, ids in CORE.items():
        L.append(f'## {col}')
        L.append('')
        L.append('**核心（每块必过脑）**：')
        L.append('')
        L.append('| 卡 | 管什么 | 失败模式 |')
        L.append('|---|---|---|')
        miss = []
        for cid in ids:
            c = cards.get(cid)
            if not c:
                miss.append(cid)
                continue
            used.add(cid)
            L.append(f"| **{cid}** | {c['title']} | {c['fail'][:34]} |")
        for cid in miss:
            L.append(f"| {cid} | ⚠️ 库中未找到 | |")
        # 情境追加
        extra = [(cid, c) for cid, c in sorted(cards.items())
                 if cid not in used and any(STATION2COL.get(s) == col for s in c['st'])]
        if extra:
            L.append('')
            L.append('<details><summary>情境追加 ' + str(len(extra)) + ' 张（涉及该维度再点开）</summary>')
            L.append('')
            for cid, c in extra:
                used.add(cid)
                L.append(f"- {cid} {c['title']} ｜ {c['fail'][:30]}")
            L.append('')
            L.append('</details>')
        L.append('')
    # 通用卡
    gen = [(cid, c) for cid, c in sorted(cards.items()) if cid not in used and '通用' in c['st']]
    if gen:
        L.append('## 通用（所有块）')
        L.append('')
        for cid, c in gen:
            used.add(cid)
            L.append(f"- {cid} {c['title']} ｜ {c['fail'][:30]}")
        L.append('')
    L.append(f'---\n覆盖 {len(used)}/{len(cards)} 张；未入本页的 {len(cards)-len(used)} 张属纯分镜/舞台维度，v6 装配不取。')
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print(f'✅ {OUT}')
    print(f'   覆盖 {len(used)}/{len(cards)} 张 ｜ 页面 {len(chr(10).join(L))} 字')


if __name__ == '__main__':
    main()
