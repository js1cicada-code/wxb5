#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩网API数据获取
"""

import requests
import json

def test_api():
    """测试竞彩网API"""
    
    # 竞彩网API接口
    api_urls = [
        # 胜平负赔率
        "https://webapi.sporttery.cn/api/lottery/football/get_odds/?_t=0.123",
        # 篮球赔率
        "https://webapi.sporttery.cn/api/lottery/basketball/get_odds/?_t=0.123",
        # 比分赔率
        "https://webapi.sporttery.cn/api/lottery/football/score_odds/?_t=0.123",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.sporttery.cn/',
        'Accept': 'application/json, text/plain, */*',
    }
    
    for url in api_urls:
        print(f"\n{'='*50}")
        print(f"尝试: {url}")
        print('='*50)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"内容长度: {len(response.text)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"JSON数据: {json.dumps(data, ensure_ascii=False)[:1000]}")
                except:
                    print(f"原始内容: {response.text[:500]}")
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api()
