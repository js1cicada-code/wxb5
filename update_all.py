#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一启动脚本 - 更新所有彩票数据
所有爬虫统一保存到 dist/data/ 目录
"""

import subprocess
import sys
import os
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def run_crawler(name, script, timeout=180):
    """运行爬虫脚本"""
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 更新 {name}...")
    print('='*50)
    
    script_path = os.path.join(SCRIPTS_DIR, script)
    if not os.path.exists(script_path):
        print(f"  跳过: 脚本不存在")
        return None
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[-8:]:
                if line.strip():
                    print(f"  {line}")
            return True
        else:
            print(f"  错误: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  超时: 超过{timeout}秒")
        return False
    except Exception as e:
        print(f"  执行失败: {e}")
        return False

def main():
    print("="*60)
    print(f"彩票数据全量更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("数据保存目录: dist/data/")
    print("="*60)
    
    crawlers = [
        ('比分直播-足球', 'live_crawler_final.py', 120),
        ('比分直播-篮球', 'live_basketball_crawler.py', 180),
        ('北京单场', 'bjdc_crawler.py', 60),
        ('胜负过关', 'sggg_crawler.py', 60),
        ('传统足彩14场', 'ctzc_crawler.py', 60),
        ('6场半全场', 'bqc6_crawler.py', 60),
        ('4场总进球', 'zjq4_crawler.py', 60),
        ('大乐透', 'dlt_crawler.py', 60),
        ('七星彩', 'qxc_crawler.py', 60),
        ('排列三/五', 'pl_crawler.py', 60),
        ('竞彩足球分析', 'analysis_crawler.py', 300),
        ('竞彩篮球分析', 'basketball_analysis_crawler.py', 300),
    ]
    
    results = []
    for name, script, timeout in crawlers:
        success = run_crawler(name, script, timeout)
        results.append((name, success))
    
    print("\n" + "="*60)
    print("更新结果汇总")
    print("="*60)
    
    success_count = 0
    for name, success in results:
        if success is None:
            status = "⊘ 跳过"
        elif success:
            status = "✓ 成功"
            success_count += 1
        else:
            status = "✗ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n完成: {success_count}/{len([r for r in results if r[1] is not None])} 个成功")
    print(f"数据目录: dist/data/")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()