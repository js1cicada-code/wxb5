#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫统一配置
所有数据文件统一保存到 dist/data/ 目录
"""

import os
import json

# 统一数据保存目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')

def ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    return DATA_DIR

def save_json(filename, data):
    """保存JSON数据到统一目录"""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath

def load_json(filename):
    """加载JSON数据"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None