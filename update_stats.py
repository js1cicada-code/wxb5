#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新stats.json统计信息
"""

import json
import glob
from datetime import datetime
from pathlib import Path

def update_stats():
    """更新统计数据"""
    
    # 统计足球分析
    football_files = glob.glob('data/analysis_*.json')
    basketball_files = glob.glob('data/basketball_analysis_*.json')
    
    football_latest = ''
    basketball_latest = ''
    
    if football_files:
        latest_fb = max(football_files, key=lambda f: Path(f).stat().st_mtime)
        try:
            with open(latest_fb, 'r') as f:
                data = json.load(f)
                football_latest = data.get('update_time', '')
        except:
            pass
    
    if basketball_files:
        latest_bb = max(basketball_files, key=lambda f: Path(f).stat().st_mtime)
        try:
            with open(latest_bb, 'r') as f:
                data = json.load(f)
                basketball_latest = data.get('update_time', '')
        except:
            pass
    
    stats = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'analysis': {
            'football': {
                'count': len(football_files),
                'latest': football_latest
            },
            'basketball': {
                'count': len(basketball_files),
                'latest': basketball_latest
            }
        }
    }
    
    # 保存到多个位置
    for path in ['data/stats.json', 'dist/data/stats.json', 'dist/stats.json']:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(stats, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存{path}失败: {e}")
    
    print(f"足球分析: {len(football_files)} 场")
    print(f"篮球分析: {len(basketball_files)} 场")
    print(f"stats.json已更新")

if __name__ == '__main__':
    update_stats()
