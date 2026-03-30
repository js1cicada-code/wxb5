#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import re, json, os
from datetime import datetime

OUTPUT_DIR = 'data/league'

def parse_team_data(js_content):
    teams = {}
    match = re.search(r"var arrTeam\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for team in arr:
            if len(team) >= 5:
                teams[team[0]] = {'id': team[0], 'name': team[1], 'name_tw': team[2], 'name_en': team[3]}
    return teams

def parse_standings(js_content, teams):
    standings = {'total': [], 'home': [], 'away': [], 'half': []}
    match = re.search(r"var totalScore\s*=\s*(\[.*?\]);", js_content, re.DOTALL)
    if match:
        arr = eval(match.group(1))
        for row in arr:
            if len(row) >= 15:
                team_id = row[2]
                team = teams.get(team_id, {})
                standings['total'].append({
                    'team_id': team_id, 'team_name': team.get('name', str(team_id)),
                    'played': row[4], 'won': row[5], 'draw': row[6], 'lost': row[7],
                    'goals_for': row[8], 'goals_against': row[9], 'goal_diff': row[10],
                    'points': row[5]*3 + row[6]
                })
        standings['total'].sort(key=lambda x: (-x['points'], -x['goal_diff']))
        for i, t in enumerate(standings['total']):
            t['rank'] = i + 1
    return standings

def parse_matches(js_content, teams):
    matches = []
    pattern = r'jh\["R_(\d+)"\]\s*=\s*(\[.*?\]);'
    for m in re.finditer(pattern, js_content, re.DOTALL):
        try:
            arr = eval(m.group(2))
            for row in arr:
                if len(row) >= 14:
                    matches.append({
                        'round': int(m.group(1)), 'match_id': row[0], 'date': row[3],
                        'home_id': row[4], 'home_name': teams.get(row[4], {}).get('name', str(row[4])),
                        'away_id': row[5], 'away_name': teams.get(row[5], {}).get('name', str(row[5])),
                        'score': row[6] or '-', 'half_score': row[7] or '-',
                        'handicap': row[10] or 0, 'total_goals': row[12] or '-'
                    })
        except: pass
    return sorted(matches, key=lambda x: (x['round'], x.get('date', '')))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    
    seasons_list = ['2006', '2007', '2008', '2015', '2016', '2018', '2019']
    
    for season in seasons_list:
        print(f'爬取 {season}...')
        for sub_id in [943, 944, 945, 946, 947]:
            url = f'https://zq.titan007.com/jsData/matchResult/{season}/s25_{sub_id}.js'
            try:
                page.goto(url, wait_until='networkidle', timeout=10000)
                content = page.content()
                if 'arrTeam' in content and len(content) > 30000:
                    teams = parse_team_data(content)
                    if len(teams) >= 16:
                        standings = parse_standings(content, teams)
                        matches = parse_matches(content, teams)
                        
                        data = {
                            'league': {}, 'seasons': [], 'current_season': season,
                            'teams': list(teams.values()), 'standings': standings,
                            'win_draw_lose_standings': [], 'handicap_standings': [],
                            'total_goals_standings': [], 'scorers': [], 'matches': matches,
                            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        os.makedirs(OUTPUT_DIR, exist_ok=True)
                        with open(f'{OUTPUT_DIR}/25_{season}.json', 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        print(f'  保存: teams={len(teams)}, matches={len(matches)}')
                        break
            except: continue
    
    browser.close()

print('完成!')