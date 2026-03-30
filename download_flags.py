#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载资料库图片 - 使用正确的URL路径
"""

import json
import os
import requests

DATA_FILE = "data/database_data.json"
OUTPUT_DIR = "data/flags"
BASE_URL = "https://zq.titan007.com/Image/info/"

def download_image(filename, save_path):
    """下载图片"""
    url = BASE_URL + filename
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://zq.titan007.com/info/index_cn.htm',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"下载失败 [{response.status_code}]: {url}")
            return False
    except Exception as e:
        print(f"下载出错: {url} - {e}")
        return False

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    success = 0
    failed = 0
    
    for country in data['countries']:
        image_path = country.get('image', '')
        if not image_path:
            continue
        
        filename = image_path.split('/')[-1]
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        country['local_image'] = f"data/flags/{filename}"
        
        if os.path.exists(save_path):
            print(f"已存在: {filename}")
            success += 1
            continue
        
        print(f"下载: {filename}")
        if download_image(filename, save_path):
            success += 1
        else:
            failed += 1
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成: 成功 {success}, 失败 {failed}")

if __name__ == "__main__":
    main()