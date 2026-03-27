#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4场总进球 数据爬虫模块

本模块用于从500彩票网爬取"4场总进球"彩票游戏的数据。
主要功能包括：
- 获取指定期次的比赛数据（主客队、联赛、比赛时间等）
- 批量获取多期历史数据
- 将数据保存为JSON格式文件

数据来源：https://trade.500.com/jqc/

作者: Auto-generated
创建日期: 2024
"""

import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 数据输出文件路径
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data', 'zjq4_data.json')

# HTTP请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def fetch_zjq4_data(expect=None):
    """
    从500.com获取4场总进球数据
    
    该函数访问500彩票网的4场总进球页面，解析HTML页面内容，
    提取期次信息、截止时间、比赛场次等数据。
    
    参数:
        expect (str, optional): 期次号，如 "24001"。
                               如果不传则获取最新期次数据。
                               默认为None。
    
    返回值:
        dict: 包含以下字段的字典：
            - updateTime (str): 数据更新时间，格式 'YYYY-MM-DD HH:MM:SS'
            - period (str): 当前期次号
            - deadline (str): 截止时间，格式 'MM-DD HH:MM'
            - matches (list): 比赛列表，每个元素包含：
                - id (str): 比赛序号 (1-4)
                - matchNum (str): 同id
                - home (str): 主队名称
                - away (str): 客队名称
                - league (str): 联赛名称
                - time (str): 比赛时间
            - periods (list, optional): 可选期次列表
        None: 如果获取或解析失败则返回None
    
    异常:
        函数内部捕获所有异常并打印错误信息，不会向外抛出异常
    """
    # 构建请求URL，如果有指定期次则添加expect参数
    url = 'https://trade.500.com/jqc/'
    if expect:
        url = f'https://trade.500.com/jqc/?expect={expect}'
    
    try:
        # 发送HTTP GET请求，设置超时时间为15秒
        response = requests.get(url, headers=headers, timeout=15)
        # 500彩票网使用gb2312编码，需要手动设置
        response.encoding = 'gb2312'
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 初始化变量存储解析结果
        period = None      # 当前期次号
        deadline = None    # 投注截止时间
        periods_data = []  # 所有可选期次列表
        
        # 从隐藏输入框中获取当前期次号
        expect_input = soup.find('input', id='expect')
        if expect_input:
            period = expect_input.get('value')
        
        # 从页面中提取截止时间
        endtime_span = soup.find('span', class_='zcfilter-endtime')
        if endtime_span:
            endtime_text = endtime_span.get_text(strip=True)
            # 使用正则表达式提取时间部分（格式：MM-DD HH:MM）
            match = re.search(r'(\d{2}-\d{2}\s+\d{2}:\d{2})', endtime_text)
            if match:
                deadline = match.group(1)
        
        # 获取所有可选期次的列表
        qih_list = soup.find('ul', class_='qih-list')
        if qih_list:
            for li in qih_list.find_all('li'):
                # data-expect属性包含期次号
                exp = li.get('data-expect', '')
                # 文本内容为期次显示名称
                text = li.get_text(strip=True)
                if exp:
                    periods_data.append({'period': exp, 'label': text})
        
        # 解析比赛数据表格
        matches = []
        table = soup.find('table', id='vsTable')
        if table:
            # 遍历表格中的每一行，最多取前4场（4场总进球只有4场比赛）
            for i, tr in enumerate(table.find_all('tr', class_='bet-tb-tr')):
                if i >= 4:
                    break
                
                # 构建比赛数据对象
                match = {'id': str(i + 1), 'matchNum': str(i + 1)}
                
                # 从data-vs属性中解析主客队名称（格式："主队 vs 客队"）
                vs_data = tr.get('data-vs', '')
                if vs_data and 'vs' in str(vs_data):
                    parts = str(vs_data).split('vs')
                    if len(parts) == 2:
                        match['home'] = parts[0].strip()  # 主队名称
                        match['away'] = parts[1].strip()  # 客队名称
                
                # 从表格单元格中获取联赛名称和比赛时间
                tds = tr.find_all('td')
                if len(tds) >= 3:
                    match['league'] = tds[1].get_text(strip=True)  # 第2列：联赛名称
                    match['time'] = tds[2].get_text(strip=True)    # 第3列：比赛时间
                
                # 只有当主客队都存在时才添加到比赛列表
                if match.get('home') and match.get('away'):
                    matches.append(match)
        
        # 如果成功获取到比赛数据和期次号，返回完整结果
        if matches and period:
            result = {
                'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period': period,
                'deadline': deadline or '',
                'matches': matches
            }
            # 如果存在期次列表，一并返回
            if periods_data:
                result['periods'] = periods_data
            return result
            
    except Exception as e:
        # 捕获并打印异常信息，返回None表示失败
        print(f"获取数据失败: {e}")
    
    return None


def fetch_all_periods():
    """
    获取所有期次数据
    
    该函数首先获取最新期次数据，然后批量获取历史期次数据（最多5期）。
    将所有数据整合成一个完整的数据结构返回。
    
    参数:
        无参数
    
    返回值:
        dict: 包含以下字段的字典：
            - updateTime (str): 数据更新时间
            - current (str): 当前期次号
            - periods (dict): 期次数据字典，键为期次号，值为：
                - period (str): 期次号
                - deadline (str): 截止时间
                - matches (list): 比赛列表
            - periods_list (list, optional): 所有可选期次的简要列表
        None: 如果获取主数据失败则返回None
    """
    # 首先获取最新一期的数据
    main_data = fetch_zjq4_data()
    if not main_data:
        return None
    
    # 初始化结果数据结构
    all_data = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'current': main_data['period'],  # 当前期次号
        'periods': {}                     # 存储所有期次数据的字典
    }
    
    # 将当前期次数据添加到结果中
    all_data['periods'][main_data['period']] = {
        'period': main_data['period'],
        'deadline': main_data.get('deadline', ''),
        'matches': main_data['matches']
    }
    
    # 如果存在其他可选期次，批量获取（限制最多5期，避免请求过多）
    if main_data.get('periods'):
        periods_list = main_data['periods'][:5]  # 取前5个期次
        for p in periods_list:
            exp = p.get('period')
            # 跳过当前期次（已经获取过了）
            if exp and exp != main_data['period']:
                print(f"获取期次 {exp}...")
                # 获取该期次的详细数据
                data = fetch_zjq4_data(exp)
                if data and data.get('matches'):
                    all_data['periods'][exp] = {
                        'period': data['period'],
                        'deadline': data.get('deadline', ''),
                        'matches': data['matches']
                    }
    
    # 将期次列表信息也保存到结果中，方便前端使用
    if main_data.get('periods'):
        all_data['periods_list'] = main_data['periods']
    
    return all_data


def save_data(data):
    """
    保存数据到多个位置
    
    将爬取的数据保存到dist/、dist/data/、data/三个位置。
    
    参数:
        data (dict): 要保存的数据字典，通常由fetch_all_periods()返回
    
    返回值:
        bool: 保存成功返回True，失败返回False
    """
    # 验证数据有效性
    if not data:
        print("跳过保存：数据无效")
        return False
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'zjq4_data.json'),
        os.path.join(base_dir, 'dist', 'data', 'zjq4_data.json'),
        os.path.join(base_dir, 'data', 'zjq4_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")
    return True


if __name__ == '__main__':
    """
    主程序入口
    
    执行流程：
    1. 启动爬虫并打印提示信息
    2. 获取所有期次数据
    3. 保存数据到文件
    4. 打印摘要信息
    """
    print("4场总进球 数据爬虫启动")
    
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