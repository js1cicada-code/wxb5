#!/bin/bash

PROJECT_DIR="/Users/bluekyo/Documents/wxingbaoh5"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/update_fast_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== 快速数据更新 (5分钟) ====="
cd "$PROJECT_DIR"

run_crawler() {
    local name=$1
    local script=$2
    local data_file=$3
    
    if [ ! -f "$PROJECT_DIR/$script" ]; then
        log "⊘ $name: 脚本不存在"
        return 1
    fi
    
    log "运行 $name..."
    if python3 "$script" 2>&1 >> "$LOG_FILE"; then
        log "✓ $name 成功"
        return 0
    else
        log "✗ $name 失败"
        return 1
    fi
}

run_crawler "北京单场" "bjdc_crawler.py" "dist/bjdc_data.json"

python3 check_data_freshness.py > /dev/null 2>&1
log "===== 快速更新完成 ====="