#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫
"""

import json
import os
import re
from datetime import datetime
import urllib.request
import ssl

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')


def fetch_live_data():
    """从500彩票网获取比分直播数据"""
    url = 'https://live.500.com/'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
        return parse_live_html(html)
    except Exception as e:
        print(f'从500彩票网获取失败: {e}')
        return None


def parse_live_html(html):
    """解析比分直播页面"""
    matches = []
    
    tr_pattern = r'<tr[^>]*id=["\']?tr_(\d+)["\']?[^>]*>(.*?)</tr>'
    tr_matches = re.findall(tr_pattern, html, re.DOTALL | re.IGNORECASE)
    
    for fid, tr_content in tr_matches:
        try:
            match = parse_match_tr(fid, tr_content)
            if match and match.get('home') and match.get('away'):
                matches.append(match)
        except Exception as e:
            continue
    
    if not matches:
        matches = parse_live_html_v2(html)
    
    matches.sort(key=lambda x: (x.get('statusOrder', 99), x.get('time', '')))
    
    return {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': matches,
        'total': len(matches),
        'live': len([m for m in matches if m['status'] == 'live']),
        'upcoming': len([m for m in matches if m['status'] == 'upcoming']),
        'finished': len([m for m in matches if m['status'] == 'finished'])
    }


def parse_match_tr(fid, tr_content):
    """解析单行比赛数据"""
    match = {'id': fid}
    
    league_patterns = [
        r'<a[^>]*href="//liansai\.500\.com/zuqiu-\d+/"[^>]*>([^<]+)</a>',
        r'title=["\']([^"\']+)["\'][^>]*>[^<]*</a>',
    ]
    for pattern in league_patterns:
        m = re.search(pattern, tr_content)
        if m:
            match['league'] = m.group(1).strip()
            break
    else:
        match['league'] = ''
    
    time_match = re.search(r'(\d{2}-\d{2})\s*(\d{2}:\d{2})', tr_content)
    if time_match:
        match['date'] = time_match.group(1)
        match['time'] = time_match.group(2)
    else:
        match['date'] = ''
        match['time'] = ''
    
    td_pattern = r'<td[^>]*>(.*?)</td>'
    tds = re.findall(td_pattern, tr_content, re.DOTALL)
    
    home = ''
    away = ''
    home_score = 0
    away_score = 0
    
    for i, td in enumerate(tds):
        td_clean = re.sub(r'<[^>]+>', '', td).strip()
        
        team_link = re.search(r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>', td)
        if team_link:
            if not home:
                home = team_link.group(1).strip()
            else:
                away = team_link.group(1).strip()
        
        score_match = re.search(r'(\d+)\s*-\s*(\d+)', td_clean)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
    
    match['home'] = home
    match['away'] = away
    match['homeScore'] = home_score
    match['awayScore'] = away_score
    
    status = 'upcoming'
    status_text = ''
    minute = ''
    
    status_patterns = [
        (r'<span[^>]*class="[^"]*live[^"]*"[^>]*>([^<]+)</span>', 'live'),
        (r'(\d+)["\']?["\']?["\']?\s*</span>', 'live'),
        (r'<td[^>]*class="[^"]*time[^"]*"[^>]*>\s*<span[^>]*>([^<]+)</span>', None),
    ]
    
    for pattern, status_type in status_patterns:
        m = re.search(pattern, tr_content)
        if m:
            status_text = m.group(1).strip()
            if status_type == 'live':
                status = 'live'
                minute = status_text.replace("'", '')
            elif '完' in status_text or '结束' in status_text:
                status = 'finished'
            elif '未' in status_text:
                status = 'upcoming'
            else:
                try:
                    int(status_text.replace("'", ''))
                    status = 'live'
                    minute = status_text.replace("'", '')
                except:
                    pass
            break
    
    match['status'] = status
    match['statusText'] = status_text
    match['minute'] = minute
    match['statusOrder'] = {'live': 1, 'upcoming': 2, 'finished': 3}.get(status, 99)
    match['matchNum'] = ''
    match['homeRank'] = ''
    match['awayRank'] = ''
    
    return match


def parse_live_html_v2(html):
    """备用解析方法"""
    matches = []
    
    table_match = re.search(r'<table[^>]*id=["\']?match_list["\']?[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
    if not table_match:
        table_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL | re.IGNORECASE)
    
    if table_match:
        table_content = table_match.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_content, re.DOTALL | re.IGNORECASE)
        
        for row in rows:
            if 'fid' not in row.lower() and 'tr_' not in row.lower():
                continue
            
            match = {}
            
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 6:
                for cell in cells:
                    text = re.sub(r'<[^>]+>', '', cell).strip()
                    
                    if re.match(r'\d{2}-\d{2}', text):
                        match['date'] = text[:5]
                    elif re.match(r'\d{2}:\d{2}', text):
                        match['time'] = text
                    elif re.match(r'\d+\s*-\s*\d+', text):
                        scores = text.split('-')
                        match['homeScore'] = int(scores[0].strip())
                        match['awayScore'] = int(scores[1].strip())
                    
                    if not match.get('home'):
                        team_link = re.search(r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>', cell)
                        if team_link:
                            match['home'] = team_link.group(1).strip()
                    elif not match.get('away'):
                        team_link = re.search(r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>', cell)
                        if team_link:
                            match['away'] = team_link.group(1).strip()
            
            if match.get('home') and match.get('away'):
                match.setdefault('homeScore', 0)
                match.setdefault('awayScore', 0)
                match.setdefault('status', 'upcoming')
                match.setdefault('minute', '')
                match.setdefault('statusOrder', 2)
                match.setdefault('league', '')
                match.setdefault('matchNum', '')
                matches.append(match)
    
    return matches


def fetch_live_data_from_api():
    """从体育彩票API获取比赛数据"""
    url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001'
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.sporttery.cn/jc/zqszsc/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        return parse_api_data(data)
    except Exception as e:
        print(f'从API获取数据失败: {e}')
        return None


def parse_api_data(data):
    """解析API数据"""
    matches = []
    
    if not data.get('success') or not data.get('value', {}).get('matchInfoList'):
        return None
    
    for day_match in data['value']['matchInfoList']:
        if not day_match.get('subMatchList'):
            continue
        
        match_date = ''
        if day_match.get('matchDate'):
            date_str = day_match['matchDate']
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                match_date = date_obj.strftime('%m-%d')
            except:
                pass
        
        for match in day_match['subMatchList']:
            match_num = match.get('matchNumStr', '')
            
            match_time = match.get('matchTime', '')
            
            home_team = match.get('homeTeamAbbName', '')
            away_team = match.get('awayTeamAbbName', '')
            league = match.get('leagueAbbName', '')
            
            home_rank = ''
            away_rank = ''
            if match.get('homeRank'):
                rank = match['homeRank']
                m = re.search(r'\[(\d+)\]', rank)
                if m:
                    home_rank = m.group(1)
            if match.get('awayRank'):
                rank = match['awayRank']
                m = re.search(r'\[(\d+)\]', rank)
                if m:
                    away_rank = m.group(1)
            
            status = 'upcoming'
            minute = ''
            
            if match.get('poolStatus') == 'close':
                status = 'finished'
            
            matches.append({
                'id': str(match.get('matchId', '')),
                'matchNum': match_num,
                'league': league,
                'date': match_date,
                'time': match_time,
                'home': home_team,
                'away': away_team,
                'homeScore': 0,
                'awayScore': 0,
                'homeRank': home_rank,
                'awayRank': away_rank,
                'status': status,
                'minute': minute,
                'statusOrder': 2 if status == 'upcoming' else 3
            })
    
    matches.sort(key=lambda x: (x.get('statusOrder', 99), x.get('date', ''), x.get('time', '')))
    
    return {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': matches,
        'total': len(matches),
        'live': len([m for m in matches if m['status'] == 'live']),
        'upcoming': len([m for m in matches if m['status'] == 'upcoming']),
        'finished': len([m for m in matches if m['status'] == 'finished'])
    }


def save_data(data, filename):
    """保存数据"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    
    print(f'数据已保存到 {filepath}')


if __name__ == '__main__':
    print('获取比分直播数据...')
    
    live_data = fetch_live_data()
    if live_data and live_data['matches']:
        save_data(live_data, 'live_data.json')
        print(f'共获取 {live_data["total"]} 场比赛')
        print(f'进行中: {live_data["live"]}, 未开始: {live_data["upcoming"]}, 已结束: {live_data["finished"]}')
    else:
        print('从500彩票网获取失败，尝试API...')
        api_data = fetch_live_data_from_api()
        if api_data:
            save_data(api_data, 'live_data.json')
            print(f'共获取 {api_data["total"]} 场比赛')
        else:
            print('获取数据失败')