#!/bin/bash
# 彩票数据定时更新脚本
# 由cron定时调用，更新后自动同步到GitHub

cd /Users/bluekyo/Documents/wxingbaoh5

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_FILE="/Users/bluekyo/Documents/wxingbaoh5/cron_update.log"
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始更新" >> "$LOG_FILE"

/usr/bin/python3 /Users/bluekyo/Documents/wxingbaoh5/update_all.py >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') 更新完成" >> "$LOG_FILE"

if git diff --quiet data/ dist/*.json dist/data/*.json 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') 无数据变更" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') 提交数据到GitHub..." >> "$LOG_FILE"
    git add data/ dist/*.json dist/data/*.json >> "$LOG_FILE" 2>&1
    git commit -m "$(date '+%Y-%m-%d %H:%M') 数据更新" >> "$LOG_FILE" 2>&1
    git push origin main >> "$LOG_FILE" 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') 已同步到GitHub" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"