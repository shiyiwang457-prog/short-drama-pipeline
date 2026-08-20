#!/usr/bin/env bash
# 短剧生产三环流水线 · 安装脚本
#
#   bash install.sh                    装到默认位置 ~/Desktop/11/_规则库/
#   bash install.sh ~/我的仓库          装到自定义位置（会自动改 skill 里的路径）
#
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$HOME/Desktop/11}"
VAULT="${VAULT/#\~/$HOME}"
RULES="$VAULT/_规则库"
SKILLS="$HOME/.claude/skills"

echo "════════════════════════════════════════════"
echo "  短剧生产三环流水线 · 安装"
echo "════════════════════════════════════════════"
echo "  规则库 → $RULES"
echo "  skill  → $SKILLS"
echo ""

# ── 1 · 前置检查
if [ ! -d "$HOME/.claude" ]; then
  echo "🔴 找不到 ~/.claude —— 这台电脑还没装过 Claude Code。"
  echo "   先装 Claude Code，跑一次让它建好 ~/.claude，再回来跑这个脚本。"
  exit 1
fi
mkdir -p "$SKILLS" "$RULES"

# ── 2 · 已存在则先备份，不覆盖用户已有的东西
STAMP="$(date +%Y%m%d-%H%M%S)"
for s in story-doctor storyboard prompt-assembly; do
  if [ -d "$SKILLS/$s" ]; then
    mv "$SKILLS/$s" "$SKILLS/$s.bak-$STAMP"
    echo "  ⚠️  已存在的 $s 备份为 $s.bak-$STAMP"
  fi
done
if [ -n "$(ls -A "$RULES" 2>/dev/null)" ]; then
  mv "$RULES" "$RULES.bak-$STAMP"
  mkdir -p "$RULES"
  echo "  ⚠️  已存在的规则库备份为 $(basename "$RULES").bak-$STAMP"
fi

# ── 3 · 复制
cp -R "$HERE/skills/"* "$SKILLS/"
cp -R "$HERE/规则库/"* "$RULES/"
echo "  ✅ 已复制"

# ── 4 · 自定义路径时，改掉 skill 里写死的 ~/Desktop/11/
if [ "$VAULT" != "$HOME/Desktop/11" ]; then
  SHORT="~${VAULT#$HOME}"
  n=0
  for f in "$SKILLS"/{story-doctor,storyboard,prompt-assembly}/**/*.md \
           "$SKILLS"/{story-doctor,storyboard,prompt-assembly}/*.md; do
    [ -f "$f" ] || continue
    if grep -q '~/Desktop/11/' "$f" 2>/dev/null; then
      perl -i -pe "s{~/Desktop/11/}{$SHORT/}g" "$f"
      n=$((n+1))
    fi
  done
  echo "  ✅ 已把 $n 个 skill 文件里的路径改成 $SHORT/"
fi

# ── 5 · 自检：数对不对、脚本跑不跑得动
echo ""
echo "──────── 自检 ────────"
CARDS=$(ls "$RULES/卡" 2>/dev/null | wc -l | tr -d ' ')
IDX=$(ls "$RULES/_索引" 2>/dev/null | wc -l | tr -d ' ')
CASES=$(ls "$RULES/案例" 2>/dev/null | wc -l | tr -d ' ')
printf "  书证卡      %3s 张   %s\n" "$CARDS" "$([ "$CARDS" -ge 112 ] && echo ✅ || echo 🔴)"
printf "  站点索引    %3s 个   %s\n" "$IDX"   "$([ "$IDX"   -ge 9   ] && echo ✅ || echo 🔴)"
printf "  案例        %3s 个   %s\n" "$CASES" "$([ "$CASES" -ge 9   ] && echo ✅ || echo 🔴)"
for s in story-doctor storyboard prompt-assembly; do
  printf "  skill %-16s %s\n" "$s" "$([ -f "$SKILLS/$s/SKILL.md" ] && echo ✅ || echo 🔴)"
done

# 门禁脚本拿样例真跑一次 —— 装完就证明能用，不靠"应该没问题"
GATE="$SKILLS/prompt-assembly/tools/check_gates.py"
SAMPLE="$HERE/样例-纪念日/提示词表-v7.md"
if [ -f "$GATE" ] && [ -f "$SAMPLE" ]; then
  echo ""
  echo "  ── 用样例真跑一遍门禁（这一步过了才算装成）"
  if python3 "$GATE" "$SAMPLE" 2>&1 | tail -3 | sed 's/^/     /'; then
    python3 "$SKILLS/prompt-assembly/tools/check_props.py" "$SAMPLE" 2>&1 | tail -1 | sed 's/^/     /'
  fi
fi

echo ""
echo "════════════════════════════════════════════"
echo "  装完了。开一个新的 Claude Code 窗口，说："
echo ""
echo "     「用 storyboard 做《XXX》场 1 的分镜」"
echo "     「用 prompt-assembly 装配提示词」"
echo ""
echo "  规则库在 $RULES"
echo "  ⚠️  新窗口才会加载新 skill，当前窗口不会"
echo "════════════════════════════════════════════"
