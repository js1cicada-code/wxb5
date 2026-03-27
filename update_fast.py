#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速更新脚本 - 每5分钟运行一次
用于launchd定时任务
"""

import sys
import os

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 导入并运行爬虫
crawlers = [
    ('比分直播', 'live_crawler_final.py'),
]

for name, script in crawlers:
    print(f"\n{'='*50}")
    print(f"运行: {name}")
    print('='*50)
    
    try:
        with open(script, 'r', encoding='utf-8') as f:
            code = compile(f.read(), script, 'exec')
            exec(code)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()