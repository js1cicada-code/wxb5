#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票数据定时更新脚本
====================

功能：
    1. 定时运行所有爬虫更新数据
    2. 确保dist目录存在且可写
    3. 记录运行日志
    4. 支持设置更新间隔

使用方法：
    python scheduled_update.py          # 立即执行一次
    python scheduled_update.py --daemon # 守护进程模式
    python scheduled_update.py --cron   # 输出crontab配置

环境要求：
    - Python 3.6+
    - requests, beautifulsoup4
"""

import os
import sys
import json
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
DATA_DIR = PROJECT_DIR / "data"
LOG_FILE = PROJECT_DIR / "update.log"

CRAWLERS = [
    ('比赛数据匹配', 'match_engine.py'),
    ('竞彩足球/篮球', 'data_fetcher.py'),
    ('北京单场', 'bjdc_crawler.py'),
    ('胜负过关', 'sggg_crawler.py'),
    ('传统足彩/任选9', 'ctzc_crawler.py'),
    ('6场半全场', 'bqc6_crawler.py'),
    ('4场总进球', 'zjq4_crawler.py'),
    ('大乐透', 'dlt_crawler.py'),
    ('七星彩', 'qxc_crawler.py'),
    ('篮球分析', 'basketball_analysis_crawler.py'),
    ('比赛分析', 'analysis_crawler.py'),
]


def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')
    except:
        pass


def ensure_directories():
    """确保必要的目录存在且可写"""
    for dir_path in [DIST_DIR, DATA_DIR]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            log(f"创建目录: {dir_path}")
        
        if not os.access(dir_path, os.W_OK):
            log(f"错误: 目录不可写 {dir_path}")
            return False
    
    test_file = DIST_DIR / '.write_test'
    try:
        test_file.write_text('test')
        test_file.unlink()
    except Exception as e:
        log(f"错误: 目录写入测试失败 {DIST_DIR}: {e}")
        return False
    
    return True


def run_crawler(name, script):
    """运行单个爬虫"""
    script_path = PROJECT_DIR / script
    
    if not script_path.exists():
        log(f"  脚本不存在: {script}")
        return False, "脚本不存在"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_DIR)
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            summary = lines[-3:] if len(lines) > 3 else lines
            return True, '\n'.join(summary)
        else:
            error = result.stderr.strip()[-200:] if result.stderr else "未知错误"
            return False, error
            
    except subprocess.TimeoutExpired:
        return False, "执行超时"
    except Exception as e:
        return False, str(e)


def update_all():
    """更新所有数据"""
    log("=" * 60)
    log("开始更新彩票数据")
    log("=" * 60)
    
    if not ensure_directories():
        log("目录检查失败，终止更新")
        return False
    
    results = []
    success_count = 0
    
    for name, script in CRAWLERS:
        log(f"更新 {name}...")
        success, output = run_crawler(name, script)
        results.append((name, success, output))
        
        if success:
            success_count += 1
            log(f"  成功: {output[:100]}")
        else:
            log(f"  失败: {output[:100]}")
        
        time.sleep(1)
    
    log("=" * 60)
    log(f"更新完成: {success_count}/{len(CRAWLERS)} 成功")
    log("=" * 60)
    
    return success_count == len(CRAWLERS)


def run_daemon(interval_minutes=10):
    """守护进程模式"""
    log(f"启动守护进程模式，更新间隔: {interval_minutes} 分钟")
    
    while True:
        try:
            update_all()
        except Exception as e:
            log(f"更新异常: {e}")
        
        next_run = datetime.now().timestamp() + interval_minutes * 60
        next_time = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
        log(f"下次更新时间: {next_time}")
        
        time.sleep(interval_minutes * 60)


def print_cron_config():
    """打印crontab配置"""
    script_path = PROJECT_DIR / 'scheduled_update.py'
    python_path = sys.executable
    
    print("\n" + "=" * 60)
    print("Crontab 配置")
    print("=" * 60)
    print("\n# 彩票数据定时更新")
    print(f"# 每10分钟更新一次")
    print(f"*/10 * * * * {python_path} {script_path} >> {LOG_FILE} 2>&1")
    print("\n# 或者每小时更新一次")
    print(f"0 * * * * {python_path} {script_path} >> {LOG_FILE} 2>&1")
    print("\n# 添加到crontab:")
    print(f"crontab -e")
    print(f"# 粘贴上面的配置行")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='彩票数据定时更新脚本')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')
    parser.add_argument('--interval', type=int, default=10, help='更新间隔(分钟)，默认10')
    parser.add_argument('--cron', action='store_true', help='输出crontab配置')
    
    args = parser.parse_args()
    
    if args.cron:
        print_cron_config()
    elif args.daemon:
        run_daemon(args.interval)
    else:
        success = update_all()
        sys.exit(0 if success else 1)