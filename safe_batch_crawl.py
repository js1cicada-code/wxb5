#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全批量爬取所有球队详情数据 - 防止被WAF拦截
"""

import json
import time
import random
import os
import requests

BASE_URL = "https://zq.titan007.com"
TEAM_DETAIL_URL = BASE_URL + "/jsData/teamInfo/teamDetail/tdl{team_id}.js"
TEAM_HISTORY_URL = BASE_URL + "/cn/team/TeamHistoryOrder/{team_id}.html"
TEAM_TRANSFER_URL = BASE_URL + "/cn/team/PlayerZhAjax.aspx?matchSeason=2025-2026&teamID={team_id}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': BASE_URL + '/',
}

CONFIG = {
    'delay_min': 3,
    'delay_max': 6,
    'waf_wait': 60,
    'max_retries': 5
}

progress_file = 'data/crawl_progress.json'

def load_progress():
    """加载爬取进度"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': []}

def save_progress(progress):
    """保存爬取进度"""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def wait_random():
    """随机等待"""
    delay = random.uniform(CONFIG['delay_min'], CONFIG['delay_max'])
    print(f"  等待 {delay:.1f} 秒...")
    time.sleep(delay)

def check_waf(response):
    """检查是否被WAF拦截"""
    if response.status_code == 442 or 'WAF' in response.text:
        print(f"\n⚠️  被WAF拦截! 等待 {CONFIG['waf_wait']} 秒...")
        time.sleep(CONFIG['waf_wait'])
        return True
    return False

def safe_request(url, retry_count=0):
    """安全的请求，带WAF检测"""
    if retry_count >= CONFIG['max_retries']:
        return None
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        
        if check_waf(response):
            return safe_request(url, retry_count + 1)
        
        if response.status_code == 200 and len(response.text) > 100:
            return response.text
        
    except Exception as e:
        print(f"  请求失败: {e}")
        if retry_count < CONFIG['max_retries']:
            time.sleep(5)
            return safe_request(url, retry_count + 1)
    
    return None

def crawl_team_safe(team_id, progress):
    """安全爬取单个球队"""
    if team_id in progress['completed']:
        print(f"  球队 {team_id} 已完成，跳过")
        return True
    
    print(f"\n[{len(progress['completed']) + 1}] 爬取球队 {team_id}...")
    
    # 导入爬虫函数
    from team_crawler import parse_team_detail, save_team_data
    
    # 获取球队详情
    url = TEAM_DETAIL_URL.format(team_id=team_id)
    js_content = safe_request(url)
    
    if not js_content:
        print(f"  ✗ 获取球队详情失败")
        progress['failed'].append(team_id)
        save_progress(progress)
        return False
    
    wait_random()
    
    # 解析数据
    result = parse_team_detail(js_content, team_id)
    
    if not result or not result.get('detail'):
        print(f"  ✗ 解析失败")
        progress['failed'].append(team_id)
        save_progress(progress)
        return False
    
    # 保存数据
    save_team_data(result, team_id)
    
    progress['completed'].append(team_id)
    save_progress(progress)
    
    team_name = result['detail'].get('name_cn', 'Unknown')
    print(f"  ✓ 成功: {team_name}")
    
    return True

def batch_crawl_safe():
    """安全批量爬取"""
    # 加载球队列表
    with open('data/all_team_ids.json', 'r') as f:
        team_ids = json.load(f)
    
    total = len(team_ids)
    
    # 加载进度
    progress = load_progress()
    
    print(f"开始批量爬取 {total} 支球队数据")
    print(f"已完成: {len(progress['completed'])} 支")
    print(f"待处理: {total - len(progress['completed'])} 支")
    print("=" * 60)
    
    # 顺序爬取
    for i, team_id in enumerate(team_ids):
        print(f"\n进度: {i+1}/{total}")
        crawl_team_safe(team_id, progress)
        wait_random()
    
    print("\n" + "=" * 60)
    print(f"爬取完成!")
    print(f"成功: {len(progress['completed'])} 支")
    print(f"失败: {len(progress['failed'])} 支")
    
    if progress['failed']:
        print(f"\n失败球队: {progress['failed']}")

if __name__ == "__main__":
    batch_crawl_safe()