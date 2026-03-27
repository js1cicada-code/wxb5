#!/bin/bash
# 数据备份脚本
# 用途：定期备份data目录中的数据文件

set -e

BACKUP_DIR="data/backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "开始备份数据..."

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 检查data目录是否存在
if [ ! -d "data" ]; then
    echo "错误: data目录不存在"
    exit 1
fi

# 创建今日备份
BACKUP_PATH="$BACKUP_DIR/backup_$DATE"
mkdir -p "$BACKUP_PATH"

# 复制所有JSON文件
cp -v data/*.json "$BACKUP_PATH/" 2>/dev/null || echo "没有找到JSON文件"

# 保留最近3次备份
echo "清理旧备份..."
ls -t "$BACKUP_DIR" | tail -n +4 | while read old_backup; do
    echo "删除旧备份: $old_backup"
    rm -rf "$BACKUP_DIR/$old_backup"
done

# 显示当前备份列表
echo ""
echo "当前备份列表:"
ls -lh "$BACKUP_DIR"

echo ""
echo "✓ 备份完成: $BACKUP_PATH"