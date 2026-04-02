#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能批量爬取 - 处理WAF拦截问题
"""

import json
import time
import random
import requests
import re
import os

BASE_URL = "https://zq.titan007.com"
TEAM_DETAIL_URL = BASE_URL + "/jsData/teamInfo/teamDetail/tdl{team_id}.js"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': BASE_URL + '/',
    'Cache-Control': 'no-cache',
}

def check_waf(response):
    """检查是否被WAF拦截"""
    return response.status_code == 442 or 'WAF' in response.text or len(response.text) < 100

def fetch_with_retry(url, max_wait=300):
    """带智能重试的请求"""
    wait_time = 60  # 初始等待时间
    
    for attempt in range(10):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.encoding = 'utf-8'
            
            if check_waf(response):
                print(f"    ⚠️  WAF拦截，等待 {wait_time} 秒...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, max_wait)  # 指数退避
                continue
            
            if response.status_code == 200 and len(response.text) > 1000:
                return response.text
                
        except Exception as e:
            print(f"    错误: {e}")
            time.sleep(10)
    
    return None

def parse_team_detail_simple(js_content, team_id):
    """简化的解析逻辑"""
    result = {
        "team_id": team_id,
        "detail": None,
        "lineup": {"goalkeeper": [], "defender": [], "midfielder": [], "forward": [], "coach": []},
        "lineup_detail": [],
        "league_stats": [],
        "cup_stats": [],
        "tech_stats": [],
        "history_ranking": [],
        "transfers": {"in": [], "out": []}
    }
    
    # 解析teamDetail - 使用更灵活的方式
    match = re.search(r'var teamDetail\s*=\s*(\[.+?\]);', js_content, re.DOTALL)
    
    if match:
        arr_str = match.group(1)
        
        # 提取所有引号内容
        strings = re.findall(r"'([^']*)'", arr_str)
        
        # 提取末尾数字
        nums = re.search(r',([\d.]+),(\d+)\]$', arr_str)
        avg_age = nums.group(1) if nums else ""
        total_value = nums.group(2) if nums else ""
        
        if len(strings) >= 15:
            result["detail"] = {
                "team_id": team_id,
                "name_cn": strings[0],
                "name_hk": strings[1],
                "name_en": strings[2],
                "logo": f"images/team/{team_id}.png",
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
            print(f"    ✓ 解析成功: {strings[0]}")
        else:
            print(f"    ✗ 字符串不足: {len(strings)}")
    else:
        print(f"    ✗ 未找到teamDetail")
    
    # 解析球员位置
    for js_var, pos_key in [('goalkeeper', 'goalkeeper'), ('rearguard', 'defender'), 
                             ('midfielder', 'midfielder'), ('vanguard', 'forward'), ('coach', 'coach')]:
        pattern = rf"var {js_var}\s*=\s*\[(.+?)\];"
        match = re.search(pattern, js_content)
        if match:
            players = re.findall(r"\['([^']+)','([^']+)','([^']+)','([^']+)','([^']+)'", match.group(1))
            for p in players:
                result["lineup"][pos_key].append({
                    "player_id": p[0], "number": p[1].strip(), "name_cn": p[2],
                    "name_hk": p[3], "name_en": p[4], "is_captain": False
                })
    
    # 解析lineupDetail
    match = re.search(r"var lineupDetail\s*=\s*(\[.+?\]);", js_content, re.DOTALL)
    if match:
        depth = 0
        start = 0
        player_arrays = []
        arr_str = match.group(1)
        
        for i, c in enumerate(arr_str):
            if c == '[':
                if depth == 0: start = i + 1
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 1:
                    player_arrays.append(arr_str[start:i])
        
        for pa in player_arrays[:30]:
            parts = []
            in_quote = False
            current = ""
            for char in pa + ",":
                if char == "'":
                    if in_quote and current:
                        parts.append(current)
                        current = ""
                    in_quote = not in_quote
                elif in_quote:
                    current += char
                elif char == ',':
                    if current.strip():
                        parts.append(current.strip())
                    current = ""
            
            if len(parts) >= 14:
                result["lineup_detail"].append({
                    "player_id": parts[0], "number": parts[1].strip(),
                    "name_cn": parts[2], "position": parts[9] if len(parts) > 9 else "",
                    "total_matches": parts[14] if len(parts) > 14 else "",
                    "goals": parts[15] if len(parts) > 15 else "",
                    "assists": parts[16] if len(parts) > 16 else ""
                })
    
    return result

def crawl_all_teams():
    """爬取所有球队"""
    # 加载球队列表
    with open('data/all_team_ids.json', 'r') as f:
        all_teams = json.load(f)
    
    # 检查已完成的球队
    completed = []
    failed = []
    
    for tid in all_teams:
        filepath = f'data/team_{tid}.json'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            if data.get('detail') and data['detail'].get('name_cn'):
                completed.append(tid)
            else:
                failed.append(tid)
        else:
            failed.append(tid)
    
    print(f"已完成: {len(completed)} 支")
    print(f"待处理: {len(failed)} 支")
    
    # 爬取失败的球队
    for i, tid in enumerate(failed):
        print(f"\n[{i+1}/{len(failed)}] 球队 {tid}")
        
        # 随机延迟5-10秒
        delay = random.uniform(5, 10)
        time.sleep(delay)
        
        # 获取数据
        url = TEAM_DETAIL_URL.format(team_id=tid)
        js_content = fetch_with_retry(url)
        
        if not js_content:
            print(f"    ✗ 获取失败")
            continue
        
        # 解析
        result = parse_team_detail_simple(js_content, tid)
        
        if result["detail"]:
            # 保存
            with open(f'data/team_{tid}.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"    ✓ 保存成功")
        else:
            print(f"    ✗ 解析失败")
        
        # 每完成5个球队后休息
        if (i + 1) % 5 == 0:
            print(f"    休息30秒...")
            time.sleep(30)

if __name__ == "__main__":
    crawl_all_teams()