#!/usr/bin/env python3
import json
import os
from datetime import datetime

def get_file_count(pattern):
    count = 0
    for f in os.listdir('data'):
        if pattern in f and f.endswith('.json'):
            count += 1
    return count

def get_latest_update(pattern):
    latest = 0
    for f in os.listdir('data'):
        if pattern in f and f.endswith('.json'):
            path = os.path.join('data', f)
            mtime = os.path.getmtime(path)
            if mtime > latest:
                latest = mtime
    return datetime.fromtimestamp(latest).strftime('%Y-%m-%d %H:%M:%S') if latest > 0 else '-'

stats = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'analysis': {
        'football': {
            'count': get_file_count('analysis_') - get_file_count('basketball_analysis_'),
            'latest': get_latest_update('analysis_')
        },
        'basketball': {
            'count': get_file_count('basketball_analysis_'),
            'latest': get_latest_update('basketball_analysis_')
        }
    }
}

with open('data/stats.json', 'w', encoding='utf-8') as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"Stats generated: 足球分析 {stats['analysis']['football']['count']} 场, 篮球分析 {stats['analysis']['basketball']['count']} 场")