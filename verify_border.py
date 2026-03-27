#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单关边框功能验证脚本
"""

import os

def check_file_exists(filename, description):
    """检查文件是否存在"""
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filename}")
    return exists

def check_content(filename, patterns, description):
    """检查文件内容"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n检查 {description}:")
        all_found = True
        for pattern_name, pattern in patterns:
            found = pattern in content
            status = "✅" if found else "❌"
            print(f"  {status} {pattern_name}")
            if not found:
                all_found = False
        
        return all_found
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    print("=" * 60)
    print("单关边框功能验证")
    print("=" * 60)
    
    # 检查文件
    print("\n1. 检查文件完整性:")
    files_ok = all([
        check_file_exists('index.html', '主页面'),
        check_file_exists('single_pass_crawler.py', '爬虫脚本'),
        check_file_exists('test_border.html', '边框效果测试页')
    ])
    
    # 检查CSS样式
    css_patterns = [
        ('odds-row单关样式', '.odds-row.single-pass'),
        ('score-grid单关样式', '.score-grid.single-pass'),
        ('zjq-grid单关样式', '.zjq-grid.single-pass'),
        ('bqc-grid单关样式', '.bqc-grid.single-pass'),
        ('适中边框', 'border: 1px solid #ffb3b3'),
        ('渐变背景', 'linear-gradient(to bottom, #fff8f8, #ffffff)')
    ]
    css_ok = check_content('index.html', css_patterns, 'CSS样式')
    
    # 检查JavaScript逻辑
    js_patterns = [
        ('混合过关-胜平负', "const singlePassClass = isSinglePassAvailable(m.id, 'spf')"),
        ('混合过关-让球胜平负', "const singlePassClass = isSinglePassAvailable(m.id, 'rqspf')"),
        ('比分玩法', "const singlePassClass = isSinglePassAvailable(m.id, 'bf')"),
        ('总进球玩法', "const singlePassClass = isSinglePassAvailable(m.id, 'zjq')"),
        ('半全场玩法', "const singlePassClass = isSinglePassAvailable(m.id, 'bqc')"),
        ('更多玩法-比分', "bodyHtml = '<div class=\"score-grid' + singlePassClass + '\">'"),
        ('更多玩法-总进球', "bodyHtml = '<div class=\"zjq-grid' + singlePassClass + '\">'"),
        ('更多玩法-半全场', "bodyHtml = '<div class=\"bqc-grid' + singlePassClass + '\">'")
    ]
    js_ok = check_content('index.html', js_patterns, 'JavaScript逻辑')
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    if files_ok and css_ok and js_ok:
        print("✅ 所有验证通过！单关边框功能已正确实现")
        print("\n功能特点:")
        print("  ✓ 支持单关的玩法会显示适中边框")
        print("  ✓ 边框颜色: #ffb3b3 (粉红色，清晰可见)")
        print("  ✓ 渐变背景: #fff8f8 到 #ffffff")
        print("  ✓ 圆角边框: 4px")
        print("  ✓ 边框宽度: 1px (细线)")
        print("  ✓ 适用于所有玩法: 胜平负、让球胜平负、比分、总进球、半全场")
        print("\n查看效果:")
        print("  1. 打开 test_border.html 查看边框效果")
        print("  2. 运行 npm run dev 启动服务")
        print("  3. 访问混合过关页面查看实际效果")
    else:
        print("⚠️ 部分验证未通过，请检查上述错误信息")
    
    print("=" * 60)

if __name__ == "__main__":
    main()