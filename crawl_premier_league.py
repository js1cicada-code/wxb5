#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
球探体育数据爬虫 - 从 zq.titan007.com 获取联赛数据

【重要】请求头说明：
====================
必须携带 Referer 请求头，否则会被网站WAF（Web应用防火墙）阻止！
- 不带 Referer: 返回19字节错误页 "您的行为已被WAF系统记录"
- 带 Referer: 正常返回JSON数据

headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Referer': 'https://zq.titan007.com/cn/League/{league_id}.html'  # 必须带！
}

【重要】URL格式说明：
====================
不同联赛/杯赛使用不同的URL格式：

1. 欧洲联赛（英超、西甲、德甲、意甲、法甲）：
   - 赛季格式: 2024-2025
   - URL: https://zq.titan007.com/jsData/matchResult/2024-2025/s36.js
   - 文件名: s{league_id}.js

2. 亚洲联赛（中超、日职联、韩K联、澳超）：
   - 赛季格式: 2024（单年）
   - URL: https://zq.titan007.com/jsData/matchResult/2024/s60_2187.js
   - 文件名: s{league_id}_{sub_league_id}.js
   - 需要先获取 SubSclassID（子联赛ID），每个赛季可能不同

3. 杯赛（欧冠、欧罗巴、亚冠精英）：
   - 赛季格式: 2024-2025
   - URL: https://zq.titan007.com/jsData/matchResult/2024-2025/c103.js
   - 文件名: c{league_id}.js
   - 数据格式: var arrCup 而非 var arrLeague

【数据结构说明】：
==================
- var arrTeam: 球队列表
- var arrLeague / var arrCup: 联赛/杯赛信息
- var totalScore: 总积分榜
- var homeScore: 主场积分榜
- var guestScore: 客场积分榜
- var halfScore: 半场积分榜
- jh["R_1"]: 第1轮比赛数据
- jh["G_xxx"]: 杯赛分组数据

作者: opencode
创建时间: 2026-03-30
"""

import json
import os
import re
import requests
from datetime import datetime

OUTPUT_DIR = "data/league"

# ============================================================================
# 【关键】请求头配置 - Referer 是必须的！
# ============================================================================
def get_headers(league_id):
    """
    获取请求头
    
    【重要】Referer 必须设置，否则会被WAF阻止！
    WAF会检查请求来源，没有Referer的请求会被认为是爬虫而拒绝。
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': f'https://zq.titan007.com/cn/League/{league_id}.html',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

def fetch_data(league_id=36, season="2025-2026"):
    """获取联赛数据"""
    season_url = f"https://zq.titan007.com/jsData/LeagueSeason/sea{league_id}.js"
    match_url = f"https://zq.titan007.com/jsData/matchResult/{season}/s{league_id}.js"
    
    headers = get_headers(league_id)
    
    print(f"获取赛季数据: {season_url}")
    season_resp = requests.get(season_url, headers=headers, timeout=30)
    season_resp.encoding = 'utf-8'
    
    print(f"获取比赛数据: {match_url}")
    match_resp = requests.get(match_url, headers=headers, timeout=30)
    match_resp.encoding = 'utf-8'
    
    return season_resp.text, match_resp.text

def parse_season_data(js_content):
    """解析赛季数据"""
    match = re.search(r"var arrSeason\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        return eval(match.group(1))
    return []

def parse_team_data(js_content):
    """解析球队数据"""
    teams = {}
    match = re.search(r"var arrTeam\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for team in arr:
            if len(team) >= 5:
                teams[team[0]] = {
                    "id": team[0],
                    "name": team[1],
                    "name_tw": team[2],
                    "name_en": team[3],
                    "logo": f"https://zq.titan007.com/{team[5]}" if len(team) > 5 else ""
                }
    return teams

def parse_league_info(js_content):
    """解析联赛信息"""
    info = {}
    
    # League format
    match = re.search(r"var arrLeague\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        if len(arr) >= 13:
            info = {
                "id": arr[0],
                "name": arr[1],
                "name_tw": arr[2],
                "name_en": arr[3],
                "current_season": arr[4],
                "total_rounds": arr[7],
                "current_round": arr[8],
                "short_name": arr[9],
                "rules": arr[12] if len(arr) > 12 else ""
            }
    
    # Cup format
    if not info:
        match = re.search(r"var arrCup\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
        if match:
            arr = eval(match.group(1))
            if len(arr) >= 13:
                info = {
                    "id": arr[0],
                    "name": arr[1],
                    "name_tw": arr[2],
                    "name_en": arr[3],
                    "short_name": arr[4] if len(arr) > 4 else "",
                    "current_season": arr[7] if len(arr) > 7 else "",
                    "rules": arr[11] if len(arr) > 11 else ""
                }
    
    return info

def parse_standings(js_content, teams):
    """解析积分榜数据"""
    standings = {
        "total": [],
        "home": [],
        "away": [],
        "half": []
    }
    
    # 总积分榜
    match = re.search(r"var totalScore\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for row in arr:
            if len(row) >= 15:
                team_id = row[2]
                team = teams.get(team_id, {})
                won = row[5]
                draw = row[6]
                lost = row[7]
                points = won * 3 + draw
                standings["total"].append({
                    "team_id": team_id,
                    "team_name": team.get("name", str(team_id)),
                    "played": row[4],
                    "won": won,
                    "draw": draw,
                    "lost": lost,
                    "goals_for": row[8],
                    "goals_against": row[9],
                    "goal_diff": row[10],
                    "win_rate": row[11],
                    "draw_rate": row[12],
                    "lost_rate": row[13],
                    "avg_goals_for": row[14],
                    "avg_goals_against": row[15] if len(row) > 15 else 0,
                    "points": points
                })
        
        # 按积分排序并添加排名
        standings["total"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["total"]):
            team["rank"] = i + 1
            team["qualify"] = get_qualify_info(i + 1, i + 1)
    
    # 主场积分榜
    match = re.search(r"var homeScore\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for row in arr:
            if len(row) >= 12:
                team_id = row[1]
                team = teams.get(team_id, {})
                won = row[3]
                draw = row[4]
                points = won * 3 + draw
                standings["home"].append({
                    "team_id": team_id,
                    "team_name": team.get("name", str(team_id)),
                    "played": row[2],
                    "won": won,
                    "draw": draw,
                    "lost": row[5],
                    "goals_for": row[6],
                    "goals_against": row[7],
                    "goal_diff": row[8],
                    "points": points
                })
        # 按积分排序并添加排名
        standings["home"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["home"]):
            team["rank"] = i + 1
    
    # 客场积分榜
    match = re.search(r"var guestScore\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for row in arr:
            if len(row) >= 12:
                team_id = row[1]
                team = teams.get(team_id, {})
                won = row[3]
                draw = row[4]
                points = won * 3 + draw
                standings["away"].append({
                    "team_id": team_id,
                    "team_name": team.get("name", str(team_id)),
                    "played": row[2],
                    "won": won,
                    "draw": draw,
                    "lost": row[5],
                    "goals_for": row[6],
                    "goals_against": row[7],
                    "goal_diff": row[8],
                    "points": points
                })
        # 按积分排序并添加排名
        standings["away"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["away"]):
            team["rank"] = i + 1
    
    # 半场积分榜
    match = re.search(r"var halfScore\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for row in arr:
            if len(row) >= 12:
                team_id = row[1]
                team = teams.get(team_id, {})
                won = row[3]
                draw = row[4]
                points = won * 3 + draw
                standings["half"].append({
                    "team_id": team_id,
                    "team_name": team.get("name", str(team_id)),
                    "played": row[2],
                    "won": won,
                    "draw": draw,
                    "lost": row[5],
                    "goals_for": row[6],
                    "goals_against": row[7],
                    "goal_diff": row[8],
                    "points": points
                })
        # 按积分排序并添加排名
        standings["half"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["half"]):
            team["rank"] = i + 1
    
    return standings

def get_qualify_info(rank_change, rank):
    """获取欧战/降级资格信息"""
    if rank <= 4:
        return {"type": "cl", "text": "欧冠杯小组赛资格"}
    elif rank == 5:
        return {"type": "el", "text": "欧罗巴联赛杯小组赛"}
    elif rank >= 18:
        return {"type": "relegation", "text": "降级"}
    return None

def parse_matches(js_content, teams):
    """
    解析比赛数据
    
    数据格式说明：
    
    1. 联赛格式: jh["R_1"] = [[比赛1], [比赛2], ...]
       - R_1 表示第1轮
       - 每场比赛数据格式: [match_id, league_id, status, date, home_id, away_id, score, half_score, ...]
    
    2. 杯赛格式: jh["G25164"] = [[比赛1], [比赛2], ...]
       - G25164 表示分组编号
       - 数据结构与联赛相同
    
    【重要】JS数组中的空值处理：
    原始数据中可能有连续逗号（如 ,,）表示空值
    需要先用正则替换为 None，否则 eval() 会报错
    """
    matches = []
    
    # League format: jh["R_x"] = [...]
    pattern = r'jh\["R_(\d+)"\]\s*=\s*(\[.*?\]);'
    for match in re.finditer(pattern, js_content, re.DOTALL):
        round_num = int(match.group(1))
        try:
            js_array = match.group(2)
            # 【重要】处理空值：,, -> ,None,
            js_array = re.sub(r',,', ',None,', js_array)
            js_array = re.sub(r',,', ',None,', js_array)
            js_array = re.sub(r'\[,', '[None,', js_array)
            js_array = re.sub(r',\]', ',None]', js_array)
            
            arr = eval(js_array)
            for m in arr:
                if len(m) >= 14:
                    home_id = m[4]
                    away_id = m[5]
                    home_team = teams.get(home_id, {})
                    away_team = teams.get(away_id, {})
                    
                    matches.append({
                        "round": round_num,
                        "match_id": m[0],
                        "date": m[3],
                        "home_id": home_id,
                        "home_name": home_team.get("name", str(home_id)),
                        "away_id": away_id,
                        "away_name": away_team.get("name", str(away_id)),
                        "score": m[6] if m[6] else '-',
                        "half_score": m[7] if m[7] else '-',
                        "status": m[2],
                        "handicap": m[10] if m[10] else 0,
                        "handicap_water": m[11] if m[11] else 0,
                        "total_goals": m[12] if m[12] else '-',
                        "total_goals_water": m[13] if m[13] else '-'
                    })
        except Exception as e:
            print(f"  解析第{round_num}轮比赛数据失败: {e}")
            continue
    
    # Cup format: jh["Gxxxxx"] = [...]
    cup_pattern = r'jh\["G([^"]+)"\]\s*=\s*(\[.*?\]);'
    for match in re.finditer(cup_pattern, js_content, re.DOTALL):
        group_key = match.group(1)
        try:
            js_array = match.group(2)
            js_array = re.sub(r',,', ',None,', js_array)
            js_array = re.sub(r',,', ',None,', js_array)
            js_array = re.sub(r'\[,', '[None,', js_array)
            js_array = re.sub(r',\]', ',None]', js_array)
            
            arr = eval(js_array)
            for m in arr:
                if len(m) >= 14:
                    home_id = m[4]
                    away_id = m[5]
                    home_team = teams.get(home_id, {})
                    away_team = teams.get(away_id, {})
                    
                    matches.append({
                        "round": group_key,
                        "match_id": m[0],
                        "date": m[3],
                        "home_id": home_id,
                        "home_name": home_team.get("name", str(home_id)),
                        "away_id": away_id,
                        "away_name": away_team.get("name", str(away_id)),
                        "score": m[6] if m[6] else '-',
                        "half_score": m[7] if m[7] else '-',
                        "status": m[2],
                        "handicap": m[10] if m[10] else 0,
                        "handicap_water": m[11] if m[11] else 0,
                        "total_goals": m[12] if m[12] else '-',
                        "total_goals_water": m[13] if m[13] else '-'
                    })
        except Exception as e:
            continue
    
    return sorted(matches, key=lambda x: (str(x.get("round", "")), x.get("date", "")))

def calculate_handicap_standings(matches, teams):
    """
    计算让球积分榜
    
    让球盘口说明：
    - 正数：主队让球（主队强），如 +0.5 表示主队让半球
    - 负数：主队受让（主队弱），如 -0.5 表示主队受让半球
    - 0：平手盘
    
    计算方法：
    调整后主队进球 = 实际主队进球 - 盘口
    
    例1：主队1-0客队，盘口+0.5（主让半球）
         调整后 = 1 - 0.5 = 0.5 > 0，主队让球胜
    
    例2：主队1-1客队，盘口-0.5（主受让半球）
         调整后 = 1 - (-0.5) = 1.5 > 1，主队让球胜
    
    例3：主队1-2客队，盘口+0.5（主让半球）
         调整后 = 1 - 0.5 = 0.5 < 2，主队让球负
    """
    team_stats = {}
    
    for team_id in teams:
        team_stats[team_id] = {
            "team_id": team_id,
            "team_name": teams[team_id]["name"],
            "played": 0,
            "won": 0,
            "draw": 0,
            "lost": 0,
            "win_pct": 0,
            "draw_pct": 0,
            "lost_pct": 0
        }
    
    for match in matches:
        if match["score"] == '-' or not match["score"]:
            continue
        
        home_id = match["home_id"]
        away_id = match["away_id"]
        handicap = match["handicap"]
        
        if home_id not in team_stats or away_id not in team_stats:
            continue
        
        if handicap is None or handicap == 0:
            continue
        
        try:
            score_parts = match["score"].split('-')
            home_goals = int(score_parts[0])
            away_goals = int(score_parts[1])
        except:
            continue
        
        # 【关键】让球计算：主队进球 - 盘口
        adjusted_home_goals = home_goals - handicap
        adjusted_away_goals = away_goals
        
        if adjusted_home_goals > adjusted_away_goals:
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["won"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["lost"] += 1
        elif adjusted_home_goals < adjusted_away_goals:
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["lost"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["won"] += 1
        else:
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["draw"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["draw"] += 1
    
    # 计算百分比并排名
    standings = []
    for team_id, stats in team_stats.items():
        if stats["played"] > 0:
            stats["win_pct"] = round(stats["won"] / stats["played"] * 100, 1)
            stats["draw_pct"] = round(stats["draw"] / stats["played"] * 100, 1)
            stats["lost_pct"] = round(stats["lost"] / stats["played"] * 100, 1)
        standings.append(stats)
    
    # 按赢率排序
    standings.sort(key=lambda x: (-x["win_pct"], -x["won"], x["team_name"]))
    
    # 添加排名
    for i, team in enumerate(standings):
        team["rank"] = i + 1
    
    return standings

def calculate_total_goals_standings(matches, teams):
    """计算大小球积分榜"""
    team_stats = {}
    
    for team_id in teams:
        team_stats[team_id] = {
            "team_id": team_id,
            "team_name": teams[team_id]["name"],
            "played": 0,
            "big": 0,
            "draw": 0,
            "small": 0,
            "big_pct": 0,
            "draw_pct": 0,
            "small_pct": 0
        }
    
    for match in matches:
        if match["score"] == '-' or not match["score"]:
            continue
        
        home_id = match["home_id"]
        away_id = match["away_id"]
        total_goals_line = match.get("total_goals")
        
        if home_id not in team_stats or away_id not in team_stats:
            continue
        
        # 跳过没有大小球盘口的比赛
        if total_goals_line is None or total_goals_line == '' or total_goals_line == '-':
            continue
        
        try:
            score_parts = match["score"].split('-')
            home_goals = int(score_parts[0])
            away_goals = int(score_parts[1])
            total_goals = home_goals + away_goals
            
            # 解析大小球盘口，如 "2.5", "2/2.5", "3"
            line = parse_total_goals_line(total_goals_line)
            if line is None:
                continue
        except:
            continue
        
        # 判断大小球结果
        # 处理走盘情况（盘口是整数且总进球等于盘口）
        if total_goals > line:
            # 大球
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["big"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["big"] += 1
        elif total_goals < line:
            # 小球
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["small"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["small"] += 1
        else:
            # 走水（总进球等于盘口，仅当盘口为整数时可能）
            team_stats[home_id]["played"] += 1
            team_stats[home_id]["draw"] += 1
            team_stats[away_id]["played"] += 1
            team_stats[away_id]["draw"] += 1
    
    # 计算百分比并排名
    standings = []
    for team_id, stats in team_stats.items():
        if stats["played"] > 0:
            stats["big_pct"] = round(stats["big"] / stats["played"] * 100, 1)
            stats["draw_pct"] = round(stats["draw"] / stats["played"] * 100, 1)
            stats["small_pct"] = round(stats["small"] / stats["played"] * 100, 1)
        standings.append(stats)
    
    # 按大球率排序
    standings.sort(key=lambda x: (-x["big_pct"], -x["big"], x["team_name"]))
    
    # 添加排名
    for i, team in enumerate(standings):
        team["rank"] = i + 1
    
    return standings

def parse_total_goals_line(line_str):
    """解析大小球盘口字符串，返回浮点数"""
    if not line_str or line_str == '':
        return None
    
    try:
        # 处理 "2.5", "3", "2/2.5" 等格式
        if '/' in line_str:
            # "2/2.5" 取较小值
            parts = line_str.split('/')
            return float(parts[0])
        else:
            return float(line_str)
    except:
        return None

def calculate_win_draw_lose_standings(standings_data, matches=None, teams=None):
    """
    计算胜平负积分榜（按胜率排序）
    
    参数:
        standings_data: 积分榜数据（联赛）
        matches: 比赛数据（杯赛使用）
        teams: 球队数据（杯赛使用）
    
    对于联赛：直接从 standings_data 计算
    对于杯赛：从 matches 数据计算（因为没有积分榜）
    """
    result = []
    
    # 如果有积分榜数据，直接使用
    if standings_data:
        for team in standings_data:
            played = team.get('played', 0)
            won = team.get('won', 0)
            draw = team.get('draw', 0)
            lost = team.get('lost', 0)
            
            win_pct = round(won / played * 100, 1) if played > 0 else 0
            draw_pct = round(draw / played * 100, 1) if played > 0 else 0
            lost_pct = round(lost / played * 100, 1) if played > 0 else 0
            
            result.append({
                'team_id': team.get('team_id'),
                'team_name': team.get('team_name'),
                'played': played,
                'won': won,
                'draw': draw,
                'lost': lost,
                'win_pct': win_pct,
                'draw_pct': draw_pct,
                'lost_pct': lost_pct
            })
    
    # 如果没有积分榜但有比赛数据，从比赛计算（杯赛）
    elif matches and teams:
        team_stats = {}
        
        for match in matches:
            if match.get('score') == '-' or not match.get('score'):
                continue
            
            home_id = match.get('home_id')
            away_id = match.get('away_id')
            
            if home_id not in teams or away_id not in teams:
                continue
            
            try:
                parts = match['score'].split('-')
                home_goals = int(parts[0])
                away_goals = int(parts[1])
            except:
                continue
            
            # 初始化球队统计
            if home_id not in team_stats:
                team_stats[home_id] = {
                    'team_id': home_id,
                    'team_name': teams[home_id].get('name', str(home_id)),
                    'played': 0, 'won': 0, 'draw': 0, 'lost': 0
                }
            if away_id not in team_stats:
                team_stats[away_id] = {
                    'team_id': away_id,
                    'team_name': teams[away_id].get('name', str(away_id)),
                    'played': 0, 'won': 0, 'draw': 0, 'lost': 0
                }
            
            team_stats[home_id]['played'] += 1
            team_stats[away_id]['played'] += 1
            
            if home_goals > away_goals:
                team_stats[home_id]['won'] += 1
                team_stats[away_id]['lost'] += 1
            elif home_goals < away_goals:
                team_stats[home_id]['lost'] += 1
                team_stats[away_id]['won'] += 1
            else:
                team_stats[home_id]['draw'] += 1
                team_stats[away_id]['draw'] += 1
        
        # 计算百分比
        for team_id, stats in team_stats.items():
            played = stats['played']
            stats['win_pct'] = round(stats['won'] / played * 100, 1) if played > 0 else 0
            stats['draw_pct'] = round(stats['draw'] / played * 100, 1) if played > 0 else 0
            stats['lost_pct'] = round(stats['lost'] / played * 100, 1) if played > 0 else 0
            result.append(stats)
    
    # 按胜率排序
    result.sort(key=lambda x: (-x['win_pct'], -x['won'], x['team_name']))
    
    # 添加排名
    for i, team in enumerate(result):
        team['rank'] = i + 1
    
    return result

def calculate_group_standings(matches, teams, cup_format='world_cup'):
    """
    计算杯赛小组赛积分榜
    
    小组赛round格式：
    - world_cup: G21534A, G21534B 等，G开头+数字+组名(A-H)
    - champions_league: 23702A, 23702B 等，数字+组名(A-H)
    
    每个小组：
    - 世界杯：4支球队，每队3场比赛
    - 欧冠：4支球队，每队6场比赛（主客场）
    """
    groups = {}
    for m in matches:
        round_name = m.get('round', '')
        # 支持两种格式：G21534A 或 23702A
        if cup_format == 'world_cup':
            # 世界杯格式：G开头
            if round_name.startswith('G') and len(round_name) > 1 and round_name[-1] in 'ABCDEFGH':
                group_name = round_name[-1]
        else:
            # 欧冠/欧罗巴格式：数字+字母
            if len(round_name) >= 2 and round_name[-1] in 'ABCDEFGH':
                # 提取组名（最后一个字母）
                group_name = round_name[-1]
        
        if group_name:
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(m)
    
    result = {}
    for group_name, group_matches in sorted(groups.items()):
        team_stats = {}
        
        for m in group_matches:
            hid, aid = m.get('home_id'), m.get('away_id')
            if hid not in teams or aid not in teams:
                continue
            
            if hid not in team_stats:
                team_stats[hid] = {
                    'team_id': hid,
                    'team_name': teams[hid].get('name', str(hid)),
                    'played': 0, 'won': 0, 'draw': 0, 'lost': 0,
                    'goals_for': 0, 'goals_against': 0, 'points': 0
                }
            if aid not in team_stats:
                team_stats[aid] = {
                    'team_id': aid,
                    'team_name': teams[aid].get('name', str(aid)),
                    'played': 0, 'won': 0, 'draw': 0, 'lost': 0,
                    'goals_for': 0, 'goals_against': 0, 'points': 0
                }
            
            if m.get('score') == '-' or not m.get('score'):
                continue
            
            try:
                parts = m['score'].split('-')
                home_goals = int(parts[0])
                away_goals = int(parts[1])
                
                team_stats[hid]['played'] += 1
                team_stats[aid]['played'] += 1
                team_stats[hid]['goals_for'] += home_goals
                team_stats[aid]['goals_for'] += away_goals
                team_stats[hid]['goals_against'] += away_goals
                team_stats[aid]['goals_against'] += home_goals
                
                if home_goals > away_goals:
                    team_stats[hid]['won'] += 1
                    team_stats[hid]['points'] += 3
                    team_stats[aid]['lost'] += 1
                elif home_goals < away_goals:
                    team_stats[hid]['lost'] += 1
                    team_stats[aid]['won'] += 1
                    team_stats[aid]['points'] += 3
                else:
                    team_stats[hid]['draw'] += 1
                    team_stats[aid]['draw'] += 1
                    team_stats[hid]['points'] += 1
                    team_stats[aid]['points'] += 1
            except:
                pass
        
        standings = list(team_stats.values())
        standings.sort(key=lambda x: (-x['points'], x['goals_for']-x['goals_against'], -x['goals_for']))
        for i, t in enumerate(standings):
            t['goal_diff'] = t['goals_for'] - t['goals_against']
            t['rank'] = i + 1
        
        result[group_name] = standings
    
    return result

def fetch_scorers_data(league_id=36, season="2025-2026"):
    """
    获取射手榜数据
    
    【重要】必须携带Referer，否则会被WAF阻止！
    """
    url = f"https://zq.titan007.com/jsData/Count/{season}/playerTech_{league_id}.js"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': f'https://zq.titan007.com/cn/TechList/{season}/{league_id}.html'  # 必须带！
    }
    
    print(f"获取射手榜数据: {url}")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.encoding = 'utf-8'
    
    return resp.text

def parse_scorers_data(js_content, teams):
    """解析射手榜数据"""
    match = re.search(r'var techCout_Player\s*=\s*(\{.*\});', js_content, re.DOTALL)
    if not match:
        return []
    
    try:
        data = json.loads(match.group(1))
    except:
        return []
    
    pid = data.get('Pid', {})
    total = data.get('Total', {})
    home = data.get('Home', {})
    guest = data.get('guest', {})
    
    total_value = total.get('value', [])
    home_value = home.get('value', [])
    guest_value = guest.get('guest', guest.get('value', []))
    
    # 构建主场/客场进球查找表
    home_goals = {}
    for h in home_value:
        if isinstance(h, list) and len(h) > 52:
            home_goals[h[0]] = h[52] if h[52] else 0
    
    guest_goals = {}
    for g in guest_value:
        if isinstance(g, list) and len(g) > 52:
            guest_goals[g[0]] = g[52] if g[52] else 0
    
    # 解析射手榜
    scorers = []
    for stats in total_value:
        if isinstance(stats, list) and len(stats) > 52:
            player_id = stats[0]
            goals = stats[52] if stats[52] else 0
            penalty = stats[5] if len(stats) > 5 and stats[5] else 0
            
            # 获取球员信息
            player_info = pid.get(str(player_id))
            if player_info and goals > 0:
                name = player_info[0][0]
                team_id = player_info[1]
                team_name = teams.get(team_id, {}).get('name', str(team_id))
                
                scorers.append({
                    'player_id': player_id,
                    'name': name,
                    'team_id': team_id,
                    'team_name': team_name,
                    'goals': goals,
                    'penalty': penalty,
                    'home_goals': home_goals.get(player_id, 0),
                    'away_goals': guest_goals.get(player_id, 0)
                })
    
    # 按进球排序
    scorers.sort(key=lambda x: (-x['goals'], x['name']))
    
    # 添加排名
    for i, s in enumerate(scorers):
        s['rank'] = i + 1
    
    return scorers

def save_data(league_id, season, data):
    """保存数据"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    filename = os.path.join(OUTPUT_DIR, f"{league_id}_{season.replace('-', '_')}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {filename}")

def get_league_url_info(league_id, season):
    """
    获取联赛URL信息
    
    不同联赛使用不同的URL格式：
    
    1. 欧洲联赛（英超36、西甲31、德甲8、意甲34、法甲11）：
       URL格式: s{league_id}.js
       例: https://zq.titan007.com/jsData/matchResult/2024-2025/s36.js
    
    2. 亚洲联赛（中超60、日职联25、韩K联15、澳超273）：
       URL格式: s{league_id}_{sub_id}.js
       例: https://zq.titan007.com/jsData/matchResult/2024/s60_2187.js
       需要先从联赛页面获取 SubSclassID
    
    3. 杯赛（欧冠103、欧罗巴113、亚冠精英192）：
       URL格式: c{league_id}.js
       例: https://zq.titan007.com/jsData/matchResult/2024-2025/c103.js
    
    返回值:
        {'type': 'sub', 'sub_id': '2187'} - 亚洲联赛格式
        {'type': 'cup', 'url_pattern': 'c'} - 杯赛格式
        None - 默认欧洲联赛格式
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': f'https://zq.titan007.com/cn/League/{league_id}.html'  # 必须带！
    }
    
    league_page_url = f"https://zq.titan007.com/cn/League/{league_id}.html"
    try:
        resp = requests.get(league_page_url, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        
        # 检查是否有 SubSclassID（亚洲联赛）
        match = re.search(r'var SubSclassID = (\d+)', resp.text)
        if match:
            return {'type': 'sub', 'sub_id': match.group(1)}
        
        # 检查JS文件路径判断格式
        match = re.search(r'src="(/jsData/matchResult/[^"]+)"', resp.text)
        if match:
            js_path = match.group(1)
            # 杯赛格式: c{id}.js
            if 'c' in js_path:
                match2 = re.search(r'c(\d+)\.js', js_path)
                if match2:
                    return {'type': 'cup', 'url_pattern': 'c'}
            # 子联赛格式: s{id}_{sub_id}.js
            match2 = re.search(r's\d+_(\d+)\.js', js_path)
            if match2:
                return {'type': 'sub', 'sub_id': match2.group(1)}
    except Exception as e:
        print(f"  获取URL信息失败: {e}")
    
    return None

def crawl_league(league_id, league_name):
    """
    爬取单个联赛的所有赛季数据
    
    流程：
    1. 获取赛季列表
    2. 遍历每个赛季：
       a. 先尝试默认URL格式 (s{id}.js)
       b. 如果失败，检测URL类型（子联赛/杯赛）
       c. 使用正确的URL格式重新请求
       d. 解析并保存数据
    """
    print(f"\n{'='*50}")
    print(f"开始爬取: {league_name} (ID: {league_id})")
    print(f"{'='*50}")
    
    # 【关键】必须带Referer！
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': f'https://zq.titan007.com/cn/League/{league_id}.html'
    }
    
    # Step 1: 获取赛季列表
    season_url = f"https://zq.titan007.com/jsData/LeagueSeason/sea{league_id}.js"
    print(f"获取赛季列表: {season_url}")
    season_resp = requests.get(season_url, headers=headers, timeout=30)
    season_resp.encoding = 'utf-8'
    seasons = parse_season_data(season_resp.text)
    
    if not seasons:
        print(f"  未获取到赛季列表，跳过")
        return
    
    print(f"共 {len(seasons)} 个赛季")
    
    # 用于缓存URL类型信息
    url_info = None
    
    # Step 2: 爬取所有赛季
    for season in seasons:
        print(f"\n爬取赛季: {season}")
        
        # 默认URL格式（欧洲联赛）
        match_url = f"https://zq.titan007.com/jsData/matchResult/{season}/s{league_id}.js"
        
        try:
            match_resp = requests.get(match_url, headers=headers, timeout=30)
            match_resp.encoding = 'utf-8'
            
            teams = parse_team_data(match_resp.text)
            
            # Step 3: 如果默认格式没有数据，尝试其他格式
            if not teams:
                # 首次失败时检测URL类型
                if url_info is None:
                    url_info = get_league_url_info(league_id, season)
                
                if url_info:
                    if url_info['type'] == 'sub':
                        # 亚洲联赛格式: s{id}_{sub_id}.js
                        match_url = f"https://zq.titan007.com/jsData/matchResult/{season}/s{league_id}_{url_info['sub_id']}.js"
                    elif url_info['type'] == 'cup':
                        # 杯赛格式: c{id}.js
                        match_url = f"https://zq.titan007.com/jsData/matchResult/{season}/c{league_id}.js"
                    print(f"  尝试特殊URL: {match_url}")
                    match_resp = requests.get(match_url, headers=headers, timeout=30)
                    match_resp.encoding = 'utf-8'
                    teams = parse_team_data(match_resp.text)
            
            print(f"获取比赛数据: {match_url}")
            
            if not teams:
                print(f"  未获取到球队数据，跳过")
                continue
            
            # Step 4: 解析数据
            league_info = parse_league_info(match_resp.text)
            standings = parse_standings(match_resp.text, teams)
            matches = parse_matches(match_resp.text, teams)
            handicap_standings = calculate_handicap_standings(matches, teams)
            total_goals_standings = calculate_total_goals_standings(matches, teams)
            
            # 杯赛计算小组积分榜和胜平负统计
            if url_info and url_info['type'] == 'cup':
                # 欧冠/欧罗巴使用champions_league格式
                cup_format = 'champions_league' if league_id in [103, 113] else 'world_cup'
                group_standings = calculate_group_standings(matches, teams, cup_format)
                # 杯赛没有积分榜，从比赛数据计算胜平负
                win_draw_lose_standings = calculate_win_draw_lose_standings(
                    standings.get('total', []), matches, teams
                )
            else:
                group_standings = {}
                win_draw_lose_standings = calculate_win_draw_lose_standings(
                    standings.get('total', []), matches, teams
                )
            
            # 获取射手榜
            scorers = []
            try:
                scorers_js = fetch_scorers_data(league_id, season)
                scorers = parse_scorers_data(scorers_js, teams)
            except Exception as e:
                print(f"  射手榜数据获取失败: {e}")
            
            # Step 5: 保存数据
            data = {
                "league": league_info,
                "seasons": seasons,
                "current_season": season,
                "teams": list(teams.values()),
                "group_standings": group_standings,
                "standings": standings,
                "win_draw_lose_standings": win_draw_lose_standings,
                "handicap_standings": handicap_standings,
                "total_goals_standings": total_goals_standings,
                "scorers": scorers,
                "matches": matches,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            save_data(league_id, season, data)
            
            print(f"  球队数: {len(teams)}, 比赛数: {len(matches)}, 胜平负: {len(win_draw_lose_standings)}, 让球: {len(handicap_standings)}, 大小球: {len(total_goals_standings)}, 射手: {len(scorers)}")
        except Exception as e:
            print(f"  爬取失败: {e}")
            continue

def main():
    """
    主函数
    
    联赛分类：
    - 欧洲联赛 (URL格式: s{id}.js, 赛季格式: 2024-2025)
      英超(36)、西甲(31)、德甲(8)、意甲(34)、法甲(11)
    
    - 亚洲联赛 (URL格式: s{id}_{sub_id}.js, 赛季格式: 2024)
      中超(60)、日职联(25)、韩K联(15)、澳超(273)
    
    - 杯赛 (URL格式: c{id}.js, 赛季格式: 2024-2025 或 2022)
      世界杯(75)、欧冠杯(103)、欧罗巴杯(113)、亚冠精英(192)
    """
    leagues = [
        # 欧洲联赛
        (36, '英超'),
        (31, '西甲'),
        (8, '德甲'),
        (34, '意甲'),
        (11, '法甲'),
        # 亚洲联赛
        (60, '中超'),
        (25, '日职联'),
        (15, '韩K联'),
        (273, '澳超'),
        # 杯赛
        (192, '亚冠精英'),
        (75, '世界杯'),
        (103, '欧冠杯'),
        (113, '欧罗巴杯'),
    ]
    
    for league_id, league_name in leagues:
        crawl_league(league_id, league_name)
    
    print(f"\n{'='*50}")
    print("全部完成!")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()