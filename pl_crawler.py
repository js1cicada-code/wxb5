#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排列三/排列五数据爬虫模块
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def fetch_pls_data():
    """从500彩票网获取排列三开奖数据"""
    url = 'https://kaijiang.500.com/pls.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        return parse_pls_html(html)
    except Exception as e:
        print(f'获取排列三数据失败: {e}')
        return None


def parse_pls_html(html):
    """解析排列三开奖页面"""
    period_match = re.search(r'第\s*<font[^>]*><strong>(\d+)</strong></font>\s*期', html)
    if not period_match:
        period_match = re.search(r'(\d{5})\s*期', html)
    
    numbers = re.findall(r'<li class="ball_orange">(\d)</li>', html)
    
    if not period_match or len(numbers) < 3:
        return None
    
    period = period_match.group(1)
    numbers = [int(n) for n in numbers[:3]]
    
    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
    draw_date = ''
    if date_match:
        draw_date = f'{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}'
    
    today = datetime.now()
    weekdays = ['周一','周二','周三','周四','周五','周六','周日']
    
    history = []
    history_file = os.path.join(DATA_DIR, 'pls_history.json')
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
    
    return {
        'currentPeriod': period,
        'nextPeriod': str(int(period) + 1),
        'nextDrawDate': today.strftime('%Y-%m-%d'),
        'nextDrawDay': weekdays[today.weekday()],
        'nextDrawTime': '20:30',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest': {
            'period': period,
            'numbers': numbers,
            'date': draw_date or today.strftime('%Y-%m-%d')
        },
        'history': history
    }


def fetch_plw_data():
    """从500彩票网获取排列五开奖数据"""
    url = 'https://kaijiang.500.com/plw.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        return parse_plw_html(html)
    except Exception as e:
        print(f'获取排列五数据失败: {e}')
        return None


def parse_plw_html(html):
    """解析排列五开奖页面"""
    period_match = re.search(r'第\s*<font[^>]*><strong>(\d+)</strong></font>\s*期', html)
    if not period_match:
        period_match = re.search(r'(\d{5})\s*期', html)
    
    numbers = re.findall(r'<li class="ball_orange">(\d)</li>', html)
    
    if not period_match or len(numbers) < 5:
        return None
    
    period = period_match.group(1)
    numbers = [int(n) for n in numbers[:5]]
    
    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
    draw_date = ''
    if date_match:
        draw_date = f'{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}'
    
    today = datetime.now()
    weekdays = ['周一','周二','周三','周四','周五','周六','周日']
    
    history = []
    history_file = os.path.join(DATA_DIR, 'plw_history.json')
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
    
    return {
        'currentPeriod': period,
        'nextPeriod': str(int(period) + 1),
        'nextDrawDate': today.strftime('%Y-%m-%d'),
        'nextDrawDay': weekdays[today.weekday()],
        'nextDrawTime': '20:30',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest': {
            'period': period,
            'numbers': numbers,
            'date': draw_date or today.strftime('%Y-%m-%d')
        },
        'history': history
    }


def fetch_pls_history(limit=100):
    """获取排列三历史数据"""
    url = 'https://datachart.500.com/pls/zoushi/jbzs.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/pls/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        
        history = parse_chart_html(html, 3)
        history = history[:limit]
        
        if history:
            save_history_data(history, 'pls_history.json')
            print(f'排列三历史数据: 获取 {len(history)} 期')
        
        return history
    except Exception as e:
        print(f'获取排列三历史数据失败: {e}')
        return None


def fetch_plw_history(limit=100):
    """获取排列五历史数据"""
    url = 'https://datachart.500.com/plw/zoushi/jbzs.shtml'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        'Referer': 'https://datachart.500.com/plw/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        
        history = parse_chart_html(html, 5)
        history = history[:limit]
        
        if history:
            save_history_data(history, 'plw_history.json')
            print(f'排列五历史数据: 获取 {len(history)} 期')
        
        return history
    except Exception as e:
        print(f'获取排列五历史数据失败: {e}')
        return None


def parse_chart_html(html, num_count):
    """解析走势图HTML"""
    history = []
    
    lines = html.split('<tr')
    
    for line in lines:
        if 'chartBall01' not in line:
            continue
        
        period_match = re.search(r'(\d{5})</td>', line)
        if not period_match:
            continue
        period = period_match.group(1)
        
        balls = re.findall(r'chartBall\d+[^>]*>(\d)<', line)
        
        if len(balls) >= num_count:
            numbers = [int(b) for b in balls[:num_count]]
            history.append({
                'period': period,
                'numbers': numbers,
                'date': ''
            })
    
    seen = set()
    unique_history = []
    for item in sorted(history, key=lambda x: int(x['period']), reverse=True):
        if item['period'] not in seen:
            seen.add(item['period'])
            unique_history.append(item)
    
    return unique_history


def save_history_data(history, filename):
    """保存历史数据"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    


def save_data(data, filename):
    """保存开奖数据"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    
    print(f'数据已保存到 {filepath}')


if __name__ == '__main__':
    print('获取排列三走势图数据...')
    fetch_pls_history()
    
    print('\n获取排列三开奖信息...')
    pls_data = fetch_pls_data()
    if pls_data:
        save_data(pls_data, 'pls_data.json')
        print(f'当前期号: {pls_data["currentPeriod"]}')
        print(f'下期开奖: {pls_data["nextDrawDate"]} {pls_data["nextDrawDay"]} {pls_data["nextDrawTime"]}')
        print(f'最新开奖: {" ".join(str(n) for n in pls_data["latest"]["numbers"])}')
    
    print('\n' + '='*50)
    
    print('\n获取排列五走势图数据...')
    fetch_plw_history()
    
    print('\n获取排列五开奖信息...')
    plw_data = fetch_plw_data()
    if plw_data:
        save_data(plw_data, 'plw_data.json')
        print(f'当前期号: {plw_data["currentPeriod"]}')
        print(f'下期开奖: {plw_data["nextDrawDate"]} {plw_data["nextDrawDay"]} {plw_data["nextDrawTime"]}')
        print(f'最新开奖: {" ".join(str(n) for n in plw_data["latest"]["numbers"])}')