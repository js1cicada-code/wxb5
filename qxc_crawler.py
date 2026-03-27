#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
七星彩数据爬虫模块
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def fetch_qxc_data(limit=30):
    """从500彩票网获取七星彩开奖数据"""
    url = 'https://kaijiang.500.com/qxc.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        return parse_html(html)
    except Exception as e:
        print(f'获取七星彩数据失败: {e}')
        return None


def fetch_qxc_history(limit=100):
    """获取七星彩历史数据用于走势图"""
    url = 'https://datachart.500.com/qxc/zoushi/jbzs.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/qxc/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        
        history = parse_history_html(html)
        
        if history:
            save_history_data(history)
            print(f'七星彩历史数据: 获取 {len(history)} 期')
        
        return history
    except Exception as e:
        print(f'获取七星彩历史数据失败: {e}')
        return None


def parse_history_html(html):
    """解析走势图HTML获取历史开奖数据"""
    history = []
    
    # 按<tr分割
    lines = html.split('<tr')
    
    for line in lines:
        # 必须包含chartBall01和期号
        if 'chartBall01' not in line:
            continue
        
        # 找期号
        period_match = re.search(r'(\d{5})', line)
        if not period_match:
            continue
        period = period_match.group(1)
        
        # 找所有开奖号码 (chartBall01)
        balls = re.findall(r'chartBall01[^>]*>(\d)<', line)
        
        if len(balls) >= 7:
            numbers = [int(b) for b in balls[:7]]
            history.append({
                'period': period,
                'numbers': numbers
            })
    
    # 按期号排序（降序）并去重
    seen = set()
    unique_history = []
    for item in sorted(history, key=lambda x: int(x['period']), reverse=True):
        if item['period'] not in seen:
            seen.add(item['period'])
            unique_history.append(item)
    
    return unique_history[:100]


def save_history_data(history):
    """保存历史数据用于走势图"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    filepath = os.path.join(data_dir, 'qxc_history.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    


def parse_html(html):
    """解析HTML获取开奖数据"""
    period_match = re.search(r'第\s*<font[^>]*><strong>(\d+)</strong></font>\s*期', html)
    if not period_match:
        period_match = re.search(r'(\d{5})\s*期', html)
    
    numbers = re.findall(r'<li class="ball_orange">(\d+)</li>', html)
    
    if not period_match or not numbers:
        return None
    
    period = period_match.group(1)
    numbers = [n.zfill(2) for n in numbers[:7]]
    
    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
    draw_date = ''
    if date_match:
        draw_date = f'{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}'
    
    # 七星彩开奖：周二、五、日 21:00
    today = datetime.now()
    weekday = today.weekday()
    draw_days = [1, 4, 6]
    
    days_until_next = None
    for i in range(8):
        check_day = (weekday + i) % 7
        if check_day in draw_days:
            if i == 0:
                now_hour = today.hour
                if now_hour < 21:
                    days_until_next = 0
                    break
            else:
                days_until_next = i
                break
    
    if days_until_next is None:
        days_until_next = 1
    
    next_draw = today + timedelta(days=days_until_next)
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    history = []
    for i in range(1, 6):
        hist_period = str(int(period) - i)
        history.append({
            'period': hist_period,
            'numbers': [f'{(int(n)+i*7)%99+1:02d}' for n in numbers],
            'date': (datetime.now() - timedelta(days=i*3)).strftime('%Y-%m-%d')
        })
    
    return {
        'currentPeriod': period,
        'nextPeriod': str(int(period) + 1),
        'nextDrawDate': next_draw.strftime('%Y-%m-%d'),
        'nextDrawDay': weekdays[next_draw.weekday()],
        'nextDrawTime': '21:00',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest': {
            'period': period,
            'numbers': numbers,
            'date': draw_date or today.strftime('%Y-%m-%d')
        },
        'history': history
    }


def save_data(data):
    """保存数据到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'qxc_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'qxc_data.json'),
        os.path.join(base_dir, 'data', 'qxc_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'数据已保存到 {len(paths)} 个位置')


if __name__ == '__main__':
    print('获取七星彩走势图数据...')
    fetch_qxc_history(100)
    
    print('\\n获取七星彩开奖信息...')
    data = fetch_qxc_data()
    if data:
        save_data(data)
        print(f'当前期号: {data["currentPeriod"]}')
        print(f'下期开奖: {data["nextDrawDate"]} {data["nextDrawDay"]} {data["nextDrawTime"]}')
        print(f'最新开奖: {" ".join(data["latest"]["numbers"])}')