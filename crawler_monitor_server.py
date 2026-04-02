#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫监控API服务
"""

from flask import Flask, jsonify, send_from_directory
import json
import os
import subprocess
import re

app = Flask(__name__)

DATA_DIR = 'data'

@app.route('/')
def index():
    return send_from_directory('.', 'crawler_monitor.html')

@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    try:
        # 读取所有球队ID
        with open(f'{DATA_DIR}/all_team_ids.json', 'r') as f:
            all_ids = json.load(f)
        
        # 读取已完成的球队
        completed = []
        if os.path.exists(f'{DATA_DIR}/completed_teams.json'):
            with open(f'{DATA_DIR}/completed_teams.json', 'r') as f:
                completed = json.load(f)
        
        # 统计失败的球队
        failed_count = 0
        if os.path.exists('batch_update_full.log'):
            with open('batch_update_full.log', 'r') as f:
                log_content = f.read()
                failed_count = log_content.count('失败:')
        
        total = len(all_ids)
        completed_count = len(completed)
        progress = (completed_count / total * 100) if total > 0 else 0
        
        return jsonify({
            'total': total,
            'completed': completed_count,
            'failed': failed_count,
            'progress': round(progress, 2),
            'remaining': total - completed_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process')
def get_process():
    """获取进程状态"""
    try:
        # 查找爬虫进程
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        processes = []
        for line in result.stdout.split('\n'):
            if 'batch_update_teams.py' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    time_elapsed = parts[9]
                    processes.append({
                        'pid': pid,
                        'cpu': cpu,
                        'mem': mem,
                        'time': time_elapsed,
                        'status': 'running'
                    })
        
        return jsonify({
            'processes': processes,
            'running': len(processes) > 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    """获取日志"""
    try:
        lines_count = 200
        if os.path.exists('batch_update_full.log'):
            with open('batch_update_full.log', 'r') as f:
                lines = f.readlines()[-lines_count:]
            return jsonify({
                'logs': [line.strip() for line in lines if line.strip()]
            })
        return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/completed')
def get_completed():
    """获取已完成的球队"""
    try:
        if os.path.exists(f'{DATA_DIR}/completed_teams.json'):
            with open(f'{DATA_DIR}/completed_teams.json', 'r') as f:
                completed = json.load(f)
            return jsonify({
                'completed': completed[-100:],  # 最近100个
                'total': len(completed)
            })
        return jsonify({'completed': [], 'total': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current')
def get_current():
    """获取当前正在处理的球队"""
    try:
        if os.path.exists('batch_update_full.log'):
            with open('batch_update_full.log', 'r') as f:
                content = f.read()
            
            # 查找最后一个"正在更新球队"
            matches = re.findall(r'\[(\d+)/(\d+)\] 正在更新球队 (\d+)', content)
            if matches:
                last = matches[-1]
                return jsonify({
                    'current': int(last[0]),
                    'total': int(last[1]),
                    'team_id': int(last[2]),
                    'progress': round(int(last[0]) / int(last[1]) * 100, 2)
                })
        
        return jsonify({'current': 0, 'total': 0, 'team_id': 0, 'progress': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/data/<path:filename>')
def serve_data(filename):
    """提供数据文件"""
    return send_from_directory(DATA_DIR, filename)

if __name__ == '__main__':
    print("=" * 50)
    print("爬虫监控服务启动")
    print("访问地址: http://localhost:5555")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5555, debug=False)