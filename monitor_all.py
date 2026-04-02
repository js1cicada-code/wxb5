#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整爬虫监控面板
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def get_file_info(filepath):
    """获取文件信息"""
    if not os.path.exists(filepath):
        return None
    
    stat = os.stat(filepath)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    size = stat.st_size
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict):
                count = len(data)
            else:
                count = 0
        return {
            'exists': True,
            'mtime': mtime,
            'size': size,
            'count': count
        }
    except:
        return {
            'exists': True,
            'mtime': mtime,
            'size': size,
            'count': 0,
            'error': True
        }

def get_process_status():
    """获取所有爬虫进程状态"""
    processes = []
    
    # 检查各种爬虫进程
    crawler_patterns = [
        ('球队爬虫', 'batch_update_teams.py'),
        ('竞彩爬虫', 'crawler.py'),
        ('北单爬虫', 'bjdc_crawler.py'),
        ('大乐透爬虫', 'dlt_crawler.py'),
        ('七星彩爬虫', 'qxc_crawler.py'),
        ('定时更新', 'scheduled_update.py'),
        ('足球分析', 'analysis_crawler.py'),
        ('篮球分析', 'basketball_analysis_crawler.py'),
        ('直播爬虫', 'live_crawler'),
    ]
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        for name, pattern in crawler_patterns:
            for line in result.stdout.split('\n'):
                if pattern in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            'name': name,
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'time': parts[9],
                            'running': True
                        })
                        break
    except Exception as e:
        pass
    
    return processes

def check_crawlers():
    """检查所有爬虫和数据状态"""
    
    # 数据文件配置
    data_configs = {
        '赛事数据': {
            '竞彩足球': 'data/jczq_data.json',
            '竞彩篮球': 'data/jclq_data.json',
            '北单': 'data/bjdc_data.json',
        },
        '数字彩': {
            '排列三': 'data/pls_data.json',
            '排列五': 'data/plw_data.json',
            '大乐透': 'data/dlt_data.json',
            '七星彩': 'data/qxc_data.json',
        },
        '传统足彩': {
            '胜负彩/任选9': 'data/ctzc_data.json',
            '6场半全场': 'data/bqc6_data.json',
            '4场总进球': 'data/zjq4_data.json',
        },
        '直播数据': {
            '足球直播': 'data/live_data.json',
            '篮球直播': 'data/live_basketball_data.json',
        },
        '分析数据': {
            '足球分析': 'data/analysis_data.json',
            '篮球分析': 'data/basketball_analysis',
        },
        '球队数据': {
            '球队详情': 'data/',
            '联赛数据': 'data/league/',
        }
    }
    
    results = {}
    
    for category, items in data_configs.items():
        results[category] = {}
        for name, filepath in items.items():
            if filepath.endswith('/'):
                # 目录
                if os.path.exists(filepath):
                    count = len([f for f in os.listdir(filepath) if f.endswith('.json')])
                    results[category][name] = {
                        'exists': True,
                        'count': count,
                        'type': 'directory'
                    }
                else:
                    results[category][name] = {'exists': False}
            else:
                # 文件
                info = get_file_info(filepath)
                if info:
                    results[category][name] = info
                else:
                    results[category][name] = {'exists': False}
    
    return results

def get_time_diff(mtime):
    """获取时间差"""
    now = datetime.now()
    diff = now - mtime
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600}小时前"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60}分钟前"
    else:
        return "刚刚"

def main():
    print("=" * 80)
    print("爬虫监控面板 - 综合状态")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 检查进程状态
    processes = get_process_status()
    print("【运行中的进程】")
    if processes:
        for proc in processes:
            print(f"  [运行] {proc['name']:12s} | PID: {proc['pid']:6s} | CPU: {proc['cpu']:4s}% | 内存: {proc['mem']:4s}% | 时间: {proc['time']}")
    else:
        print("  [停止] 无运行中的爬虫进程")
    
    print("\n" + "=" * 80)
    
    # 检查数据状态
    crawler_data = check_crawlers()
    
    for category, items in crawler_data.items():
        print(f"\n【{category}】")
        for name, info in items.items():
            if info.get('exists'):
                if info.get('type') == 'directory':
                    print(f"  [正常] {name:12s}: {info['count']} 个文件")
                elif info.get('error'):
                    print(f"  [警告] {name:12s}: 文件格式错误")
                else:
                    time_diff = get_time_diff(info['mtime'])
                    print(f"  [正常] {name:12s}: {time_diff:8s} | {info['size']:>8,} bytes | {info['count']} 条记录")
            else:
                print(f"  [缺失] {name:12s}: 文件不存在")
    
    # 统计信息
    print("\n" + "=" * 80)
    print("【数据统计】")
    
    # 球队数据
    team_files = len([f for f in os.listdir('data') if f.startswith('team_') and f.endswith('.json')])
    completed_teams = 0
    if os.path.exists('data/completed_teams.json'):
        with open('data/completed_teams.json', 'r') as f:
            completed_teams = len(json.load(f))
    
    print(f"  球队数据: {team_files} 个文件 (已完成: {completed_teams}/1263)")
    
    # 篮球分析
    basketball_analysis = len([f for f in os.listdir('data') if f.startswith('basketball_analysis_')])
    print(f"  篮球分析: {basketball_analysis} 场比赛")
    
    # 联赛数据
    league_files = len([f for f in os.listdir('data/league') if f.endswith('.json')]) if os.path.exists('data/league') else 0
    print(f"  联赛数据: {league_files} 个文件")
    
    print("\n" + "=" * 80)
    print("监控命令:")
    print("  启动所有爬虫: python3 scheduled_update.py")
    print("  查看实时日志: tail -f update.log")
    print("  防止休眠: caffeinate -i")
    print("=" * 80)

if __name__ == '__main__':
    main()