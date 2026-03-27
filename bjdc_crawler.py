#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北京单场数据爬虫 - 使用Playwright从北京体彩网获取数据
"""

from playwright.sync_api import sync_playwright
import json
import os
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def fetch_bjdc_data():
    """从北京体彩网获取北京单场数据"""
    print(f"开始爬取北京单场数据... {datetime.now()}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto('https://www.bjlot.com.cn/ssm/dc200_spf.shtml', wait_until='networkidle', timeout=30000)
            time.sleep(2)
            
            all_matches = []
            period = ''
            
            # 获取期次
            period = page.evaluate('''() => {
                const match = document.body.innerText.match(/奖期[\\s]*(\\d+)/);
                return match ? match[1] : '';
            }''')
            
            print(f"期次: {period}")
            
            # 获取日期链接
            date_links = page.query_selector_all('a:has-text("场")')
            date_urls = []
            
            for link in date_links:
                text = link.text_content()
                if '场' in text and '/' in text:
                    date_urls.append(text.strip())
            
            print(f"找到日期: {len(date_urls)} 个")
            
            # 逐个点击日期获取数据
            for date_url in date_urls:
                try:
                    date_text = date_url.split()[0] if ' ' in date_url else date_url[:10]
                    page.click(f'text={date_text}')
                    time.sleep(1)
                    
                    matches = page.evaluate('''() => {
                        const results = [];
                        const rows = document.querySelectorAll('table tr');
                        
                        rows.forEach((row) => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 7) {
                                const no = cells[0]?.textContent?.trim() || '';
                                const status = cells[1]?.textContent?.trim() || '';
                                const league = cells[2]?.textContent?.trim() || '';
                                const matchTime = cells[3]?.textContent?.trim() || '';
                                const home = cells[4]?.textContent?.trim() || '';
                                let handicap = cells[5]?.textContent?.trim() || '0';
                                const away = cells[6]?.textContent?.trim() || '';
                                
                                if (handicap.includes('受')) {
                                    handicap = '-' + handicap.replace('受', '').replace('球', '');
                                }
                                handicap = parseInt(handicap) || 0;
                                
                                if (no && status.includes('销售中')) {
                                    results.push({
                                        id: no,
                                        matchNum: no,
                                        league: league,
                                        time: matchTime,
                                        home: home,
                                        away: away,
                                        handicap: handicap,
                                        status: 'selling',
                                        spf: [2.5, 3.2, 2.8]
                                    });
                                }
                            }
                        });
                        return results;
                    }''')
                    
                    print(f"  {date_url}: {len(matches)}场")
                    all_matches.extend(matches)
                    
                except Exception as e:
                    print(f"  点击 {date_url} 失败: {e}")
            
            # 去重
            seen = set()
            unique_matches = []
            for m in all_matches:
                key = f"{m['home']}_{m['away']}"
                if key not in seen:
                    seen.add(key)
                    unique_matches.append(m)
            
            print(f"\n总共: {len(unique_matches)} 场比赛")
            
            browser.close()
            
            return {
                'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'period': period,
                'matchCount': len(unique_matches),
                'total': len(unique_matches),
                'matches': unique_matches
            }
            
        except Exception as e:
            print(f"爬取失败: {e}")
            browser.close()
            return None


def save_data(data):
    """保存数据到多个位置"""
    if not data:
        return
    
    paths = [
        os.path.join(BASE_DIR, 'dist', 'bjdc_data.json'),
        os.path.join(BASE_DIR, 'dist', 'data', 'bjdc_data.json'),
        os.path.join(BASE_DIR, 'data', 'bjdc_data.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到 {len(paths)} 个位置")
    
    # 显示统计
    if data['matches']:
        print(f"\n前3场比赛:")
        for m in data['matches'][:3]:
            print(f"  {m['id']}. [{m['league']}] {m['home']} vs {m['away']}")


if __name__ == '__main__':
    data = fetch_bjdc_data()
    if data:
        save_data(data)