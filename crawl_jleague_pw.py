#!/usr/bin/env python3
import json
import os
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "data/league"

def parse_team_data(js_content):
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
    info = {}
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
    return info

def parse_standings(js_content, teams):
    standings = {"total": [], "home": [], "away": [], "half": []}
    
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
                    "points": points
                })
        standings["total"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["total"]):
            team["rank"] = i + 1
    
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
        standings["home"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["home"]):
            team["rank"] = i + 1
    
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
        standings["away"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["away"]):
            team["rank"] = i + 1
    
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
        standings["half"].sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"], x["team_name"]))
        for i, team in enumerate(standings["half"]):
            team["rank"] = i + 1
    
    return standings

def parse_matches(js_content, teams):
    matches = []
    
    pattern = r'jh\["R_(\d+)"\]\s*=\s*(\[.*?\]);'
    for match in re.finditer(pattern, js_content, re.DOTALL):
        round_num = int(match.group(1))
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
        except:
            continue
    
    return sorted(matches, key=lambda x: (x["round"], x.get("date", "")))

def calculate_handicap_standings(matches, teams):
    team_stats = {}
    for team_id in teams:
        team_stats[team_id] = {
            "team_id": team_id,
            "team_name": teams[team_id]["name"],
            "played": 0, "won": 0, "draw": 0, "lost": 0,
            "win_pct": 0, "draw_pct": 0, "lost_pct": 0
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
        adjusted_home_goals = home_goals - handicap
        if adjusted_home_goals > away_goals:
            team_stats[home_id]["won"] += 1
            team_stats[away_id]["lost"] += 1
        elif adjusted_home_goals < away_goals:
            team_stats[home_id]["lost"] += 1
            team_stats[away_id]["won"] += 1
        else:
            team_stats[home_id]["draw"] += 1
            team_stats[away_id]["draw"] += 1
        team_stats[home_id]["played"] += 1
        team_stats[away_id]["played"] += 1
    
    result = []
    for team_id, stats in team_stats.items():
        if stats["played"] > 0:
            stats["win_pct"] = round(stats["won"] / stats["played"] * 100, 1)
            stats["draw_pct"] = round(stats["draw"] / stats["played"] * 100, 1)
            stats["lost_pct"] = round(stats["lost"] / stats["played"] * 100, 1)
            result.append(stats)
    
    result.sort(key=lambda x: (-x["win_pct"], -x["won"], x["team_name"]))
    for i, team in enumerate(result):
        team["rank"] = i + 1
    return result

def calculate_total_goals_standings(matches, teams):
    team_stats = {}
    for team_id in teams:
        team_stats[team_id] = {
            "team_id": team_id,
            "team_name": teams[team_id]["name"],
            "played": 0, "over": 0, "draw": 0, "under": 0,
            "over_pct": 0, "draw_pct": 0, "under_pct": 0
        }
    
    for match in matches:
        if match["score"] == '-' or not match["score"]:
            continue
        home_id = match["home_id"]
        away_id = match["away_id"]
        total_goals_line = match["total_goals"]
        if home_id not in team_stats or away_id not in team_stats:
            continue
        if total_goals_line == '-' or total_goals_line == 0:
            continue
        try:
            score_parts = match["score"].split('-')
            home_goals = int(score_parts[0])
            away_goals = int(score_parts[1])
            total_goals = home_goals + away_goals
            if '/' in str(total_goals_line):
                parts = str(total_goals_line).split('/')
                line = float(parts[0]) + float(parts[1]) / 2
            else:
                line = float(total_goals_line)
        except:
            continue
        if total_goals > line:
            team_stats[home_id]["over"] += 1
            team_stats[away_id]["over"] += 1
        elif total_goals < line:
            team_stats[home_id]["under"] += 1
            team_stats[away_id]["under"] += 1
        else:
            team_stats[home_id]["draw"] += 1
            team_stats[away_id]["draw"] += 1
        team_stats[home_id]["played"] += 1
        team_stats[away_id]["played"] += 1
    
    result = []
    for team_id, stats in team_stats.items():
        if stats["played"] > 0:
            stats["over_pct"] = round(stats["over"] / stats["played"] * 100, 1)
            stats["draw_pct"] = round(stats["draw"] / stats["played"] * 100, 1)
            stats["under_pct"] = round(stats["under"] / stats["played"] * 100, 1)
            result.append(stats)
    
    result.sort(key=lambda x: (-x["over_pct"], -x["over"], x["team_name"]))
    for i, team in enumerate(result):
        team["rank"] = i + 1
    return result

def calculate_win_draw_lose_standings(total_standings):
    result = []
    for team in total_standings:
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
            'played': played, 'won': won, 'draw': draw, 'lost': lost,
            'win_pct': win_pct, 'draw_pct': draw_pct, 'lost_pct': lost_pct
        })
    result.sort(key=lambda x: (-x['win_pct'], -x['won'], x['team_name']))
    for i, team in enumerate(result):
        team['rank'] = i + 1
    return result

def parse_scorers_data(js_content, teams):
    match = re.search(r'var techCout_Player\s*=\s*(\{.*?\});', js_content, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except:
        return []
    
    pid = data.get('Pid', {})
    total = data.get('Total', {})
    scorers = []
    
    key_info = total.get('key', {})
    value_list = total.get('value', [])
    
    player_id_idx = key_info.get('PlayerID', 0)
    non_penalty_goals_idx = key_info.get('notPenaltyGoals', 4)
    penalty_goals_idx = key_info.get('penaltyGoals', 5)
    
    for player_stats in value_list:
        if not player_stats or len(player_stats) < 6:
            continue
        player_id = player_stats[player_id_idx] if player_id_idx < len(player_stats) else None
        non_penalty_goals = player_stats[non_penalty_goals_idx] if non_penalty_goals_idx < len(player_stats) else 0
        penalty_goals = player_stats[penalty_goals_idx] if penalty_goals_idx < len(player_stats) else 0
        goals = non_penalty_goals + penalty_goals
        
        if goals > 0:
            scorers.append({
                "player_id": player_id,
                "name": pid.get(str(player_id), str(player_id)),
                "team_id": None,
                "team_name": "",
                "goals": goals,
                "penalty": penalty_goals
            })
    
    scorers.sort(key=lambda x: (-x['goals'], x['name']))
    for i, s in enumerate(scorers):
        s['rank'] = i + 1
    return scorers

def process_and_save(js_content, season, seasons_list):
    teams = parse_team_data(js_content)
    if not teams:
        return False
    
    league_info = parse_league_info(js_content)
    standings = parse_standings(js_content, teams)
    matches = parse_matches(js_content, teams)
    handicap_standings = calculate_handicap_standings(matches, teams)
    total_goals_standings = calculate_total_goals_standings(matches, teams)
    win_draw_lose_standings = calculate_win_draw_lose_standings(standings.get('total', []))
    
    data = {
        "league": league_info,
        "seasons": seasons_list,
        "current_season": season,
        "teams": list(teams.values()),
        "standings": standings,
        "win_draw_lose_standings": win_draw_lose_standings,
        "handicap_standings": handicap_standings,
        "total_goals_standings": total_goals_standings,
        "scorers": [],
        "matches": matches,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(OUTPUT_DIR, f"25_{season}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  保存: {filename}")
    print(f"  球队: {len(teams)}, 比赛: {len(matches)}, 积分榜: {len(standings.get('total', []))}")
    return True

def main():
    print("使用Playwright爬取日职联数据...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        js_data = {}
        
        def handle_response(response):
            url = response.url
            if 's25_' in url and '.js' in url and 'matchResult' in url:
                try:
                    text = response.text()
                    if 'arrTeam' in text:
                        # 提取赛季
                        match = re.search(r'/(\d{4})/s25_', url)
                        if match:
                            season = match.group(1)
                            js_data[season] = text
                            print(f"  拦截: {season} 赛季 ({len(text)} bytes)")
                except:
                    pass
        
        page.on('response', handle_response)
        
        # 获取赛季列表
        print("\n获取赛季列表...")
        page.goto('https://zq.titan007.com/jsData/LeagueSeason/sea25.js', wait_until='networkidle', timeout=30000)
        season_text = page.content()
        match = re.search(r"var arrSeason\s*=\s*(\[.*?\]);", season_text, re.DOTALL)
        seasons = eval(match.group(1)) if match else []
        print(f"找到 {len(seasons)} 个赛季: {seasons}")
        
        # 访问联赛主页获取数据
        print("\n开始拦截数据...")
        
        # 方法1: 访问主页，让页面自动加载当前赛季
        page.goto('https://zq.titan007.com/cn/League/25.html', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(2000)
        
        # 方法2: 遍历每个赛季的子联赛页面
        for season in seasons:
            if season in js_data:
                continue
            
            print(f"\n尝试获取 {season} 赛季...")
            
            # 尝试不同的SubSclassID
            for sub_id in ['943', '944', '3540', '2187']:
                url = f'https://zq.titan007.com/cn/SubLeague/{season}/25/{sub_id}.html'
                try:
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.wait_for_timeout(1000)
                    if season in js_data:
                        break
                except:
                    continue
        
        browser.close()
        
        # 处理和保存数据
        print(f"\n处理 {len(js_data)} 个赛季的数据...")
        for season, js_content in sorted(js_data.items(), reverse=True):
            process_and_save(js_content, season, seasons)
        
        print("\n完成!")

if __name__ == "__main__":
    main()