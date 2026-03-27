#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画直播截图服务 - 后台运行
"""

import os
import time
import threading
import json
import urllib.request
import ssl
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except:
    HAS_PLAYWRIGHT = False

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

active_matches = {}

def init():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    if HAS_PLAYWRIGHT:
        print("Playwright可用")
        return True
    return False

def capture(fid):
    if not HAS_PLAYWRIGHT:
        return False
    
    try:
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        animation_url = f'https://live.500.com/animation/v2/?fixtureid={fid}&width=800&lang=zhs'
        stats_url = f'https://odds.500.com/fenxi/stat-{fid}.shtml'
        
        try:
            page.goto(animation_url, timeout=15000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"动画页面失败，使用统计页: {e}")
            try:
                page.goto(stats_url, timeout=15000, wait_until='domcontentloaded')
                page.wait_for_timeout(2000)
            except:
                pass
        
        path = os.path.join(DATA_DIR, f'animation_{fid}.png')
        page.screenshot(path=path, clip={'x': 0, 'y': 0, 'width': 800, 'height': 500})
        
        import shutil
        shutil.copy(path, os.path.join(DIST_DIR, f'animation_{fid}.png'))
        
        browser.close()
        p.stop()
        
        if fid in active_matches:
            active_matches[fid]['last_update'] = time.time()
        return True
        
    except Exception as e:
        print(f"截图失败 {fid}: {e}")
        return False

def get_events(fid):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f'https://odds.500.com/fenxi1/inc/stat_ajax.php?act=event&id={fid}'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None

def start_match(fid, home='', away=''):
    if fid in active_matches:
        return
    
    active_matches[fid] = {
        'home': home,
        'away': away,
        'last_update': 0,
        'thread': None
    }
    
    def update_loop():
        while fid in active_matches:
            capture(fid)
            time.sleep(15)
    
    thread = threading.Thread(target=update_loop, daemon=True)
    thread.start()
    active_matches[fid]['thread'] = thread
    print(f"开始监控比赛 {fid}: {home} vs {away}")

def stop_match(fid):
    if fid in active_matches:
        del active_matches[fid]
        print(f"停止监控比赛 {fid}")

def get_status():
    return {
        'playwright': HAS_PLAYWRIGHT,
        'matches': list(active_matches.keys())
    }

if __name__ == '__main__':
    init()
    start_match('1398255', '土耳其', '罗马尼亚')
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n停止...")