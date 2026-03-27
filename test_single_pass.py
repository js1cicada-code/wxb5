#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单关状态功能测试脚本
"""

import requests
import json

def test_api():
    """测试API是否可访问"""
    print("1. 测试单关状态API...")
    
    url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.sporttery.cn/jc/zqszsc/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                matches = data['value']['matchInfoList'][0]['subMatchList']
                print(f"   ✅ API正常，获取到 {len(matches)} 场比赛")
                
                # 显示第一场比赛的单关状态
                first_match = matches[0]
                print(f"\n   第一场比赛: {first_match['matchNumStr']} {first_match['homeTeamAbbName']} VS {first_match['awayTeamAbbName']}")
                print("   单关状态:")
                for pool in first_match.get('poolList', []):
                    status = "✓ 可单关" if (pool['cbtValue'] == 1 and pool['cbtSingle'] == 1) else "✗ 不可单关"
                    print(f"      {pool['poolCode']}: {status}")
                return True
            else:
                print("   ❌ API返回失败")
                return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def test_crawler():
    """测试爬虫脚本"""
    print("\n2. 测试爬虫脚本...")
    
    try:
        from single_pass_crawler import SinglePassCrawler
        crawler = SinglePassCrawler()
        data = crawler.get_single_pass_status()
        
        if data:
            print(f"   ✅ 爬虫正常，获取 {len(data['matches'])} 场比赛")
            
            # 统计单关数量
            single_count = sum(1 for m in data['matches'] 
                             if any(sp['singlePass'] for sp in m['singlePass'].values()))
            print(f"   支持单关: {single_count} 场")
            return True
        else:
            print("   ❌ 爬虫返回空数据")
            return False
    except Exception as e:
        print(f"   ❌ 爬虫错误: {e}")
        return False

def test_data_files():
    """测试数据文件"""
    print("\n3. 测试数据文件...")
    
    files = ['single_pass_status.json', 'dist/single_pass.json']
    
    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   ✅ {filename} 存在且有效")
        except FileNotFoundError:
            print(f"   ⚠️  {filename} 不存在（运行爬虫后会生成）")
        except Exception as e:
            print(f"   ❌ {filename} 错误: {e}")

def test_frontend_code():
    """测试前端代码"""
    print("\n4. 测试前端代码...")
    
    checks = [
        ('fetchSinglePassStatus函数', 'fetchSinglePassStatus'),
        ('singlePassStatus变量', 'singlePassStatus'),
        ('isSinglePassAvailable函数', 'isSinglePassAvailable'),
        ('getSinglePassLabel函数', 'getSinglePassLabel')
    ]
    
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        for name, keyword in checks:
            if keyword in content:
                print(f"   ✅ {name} 已实现")
            else:
                print(f"   ❌ {name} 未找到")
                
        return True
    except Exception as e:
        print(f"   ❌ 检查错误: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("竞彩足球单关状态功能测试")
    print("=" * 60)
    
    results = []
    results.append(test_api())
    results.append(test_crawler())
    test_data_files()
    results.append(test_frontend_code())
    
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    if all(results):
        print("✅ 所有测试通过！")
        print("\n使用说明:")
        print("1. 运行爬虫: python3 single_pass_crawler.py")
        print("2. 启动服务: npm run dev")
        print("3. 访问页面查看单关状态标识")
    else:
        print("⚠️  部分测试未通过，请检查上述错误信息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()