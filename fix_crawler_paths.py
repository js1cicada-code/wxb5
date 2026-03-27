#!/usr/bin/env python3
"""统一所有爬虫的保存路径到 dist/data/"""

import os
import re

CRAWLERS = [
    'live_crawler_final.py',
    'live_basketball_crawler.py',
    'analysis_crawler.py',
    'basketball_analysis_crawler.py',
    'bjdc_crawler.py',
    'sggg_crawler.py',
    'ctzc_crawler.py',
    'bqc6_crawler.py',
    'zjq4_crawler.py',
    'dlt_crawler.py',
    'qxc_crawler.py',
    'pl_crawler.py',
    'live_crawler.py',
    'live_selenium_crawler.py',
    'live_playwright_crawler.py',
    'football_rank_crawler.py',
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_DATA_DIR = "os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')"

for crawler in CRAWLERS:
    filepath = os.path.join(BASE_DIR, crawler)
    if not os.path.exists(filepath):
        print(f"跳过: {crawler} (不存在)")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 替换 DIST_DIR 和 DATA_DIR 定义
    # 模式1: DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
    content = re.sub(
        r"DATA_DIR\s*=\s*os\.path\.join\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\),\s*['\"]data['\"]\)",
        f"DATA_DIR = {NEW_DATA_DIR}",
        content
    )
    content = re.sub(
        r"DIST_DIR\s*=\s*os\.path\.join\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\),\s*['\"]dist['\"]\)",
        f"DIST_DIR = {NEW_DATA_DIR}",
        content
    )
    
    # 替换 OUTPUT_FILE
    content = re.sub(
        r"OUTPUT_FILE\s*=\s*['\"]dist/([^'\"]+)['\"]",
        r"OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data', '\1')",
        content
    )
    
    # 替换 filepath = os.path.join(script_dir, 'dist', ...)
    content = re.sub(
        r"filepath\s*=\s*os\.path\.join\(script_dir,\s*['\"]dist['\"]",
        "filepath = os.path.join(script_dir, 'dist', 'data'",
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 已更新: {crawler}")
    else:
        print(f"  无变化: {crawler}")

print("\n完成!")
