#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画直播截图服务
"""

import json
import os
import time
import threading
from datetime import datetime
from playwright.sync_api import sync_playwright

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 存储截图
screenshots = {}
browser = None
page = None
playwright = None

def init_browser():
    """初始化浏览器"""
    global browser, page, playwright
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        viewport={'width': 800, 'height': 600}
    )
    page = context.new_page()
    print("浏览器初始化完成")

def capture_animation(fid, home='', away=''):
    """截取动画直播画面"""
    global page
    
    if not page:
        init_browser()
    
    try:
        url = f'https://live.500.com/animation/v2/?fixtureid={fid}&width=800&lang=zhs'
        
        page.goto(url, timeout=30000, wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        # 截图
        screenshot_path = os.path.join(DATA_DIR, f'animation_{fid}.png')
        os.makedirs(DATA_DIR, exist_ok=True)
        page.screenshot(path=screenshot_path, full_page=False)
        
        # 复制到dist
        import shutil
        dist_path = os.path.join(DIST_DIR, f'animation_{fid}.png')
        shutil.copy(screenshot_path, dist_path)
        
        return True
    except Exception as e:
        print(f"截图失败 {fid}: {e}")
        return False

def get_match_events(fid):
    """获取比赛事件"""
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f'https://odds.500.com/fenxi1/inc/stat_ajax.php?act=event&id={fid}'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            data = response.read().decode('utf-8')
            return data
    except Exception as e:
        print(f"获取事件失败: {e}")
        return None

def start_live_capture(fid, home='', away=''):
    """启动直播截图"""
    def capture_loop():
        while True:
            capture_animation(fid, home, away)
            time.sleep(10)
    
    thread = threading.Thread(target=capture_loop, daemon=True)
    thread.start()
    return thread

if __name__ == '__main__':
    # 测试截图
    init_browser()
    capture_animation('1398255', '土耳其', '罗马尼亚')
    print("截图完成")