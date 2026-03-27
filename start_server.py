#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票数据服务 - 支持期次切换API
"""

import json
import threading
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

from data_fetcher import fetch_bqc6_data, fetch_zjq4_data, fetch_ctzc_data, save_json, update_all_data

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')


class LotteryHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # API端点
        if path == '/api/bqc6':
            self.handle_api('bqc6', query)
        elif path == '/api/zjq4':
            self.handle_api('zjq4', query)
        elif path == '/api/ctzc':
            self.handle_api('ctzc', query)
        else:
            self.serve_static_file(path)
    
    def handle_api(self, lottery_type, query):
        expect = query.get('expect', [None])[0]
        
        try:
            if lottery_type == 'bqc6':
                data = fetch_bqc6_data(expect)
            elif lottery_type == 'zjq4':
                data = fetch_zjq4_data(expect)
            elif lottery_type == 'ctzc':
                data = fetch_ctzc_data(expect)
            else:
                data = None
            
            if data:
                self.send_json_response(200, data)
            else:
                self.send_json_response(404, {'error': '无数据'})
        except Exception as e:
            self.send_json_response(500, {'error': str(e)})
    
    def send_json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def serve_static_file(self, path):
        # 移除前导斜杠
        if path.startswith('/'):
            path = path[1:]
        
        # 确定文件路径
        if path.startswith('dist/'):
            filepath = os.path.join(BASE_DIR, path)
        elif path == '':
            filepath = os.path.join(BASE_DIR, 'index.html')
        else:
            filepath = os.path.join(BASE_DIR, path)
        
        if os.path.isfile(filepath):
            # 确定MIME类型
            ext = os.path.splitext(filepath)[1].lower()
            mime_types = {
                '.html': 'text/html; charset=utf-8',
                '.css': 'text/css; charset=utf-8',
                '.js': 'application/javascript; charset=utf-8',
                '.json': 'application/json; charset=utf-8',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.gif': 'image/gif',
                '.ico': 'image/x-icon',
            }
            mime = mime_types.get(ext, 'application/octet-stream')
            
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.end_headers()
            
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def log_message(self, format, *args):
        # 只记录API请求
        if '/api/' in args[0]:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def periodic_update():
    """每2分钟更新一次数据"""
    while True:
        try:
            time.sleep(120)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 定时更新数据...")
            update_all_data()
        except Exception as e:
            print(f"更新失败: {e}")


def main():
    print("\n" + "="*60)
    print("彩票数据服务")
    print("="*60)
    
    # 初始更新
    update_all_data()
    
    # 启动定时更新线程
    update_thread = threading.Thread(target=periodic_update, daemon=True)
    update_thread.start()
    
    # 启动HTTP服务
    server = HTTPServer(('', PORT), LotteryHandler)
    
    print(f"\n服务已启动!")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"\n可用页面:")
    print(f"  - 竞彩足球: http://localhost:{PORT}/index.html")
    print(f"  - 竞彩篮球: http://localhost:{PORT}/basketball.html")
    print(f"  - 6场半全场: http://localhost:{PORT}/bqc6.html")
    print(f"  - 4场总进球: http://localhost:{PORT}/zjq4.html")
    print(f"  - 传统足彩: http://localhost:{PORT}/ctzc.html")
    print(f"  - 任选9场: http://localhost:{PORT}/rx9.html")
    print(f"\nAPI端点:")
    print(f"  - /api/bqc6?expect=期次")
    print(f"  - /api/zjq4?expect=期次")
    print(f"  - /api/ctzc?expect=期次")
    print(f"\n数据每2分钟自动更新")
    print(f"按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


if __name__ == '__main__':
    main()