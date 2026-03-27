#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞彩足球单关状态爬虫模块
========================

功能说明：
    从中国体育彩票官方网站（竞彩网）获取竞彩足球比赛的单关状态数据。
    单关是指可以单独投注一场比赛的玩法，而非必须多场串关。

主要功能：
    1. 获取当前可投注的足球比赛列表
    2. 解析每场比赛各玩法的单关状态
    3. 生成结构化数据供前端使用
    4. 保存数据到JSON文件

玩法代码说明：
    - SPF: 胜平负
    - RQSPF: 让球胜平负
    - BF: 比分
    - ZJQ: 总进球
    - BQC: 半全场

使用示例：
    python single_pass_crawler.py

输出文件：
    - single_pass_status.json: 完整的比赛数据
    - dist/single_pass.json: 前端精简数据

作者: 自动生成
更新时间: 2024
"""

import requests
import json
import time
from datetime import datetime


class SinglePassCrawler:
    """
    竞彩足球单关状态爬虫类
    
    该类负责从竞彩网API获取足球比赛数据，并解析出各玩法的单关状态。
    使用requests.Session保持会话，提高请求效率。
    
    属性：
        api_url (str): 竞彩网比赛数据API地址
        headers (dict): HTTP请求头信息
        session (requests.Session): 请求会话对象
    
    使用示例：
        crawler = SinglePassCrawler()
        data = crawler.get_single_pass_status()
    """
    
    def __init__(self):
        """
        初始化爬虫实例
        
        设置API地址、请求头和会话对象。
        使用Session对象可以保持连接，提高多次请求的效率。
        """
        # 竞彩网比赛列表API地址
        self.api_url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry"
        
        # 设置HTTP请求头，模拟浏览器访问
        self.headers = {
            # 用户代理，模拟Chrome浏览器
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # 来源页面，部分API会验证来源
            'Referer': 'https://www.sporttery.cn/jc/zqszsc/',
            # 接受的响应类型
            'Accept': 'application/json, text/plain, */*',
        }
        
        # 创建Session对象，保持会话状态
        self.session = requests.Session()
        # 将请求头应用到会话
        self.session.headers.update(self.headers)
    
    def get_single_pass_status(self):
        """
        获取所有比赛的单关状态
        
        向竞彩网API发送请求，获取当前可投注的足球比赛列表及其单关状态。
        
        参数：
            无参数
        
        返回值：
            dict | None: 返回解析后的比赛数据字典，包含以下字段：
                - updateTime (str): 数据更新时间
                - matches (list): 比赛列表，每个元素为一场比赛的信息
            如果请求失败或解析出错，返回None
        
        异常处理：
            捕获所有异常并打印错误信息，返回None
        """
        try:
            # 构建请求参数，clientCode为客户端类型代码
            params = {'clientCode': '3001'}
            
            # 发送GET请求，设置10秒超时
            response = self.session.get(self.api_url, params=params, timeout=10)
            
            # 检查HTTP状态码，200表示请求成功
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                
                # 检查API返回的业务状态
                # success字段表示接口调用是否成功
                # value字段包含实际的比赛数据
                if data.get('success') and data.get('value'):
                    # 调用解析方法处理数据
                    return self.parse_single_pass_data(data['value'])
                else:
                    # API返回业务错误，打印错误信息
                    print(f"API返回错误: {data.get('errorMessage', '未知错误')}")
                    return None
            else:
                # HTTP请求失败，打印状态码
                print(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            # 捕获并打印所有异常
            print(f"获取单关状态失败: {e}")
            return None
    
    def parse_single_pass_data(self, value):
        """
        解析单关状态数据
        
        将API返回的原始数据解析为结构化的比赛信息，提取每场比赛
        各玩法的单关状态。
        
        参数：
            value (dict): API返回的value字段，包含比赛信息列表
        
        返回值：
            dict: 解析后的数据字典，包含以下字段：
                - updateTime (str): 数据更新时间，格式为 'YYYY-MM-DD HH:MM:SS'
                - matches (list): 比赛列表，每场比赛包含：
                    - matchId: 比赛唯一标识
                    - matchNumStr: 比赛编号（如"周四001"）
                    - home: 主队简称
                    - away: 客队简称
                    - league: 联赛简称
                    - matchTime: 比赛时间
                    - matchDate: 比赛日期
                    - singlePass (dict): 各玩法的单关状态
        """
        # 初始化结果字典
        result = {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 记录数据抓取时间
            'matches': []  # 比赛列表
        }
        
        # 检查是否存在比赛数据
        if not value.get('matchInfoList'):
            return result
        
        # 遍历每日的比赛数据（API按日期分组返回）
        for day_match in value['matchInfoList']:
            # 检查该日期下是否有比赛
            if not day_match.get('subMatchList'):
                continue
            
            # 遍历该日期下的每场比赛
            for match in day_match['subMatchList']:
                # 提取比赛基本信息
                match_info = {
                    'matchId': match.get('matchId'),              # 比赛唯一ID
                    'matchNumStr': match.get('matchNumStr'),      # 比赛编号（如"周四001"）
                    'home': match.get('homeTeamAbbName'),         # 主队简称
                    'away': match.get('awayTeamAbbName'),         # 客队简称
                    'league': match.get('leagueAbbName'),         # 联赛简称
                    'matchTime': match.get('matchTime'),          # 比赛具体时间
                    'matchDate': match.get('matchDate'),          # 比赛日期
                    'singlePass': {}  # 各玩法单关状态字典
                }
                
                # 解析各玩法的投注池信息
                if match.get('poolList'):
                    for pool in match['poolList']:
                        # poolCode: 玩法代码（SPF=胜平负，RQSPF=让球胜平负等）
                        pool_code = pool.get('poolCode')
                        
                        # cbtSingle: 是否支持单关投注的标志位（1=支持）
                        cbt_single = pool.get('cbtSingle', 0)
                        
                        # cbtValue: 该玩法是否开放的标志位（1=开放）
                        cbt_value = pool.get('cbtValue', 0)
                        
                        # poolStatus: 玩法状态（如"ONSALE"表示在售）
                        pool_status = pool.get('poolStatus', '')
                        
                        # 判断是否真正支持单关
                        # 需要同时满足：玩法开放（cbt_value=1）且支持单关（cbt_single=1）
                        is_single_pass = (cbt_value == 1 and cbt_single == 1)
                        
                        # 将该玩法的状态存入字典
                        match_info['singlePass'][pool_code] = {
                            'available': cbt_value == 1,     # 该玩法是否开放
                            'singlePass': is_single_pass,    # 是否支持单关投注
                            'status': pool_status            # 玩法状态
                        }
                
                # 将解析后的比赛信息添加到结果列表
                result['matches'].append(match_info)
        
        return result
    
    def save_to_json(self, data, filename='single_pass_status.json'):
        """
        保存数据到JSON文件
        
        将解析后的数据保存为JSON格式文件，使用UTF-8编码确保中文正常显示。
        
        参数：
            data (dict): 要保存的数据字典
            filename (str): 保存的文件名，默认为 'single_pass_status.json'
        
        返回值：
            bool: 保存成功返回True，失败返回False
        """
        try:
            # 使用UTF-8编码写入文件，ensure_ascii=False保留中文字符
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, ensure_ascii=False, indent=2, fp=f)
            print(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def generate_frontend_data(self, data):
        """
        生成前端可用的数据格式
        
        将完整的比赛数据转换为前端需要的精简格式，
        以比赛ID为键，便于快速查找。
        
        参数：
            data (dict): parse_single_pass_data方法返回的完整数据
        
        返回值：
            dict: 前端数据字典，格式为：
                {
                    "比赛ID": {
                        "matchNumStr": "比赛编号",
                        "home": "主队",
                        "away": "客队",
                        "singlePass": {...}
                    },
                    ...
                }
            如果输入数据为空，返回空字典{}
        """
        # 检查输入数据是否有效
        if not data or not data.get('matches'):
            return {}
        
        frontend_data = {}
        
        # 遍历所有比赛，构建以ID为键的字典
        for match in data['matches']:
            # 将比赛ID转为字符串作为键
            match_id = str(match['matchId'])
            
            # 只保留前端需要的字段，减少数据传输量
            frontend_data[match_id] = {
                'matchNumStr': match['matchNumStr'],  # 比赛编号
                'home': match['home'],                # 主队
                'away': match['away'],                # 客队
                'singlePass': match['singlePass']     # 单关状态
            }
        
        return frontend_data


def main():
    """
    主函数 - 程序入口
    
    执行流程：
        1. 创建爬虫实例
        2. 获取单关状态数据
        3. 保存完整数据到JSON文件
        4. 生成并保存前端精简数据
        5. 打印统计信息
    
    输出：
        - single_pass_status.json: 完整数据文件
        - dist/single_pass.json: 前端数据文件
        - 控制台输出统计信息
    """
    # 打印程序标题
    print("=" * 60)
    print("竞彩足球单关状态爬虫")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = SinglePassCrawler()
    
    # 获取单关状态数据
    print("\n正在获取单关状态数据...")
    data = crawler.get_single_pass_status()
    
    if data:
        # 数据获取成功，打印基本信息
        print(f"\n成功获取 {len(data['matches'])} 场比赛数据")
        print(f"更新时间: {data['updateTime']}")
        
        # 保存完整数据
        crawler.save_to_json(data, 'single_pass_status.json')
        
        # 生成并保存前端数据
        frontend_data = crawler.generate_frontend_data(data)
        crawler.save_to_json(frontend_data, 'dist/single_pass.json')
        
        # 统计并打印单关信息
        print("\n单关状态统计:")
        single_pass_count = 0  # 支持单关的比赛计数
        
        for match in data['matches']:
            # 检查是否有任一玩法支持单关
            has_single = any(sp['singlePass'] for sp in match['singlePass'].values())
            
            if has_single:
                single_pass_count += 1
                
                # 获取支持单关的玩法代码列表
                sp_plays = [code for code, sp in match['singlePass'].items() if sp['singlePass']]
                
                # 打印比赛信息和单关玩法
                print(f"  {match['matchNumStr']} {match['home']} VS {match['away']}")
                print(f"    单关玩法: {', '.join(sp_plays)}")
        
        # 打印统计结果
        print(f"\n总计: {single_pass_count} 场比赛支持单关投注")
    else:
        # 数据获取失败
        print("\n获取数据失败")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()