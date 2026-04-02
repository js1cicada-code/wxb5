#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新所有球队数据
"""

import json
import os
import sys
import time
from team_crawler import crawl_team

def main():
    # 读取所有球队ID
    with open('data/all_team_ids.json', 'r') as f:
        team_ids = json.load(f)
    
    # 检查已完成的球队
    completed = []
    if os.path.exists('data/completed_teams.json'):
        with open('data/completed_teams.json', 'r') as f:
            completed = json.load(f)
    
    print(f"总共需要更新 {len(team_ids)} 个球队")
    print(f"已完成: {len(completed)} 个")
    
    # 过滤已完成的
    remaining = [tid for tid in team_ids if tid not in completed]
    print(f"待更新: {len(remaining)} 个")
    
    success_count = len(completed)
    failed_teams = []
    
    for i, tid in enumerate(remaining, 1):
        print(f"\n[{i}/{len(remaining)}] 正在更新球队 {tid}...")
        
        try:
            result = crawl_team(str(tid))
            
            if result and result.get('detail'):
                success_count += 1
                completed.append(tid)
                print(f"  成功: {result['detail'].get('name_cn', '未知')}")
                
                # 每10个球队保存一次进度
                if i % 10 == 0:
                    with open('data/completed_teams.json', 'w') as f:
                        json.dump(completed, f, indent=2)
            else:
                failed_teams.append(tid)
                print(f"  失败: 数据不完整")
                
        except Exception as e:
            failed_teams.append(tid)
            print(f"  失败: {e}")
        
        # 添加延迟避免被封 (10-15秒随机)
        if i < len(remaining):
            delay = 10 + (i % 5)
            time.sleep(delay)
    
    # 最终保存
    with open('data/completed_teams.json', 'w') as f:
        json.dump(completed, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"更新完成: {success_count}/{len(team_ids)} 成功")
    
    if failed_teams:
        print(f"失败球队 ({len(failed_teams)}): {failed_teams}")
    else:
        print("所有球队数据已完整!")
    
    return success_count == len(team_ids)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)