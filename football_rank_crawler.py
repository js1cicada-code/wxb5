#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
足球排名数据补充爬虫
从500.com获取竞彩官方API中没有的排名数据
"""

import json
import os
import re
import requests
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
}

TIMEOUT = 15


def fetch_match_list_from_500():
    """从500.com获取竞彩足球比赛列表"""
    url = 'https://trade.500.com/jczq/'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        
        rows = re.findall(
            r'<tr[^>]*data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"[^>]*data-matchnum="([^"]*)"[^>]*>',
            html
        )
        
        matches = []
        for row in rows:
            matches.append({
                'fixtureId': row[0],
                'home': row[1],
                'away': row[2],
                'matchNum': row[3]
            })
        
        print(f"从500.com获取到 {len(matches)} 场比赛")
        return matches
        
    except Exception as e:
        print(f"获取500.com比赛列表失败: {e}")
        return []


def fetch_ranking_from_500(fixture_id):
    """从500.com分析页面获取排名"""
    url = f'https://odds.500.com/fenxi/shuju-{fixture_id}'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        
        home_rank = None
        away_rank = None
        
        # 方法1: 从赛前联赛积分排名表格获取
        pos = html.find('赛前联赛积分排名')
        if pos > 0:
            section = html[pos:pos+5000]
            
            # 找team_a区域
            team_a_pos = section.find('team_a')
            if team_a_pos > 0:
                team_a_section = section[team_a_pos:team_a_pos+2000]
                # 找tbody
                tbody = re.search(r'<tbody>(.*?)</tbody>', team_a_section, re.DOTALL)
                if tbody:
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
                    for row in rows:
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                        if cells:
                            # 检查是否是总成绩行
                            text = re.sub(r'<[^>]+>', '', cells[0])
                            if '总成绩' in text and len(cells) >= 10:
                                # 排名在最后一列
                                rank_text = re.sub(r'<[^>]+>', '', cells[-1])
                                rank_match = re.search(r'(\d+)', rank_text)
                                if rank_match:
                                    home_rank = rank_match.group(1)
                                    break
            
            # 找team_b区域
            team_b_pos = section.find('team_b')
            if team_b_pos > 0:
                team_b_section = section[team_b_pos:team_b_pos+2000]
                tbody = re.search(r'<tbody>(.*?)</tbody>', team_b_section, re.DOTALL)
                if tbody:
                    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
                    for row in rows:
                        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                        if cells:
                            text = re.sub(r'<[^>]+>', '', cells[0])
                            if '总成绩' in text and len(cells) >= 10:
                                rank_text = re.sub(r'<[^>]+>', '', cells[-1])
                                rank_match = re.search(r'(\d+)', rank_text)
                                if rank_match:
                                    away_rank = rank_match.group(1)
                                    break
        
        # 方法2: 从球队名称旁的括号提取
        if not home_rank:
            match = re.search(r'team_name[^>]*>[^<]*<span>\[([^\]]+)\]', html)
            if match:
                # 检查是否包含数字（可能是排名）
                content = match.group(1)
                rank_match = re.search(r'(\d+)', content)
                if rank_match and len(content) < 10:
                    home_rank = rank_match.group(1)
        
        return home_rank, away_rank
        
    except Exception as e:
        return None, None


def fetch_all_rankings():
    """获取所有比赛的排名数据"""
    matches = fetch_match_list_from_500()
    
    if not matches:
        print("未获取到比赛数据")
        return {}
    
    rankings = {}
    success_count = 0
    
    for match in matches:
        fixture_id = match['fixtureId']
        match_num = match['matchNum']
        home = match['home']
        away = match['away']
        
        home_rank, away_rank = fetch_ranking_from_500(fixture_id)
        
        if home_rank or away_rank:
            rankings[match_num] = {
                'fixtureId': fixture_id,
                'home': home,
                'away': away,
                'homeRank': home_rank or '',
                'awayRank': away_rank or ''
            }
            success_count += 1
            print(f"  {match_num}: {home}[{home_rank or '-'}] vs {away}[{away_rank or '-'}]")
        else:
            # 即使没有排名也记录，表示已处理
            rankings[match_num] = {
                'fixtureId': fixture_id,
                'home': home,
                'away': away,
                'homeRank': '',
                'awayRank': ''
            }
    
    print(f"\n成功获取 {success_count}/{len(matches)} 场比赛的排名数据")
    return rankings


def save_rankings(rankings):
    """保存排名数据"""
    if not os.path.exists(DIST_DIR):
        os.makedirs(DIST_DIR)
    
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(rankings),
        'rankings': rankings
    }
    
    filepath = os.path.join(DIST_DIR, 'football_rankings.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"排名数据已保存: {filepath}")


def main():
    print("=" * 60)
    print("足球排名数据补充爬虫")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    rankings = fetch_all_rankings()
    
    if rankings:
        save_rankings(rankings)
    else:
        print("未获取到排名数据")


if __name__ == '__main__':
    main()