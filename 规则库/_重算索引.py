#!/usr/bin/env python3
"""从 _扫描/ 的批次文件重算总索引。派生物，绝不手改。"""
import io, os, re, glob
from collections import defaultdict
base=os.path.dirname(os.path.abspath(__file__))
rows=[]
for f in sorted(glob.glob(f"{base}/_扫描/*/*.md")):
    fm=io.open(f,encoding='utf-8').read().split("---")[1]
    d=dict(re.findall(r'^(\w+):\s*(.*)$', fm, flags=re.M))
    d['状态']=d.get('状态','').strip('`')
    d['出卡数']=int(d.get('出卡数',0) or 0)
    d['字符']=int(d.get('字符',0) or 0)
    rows.append(d)
byb=defaultdict(list); byt=defaultdict(list)
for r in rows: byb[r['书']].append(r); byt[r['书型']].append(r)
done=lambda l:[x for x in l if x['状态'].startswith('已扫')]
# 纪律 15：部分精读也出卡，账目必须计入；但不计入「已扫」批次进度
scanned=lambda l:[x for x in l if x['状态'].startswith(('已扫','部分精读'))]
# ⭐ 卡片账目对账（纪律 11）：以 卡/ 目录实际文件数为唯一权威
import io as _io0
_cards=sorted(glob.glob(f"{base}/卡/*.md"))
_src={}; _orphan=[]
for _f in _cards:
    _fm=_io0.open(_f,encoding='utf-8').read().split("---")[1]
    _v=(re.search(r'^来源批次:\s*(.*)$',_fm,re.M) or [None,''])[1]
    _m=re.search(r'\[\[([^\]]+)\]\]',_v)
    if _m: _src[_m.group(1)]=_src.get(_m.group(1),0)+1
    else: _orphan.append(os.path.basename(_f)[:-3])
# 出卡数是派生值：按实到数自动回写批次文件，并同步 rows（纪律 11）
_synced=[]
for _f in sorted(glob.glob(f"{base}/_扫描/*/*.md")):
    _t=_io0.open(_f,encoding='utf-8').read(); _fm=_t.split("---")[1]
    _i=(re.search(r'^id:\s*(.*)$',_fm,re.M) or [None,''])[1].strip()
    _d=int((re.search(r'^出卡数:\s*(\d+)',_fm,re.M) or [None,0])[1])
    _a=_src.get(_i,0)
    if _a!=_d:
        _t=re.sub(r'^出卡数:\s*\d+$',f'出卡数: {_a}',_t,count=1,flags=re.M)
        _t=re.sub(r'^状态:\s*`(已扫|部分精读)·出卡\d+`$',lambda _m:f'状态: `{_m.group(1)}·出卡{_a}`',_t,count=1,flags=re.M)
        _io0.open(_f,"w",encoding='utf-8').write(_t); _synced.append((_i,_d,_a))
        for _r in rows:
            if _r.get('id')==_i:
                _r['出卡数']=_a
                if _r['状态'].startswith(('已扫','部分精读')):
                    _pre=_r['状态'].split('·')[0]
                    _r['状态']=f'{_pre}·出卡{_a}'
_declared=sum(x['出卡数'] for x in rows)
_mismatch=[(r['id'],r['出卡数'],_src.get(r['id'],0)) for r in rows if _src.get(r['id'],0)!=r['出卡数']]

o=["---","类型: 扫描索引","说明: 本文件由 _重算索引.py 从 _扫描/ 重算，请勿手改","---","",
"# 扫描索引（派生·勿手改）","",
f"重算命令：`python3 ~/Desktop/11/_规则库/_重算索引.py`","",
"## 总进度","",
f"- 批次：**{len(done(rows))} / {len(rows)}** 已扫（{len(done(rows))/len(rows)*100:.1f}%）" + (f" ＋ **{len(scanned(rows))-len(done(rows))}** 批部分精读" if len(scanned(rows))>len(done(rows)) else ""),
f"- 字符：{sum(x['字符'] for x in done(rows)):,} / {sum(x['字符'] for x in rows):,}",
f"- 卡片：**{len(_cards)} 张**（以 `卡/` 目录实际文件数为准）",
f"- 账目对账：批次声明合计 {_declared} · 卡片自报 {sum(_src.values())} · " +
  ("**✅ 一致**" if (_declared==len(_cards) and not _orphan and not _mismatch)
   else f"**⚠️ 不一致** — 无来源卡 {len(_orphan)} 张，批次数不符 {len(_mismatch)} 处"),"",
"## 按书型（出卡密度，用于外推）","",
"| 书型 | 批数 | 已扫 | 出卡 | 密度（张/批） |","|---|---|---|---|---|"]
for t,l in sorted(byt.items()):
    dn=done(l); dens=f"{sum(x['出卡数'] for x in dn)/len(dn):.2f}" if dn else "—"
    o.append(f"| {t} | {len(l)} | {len(dn)} | {sum(x['出卡数'] for x in l)} | {dens} |")
o+=["","## 按书","","| 书 | 书型 | 批数 | 已扫 | 出卡 |","|---|---|---|---|---|"]
for b,l in sorted(byb.items()):
    o.append(f"| {b[3:]} | {l[0]['书型']} | {len(l)} | {len(done(l))} | {sum(x['出卡数'] for x in l)} |")
# 积压与排除（纪律 5/6：三终态封闭）
import io as _io
bl=[];ex=[]
for f in sorted(glob.glob(f"{base}/_扫描/*/*.md")):
    s=_io.open(f,encoding='utf-8').read(); nm=os.path.basename(f)[:-3]
    for sec,acc in (("待成卡",bl),("已排除",ex)):
        m=re.search(r'## '+sec+r'[^\n]*\n(.*?)(?=\n## |\Z)',s,re.S)
        if m:
            for ln in m.group(1).split("\n"):
                if re.match(r'^\s*(\d+\.|\|)',ln) and '---' not in ln and '原积压' not in ln and '内容' not in ln[:8]:
                    acc.append((nm,ln.strip()))
q=[r for r in rows if r['状态']=='未扫']
w=[r for r in rows if r['状态']=='待复核']
o+=["","## 待复核（已从局部精读出卡，但本批未完整扫描）",""]
o+=[f"- `{r['id']}` p.{r['页']} —— 已出 {r['出卡数']} 张" for r in w] or ["（无）"]
o+=["","## 积压（纪律 5：同一主题第二次出现即成卡）",""]
o+=[f"- `{n}` {l}" for n,l in bl] or ["**0 条** ✅"]
o+=["","## 已排除（读过·判定不进流水线）",""]
o+=[f"- `{n}` {l}" for n,l in ex] or ["（无）"]
# 站点覆盖（纪律 7：全部标注 vs 首要站点，以首要为准）
from collections import Counter as _C
_all,_first=_C(),_C()
for f in glob.glob(f"{base}/卡/*.md"):
    _fm=_io.open(f,encoding='utf-8').read().split("---")[1]
    _v=(re.search(r'^站点:\s*(.*)$',_fm,re.M) or [None,''])[1]
    _t=re.findall(r'站[\w\d\-]+|通用',_v)
    for s in _t: _all[s]+=1
    if _t: _first[_t[0]]+=1
_CANON={'站0-形体卡','站1-场景卡','站2-拆镜','站2-人物基线','站3-景别机位','站4-关系轴线','站5-光色','站6-可见状态','通用'}
_badtag=sorted(set(_all)-_CANON)
o+=["","## 站点覆盖（纪律 7：以「首要」为准，「全部」含次要标注）","",
    ("- 标签校验：**✅ 全部在白名单内**" if not _badtag else f"- 标签校验：**⚠️ 白名单外的标签** {_badtag} — 拼写错误会造出幽灵站"),"",
    "| 站 | 首要 | 全部 | 判定 |","|---|---|---|---|"]
for k in ['站0-形体卡','站1-场景卡','站2-拆镜','站2-人物基线','站3-景别机位','站4-关系轴线','站5-光色','站6-可见状态','通用']:
    _n=_first.get(k,0)
    o.append(f"| {k} | **{_n}** | {_all.get(k,0)} | {'✅' if _n>=3 else ('🟡' if _n else '⬜ 空')} |")

# 跨书印证统计与对称性检查（纪律 10）
xb={}
for f in glob.glob(f"{base}/卡/*.md"):
    nm=os.path.basename(f)[:-3]
    _fm=_io.open(f,encoding='utf-8').read().split("---")[1]
    # 两种写法都认：行内列表 `跨书印证: [...]` 与多行 YAML 块（规范 §v0.4 的示例形态）
    _m=re.search(r'^跨书印证:[ \t]*(.*)$((?:\n[ \t]+-[ \t]*.*)*)',_fm,re.M)
    _v=((_m.group(1) or '')+' '+(_m.group(2) or '')) if _m else '[]'
    xb[nm]=(re.findall(r'\[\[([^\]]+)\]\]',_v), _v.strip() not in ('[]',''))
asym=[(a,x) for a,(ls,_) in xb.items() for x in ls if x in xb and a not in xb[x][0]]
nxb=sum(1 for v in xb.values() if v[1])
o+=["","## 跨书印证（纪律 9：必须双向）",""]
o+=[f"- 有跨书印证的卡：**{nxb} / {len(xb)}**（{nxb/len(xb)*100:.0f}%）"]
o+=["- 对称性检查：" + ("**✅ 全部双向**" if not asym else f"**⚠️ {len(asym)} 处单向** " + ", ".join(f"`{a}` → `{x}`" for a,x in asym))]
o+=["","| 卡 | 跨书印证 |","|---|---|"]
o+=[f"| [[{k}]] | {v[0] and '→ '+' · '.join(f'[[{x}]]' for x in v[0]) or '（对方未成卡）'} |" for k,v in sorted(xb.items()) if v[1]]
o+=["","## 下一批扫什么（未扫队列前 10）",""]
o+=[f"{i+1}. `{r['id']}` {r['书'][3:]} p.{r['页']}（{r['字符']:,} 字）" for i,r in enumerate(q[:10])]
io.open(f"{base}/_扫描索引.md","w",encoding='utf-8').write("\n".join(o)+"\n")

# ⭐ 派生质检清单：全库 失败模式 按站分组（质检不是一个站，是横切在每张卡里的一栏）
_qc={}
for _f in sorted(glob.glob(f"{base}/卡/*.md")):
    _nm=os.path.basename(_f)[:-3]
    _fm=_io0.open(_f,encoding='utf-8').read().split("---")[1]
    _g=lambda k:(re.search(rf'^{k}:\s*(.*)$',_fm,re.M) or [None,''])[1].strip()
    _fmode=_g('失败模式')
    if not _fmode or _fmode.startswith('（'): continue
    _st=(re.findall(r'站[\w\d\-]+|通用',_g('站点')) or ['未分站'])[0]
    _qc.setdefault(_st,[]).append((_nm,_fmode))
_q=["---","类型: 质检清单","说明: 本文件由 _重算索引.py 从全库卡片的「失败模式」字段派生，请勿手改","---","",
    "# 质检清单（派生·勿手改）","",
    "> **质检不是一个站，是横切在每张卡里的一栏。** 各站作业完成时，逐条比对本站的失败模式。","",
    f"全库 **{sum(len(v) for v in _qc.values())} 条**，覆盖 {len(_qc)} 个站。",""]
for _k in ['站0-形体卡','站1-场景卡','站2-拆镜','站2-人物基线','站3-景别机位','站4-关系轴线','站5-光色','站6-可见状态','通用','未分站']:
    if _k not in _qc: continue
    _q+=[f"## {_k}（{len(_qc[_k])} 条）",""]
    _q+=[f"- **[[{a}]]** — {c}" for a,c in _qc[_k]]
    _q+=[""]
io.open(f"{base}/_质检清单.md","w",encoding='utf-8').write("\n".join(_q)+"\n")
# ⭐ 派生检索索引：按站切分，每站一份（skill 取卡先读本站索引，再按需 Read 全卡）
# 全部字段派生自卡的 frontmatter，零人工。新卡自动纳入，不会变孤儿。
_REF=f"{os.path.expanduser('~')}/.claude/skills/storyboard/references"
_deep=set()
for _rf in glob.glob(f"{_REF}/*.md"):
    _deep|=set(re.findall(r'\[\[([A-Z]+-\d+)', _io0.open(_rf,encoding='utf-8').read()))
_idx={}
for _f in sorted(glob.glob(f"{base}/卡/*.md")):
    _bn=os.path.basename(_f)[:-3]
    _id=_bn.split(" ")[0]; _name=_bn[len(_id):].strip()
    _fm=_io0.open(_f,encoding='utf-8').read().split("---")[1]
    _g=lambda k:(re.search(rf'^{k}:\s*(.*)$',_fm,re.M) or [None,''])[1].strip()
    _sq=lambda v:v.strip('[]').replace(', ','/').replace('，','/').strip() or '—'
    # 场景类型是「限制标记」不是「分类」：空 ＝ 无人数限制（见 _抽取规范.md 纪律 13）
    _sc=_sq(_g('适用场景类型'))
    _row={'id':_id,'name':_name,'型':_g('型') or '—','景别':_sq(_g('适用景别')),
          '场景':'**无限制**' if _sc=='—' else f'⚠️{_sc}','反用':_g('可反用').lower()=='true',
          '前置':_sq(_g('前置条件')),'失败':_g('失败模式') or '—','深度':_id in _deep}
    for _s in (re.findall(r'站[\w\d\-]+|通用',_g('站点')) or ['未分站']):
        _idx.setdefault(_s,[]).append(_row)
_STATIONS=['站0-形体卡','站1-场景卡','站2-拆镜','站2-人物基线','站3-景别机位',
           '站4-关系轴线','站5-光色','站6-可见状态','未分站']
os.makedirs(f"{base}/_索引",exist_ok=True)
_gen=[]
_common=_idx.get('通用',[])
def _tbl(rows):
    out=["| 卡 | 型 | 适用景别 | 人数限制 | 什么时候需要它（失败模式） |","|---|---|---|---|---|"]
    for r in sorted(rows,key=lambda x:x['id']):
        _mk=('📖' if r['深度'] else '')+('🔄' if r['反用'] else '')+('🚧' if r['前置']!='—' else '')
        _f=r['失败'] + (f"　🚧**前置：{r['前置']}**" if r['前置']!='—' else '')
        out.append(f"| [[{r['id']} {r['name']}]] {_mk} | {r['型'][:3]} | {r['景别']} | {r['场景']} | {_f} |")
    return out
for _s in _STATIONS:
    if _s not in _idx: continue
    _rs=_idx[_s]
    _o=["---","类型: 检索索引","说明: 本文件由 _重算索引.py 从卡的 frontmatter 派生，请勿手改","---","",
        f"# 检索索引 · {_s}","",
        f"> **{len(_rs)} 张本站卡 ＋ {len(_common)} 张通用卡。** 先读本页选卡，再 Read 选中的那几张全卡。",
        "> 📖 ＝ `references/` 有深度蒸馏版，**读那份不读全卡** ｜ 🔄 ＝ 可反用 ｜ 🚧 ＝ **有项目级前置条件，不满足就整张不适用**",
        "> **人数限制**栏：`无限制` ＝ 单人戏也用得上；`⚠️对话/多人同场` ＝ **画面里得有 ≥2 人才适用**。","",
        f"## 本站（{len(_rs)} 张）",""]+_tbl(_rs)+["",f"## 通用（{len(_common)} 张，每站都适用）",""]+_tbl(_common)
    _p=f"{base}/_索引/{_s}.md"
    io.open(_p,"w",encoding='utf-8').write("\n".join(_o)+"\n")
    _gen.append((_s,len(_rs),os.path.getsize(_p)))

cards=len(glob.glob(f"{base}/卡/*.md")); cases=len(glob.glob(f"{base}/案例/*.md"))
print("检索索引已生成 → _索引/：")
for _s,_n,_b in _gen: print(f"  {_s:14s} {_n:3d}+{len(_common)}张  {_b:6,d} 字节 ≈ {_b//3:,} 汉字")
_covered=len({r['id'] for v in _idx.values() for r in v})
print(f"  覆盖 {_covered}/{cards} 张卡" + ("  ✅" if _covered==cards else "  ⚠️ 有卡未进任何索引"))
if _orphan or _mismatch:
    print("  ⚠️ 账目不一致：", f"无来源卡 {_orphan}" if _orphan else "", f"批次数不符 {_mismatch}" if _mismatch else "")
print(f"索引已重算：{len(done(rows))}/{len(rows)} 批已扫 | 卡 {cards} 张 | 范例 {cases} | 积压 {len(bl)} | 已排除 {len(ex)} | 跨书印证 {nxb} ({'对称✅' if not asym else f'单向⚠️{len(asym)}'})")
