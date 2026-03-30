#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资料库数据爬虫 - 从球探体育获取足球资料库数据
"""

import json
import re
import requests
from datetime import datetime

DATA_URL = "https://zq.titan007.com/jsData/infoHeader.js"
OUTPUT_FILE = "data/database_data.json"

REGION_MAP = {
    "0": "全部赛事",
    "1": "欧洲赛事", 
    "2": "美洲赛事",
    "3": "亚洲赛事",
    "4": "大洋洲",
    "5": "非洲赛事"
}

def fetch_data():
    """获取JS数据文件"""
    print(f"正在获取数据: {DATA_URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://zq.titan007.com/info/index_cn.htm'
    }
    response = requests.get(DATA_URL, headers=headers, timeout=30)
    response.encoding = 'utf-8'
    return response.text

def parse_js_data(js_content):
    """解析JS数据"""
    result = {
        "countries": [],
        "leagues": [],
        "hot_leagues": [],
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    hot_league_ids = [36, 31, 8, 34, 11, 60, 25, 192, 103, 15, 273, 37, 40, 9, 33, 5, 29]
    
    pattern = r'arr\[\d+\]\s*=\s*\["(InfoID_\d+)","([^"]+)","([^"]+)","(\d+)",\[(.*?)\]\];'
    matches = re.findall(pattern, js_content, re.DOTALL)
    
    for match in matches:
        country_id = match[0]
        country_name = match[1]
        country_img = match[2]
        region_type = match[3]
        leagues_str = match[4]
        
        leagues_data = []
        league_pattern = r'"(\d+),([^,]+),(\d+),(\d+)(,[^"]+)?"'
        league_matches = re.findall(league_pattern, leagues_str)
        
        for lm in league_matches:
            league_id = int(lm[0])
            league_name = lm[1]
            league_type = lm[2]
            is_sub = lm[3]
            seasons_str = lm[4].strip(',') if len(lm) > 4 else ""
            seasons = [s.strip() for s in seasons_str.split(',') if s.strip()]
            
            leagues_data.append({
                "id": league_id,
                "name": league_name,
                "type": "联赛" if league_type == "1" else "杯赛",
                "is_sub": is_sub == "1",
                "seasons": seasons,
                "country": country_name,
                "country_id": country_id
            })
            
            if league_id in hot_league_ids:
                result["hot_leagues"].append({
                    "id": league_id,
                    "name": league_name,
                    "country": country_name
                })
        
        result["countries"].append({
            "id": country_id,
            "name": country_name,
            "image": f"https://zq.titan007.com/{country_img}",
            "region": region_type,
            "region_name": REGION_MAP.get(region_type, "其他"),
            "leagues": leagues_data
        })
        
        result["leagues"].extend(leagues_data)
    
    result["hot_leagues"] = sorted(
        result["hot_leagues"], 
        key=lambda x: hot_league_ids.index(x["id"]) if x["id"] in hot_league_ids else 999
    )
    
    return result

def save_data(data):
    """保存数据到JSON文件"""
    import os
    os.makedirs("data", exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {OUTPUT_FILE}")
    print(f"共 {len(data['countries'])} 个国家/地区")
    print(f"共 {len(data['leagues'])} 个联赛/杯赛")

def main():
    try:
        js_content = fetch_data()
        data = parse_js_data(js_content)
        save_data(data)
        return data
    except Exception as e:
        print(f"爬取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()