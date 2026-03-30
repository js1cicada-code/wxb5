#!/usr/bin/env python3
import json
import os
import re
import time
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
        except Exception as e:
            continue
    
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
        adjusted_home_goals = home_goals - handicap
        adjusted_away_goals = away_goals
        if adjusted_home_goals > adjusted_away_goals:
            team_stats[home_id]["won"] += 1
            team_stats[away_id]["lost"] += 1
        elif adjusted_home_goals < adjusted_away_goals:
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
            "played": 0,
            "over": 0,
            "draw": 0,
            "under": 0,
            "over_pct": 0,
            "draw_pct": 0,
            "under_pct": 0
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
            'played': played,
            'won': won,
            'draw': draw,
            'lost': lost,
            'win_pct': win_pct,
            'draw_pct': draw_pct,
            'lost_pct': lost_pct
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
    home = data.get('Home', {})
    guest = data.get('Guest', {})
    scorers = []
    value_list = total.get('value', [])
    key_info = total.get('key', {})
    player_id_idx = key_info.get('PlayerID', 0)
    team_id_idx = key_info.get('TeamID', -1) if 'TeamID' in key_info else -1
    non_penalty_goals_idx = key_info.get('notPenaltyGoals', 4)
    penalty_goals_idx = key_info.get('penaltyGoals', 5)
    home_goals_idx = key_info.get('HomeGoals', -1) if 'HomeGoals' in key_info else -1
    away_goals_idx = key_info.get('AwayGoals', -1) if 'AwayGoals' in key_info else -1
    for i, player_stats in enumerate(value_list):
        if not player_stats or len(player_stats) < 6:
            continue
        player_id = player_stats[player_id_idx] if player_id_idx < len(player_stats) else None
        non_penalty_goals = player_stats[non_penalty_goals_idx] if non_penalty_goals_idx < len(player_stats) else 0
        penalty_goals = player_stats[penalty_goals_idx] if penalty_goals_idx < len(player_stats) else 0
        goals = non_penalty_goals + penalty_goals
        if goals > 0:
            team_id = None
            team_name = ""
            scorers.append({
                "player_id": player_id,
                "name": pid.get(str(player_id), str(player_id)),
                "team_id": team_id,
                "team_name": team_name,
                "goals": goals,
                "penalty": penalty_goals
            })
    scorers.sort(key=lambda x: (-x['goals'], x['name']))
    for i, s in enumerate(scorers):
        s['rank'] = i + 1
    return scorers

def crawl_jleague_with_playwright():
    from datetime import datetime
    
    league_id = 25
    league_name = '日职联'
    
    print(f"使用Playwright爬取: {league_name} (ID: {league_id})")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN'
        )
        page = context.new_page()
        
        js_contents = {}
        
        def handle_response(response):
            url = response.url
            if 's25' in url and url.endswith('.js'):
                try:
                    js_contents[url] = response.text()
                except:
                    pass
        
        page.on('response', handle_response)
        
        # 访问主页面
        print("访问日职联主页...")
        page.goto(f'https://zq.titan007.com/cn/League/{league_id}.html', wait_until='networkidle', timeout=60000)
        time.sleep(2)
        
        # 获取赛季列表
        season_url = f"https://zq.titan007.com/jsData/LeagueSeason/sea{league_id}.js"
        page.goto(season_url, wait_until='networkidle', timeout=30000)
        season_text = page.content()
        match = re.search(r"var arrSeason\s*=\s*(\[.*?\]);", season_text, re.DOTALL)
        seasons = eval(match.group(1)) if match else []
        print(f"找到 {len(seasons)} 个赛季")
        
        # 获取sub_league_id
        page.goto(f'https://zq.titan007.com/cn/League/{league_id}.html', wait_until='networkidle', timeout=60000)
        page_content = page.content()
        match = re.search(r'var SubSclassID = (\d+)', page_content)
        sub_league_id = match.group(1) if match else '3540'
        print(f"SubSclassID: {sub_league_id}")
        
        # 爬取每个赛季
        for season in seasons:
            print(f"\n爬取赛季: {season}")
            
            js_file = f"s{league_id}_{sub_league_id}.js"
            match_url = f"https://zq.titan007.com/jsData/matchResult/{season}/{js_file}"
            
            try:
                page.goto(match_url, wait_until='networkidle', timeout=30000)
                js_content = page.content()
                
                # 提取JS内容
                if 'var arrTeam' not in js_content:
                    print(f"  未获取到数据，跳过")
                    continue
                
                # 解析数据
                teams = parse_team_data(js_content)
                if not teams:
                    print(f"  未解析到球队，跳过")
                    continue
                
                league_info = parse_league_info(js_content)
                standings = parse_standings(js_content, teams)
                matches = parse_matches(js_content, teams)
                handicap_standings = calculate_handicap_standings(matches, teams)
                total_goals_standings = calculate_total_goals_standings(matches, teams)
                win_draw_lose_standings = calculate_win_draw_lose_standings(standings.get('total', []))
                
                # 获取射手榜
                scorers = []
                scorers_url = f"https://zq.titan007.com/jsData/Count/{season}/playerTech_{league_id}.js"
                try:
                    page.goto(scorers_url, wait_until='networkidle', timeout=15000)
                    scorers_js = page.content()
                    scorers = parse_scorers_data(scorers_js, teams)
                except:
                    pass
                
                # 保存数据
                data = {
                    "league": league_info,
                    "seasons": seasons,
                    "current_season": season,
                    "teams": list(teams.values()),
                    "standings": standings,
                    "win_draw_lose_standings": win_draw_lose_standings,
                    "handicap_standings": handicap_standings,
                    "total_goals_standings": total_goals_standings,
                    "scorers": scorers,
                    "matches": matches,
                    "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                filename = os.path.join(OUTPUT_DIR, f"{league_id}_{season}.json")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"  保存: {filename}")
                print(f"  球队: {len(teams)}, 比赛: {len(matches)}, 积分榜: {len(standings.get('total', []))}, 射手: {len(scorers)}")
                
            except Exception as e:
                print(f"  错误: {e}")
                continue
        
        browser.close()
    
    print("\n完成!")

if __name__ == "__main__":
    crawl_jleague_with_playwright()