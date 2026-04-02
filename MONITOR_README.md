# 爬虫监控面板使用说明

## 快速启动

### 方式1: 直接打开HTML（推荐）
直接用浏览器打开：
```
crawler_monitor.html
```
或
```
dist/crawler_monitor.html
```

**功能**：
- 每5秒自动刷新数据
- 显示爬虫进度和统计
- 实时日志查看
- 已完成球队列表

### 方式2: 使用API服务（完整功能）
启动监控服务器：
```bash
python3 crawler_monitor_server.py
```

访问：http://localhost:5555

**额外功能**：
- 实时进程状态（PID、CPU、内存）
- 一键停止进程
- 更快的API响应

## 监控内容

### 1. 统计信息
- 总球队数
- 已完成数量
- 失败数量
- 完成率进度条

### 2. 进程状态
- 运行状态指示器
- 进程详细信息
- 停止按钮

### 3. 实时日志
- 最后200行日志
- 错误/成功高亮显示
- 自动滚动到底部

### 4. 已完成球队
- 最近100个完成的球队ID
- 状态标识

## 当前爬虫状态

### 检查进程
```bash
ps aux | grep batch_update | grep -v grep
```

### 查看实时日志
```bash
tail -f batch_update_full.log
```

### 查看进度
```bash
cat data/completed_teams.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```

### 防止休眠
```bash
caffeinate -i -w $(pgrep -f batch_update_teams.py)
```

## 注意事项

1. **电脑休眠会暂停爬虫** - 使用caffeinate防止
2. **进度自动保存** - 每10个球队保存一次
3. **可中断恢复** - 重新运行会从断点继续
4. **预计时间** - 1263个球队约需10-20小时

## 问题排查

### 爬虫停止了
1. 检查是否休眠
2. 查看日志最后内容
3. 重新启动：`python3 batch_update_teams.py`

### 进度不更新
1. 刷新监控页面
2. 检查`data/completed_teams.json`文件
3. 查看日志是否有错误

### 数据缺失
1. 失败的球队会记录在日志
2. 可以单独重新爬取：`python3 team_crawler.py <team_id>`