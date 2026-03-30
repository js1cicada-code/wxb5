#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 竞彩官网版

数据来源：
1. sporttery.cn - 比赛列表、比分、状态（主数据源）
2. 500.com - fixtureId（用于动画链接）

重要规则：
1. 只保留竞彩比赛（有matchNum的比赛）
2. 主数据从竞彩官网获取
3. 500.com仅用于补充fixtureId
"""

import json
import os
import re
from datetime import datetime
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
            
            for day_info in match_info_list:
                match_date = day_info.get('matchDate', '')
                sub_matches = day_info.get('subMatchList', [])
                
                for m in sub_matches:
                    match_num = m.get('matchNumStr', '')
                    if not match_num:
                        continue
                    
                    status_code = str(m.get('matchStatus', '1'))
                    status = status_map.get(status_code, 'upcoming')
                    
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
                        'status': status,
                        'statusName': m.get('matchStatusName', ''),
                        'statusOrder': 1 if status == 'upcoming' else (2 if status == 'live' else 3),
                        'homeId': m.get('homeTeamId', ''),
                        'awayId': m.get('awayTeamId', ''),
                        'leagueId': m.get('leagueId', ''),
                        'fid': '',
                        'fixtureId': '',
                    }
                    
                    matches.append(match_item)
            
            print(f"从竞彩官网获取 {len(matches)} 场比赛")
            return matches
            
    except Exception as e:
        print(f"竞彩官网获取失败: {e}")
        return []


def fetch_fixture_ids_from_500(matches):
    """从500.com获取fixtureId（用于动画链接）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://trade.500.com/jczq/index.php?playid=312&g=2'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    fixture_map = {}
    
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
    
    # 匹配fixtureId到比赛
    matched = 0
    for match in matches:
        key = f"{match['home']}_{match['away']}"
        if key in fixture_map:
            match['fid'] = fixture_map[key]
            match['fixtureId'] = fixture_map[key]
            matched += 1
    
    print(f"匹配到 {matched} 场比赛的fixtureId")


def fetch_namitiyu_ids(matches):
    """获取namitiyu动画ID"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 从fixture_mapping获取
    mapping_file = os.path.join(BASE_DIR, 'data', 'fixture_mapping.json')
    if not os.path.exists(mapping_file):
        mapping_file = os.path.join(BASE_DIR, 'dist', 'fixture_mapping.json')
    
    namitiyu_map = {}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                for key, info in mapping_data.get('mapping', {}).items():
                    fixture_id = info.get('fixtureId')
                    namitiyu_id = info.get('namitiyuId')
                    if fixture_id and namitiyu_id:
                        namitiyu_map[fixture_id] = namitiyu_id
            print(f"从fixture_mapping获取 {len(namitiyu_map)} 个namitiyuId")
        except:
            pass
    
    # 应用到比赛
    matched = 0
    for match in matches:
        fixture_id = match.get('fixtureId', '')
        if fixture_id and fixture_id in namitiyu_map:
            match['namitiyuId'] = namitiyu_map[fixture_id]
            matched += 1
    
    print(f"匹配到 {matched} 场比赛的namitiyuId")


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
    
    # 2. 从500.com获取fixtureId
    print("\n>>> 从500.com获取fixtureId...")
    fetch_fixture_ids_from_500(matches)
    
    # 3. 获取namitiyuId
    print("\n>>> 获取namitiyu动画ID...")
    fetch_namitiyu_ids(matches)
    
    # 4. 统计
    live_count = len([m for m in matches if m['status'] == 'live'])
    finished_count = len([m for m in matches if m['status'] == 'finished'])
    upcoming_count = len([m for m in matches if m['status'] == 'upcoming'])
    
    print(f"\n>>> 统计:")
    print(f"    总比赛: {len(matches)}")
    print(f"    进行中: {live_count}")
    print(f"    已结束: {finished_count}")
    print(f"    未开始: {upcoming_count}")
    print(f"    有fixtureId: {len([m for m in matches if m.get('fixtureId')])}")
    print(f"    有namitiyuId: {len([m for m in matches if m.get('namitiyuId')])}")
    
    # 5. 保存数据
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