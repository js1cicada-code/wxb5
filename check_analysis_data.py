#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析数据完整性检查脚本
检查足球和篮球分析数据是否正常生成
"""

import json
import glob
from pathlib import Path
from datetime import datetime

def check_analysis_data():
    """检查分析数据完整性"""
    
    # 统计文件数量
    football_files = glob.glob('data/analysis_*.json')
    basketball_files = glob.glob('data/basketball_analysis_*.json')
    
    # 获取比赛数据
    try:
        with open('data/jczq_data.json', 'r') as f:
            jczq = json.load(f)
            football_matches = len(jczq.get('matches', []))
    except:
        football_matches = 0
    
    try:
        with open('data/jclq_data.json', 'r') as f:
            jclq = json.load(f)
            basketball_matches = len(jclq.get('matches', []))
    except:
        basketball_matches = 0
    
    # 检查数据完整性
    football_complete = len(football_files) >= football_matches * 0.8  # 至少80%
    basketball_complete = len(basketball_files) >= basketball_matches * 0.8
    
    # 生成报告
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'football': {
            'matches': football_matches,
            'analysis_files': len(football_files),
            'complete': football_complete,
            'coverage': f"{len(football_files)}/{football_matches}" if football_matches > 0 else "0/0"
        },
        'basketball': {
            'matches': basketball_matches,
            'analysis_files': len(basketball_files),
            'complete': basketball_complete,
            'coverage': f"{len(basketball_files)}/{basketball_matches}" if basketball_matches > 0 else "0/0"
        },
        'status': 'OK' if (football_complete and basketball_complete) else 'WARNING'
    }
    
    # 打印报告
    print("=" * 60)
    print("分析数据完整性检查报告")
    print("=" * 60)
    print(f"时间: {report['timestamp']}")
    print(f"状态: {report['status']}")
    print()
    print(f"足球分析:")
    print(f"  比赛场次: {report['football']['matches']}")
    print(f"  分析文件: {report['football']['analysis_files']}")
    print(f"  覆盖率: {report['football']['coverage']}")
    print(f"  完整性: {'✓' if report['football']['complete'] else '✗'}")
    print()
    print(f"篮球分析:")
    print(f"  比赛场次: {report['basketball']['matches']}")
    print(f"  分析文件: {report['basketball']['analysis_files']}")
    print(f"  覆盖率: {report['basketball']['coverage']}")
    print(f"  完整性: {'✓' if report['basketball']['complete'] else '✗'}")
    print("=" * 60)
    
    # 保存报告
    with open('data/analysis_check_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report['status'] == 'OK'

if __name__ == '__main__':
    import sys
    success = check_analysis_data()
    sys.exit(0 if success else 1)
