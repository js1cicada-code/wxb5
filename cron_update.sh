#!/bin/bash
# 彩票数据定时更新脚本
# 由cron定时调用

cd /Users/bluekyo/Documents/wxingbaoh5

# 设置环境变量
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# 记录日志
LOG_FILE="/Users/bluekyo/Documents/wxingbaoh5/cron_update.log"
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') 开始更新" >> "$LOG_FILE"

# 运行更新脚本
/usr/bin/python3 /Users/bluekyo/Documents/wxingbaoh5/update_all.py >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') 更新完成" >> "$LOG_FILE"