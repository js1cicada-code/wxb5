# 爬虫综合监控使用说明

## 📊 监控面板

### 方式1: Web监控页面（推荐）

**已启动HTTP服务器**，访问以下地址：

```
http://localhost:8000/all_crawlers_monitor.html
```

**功能特点**：
- ✅ 实时显示所有爬虫运行状态
- ✅ 数据更新时间
- ✅ 数据量统计
- ✅ 球队爬取进度条
- ✅ 自动刷新（每10秒）
- ✅ 分类显示（赛事/数字彩/足彩/直播）

### 方式2: 终端监控脚本

```bash
# 查看综合状态
bash monitor.sh

# 或查看详细状态
python3 monitor_all.py

# 或简化版
python3 monitor.py
```

## 📈 当前爬虫状态

### ✅ 运行中
- **球队数据爬虫**: PID 56684, 进度 12/1263 (1%)

### ✅ 数据状态良好
- **赛事数据**: 竞足/竞篮/北单 - 10分钟前更新
- **数字彩**: 大乐透/七星彩/传统彩 - 9分钟前更新
- **足彩玩法**: 四场进球/半全场/总进球 - 1小时前更新
- **直播数据**: 足球直播 - 1天前更新
- **篮球分析**: 102场比赛数据

## 🎯 各类爬虫说明

### 1. 赛事爬虫
```bash
# 竞彩足球/篮球
python3 crawler.py

# 北单
python3 bjdc_crawler.py
```

### 2. 数字彩爬虫
```bash
# 大乐透
python3 dlt_crawler.py

# 七星彩
python3 qxc_crawler.py

# 传统彩
python3 ctzc_crawler.py
```

### 3. 足彩玩法爬虫
```bash
# 四场进球
python3 sggg_crawler.py

# 半全场
python3 bqc6_crawler.py

# 总进球
python3 zjq4_crawler.py
```

### 4. 分析爬虫
```bash
# 足球分析
python3 analysis_crawler.py

# 篮球分析
python3 basketball_analysis_crawler.py
```

### 5. 直播爬虫
```bash
# 足球直播
python3 live_crawler.py

# 篮球直播
python3 live_basketball_crawler.py
```

### 6. 球队数据爬虫
```bash
# 批量更新所有球队
python3 batch_update_teams.py

# 单个球队
python3 team_crawler.py <team_id>
```

## 🔄 定时更新

### 启动定时更新（推荐）
```bash
python3 scheduled_update.py
```

### 快速更新
```bash
python3 update_fast.py
```

### 更新所有
```bash
python3 update_all.py
```

## ⚙️ 管理命令

### 查看运行状态
```bash
# 所有爬虫进程
ps aux | grep -E "crawler|update" | grep -v grep

# 球队爬虫进程
ps aux | grep batch_update | grep -v grep
```

### 停止爬虫
```bash
# 停止特定进程
kill <PID>

# 停止所有爬虫
pkill -f crawler
pkill -f batch_update
```

### 查看日志
```bash
# 球队爬虫日志
tail -f batch_update_full.log

# 定时更新日志
tail -f update.log

# 最新50行
tail -50 batch_update_full.log
```

## 💡 防止休眠

电脑休眠会暂停所有爬虫，运行以下命令保持唤醒：

```bash
# 防止系统休眠
caffeinate -i

# 或针对特定进程
caffeinate -i -w $(pgrep -f batch_update_teams.py)
```

## 📁 数据文件位置

```
data/
├── jczq_data.json          # 竞彩足球
├── jclq_data.json          # 竞彩篮球
├── bjdc_data.json          # 北京单场
├── dlt_data.json           # 大乐透
├── qxc_data.json           # 七星彩
├── ctzc_data.json          # 传统彩
├── sggg_data.json          # 四场进球
├── bqc6_data.json          # 半全场
├── zjq4_data.json          # 总进球
├── live_data.json          # 直播数据
├── team_*.json             # 球队详情
├── basketball_analysis_*.json  # 篮球分析
└── league/                 # 联赛数据
    └── *.json
```

## 🔧 HTTP服务器

已启动的HTTP服务器（端口8000）：
- 启动命令: `python3 -m http.server 8000`
- 停止命令: `kill $(lsof -ti:8000)`
- 重启命令: `kill $(lsof -ti:8000); python3 -m http.server 8000 &`

## 📱 监控面板地址

```
综合监控: http://localhost:8000/all_crawlers_monitor.html
球队监控: http://localhost:8000/crawler_monitor_simple.html
```

## ⚠️ 注意事项

1. **电脑休眠**: 会暂停所有爬虫，使用 `caffeinate -i` 防止
2. **进度保存**: 球队爬虫每10个自动保存进度
3. **中断恢复**: 重新运行会从断点继续
4. **预计时间**: 1263个球队约需10-20小时
5. **数据更新**: 其他爬虫建议每小时运行一次

## 📞 故障排查

### 爬虫停止了
1. 检查是否休眠
2. 查看日志最后内容
3. 重新启动

### 数据不更新
1. 检查爬虫进程
2. 查看日志错误信息
3. 手动运行一次

### 监控页面打不开
1. 确认HTTP服务器运行中
2. 检查端口8000是否被占用
3. 使用终端监控脚本替代