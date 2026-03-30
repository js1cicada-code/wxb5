#!/bin/bash

PROJECT_DIR="/Users/bluekyo/Documents/wxingbaoh5"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/update_$(date +%Y%m%d).log"
ALERT_FILE="$PROJECT_DIR/data_alert.json"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== 数据更新开始 =========="

cd "$PROJECT_DIR"

ERROR_COUNT=0
SUCCESS_COUNT=0
TOTAL_COUNT=0

run_crawler() {
    local name=$1
    local script=$2
    local data_file=$3
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    if [ ! -f "$PROJECT_DIR/$script" ]; then
        log "⊘ $name: 爬虫脚本不存在 ($script)"
        return
    fi
    
    log "运行 $name 爬虫..."
    output=$(python3 "$script" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "✓ $name 更新成功"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        if [ -f "$PROJECT_DIR/$data_file" ]; then
            update_time=$(python3 -c "
import json
try:
    with open('$PROJECT_DIR/$data_file') as f:
        data = json.load(f)
    print(data.get('updateTime', 'unknown'))
except:
    print('error')
" 2>/dev/null)
            log "  数据文件: $data_file"
            log "  更新时间: $update_time"
        fi
    else
        log "✗ $name 更新失败 (exit code: $exit_code)"
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
}

run_crawler "足球直播数据" "live_crawler_final.py" "data/live_data.json"
run_crawler "比赛匹配引擎" "match_engine.py" "data/fixture_mapping.json"
run_crawler "北京单场" "bjdc_crawler.py" "dist/bjdc_data.json"
run_crawler "胜负过关" "sggg_crawler.py" "dist/sggg_data.json"
run_crawler "传统足彩14场/任选9场" "ctzc_crawler.py" "dist/ctzc_data.json"
run_crawler "6场半全场" "bqc6_crawler.py" "dist/bqc6_data.json"
run_crawler "4场总进球" "zjq4_crawler.py" "dist/zjq4_data.json"
run_crawler "大乐透" "dlt_crawler.py" "dist/dlt_data.json"
run_crawler "七星彩" "qxc_crawler.py" "dist/qxc_data.json"
run_crawler "单关状态" "single_pass_crawler.py" "dist/single_pass.json"
run_crawler "比赛分析" "analysis_crawler.py" "dist/fixture_mapping.json"
run_crawler "篮球分析" "basketball_analysis_crawler.py" "dist/basketball_matches.json"

python3 check_data_freshness.py > /dev/null 2>&1

log "========== 数据更新完成 =========="
log "成功: $SUCCESS_COUNT/$TOTAL_COUNT"
log "失败: $ERROR_COUNT/$TOTAL_COUNT"

if [ $ERROR_COUNT -gt 0 ]; then
    log "⚠ 存在更新失败的爬虫，请检查日志: $LOG_FILE"
    exit 1
fi

exit 0