#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传统足彩14场/任选9场 数据爬虫模块

本模块用于从500.com网站爬取传统足彩（14场胜负彩和任选9场）的比赛数据。
主要功能包括：
- 获取当前期次的比赛信息（球队、联赛、时间、赔率等）
- 支持获取历史期次数据
- 将数据保存为JSON格式文件

使用方法：
    直接运行：python ctzc_crawler.py
    作为模块导入：from ctzc_crawler import fetch_ctzc_data, fetch_all_periods

作者：自动生成
创建日期：2024
"""

import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# 数据输出文件路径
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data', 'ctzc_data.json')

# HTTP请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def fetch_ctzc_data(expect=None):
    """
    从500.com获取传统足彩数据
    
    从500.com网站爬取传统足彩（14场胜负彩）的比赛数据，包括比赛信息、
    球队名称、赔率等。支持获取指定期次或当前期次的数据。
    
    参数：
        expect (str, optional): 期次号，如 "2024001"。如果为None，则获取当前期次。
                                默认为None。
    
    返回值：
        dict | None: 成功时返回包含以下字段的字典：
            - updateTime (str): 数据更新时间，格式为 'YYYY-MM-DD HH:MM:SS'
            - period (str): 当前期次号
            - deadline (str): 投注截止时间，格式为 'MM-DD HH:MM'
            - matches (list): 比赛列表，最多14场比赛，每场比赛包含：
                - id (str): 比赛编号
                - matchNum (str): 比赛序号
                - league (str): 联赛名称
                - time (str): 比赛时间
                - home (str): 主队名称
                - away (str): 客队名称
                - odds3 (float): 主胜赔率
                - odds1 (float): 平局赔率
                - odds0 (float): 客胜赔率
            - periods (list, optional): 可选期次列表，每项包含 period 和 label
        如果获取失败，返回None。
    
    异常：
        函数内部捕获所有异常，不会向外抛出。
    
    示例：
        >>> data = fetch_ctzc_data()  # 获取当前期次
        >>> data = fetch_ctzc_data("2024001")  # 获取指定期次
    """
    # 500.com的传统足彩数据源URL列表
    urls = [
        'https://trade.500.com/sfc/',      # 胜负彩页面
        'https://trade.500.com/ctzc.php',  # 传统足彩页面
    ]
    
    # 遍历所有可能的URL，直到成功获取数据
    for url in urls:
        try:
            # 构建目标URL，如果指定期次则添加expect参数
            target_url = url
            if expect:
                # 根据URL是否已包含参数，选择正确的参数连接符
                target_url = url + ('?expect=' + expect if '?' not in url else '&expect=' + expect)
            
            # 发送HTTP GET请求，设置15秒超时
            response = requests.get(target_url, headers=headers, timeout=15)
            # 500.com使用gb2312编码，需要手动设置
            response.encoding = 'gb2312'
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 初始化数据容器
            matches = []       # 比赛列表
            period = None      # 当前期次号
            deadline = None    # 投注截止时间
            periods_data = []  # 可选期次列表
            
            # ==================== 提取期次信息 ====================
            # 从隐藏的input元素获取当前期次号
            expect_input = soup.find('input', id='expect')
            if expect_input:
                period = expect_input.get('value')
            
            # ==================== 提取截止时间 ====================
            # 从页面上的截止时间显示区域提取
            endtime_span = soup.find('span', class_='zcfilter-endtime')
            if endtime_span:
                endtime_text = endtime_span.get_text(strip=True)
                # 使用正则提取时间格式，如 "12-25 22:00"
                match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', endtime_text)
                if match:
                    deadline = match.group(1)
            
            # ==================== 提取多期信息 ====================
            # 获取页面上显示的可选期次列表
            qih_list = soup.find('ul', class_='qih-list')
            if qih_list:
                for li in qih_list.find_all('li'):
                    exp = li.get('data-expect', '')  # 期次号
                    text = li.get_text(strip=True)    # 显示文本
                    if exp:
                        periods_data.append({'period': exp, 'label': text})
            
            # ==================== 查找比赛数据表格 ====================
            # 首先尝试通过ID查找表格
            table = soup.find('table', id='vsTable')
            if not table:
                # 如果没有找到，遍历所有表格，寻找包含足够多行的表格
                tables = soup.find_all('table')
                for t in tables:
                    rows = t.find_all('tr')
                    # 传统足彩有14场比赛，至少需要10行以上的表格
                    if len(rows) >= 10:
                        table = t
                        break
            
            # 如果没有找到合适的表格，尝试下一个URL
            if not table:
                continue
            
            # ==================== 提取比赛数据 ====================
            # 首先尝试通过class定位比赛行
            rows = table.find_all('tr', class_='bet-tb-tr')
            if not rows:
                # 如果没有class，则通过fid属性定位
                rows = table.find_all('tr', attrs={'fid': True})
            
            # 遍历每场比赛，最多提取14场
            for i, row in enumerate(rows):
                if i >= 14:  # 传统足彩最多14场比赛
                    break
                
                # 初始化比赛数据结构
                match = {'id': str(i + 1), 'matchNum': str(i + 1)}
                
                # ---------- 提取基本信息：编号、联赛、时间 ----------
                tds = row.find_all('td')
                if len(tds) >= 3:
                    match['id'] = tds[0].get_text(strip=True) or str(i + 1)   # 比赛编号
                    match['matchNum'] = match['id']
                    match['league'] = tds[1].get_text(strip=True) or '足球'   # 联赛名称
                    match['time'] = tds[2].get_text(strip=True) or ''          # 开赛时间
                
                # ---------- 提取球队信息 ----------
                # 从data-vs属性获取主客队信息，格式如 "曼联vs利物浦"
                vs_data = row.get('data-vs', '')
                if vs_data and 'vs' in str(vs_data):
                    parts = str(vs_data).split('vs')
                    if len(parts) == 2:
                        match['home'] = parts[0].strip()  # 主队
                        match['away'] = parts[1].strip()  # 客队
                
                # ---------- 提取赔率信息 ----------
                # 从data-bjpl属性获取赔率，格式如 "2.5,3.2,2.8"（主胜,平,客胜）
                bjpl = row.get('data-bjpl', '')
                if bjpl:
                    odds_parts = str(bjpl).split(',')
                    if len(odds_parts) >= 3:
                        try:
                            # 赔率分别对应：主胜(3)、平(1)、客胜(0)
                            match['odds3'] = float(odds_parts[0])  # 主胜赔率
                            match['odds1'] = float(odds_parts[1])  # 平局赔率
                            match['odds0'] = float(odds_parts[2])  # 客胜赔率
                        except:
                            # 赔率转换失败时跳过
                            pass
                
                # 只有成功获取到球队信息才添加到列表
                if match.get('home') and match.get('away'):
                    matches.append(match)
            
            # ==================== 组装返回结果 ====================
            # 只有成功获取到期次和比赛数据才返回
            if matches and period:
                result = {
                    'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 当前时间
                    'period': period,                    # 期次号
                    'deadline': deadline or '',          # 截止时间
                    'matches': matches[:14]              # 比赛列表（限制14场）
                }
                # 如果有期次列表数据，一并返回
                if periods_data:
                    result['periods'] = periods_data
                return result
                
        except Exception as e:
            # 捕获异常，打印错误信息后尝试下一个URL
            print(f"从 {url} 获取数据失败: {e}")
            continue
    
    # 所有URL都尝试失败，返回None
    return None


def fetch_all_periods():
    """
    获取所有期次数据
    
    获取当前期次和最近几期的传统足彩数据。首先获取当前期次，
    然后从页面中提取最近5期的期次号，分别获取这些期次的数据。
    
    参数：
        无
    
    返回值：
        dict | None: 成功时返回包含以下字段的字典：
            - updateTime (str): 数据更新时间
            - current (str): 当前期次号
            - periods (dict): 期次数据字典，键为期次号，值为期次详细数据：
                - period (str): 期次号
                - deadline (str): 截止时间
                - matches (list): 比赛列表
            - periods_list (list, optional): 可选期次列表
        如果获取失败，返回None。
    
    示例：
        >>> all_data = fetch_all_periods()
        >>> print(all_data['current'])  # 当前期次号
        >>> print(all_data['periods'].keys())  # 所有已获取的期次
    """
    # 首先获取当前期次的数据
    main_data = fetch_ctzc_data()
    if not main_data:
        return None
    
    # 初始化返回数据结构
    all_data = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 更新时间
        'current': main_data['period'],      # 当前期次
        'periods': {}                         # 所有期次数据
    }
    
    # 将当前期次数据添加到结果中
    all_data['periods'][main_data['period']] = {
        'period': main_data['period'],
        'deadline': main_data.get('deadline', ''),
        'matches': main_data['matches']
    }
    
    # ==================== 获取历史期次数据 ====================
    # 如果有期次列表，获取最近5期的数据
    if main_data.get('periods'):
        # 限制最多获取5期历史数据，避免请求过多
        periods_list = main_data['periods'][:5]
        for p in periods_list:
            exp = p.get('period')
            # 跳过当前期次（已经获取过）
            if exp and exp != main_data['period']:
                print(f"获取期次 {exp}...")
                # 获取指定期次的数据
                data = fetch_ctzc_data(exp)
                if data and data.get('matches'):
                    all_data['periods'][exp] = {
                        'period': data['period'],
                        'deadline': data.get('deadline', ''),
                        'matches': data['matches']
                    }
    
    # 将期次列表信息添加到结果中，便于前端显示选择
    if main_data.get('periods'):
        all_data['periods_list'] = main_data['periods']
    
    return all_data


def save_data(data):
    """
    保存数据到多个位置
    
    将爬取的数据保存到dist/、dist/data/、data/三个位置。
    
    参数：
        data (dict): 要保存的数据字典，包含期次、比赛等信息。
    
    返回值：
        bool: 保存成功返回True，失败或数据无效返回False
    """
    # 验证数据有效性
    if not data:
        print("跳过保存：数据无效")
        return False
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'ctzc_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'ctzc_data.json'),
        os.path.join(base_dir, 'data', 'ctzc_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")
    return True


# ==================== 程序入口 ====================
if __name__ == '__main__':
    print("传统足彩14场/任选9场 数据爬虫启动")
    
    # 获取所有期次数据
    data = fetch_all_periods()
    
    if data:
        # 保存数据到文件
        save_data(data)
        # 打印摘要信息
        print(f"当前期号: {data.get('current')}")
        print(f"期次数量: {len(data.get('periods', {}))}")
    else:
        print("获取数据失败")