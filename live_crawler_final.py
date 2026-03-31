#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比分直播数据爬虫 - 竞彩官网版
============================

数据来源:
1. sporttery.cn - 比赛列表、比分、状态（主数据源）
2. 500.com - fixtureId、namitiyuId（用于动画链接）

输出文件:
- live_data.json -> dist/data/, dist/, data/
- fixture_mapping.json -> dist/data/, dist/, data/

匹配规则:
- 使用 matchNum (如"周二003") 作为主键匹配竞彩和500.com数据
- 同时保存 byMatchNum 索引便于快速查找
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl

from path_config import save_json, load_json, get_data_paths, ensure_dir, DATA_DIR, DIST_DATA_DIR

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
    """从500.com获取fixtureId（使用matchNum精确匹配）"""
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
            
            pattern = r'<tr[^>]*data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"[^>]*data-matchdate="([^"]*)"[^>]*data-matchtime="([^"]*)"[^>]*data-matchnum="([^"]*)"[^>]*>'
            for m in re.finditer(pattern, html):
                fixture_id, home, away, match_date, match_time, match_num = m.groups()
                if match_num and match_num != '---':
                    key = match_num
                    fixture_map[key] = {
                        'fixtureId': fixture_id,
                        'home': home,
                        'away': away,
                        'date': match_date,
                        'time': match_time,
                        'matchNum': match_num,
                    }
            
            print(f"从500.com获取 {len(fixture_map)} 个fixtureId (按matchNum)")
            
    except Exception as e:
        print(f"500.com获取fixtureId失败: {e}")
    
    return fixture_map


def fetch_namitiyu_id(fixture_id):
    """从500.com的stat页面获取namitiyuId"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    url = f'https://odds.500.com/fenxi/stat-{fixture_id}.shtml?showAnimation=1'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            pattern = r'tracker\.namitiyu\.com[^"]*id=(\d+)'
            match = re.search(pattern, html)
            if match:
                namitiyu_id = match.group(1)
                print(f"  fixtureId={fixture_id} → namitiyuId={namitiyu_id}")
                return namitiyu_id
            
    except Exception as e:
        print(f"  fixtureId={fixture_id} 获取namitiyuId失败: {e}")
    
    return None


def fetch_all_namitiyu_ids(fixture_map, existing_mapping):
    """批量获取namitiyuId"""
    namitiyu_map = {}
    
    for key, info in fixture_map.items():
        fixture_id = info.get('fixtureId')
        
        if not fixture_id:
            continue
        
        existing_entry = existing_mapping.get('byMatchNum', {}).get(key, {})
        if existing_entry.get('namitiyuId'):
            namitiyu_map[key] = existing_entry['namitiyuId']
            continue
        
        namitiyu_id = fetch_namitiyu_id(fixture_id)
        if namitiyu_id:
            namitiyu_map[key] = namitiyu_id
    
    print(f"获取 {len(namitiyu_map)} 个namitiyuId")
    return namitiyu_map


def update_fixture_mapping(all_matches, fixture_map):
    """更新fixture_mapping.json（累积保存）- 使用matchNum作为主键
    
    输出: dist/data/fixture_mapping.json, dist/fixture_mapping.json, data/fixture_mapping.json
    """
    mapping_data = load_json('fixture_mapping.json') or {'mapping': {}, 'byMatchId': {}, 'byMatchNum': {}}
    
    if 'byMatchNum' not in mapping_data:
        mapping_data['byMatchNum'] = {}
    
    print("\n>>> 获取动画ID (namitiyuId)...")
    namitiyu_map = fetch_all_namitiyu_ids(fixture_map, mapping_data)
    
    analysis_files = []
    try:
        analysis_files = [f for f in os.listdir(DATA_DIR) if f.startswith('analysis_') and f.endswith('.json')]
    except:
        pass
    
    analysis_count = 0
    for af in analysis_files:
        try:
            fid = af.replace('analysis_', '').replace('.json', '')
            af_path = os.path.join(DATA_DIR, af)
            with open(af_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                home = data.get('home', '')
                away = data.get('away', '')
                match_num = data.get('matchNum', '')
                if home and away:
                    name_key = f"{home}_{away}"
                    if name_key not in mapping_data['mapping']:
                        mapping_data['mapping'][name_key] = {
                            'fixtureId': fid,
                            'home': home,
                            'away': away,
                        }
                        analysis_count += 1
                    elif 'fixtureId' not in mapping_data['mapping'][name_key]:
                        mapping_data['mapping'][name_key]['fixtureId'] = fid
                        analysis_count += 1
        except:
            pass
    
    print(f"从 {len(analysis_files)} 个分析文件中提取 {analysis_count} 个fixtureId")
    
    new_count = 0
    
    for m in all_matches:
        match_id = m['id']
        match_num = m['matchNum']
        name_key = f"{m['home']}_{m['away']}"
        
        entry = {
            'matchId': match_id,
            'home': m['home'],
            'away': m['away'],
            'matchNum': match_num,
            'league': m['league'],
            'date': m['date'],
        }
        
        if match_num in mapping_data.get('byMatchNum', {}):
            existing_num_entry = mapping_data['byMatchNum'][match_num]
            if 'fixtureId' in existing_num_entry:
                entry['fixtureId'] = existing_num_entry['fixtureId']
            if 'namitiyuId' in existing_num_entry:
                entry['namitiyuId'] = existing_num_entry['namitiyuId']
        
        if match_num in fixture_map:
            entry['fixtureId'] = fixture_map[match_num]['fixtureId']
            entry['home'] = fixture_map[match_num]['home']
            entry['away'] = fixture_map[match_num]['away']
        
        if match_num in namitiyu_map:
            entry['namitiyuId'] = namitiyu_map[match_num]
        
        if match_num and match_num not in mapping_data.get('byMatchNum', {}):
            new_count += 1
        mapping_data['byMatchNum'][match_num] = entry
        
        if name_key not in mapping_data['mapping']:
            new_count += 1
        mapping_data['mapping'][name_key] = entry
        
        if match_id:
            if match_id not in mapping_data['byMatchId']:
                new_count += 1
            mapping_data['byMatchId'][match_id] = entry
    
    mapping_data['byFixtureId'] = {}
    for key, entry in mapping_data['mapping'].items():
        if 'fixtureId' in entry:
            mapping_data['byFixtureId'][entry['fixtureId']] = {
                'namitiyuId': entry.get('namitiyuId'),
                'home': entry.get('home'),
                'away': entry.get('away'),
                'matchNum': entry.get('matchNum'),
                'matchKey': key
            }
    
    count = save_json(mapping_data, 'fixture_mapping.json')
    
    fixture_count = len([v for v in mapping_data['mapping'].values() if 'fixtureId' in v])
    num_fixture_count = len([v for v in mapping_data['byMatchNum'].values() if 'fixtureId' in v])
    print(f"fixture_mapping: 总计 {len(mapping_data['mapping'])} 条, byMatchNum {len(mapping_data['byMatchNum'])} 条")
    print(f"  有fixtureId: mapping {fixture_count} 条, byMatchNum {num_fixture_count} 条, 新增 {new_count} 条")
    print(f"  已保存到 {count} 个位置")
    
    return mapping_data


def apply_fixture_to_matches(matches, mapping):
    """将fixtureId应用到比赛数据 - 优先使用matchNum匹配"""
    matched = 0
    for m in matches:
        match_num = m.get('matchNum', '')
        
        if match_num and match_num in mapping.get('byMatchNum', {}):
            entry = mapping['byMatchNum'][match_num]
            if 'fixtureId' in entry:
                m['fid'] = entry['fixtureId']
                m['fixtureId'] = entry['fixtureId']
                matched += 1
            if 'namitiyuId' in entry:
                m['namitiyuId'] = entry['namitiyuId']
        else:
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
    """保存数据到所有位置
    
    输出: dist/data/live_data.json, dist/live_data.json, data/live_data.json
    """
    count = save_json(data, 'live_data.json')
    print(f"数据已保存到 {count} 个位置")


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