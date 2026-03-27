#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 多数据源整合版
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl
import gzip

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_live_scores_500():
    """从500.com获取实时比分和状态 - 支持多天数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    live_data = {}
    now = datetime.now()
    
    # 星期映射
    weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
    today_weekday = now.weekday()
    
    # 获取今天和昨天的比赛
    urls_to_fetch = []
    
    # 今天的比赛
    urls_to_fetch.append(('https://live.500.com/', 'today'))
    
    # 昨天的比赛
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    urls_to_fetch.append((f'https://live.500.com/?e={yesterday_str}', 'yesterday'))
    
    for url, day_type in urls_to_fetch:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                html = response.read().decode('gb2312', errors='ignore')
                
                # 匹配所有比赛行
                pattern = r'<tr[^>]*fid=["\']?(\d+)["\']?[^>]*>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
                
                for fid, row in rows:
                    # 获取球队名称
                    team_pattern = r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>'
                    teams = re.findall(team_pattern, row)
                    
                    if len(teams) >= 2:
                        home = teams[0].strip()
                        away = teams[1].strip()
                        
                        # 获取比赛编号（周五001）
                        num_match = re.search(r'>(周[一二三四五六日])(\d+)</', row)
                        if num_match:
                            sale_day_name = num_match.group(1)  # 周五
                            match_num = num_match.group(1) + num_match.group(2)  # 周五001
                            
                            # 计算开售日期
                            sale_weekday = weekday_map.get(sale_day_name, today_weekday)
                            
                            if sale_weekday >= today_weekday:
                                # 未来或今天开售
                                days_diff = sale_weekday - today_weekday
                                sale_date = now + timedelta(days=days_diff)
                            else:
                                # 过去开售
                                days_diff = today_weekday - sale_weekday
                                sale_date = now - timedelta(days=days_diff)
                        else:
                            match_num = ''
                            sale_date = now if day_type == 'today' else yesterday
                        
                        # 获取比分
                        score_pattern = r'href="./detail\.php\?fid=\d+[^"]*"[^>]*>(\d+)</a>'
                        scores = re.findall(score_pattern, row)
                        
                        home_score = int(scores[0]) if len(scores) > 0 else 0
                        away_score = int(scores[1]) if len(scores) > 1 else 0
                        
                        # 获取联赛
                        league_match = re.search(r'<a[^>]*href="//liansai\.500\.com/zuqiu-\d+/"[^>]*>([^<]+)</a>', row)
                        league = league_match.group(1) if league_match else '国际赛'
                        
                        # 获取比赛日期和时间
                        date_time_match = re.search(r'(\d{2}-\d{2})\s+(\d{2}:\d{2})', row)
                        match_date_str = date_time_match.group(1) if date_time_match else ''
                        time_str = date_time_match.group(2) if date_time_match else ''
                        
                        # 计算实际比赛时间
                        if match_date_str:
                            month, day = map(int, match_date_str.split('-'))
                            match_datetime = datetime(now.year, month, day)
                        else:
                            match_datetime = sale_date
                        
                        if time_str:
                            h, m = map(int, time_str.split(':'))
                            match_datetime = match_datetime.replace(hour=h, minute=m)
                        
# 判断状态 - 基于比分和时间的智能判断
                        status = 'upcoming'
                        minute = ''
                        
                        # 先检查页面上的明确状态
                        if '完场' in row or '-完' in row:
                            status = 'finished'
                        elif '进行中' in row or "class='live'" in row or 'class="live"' in row:
                            status = 'live'
                            minute_match = re.search(r"(\d+)'", row)
                            if minute_match:
                                minute = minute_match.group(1)
                        else:
                            # 没有明确状态，根据比分和时间智能判断
                            has_score = home_score > 0 or away_score > 0
                            
                            if match_date_str and time_str:
                                try:
                                    month, day = map(int, match_date_str.split('-'))
                                    h, m = map(int, time_str.split(':'))
                                    
                                    match_dt = datetime(now.year, month, day, h, m)
                                    match_end = match_dt + timedelta(minutes=105)  # 比赛结束时间(含补时)
                                    
                                    if now < match_dt:
                                        # 还未开始
                                        status = 'upcoming'
                                    elif now < match_end:
                                        # 比赛进行中
                                        status = 'live'
                                        elapsed = int((now - match_dt).total_seconds() / 60)
                                        if elapsed > 90:
                                            elapsed = 90  # 补时不显示
                                        minute = str(elapsed)
                                    else:
                                        # 已结束
                                        status = 'finished'
                                        
                                        # 如果是今天或昨天开售的比赛，且无比分，尝试获取比分
                                        if not has_score:
                                            days_diff = (now.date() - match_dt.date()).days
                                            if days_diff <= 1:  # 今天或昨天的比赛
                                                # 暂时标记为finished，后续会从okooo获取比分
                                                pass
                                except:
                                    pass
                            elif has_score:
                                # 有比分但没有时间，假设已结束
                                status = 'finished'
                        
                        key = f"{home}_{away}"
                        live_data[key] = {
                            'fid': fid,
                            'matchNum': match_num,
                            'homeScore': home_score,
                            'awayScore': away_score,
                            'status': status,
                            'minute': minute,
                            'league': league,
                            'date': match_date_str,
                            'time': time_str,
                            'saleDate': sale_date.strftime('%m-%d'),
                            'saleDateDisplay': sale_date.strftime('%Y-%m-%d')
                        }
                        
        except Exception as e:
            print(f"    {day_type}数据获取失败: {e}")
    
    print(f"    获取 {len(live_data)} 场实时比分")
    return live_data


def fetch_all_data():
    """整合所有数据源"""
    # 1. 从sporttery获取完整赛程和日期
    print(">>> 从sporttery获取赛程...")
    sporttery_matches = fetch_from_sporttery()
    
    # 2. 从500彩票网获取实时比分和fid
    print(">>> 从500彩票网获取实时比分和动画ID...")
    live_data = fetch_live_scores_500()
    
    # 3. 从59itou获取联赛信息补充
    print(">>> 从59itou获取联赛信息...")
    league_map = fetch_league_map()
    
    # 合并数据
    matches = []
    processed_keys = set()
    
    # 首先处理sporttery的比赛
    if sporttery_matches:
        for m in sporttery_matches:
            key = f"{m['home']}_{m['away']}"
            processed_keys.add(key)
            
            if key in live_data:
                ld = live_data[key]
                m['fid'] = ld['fid']
                m['matchNum'] = ld.get('matchNum', '')
                m['homeScore'] = ld['homeScore']
                m['awayScore'] = ld['awayScore']
                m['status'] = ld['status']
                m['minute'] = ld['minute']
                m['saleDate'] = ld.get('saleDate', '')
                m['saleDateDisplay'] = ld.get('saleDateDisplay', '')
                # 用500.com的数据覆盖日期时间（更准确）
                if ld.get('date'):
                    m['date'] = ld['date']
                if ld.get('time'):
                    m['time'] = ld['time']
                # 用500.com的联赛信息（更准确）
                if ld.get('league'):
                    m['league'] = ld['league']
            else:
                m['fid'] = ''
                m['matchNum'] = ''
                # 对于不在500.com中的比赛，使用比赛日期作为分组依据
                if not m.get('saleDateDisplay'):
                    # 从date字段解析日期 (格式: "2026年3月28日 周六")
                    date_str = m.get('date', '')
                    if date_str:
                        import re
                        match = re.search(r'(\d{4})年(\d+)月(\d+)日', date_str)
                        if match:
                            year, month, day = match.groups()
                            m['saleDateDisplay'] = f"{year}-{int(month):02d}-{int(day):02d}"
                        else:
                            m['saleDateDisplay'] = date_str
                    else:
                        m['saleDateDisplay'] = '未知日期'
            
            # 补充联赛信息
            if not m.get('league') or m['league'] == '国际赛':
                league_key = f"{m['home']}_{m['away']}"
                if league_key in league_map:
                    m['league'] = league_map[league_key]
            
            matches.append(m)
    
    # 添加500.com独有的比赛（不在sporttery中的）
    for key, ld in live_data.items():
        if key not in processed_keys:
            # 创建新的比赛记录
            match = {
                'matchId': '',
                'fid': ld['fid'],
                'matchNum': ld.get('matchNum', ''),
                'home': key.split('_')[0] if '_' in key else '',
                'away': key.split('_')[1] if '_' in key else '',
                'homeScore': ld['homeScore'],
                'awayScore': ld['awayScore'],
                'status': ld['status'],
                'minute': ld['minute'],
                'league': ld.get('league', '国际赛'),
                'date': ld.get('date', ''),
                'time': ld.get('time', ''),
                'saleDate': ld.get('saleDate', ''),
                'saleDateDisplay': ld.get('saleDateDisplay', ''),
                'homeRank': '',
                'awayRank': ''
            }
            
            matches.append(match)
            print(f"    添加500独有比赛: {match['home']} vs {match['away']}")
    
    # 获取namitiyu ID
    print(">>> 获取namitiyu动画ID...")
    matches = fetch_namitiyu_ids(matches)
    
    # 根据时间判断状态
    print(">>> 判断比赛状态...")
    now = datetime.now()
    for m in matches:
        if m['status'] == 'upcoming':
            date_str = m.get('date', '')
            time_str = m.get('time', '')
            
            try:
                if not time_str:
                    continue
                    
                h, mi = map(int, time_str.split(':'))
                match_minutes = h * 60 + mi
                now_minutes = now.hour * 60 + now.minute
                
                # 检查日期
                today = now.day
                match_day = None
                
                if '今天' in date_str or date_str == '':
                    match_day = today
                else:
                    # 格式: 03-27
                    day_match = re.search(r'(\d{2})-(\d{2})', date_str)
                    if day_match:
                        match_day = int(day_match.group(2))
                
                if match_day:
                    # 同一天的比赛
                    if match_day == today:
                        # 已经过了比赛时间
                        if now_minutes > match_minutes:
                            # 超过2.5小时算结束
                            if now_minutes - match_minutes > 150:
                                m['status'] = 'finished'
                            else:
                                m['status'] = 'live'
                                m['minute'] = str(now_minutes - match_minutes)
                    # 比赛日期在过去
                    elif match_day < today or (match_day > 25 and today < 5):
                        m['status'] = 'finished'
            except:
                pass
    
    # 获取已结束比赛的比分
    print(">>> 获取已结束比赛比分...")
    fetch_finished_scores(matches)
    
    # 统计状态
    live_count = len([m for m in matches if m['status'] == 'live'])
    finished_count = len([m for m in matches if m['status'] == 'finished'])
    upcoming_count = len([m for m in matches if m['status'] == 'upcoming'])
    print(f">>> 支持动画直播: {len([m for m in matches if m.get('fid')])}场")
    print(f">>> 支持namitiyu动画: {len([m for m in matches if m.get('namitiyuId')])}场")
    print(f">>> 进行中: {live_count}场, 已结束: {finished_count}场, 未开始: {upcoming_count}场")
    
    return {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': matches,
        'total': len(matches),
        'live': live_count,
        'upcoming': upcoming_count,
        'finished': finished_count
    }


def fetch_finished_scores(matches):
    """从okooo获取已结束比赛的比分"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    updated = 0
    for m in matches:
        if m['status'] != 'finished' or not m.get('fid'):
            continue
        
        if m['homeScore'] > 0 or m['awayScore'] > 0:
            continue
        
        fid = m['fid']
        url = f'https://www.okooo.com/match/{fid}/'
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                
                score_pattern = r'<span[^>]*class="[^"]*score[^"]*"[^>]*>(\d+)</span>'
                scores = re.findall(score_pattern, html)
                
                if len(scores) >= 2:
                    m['homeScore'] = int(scores[0])
                    m['awayScore'] = int(scores[1])
                    updated += 1
        except:
            pass
    
    if updated > 0:
        print(f"    从okooo更新 {updated} 场比分")


def fetch_from_sporttery():
    """从体育彩票API获取数据 - 使用getMatchListV1获取完整列表"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001'
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.sporttery.cn/'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return parse_sporttery_data(data)
    except Exception as e:
        print(f"    sporttery获取失败: {e}")
        return None


def parse_sporttery_data(data):
    """解析sporttery数据"""
    matches = []
    
    if not data.get('success') or not data.get('value', {}).get('matchInfoList'):
        return None
    
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    
    for day_match in data['value']['matchInfoList']:
        if not day_match.get('subMatchList'):
            continue
        
        for match in day_match['subMatchList']:
            match_num = match.get('matchNumStr', '')
            match_time_str = match.get('matchTime', '')
            
            # 获取比赛小时
            hour = 0
            if match_time_str:
                try:
                    hour = int(match_time_str.split(':')[0])
                except:
                    pass
            
            # 计算比赛日期
            weekdays_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
            match_weekday = None
            for day_name, day_num in weekdays_map.items():
                if match_num.startswith(day_name):
                    match_weekday = day_num
                    break
            
            if match_weekday is not None:
                today_weekday = today.weekday()
                days_diff = (match_weekday - today_weekday) % 7
                if days_diff > 3:
                    days_diff -= 7
                match_date = today + timedelta(days=days_diff)
                
                weekday_name = weekdays[match_date.weekday()]
                match_date_str = match_date.strftime('%Y-%m-%d')
                
                if match_date_str == today_str:
                    match_date_display = f"{match_date.year}年{match_date.month}月{match_date.day}日 今天 {weekday_name}"
                else:
                    match_date_display = f"{match_date.year}年{match_date.month}月{match_date.day}日 {weekday_name}"
            else:
                match_date_display = ''
                match_date_str = ''
            
            matches.append({
                'id': str(match.get('matchId', '')),
                'fid': '',
                'matchNum': match_num,
                'league': match.get('leagueAbbName', ''),
                'date': match_date_display,
                'time': match_time_str[:5] if match_time_str else '',
                'home': match.get('homeTeamAbbName', ''),
                'away': match.get('awayTeamAbbName', ''),
                'homeScore': 0,
                'awayScore': 0,
                'status': 'upcoming',
                'minute': '',
                'statusOrder': 2
            })
    
    return matches


def fetch_namitiyu_ids(matches):
    """批量获取namitiyu ID"""
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
                match = re.search(r'tracker\.namitiyu\.com[^\"\']+id=(\d+)', html)
                if match:
                    m['namitiyuId'] = match.group(1)
                    count += 1
            except:
                pass
    print(f"    获取 {count} 个namitiyu ID")
    return matches


def fetch_league_map():
    """从59itou获取联赛信息"""
    from playwright.sync_api import sync_playwright
    
    url = 'https://kt.59itou.com/694/livescore/631/jingcai/'
    league_map = {}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15')
            page.goto(url, wait_until='networkidle', timeout=60000)
            page.wait_for_selector('.liveitem', timeout=10000)
            html = page.content()
            browser.close()
            
            pattern = r'<div[^>]*class="[^"]*liveitem[^"]*"[^>]*>([\s\S]*?)</div>\s*</div>\s*</div>'
            items = re.findall(pattern, html)
            
            for item in items:
                league = re.search(r'<p class="fontblue">([^<]+)</p>', item)
                teams = re.findall(r'<span class="font15">([^<]+)</span>', item)
                
                if league and len(teams) >= 2:
                    key = f"{teams[0].strip()}_{teams[1].strip()}"
                    league_map[key] = league.group(1).strip()
                    
        print(f"    获取 {len(league_map)} 个联赛信息")
    except Exception as e:
        print(f"    59itou获取失败: {e}")
    
    return league_map


def save_data(data, filename):
    """保存数据到所有需要的位置"""
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
    print('比分直播爬虫')
    print('=' * 50)
    
    data = fetch_all_data()
    
    if data and data['matches']:
        save_data(data, 'live_data.json')
        
        by_date = {}
        for m in data['matches']:
            d = m.get('saleDateDisplay', '未知')
            by_date[d] = by_date.get(d, 0) + 1
        
        print("\n按开售日期统计:")
        for d, count in sorted(by_date.items()):
            print(f"  {d}: {count}场")