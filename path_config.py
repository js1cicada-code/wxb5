#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径配置模块 - 所有爬虫必须使用此模块获取路径

目录规范:
- HTML页面在根目录，通过 data/xxx.json 读取数据
- 实际数据在 dist/data/ 目录
- data/ 目录作为备份

使用方法:
    from path_config import get_data_paths, ensure_dir
    paths = get_data_paths('live_data.json')
    for path in paths:
        ensure_dir(path)
        with open(path, 'w') as f:
            json.dump(data, f)
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, 'data')
DIST_DIR = os.path.join(BASE_DIR, 'dist')
DIST_DATA_DIR = os.path.join(BASE_DIR, 'dist', 'data')


def get_data_paths(filename):
    """
    获取数据文件的所有存储路径
    
    参数:
        filename: 文件名，如 'live_data.json'
    
    返回:
        list: 三个路径 [dist/data/, dist/, data/]
              按优先级排序，第一个是HTML读取的主路径
    """
    return [
        os.path.join(DIST_DATA_DIR, filename),
        os.path.join(DIST_DIR, filename),
        os.path.join(DATA_DIR, filename),
    ]


def get_primary_path(filename):
    """获取主数据路径 (dist/data/)"""
    return os.path.join(DIST_DATA_DIR, filename)


def get_backup_paths(filename):
    """获取备份路径 [dist/, data/]"""
    return [
        os.path.join(DIST_DIR, filename),
        os.path.join(DATA_DIR, filename),
    ]


def ensure_dir(filepath):
    """确保目录存在"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)


def save_json(data, filename):
    """
    保存JSON到所有位置
    
    参数:
        data: 要保存的数据
        filename: 文件名
    
    返回:
        保存的路径数量
    """
    import json
    paths = get_data_paths(filename)
    for path in paths:
        ensure_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return len(paths)


def load_json(filename):
    """
    加载JSON，优先从主路径读取
    
    参数:
        filename: 文件名
    
    返回:
        数据或None
    """
    import json
    paths = get_data_paths(filename)
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    return None


if __name__ == '__main__':
    print("=" * 50)
    print("路径配置")
    print("=" * 50)
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"DIST_DIR: {DIST_DIR}")
    print(f"DIST_DATA_DIR: {DIST_DATA_DIR}")
    print()
    print("示例 - live_data.json 的路径:")
    for p in get_data_paths('live_data.json'):
        print(f"  {p}")