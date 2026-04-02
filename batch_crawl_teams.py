#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量爬取所有球队详情数据
"""

import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from team_crawler import crawl_team

def load_team_ids():
    """加载球队ID列表"""
    with open('data/all_team_ids.json', 'r') as f:
        return json.load(f)

def crawl_team_with_retry(team_id, max_retries=3):
    """带重试的爬取"""
    for attempt in range(max_retries):
        try:
            result = crawl_team(team_id)
            if result and result.get('detail'):
                return team_id, True, result
            else:
                print(f"  球队 {team_id} 数据不完整，尝试 {attempt+1}/{max_retries}")
        except Exception as e:
            print(f"  球队 {team_id} 爬取失败: {e}，尝试 {attempt+1}/{max_retries}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    return team_id, False, None

def batch_crawl_teams(max_workers=5, delay=1):
    """批量爬取球队数据"""
    team_ids = load_team_ids()
    total = len(team_ids)
    
    print(f"开始批量爬取 {total} 支球队数据...")
    print(f"并发数: {max_workers}, 请求间隔: {delay}秒")
    print("=" * 60)
    
    success_count = 0
    failed_teams = []
    
    # 使用线程池并发爬取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        for i, team_id in enumerate(team_ids):
            future = executor.submit(crawl_team_with_retry, team_id)
            futures[future] = team_id
            
            # 控制请求频率
            if (i + 1) % max_workers == 0:
                time.sleep(delay)
        
        # 等待所有任务完成
        completed = 0
        for future in as_completed(futures):
            team_id, success, result = future.result()
            completed += 1
            
            if success:
                success_count += 1
                team_name = result['detail'].get('name_cn', 'Unknown')
                print(f"[{completed}/{total}] ✓ 球队 {team_id} ({team_name})")
            else:
                failed_teams.append(team_id)
                print(f"[{completed}/{total}] ✗ 球队 {team_id} 失败")
    
    print("=" * 60)
    print(f"爬取完成!")
    print(f"成功: {success_count}/{total}")
    print(f"失败: {len(failed_teams)}/{total}")
    
    if failed_teams:
        print(f"\n失败球队ID: {failed_teams}")
        
        # 保存失败列表
        with open('data/failed_teams.json', 'w') as f:
            json.dump(failed_teams, f)
        print("失败列表已保存到 data/failed_teams.json")
    
    return success_count, failed_teams

def verify_data():
    """验证数据完整性"""
    team_ids = load_team_ids()
    
    print("\n验证数据完整性...")
    
    missing = []
    incomplete = []
    
    for team_id in team_ids:
        filepath = f'data/team_{team_id}.json'
        
        if not os.path.exists(filepath):
            missing.append(team_id)
            continue
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # 检查必要字段
        if not data.get('detail'):
            incomplete.append(team_id)
        elif not data['detail'].get('name_cn'):
            incomplete.append(team_id)
    
    print(f"缺失: {len(missing)} 支球队")
    print(f"不完整: {len(incomplete)} 支球队")
    
    if missing:
        print(f"缺失球队ID: {missing[:10]}...")
    if incomplete:
        print(f"不完整球队ID: {incomplete[:10]}...")
    
    return len(missing) == 0 and len(incomplete) == 0

if __name__ == "__main__":
    import sys
    
    # 解析参数
    max_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    # 批量爬取
    success, failed = batch_crawl_teams(max_workers=max_workers, delay=delay)
    
    # 验证数据
    is_valid = verify_data()
    
    # 返回状态码
    sys.exit(0 if is_valid else 1)