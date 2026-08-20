#!/usr/bin/env python3
"""v6 装配日志核查（Stop hook · 第一阶段：只记不拦）。

查什么：本轮输出里出现 v6 成品块签名时——
  ① 本会话是否 Read 过 _索引/v6装配.md（读没读索引，查的是工具调用记录）
  ② 装配日志里是否有本会话的条目（无日志条目不出块）
违规 → 追加 ~/Desktop/11/_规则库/_装配日志_违规.jsonl，永远 exit 0 不拦截。
升级为拦截：把 OBSERVE_ONLY 改 False（连续一周零误报后再升）。
"""
import sys, json, re, io, os, datetime

OBSERVE_ONLY = True
RULES = os.path.expanduser('~/Desktop/11/_规则库')
LOG = os.path.join(RULES, '_装配日志.jsonl')
VIO = os.path.join(RULES, '_装配日志_违规.jsonl')
# 成品块签名：参考图行 ＋ 镜头串头，两个都命中才算（降低讨论格式时的误报）
SIG_IMG = re.compile(r'=\{\{Image')
SIG_SHOT = re.compile(r'c\d{1,2},\s*\d+(?:\.\d+)?s,\(空间:')


def main():
    try:
        inp = json.load(sys.stdin)
    except Exception:
        return 0
    tp = inp.get('transcript_path', '')
    sid = inp.get('session_id', '')
    if not tp or not os.path.exists(tp):
        return 0

    has_block, read_index = False, False
    try:
        with io.open(tp, encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'tool_use' not in line and 'Image' not in line:
                    continue          # ASCII 预筛；中文可能被转义，不能用中文筛 raw 行
                try:
                    j = json.loads(line)
                except Exception:
                    continue
                for c in (j.get('message') or {}).get('content') or []:
                    if not isinstance(c, dict):
                        continue
                    if c.get('type') == 'tool_use' and c.get('name') == 'Read' \
                       and 'v6装配' in str((c.get('input') or {}).get('file_path', '')):
                        read_index = True
                    if not has_block and j.get('type') == 'assistant':
                        txt = c.get('text', '')
                        if txt and SIG_IMG.search(txt) and SIG_SHOT.search(txt):
                            has_block = True
    except Exception:
        return 0

    if not has_block:
        return 0

    logged = False
    if os.path.exists(LOG):
        with io.open(LOG, encoding='utf-8', errors='ignore') as f:
            for line in f:
                if sid and sid in line:
                    logged = True
                    break

    missing = []
    if not read_index:
        missing.append('未Read v6装配索引')
    if not logged:
        missing.append('无本会话日志条目')
    if not missing:
        return 0

    entry = {'ts': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
             'session': sid, 'missing': missing}
    # 去重：同一会话同一缺失组合只记一次
    if os.path.exists(VIO):
        with io.open(VIO, encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    old = json.loads(line)
                except Exception:
                    continue
                if old.get('session') == sid and old.get('missing') == missing:
                    return 0
    with io.open(VIO, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"⚠️ v6装配核查：{'、'.join(missing)}（已记违规，观测模式不拦截）")
    return 0


if __name__ == '__main__':
    sys.exit(main())
