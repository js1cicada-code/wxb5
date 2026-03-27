#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
篮球比赛分析数据爬虫模块
============================

功能说明：
    从竞彩网和500.com爬取篮球比赛的完整分析数据

数据模块：
    1. 球队排名信息
    2. 近期战绩
    3. 交战历史
    4. 让分/大小分赔率
"""

import json
import os
import re
import time
import requests
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.sporttery.cn/jc/lqszsc/',
}

TIMEOUT = 15

MANUAL_MATCH_MAPPING = {
    # 周三欧篮联比赛
    '周三301': '229706',
    '周三302': '229707', 
    '周三303': '229708',
    '周三304': '229709',
    '周三305': '229710',
}

TEAM_NAME_MAP = {
    '巴斯克尼亚': '巴斯克',
    '贝尔格莱德红星': '贝红星',
    '底特律活塞': '活塞',
    '亚特兰大老鹰': '老鹰',
    '印第安那步行者': '步行者',
    '洛杉矶湖人': '湖人',
    '克利夫兰骑士': '骑士',
    '迈阿密热火': '热火',
    '波士顿凯尔特人': '凯尔特',
    '俄克拉荷马城雷霆': '雷霆',
    '孟菲斯灰熊': '灰熊',
    '圣安东尼奥马刺': '马刺',
    '犹他爵士': '爵士',
    '华盛顿奇才': '奇才',
    '明尼苏达森林狼': '森林狼',
    '休斯敦火箭': '火箭',
    '波特兰开拓者': '开拓者',
    '密尔沃基雄鹿': '雄鹿',
    '金州勇士': '勇士',
    '布鲁克林篮网': '篮网',
    '丹佛掘金': '掘金',
    '达拉斯独行侠': '独行侠',
    '洛杉矶快船': '快船',
    '多伦多猛龙': '猛龙',
}

def fetch_500_match_list():
    """从500.com获取篮球比赛列表"""
    result = {}
    team_mapping = {}
    matchid_mapping = {}
    
    result.update(MANUAL_MATCH_MAPPING)
    
    url = 'https://live.500.com/lq.php'
    
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        }, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        
        match = re.search(r'var matchList\s*=\s*(\[[\s\S]*?\]);', html)
        if match:
            data_str = match.group(1)
            match_list = json.loads(data_str)
            
            for m in match_list:
                if len(m) >= 27:
                    match_id_500 = m[1]
                    match_num_str = m[26]
                    home_team = m[13] if len(m) > 13 else ''
                    away_team = m[14] if len(m) > 14 else ''
                    if match_num_str and match_num_str != '---' and match_id_500:
                        result[match_num_str] = match_id_500
                    if home_team and away_team and match_id_500:
                        team_key = f"{home_team}_{away_team}"
                        team_mapping[team_key] = match_id_500
            
            print(f"500.com live获取到 {len(result)} 场比赛")
        
    except Exception as e:
        print(f"获取500.com live失败: {e}")
    
    return result, team_mapping, matchid_mapping


def search_500_match_id(home, away):
    """通过球队名称搜索500.com比赛ID"""
    home_short = TEAM_NAME_MAP.get(home, home[:2] if len(home) >= 2 else home)
    away_short = TEAM_NAME_MAP.get(away, away[:2] if len(away) >= 2 else away)
    
    cached_matches = getattr(search_500_match_id, 'cache', None)
    if cached_matches is None:
        cached_matches = {}
        id_ranges = [(229700, 229750), (236100, 236200)]
        for id_start, id_end in id_ranges:
            for match_id_500 in range(id_start, id_end):
                try:
                    url = f'https://odds.500.com/lq/shuju.php?id={match_id_500}&r=1'
                    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                    html = resp.content.decode('gb2312', errors='ignore')
                    
                    title_match = re.search(r'<title>([^<]+)</title>', html)
                    if title_match:
                        title = title_match.group(1)
                        teams = re.match(r'([^V]+)VS([^\(]+)', title)
                        if teams:
                            h = teams.group(1).strip()
                            a = teams.group(2).strip()
                            cached_matches[f"{h}_{a}"] = str(match_id_500)
                            cached_matches[h] = str(match_id_500)
                            cached_matches[a] = str(match_id_500)
                except:
                    pass
        search_500_match_id.cache = cached_matches
        print(f"  缓存了 {len(cached_matches)} 个500.com比赛映射")
    
    for key in [home_short, away_short, home, away]:
        if key in cached_matches:
            return cached_matches[key]
    
    return None


def fetch_basketball_matches():
    """获取竞彩篮球比赛列表"""
    url = 'https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        
        if not data.get('success') or not data.get('value'):
            print("获取篮球比赛失败")
            return []
        
        matches = []
        for day_match in data['value'].get('matchInfoList', []):
            for match in day_match.get('subMatchList', []):
                match_info = {
                    'matchId': match.get('matchId', ''),
                    'matchNumStr': match.get('matchNumStr', ''),
                    'league': match.get('leagueAbbName', ''),
                    'home': match.get('homeTeamAllName', '') or match.get('homeTeamAbbName', ''),
                    'away': match.get('awayTeamAllName', '') or match.get('awayTeamAbbName', ''),
                    'date': day_match.get('matchDate', ''),
                    'time': match.get('matchTime', ''),
                    'homeRank': match.get('homeRank', ''),
                    'awayRank': match.get('awayRank', ''),
                }
                
                odds = {}
                
                if match.get('mnl'):
                    odds['sf'] = {
                        'home': match['mnl'].get('h', '-'),
                        'away': match['mnl'].get('a', '-'),
                    }
                
                if match.get('hdc'):
                    odds['rfsf'] = {
                        'handicap': match['hdc'].get('goalLine', ''),
                        'home': match['hdc'].get('h', '-'),
                        'away': match['hdc'].get('a', '-'),
                    }
                
                if match.get('hilo'):
                    odds['dxf'] = {
                        'line': match['hilo'].get('goalLine', ''),
                        'over': match['hilo'].get('h', '-'),
                        'under': match['hilo'].get('l', '-'),
                    }
                
                match_info['odds'] = odds
                matches.append(match_info)
        
        print(f"获取到 {len(matches)} 场篮球比赛")
        return matches
        
    except Exception as e:
        print(f"获取篮球比赛失败: {e}")
        return []


def parse_500_team_stats(html, team_class):
    """解析500.com球队战绩统计"""
    result = {
        'total': None,
        'home': None,
        'away': None,
        'recent10': None
    }
    
    try:
        pattern = rf'<div class="{team_class}">.*?</table>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return result
        
        table_html = match.group(0)
        
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        
        for row in rows:
            if '<strong>总计</strong>' in row:
                result['total'] = parse_stats_row(row)
            elif '<strong>主场</strong>' in row:
                result['home'] = parse_stats_row(row)
            elif '<strong>客场</strong>' in row:
                result['away'] = parse_stats_row(row)
            elif '<strong>近10场</strong>' in row:
                result['recent10'] = parse_stats_row(row)
        
    except Exception as e:
        print(f"解析球队战绩失败: {e}")
    
    return result


def parse_stats_row(row):
    """解析单行战绩数据"""
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    if len(cells) < 9:
        return None
    
    def clean_cell(c):
        c = re.sub(r'<[^>]+>', '', c)
        c = c.replace('&nbsp;', ' ').strip()
        return c
    
    return {
        'games': clean_cell(cells[1]) if len(cells) > 1 else '',
        'wins': clean_cell(cells[2]) if len(cells) > 2 else '',
        'losses': clean_cell(cells[3]) if len(cells) > 3 else '',
        'pointsFor': clean_cell(cells[4]) if len(cells) > 4 else '',
        'pointsAgainst': clean_cell(cells[5]) if len(cells) > 5 else '',
        'pointDiff': clean_cell(cells[6]) if len(cells) > 6 else '',
        'rank': clean_cell(cells[7]) if len(cells) > 7 else '',
        'winRate': clean_cell(cells[8]) if len(cells) > 8 else ''
    }


def parse_500_h2h(html):
    """解析500.com交战历史"""
    result = {
        'summary': '',
        'matches': []
    }
    
    try:
        summary_match = re.search(r'双方近<span[^>]*>(\d+)</span>次交战.*?<em[^>]*>(\d+)胜</em>.*?<em[^>]*>(\d+)负</em>', html, re.DOTALL)
        if summary_match:
            count = summary_match.group(1)
            wins = summary_match.group(2)
            losses = summary_match.group(3)
            result['summary'] = f"近{count}次交战：{wins}胜{losses}负"
        
        tbody_match = re.search(r'<tbody id="vs_target">(.*?)</tbody>', html, re.DOTALL)
        if tbody_match:
            tbody = tbody_match.group(1)
            rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
            
            for row in rows[:10]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 7:
                    def clean(c):
                        c = re.sub(r'<[^>]+>', '', c)
                        return c.replace('&nbsp;', ' ').strip()
                    
                    match_info = {
                        'league': clean(cells[0]),
                        'date': clean(cells[1]),
                        'away': clean(cells[2]),
                        'score': clean(cells[3]),
                        'home': clean(cells[4]),
                        'result': clean(cells[5]),
                        'diff': clean(cells[6])
                    }
                    result['matches'].append(match_info)
        
    except Exception as e:
        print(f"解析交战历史失败: {e}")
    
    return result if result['matches'] or result['summary'] else None


def parse_500_recent_matches(html, team_name, is_home):
    """解析500.com近期战绩"""
    result = {
        'summary': '',
        'matches': []
    }
    
    try:
        # 查找近期战绩部分
        recent_section = re.search(r'近期战绩.*?未来赛事', html, re.DOTALL)
        if not recent_section:
            return None
        
        recent_html = recent_section.group(0)
        
        # 根据主客确定tbody ID
        tbody_id = 'home_num_target' if is_home else 'away_num_target'
        
        # 提取对应球队的表格
        pattern = rf'<tbody id="{tbody_id}">(.*?)</tbody>'
        tbody_match = re.search(pattern, recent_html, re.DOTALL)
        
        if tbody_match:
            tbody = tbody_match.group(1)
            rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
            
            for row in rows[:10]:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 6:
                    def clean(c):
                        c = re.sub(r'<[^>]+>', '', c)
                        return c.replace('&nbsp;', ' ').strip()
                    
                    # 提取比分
                    score_text = clean(cells[3])
                    score_match = re.search(r'(\d+-\d+)', score_text)
                    score = score_match.group(1) if score_match else clean(cells[3])
                    
                    # 判断对手（如果cells[2]有lzhu标签，说明对手是cells[4]）
                    opponent_cell = cells[2] if 'lzhu' not in cells[2] else cells[4]
                    
                    match_info = {
                        'league': clean(cells[0]),
                        'date': clean(cells[1]),
                        'opponent': clean(opponent_cell),
                        'score': score,
                        'result': clean(cells[5])
                    }
                    result['matches'].append(match_info)
            
            # 生成总结
            wins = sum(1 for m in result['matches'] if m['result'] == '胜')
            losses = sum(1 for m in result['matches'] if m['result'] == '负')
            result['summary'] = f"近{len(result['matches'])}场：{wins}胜{losses}负"
        
    except Exception as e:
        print(f"解析近期战绩失败: {e}")
    
    return result if result['matches'] else None


def parse_500_league_ranking(html, home_team, away_team):
    """解析500.com联赛排名"""
    result = {
        'home': None,
        'away': None,
        'standings': []
    }
    
    try:
        # 解析联赛排名表格
        ranking_match = re.search(r'<h2>欧篮联排名</h2>.*?<tbody>(.*?)</tbody>', html, re.DOTALL)
        if ranking_match:
            tbody = ranking_match.group(1)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
            
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 4:
                    def clean(c):
                        c = re.sub(r'<[^>]+>', '', c)
                        return c.replace('&nbsp;', ' ').strip()
                    
                    rank_match = re.search(r'(\d+)', clean(cells[0]))
                    team_match = re.search(r'>([^<]+)</a>', cells[0])
                    
                    if rank_match and team_match:
                        team_name = team_match.group(1)
                        standing = {
                            'rank': rank_match.group(1),
                            'team': team_name,
                            'wins': clean(cells[1]),
                            'losses': clean(cells[2]),
                            'winRate': clean(cells[3])
                        }
                        result['standings'].append(standing)
                        
                        if home_team and home_team in team_name:
                            result['home'] = standing
                        if away_team and away_team in team_name:
                            result['away'] = standing
        
    except Exception as e:
        print(f"解析联赛排名失败: {e}")
    
    return result if result['standings'] else None


def parse_500_handicap_comparison(html):
    """解析500.com双方盘路比较"""
    result = {
        'home': None,
        'away': None
    }
    
    try:
        # 查找盘路比较部分
        section_match = re.search(r'双方盘路比较.*?未来赛事', html, re.DOTALL)
        if not section_match:
            return None
        
        section_html = section_match.group(0)
        
        # 解析两个球队的盘路数据
        for team_class, key in [('team_a', 'away'), ('team_b', 'home')]:
            pattern = rf'<div class="{team_class}">.*?<tbody>(.*?)</tbody>'
            tbody_match = re.search(pattern, section_html, re.DOTALL)
            
            if tbody_match:
                tbody = tbody_match.group(1)
                rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
                
                stats = {}
                for row in rows:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if len(cells) >= 8:
                        def clean(c):
                            c = re.sub(r'<[^>]+>', '', c)
                            return c.replace('&nbsp;', ' ').strip()
                        
                        label = clean(cells[0])
                        if label and '总计' in label:
                            stats['total'] = {
                                'games': clean(cells[1]),
                                'winHandicap': clean(cells[2]),
                                'loseHandicap': clean(cells[3]),
                                'winRate': clean(cells[4]),
                                'bigBall': clean(cells[5]),
                                'smallBall': clean(cells[6]),
                                'bigBallRate': clean(cells[7])
                            }
                        elif label and '主场' in label:
                            stats['home'] = {
                                'games': clean(cells[1]),
                                'winHandicap': clean(cells[2]),
                                'loseHandicap': clean(cells[3]),
                                'winRate': clean(cells[4]),
                                'bigBall': clean(cells[5]),
                                'smallBall': clean(cells[6]),
                                'bigBallRate': clean(cells[7])
                            }
                        elif label and '客场' in label:
                            stats['away'] = {
                                'games': clean(cells[1]),
                                'winHandicap': clean(cells[2]),
                                'loseHandicap': clean(cells[3]),
                                'winRate': clean(cells[4]),
                                'bigBall': clean(cells[5]),
                                'smallBall': clean(cells[6]),
                                'bigBallRate': clean(cells[7])
                            }
                
                if stats:
                    result[key] = stats
        
    except Exception as e:
        print(f"解析盘路比较失败: {e}")
    
    return result if result['home'] or result['away'] else None


def parse_500_future_matches(html):
    """解析500.com未来赛事"""
    result = {
        'home': [],
        'away': []
    }
    
    try:
        # 查找未来赛事部分
        section_match = re.search(r'未来赛事.*?预计阵容', html, re.DOTALL)
        if not section_match:
            return None
        
        section_html = section_match.group(0)
        
        # 解析两个球队的未来赛事
        for tbody_id, key in [('away_future_target', 'away'), ('home_future_target', 'home')]:
            pattern = rf'<tbody id="{tbody_id}">(.*?)</tbody>'
            tbody_match = re.search(pattern, section_html, re.DOTALL)
            
            if tbody_match:
                tbody = tbody_match.group(1)
                rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
                
                for row in rows[:5]:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if len(cells) >= 5:
                        def clean(c):
                            c = re.sub(r'<[^>]+>', '', c)
                            return c.replace('&nbsp;', ' ').strip()
                        
                        match_info = {
                            'league': clean(cells[0]),
                            'date': clean(cells[1]),
                            'homeAway': clean(cells[2]),
                            'opponent': clean(cells[3]),
                            'daysApart': clean(cells[4])
                        }
                        result[key].append(match_info)
        
    except Exception as e:
        print(f"解析未来赛事失败: {e}")
    
    return result if result['home'] or result['away'] else None


def parse_500_ouzhi(html):
    """解析500.com欧赔指数"""
    result = {
        'companies': [],
        'summary': {}
    }
    
    try:
        # 查找欧赔表格
        table_match = re.search(r'<table[^>]*class="oz_table"[^>]*id="datatable">(.*?)</table>', html, re.DOTALL)
        if not table_match:
            return None
        
        table_html = table_match.group(1)
        
        # 找到所有公司行
        all_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        
        # 分离公司数据和统计数据 - 通过class提取tr3行
        summary_rows = re.findall(r'<tr[^>]*class="tr3"[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        
        # 公司数据：排除表头行和统计行
        company_rows = []
        for row in all_rows:
            # 跳过表头
            if 'sorttr' in row or '<th' in row:
                continue
            # 跳过统计行（通过class或关键词）
            if 'class="tr3"' in row or '最高值' in row or '最低值' in row or '平均值' in row:
                continue
            company_rows.append(row)
        
        # 解析公司数据
        i = 0
        while i < len(company_rows):
            row1 = company_rows[i]
            if i + 1 >= len(company_rows):
                break
            row2 = company_rows[i + 1]
            
            # 解析第一行（初盘）
            cells1 = re.findall(r'<td[^>]*>(.*?)</td>', row1, re.DOTALL)
            # 解析第二行（即时）
            cells2 = re.findall(r'<td[^>]*>(.*?)</td>', row2, re.DOTALL)
            
            if len(cells1) >= 8 and len(cells2) >= 5:
                def clean(c):
                    c = re.sub(r'<[^>]+>', '', c)
                    return c.replace('&nbsp;', ' ').strip()
                
                # 提取公司名称
                company_name = clean(cells1[1])
                
                # 提取初盘赔率
                initial_lose = clean(cells1[2])
                initial_win = clean(cells1[3])
                initial_lose_rate = clean(cells1[4])
                initial_win_rate = clean(cells1[5])
                initial_return_rate = clean(cells1[6])
                
                # 提取即时赔率
                instant_lose = clean(cells2[0])
                instant_win = clean(cells2[1])
                instant_lose_rate = clean(cells2[2])
                instant_win_rate = clean(cells2[3])
                instant_return_rate = clean(cells2[4])
                
                # 提取更新时间
                update_time = clean(cells1[7]) if len(cells1) > 7 else ''
                
                company_data = {
                    'company': company_name,
                    'initial': {
                        'lose': initial_lose,
                        'win': initial_win,
                        'loseRate': initial_lose_rate,
                        'winRate': initial_win_rate,
                        'returnRate': initial_return_rate
                    },
                    'instant': {
                        'lose': instant_lose,
                        'win': instant_win,
                        'loseRate': instant_lose_rate,
                        'winRate': instant_win_rate,
                        'returnRate': instant_return_rate
                    },
                    'updateTime': update_time
                }
                
                result['companies'].append(company_data)
            
            i += 2
        
        # 解析统计汇总数据（最高值、最低值、平均值）
        summary_labels = ['最高值', '最低值', '平均值']
        summary_index = 0
        
        for i in range(0, len(summary_rows), 2):
            if summary_index >= 3 or i + 1 >= len(summary_rows):
                break
                
            row1 = summary_rows[i]
            row2 = summary_rows[i + 1]
            
            cells1 = re.findall(r'<td[^>]*>(.*?)</td>', row1, re.DOTALL)
            cells2 = re.findall(r'<td[^>]*>(.*?)</td>', row2, re.DOTALL)
            
            if len(cells1) >= 6 and len(cells2) >= 5:
                def clean(c):
                    c = re.sub(r'<[^>]+>', '', c)
                    return c.replace('&nbsp;', ' ').strip()
                
                # 提取标签（从第一个单元格）
                label_text = clean(cells1[0]) if cells1 else ''
                label = summary_labels[summary_index] if summary_index < len(summary_labels) else ''
                
                # 提取数据（从cells1[1]开始，因为cells1[0]是标签）
                summary_data = {
                    'initial': {
                        'lose': clean(cells1[1]) if len(cells1) > 1 else '',
                        'win': clean(cells1[2]) if len(cells1) > 2 else '',
                        'loseRate': clean(cells1[3]) if len(cells1) > 3 else '',
                        'winRate': clean(cells1[4]) if len(cells1) > 4 else '',
                        'returnRate': clean(cells1[5]) if len(cells1) > 5 else ''
                    },
                    'instant': {
                        'lose': clean(cells2[0]) if len(cells2) > 0 else '',
                        'win': clean(cells2[1]) if len(cells2) > 1 else '',
                        'loseRate': clean(cells2[2]) if len(cells2) > 2 else '',
                        'winRate': clean(cells2[3]) if len(cells2) > 3 else '',
                        'returnRate': clean(cells2[4]) if len(cells2) > 4 else ''
                    }
                }
                
                result['summary'][label] = summary_data
                summary_index += 1
        
    except Exception as e:
        print(f"解析欧赔指数失败: {e}")
    
    return result if result['companies'] else None


def parse_500_rangfen(html):
    """解析500.com让分盘数据"""
    result = {
        'comparison': [],
        'summary': {},
        'changes': []
    }
    
    try:
        # 解析让分盘对比表格
        tbody_match = re.search(r'<tbody id="loop_f">(.*?)</tbody>', html, re.DOTALL)
        if tbody_match:
            tbody = tbody_match.group(1)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
            
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cells) >= 11:
                    def clean(c):
                        c = re.sub(r'<[^>]+>', '', c)
                        return c.replace('&nbsp;', ' ').strip()
                    
                    # 提取数据
                    company = clean(cells[1])
                    
                    # 即时盘
                    instant_guest = clean(cells[2])
                    instant_handicap = clean(cells[3])
                    instant_home = clean(cells[4])
                    instant_time = clean(cells[5])
                    
                    # 初盘
                    initial_guest = clean(cells[6])
                    initial_handicap = clean(cells[7])
                    initial_home = clean(cells[8])
                    initial_time = clean(cells[9])
                    
                    comparison_data = {
                        'company': company,
                        'instant': {
                            'guest': instant_guest,
                            'handicap': instant_handicap,
                            'home': instant_home,
                            'time': instant_time
                        },
                        'initial': {
                            'guest': initial_guest,
                            'handicap': initial_handicap,
                            'home': initial_home,
                            'time': initial_time
                        }
                    }
                    
                    result['comparison'].append(comparison_data)
        
        # 解析最大值和最小值
        max_match = re.search(r'<td colspan="2">最大值</td>.*?<td id="kd_dx_max">([^<]+)</td>.*?<td id="js_dx_max">([^<]+)</td>.*?<td id="zd_dx_max">([^<]+)</td>.*?<td id="kd2_dx_max">([^<]+)</td>.*?<td id="cp_dx_max">([^<]+)</td>.*?<td id="zd2_dx_max">([^<]+)</td>', html, re.DOTALL)
        
        if max_match:
            result['summary']['最大值'] = {
                'instant': {
                    'guest': max_match.group(1),
                    'handicap': max_match.group(2),
                    'home': max_match.group(3)
                },
                'initial': {
                    'guest': max_match.group(4),
                    'handicap': max_match.group(5),
                    'home': max_match.group(6)
                }
            }
        
        min_match = re.search(r'<td colspan="2"[^>]*>最小值</td>.*?<td id="kd_dx_min">([^<]+)</td>.*?<td id="js_dx_min">([^<]+)</td>.*?<td id="zd_dx_min">([^<]+)</td>.*?<td id="kd2_dx_min">([^<]+)</td>.*?<td id="cp_dx_min">([^<]+)</td>.*?<td id="zd2_dx_min">([^<]+)</td>', html, re.DOTALL)
        
        if min_match:
            result['summary']['最小值'] = {
                'instant': {
                    'guest': min_match.group(1),
                    'handicap': min_match.group(2),
                    'home': min_match.group(3)
                },
                'initial': {
                    'guest': min_match.group(4),
                    'handicap': min_match.group(5),
                    'home': min_match.group(6)
                }
            }
        
        # 解析主流公司让分盘变化
        changes_match = re.search(r'<h2>主流公司让分盘变化</h2>.*?<table[^>]*>(.*?)</table>', html, re.DOTALL)
        if changes_match:
            table_html = changes_match.group(1)
            
            # 提取表头（公司名称）
            header_match = re.search(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
            if header_match:
                headers = re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL)
                companies = [re.sub(r'<[^>]+>', '', h).strip() for h in headers[:-1]]  # 排除最后一列"时间"
                
                # 提取数据行
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)[1:]  # 跳过表头
                
                for row in rows[:20]:  # 只取最近20条
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    
                    if len(cells) >= len(companies) + 1:
                        change_data = {
                            'companies': [],
                            'time': ''
                        }
                        
                        for i, company in enumerate(companies):
                            cell = cells[i]
                            # 提取盘口和水位
                            handicap_match = re.search(r'<strong[^>]*>([^<]+)</strong>', cell)
                            odds_match = re.findall(r'<span[^>]*>([^<]+)</span>', cell)
                            
                            if handicap_match:
                                handicap = handicap_match.group(1).strip()
                                guest_odds = odds_match[0] if len(odds_match) > 0 else ''
                                home_odds = odds_match[1] if len(odds_match) > 1 else ''
                                
                                change_data['companies'].append({
                                    'name': company,
                                    'handicap': handicap,
                                    'guestOdds': guest_odds,
                                    'homeOdds': home_odds
                                })
                        
                        # 提取时间
                        time_cell = cells[-1]
                        change_data['time'] = re.sub(r'<[^>]+>', '', time_cell).strip()
                        
                        if change_data['companies']:
                            result['changes'].append(change_data)
        
    except Exception as e:
        print(f"解析让分盘数据失败: {e}")
    
    return result if result['comparison'] else None


def parse_500_zongfen(html):
    """解析500.com总分盘数据"""
    result = {
        'comparison': [],
        'summary': {},
        'changes': []
    }
    
    try:
        # 解析总分盘对比表格
        tbody_match = re.search(r'<tbody id="loop_f">(.*?)</tbody>', html, re.DOTALL)
        if tbody_match:
            tbody = tbody_match.group(1)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody, re.DOTALL)
            
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cells) >= 11:
                    def clean(c):
                        c = re.sub(r'<[^>]+>', '', c)
                        return c.replace('&nbsp;', ' ').strip()
                    
                    company = clean(cells[1])
                    
                    instant_over = clean(cells[2])
                    instant_handicap = clean(cells[3])
                    instant_under = clean(cells[4])
                    
                    initial_over = clean(cells[6])
                    initial_handicap = clean(cells[7])
                    initial_under = clean(cells[8])
                    
                    comparison_data = {
                        'company': company,
                        'instant': {
                            'over': instant_over,
                            'handicap': instant_handicap,
                            'under': instant_under
                        },
                        'initial': {
                            'over': initial_over,
                            'handicap': initial_handicap,
                            'under': initial_under
                        }
                    }
                    
                    result['comparison'].append(comparison_data)
        
        # 解析最大值和最小值
        max_match = re.search(r'<td colspan="2">最大值</td>.*?<td id="kd_dx_max">([^<]+)</td>.*?<td id="js_dx_max">([^<]+)</td>.*?<td id="zd_dx_max">([^<]+)</td>.*?<td id="kd2_dx_max">([^<]+)</td>.*?<td id="cp_dx_max">([^<]+)</td>.*?<td id="zd2_dx_max">([^<]+)</td>', html, re.DOTALL)
        
        if max_match:
            result['summary']['最大值'] = {
                'instant': {
                    'over': max_match.group(1),
                    'handicap': max_match.group(2),
                    'under': max_match.group(3)
                },
                'initial': {
                    'over': max_match.group(4),
                    'handicap': max_match.group(5),
                    'under': max_match.group(6)
                }
            }
        
        min_match = re.search(r'<td colspan="2"[^>]*>最小值</td>.*?<td id="kd_dx_min">([^<]+)</td>.*?<td id="js_dx_min">([^<]+)</td>.*?<td id="zd_dx_min">([^<]+)</td>.*?<td id="kd2_dx_min">([^<]+)</td>.*?<td id="cp_dx_min">([^<]+)</td>.*?<td id="zd2_dx_min">([^<]+)</td>', html, re.DOTALL)
        
        if min_match:
            result['summary']['最小值'] = {
                'instant': {
                    'over': min_match.group(1),
                    'handicap': min_match.group(2),
                    'under': min_match.group(3)
                },
                'initial': {
                    'over': min_match.group(4),
                    'handicap': min_match.group(5),
                    'under': min_match.group(6)
                }
            }
        
        # 解析主流公司总分盘变化
        changes_match = re.search(r'<h2>主流公司总分盘变化</h2>.*?<table[^>]*>(.*?)</table>', html, re.DOTALL)
        if changes_match:
            table_html = changes_match.group(1)
            
            # 提取表头（公司名称）
            header_match = re.search(r'<tr>(.*?)</tr>', table_html, re.DOTALL)
            if header_match:
                headers = re.findall(r'<th[^>]*>(.*?)</th>', header_match.group(1), re.DOTALL)
                companies = [re.sub(r'<[^>]+>', '', h).strip() for h in headers[:-1]]
                
                # 提取数据行
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)[1:]
                
                for row in rows[:20]:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    
                    if len(cells) >= len(companies) + 1:
                        change_data = {
                            'companies': [],
                            'time': ''
                        }
                        
                        for i, company in enumerate(companies):
                            cell = cells[i]
                            handicap_match = re.search(r'<strong[^>]*>([^<]+)</strong>', cell)
                            
                            if handicap_match:
                                handicap = handicap_match.group(1).strip()
                                
                                # 提取所有span
                                spans = re.findall(r'<span[^>]*>([^<]+)</span>', cell)
                                
                                # 提取颜色信息
                                over_color_match = re.search(r'<span[^>]*class="([^"]*)"[^>]*>' + re.escape(spans[0] if spans else ''), cell)
                                under_color_match = re.search(r'<span[^>]*class="([^"]*)"[^>]*>' + re.escape(spans[1] if len(spans) > 1 else ''), cell)
                                
                                over_color = ''
                                under_color = ''
                                
                                # 检查第一个span的颜色
                                if 'green' in cell[cell.find('<span'):cell.find('>')+50 if spans else 0]:
                                    over_color = 'loss'
                                elif 'ying' in cell[cell.find('<span'):cell.find('>')+50 if spans else 0]:
                                    over_color = 'win'
                                
                                # 检查第二个span的颜色
                                if len(spans) > 1:
                                    second_span_pos = cell.find('</span>') + 7
                                    if 'green' in cell[second_span_pos:second_span_pos+100]:
                                        under_color = 'loss'
                                    elif 'ying' in cell[second_span_pos:second_span_pos+100]:
                                        under_color = 'win'
                                
                                change_data['companies'].append({
                                    'name': company,
                                    'handicap': handicap,
                                    'overOdds': spans[0] if len(spans) > 0 else '',
                                    'overColor': over_color,
                                    'underOdds': spans[1] if len(spans) > 1 else '',
                                    'underColor': under_color
                                })
                        
                        time_cell = cells[-1]
                        change_data['time'] = re.sub(r'<[^>]+>', '', time_cell).strip()
                        
                        if change_data['companies']:
                            result['changes'].append(change_data)
        
    except Exception as e:
        print(f"解析总分盘数据失败: {e}")
    
    return result if result['comparison'] else None


def fetch_500_basketball_analysis(match_id_500, result):
    """从500.com获取篮球比赛分析数据"""
    url = f'https://odds.500.com/lq/shuju.php?id={match_id_500}&r=1'
    
    try:
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        }, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        
        result['homeStats'] = parse_500_team_stats(html, 'team_a')
        result['awayStats'] = parse_500_team_stats(html, 'team_b')
        result['h2h'] = parse_500_h2h(html)
        
        result['leagueRanking'] = parse_500_league_ranking(html, result.get('home'), result.get('away'))
        result['homeRecent'] = parse_500_recent_matches(html, result.get('home'), is_home=True)
        result['awayRecent'] = parse_500_recent_matches(html, result.get('away'), is_home=False)
        result['handicapComparison'] = parse_500_handicap_comparison(html)
        result['futureMatches'] = parse_500_future_matches(html)
        
        home_win_rate = result.get('homeStats', {}).get('total', {}).get('winRate', '-') if result.get('homeStats') else '-'
        away_win_rate = result.get('awayStats', {}).get('total', {}).get('winRate', '-') if result.get('awayStats') else '-'
        print(f"  500.com数据: 主队战绩={home_win_rate}, 客队战绩={away_win_rate}")
        
    except Exception as e:
        print(f"获取500.com分析数据失败: {e}")
    
    # 获取欧赔数据
    ouzhi_url = f'https://odds.500.com/lq/ouzhi.php?id={match_id_500}'
    try:
        resp = requests.get(ouzhi_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        }, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        result['ouzhi'] = parse_500_ouzhi(html)
        if result['ouzhi'] and result['ouzhi']['companies']:
            print(f"  欧赔数据: {len(result['ouzhi']['companies'])}家公司")
    except Exception as e:
        print(f"获取欧赔数据失败: {e}")
    
    # 获取让分盘数据
    rangfen_url = f'https://odds.500.com/lq/rangfen.php?id={match_id_500}'
    try:
        resp = requests.get(rangfen_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        }, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        result['rangfen'] = parse_500_rangfen(html)
        if result['rangfen'] and result['rangfen']['comparison']:
            print(f"  让分盘数据: {len(result['rangfen']['comparison'])}家公司")
    except Exception as e:
        print(f"获取让分盘数据失败: {e}")
    
    # 获取总分盘数据
    zongfen_url = f'https://odds.500.com/lq/zongfen.php?id={match_id_500}'
    try:
        resp = requests.get(zongfen_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36',
        }, timeout=TIMEOUT)
        html = resp.content.decode('gb2312', errors='ignore')
        result['zongfen'] = parse_500_zongfen(html)
        if result['zongfen'] and result['zongfen']['comparison']:
            print(f"  总分盘数据: {len(result['zongfen']['comparison'])}家公司")
    except Exception as e:
        print(f"获取总分盘数据失败: {e}")


def fetch_basketball_analysis(match_id, match_num_str=None):
    """获取篮球比赛完整分析数据"""
    result = {
        'matchId': match_id,
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'home': '',
        'away': '',
        'league': '',
        'homeRank': '',
        'awayRank': '',
        'homeStats': None,
        'awayStats': None,
        'odds': {},
        'h2h': None,
        'homeRecent': None,
        'awayRecent': None,
    }
    
    url = f'https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        data = resp.json()
        
        if data.get('success') and data.get('value'):
            for day_match in data['value'].get('matchInfoList', []):
                for match in day_match.get('subMatchList', []):
                    if str(match.get('matchId')) == str(match_id):
                        result['home'] = match.get('homeTeamAllName', '') or match.get('homeTeamAbbName', '')
                        result['away'] = match.get('awayTeamAllName', '') or match.get('awayTeamAbbName', '')
                        result['league'] = match.get('leagueAbbName', '')
                        result['homeRank'] = match.get('homeRank', '')
                        result['awayRank'] = match.get('awayRank', '')
                        match_num_str = match.get('matchNumStr', '')
                        
                        odds = {}
                        
                        if match.get('mnl'):
                            odds['sf'] = {
                                'home': match['mnl'].get('h', '-'),
                                'away': match['mnl'].get('a', '-'),
                            }
                        
                        if match.get('hdc'):
                            odds['rfsf'] = {
                                'handicap': match['hdc'].get('goalLine', ''),
                                'home': match['hdc'].get('h', '-'),
                                'away': match['hdc'].get('a', '-'),
                            }
                        
                        if match.get('hilo'):
                            odds['dxf'] = {
                                'line': match['hilo'].get('goalLine', ''),
                                'over': match['hilo'].get('h', '-'),
                                'under': match['hilo'].get('l', '-'),
                            }
                        
                        result['odds'] = odds
                        break
        
    except Exception as e:
        print(f"获取篮球分析失败: {e}")
    
    return result


def save_basketball_matches(matches):
    """保存篮球比赛列表到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(matches),
        'matches': matches
    }
    
    paths = [
        os.path.join(base_dir, 'dist', 'basketball_matches.json'),
        os.path.join(base_dir, 'dist', 'data', 'basketball_matches.json'),
        os.path.join(base_dir, 'data', 'basketball_matches.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"篮球比赛列表已保存到 {len(paths)} 个位置")


def save_basketball_analysis(match_id, data):
    """保存篮球分析数据到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', f'basketball_analysis_{match_id}.json'),
        os.path.join(base_dir, 'dist', 'data', f'basketball_analysis_{match_id}.json'),
        os.path.join(base_dir, 'data', f'basketball_analysis_{match_id}.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return paths[0]


def fetch_all_basketball_analysis(limit=None):
    """批量获取篮球比赛分析"""
    matches = fetch_basketball_matches()
    
    if not matches:
        return
    
    save_basketball_matches(matches)
    
    match_list_500, team_mapping_500, matchid_mapping_500 = fetch_500_match_list()
    
    print(f"\n开始爬取篮球分析...")
    count = 0
    
    for match in matches:
        if limit is not None and count >= limit:
            break
        
        match_id = match['matchId']
        match_num_str = match.get('matchNumStr', '')
        home = match.get('home', '')
        away = match.get('away', '')
        
        print(f"\n[{count+1}] {home} vs {away} ({match_num_str})")
        
        data = fetch_basketball_analysis(match_id, match_num_str)
        
        match_id_500 = match_list_500.get(match_num_str) or matchid_mapping_500.get(str(match_id))
        
        if not match_id_500:
            home_keywords = [h for h in home.replace('(', ' ').replace(')', ' ').split() if len(h) >= 2]
            away_keywords = [a for a in away.replace('(', ' ').replace(')', ' ').split() if len(a) >= 2]
            for key, mid in team_mapping_500.items():
                key_parts = key.split('_')
                if len(key_parts) >= 2:
                    for kw in home_keywords + away_keywords:
                        if kw in key:
                            match_id_500 = mid
                            break
                if match_id_500:
                    break
        
        if not match_id_500:
            match_id_500 = search_500_match_id(home, away)
            if match_id_500:
                print(f"  搜索到500.com ID: {match_id_500}")
        
        if match_id_500:
            fetch_500_basketball_analysis(match_id_500, data)
        else:
            print(f"  未找到500.com比赛ID")
        
        filepath = save_basketball_analysis(match_id, data)
        print(f"  已保存: {filepath}")
        count += 1
        
        time.sleep(0.3)
    
    print(f"\n完成! 共 {count} 场")


if __name__ == '__main__':
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    fetch_all_basketball_analysis(limit)