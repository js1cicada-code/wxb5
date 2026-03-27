#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
胜负过关数据爬虫 - 从北京体彩网获取数据
"""

import urllib.request
import ssl
import re
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def get_current_period():
    """获取当前期次"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.strftime('%m')
    
    # 获取当月的期次列表
    url = f'https://www.bjlot.com.cn/data/270/control/drawnolist_{year}{month}.js'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    periods = []
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read().decode('utf-8')
            periods = re.findall(r'"drawno":"(\d+)"', content)
    except:
        pass
    
    # 检查是否有更新的期次（drawnolist可能未及时更新）
    if periods:
        latest = int(periods[0])
        # 检查下一个期次是否存在
        next_period = str(latest + 1)
        test_url = f'https://www.bjlot.com.cn/ssm/270/html/gameinfo_{next_period}.js'
        try:
            with urllib.request.urlopen(urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'}), context=ctx, timeout=10) as resp:
                content = resp.read().decode('utf-8')
                if '"DrawNo"' in content:
                    return next_period
        except:
            pass
        return periods[0]
    
    return None


def fetch_sggg_data():
    """从北京体彩网获取胜负过关数据"""
    print("开始爬取胜负过关数据...", datetime.now())
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 获取当前期次
    period = get_current_period()
    if not period:
        print("获取期次失败")
        return None
    
    print(f"当前期次: {period}")
    
    # 获取XML数据
    url = f'https://www.bjlot.com.cn/data/270ParlayGetGame_{period}.xml'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read().decode('utf-8')
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None
    
    # 解析比赛数据
    items = re.findall(r'<item[^>]*no="(\d+)"[^>]*>(.*?)</item>', content, re.DOTALL)
    print(f"找到 {len(items)} 场比赛")
    
    selling_matches = []
    stopped_matches = []
    
    for no, item_content in items:
        host = re.search(r'<host>([^<]+)</host>', item_content)
        guest = re.search(r'<guest>([^<]+)</guest>', item_content)
        match_time = re.search(r'<matchTime[^>]*>([^<]+)</matchTime>', item_content)
        date_time = re.search(r'<DateTime>([^<]+)</DateTime>', item_content)
        league = re.search(r'<leagueName>([^<]+)</leagueName>', item_content)
        game_type = re.search(r'<gameTypeName>([^<]+)</gameTypeName>', item_content)
        state = re.search(r'<matchandstate>([^<]+)</matchandstate>', item_content)
        handicap = re.search(r'<handicap>([^<]+)</handicap>', item_content)
        sp1 = re.search(r'<sp1>([^<]+)</sp1>', item_content)
        sp2 = re.search(r'<sp2>([^<]+)</sp2>', item_content)
        
        match_data = {
            'id': no,
            'matchNum': no,
            'date': match_time.group(1)[:10] if match_time else '',
            'time': date_time.group(1) if date_time else '',
            'league': league.group(1) if league else '',
            'matchType': game_type.group(1) if game_type else '',
            'home': host.group(1) if host else '',
            'away': guest.group(1) if guest else '',
            'handicap': float(handicap.group(1)) if handicap else 0,
            'homeOdds': float(sp1.group(1)) if sp1 else 1.90,
            'awayOdds': float(sp2.group(1)) if sp2 else 1.90,
            'state': state.group(1) if state else ''
        }
        
        if match_data['state'] == '销售中':
            selling_matches.append(match_data)
        else:
            stopped_matches.append(match_data)
    
    print(f"销售中: {len(selling_matches)} 场")
    print(f"已停售: {len(stopped_matches)} 场")
    
    # 统计类型
    football = len([m for m in selling_matches if '足' in m['matchType']])
    basketball = len([m for m in selling_matches if '篮' in m['matchType']])
    other = len(selling_matches) - football - basketball
    
    print(f"足球: {football} 场, 篮球: {basketball} 场, 其他: {other} 场")
    
    return {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'issue': period,
        'period': period,
        'matchCount': len(selling_matches),
        'matches': selling_matches
    }


def save_data(data):
    """保存数据到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'sggg_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'sggg_data.json'),
        os.path.join(base_dir, 'data', 'sggg_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")


if __name__ == '__main__':
    data = fetch_sggg_data()
    if data:
        save_data(data)