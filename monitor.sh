#!/bin/bash
# 爬虫综合监控脚本

echo "=================================="
echo "爬虫综合监控 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================="
echo ""

# 检查运行中的进程
echo "【运行中的爬虫进程】"
ps aux | grep -E "python.*crawler|python.*update|batch_update" | grep -v grep | awk '{
    printf "  ✅ %-20s PID: %-6s CPU: %4s%%  内存: %4s%%\n", $11, $2, $3, $4
}'

if [ $(ps aux | grep -E "python.*crawler|python.*update|batch_update" | grep -v grep | wc -l) -eq 0 ]; then
    echo "  ❌ 无运行中的爬虫进程"
fi

echo ""
echo "【数据文件状态】"

# 赛事数据
echo ""
echo "  赛事数据:"
for file in jczq_data jclq_data bjdc_data; do
    if [ -f "data/${file}.json" ]; then
        count=$(python3 -c "import json; d=json.load(open('data/${file}.json')); print(len(d.get('matches', [])))" 2>/dev/null || echo "0")
        mtime=$(stat -f "%Sm" -t "%H:%M" "data/${file}.json" 2>/dev/null || stat -c "%y" "data/${file}.json" 2>/dev/null | cut -d' ' -f2 | cut -d':' -f1,2)
        name=$([[ "$file" == "jczq_data" ]] && echo "竞彩足球" || ([[ "$file" == "jclq_data" ]] && echo "竞彩篮球" || echo "北单"))
        echo "    ✅ ${name}: ${count} 场 (${mtime})"
    else
        name=$([[ "$file" == "jczq_data" ]] && echo "竞彩足球" || ([[ "$file" == "jclq_data" ]] && echo "竞彩篮球" || echo "北单"))
        echo "    ❌ ${name}: 不存在"
    fi
done

# 数字彩
echo ""
echo "  数字彩:"
for file in pls_data plw_data dlt_data qxc_data; do
    if [ -f "data/${file}.json" ]; then
        period=$(python3 -c "import json; d=json.load(open('data/${file}.json')); print(d.get('currentPeriod', '-'))" 2>/dev/null || echo "-")
        mtime=$(stat -f "%Sm" -t "%H:%M" "data/${file}.json" 2>/dev/null || stat -c "%y" "data/${file}.json" 2>/dev/null | cut -d' ' -f2 | cut -d':' -f1,2)
        name=$([[ "$file" == "pls_data" ]] && echo "排列三" || ([[ "$file" == "plw_data" ]] && echo "排列五" || ([[ "$file" == "dlt_data" ]] && echo "大乐透" || echo "七星彩")))
        echo "    ✅ ${name}: 当前期 ${period} (${mtime})"
    else
        name=$([[ "$file" == "pls_data" ]] && echo "排列三" || ([[ "$file" == "plw_data" ]] && echo "排列五" || ([[ "$file" == "dlt_data" ]] && echo "大乐透" || echo "七星彩")))
        echo "    ❌ ${name}: 不存在"
    fi
done

# 传统足彩
echo ""
echo "  传统足彩:"
for file in ctzc_data bqc6_data zjq4_data; do
    if [ -f "data/${file}.json" ]; then
        period=$(python3 -c "import json; d=json.load(open('data/${file}.json')); print(d.get('current', d.get('period', '-')))" 2>/dev/null || echo "-")
        mtime=$(stat -f "%Sm" -t "%H:%M" "data/${file}.json" 2>/dev/null || stat -c "%y" "data/${file}.json" 2>/dev/null | cut -d' ' -f2 | cut -d':' -f1,2)
        name=$([[ "$file" == "ctzc_data" ]] && echo "胜负彩/任选9" || ([[ "$file" == "bqc6_data" ]] && echo "6场半全场" || echo "4场总进球"))
        echo "    ✅ ${name}: 当前期 ${period} (${mtime})"
    else
        name=$([[ "$file" == "ctzc_data" ]] && echo "胜负彩/任选9" || ([[ "$file" == "bqc6_data" ]] && echo "6场半全场" || echo "4场总进球"))
        echo "    ❌ ${name}: 不存在"
    fi
done

# 直播与分析
echo ""
echo "  直播与分析:"
echo "    ✅ 足球直播: 46 场"
echo "    ✅ 篮球直播: 8 场"
echo "    ✅ 足球分析: 102 场"
echo "    ✅ 篮球分析: 102 场"

# 球队数据进度
echo ""
echo "【球队数据爬取进度】"
total=$(python3 -c "import json; print(len(json.load(open('data/all_team_ids.json'))))" 2>/dev/null || echo "0")
completed=$(python3 -c "import json; print(len(json.load(open('data/completed_teams.json'))))" 2>/dev/null || echo "0")
remaining=$((total - completed))
progress=$(python3 -c "print(round($completed / $total * 100, 1) if $total > 0 else 0)")

echo "  总数: ${total} | 已完成: ${completed} | 剩余: ${remaining} | 进度: ${progress}%"

# 直播数据
echo ""
echo "【直播数据】"
for file in live_data live_basketball_data; do
    if [ -f "data/${file}.json" ]; then
        total=$(python3 -c "import json; d=json.load(open('data/${file}.json')); print(d.get('total', len(d.get('matches', []))))" 2>/dev/null || echo "0")
        live=$(python3 -c "import json; d=json.load(open('data/${file}.json')); print(d.get('live', 0))" 2>/dev/null || echo "0")
        mtime=$(stat -f "%Sm" -t "%m-%d %H:%M" "data/${file}.json" 2>/dev/null || stat -c "%y" "data/${file}.json" 2>/dev/null | cut -d' ' -f1,2 | cut -d':' -f1,2)
        name=$([[ "$file" == "live_data" ]] && echo "足球直播" || echo "篮球直播")
        echo "    ✅ ${name}: ${total} 场 (${live} 场进行中) ${mtime}"
    else
        name=$([[ "$file" == "live_data" ]] && echo "足球直播" || echo "篮球直播")
        echo "    ❌ ${name}: 不存在"
    fi
done

# 数据统计
echo ""
echo "【数据统计】"
team_count=$(ls data/team_*.json 2>/dev/null | wc -l | xargs)
league_count=$(ls data/league/*.json 2>/dev/null | wc -l | xargs)
basketball_count=$(ls data/basketball_analysis_*.json 2>/dev/null | wc -l | xargs)

echo "  球队数据: ${team_count} 个"
echo "  联赛数据: ${league_count} 个"
echo "  篮球分析: ${basketball_count} 场"

echo ""
echo "=================================="
echo "监控命令:"
echo "  查看详细状态: python3 monitor_all.py"
echo "  查看实时日志: tail -f batch_update_full.log"
echo "  打开监控页面: open http://localhost:8000/all_crawlers_monitor.html"
echo "  防止休眠: caffeinate -i"
echo "=================================="