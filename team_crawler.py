#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
球队详情数据爬虫 - 从球探体育获取球队详细信息
"""

import json
import re
import requests
import time
from datetime import datetime
from path_config import save_json
import os

BASE_URL = "https://zq.titan007.com"
TEAM_DETAIL_URL = BASE_URL + "/jsData/teamInfo/teamDetail/tdl{team_id}.js"
TEAM_HISTORY_URL = BASE_URL + "/cn/team/TeamHistoryOrder/{team_id}.html"
TEAM_TRANSFER_URL = BASE_URL + "/cn/team/PlayerZhAjax.aspx?matchSeason={season}&teamID={team_id}"
LOGO_URL_TM = "https://tmssl.akamaized.net/images/wappen/head/{team_id}.png"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': BASE_URL,
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0'
}

session = requests.Session()
session.headers.update(HEADERS)

def download_logo(team_id, logo_url=None):
    """下载球队logo到本地"""
    local_path = f"data/images/team/{team_id}.png"
    
    if os.path.exists(local_path):
        print(f"Logo已存在: {local_path}")
        return f"images/team/{team_id}.png"
    
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    urls_to_try = [
        LOGO_URL_TM.format(team_id=team_id),
    ]
    
    if logo_url:
        urls_to_try.insert(0, logo_url)
    
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 500:
                with open(local_path, 'wb') as f:
                    f.write(resp.content)
                print(f"Logo下载成功: {local_path}")
                return f"images/team/{team_id}.png"
        except Exception as e:
            continue
    
    print(f"Logo下载失败，使用占位图")
    return f"images/team/default.png"

def fetch_team_detail(team_id):
    """获取球队详细信息"""
    url = TEAM_DETAIL_URL.format(team_id=team_id)
    print(f"获取球队数据: {url}")
    
    try:
        response = session.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        # 检查是否被WAF拦截
        if 'WAF' in response.text or '非法' in response.text:
            print(f"WAF拦截，等待30秒后重试...")
            time.sleep(30)
            response = session.get(url, timeout=30)
            response.encoding = 'utf-8'
        
        return response.text
    except Exception as e:
        print(f"获取失败: {e}")
        return None

def fetch_team_history(team_id):
    """获取球队历史排名走势"""
    url = TEAM_HISTORY_URL.format(team_id=team_id)
    print(f"获取球队走势: {url}")
    
    try:
        response = session.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        if 'WAF' in response.text or '非法' in response.text:
            print(f"WAF拦截，等待30秒后重试...")
            time.sleep(30)
            response = session.get(url, timeout=30)
            response.encoding = 'utf-8'
        
        return response.text
    except Exception as e:
        print(f"获取走势失败: {e}")
        return None

def parse_history_data(html_content):
    """从HTML中解析历史排名数据"""
    import re
    
    match = re.search(r"var orderData='([^']+)';", html_content)
    if not match:
        return []
    
    order_data = match.group(1)
    parts = order_data.split('$')
    
    history_data = []
    if len(parts) > 2:
        history_str = parts[2]
        for h in history_str.split('!'):
            items = h.split('^')
            if len(items) >= 7:
                try:
                    season = items[1]
                    if '/' in season and len(season) == 5:
                        start_year = int(season.split('/')[0])
                        if start_year < 50:
                            start_year += 2000
                        else:
                            start_year += 1900
                        season = f"{start_year}-{start_year + 1}"
                    
                    history_data.append({
                        'season': season,
                        'rank': int(items[2]),
                        'wins': int(items[3]),
                        'draws': int(items[4]),
                        'losses': int(items[5]),
                        'points': int(items[6])
                    })
                except:
                    continue
    
    print(f"解析到 {len(history_data)} 个赛季历史排名")
    return history_data

def fetch_transfer_data(team_id, season='2025-2026'):
    """获取球队转会数据"""
    url = TEAM_TRANSFER_URL.format(team_id=team_id, season=season)
    print(f"获取转会数据: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.encoding = 'utf-8'
        return response.text
    except Exception as e:
        print(f"获取转会数据失败: {e}")
        return None

def fetch_all_transfers(team_id):
    """获取所有赛季的转会数据"""
    from datetime import datetime
    current_year = datetime.now().year
    seasons = []
    
    # 生成从2003到当前年份的所有赛季
    for year in range(2003, current_year + 1):
        seasons.append(f"{year}-{year+1}")
    
    all_transfers = {}
    
    for season in seasons:
        print(f"  获取 {season} 赛季...")
        html = fetch_transfer_data(team_id, season)
        if html:
            transfers = parse_transfer_data(html)
            if transfers['in'] or transfers['out']:
                all_transfers[season] = transfers
                print(f"    {season}: 转入{len(transfers['in'])}人, 转出{len(transfers['out'])}人")
        
        # 添加延迟避免被封
        time.sleep(1)
    
    return all_transfers

def parse_transfer_data(html_content):
    """解析转会数据HTML"""
    from bs4 import BeautifulSoup
    import re
    
    if not html_content or len(html_content) < 100:
        return {'in': [], 'out': []}
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    transfers_in = []
    transfers_out = []
    
    tables = soup.find_all('table')
    
    for table in tables:
        prev = table.find_previous_sibling('div', class_='main_title')
        if not prev:
            continue
            
        title = prev.get_text(strip=True)
        is_in = '转入' in title
        
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                player_link = cols[1].find('a')
                from_link = cols[3].find('a')
                
                player_id = ''
                if player_link and player_link.get('href'):
                    match = re.search(r'PlayerID=(\d+)', player_link['href'])
                    if match:
                        player_id = match.group(1)
                
                transfer = {
                    'date': cols[0].get_text(strip=True),
                    'player': player_link.get_text(strip=True) if player_link else cols[1].get_text(strip=True),
                    'player_id': player_id,
                    'position': cols[2].get_text(strip=True),
                    'club': from_link.get_text(strip=True) if from_link else cols[3].get_text(strip=True),
                    'type': cols[4].get_text(strip=True)
                }
                
                if is_in:
                    transfers_in.append(transfer)
                else:
                    transfers_out.append(transfer)
    
    print(f"解析到 转入{len(transfers_in)}人, 转出{len(transfers_out)}人")
    return {'in': transfers_in, 'out': transfers_out}

def safe_eval_array(js_str):
    """安全解析JS数组"""
    js_str = js_str.strip()
    if js_str.endswith(';'):
        js_str = js_str[:-1]
    
    try:
        import json
        json_str = js_str.replace("'", '"')
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        return json.loads(json_str)
    except:
        pass
    
    return None

def parse_team_detail(js_content, team_id):
    """解析球队详情JS数据"""
    result = {
        "team_id": team_id,
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "detail": None,
        "lineup": {
            "goalkeeper": [],
            "defender": [],
            "midfielder": [],
            "forward": [],
            "coach": []
        },
        "lineup_detail": [],
        "league_stats": [],
        "cup_stats": [],
        "tech_stats": [],
        "history_ranking": [],
        "transfers": []
    }
    
    local_logo = download_logo(team_id)
    
    # 获取历史排名
    history_html = fetch_team_history(team_id)
    if history_html:
        result["history_ranking"] = parse_history_data(history_html)
    
    # 获取所有赛季转会数据
    result["transfers"] = fetch_all_transfers(team_id)
    
    try:
        # 更灵活的正则表达式，匹配teamDetail数组
        team_detail_match = re.search(r'(?:var\s+)?teamDetail\s*=\s*\[(\d+),(.+?)\];', js_content, re.DOTALL)
        if team_detail_match:
            team_id_val = team_detail_match.group(1)
            rest = team_detail_match.group(2)
            
            # 提取所有字符串
            strings = re.findall(r"'([^']*)'", rest)
            # 提取所有数字
            numbers = re.findall(r"([\d.]+)", rest)
            
            print(f"Parsed {len(strings)} string values, {len(numbers)} numeric values")
            for idx, s in enumerate(strings):
                print(f"  [{idx}]: {s[:30]}..." if len(s) > 30 else f"  [{idx}]: {s}")
            
            if len(strings) >= 15:
                avg_age = numbers[-2] if len(numbers) >= 2 else "0"
                total_value = numbers[-1] if len(numbers) >= 1 else "0"
                
                result["detail"] = {
                    "team_id": team_id_val,
                    "name_cn": strings[0],
                    "name_hk": strings[1],
                    "name_en": strings[2],
                    "logo": local_logo,
                    "logo_original": BASE_URL + "/" + strings[3] if strings[3] else "",
                    "city_cn": strings[4],
                    "city_hk": strings[5],
                    "city_en": strings[6],
                    "stadium_cn": strings[7],
                    "stadium_hk": strings[8],
                    "stadium_en": strings[9],
                    "capacity": strings[10],
                    "founded": strings[11],
                    "website": "https:" + strings[12] if strings[12].startswith('//') else strings[12],
                    "intro": strings[13],
                    "stadium_address": strings[14] if len(strings) > 14 else "",
                    "avg_age": avg_age,
                    "total_value": total_value + "万欧元"
                }
        
        position_map = {
            'goalkeeper': ('守门员', 'goalkeeper'),
            'rearguard': ('后卫', 'defender'),
            'midfielder': ('中场', 'midfielder'),
            'vanguard': ('前锋', 'forward'),
            'coach': ('教练', 'coach')
        }
        
        for js_var, (cn_name, en_name) in position_map.items():
            pattern = rf"var {js_var}\s*=\s*\[(.+?)\];"
            match = re.search(pattern, js_content)
            if match:
                arr_str = match.group(1)
                player_arrays = re.findall(r"\[(.+?)\](?:,|$)", arr_str)
                
                for pa in player_arrays:
                    parts = re.findall(r"'([^']*)'", pa)
                    nums = re.findall(r",(\d+)(?:,|$)", pa)
                    
                    if len(parts) >= 5:
                        is_captain = int(nums[-1]) if nums else 0
                        result["lineup"][en_name].append({
                            "player_id": parts[0],
                            "number": parts[1].strip(),
                            "name_cn": parts[2],
                            "name_hk": parts[3],
                            "name_en": parts[4],
                            "is_captain": is_captain == 1,
                            "position": cn_name
                        })
        
        # Parse lineup detail using regex
        try:
            # Find lineupDetail start
            ld_start = js_content.find('var lineupDetail=')
            if ld_start != -1:
                ld_start = js_content.find('[', ld_start)
                if ld_start != -1:
                    # Find matching closing bracket
                    depth = 0
                    ld_end = ld_start
                    for i, c in enumerate(js_content[ld_start:], ld_start):
                        if c == '[':
                            depth += 1
                        elif c == ']':
                            depth -= 1
                            if depth == 0:
                                ld_end = i + 1
                                break
                    
                    ld_content = js_content[ld_start+1:ld_end-1]  # Remove outer brackets
                    print(f"lineupDetail content length: {len(ld_content)}")
                    
                    # Split by '],[' to get individual player arrays
                    # First, find all player arrays
                    player_arrays = []
                    current_start = 0
                    bracket_depth = 0
                    
                    for i, c in enumerate(ld_content):
                        if c == '[':
                            bracket_depth += 1
                        elif c == ']':
                            bracket_depth -= 1
                            if bracket_depth == 0 and i > current_start:
                                # Found complete player array
                                player_arrays.append(ld_content[current_start:i+1])
                                current_start = i + 2  # Skip ],
                    
                    print(f"Found {len(player_arrays)} player arrays")
                    
                    for pa in player_arrays:
                        # Remove outer brackets
                        pa = pa.strip()
                        if pa.startswith('['):
                            pa = pa[1:]
                        if pa.endswith(']'):
                            pa = pa[:-1]
                        
                        # Parse values - handle both strings and numbers
                        values = []
                        in_string = False
                        current_val = ""
                        i = 0
                        
                        while i < len(pa):
                            c = pa[i]
                            
                            if c == "'" and not in_string:
                                in_string = True
                                current_val = ""
                                i += 1
                            elif c == "'" and in_string:
                                in_string = False
                                values.append(current_val)
                                current_val = ""
                                i += 1
                            elif in_string:
                                current_val += c
                                i += 1
                            elif c == ',':
                                if current_val.strip():
                                    try:
                                        values.append(int(current_val.strip()))
                                    except:
                                        values.append(current_val.strip())
                                current_val = ""
                                i += 1
                            else:
                                current_val += c
                                i += 1
                        
                        # Add last value
                        if current_val.strip():
                            try:
                                values.append(int(current_val.strip()))
                            except:
                                values.append(current_val.strip())
                        
                        if len(values) >= 14:
                            result["lineup_detail"].append({
                                "player_id": str(values[0]) if len(values) > 0 else "",
                                "number": str(values[1]).strip() if len(values) > 1 else "",
                                "name_cn": str(values[2]) if len(values) > 2 and values[2] else "",
                                "name_hk": str(values[3]) if len(values) > 3 and values[3] else "",
                                "name_en": str(values[4]) if len(values) > 4 and values[4] else "",
                                "is_captain": values[5] == 1 if len(values) > 5 else False,
                                "birthday": str(values[6]) if len(values) > 6 and values[6] else "",
                                "height": str(values[7]) if len(values) > 7 else "",
                                "weight": str(values[8]) if len(values) > 8 else "",
                                "position": str(values[9]) if len(values) > 9 and values[9] else "",
                                "country_cn": str(values[10]) if len(values) > 10 and values[10] else "",
                                "country_en": str(values[11]) if len(values) > 11 and values[11] else "",
                                "value": str(values[12]) + '万欧元' if len(values) > 12 and values[12] else "",
                                "contract_end": str(values[13]) if len(values) > 13 else "",
                                "total_matches": str(values[14]) if len(values) > 14 else "0",
                                "goals": str(values[15]) if len(values) > 15 else "0",
                                "assists": str(values[16]) if len(values) > 16 else "0",
                                "yellow_cards": str(values[17]) if len(values) > 17 else "0",
                                "red_cards": str(values[18]) if len(values) > 18 else "0"
                            })
                    
                    print(f"Parsed {len(result['lineup_detail'])} players from lineupDetail")
                    
        except Exception as e:
            print(f"Error parsing lineupDetail: {e}")
            import traceback
            traceback.print_exc()
        
        league_match = re.search(r"var leagueData\s*=\s*\[(.+?)\];", js_content)
        if league_match:
            arr_str = league_match.group(1)
            arr_str = re.sub(r',0$', '', arr_str)
            
            season_arrays = re.findall(r"\[([^\]]+)\]", arr_str)
            
            labels = ['主场', '客场', '总', '上半场主场', '上半场客场', '上半场总']
            
            for i, sa in enumerate(season_arrays[:6]):
                parts = sa.split(',')
                if len(parts) >= 13:
                    result["league_stats"].append({
                        "type": labels[i] if i < len(labels) else f"类型{i+1}",
                        "matches": parts[0].strip().lstrip('['),
                        "wins": parts[1].strip(),
                        "draws": parts[2].strip(),
                        "losses": parts[3].strip(),
                        "goals": parts[4].strip(),
                        "conceded": parts[5].strip(),
                        "goal_diff": parts[6].strip(),
                        "win_rate": parts[7].strip().strip("'"),
                        "draw_rate": parts[8].strip().strip("'"),
                        "loss_rate": parts[9].strip().strip("'"),
                        "avg_goals": parts[10].strip(),
                        "avg_conceded": parts[11].strip()
                    })
        
        cup_match = re.search(r"var cupData\s*=\s*(\[.+\]);", js_content)
        if cup_match:
            arr_str = cup_match.group(1)
            cup_arrays = re.findall(r"\[(\d+),'([^']+)','([^']+)','([^']+)','([^']+)'\]", arr_str)
            
            for c in cup_arrays:
                result["cup_stats"].append({
                    "cup_id": c[0],
                    "name_cn": c[1],
                    "name_hk": c[2],
                    "name_en": c[3],
                    "season": c[4]
                })
            print(f"Found {len(cup_arrays)} cup entries")
        
        count_match = re.search(r"var countSum\s*=\s*(\[.+\]);", js_content)
        if count_match:
            arr_str = count_match.group(1)
            count_arrays = re.findall(r"\['([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)','([^']+)'(?:,'[^']*')*\]", arr_str)
            
            for c in count_arrays:
                league_name = c[1].split('^') if '^' in c[1] else [c[1], c[1]]
                result["tech_stats"].append({
                    "league_id": c[0],
                    "league_name_cn": league_name[0],
                    "league_name_hk": league_name[1] if len(league_name) > 1 else league_name[0],
                    "total_matches": c[2],
                    "wins": c[3],
                    "draws": c[4],
                    "total_goals": c[5],
                    "conceded": c[6],
                    "clean_sheets": c[7],
                    "win_rate": c[8]
                })
            print(f"Found {len(count_arrays)} tech stats entries")
        
    except Exception as e:
        print(f"解析失败: {e}")
        import traceback
        traceback.print_exc()
    
    return result

def save_team_data(team_data, team_id):
    """保存球队数据"""
    filename = f"team_{team_id}.json"
    save_json(team_data, filename)
    print(f"球队 {team_id} 数据已保存")

def crawl_team(team_id):
    """爬取单个球队数据"""
    js_content = fetch_team_detail(team_id)
    if js_content:
        team_data = parse_team_detail(js_content, team_id)
        save_team_data(team_data, team_id)
        return team_data
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        team_ids = sys.argv[1:]
    else:
        team_ids = [19]
    
    print(f"开始爬取球队: {team_ids}")
    for tid in team_ids:
        crawl_team(tid)
    print("完成!")