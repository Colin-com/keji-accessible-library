#!/usr/bin/env bash
# 一键：创建公开仓库 → 推源码 → 开 GitHub Pages → 打印可玩链接
# 用法：bash tools/push_github.sh [仓库名]
set -e
NAME="${1:-keji-accessible-library}"

if ! gh auth status >/dev/null 2>&1; then
  echo "[授权] 需要你在浏览器确认一次："
  gh auth login --web --git-protocol https --hostname github.com
fi

OWNER=$(gh api user -q .login)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "[账号] $OWNER   [分支] $BRANCH"

git remote remove origin 2>/dev/null || true
if gh repo view "$OWNER/$NAME" >/dev/null 2>&1; then
  echo "[仓库] 已存在，直接加远端并推"
  git remote add origin "https://github.com/$OWNER/$NAME.git"
  git push -u origin "$BRANCH"
else
  gh repo create "$NAME" --public --source=. --remote=origin --push \
    --description "《可及》无障碍科普叙事游戏 · 网页像素 demo（117 节点 / 9 决策点 / 4 结局 / 10 条可溯源科普档案）"
fi

# 开 Pages（幂等：已开则忽略错误）
gh api -X POST "repos/$OWNER/$NAME/pages" \
  -f "source[branch]=$BRANCH" -f "source[path]=/" >/dev/null 2>&1 \
  || gh api -X PUT "repos/$OWNER/$NAME/pages" \
     -f "source[branch]=$BRANCH" -f "source[path]=/" >/dev/null 2>&1 || true

echo
echo "仓库：https://github.com/$OWNER/$NAME"
echo "可玩：https://$OWNER.github.io/$NAME/web/index.html"
echo "（Pages 首次生效约 1 分钟）"
