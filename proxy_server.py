#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画直播代理服务
"""

import http.server
import socketserver
import urllib.request
import ssl
import re
import json
import os
from urllib.parse import urlparse, parse_qs

PORT = 8080
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 动画服务
animation_service = None

def init_animation_service():
    """初始化动画服务"""
    global animation_service
    try:
        import animation_service as as_mod
        if as_mod.init():
            animation_service = as_mod
            print("动画服务初始化成功")
            return True
    except Exception as e:
        print(f"动画服务初始化失败: {e}")
    return False

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 动画截图API
        if parsed.path == '/animation_screenshot':
            query = parse_qs(parsed.query)
            fid = query.get('fid', [''])[0]
            if fid:
                self.serve_screenshot(fid)
            else:
                self.send_error(400, 'Missing fid')
            return
        
        # 动画事件API
        if parsed.path == '/animation_events':
            query = parse_qs(parsed.query)
            fid = query.get('fid', [''])[0]
            if fid:
                self.serve_events(fid)
            else:
                self.send_error(400, 'Missing fid')
            return
        
        # 代理动画直播iframe内容
        if parsed.path == '/proxy_animation':
            query = parse_qs(parsed.query)
            fid = query.get('fid', [''])[0]
            if fid:
                self.proxy_animation_frame(fid)
            else:
                self.send_error(400, 'Missing fid')
            return
        
        # 代理动画直播页面
        if parsed.path == '/live_animation':
            query = parse_qs(parsed.query)
            fid = query.get('fid', [''])[0]
            
            if fid:
                self.proxy_animation(fid)
            else:
                self.send_error(400, 'Missing fid parameter')
            return
        
        # 代理500彩票网静态资源
        if parsed.path.startswith('/css/') or parsed.path.startswith('/js/') or parsed.path.startswith('/images/') or parsed.path.startswith('/static/'):
            self.proxy_static(parsed.path)
            return
        
        # API：获取动画页面HTML
        if parsed.path == '/api/animation':
            query = parse_qs(parsed.query)
            fid = query.get('fid', [''])[0]
            
            if fid:
                self.get_animation_html(fid)
            else:
                self.send_error(400, 'Missing fid parameter')
            return
        
        # 其他请求按静态文件处理
        super().do_GET()
    
    def serve_screenshot(self, fid):
        """提供截图"""
        import os
        
        # 启动动画服务
        if animation_service:
            # 检查是否已在监控
            if fid not in animation_service.active_matches:
                # 从数据文件获取球队名
                try:
                    data_path = os.path.join(DATA_DIR, 'live_data.json')
                    if os.path.exists(data_path):
                        with open(data_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for m in data.get('matches', []):
                                if str(m.get('fid')) == str(fid) or str(m.get('id')) == str(fid):
                                    animation_service.start_match(fid, m.get('home', ''), m.get('away', ''))
                                    break
                except:
                    pass
        
        screenshot_path = os.path.join(DATA_DIR, f'animation_{fid}.png')
        
        if os.path.exists(screenshot_path):
            try:
                with open(screenshot_path, 'rb') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store')
                self.end_headers()
                self.wfile.write(content)
                return
            except:
                pass
        
        # 生成等待图
        self.generate_waiting(fid)
    
    def generate_waiting(self, fid):
        """生成等待图"""
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500">
<rect width="800" height="500" fill="#1a1a2e"/>
<text x="400" y="250" text-anchor="middle" fill="#4CAF50" font-family="sans-serif" font-size="18">⚽ 加载动画直播中...</text>
</svg>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'image/svg+xml')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(svg.encode('utf-8'))
    
    def serve_events(self, fid):
        """提供比赛事件"""
        try:
            import urllib.request
            import ssl
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f'https://odds.500.com/fenxi1/inc/stat_ajax.php?act=event&id={fid}'
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                content = response.read().decode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"events":[]}')
    
    def proxy_animation_frame(self, fid):
        """代理动画直播iframe"""
        try:
            # 获取原始统计页面
            url = f'https://odds.500.com/fenxi/stat-{fid}.shtml?showAnimation=1'
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                html = response.read().decode('gb2312', errors='ignore')
            
            # 提取动画区域和必要的数据
            # 获取动画参数
            import re
            
            # 提取fixtureid
            fixture_match = re.search(r"'fixtureid'\s*:\s*(\d+)", html)
            fixtureid = fixture_match.group(1) if fixture_match else fid
            
            # 提取球队名
            home_match = re.search(r"homeTeam.*?encodeURIComponent\(['\"]([^'\"]+)['\"]", html)
            away_match = re.search(r"awayTeam.*?encodeURIComponent\(['\"]([^'\"]+)['\"]", html)
            home_team = home_match.group(1) if home_match else ''
            away_team = away_match.group(1) if away_match else ''
            
            # 构建纯动画页面
            animation_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:sans-serif; background:#1a1a2e; color:#fff; min-height:100vh; }}
.loading {{ display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; }}
.spinner {{ width:40px; height:40px; border:3px solid #333; border-top-color:#4CAF50; border-radius:50%; animation:spin 1s linear infinite; }}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}
.error {{ text-align:center; padding:40px; color:#888; }}
</style>
</head>
<body>
<div class="loading" id="loading">
<div class="spinner"></div>
<p style="margin-top:16px;color:#888">加载动画直播...</p>
</div>
<div class="error" id="error" style="display:none">
<p>⚠️ 暂无动画直播数据</p>
<p style="font-size:12px;margin-top:8px;color:#666">该比赛可能尚未开始</p>
</div>
<script>
(function(){{
var fid = {fixtureid};
var home = "{home_team}";
var away = "{away_team}";
var loaded = false;

function loadAnimation() {{
try {{
var iframe = document.createElement('iframe');
iframe.src = 'https://live.500.com/animation/v2/?fixtureid=' + fid + '&width=100%25&lang=zhs&homeTeam=' + encodeURIComponent(home) + '&awayTeam=' + encodeURIComponent(away);
iframe.style.cssText = 'width:100%;height:100vh;border:none;position:absolute;top:0;left:0;';
iframe.onload = function() {{
document.getElementById('loading').style.display = 'none';
}};
iframe.onerror = function() {{
document.getElementById('loading').style.display = 'none';
document.getElementById('error').style.display = 'block';
}};
document.body.appendChild(iframe);
}} catch(e) {{
document.getElementById('loading').style.display = 'none';
document.getElementById('error').style.display = 'block';
}}
}}

loadAnimation();
}})();
</script>
</body>
</html>'''
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(animation_html.encode('utf-8'))
            
        except Exception as e:
            print(f'代理动画iframe失败: {e}')
            self.send_error(500, str(e))
    
    def proxy_static(self, path):
        """代理静态资源"""
        try:
            url = f'https://odds.500.com{path}'
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                content = response.read()
                content_type = response.headers.get('Content-Type', 'text/plain')
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            self.send_error(404, str(e))
    
    def proxy_animation(self, fid):
        """代理动画直播页面"""
        try:
            html = self.fetch_animation_page(fid)
            
            # 移除CSP限制
            html = self.remove_csp(html)
            
            # 注入基础样式
            html = self.inject_base_style(html)
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            print(f'代理失败: {e}')
            self.send_error(500, str(e))
    
    def get_animation_html(self, fid):
        """返回动画HTML（JSON格式）"""
        try:
            html = self.fetch_animation_page(fid)
            html = self.remove_csp(html)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = json.dumps({'html': html}, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))
    
    def fetch_animation_page(self, fid):
        """获取动画直播页面"""
        # 直接获取动画直播iframe内容
        url = f'https://live.500.com/animation/v2/?fixtureid={fid}&width=100%25&lang=zhs'
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://odds.500.com/'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # 添加viewport适配
        html = html.replace('<head>', '<head><meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        return html
    
    def remove_csp(self, html):
        """移除CSP和X-Frame-Options限制"""
        # 移除CSP meta标签
        html = re.sub(r'<meta[^>]*http-equiv=["\']?Content-Security-Policy[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<meta[^>]*Content-Security-Policy[^>]*>', '', html, flags=re.IGNORECASE)
        
        # 移除X-Frame-Options
        html = re.sub(r'<meta[^>]*http-equiv=["\']?X-Frame-Options[^>]*>', '', html, flags=re.IGNORECASE)
        
        return html
    
    def inject_base_style(self, html):
        """注入基础样式，隐藏不需要的元素"""
        style = '''
        <base href="https://odds.500.com/">
        <style>
            /* 隐藏顶部导航 */
            .top-bar, .header, #header, .nav, #nav, .top, #top { display: none !important; }
            /* 隐藏侧边栏 */
            .sidebar, #sidebar, .side-bar { display: none !important; }
            /* 隐藏登录相关 */
            .login, #login, .user-info, .user { display: none !important; }
            /* 隐藏广告 */
            .ad, .ads, .advertisement { display: none !important; }
            /* 调整主内容区域 */
            body { margin: 0; padding: 0; }
            .main-content, #main, .content, .wrapper { margin-top: 0 !important; padding: 10px !important; }
            /* 动画区域 */
            #match_animation, .match-animation { min-height: 400px; }
        </style>
        '''
        # 在<head>后注入
        if '<head>' in html:
            html = html.replace('<head>', '<head>' + style)
        else:
            html = style + html
        
        return html
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


def run_server():
    init_animation_service()
    print(f'动画直播代理服务启动在端口 {PORT}')
    print(f'访问 http://localhost:{PORT}/live.html')
    print('按 Ctrl+C 停止服务')
    
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        httpd.serve_forever()


if __name__ == '__main__':
    run_server()