#!/bin/bash

PROJECT_DIR="/Users/bluekyo/Documents/wxingbaoh5"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/update_medium_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "===== 中频数据更新 (10分钟) ====="
cd "$PROJECT_DIR"

ERROR_COUNT=0

run_crawler() {
    local name=$1
    local script=$2
    
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
        ERROR_COUNT=$((ERROR_COUNT + 1))
        return 1
    fi
}

run_crawler "胜负过关" "sggg_crawler.py"
run_crawler "传统足彩14场/任选9场" "ctzc_crawler.py"
run_crawler "6场半全场" "bqc6_crawler.py"
run_crawler "4场总进球" "zjq4_crawler.py"
run_crawler "单关状态" "single_pass_crawler.py"
run_crawler "比赛分析" "analysis_crawler.py"
run_crawler "篮球分析" "basketball_analysis_crawler.py"

python3 check_data_freshness.py > /dev/null 2>&1
log "===== 中频更新完成 (错误: $ERROR_COUNT) ====="