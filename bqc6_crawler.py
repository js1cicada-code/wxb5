#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6场半全场 数据爬虫模块

本模块用于从500.com网站爬取"6场半全场"彩票数据，包括：
- 当前期次信息（期号、截止时间）
- 比赛详情（主队、客队、联赛、比赛时间）
- 赔率数据（胜、平、负三种结果对应的赔率）
- 历史期次数据

主要功能：
1. fetch_bqc6_data(): 获取指定期次的6场半全场数据
2. fetch_all_periods(): 获取所有期次的完整数据
3. save_data(): 将爬取的数据保存为JSON文件

使用方法：
    python bqc6_crawler.py

输出文件：
    dist/bqc6_data.json
"""

import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 数据输出文件路径
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data', 'bqc6_data.json')

# HTTP请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def fetch_bqc6_data(expect=None):
    """
    从500.com获取6场半全场数据
    
    该函数通过发送HTTP请求访问500.com的6场半全场页面，
    解析HTML内容提取期次信息、比赛列表和赔率数据。
    
    参数:
        expect (str, optional): 期次号码。如果为None，则获取当前最新期次；
                               如果指定期次号，则获取对应历史期次的数据。
                               例如: '24001' 表示2024年第001期
    
    返回值:
        dict | None: 成功时返回包含以下字段的字典：
            - updateTime (str): 数据更新时间，格式为 'YYYY-MM-DD HH:MM:SS'
            - period (str): 当前期号
            - deadline (str): 投注截止时间，格式为 'MM-DD HH:MM'
            - matches (list): 比赛列表，最多6场比赛，每场比赛包含：
                - id (str): 比赛序号 (1-6)
                - matchNum (str): 比赛序号 (同id)
                - home (str): 主队名称
                - away (str): 客队名称
                - league (str): 联赛名称
                - time (str): 比赛时间
                - odds3 (float): 主胜赔率
                - odds1 (float): 平局赔率
                - odds0 (float): 客胜赔率
            - periods (list, optional): 可选期次列表
        失败时返回 None
    
    异常:
        函数内部捕获所有异常并打印错误信息，不会向外抛出异常
    
    示例:
        >>> data = fetch_bqc6_data()          # 获取最新期次
        >>> data = fetch_bqc6_data('24001')   # 获取指定期次
    """
    # 根据是否指定期次构建URL
    url = 'https://trade.500.com/bqc/'
    if expect:
        url = f'https://trade.500.com/bqc/?expect={expect}'
    
    try:
        # 发送HTTP GET请求获取页面内容
        response = requests.get(url, headers=headers, timeout=15)
        # 500.com使用gb2312编码，需要手动设置
        response.encoding = 'gb2312'
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 初始化需要提取的数据变量
        period = None       # 当前期号
        deadline = None     # 投注截止时间
        periods_data = []   # 所有可选期次列表
        
        # 尝试从expect输入框获取期号（指定期次页面）
        expect_input = soup.find('input', id='expect')
        if expect_input:
            period = expect_input.get('value')
        
        # 如果expect输入框不存在，尝试从curexp输入框获取（默认页面）
        if not period:
            curexp_input = soup.find('input', id='curexp')
            if curexp_input:
                period = curexp_input.get('value')
        
        # 提取投注截止时间
        endtime_span = soup.find('span', class_='zcfilter-endtime')
        if endtime_span:
            endtime_text = endtime_span.get_text(strip=True)
            # 使用正则表达式匹配时间格式：MM-DD HH:MM
            match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', endtime_text)
            if match:
                deadline = match.group(1)
        
        # 提取所有可选期次列表（用于历史期次查询）
        qih_list = soup.find('ul', class_='qih-list')
        if qih_list:
            for li in qih_list.find_all('li'):
                exp = li.get('data-expect', '')  # 期号数据属性
                text = li.get_text(strip=True)    # 显示文本
                if exp:
                    periods_data.append({'period': exp, 'label': text})
        
        # 提取比赛列表数据
        matches = []
        table = soup.find('table', id='vsTable')
        if table:
            # 遍历所有比赛行，最多取前6场（6场半全场）
            for i, tr in enumerate(table.find_all('tr', class_='bet-tb-tr')):
                if i >= 6:
                    break
                
                # 初始化比赛数据结构
                match = {'id': str(i + 1), 'matchNum': str(i + 1)}
                
                # 从data-vs属性提取主客队名称，格式为 "主队vs客队"
                vs_data = tr.get('data-vs', '')
                if vs_data and 'vs' in str(vs_data):
                    parts = str(vs_data).split('vs')
                    if len(parts) == 2:
                        match['home'] = parts[0].strip()  # 主队名称
                        match['away'] = parts[1].strip()  # 客队名称
                
                # 从data-bjpl属性提取赔率数据，格式为 "主胜赔率,平局赔率,客胜赔率,..."
                bjpl = tr.get('data-bjpl', '')
                if bjpl:
                    odds_parts = str(bjpl).split(',')
                    if len(odds_parts) >= 3:
                        try:
                            match['odds3'] = float(odds_parts[0])  # 主胜赔率（3表示主队得3分）
                            match['odds1'] = float(odds_parts[1])  # 平局赔率（1表示各得1分）
                            match['odds0'] = float(odds_parts[2])  # 客胜赔率（0表示主队得0分）
                        except:
                            pass
                
                # 从表格单元格提取联赛名称和比赛时间
                tds = tr.find_all('td')
                if len(tds) >= 3:
                    match['league'] = tds[1].get_text(strip=True)  # 第2列：联赛名称
                    match['time'] = tds[2].get_text(strip=True)    # 第3列：比赛时间
                
                # 只有成功提取到主客队名称才添加到比赛列表
                if match.get('home') and match.get('away'):
                    matches.append(match)
        
        # 构建返回结果
        if matches and period:
            result = {
                'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 数据更新时间戳
                'period': period,           # 当前期号
                'deadline': deadline or '',  # 投注截止时间
                'matches': matches           # 比赛列表
            }
            # 如果存在可选期次列表，添加到结果中
            if periods_data:
                result['periods'] = periods_data
            return result
            
    except Exception as e:
        # 捕获所有异常并打印错误信息
        print(f"获取数据失败: {e}")
    
    return None


def fetch_all_periods():
    """
    获取所有期次的完整数据
    
    该函数首先获取主页面的当前期次数据，然后根据期次列表
    依次获取其他历史期次的数据（最多5期），最终整合为
    包含多期数据的完整数据结构。
    
    参数:
        无参数
    
    返回值:
        dict | None: 成功时返回包含以下字段的字典：
            - updateTime (str): 数据更新时间
            - current (str): 当前期号
            - periods (dict): 各期次数据，键为期号，值为该期数据：
                - period (str): 期号
                - deadline (str): 投注截止时间
                - matches (list): 比赛列表
            - periods_list (list, optional): 期次选择列表
        失败时返回 None
    
    示例:
        >>> all_data = fetch_all_periods()
        >>> print(all_data['current'])  # 当前期号
        >>> print(all_data['periods'].keys())  # 所有期号
    """
    # 首先获取主页面数据，从中提取期次列表
    main_data = fetch_bqc6_data()
    if not main_data:
        return None
    
    # 初始化完整数据结构
    all_data = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 数据更新时间
        'current': main_data['period'],  # 当前期号
        'periods': {}                    # 各期次数据字典
    }
    
    # 将当前期次数据保存到结果中
    all_data['periods'][main_data['period']] = {
        'period': main_data['period'],
        'deadline': main_data.get('deadline', ''),
        'matches': main_data['matches']
    }
    
    # 获取其他历史期次数据
    if main_data.get('periods'):
        periods_list = main_data['periods'][:5]  # 限制最多获取5期，避免请求过多
        for p in periods_list:
            exp = p.get('period')
            # 跳过当前期次（已经获取过了）
            if exp and exp != main_data['period']:
                print(f"获取期次 {exp}...")
                data = fetch_bqc6_data(exp)
                if data and data.get('matches'):
                    all_data['periods'][exp] = {
                        'period': data['period'],
                        'deadline': data.get('deadline', ''),
                        'matches': data['matches']
                    }
    
    # 将期次选择列表添加到结果中（用于前端展示选择器）
    if main_data.get('periods'):
        all_data['periods_list'] = main_data['periods']
    
    return all_data


def save_data(data):
    """
    将爬取的数据保存到多个位置
    
    将字典格式的数据序列化为JSON格式并写入多个文件。
    如果目标目录不存在，会自动创建。
    
    参数:
        data (dict): 要保存的数据字典，通常来自 fetch_all_periods() 的返回值
    
    返回值:
        bool: 保存成功返回 True，数据无效或保存失败返回 False
    """
    # 数据有效性检查
    if not data:
        print("跳过保存：数据无效")
        return False
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'bqc6_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'bqc6_data.json'),
        os.path.join(base_dir, 'data', 'bqc6_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")
    return True


if __name__ == '__main__':
    """
    程序入口点
    
    执行流程：
    1. 打印启动信息
    2. 获取所有期次数据
    3. 保存数据到文件
    4. 打印执行结果统计
    """
    print("6场半全场 数据爬虫启动")
    
    # 获取所有期次数据
    data = fetch_all_periods()
    
    if data:
        # 保存数据到文件
        save_data(data)
        # 打印执行结果统计
        print(f"当前期号: {data.get('current')}")
        print(f"期次数量: {len(data.get('periods', {}))}")
    else:
        print("获取数据失败")