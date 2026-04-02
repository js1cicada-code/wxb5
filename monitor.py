#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的爬虫监控 - 直接输出HTML
"""

import json
import os
import subprocess
from datetime import datetime

def get_stats():
    """获取统计信息"""
    try:
        with open('data/all_team_ids.json', 'r') as f:
            all_ids = json.load(f)
        
        completed = []
        if os.path.exists('data/completed_teams.json'):
            with open('data/completed_teams.json', 'r') as f:
                completed = json.load(f)
        
        total = len(all_ids)
        completed_count = len(completed)
        progress = (completed_count / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'completed': completed_count,
            'progress': round(progress, 2),
            'remaining': total - completed_count,
            'completed_list': completed
        }
    except Exception as e:
        return {'error': str(e)}

def get_process_status():
    """获取进程状态"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        for line in result.stdout.split('\n'):
            if 'batch_update_teams.py' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 11:
                    return {
                        'running': True,
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3],
                        'time': parts[9]
                    }
        
        return {'running': False}
    except Exception as e:
        return {'error': str(e)}

def get_recent_logs(lines=50):
    """获取最近的日志"""
    try:
        if os.path.exists('batch_update_full.log'):
            with open('batch_update_full.log', 'r') as f:
                all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:] if line.strip()]
        return []
    except Exception as e:
        return [f"Error: {e}"]

def main():
    stats = get_stats()
    process = get_process_status()
    logs = get_recent_logs()
    
    print("=" * 60)
    print("爬虫监控面板")
    print("=" * 60)
    print(f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("【统计信息】")
    print(f"  总球队数: {stats.get('total', 0)}")
    print(f"  已完成: {stats.get('completed', 0)}")
    print(f"  剩余: {stats.get('remaining', 0)}")
    print(f"  进度: {stats.get('progress', 0)}%")
    
    progress_bar = int(stats.get('progress', 0) / 2)
    print(f"  [{'#' * progress_bar}{' ' * (50 - progress_bar)}]")
    
    print(f"\n【进程状态】")
    if process.get('running'):
        print(f"  ✅ 运行中")
        print(f"  PID: {process['pid']}")
        print(f"  CPU: {process['cpu']}%")
        print(f"  内存: {process['mem']}%")
        print(f"  运行时间: {process['time']}")
    else:
        print(f"  ❌ 已停止")
    
    print(f"\n【最近日志】")
    for log in logs[-10:]:
        # 高亮错误
        if '失败' in log or '错误' in log:
            print(f"  ❌ {log[:80]}")
        elif '成功' in log or '保存' in log:
            print(f"  ✅ {log[:80]}")
        else:
            print(f"  ℹ️  {log[:80]}")
    
    print("\n" + "=" * 60)
    print("监控命令:")
    print("  查看实时日志: tail -f batch_update_full.log")
    print("  打开监控页面: open http://localhost:8000/crawler_monitor.html")
    print("  防止休眠: caffeinate -i -w $(pgrep -f batch_update_teams.py)")
    print("=" * 60)

if __name__ == '__main__':
    main()