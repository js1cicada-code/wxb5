#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - Playwright版本
"""

import json
import os
import re
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def fetch_live_data(url='https://kt.59itou.com/694/livescore/631/jingcai/'):
    """使用Playwright获取比分直播数据"""
    from playwright.sync_api import sync_playwright
    
    print(f"正在访问: {url}")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        )
        page = context.new_page()
        
        try:
            # 访问页面
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # 等待内容加载
            page.wait_for_selector('.liveitem', timeout=10000)
            
            # 获取页面内容
            html = page.content()
            
            # 保存调试文件
            os.makedirs(DATA_DIR, exist_ok=True)
            debug_file = os.path.join(DATA_DIR, 'live_page_debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"页面已保存: {debug_file}")
            
            # 解析数据
            matches = parse_page(html)
            
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
            browser.close()


def parse_page(html):
    """解析页面"""
    matches = []
    
    # 先获取日期
    current_date = ''
    date_match = re.search(r'livedatetit[^>]*><span[^>]*>([^<]+)</span>', html)
    if date_match:
        current_date = date_match.group(1).strip()
    
    # 查找所有比赛项
    pattern = r'<div[^>]*class="[^"]*liveitem[^"]*"[^>]*>([\s\S]*?)</div>\s*</div>\s*</div>'
    items = re.findall(pattern, html)
    
    print(f"找到 {len(items)} 个比赛项, 日期: {current_date}")
    
    for item in items:
        match = parse_match(item)
        if match and match.get('home') and match.get('away'):
            match['date'] = current_date
            matches.append(match)
    
    return matches


def parse_match(item):
    """解析单场比赛"""
    match = {}
    
    # 联赛
    league = re.search(r'<p class="fontblue">([^<]+)</p>', item)
    match['league'] = league.group(1).strip() if league else ''
    
    # 编号
    num = re.search(r'<p class="graya6">(\d+)</p>', item)
    match['matchNum'] = num.group(1) if num else ''
    
    # 球队
    teams = re.findall(r'<span class="font15">([^<]+)</span>', item)
    match['home'] = teams[0].strip() if len(teams) >= 1 else ''
    match['away'] = teams[1].strip() if len(teams) >= 2 else ''
    
    # 时间
    time = re.search(r'<p class="graya6 font18">([^<]+)</p>', item)
    match['time'] = time.group(1).strip() if time else ''
    
    # 日期默认值，会在parse_page中设置
    match['date'] = ''
    
    # 比分
    score_text = re.search(r'>(\d+)\s*-\s*(\d+)<', item)
    if score_text:
        match['homeScore'] = int(score_text.group(1))
        match['awayScore'] = int(score_text.group(2))
    else:
        match['homeScore'] = 0
        match['awayScore'] = 0
    
    # 状态
    if 'data-unstart="true"' in item:
        match['status'] = 'upcoming'
    else:
        match['status'] = 'upcoming'
    
    match['minute'] = ''
    match['statusOrder'] = 2
    match['id'] = ''
    
    return match


def save_data(data, filename):
    """保存数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'数据已保存: {filepath}')


if __name__ == '__main__':
    print('=' * 50)
    print('比分直播爬虫 - Playwright版')
    print('=' * 50)
    
    data = fetch_live_data()
    
    if data and data['matches']:
        save_data(data, 'live_data.json')
        print(f"\n成功获取 {data['total']} 场比赛")
        
        print("\n前5场比赛:")
        for m in data['matches'][:5]:
            print(f"  {m['matchNum']} {m['league']} {m['home']} vs {m['away']} ({m['time']})")
    else:
        print("获取失败")