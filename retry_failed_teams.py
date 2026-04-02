#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试失败的球队 - 分批次进行
"""

import json
import os
import sys
import time
from datetime import datetime
from team_crawler import crawl_team

def main():
    batch_size = 50  # 每批处理50个球队
    delay_between_requests = 12  # 每个请求间隔12秒
    delay_between_batches = 300  # 每批之间等待5分钟
    
    # 读取所有球队ID
    with open('data/all_team_ids.json', 'r') as f:
        all_team_ids = json.load(f)
    
    # 读取已完成的球队
    completed = []
    if os.path.exists('data/completed_teams.json'):
        with open('data/completed_teams.json', 'r') as f:
            completed = json.load(f)
    
    # 计算失败的球队
    failed_teams = [tid for tid in all_team_ids if tid not in completed]
    
    print(f"总共需要更新 {len(all_team_ids)} 个球队")
    print(f"已完成: {len(completed)} 个")
    print(f"失败待重试: {len(failed_teams)} 个")
    
    if len(failed_teams) == 0:
        print("所有球队数据已完整!")
        return True
    
    # 分批处理
    total_batches = (len(failed_teams) // batch_size) + 1
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(failed_teams))
        batch_teams = failed_teams[start_idx:end_idx]
        
        print(f"\n{'='*60}")
        print(f"开始批次 {batch_num + 1}/{total_batches} ({len(batch_teams)} 个球队)")
        print(f"球队ID范围: {batch_teams[0]} - {batch_teams[-1]}")
        print(f"{'='*60}")
        
        success_count = 0
        batch_failed = []
        
        for i, tid in enumerate(batch_teams, 1):
            print(f"\n[{i}/{len(batch_teams)}] 正在更新球队 {tid}...")
            
            try:
                result = crawl_team(str(tid))
                
                if result and result.get('detail'):
                    success_count += 1
                    completed.append(tid)
                    print(f"  成功: {result['detail'].get('name_cn', '未知')}")
                    
                    # 每10个保存一次
                    if i % 10 == 0:
                        with open('data/completed_teams.json', 'w') as f:
                            json.dump(completed, f, indent=2)
                else:
                    batch_failed.append(tid)
                    print(f"  失败: 数据不完整或WAF拦截")
                    
            except Exception as e:
                batch_failed.append(tid)
                print(f"  失败: {e}")
            
            # 请求间隔
            if i < len(batch_teams):
                time.sleep(delay_between_requests)
        
        # 保存进度
        with open('data/completed_teams.json', 'w') as f:
            json.dump(completed, f, indent=2)
        
        print(f"\n批次 {batch_num + 1} 完成: {success_count}/{len(batch_teams)} 成功")
        
        # 如果还有更多批次，等待一段时间
        if batch_num + 1 < total_batches and len(batch_failed) > 0:
            print(f"等待 {delay_between_batches} 秒后继续下一批...")
            time.sleep(delay_between_batches)
    
    print(f"\n{'='*60}")
    print(f"全部完成!")
    print(f"总成功: {len(completed)}/{len(all_team_ids)}")
    
    # 更新失败列表
    final_failed = [tid for tid in all_team_ids if tid not in completed]
    if final_failed:
        print(f"仍失败: {len(final_failed)} 个球队")
        with open('data/failed_teams.json', 'w') as f:
            json.dump(final_failed, f, indent=2)
    else:
        print("所有球队数据已完整!")
    
    return len(final_failed) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)