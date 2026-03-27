#!/bin/bash
# 北京单场数据爬虫启动脚本

echo "启动北京单场数据爬虫..."
echo "数据将每5分钟自动更新一次"
echo "按 Ctrl+C 停止"
echo ""

cd /Users/bluekyo/Downloads/wxingbaoh5
python3 bjdc_crawler.py