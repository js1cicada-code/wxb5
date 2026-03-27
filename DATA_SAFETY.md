# 数据安全机制说明

## 目录结构

```
/wxingbaoh5/
├── data/                    # 数据文件主存储（纳入版本控制）
│   ├── matches/            # 比赛列表数据（未来规划）
│   ├── analysis/           # 分析详细数据（未来规划）
│   ├── *.json              # 各类数据文件
│   └── backup/             # 自动备份（不纳入版本控制）
├── dist/                    # 构建产物（可随时删除重建）
│   ├── *.html              # HTML页面
│   ├── *.css               # 样式文件
│   ├── *.js                # JavaScript文件
│   └── *.json              # 从data/复制的数据文件
└── src/                     # 源代码
```

## 数据安全原则

### 1. 双重存储机制
所有爬虫生成的JSON文件同时保存到两个位置：
- **data/**: 主存储，纳入版本控制，永远不会被误删
- **dist/**: 供Web访问，可随时从data/恢复

### 2. 可重建 vs 不可重建

| 文件类型 | 存储位置 | 可删除 | 可重建方式 |
|---------|---------|--------|-----------|
| HTML/CSS/JS | dist/ | ✅ | `npm run build` |
| JSON数据 | data/ + dist/ | ⚠️ data/不可删 | 从data/复制或重新爬取 |

### 3. 删除dist目录的影响

✅ **安全操作**:
```bash
rm -rf dist/
npm run build          # 重新构建
./restore_data.sh      # 从data/恢复JSON文件
```

❌ **危险操作**:
```bash
rm -rf data/          # 数据将永久丢失！
```

## 快速恢复

如果dist目录被误删，执行以下命令恢复：

```bash
# 方法1: 使用恢复脚本
./restore_data.sh

# 方法2: 手动恢复
npm run build
cp data/*.json dist/
```

## 数据备份

### 自动备份
```bash
# 运行备份脚本
./backup_data.sh

# 备份位置: data/backup/backup_YYYYMMDD_HHMMSS/
```

### 定时备份（可选）
```bash
# 添加到crontab
0 */6 * * * cd /path/to/wxingbaoh5 && ./backup_data.sh
```

## 爬虫开发规范

### 保存数据的正确方式
```python
# ✅ 正确: 同时保存到data和dist
def save_data(filename, data):
    # 保存到data目录
    with open(f'data/{filename}', 'w') as f:
        json.dump(data, f)
    
    # 保存到dist目录
    with open(f'dist/{filename}', 'w') as f:
        json.dump(data, f)

# ❌ 错误: 只保存到dist
def save_data_wrong(filename, data):
    with open(f'dist/{filename}', 'w') as f:
        json.dump(data, f)
```

## 相关脚本

| 脚本 | 用途 | 使用场景 |
|------|------|---------|
| `restore_data.sh` | 从data恢复到dist | dist被误删后恢复数据 |
| `backup_data.sh` | 备份data目录 | 定期备份数据安全 |
| `update_fast.sh` | 快速更新爬虫 | 每5分钟自动运行 |
| `update_medium.sh` | 中频更新爬虫 | 每10分钟自动运行 |
| `update_slow.sh` | 低频更新爬虫 | 每30分钟自动运行 |

## 应急处理

### 场景1: dist目录被删除
```bash
# 1. 确认data目录存在
ls -la data/

# 2. 恢复数据
./restore_data.sh

# 3. 重新构建
npm run build

# 4. 重启服务
npm run dev
```

### 场景2: data目录损坏
```bash
# 1. 从备份恢复
ls -la data/backup/

# 2. 复制最近的备份
cp -r data/backup/backup_YYYYMMDD_HHMMSS/* data/

# 3. 如果没有备份，重新爬取
python3 basketball_analysis_crawler.py
python3 bjdc_crawler.py
python3 ctzc_crawler.py
```

### 场景3: 需要回滚到历史数据
```bash
# 1. 查看可用备份
ls -la data/backup/

# 2. 恢复指定备份
cp -r data/backup/backup_YYYYMMDD_HHMMSS/* data/
cp data/*.json dist/

# 3. 重启服务
npm run build && npm run dev
```

## 检查清单

### 开发环境设置
- [ ] 确认data目录存在
- [ ] 确认restore_data.sh可执行
- [ ] 确认backup_data.sh可执行
- [ ] 运行一次备份测试

### 部署前检查
- [ ] data目录包含所有必要的数据文件
- [ ] dist目录可以正常访问
- [ ] 备份机制正常工作

### 定期维护
- [ ] 每周检查备份文件
- [ ] 每月清理旧备份（保留最近3次）
- [ ] 定期测试恢复流程

## 更多信息

详细的事故分析和预防措施，请参考：
- [RCA文档](./RCA_DATA_LOSS.md)