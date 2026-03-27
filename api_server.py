#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""彩票数据API服务"""

import json
import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time
from datetime import datetime
from pathlib import Path

PORT = 8081
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')

update_in_progress = False
last_update_time = None


class LotteryAPIHandler(SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == '/api/status':
            self.handle_status()
        elif path == '/api/update':
            self.handle_update()
        elif path == '/api/matches':
            self.handle_matches()
        elif path == '/api/basketball_matches':
            self.handle_basketball_matches()
        elif path.startswith('/dist/'):
            self.serve_dist_file(path[6:])
        else:
            super().do_GET()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/api/update':
            self.handle_update()
        else:
            self.send_error(404)
    
    def serve_dist_file(self, filename):
        filepath = os.path.join(DIST_DIR, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            if filename.endswith('.json'):
                self.send_header('Content-Type', 'application/json; charset=utf-8')
            elif filename.endswith('.css'):
                self.send_header('Content-Type', 'text/css; charset=utf-8')
            elif filename.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript; charset=utf-8')
            else:
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, 'File not found')
    
    def handle_status(self):
        global update_in_progress, last_update_time
        
        try:
            status_file = os.path.join(DIST_DIR, 'data_status.json')
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            else:
                status_data = {"status": "unknown", "files": [], "alerts": []}
            
            status_data['updateInProgress'] = update_in_progress
            status_data['lastUpdateTime'] = last_update_time
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status_data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def handle_matches(self):
        """获取比赛分析列表"""
        try:
            matches = []
            
            mapping_file = os.path.join(DIST_DIR, 'fixture_mapping.json')
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                    mapping = mapping_data.get('mapping', {})
                    
                    for key, info in mapping.items():
                        fixture_id = info.get('fixtureId')
                        if fixture_id:
                            analysis_file = os.path.join(DIST_DIR, f'analysis_{fixture_id}.json')
                            match_info = {
                                'fixtureId': fixture_id,
                                'home': info.get('home', ''),
                                'away': info.get('away', ''),
                                'league': info.get('league', ''),
                                'date': info.get('date', ''),
                                'time': info.get('time', ''),
                                'hasAnalysis': os.path.exists(analysis_file)
                            }
                            
                            if os.path.exists(analysis_file):
                                try:
                                    with open(analysis_file, 'r', encoding='utf-8') as af:
                                        analysis = json.load(af)
                                        home_ability = analysis.get('homeAbility', {})
                                        away_ability = analysis.get('awayAbility', {})
                                        
                                        if home_ability and home_ability.get('totalValue'):
                                            match_info['homeValue'] = home_ability['totalValue'].get('raw', '')
                                        if away_ability and away_ability.get('totalValue'):
                                            match_info['awayValue'] = away_ability['totalValue'].get('raw', '')
                                except:
                                    pass
                            
                            matches.append(match_info)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'matches': matches}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def handle_basketball_matches(self):
        """获取篮球比赛分析列表"""
        try:
            matches = []
            
            matches_file = os.path.join(DIST_DIR, 'basketball_matches.json')
            if os.path.exists(matches_file):
                with open(matches_file, 'r', encoding='utf-8') as f:
                    matches_data = json.load(f)
                    match_list = matches_data.get('matches', [])
                    
                    for match in match_list:
                        match_id = match.get('matchId')
                        if match_id:
                            analysis_file = os.path.join(DIST_DIR, f'basketball_analysis_{match_id}.json')
                            match_info = {
                                'matchId': match_id,
                                'home': match.get('home', ''),
                                'away': match.get('away', ''),
                                'league': match.get('league', ''),
                                'date': match.get('date', ''),
                                'time': match.get('time', ''),
                                'hasAnalysis': os.path.exists(analysis_file)
                            }
                            
                            if os.path.exists(analysis_file):
                                try:
                                    with open(analysis_file, 'r', encoding='utf-8') as af:
                                        analysis = json.load(af)
                                        home_ability = analysis.get('homeAbility', {})
                                        away_ability = analysis.get('awayAbility', {})
                                        
                                        if home_ability and home_ability.get('totalValue'):
                                            match_info['homeValue'] = home_ability['totalValue'].get('raw', '')
                                        if away_ability and away_ability.get('totalValue'):
                                            match_info['awayValue'] = away_ability['totalValue'].get('raw', '')
                                        
                                        odds = analysis.get('odds', {})
                                        if odds:
                                            match_info['odds'] = odds
                                except:
                                    pass
                            
                            matches.append(match_info)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'matches': matches}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def handle_update(self):
        global update_in_progress, last_update_time
        
        if update_in_progress:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'in_progress', 'message': '更新正在进行中'}).encode('utf-8'))
            return
        
        def run_update():
            global update_in_progress, last_update_time
            update_in_progress = True
            try:
                script_path = os.path.join(BASE_DIR, 'update_all_data.sh')
                subprocess.run(['bash', script_path], cwd=BASE_DIR, capture_output=True, text=True)
                last_update_time = datetime.now().isoformat()
                
                subprocess.run(['python3', 'check_data_freshness.py'], cwd=BASE_DIR, capture_output=True)
            except Exception as e:
                print(f"更新失败: {e}")
            finally:
                update_in_progress = False
        
        threading.Thread(target=run_update, daemon=True).start()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'started', 'message': '数据更新已启动'}).encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    
    subprocess.run(['python3', 'check_data_freshness.py'], cwd=BASE_DIR, capture_output=True)
    
    server = HTTPServer(('', PORT), LotteryAPIHandler)
    
    print(f"\n✓ API服务已启动!")
    print(f"  端口: {PORT}")
    print(f"  监控面板: http://localhost:8082/data_monitor.html")
    print(f"  API端点:")
    print(f"    GET /api/status  - 获取数据状态")
    print(f"    POST /api/update - 触发数据更新")
    print(f"\n按 Ctrl+C 停止服务")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == '__main__':
    main()