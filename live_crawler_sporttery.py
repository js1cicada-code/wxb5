#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 竞彩网官方API版 + 500.com动画数据

数据源：
1. 竞彩网官方API - 比赛列表、状态、比分
2. 500.com - fid（用于动画链接）
3. namitiyu - 动画ID

状态码说明：
- 1: 待开售
- 2: 已开售
- 3: 暂停销售
- 4: 未开播
- 5: 直播中
- 6: 直播结束
- 7: 直播暂停
- 8: 直播推迟
- 9: 直播取消
- 10: 待开奖(销售关闭)
- 11: 已完成
- 12: 销售取消
- 13: 暂停兑奖
"""

import json
import os
import re
import urllib.request
import ssl
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_status_category(status, match_date_str, match_time_str):
    """根据状态码和时间返回状态分类"""
    # 明确已结束的状态
    if status in ['10', '11', '12', '13']:
        return 'finished'
    
    # 明确进行中的状态
    if status in ['5', '6', '7', '8', '9']:
        return 'live'
    
    # 明确未开始的状态
    if status in ['1', '4']:
        return 'upcoming'
    
    # 状态 2, 3 需要根据时间判断
    if status in ['2', '3']:
        now = datetime.now()
        if match_date_str and match_time_str:
            try:
                time_parts = match_time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                date_parts = match_date_str.split('-')
                match_dt = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]), hour, minute)
                match_end = match_dt + timedelta(minutes=120)
                if now < match_dt:
                    return 'upcoming'
                elif now < match_end:
                    return 'live'
                else:
                    return 'finished'
            except:
                pass
        return 'upcoming'
    
    return 'upcoming'

def fetch_match_data():
    """从竞彩网官方API获取比分直播数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://webapi.sporttery.cn/gateway/uniform/fb/getMatchDataPageListV1.qry?method=all&pageSize=200'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://m.sporttery.cn/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return parse_match_data(data)
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def parse_match_data(data):
    """解析API返回的数据"""
    if not data.get('success') or not data.get('value'):
        return None
    
    matches = []
    now = datetime.now()
    
    # 计算5天的日期范围
    today = now.date()
    date_range = []
    for i in range(-2, 3):
        d = today + timedelta(days=i)
        date_range.append(d.strftime('%Y-%m-%d'))
    
    for day_match in data['value'].get('matchInfoList', []):
        match_date = day_match.get('matchDate', '')
        if match_date not in date_range:
            continue
            
        for match in day_match.get('subMatchList', []):
            match_status = str(match.get('matchStatus', ''))
            match_date_str = match.get('matchDate', '')
            match_time_full = match.get('matchTime', '')
            match_time = match_time_full[:5] if match_time_full else ''
            
            status_category = get_status_category(match_status, match_date_str, match_time_full)
            
            # 解析比分
            score_str = match.get('sectionsNo999', '')
            home_score = 0
            away_score = 0
            if score_str and ':' in score_str:
                try:
                    parts = score_str.split(':')
                    home_score = int(parts[0])
                    away_score = int(parts[1])
                except:
                    pass
            
            half_score = match.get('sectionsNo1', '')
            sale_date_display = match_date_str if match_date_str else ''
            
            item = {
                'id': str(match.get('matchId', '')),
                'fid': '',
                'matchNum': match.get('matchNumStr', ''),
                'league': match.get('leagueAbbName', ''),
                'date': match_date_str,
                'time': match_time,
                'home': match.get('homeTeamAbbName', ''),
                'away': match.get('awayTeamAbbName', ''),
                'homeScore': home_score,
                'awayScore': away_score,
                'halfScore': half_score,
                'status': status_category,
                'statusCode': match_status,
                'statusName': match.get('matchStatusName', ''),
                'minute': '',
                'statusOrder': 1 if status_category == 'live' else (2 if status_category == 'upcoming' else 3),
                'saleDateDisplay': sale_date_display,
                'namitiyuId': ''
            }
            
            # 如果是直播中，计算分钟数
            if status_category == 'live' and match_date_str and match_time_full:
                try:
                    time_parts = match_time_full.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    date_parts = match_date_str.split('-')
                    match_dt = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]), hour, minute)
                    elapsed = int((now - match_dt).total_seconds() / 60)
                    if 0 < elapsed <= 90:
                        item['minute'] = str(elapsed)
                except:
                    pass
            
            matches.append(item)
    
    matches.sort(key=lambda x: (x['statusOrder'], x.get('matchNum', '')))
    return matches

def fetch_500_fid_map():
    """从500.com获取fid映射（球队名 -> fid）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    fid_map = {}
    now = datetime.now()
    
    urls = [
        'https://live.500.com/',
        f'https://live.500.com/?e={(now - timedelta(days=1)).strftime("%Y-%m-%d")}'
    ]
    
    for url in urls:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                html = response.read().decode('gb2312', errors='ignore')
                
                pattern = r'<tr[^>]*fid=["\']?(\d+)["\']?[^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
                
                for fid, row in rows:
                    team_pattern = r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>'
                    teams = re.findall(team_pattern, row)
                    
                    if len(teams) >= 2:
                        home = teams[0].strip()
                        away = teams[1].strip()
                        key = f"{home}_{away}"
                        fid_map[key] = fid
        except Exception as e:
            print(f"    获取500.com数据失败: {e}")
    
    print(f"    获取 {len(fid_map)} 个fid映射")
    return fid_map

def enrich_matches_with_fid(matches, fid_map):
    """用500.com的fid补充比赛数据"""
    count = 0
    for m in matches:
        # 尝试多种匹配方式
        keys_to_try = [
            f"{m.get('home', '')}_{m.get('away', '')}",
            f"{m.get('home', '').replace(' ', '')}_{m.get('away', '').replace(' ', '')}",
        ]
        
        for key in keys_to_try:
            if key in fid_map:
                m['fid'] = fid_map[key]
                count += 1
                break
    
    print(f"    匹配到 {count} 个fid")
    return matches

def fetch_namitiyu_ids(matches):
    """获取namitiyu动画ID"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    count = 0
    for m in matches:
        fid = m.get('fid')
        if fid and not m.get('namitiyuId'):
            url = f'https://odds.500.com/fenxi/stat-{fid}.shtml'
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                    html = resp.read().decode('gb2312', errors='ignore')
                match = re.search(r'tracker\.namitiyu\.com[^"\']+id=(\d+)', html)
                if match:
                    m['namitiyuId'] = match.group(1)
                    count += 1
            except:
                pass
    
    print(f"    获取 {count} 个namitiyu ID")
    return matches

def fetch_basketball_data():
    """获取篮球比分直播数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://webapi.sporttery.cn/gateway/uniform/bk/getMatchDataPageListV1.qry?method=all&pageSize=200'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://m.sporttery.cn/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return parse_basketball_data(data)
    except Exception as e:
        print(f"获取篮球数据失败: {e}")
        return []

def parse_basketball_data(data):
    """解析篮球数据"""
    if not data.get('success') or not data.get('value'):
        return []
    
    matches = []
    now = datetime.now()
    
    today = now.date()
    date_range = []
    for i in range(-2, 3):
        d = today + timedelta(days=i)
        date_range.append(d.strftime('%Y-%m-%d'))
    
    for day_match in data['value'].get('matchInfoList', []):
        match_date = day_match.get('matchDate', '')
        if match_date not in date_range:
            continue
            
        for match in day_match.get('subMatchList', []):
            match_status = str(match.get('matchStatus', ''))
            match_date_str = match.get('matchDate', '')
            match_time_full = match.get('matchTime', '')
            match_time = match_time_full[:5] if match_time_full else ''
            
            status_category = get_status_category(match_status, match_date_str, match_time_full)
            
            score_str = match.get('sectionsNo999', '')
            home_score = 0
            away_score = 0
            if score_str and ':' in score_str:
                try:
                    parts = score_str.split(':')
                    home_score = int(parts[0])
                    away_score = int(parts[1])
                except:
                    pass
            
            item = {
                'id': str(match.get('matchId', '')),
                'matchNum': match.get('matchNumStr', ''),
                'league': match.get('leagueAbbName', ''),
                'date': match_date_str,
                'time': match_time,
                'home': match.get('homeTeamAbbName', ''),
                'away': match.get('awayTeamAbbName', ''),
                'homeScore': home_score,
                'awayScore': away_score,
                'status': status_category,
                'statusCode': match_status,
                'statusName': match.get('matchStatusName', ''),
                'minute': '',
                'statusOrder': 1 if status_category == 'live' else (2 if status_category == 'upcoming' else 3),
                'saleDateDisplay': match_date_str
            }
            
            matches.append(item)
    
    matches.sort(key=lambda x: (x['statusOrder'], x.get('matchNum', '')))
    return matches

def save_data(data, filename):
    """保存数据到多个位置"""
    paths = [
        os.path.join(BASE_DIR, 'data', filename),
        os.path.join(BASE_DIR, 'dist', filename),
        os.path.join(BASE_DIR, 'dist', 'data', filename)
    ]
    
    for path in paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'>>> 数据已保存到 {len(paths)} 个位置')

if __name__ == '__main__':
    print('=' * 50)
    print('比分直播爬虫 - 竞彩网API + 500.com动画')
    print('=' * 50)
    
    # 获取足球数据
    print('>>> 获取足球比分直播数据...')
    football_matches = fetch_match_data()
    
    if football_matches:
        # 统计
        finished_count = len([m for m in football_matches if m['status'] == 'finished'])
        live_count = len([m for m in football_matches if m['status'] == 'live'])
        upcoming_count = len([m for m in football_matches if m['status'] == 'upcoming'])
        
        print(f'>>> 足球: 已结束 {finished_count}场, 进行中 {live_count}场, 未开始 {upcoming_count}场')
        
        # 获取500.com fid
        print('>>> 从500.com获取fid...')
        fid_map = fetch_500_fid_map()
        football_matches = enrich_matches_with_fid(football_matches, fid_map)
        
        # 获取namitiyu动画ID
        print('>>> 获取动画ID...')
        football_matches = fetch_namitiyu_ids(football_matches)
        
        animation_count = len([m for m in football_matches if m.get('namitiyuId')])
        print(f'>>> 支持动画直播: {animation_count}场')
        
        data = {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(football_matches),
            'live': live_count,
            'finished': finished_count,
            'upcoming': upcoming_count,
            'matches': football_matches
        }
        
        save_data(data, 'live_data.json')
    
    # 获取篮球数据
    print('>>> 获取篮球比分直播数据...')
    basketball_matches = fetch_basketball_data()
    
    if basketball_matches:
        finished_count = len([m for m in basketball_matches if m['status'] == 'finished'])
        live_count = len([m for m in basketball_matches if m['status'] == 'live'])
        upcoming_count = len([m for m in basketball_matches if m['status'] == 'upcoming'])
        
        print(f'>>> 篮球: 已结束 {finished_count}场, 进行中 {live_count}场, 未开始 {upcoming_count}场')
        
        data = {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total': len(basketball_matches),
            'live': live_count,
            'finished': finished_count,
            'upcoming': upcoming_count,
            'matches': basketball_matches
        }
        
        save_data(data, 'live_basketball_data.json')
    
    print('>>> 完成')