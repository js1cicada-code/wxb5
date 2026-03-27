#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩网数据爬虫
定时抓取竞彩网足球比赛数据
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time

class JJCrawler:
    def __init__(self):
        self.base_url = "https://www.sporttery.cn/jc/jsq/zqspf/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.sporttery.cn/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_page(self):
        """获取竞彩网页面"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"获取页面失败: {e}")
            return None

    def parse_matches(self, html):
        """解析比赛数据"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        matches = []

        # 查找所有比赛行
        # 竞彩网的数据在特定的表格或div中
        content = soup.find('div', class_='content')
        if not content:
            # 尝试其他方式查找
            content = soup

        # 查找所有包含比赛信息的元素
        text = str(soup)
        
        # 使用正则提取比赛数据
        # 格式: 周一001荷乙03-1703:00[荷乙16]海尔蒙特 VS 坎布尔[荷乙2]
        date_pattern = r'(周[一二三四五六日])(\d{6})'
        match_pattern = r'(\d{3})([^VS]+)VS([^[]+)\[([^\]]+)\]'
        odds_pattern = r'(\d+\.\d+|\d+)'

        # 简化解析 - 提取关键信息
        # 查找所有比赛编号和赔率信息
        # 这里需要根据实际页面结构调整

        # 尝试提取表格数据
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    cell_text = ' '.join([c.get_text(strip=True) for c in cells])
                    if 'VS' in cell_text and ('胜' in cell_text or '胜' in cell_text):
                        print(f"找到比赛行: {cell_text[:100]}")

        # 返回解析结果
        return matches

    def get_odds_data(self):
        """尝试获取赔率数据"""
        # 竞彩网可能有API接口
        api_urls = [
            "https://www.sporttery.cn/wap/fb/odds/consts/?_t_t_t=0.123",
            "https://www.sporttery.cn/wap/fb/odds/getOdds",
        ]

        for url in api_urls:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"API返回数据: {json.dumps(data, ensure_ascii=False)[:500]}")
                        return data
                    except:
                        pass
            except Exception as e:
                print(f"尝试API {url} 失败: {e}")

        return None

    def fetch_all(self):
        """抓取所有数据"""
        print("=" * 50)
        print("开始抓取竞彩网数据...")
        print("=" * 50)

        # 尝试获取API数据
        print("\n1. 尝试获取API数据...")
        api_data = self.get_odds_data()
        
        # 尝试解析页面
        print("\n2. 尝试解析页面...")
        html = self.get_page()
        if html:
            print(f"页面长度: {len(html)} 字符")
            matches = self.parse_matches(html)
            print(f"解析到 {len(matches)} 场比赛")

        print("\n抓取完成!")
        return {
            'api_data': api_data,
            'html_length': len(html) if html else 0,
            'matches': []
        }

def test_simple():
    """简单测试 - 直接请求页面看看返回什么"""
    print("测试直接请求竞彩网...")
    
    url = "https://www.sporttery.cn/jc/jsq/zqspf/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)}")
        
        # 保存到文件查看
        with open('jj_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("页面已保存到 jj_page.html")
        
        # 打印部分内容
        print("\n页面内容片段:")
        print(response.text[:2000])
        
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_simple()
