#!/bin/bash
# 从data目录恢复数据到dist目录
# 用途：当dist目录被误删后，从data目录恢复数据文件

set -e

echo "开始恢复数据..."

# 创建dist目录
mkdir -p dist

# 检查data目录是否存在
if [ ! -d "data" ]; then
    echo "错误: data目录不存在，请先运行爬虫获取数据"
    exit 1
fi

# 复制所有JSON文件
echo "复制JSON数据文件..."
cp -v data/*.json dist/ 2>/dev/null || echo "没有找到JSON文件"

# 检查复制结果
json_count=$(ls dist/*.json 2>/dev/null | wc -l)
echo "已恢复 $json_count 个JSON文件"

# 提示用户
echo ""
echo "✓ 数据恢复完成!"
echo "提示: 如果需要重新构建页面，请运行: npm run build"