#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透数据爬虫模块
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def fetch_dlt_data(limit=30):
    """从500彩票网获取大乐透开奖数据"""
    url = f'https://datachart.500.com/dlt/history/newinc/history.php?limit={limit}'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/dlt/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        return parse_html(html)
    except Exception as e:
        print(f'获取大乐透数据失败: {e}')
        return None


def fetch_dlt_history(limit=100):
    """获取大乐透历史数据用于走势图"""
    url = f'https://datachart.500.com/dlt/history/newinc/history.php?limit={limit}'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/dlt/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        history = parse_history_html(html)
        
        if history:
            save_history_data(history)
            print(f'大乐透历史数据: 获取 {len(history)} 期')
        
        return history
    except Exception as e:
        print(f'获取大乐透历史数据失败: {e}')
        return None


def parse_history_html(html):
    """解析HTML获取历史开奖数据（简化版，用于走势图）"""
    pattern = r'<tr class="t_tr1"><!--<td>.*?</td>--><td class="t_tr1">(\d{5})</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont4">(\d+)</td><td class="cfont4">(\d+)</td>'
    
    matches = re.findall(pattern, html, re.DOTALL)
    
    history = []
    for m in matches:
        period = m[0]
        front = sorted([int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5])])
        back = sorted([int(m[6]), int(m[7])])
        
        history.append({
            'period': period,
            'front': front,
            'back': back
        })
    
    return history


def save_history_data(history):
    """保存历史数据用于走势图"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    filepath = os.path.join(data_dir, 'dlt_history.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    # 同时保存到dist目录


def parse_html(html):
    """解析HTML获取开奖数据"""
    # 更新正则表达式，适配新的HTML结构（包含注释 <!--<td>2</td>-->）
    pattern = r'<tr class="t_tr1"><!--<td>.*?</td>--><td class="t_tr1">(\d{5})</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont2">(\d+)</td><td class="cfont4">(\d+)</td><td class="cfont4">(\d+)</td><td class="t_tr1">([\d,]+)</td><td class="t_tr1">(\d+)</td><td class="t_tr1">([\d,]+)</td><td class="t_tr1">(\d+)</td><td class="t_tr1">([\d,]+)</td><td class="t_tr1">([\d,]+)</td><td class="t_tr1">(\d{4}-\d{2}-\d{2})</td></tr>'
    
    matches = re.findall(pattern, html, re.DOTALL)
    
    history = []
    for m in matches:
        period = m[0]
        front = [m[1].zfill(2), m[2].zfill(2), m[3].zfill(2), m[4].zfill(2), m[5].zfill(2)]
        back = [m[6].zfill(2), m[7].zfill(2)]
        pool = m[8].replace(',', '')
        first_count = m[9]
        first_prize = m[10].replace(',', '')
        second_count = m[11]
        second_prize = m[12].replace(',', '')
        sales = m[13].replace(',', '')
        date = m[14]
        
        history.append({
            'period': period,
            'numbers': front + back,
            'front': front,
            'back': back,
            'pool': pool,
            'firstCount': first_count,
            'firstPrize': first_prize,
            'secondCount': second_count,
            'secondPrize': second_prize,
            'sales': sales,
            'date': date
        })
    
    if not history:
        return None
    
    latest = history[0]
    
    # 大乐透开奖：周一、三、六 21:25
    today = datetime.now()
    weekday = today.weekday()
    draw_days = [0, 2, 5]
    
    days_until_next = None
    for i in range(8):
        check_day = (weekday + i) % 7
        if check_day in draw_days:
            if i == 0:
                now_hour = today.hour
                now_minute = today.minute
                if now_hour < 21 or (now_hour == 21 and now_minute < 25):
                    days_until_next = 0
                    break
            else:
                days_until_next = i
                break
    
    if days_until_next is None:
        days_until_next = 1
    
    next_draw = today + timedelta(days=days_until_next)
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    return {
        'currentPeriod': latest['period'],
        'nextPeriod': str(int(latest['period']) + 1),
        'nextDrawDate': next_draw.strftime('%Y-%m-%d'),
        'nextDrawDay': weekdays[next_draw.weekday()],
        'nextDrawTime': '21:25',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest': {
            'period': latest['period'],
            'numbers': latest['numbers'],
            'date': latest['date']
        },
        'history': history
    }


def save_data(data):
    """保存数据到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'dlt_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'dlt_data.json'),
        os.path.join(base_dir, 'data', 'dlt_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'数据已保存到 {len(paths)} 个位置')


if __name__ == '__main__':
    print('获取大乐透走势图数据...')
    fetch_dlt_history(100)
    
    print('\\n获取大乐透开奖信息...')
    data = fetch_dlt_data(30)
    if data:
        save_data(data)
        print(f'当前期号: {data["currentPeriod"]}')
        print(f'下期开奖: {data["nextDrawDate"]} {data["nextDrawDay"]} {data["nextDrawTime"]}')
        print(f'最新开奖: {" ".join(data["latest"]["numbers"])}')