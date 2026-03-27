#!/bin/bash

echo "=========================================="
echo "比分直播服务"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 先更新数据
echo "正在获取最新比分数据..."
python3 live_crawler_final.py

echo ""
echo "启动代理服务器..."
echo "访问地址: http://localhost:8080/live.html"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动代理服务
python3 proxy_server.py