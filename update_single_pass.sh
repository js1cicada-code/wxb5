#!/bin/bash
# 竞彩足球单关状态功能快速启动脚本

echo "============================================================"
echo "竞彩足球单关状态功能"
echo "============================================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未安装Python3"
    exit 1
fi

# 检查依赖
echo ""
echo "检查依赖..."
pip3 list | grep requests > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "安装requests库..."
    pip3 install requests
fi

# 运行爬虫
echo ""
echo "运行爬虫获取单关状态..."
python3 single_pass_crawler.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 单关状态数据已更新"
    echo ""
    echo "数据文件:"
    echo "  - single_pass_status.json (完整数据)"
    echo "  - dist/single_pass.json (前端数据)"
    echo ""
    echo "下一步:"
    echo "  1. 启动开发服务器: npm run dev"
    echo "  2. 访问 http://localhost:8082 查看效果"
    echo "  3. 混合过关页面会显示单关标识"
else
    echo ""
    echo "❌ 爬虫运行失败"
fi

echo "============================================================"