#!/bin/bash
# 自动更新彩票数据脚本

echo "开始更新彩票数据..."

cd /Users/bluekyo/Downloads/wxingbaoh5

# 更新竞彩足球/篮球、6场、4场、传统足彩
python3 data_fetcher.py

# 更新北京单场
python3 bjdc_crawler.py

# 更新胜负过关
python3 sggg_crawler.py

# 更新大乐透
python3 dlt_crawler.py

echo "所有数据更新完成！"
echo "更新时间: $(date '+%Y-%m-%d %H:%M:%S')"