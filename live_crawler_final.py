#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 竞彩官网版

数据来源：
1. sporttery.cn - 比赛列表、比分、状态（主数据源）
2. 500.com - fixtureId、namitiyuId（用于动画链接）

规则：
1. 只保留竞彩比赛（有matchNum的比赛）
2. 已结束的比赛只保留过去3天（live_data.json）
3. 所有比赛映射保存到fixture_mapping.json（累积）
4. 定时任务会累积历史数据
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_all_from_sporttery():
    """从竞彩官网获取所有比赛数据（包括历史）"""
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
            
            all_matches = []
            match_info_list = data.get('value', {}).get('matchInfoList', [])
            
            status_map = {
                '1': 'upcoming',
                '3': 'upcoming',
                '11': 'finished',
            }
            
            for day_info in match_info_list:
                match_date = day_info.get('matchDate', '')
                sub_matches = day_info.get('subMatchList', [])
                
                try:
                    date_obj = datetime.strptime(match_date, '%Y-%m-%d')
                except:
                    date_obj = None
                
                weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                weekday = weekday_names[date_obj.weekday()] if date_obj else ''
                
                for m in sub_matches:
                    match_num = m.get('matchNumStr', '')
                    if not match_num:
                        continue
                    
                    status_code = str(m.get('matchStatus', '1'))
                    status = status_map.get(status_code, 'upcoming')
                    
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
                    
                    all_matches.append(match_item)
            
            print(f"从竞彩官网获取 {len(all_matches)} 场比赛")
            return all_matches
            
    except Exception as e:
        print(f"竞彩官网获取失败: {e}")
        return []


def filter_for_display(all_matches):
    """过滤比赛用于显示：已结束只保留过去3天"""
    now = datetime.now()
    three_days_ago = now - timedelta(days=3)
    
    filtered = []
    for m in all_matches:
        if m['status'] == 'finished':
            try:
                match_date = datetime.strptime(m['date'], '%Y-%m-%d')
                if match_date.date() < three_days_ago.date():
                    continue
            except:
                pass
        filtered.append(m)
    
    return filtered


def fetch_fixture_from_500():
    """从500.com获取fixtureId"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    fixture_map = {}
    
    url = 'https://trade.500.com/jczq/index.php'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('gb2312', errors='ignore')
            
            pattern = r'data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"'
            for m in re.finditer(pattern, html):
                fixture_id, home, away = m.groups()
                key = f"{home}_{away}"
                fixture_map[key] = {
                    'fixtureId': fixture_id,
                    'home': home,
                    'away': away,
                }
            
            print(f"从500.com获取 {len(fixture_map)} 个fixtureId")
            
    except Exception as e:
        print(f"500.com获取fixtureId失败: {e}")
    
    return fixture_map


def update_fixture_mapping(all_matches, fixture_map):
    """更新fixture_mapping.json（累积保存）"""
    mapping_file = os.path.join(BASE_DIR, 'data', 'fixture_mapping.json')
    
    existing = {'mapping': {}, 'byMatchId': {}}
    if os.path.exists(mapping_file):
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            pass
    
    # 从已有的分析文件中提取fixtureId
    analysis_dir = os.path.join(BASE_DIR, 'data')
    analysis_files = []
    try:
        analysis_files = [f for f in os.listdir(analysis_dir) if f.startswith('analysis_') and f.endswith('.json')]
    except:
        pass
    
    analysis_count = 0
    for af in analysis_files:
        try:
            fid = af.replace('analysis_', '').replace('.json', '')
            af_path = os.path.join(analysis_dir, af)
            with open(af_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                home = data.get('home', '')
                away = data.get('away', '')
                if home and away:
                    key = f"{home}_{away}"
                    if key not in existing['mapping']:
                        existing['mapping'][key] = {
                            'fixtureId': fid,
                            'home': home,
                            'away': away,
                        }
                        analysis_count += 1
                    elif 'fixtureId' not in existing['mapping'][key]:
                        existing['mapping'][key]['fixtureId'] = fid
                        analysis_count += 1
        except:
            pass
    
    print(f"从 {len(analysis_files)} 个分析文件中提取 {analysis_count} 个fixtureId")
    
    new_count = 0
    
    for m in all_matches:
        match_id = m['id']
        key = f"{m['home']}_{m['away']}"
        
        # 保留已有的fixtureId
        existing_entry = existing['mapping'].get(key, {})
        
        entry = {
            'matchId': match_id,
            'home': m['home'],
            'away': m['away'],
            'matchNum': m['matchNum'],
            'league': m['league'],
            'date': m['date'],
        }
        
        # 保留已有的fixtureId
        if 'fixtureId' in existing_entry:
            entry['fixtureId'] = existing_entry['fixtureId']
            # 保存备用fixtureId（分析文件可能有不同的fixtureId）
            if 'analysisFixtureId' in existing_entry:
                entry['analysisFixtureId'] = existing_entry['analysisFixtureId']
        
        # 如果500.com有新的fixtureId，使用新的
        if key in fixture_map:
            entry['fixtureId'] = fixture_map[key]['fixtureId']
            if 'namitiyuId' in fixture_map[key]:
                entry['namitiyuId'] = fixture_map[key]['namitiyuId']
        
        if key not in existing['mapping']:
            new_count += 1
        existing['mapping'][key] = entry
        
        if match_id:
            if match_id not in existing['byMatchId']:
                new_count += 1
            existing['byMatchId'][match_id] = entry
    
    os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    # 同步到其他位置
    for path in [
        os.path.join(BASE_DIR, 'dist', 'fixture_mapping.json'),
        os.path.join(BASE_DIR, 'dist', 'data', 'fixture_mapping.json'),
    ]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    fixture_count = len([v for v in existing['mapping'].values() if 'fixtureId' in v])
    print(f"fixture_mapping: 总计 {len(existing['mapping'])} 条, 新增 {new_count} 条, 有fixtureId {fixture_count} 条")
    
    return existing


def apply_fixture_to_matches(matches, mapping):
    """将fixtureId应用到比赛数据"""
    matched = 0
    for m in matches:
        key = f"{m['home']}_{m['away']}"
        
        if key in mapping.get('mapping', {}):
            entry = mapping['mapping'][key]
            if 'fixtureId' in entry:
                m['fid'] = entry['fixtureId']
                m['fixtureId'] = entry['fixtureId']
                matched += 1
            if 'namitiyuId' in entry:
                m['namitiyuId'] = entry['namitiyuId']
        elif m['id'] in mapping.get('byMatchId', {}):
            entry = mapping['byMatchId'][m['id']]
            if 'fixtureId' in entry:
                m['fid'] = entry['fixtureId']
                m['fixtureId'] = entry['fixtureId']
                matched += 1
            if 'namitiyuId' in entry:
                m['namitiyuId'] = entry['namitiyuId']
    
    print(f"匹配到 {matched} 场比赛的fixtureId")


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
    
    # 1. 从竞彩官网获取所有比赛数据
    print("\n>>> 从竞彩官网获取比赛数据...")
    all_matches = fetch_all_from_sporttery()
    
    if not all_matches:
        print("未获取到比赛数据")
        return
    
    # 2. 从500.com获取fixtureId
    print("\n>>> 从500.com获取动画链接...")
    fixture_map = fetch_fixture_from_500()
    
    # 3. 更新fixture_mapping.json（累积保存）
    print("\n>>> 更新映射关系...")
    mapping = update_fixture_mapping(all_matches, fixture_map)
    
    # 4. 过滤用于显示的比赛
    display_matches = filter_for_display(all_matches)
    
    # 5. 应用fixtureId到比赛数据
    apply_fixture_to_matches(display_matches, mapping)
    
    # 6. 统计
    live_count = len([m for m in display_matches if m['status'] == 'live'])
    finished_count = len([m for m in display_matches if m['status'] == 'finished'])
    upcoming_count = len([m for m in display_matches if m['status'] == 'upcoming'])
    
    print(f"\n>>> 统计:")
    print(f"    总比赛: {len(all_matches)}")
    print(f"    显示比赛: {len(display_matches)} (过去3天已结束 + 未来)")
    print(f"    进行中: {live_count}")
    print(f"    已结束: {finished_count}")
    print(f"    未开始: {upcoming_count}")
    print(f"    有fixtureId: {len([m for m in display_matches if m.get('fixtureId')])}")
    
    # 7. 保存数据
    data = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': display_matches,
        'total': len(display_matches),
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