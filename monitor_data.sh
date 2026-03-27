#!/bin/bash

PROJECT_DIR="/Users/bluekyo/Documents/wxingbaoh5"
STATUS_FILE="$PROJECT_DIR/data_status.json"
ALERT_FILE="$PROJECT_DIR/data_alert.json"

check_and_alert() {
    python3 "$PROJECT_DIR/check_data_freshness.py"
    
    if [ -f "$STATUS_FILE" ]; then
        status=$(python3 -c "
import json
with open('$STATUS_FILE') as f:
    data = json.load(f)
print(data.get('status', 'unknown'))
" 2>/dev/null)
        
        if [ "$status" = "critical" ]; then
            echo "[CRITICAL] 多个数据文件过期或缺失，请立即处理"
        elif [ "$status" = "warning" ]; then
            echo "[WARNING] 部分数据文件需要更新"
        fi
    fi
}

check_and_alert