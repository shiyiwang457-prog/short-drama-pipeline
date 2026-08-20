#!/usr/bin/env python3
"""物件流转门禁 —— 追踪每个物件在哪只手，抓五类错。

判据（全部可执行，不依赖语义理解）：
  ① 一手持两物      同一只手同时持有两个物件
  ② 接收方=持有方    容器握在某只手，倒出来的东西却接进同一只手（物理不可能）
  ③ 凭空出现        物件被操作，但此前从未被取得
  ④ 容器凭空出现     「把 A 装进 B」中的 B 此前从未出现
  ⑤ 悬空           物件被拿起，到结束都没放下也没交代去向

用法：
  python3 check_props.py 提示词表.md      # 扫全表
  echo "文本" | python3 check_props.py -   # 扫单段
"""
import re, sys, io

OBJ  = r'磁带|药盒|药片|盖子|杯子|玻璃杯|遥控器|遥控|领带|镜头盖|摄像机|DV|纸|笔|书|花|包|西装|钥匙|衣服'
HAND = r'左手|右手|双手|两只手|拇指'
SUBJ = r'左手|右手|双手|两只手|拇指|他|她'   # 取物的主语可以是人，不必是手
GET  = r'(?:拿出|拿起|取下|接过|捡起|摸出|抓起|取过|托住|握着)'
PUT  = r'(?:放下|放到|放回|搁在|搁到|递给|递上|松开|放在|扔|垂到|落回|挪开|退出|穿在|穿上|挂在|套上)'
OPER = r'(?:拧开|倒过来|举到|送进|推开|扯正|拉正|吹|翻开)'

ALIAS = {'玻璃杯':'杯子', 'DV':'摄像机', '遥控':'遥控器'}
PART  = {'盖子':'药盒', '镜头盖':'摄像机'}          # 附属物 -> 母体
KEEP  = {'摄像机', '遥控器', '包'}                 # 长期持有物：块末仍在手是正常的（跨块延续）

def norm(o):
    return ALIAS.get(o, o)

def analyze(text):
    errs, hold, where, container = [], {}, {}, [None]
    for s in re.split(r'[。；\n]', text):
        s = s.strip()
        if not s or not re.search(OBJ, s):
            continue

        # —— 取得（主语可以是「他/她」，此时归到「手」这一个笼统槽）
        for h in re.findall(SUBJ, s):
            h = h if h in ('左手','右手','双手','两只手','拇指') else '手'
            pat_h = h if h != '手' else r'[他她]'
            for m in re.finditer(rf'{pat_h}[^，。]{{0,8}}{GET}[^，。]{{0,6}}({OBJ})', s):
                o = norm(m.group(1))
                for h2 in hold:
                    hold[h2].discard(o)
                hold.setdefault(h, set()).add(o)
                where[o] = h

        # —— 释放（两种语序）
        rel = set()
        for m in re.finditer(rf'{PUT}[^，。]{{0,6}}({OBJ})', s):
            rel.add(norm(m.group(1)))
        for m in re.finditer(rf'把?({OBJ})[^，。]{{0,8}}{PUT}', s):
            rel.add(norm(m.group(1)))
        for o in rel:
            for h2 in hold:
                hold[h2].discard(o)
            where[o] = '桌上'

        # —— ① 一手持两物
        for h, os_ in list(hold.items()):
            if len(os_) > 1:
                errs.append(('一手持两物', f'{h} 同时持有：{"、".join(sorted(os_))}', s[:44]))
                hold[h] = {sorted(os_)[-1]}

        # —— ② 容器 -> 内容物
        cm = re.search(rf'把?({OBJ})[^，。]{{0,6}}(?:倒过来|倒转|翻过来)', s)
        if cm:
            container[0] = norm(cm.group(1))
        for m in re.finditer(r'(?:倒进|落进|倒入|落到)[^，。]{0,6}(左|右)(?:掌心|手)', s):
            dst, c = m.group(1) + '手', container[0]
            if c and where.get(c) == dst:
                errs.append(('接收方=持有方',
                             f'{c} 握在{dst}里，倒出来的东西却接进同一只{dst}——物理不可能', s[:44]))
                container[0] = None

        # —— ④ 容器必须已存在
        for m in re.finditer(rf'({OBJ})[^，。]{{0,6}}(?:装进|放进|塞进)[^，。]{{0,4}}({OBJ})', s):
            cont = norm(m.group(2))
            if cont not in where:
                errs.append(('容器凭空出现', f'{cont} 在被装入东西之前从未出现', s[:44]))
                where[cont] = '?'

        # —— ③ 凭空出现
        for m in re.finditer(rf'{OPER}[^，。]{{0,6}}({OBJ})', s):
            o = norm(m.group(1))
            if o not in where:
                mother = PART.get(o)
                if mother and mother in where:
                    where[o] = where[mother]
                else:
                    errs.append(('凭空出现', f'{o} 被操作前从未出现', s[:44]))
                    where[o] = '?'

    # —— ⑤ 悬空
    for h, os_ in hold.items():
        for o in os_:
            if o in KEEP:
                continue        # 长期持有物，跨块继续拿着，不算悬空
            errs.append(('悬空', f'{o} 结束时仍在{h}，去向未交代', ''))
    return errs


if __name__ == '__main__':
    if sys.argv[1] == '-':
        for t, d, s in analyze(sys.stdin.read()):
            print(f"🔴 {t}: {d}" + (f"  ｜ {s}" if s else ""))
    else:
        src = io.open(sys.argv[1], encoding='utf-8').read()
        n = 0
        for blk in re.split(r'\n## ', src):
            if not re.match(r'块 \d+\w? ｜', blk):
                continue
            c = re.search(r'```\n(.*?)```', blk, re.S)
            if not c:
                continue
            h = re.sub(r'[*·]', '', blk.split('\n')[0])[:22]
            # 按块分析（物件可以跨镜流转，逐镜会误报）
            body = re.sub(r'\{[^}]*\}', '', c.group(1))
            body = re.sub(r'【[^】]*】', '\n', body)
            for t, d, s in analyze(body):
                print(f"🔴 {h}  [{t}] {d}" + (f"\n      {s}" if s else ""))
                n += 1
        print(f"\n{'✅ 物件流转门禁通过' if n == 0 else f'🔴 命中 {n} 处'}")
