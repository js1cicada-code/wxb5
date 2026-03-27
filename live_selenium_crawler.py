#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 59itou专用版
"""

import json
import os
import time
import re
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def get_driver():
    """获取Selenium WebDriver"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    
    return driver


def fetch_live_data(url='https://kt.59itou.com/694/livescore/631/jingcai/'):
    """获取比分直播数据"""
    driver = get_driver()
    
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        time.sleep(5)
        
        page_source = driver.page_source
        
        # 保存调试文件
        debug_file = os.path.join(DATA_DIR, 'live_page_debug.html')
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"页面已保存: {debug_file}")
        
        matches = parse_page(page_source)
        
        return {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': matches,
            'total': len(matches),
            'live': len([m for m in matches if m['status'] == 'live']),
            'upcoming': len([m for m in matches if m['status'] == 'upcoming']),
            'finished': len([m for m in matches if m['status'] == 'finished'])
        }
    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()


def parse_page(html):
    """解析59itou页面"""
    matches = []
    
    # 查找所有 liveitem
    liveitem_pattern = r'<div[^>]*class="[^"]*liveitem[^"]*"[^>]*>([\s\S]*?)</div>\s*</div>\s*</div>'
    items = re.findall(liveitem_pattern, html)
    
    if not items:
        # 备用模式
        liveitem_pattern = r'data-unstart="[^"]*"[^>]*class="[^"]*liveitem[^"]*"[^>]*>([\s\S]*?)</div>\s*</div>\s*</div>'
        items = re.findall(liveitem_pattern, html)
    
    print(f"找到 {len(items)} 个比赛项")
    
    for item in items:
        match = parse_liveitem(item)
        if match and match.get('home') and match.get('away'):
            matches.append(match)
    
    return matches


def parse_liveitem(item):
    """解析单个比赛项"""
    match = {}
    
    # 提取联赛名: <p class="fontblue">欧洲世预</p>
    league_match = re.search(r'<p class="fontblue">([^<]+)</p>', item)
    if league_match:
        match['league'] = league_match.group(1).strip()
    else:
        match['league'] = ''
    
    # 提取比赛编号: <p class="graya6">001</p>
    num_match = re.search(r'<p class="graya6">(\d+)</p>', item)
    if num_match:
        match['matchNum'] = num_match.group(1)
    else:
        match['matchNum'] = ''
    
    # 提取主队: <span class="font15">土耳其</span>
    teams = re.findall(r'<span class="font15">([^<]+)</span>', item)
    if len(teams) >= 2:
        match['home'] = teams[0].strip()
        match['away'] = teams[1].strip()
    else:
        match['home'] = ''
        match['away'] = ''
    
    # 提取时间: <p class="graya6 font18">01:00</p>
    time_match = re.search(r'<p class="graya6 font18">([^<]+)</p>', item)
    if time_match:
        match['time'] = time_match.group(1).strip()
    else:
        match['time'] = ''
    
    # 提取比分 (如果有的话)
    # 查找比分元素
    score_pattern = r'<cite[^>]*class="[^"]*fontgreen[^"]*"[^>]*>([\s\S]*?)</cite>'
    score_match = re.search(score_pattern, item)
    
    if score_match:
        score_text = score_match.group(1)
        # 查找比分数字
        score_nums = re.search(r'(\d+)\s*-\s*(\d+)', score_text)
        if score_nums:
            match['homeScore'] = int(score_nums.group(1))
            match['awayScore'] = int(score_nums.group(2))
        else:
            match['homeScore'] = 0
            match['awayScore'] = 0
    else:
        match['homeScore'] = 0
        match['awayScore'] = 0
    
    # 判断比赛状态
    if 'data-unstart="true"' in item:
        match['status'] = 'upcoming'
        match['minute'] = ''
    elif 'fontgreen' in item and '未开始' not in item:
        # 可能有比分，检查是否有进行中的标志
        minute_match = re.search(r'(\d+)["\']', item)
        if minute_match:
            match['status'] = 'live'
            match['minute'] = minute_match.group(1)
        else:
            match['status'] = 'live'
            match['minute'] = ''
    else:
        match['status'] = 'upcoming'
        match['minute'] = ''
    
    match['statusOrder'] = {'live': 1, 'upcoming': 2, 'finished': 3}.get(match['status'], 99)
    match['id'] = ''
    
    return match


def save_data(data, filename):
    """保存数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    
    print(f'数据已保存: {filepath}')


if __name__ == '__main__':
    print('=' * 50)
    print('比分直播爬虫 - 59itou版')
    print('=' * 50)
    
    data = fetch_live_data()
    
    if data and data['matches']:
        save_data(data, 'live_data.json')
        print(f"\n成功获取 {data['total']} 场比赛")
        print(f"  进行中: {data['live']}")
        print(f"  未开始: {data['upcoming']}")
        print(f"  已结束: {data['finished']}")
        
        print("\n前5场比赛:")
        for m in data['matches'][:5]:
            print(f"  {m['matchNum']} {m['league']} {m['home']} vs {m['away']} ({m['time']})")
    else:
        print("获取失败")