#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据获取模块
- 竞彩足球/篮球：使用竞彩网API
- 传统足彩相关：使用500网
"""

import json
import os
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DIST_DIR = 'dist'
os.makedirs(DIST_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.sporttery.cn/',
}


def save_json(data, filename):
    """保存到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', filename),
        os.path.join(base_dir, 'dist', 'data', filename),
        os.path.join(base_dir, 'data', filename)
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"保存: {filename}")


def load_fixture_mapping():
    """加载fixture映射"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(base_dir, 'data', 'fixture_mapping.json')
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def fetch_jczq_data():
    """竞彩足球 - 使用竞彩网API + 500.com fixtureId"""
    url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1'
    
    fixture_mapping = load_fixture_mapping()
    by_match_num = fixture_mapping.get('byMatchNum', {})
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if not data.get('success'):
            return None
        
        matches = []
        for day_match in data.get('value', {}).get('matchInfoList', []):
            for m in day_match.get('subMatchList', []):
                match_num = m.get('matchNumStr', '')
                
                item = {
                    'id': m.get('matchId'),
                    'matchNumStr': match_num,
                    'home': m.get('homeTeamAbbName'),
                    'away': m.get('awayTeamAbbName'),
                    'league': m.get('leagueAbbName'),
                    'time': m.get('matchTime', '')[:5],
                    'date': m.get('matchDate'),
                    'fixtureId': '',
                    'namitiyuId': '',
                }
                
                if match_num in by_match_num:
                    entry = by_match_num[match_num]
                    item['fixtureId'] = entry.get('fixtureId', '')
                    item['namitiyuId'] = entry.get('namitiyuId', '')
                
                if m.get('had'):
                    item['spf'] = [
                        float(m['had'].get('h', 0)),
                        float(m['had'].get('d', 0)),
                        float(m['had'].get('a', 0))
                    ]
                
                if m.get('hhad'):
                    item['rqspf'] = {
                        'handicap': int(m['hhad'].get('goalLine', 0)),
                        'odds': [
                            float(m['hhad'].get('h', 0)),
                            float(m['hhad'].get('d', 0)),
                            float(m['hhad'].get('a', 0))
                        ]
                    }
                
                matches.append(item)
        
        return {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': matches
        }
    except Exception as e:
        print(f"竞彩足球获取失败: {e}")
        return None


def fetch_jclq_data():
    """竞彩篮球 - 使用竞彩网API + 500.com fixtureId"""
    url = 'https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1'
    
    fixture_mapping = load_fixture_mapping()
    by_match_num = fixture_mapping.get('byMatchNum', {})
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        
        if not data.get('success'):
            return None
        
        matches = []
        for day_match in data.get('value', {}).get('matchInfoList', []):
            for m in day_match.get('subMatchList', []):
                match_num = m.get('matchNumStr', '')
                
                item = {
                    'id': m.get('matchId'),
                    'matchNumStr': match_num,
                    'home': m.get('homeTeamAbbName'),
                    'away': m.get('awayTeamAbbName'),
                    'league': m.get('leagueAbbName'),
                    'time': m.get('matchTime', '')[:5],
                    'fixtureId': '',
                    'namitiyuId': '',
                }
                
                if match_num in by_match_num:
                    entry = by_match_num[match_num]
                    item['fixtureId'] = entry.get('fixtureId', '')
                    item['namitiyuId'] = entry.get('namitiyuId', '')
                
                if m.get('mnl'):
                    item['sf'] = [
                        float(m['mnl'].get('h', 0)),
                        float(m['mnl'].get('a', 0))
                    ]
                
                if m.get('hdc'):
                    item['rfsf'] = {
                        'handicap': float(m['hdc'].get('p', 0)),
                        'odds': [
                            float(m['hdc'].get('h', 0)),
                            float(m['hdc'].get('a', 0))
                        ]
                    }
                
                matches.append(item)
        
        return {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': matches
        }
    except Exception as e:
        print(f"竞彩篮球获取失败: {e}")
        return None


def fetch_500com_single_period(url, max_matches, expect=None):
    """获取单个期号的数据"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    target_url = f"{url}?expect={expect}" if expect else url
    
    try:
        resp = requests.get(target_url, headers=headers, timeout=15)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        period = None
        deadline = None
        periods_list = []
        
        expect_input = soup.find('input', id='expect')
        if expect_input:
            period = expect_input.get('value')
        
        endtime_span = soup.find('span', class_='zcfilter-endtime')
        if endtime_span:
            match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', endtime_span.get_text())
            if match:
                deadline = match.group(1)
        
        qih_list = soup.find('ul', class_='qih-list')
        if qih_list:
            for li in qih_list.find_all('li'):
                exp = li.get('data-expect', '')
                text = li.get_text(strip=True)
                if exp:
                    periods_list.append({'period': exp, 'label': text})
        
        matches = []
        table = soup.find('table', id='vsTable')
        if table:
            for i, tr in enumerate(table.find_all('tr', class_='bet-tb-tr')):
                if i >= max_matches:
                    break
                
                cells = tr.find_all('td')
                if len(cells) < 3:
                    continue
                
                match_item = {
                    'id': str(i + 1),
                    'matchNum': str(i + 1),
                    'league': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                    'time': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                }
                
                vs_data = tr.get('data-vs', '')
                if vs_data:
                    parts = str(vs_data).split('vs')
                    if len(parts) == 2:
                        match_item['home'] = parts[0].strip()
                        match_item['away'] = parts[1].strip()
                
                bjpl = tr.get('data-bjpl', '')
                if bjpl:
                    odds = str(bjpl).split(',')
                    if len(odds) >= 3:
                        try:
                            match_item['odds3'] = float(odds[0])
                            match_item['odds1'] = float(odds[1])
                            match_item['odds0'] = float(odds[2])
                        except:
                            pass
                
                if match_item.get('home') and match_item.get('away'):
                    matches.append(match_item)
        
        return {
            'period': period,
            'deadline': deadline,
            'matches': matches,
            'periods_list': periods_list
        }
        
    except Exception as e:
        print(f"500网获取失败: {e}")
        return None


def fetch_500com_data(url, max_matches):
    """500网通用爬虫 - 获取所有期号数据"""
    first_result = fetch_500com_single_period(url, max_matches)
    if not first_result:
        return None
    
    periods_list = first_result.get('periods_list', [])
    if not periods_list:
        return {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current': first_result.get('period'),
            'periods': {
                first_result.get('period'): {
                    'period': first_result.get('period'),
                    'deadline': first_result.get('deadline'),
                    'matches': first_result.get('matches', [])
                }
            },
            'periods_list': [{'period': first_result.get('period'), 'label': f"第{first_result.get('period')}期"}]
        }
    
    periods_data = {}
    
    for p in periods_list[:4]:
        expect = p.get('period')
        if not expect:
            continue
        
        if expect == first_result.get('period'):
            periods_data[expect] = {
                'period': expect,
                'deadline': first_result.get('deadline'),
                'matches': first_result.get('matches', [])
            }
        else:
            time.sleep(0.5)
            result = fetch_500com_single_period(url, max_matches, expect)
            if result and result.get('matches'):
                periods_data[expect] = {
                    'period': expect,
                    'deadline': result.get('deadline'),
                    'matches': result.get('matches', [])
                }
            else:
                periods_data[expect] = {
                    'period': expect,
                    'deadline': None,
                    'matches': []
                }
    
    return {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current': first_result.get('period'),
        'periods': periods_data,
        'periods_list': periods_list[:4]
    }


def fetch_bqc6_data():
    """6场半全场"""
    return fetch_500com_data('https://trade.500.com/bqc/', 6)


def fetch_zjq4_data():
    """4场总进球"""
    return fetch_500com_data('https://trade.500.com/jqc/', 4)


def fetch_ctzc_data():
    """传统足彩14场"""
    return fetch_500com_data('https://trade.500.com/sfc/', 14)


def update_all_data():
    """更新所有数据"""
    print(f"\n{'='*50}")
    print(f"开始更新数据 - {datetime.now().strftime('%H:%M:%S')}")
    print('='*50)
    
    # 竞彩足球
    data = fetch_jczq_data()
    if data:
        save_json(data, 'jczq_data.json')
        print(f"竞彩足球: {len(data['matches'])}场")
    
    # 竞彩篮球
    data = fetch_jclq_data()
    if data:
        save_json(data, 'jclq_data.json')
        print(f"竞彩篮球: {len(data['matches'])}场")
    
    # 6场半全场
    data = fetch_bqc6_data()
    if data:
        save_json(data, 'bqc6_data.json')
        periods_count = len(data.get('periods', {}))
        print(f"6场半全场: {data.get('current')}期, 共{periods_count}期")
    
    # 4场总进球
    data = fetch_zjq4_data()
    if data:
        save_json(data, 'zjq4_data.json')
        periods_count = len(data.get('periods', {}))
        print(f"4场总进球: {data.get('current')}期, 共{periods_count}期")
    
    # 传统足彩
    data = fetch_ctzc_data()
    if data:
        save_json(data, 'ctzc_data.json')
        periods_count = len(data.get('periods', {}))
        print(f"传统足彩: {data.get('current')}期, 共{periods_count}期")
    
    print(f"{'='*50}\n")


if __name__ == '__main__':
    update_all_data()