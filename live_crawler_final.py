#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 竞彩官网版

数据来源：
1. sporttery.cn - 比赛列表、比分、状态（主数据源）
2. 500.com - fixtureId、namitiyuId（用于动画链接）

规则：
1. 只保留竞彩比赛（有matchNum的比赛）
2. 已结束的比赛只保留过去3天
3. 所有比赛都要匹配动画链接
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_from_sporttery():
    """从竞彩官网获取比分直播数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://webapi.sporttery.cn/gateway/uniform/fb/getMatchDataPageListV1.qry?method=all&pageSize=200'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.sporttery.cn/',
        'Accept': 'application/json, text/plain, */*'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.load(response)
            
            if not data.get('success'):
                print("竞彩API返回失败")
                return []
            
            matches = []
            match_info_list = data.get('value', {}).get('matchInfoList', [])
            
            status_map = {
                '1': 'upcoming',    # 待开售
                '3': 'upcoming',    # 暂停销售
                '11': 'finished',   # 已完成
            }
            
            now = datetime.now()
            three_days_ago = now - timedelta(days=3)
            
            for day_info in match_info_list:
                match_date = day_info.get('matchDate', '')
                sub_matches = day_info.get('subMatchList', [])
                
                # 解析日期
                try:
                    date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                except:
                    date_obj = None
                
                # 计算周几
                weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                weekday = weekday_names[date_obj.weekday()] if date_obj else ''
                
                for m in sub_matches:
                    match_num = m.get('matchNumStr', '')
                    if not match_num:
                        continue
                    
                    status_code = str(m.get('matchStatus', '1'))
                    status = status_map.get(status_code, 'upcoming')
                    
                    # 已结束的比赛只保留过去3天
                    if status == 'finished' and date_obj:
                        if date_obj.date() < three_days_ago.date():
                            continue
                    
                    # 解析比分
                    score_str = m.get('sectionsNo999', '')
                    home_score = 0
                    away_score = 0
                    if score_str and ':' in score_str:
                        try:
                            parts = score_str.split(':')
                            home_score = int(parts[0])
                            away_score = int(parts[1])
                        except:
                            pass
                    
                    # 格式化日期显示 (X月X日 周X)
                    month = date_obj.month if date_obj else 0
                    day = date_obj.day if date_obj else 0
                    sale_date_display = f"{month}月{day}日 {weekday}" if date_obj else match_date
                    
                    match_item = {
                        'id': str(m.get('matchId', '')),
                        'matchNum': match_num,
                        'matchNumStr': match_num,
                        'home': m.get('homeTeamAbbName', ''),
                        'away': m.get('awayTeamAbbName', ''),
                        'homeName': m.get('homeTeamAllName', m.get('homeTeamAbbName', '')),
                        'awayName': m.get('awayTeamAllName', m.get('awayTeamAbbName', '')),
                        'homeScore': home_score,
                        'awayScore': away_score,
                        'league': m.get('leagueAbbName', ''),
                        'leagueName': m.get('leagueAllName', m.get('leagueAbbName', '')),
                        'date': match_date,
                        'time': m.get('matchTime', ''),
                        'saleDateDisplay': sale_date_display,
                        'status': status,
                        'statusName': m.get('matchStatusName', ''),
                        'statusOrder': 1 if status == 'upcoming' else (2 if status == 'live' else 3),
                        'homeId': m.get('homeTeamId', ''),
                        'awayId': m.get('awayTeamId', ''),
                        'leagueId': m.get('leagueId', ''),
                        'fid': '',
                        'fixtureId': '',
                        'namitiyuId': '',
                    }
                    
                    matches.append(match_item)
            
            print(f"从竞彩官网获取 {len(matches)} 场比赛")
            return matches
            
    except Exception as e:
        print(f"竞彩官网获取失败: {e}")
        return []


def fetch_animation_ids_from_500(matches):
    """从500.com获取fixtureId和namitiyuId（用于动画链接）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    # 1. 从比赛列表页获取fixtureId
    url = 'https://trade.500.com/jczq/index.php'
    fixture_map = {}  # 球队名 -> fixtureId
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
            
            # 解析fixtureId
            pattern = r'data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"'
            for m in re.finditer(pattern, html):
                fixture_id, home, away = m.groups()
                key = f"{home}_{away}"
                fixture_map[key] = fixture_id
            
            print(f"从500.com获取 {len(fixture_map)} 个fixtureId")
            
    except Exception as e:
        print(f"500.com获取fixtureId失败: {e}")
    
    # 2. 从namitiyu API获取动画ID
    namitiyu_map = {}  # fixtureId -> namitiyuId
    
    # 收集所有fixtureId
    fixture_ids = list(set(fixture_map.values()))
    
    if fixture_ids:
        # 批量获取namitiyuId
        for i in range(0, len(fixture_ids), 20):
            batch = fixture_ids[i:i+20]
            ids_str = ','.join(batch)
            namitiyu_url = f'https://live.500.com/static/info/bifen/xml/namitiyu/{ids_str}.txt'
            
            try:
                req = urllib.request.Request(namitiyu_url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    # 解析JSONP格式
                    if content.startswith('namitiyuCallback'):
                        json_str = content[content.index('(')+1:content.rindex(')')]
                        data = json.loads(json_str)
                        for fid, nid in data.items():
                            namitiyu_map[fid] = nid
            except:
                pass
        
        print(f"获取到 {len(namitiyu_map)} 个namitiyuId")
    
    # 3. 匹配到比赛
    matched_fixture = 0
    matched_namitiyu = 0
    
    for match in matches:
        key = f"{match['home']}_{match['away']}"
        
        # 精确匹配
        if key in fixture_map:
            match['fid'] = fixture_map[key]
            match['fixtureId'] = fixture_map[key]
            matched_fixture += 1
            
            if fixture_map[key] in namitiyu_map:
                match['namitiyuId'] = namitiyu_map[fixture_map[key]]
                matched_namitiyu += 1
        else:
            # 模糊匹配
            for k, fid in fixture_map.items():
                if match['home'][:3] in k and match['away'][:3] in k:
                    match['fid'] = fid
                    match['fixtureId'] = fid
                    matched_fixture += 1
                    
                    if fid in namitiyu_map:
                        match['namitiyuId'] = namitiyu_map[fid]
                        matched_namitiyu += 1
                    break
    
    print(f"匹配 fixtureId: {matched_fixture}, namitiyuId: {matched_namitiyu}")


def save_data(data):
    """保存数据到多个位置"""
    paths = [
        os.path.join(BASE_DIR, 'data', 'live_data.json'),
        os.path.join(BASE_DIR, 'dist', 'live_data.json'),
        os.path.join(BASE_DIR, 'dist', 'data', 'live_data.json'),
    ]
    
    for path in paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")


def main():
    print("=" * 50)
    print("比分直播爬虫 - 竞彩官网版")
    print("=" * 50)
    
    # 1. 从竞彩官网获取比赛数据
    print("\n>>> 从竞彩官网获取比分直播数据...")
    matches = fetch_from_sporttery()
    
    if not matches:
        print("未获取到比赛数据")
        return
    
    # 2. 从500.com获取动画ID
    print("\n>>> 从500.com获取动画链接...")
    fetch_animation_ids_from_500(matches)
    
    # 3. 统计
    live_count = len([m for m in matches if m['status'] == 'live'])
    finished_count = len([m for m in matches if m['status'] == 'finished'])
    upcoming_count = len([m for m in matches if m['status'] == 'upcoming'])
    
    print(f"\n>>> 统计:")
    print(f"    总比赛: {len(matches)}")
    print(f"    进行中: {live_count}")
    print(f"    已结束: {finished_count}")
    print(f"    未开始: {upcoming_count}")
    print(f"    有动画链接: {len([m for m in matches if m.get('fixtureId')])}")
    
    # 4. 保存数据
    data = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': matches,
        'total': len(matches),
        'live': live_count,
        'finished': finished_count,
        'upcoming': upcoming_count
    }
    
    save_data(data)
    
    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == '__main__':
    main()