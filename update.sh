#!/bin/bash
# 一键更新：从 Liquipedia 拉最新赛程 → 生成 major.ics → 推到 GitHub
set -e
cd "$(dirname "$0")"
python3 scripts/sync.py --contact-url https://github.com/ChihayaAnon9888/-Singapore-Major-Match-Calendar-
python3 scripts/build.py
cp dist/major.ics major.ics
git add major.ics data/schedule.json
if git diff --cached --quiet; then
  echo "赛程没有变化，不用推送。"
else
  git commit -m "Update schedule $(date '+%Y-%m-%d %H:%M')"
  git push
  echo "已推送，订阅者会在日历刷新时收到更新。"
fi
