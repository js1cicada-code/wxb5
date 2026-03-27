#!/usr/bin/env python3
"""
数据新鲜度监控脚本
检查所有数据文件的更新时间，生成监控报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
STATUS_FILE = DIST_DIR / "data_status.json"

DATA_FILES = {
    "bjdc_data.json": {"name": "北京单场", "max_age_hours": 1, "update_interval": 5},
    "sggg_data.json": {"name": "胜负过关", "max_age_hours": 1, "update_interval": 10},
    "ctzc_data.json": {"name": "传统足彩/任选9场", "max_age_hours": 1, "update_interval": 10},
    "bqc6_data.json": {"name": "6场半全场", "max_age_hours": 1, "update_interval": 10},
    "zjq4_data.json": {"name": "4场总进球", "max_age_hours": 1, "update_interval": 10},
    "dlt_data.json": {"name": "大乐透", "max_age_hours": 2, "update_interval": 30},
    "qxc_data.json": {"name": "七星彩", "max_age_hours": 2, "update_interval": 30},
    "single_pass.json": {"name": "单关状态", "max_age_hours": 1, "update_interval": 10},
    "fixture_mapping.json": {"name": "足球分析", "max_age_hours": 1, "update_interval": 10},
    "basketball_matches.json": {"name": "篮球分析", "max_age_hours": 1, "update_interval": 10},
}

def check_data_freshness():
    """检查所有数据文件的新鲜度"""
    now = datetime.now()
    status = {
        "checkTime": now.isoformat(),
        "status": "ok",
        "files": [],
        "alerts": []
    }
    
    for filename, config in DATA_FILES.items():
        filepath = DIST_DIR / filename
        file_status = {
            "file": filename,
            "name": config["name"],
            "exists": False,
            "updateTime": None,
            "ageMinutes": None,
            "ageHours": None,
            "isFresh": False,
            "status": "unknown",
            "updateInterval": config.get("update_interval", 30)
        }
        
        if filepath.exists():
            file_status["exists"] = True
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                update_time_str = data.get('updateTime')
                if update_time_str:
                    try:
                        update_time = datetime.strptime(update_time_str, '%Y-%m-%d %H:%M:%S')
                        file_status["updateTime"] = update_time_str
                    except ValueError:
                        update_time = None
                else:
                    update_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                    file_status["updateTime"] = update_time.strftime('%Y-%m-%d %H:%M:%S')
                
                if update_time:
                    age = now - update_time
                    file_status["ageMinutes"] = int(age.total_seconds() / 60)
                    file_status["ageHours"] = round(age.total_seconds() / 3600, 2)
                    
                    if age.total_seconds() < config["max_age_hours"] * 3600:
                        file_status["isFresh"] = True
                        file_status["status"] = "fresh"
                    else:
                        file_status["isFresh"] = False
                        file_status["status"] = "stale"
                        status["alerts"].append({
                            "type": "stale",
                            "file": filename,
                            "name": config["name"],
                            "ageHours": file_status["ageHours"],
                            "maxAgeHours": config["max_age_hours"],
                            "message": f"{config['name']}数据已过期 ({file_status['ageHours']}小时前)"
                        })
            except Exception as e:
                file_status["status"] = f"error: {str(e)}"
        else:
            file_status["status"] = "missing"
            status["alerts"].append({
                "type": "missing",
                "file": filename,
                "name": config["name"],
                "message": f"{config['name']}数据文件不存在"
            })
        
        status["files"].append(file_status)
    
    if any(a["type"] in ["missing", "stale"] for a in status["alerts"]):
        status["status"] = "warning" if len(status["alerts"]) < 3 else "critical"
    
    return status

def print_status_report(status):
    """打印状态报告"""
    print("\n" + "="*60)
    print("           数据新鲜度监控报告")
    print("="*60)
    print(f"检查时间: {status['checkTime']}")
    print(f"整体状态: {status['status'].upper()}")
    print("-"*60)
    
    for f in status["files"]:
        icon = "✓" if f["isFresh"] else ("✗" if f["exists"] else "?")
        status_text = f["status"].upper()
        age_info = f"{f['ageHours']}h" if f["ageHours"] is not None else "N/A"
        print(f"{icon} {f['name']:<12} | {status_text:<12} | 更新: {age_info}")
    
    if status["alerts"]:
        print("-"*60)
        print("告警信息:")
        for alert in status["alerts"]:
            print(f"  ⚠ {alert['message']}")
    
    print("="*60 + "\n")

def main():
    status = check_data_freshness()
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    
    print_status_report(status)
    
    if status["status"] in ["warning", "critical"]:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())