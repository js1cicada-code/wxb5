# 彩票数据定时更新

## 快速开始

### 手动更新
```bash
python3 scheduled_update.py
```

### 守护进程模式（后台运行）
```bash
# 每10分钟更新一次
python3 scheduled_update.py --daemon --interval 10
```

### 定时任务配置

#### 方法1: 使用 crontab
```bash
# 编辑定时任务
crontab -e

# 添加以下行（每10分钟更新）
*/10 * * * * /usr/bin/python3 /path/to/wxingbaoh5/scheduled_update.py >> /path/to/wxingbaoh5/update.log 2>&1

# 或者每小时更新
0 * * * * /usr/bin/python3 /path/to/wxingbaoh5/scheduled_update.py >> /path/to/wxingbaoh5/update.log 2>&1
```

#### 方法2: 使用 launchd（macOS推荐）
创建 `~/Library/LaunchAgents/com.lottery.update.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lottery.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/wxingbaoh5/scheduled_update.py</string>
    </array>
    <key>StartInterval</key>
    <integer>600</integer>  <!-- 10分钟 = 600秒 -->
    <key>StandardOutPath</key>
    <string>/path/to/wxingbaoh5/update.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/wxingbaoh5/update.log</string>
</dict>
</plist>
```

加载任务:
```bash
launchctl load ~/Library/LaunchAgents/com.lottery.update.plist
```

## 更新的数据

| 数据类型 | 更新频率 | 文件 |
|---------|---------|------|
| 竞彩足球/篮球 | 实时API | 直接从竞彩网获取 |
| 北京单场 | 每10分钟 | dist/bjdc_data.json |
| 胜负过关 | 每10分钟 | dist/sggg_data.json |
| 传统足彩14场 | 每10分钟 | dist/ctzc_data.json |
| 任选9场 | 每10分钟 | dist/ctzc_data.json (同上) |
| 6场半全场 | 每10分钟 | dist/bqc6_data.json |
| 4场总进球 | 每10分钟 | dist/zjq4_data.json |
| 大乐透 | 每小时 | dist/dlt_data.json |
| 七星彩 | 每小时 | dist/qxc_data.json |
| 篮球分析 | 每10分钟 | dist/basketball_matches.json |

## 日志查看

```bash
# 查看最新日志
tail -f update.log

# 查看最近50行
tail -50 update.log
```

## 状态检查

```bash
# 检查数据新鲜度
python3 check_data_freshness.py
```

## 销售时间规则

- **周一至周五**: 11:00 - 22:00
- **周六日**: 11:00 - 23:00
- 非销售时间显示"已停售"
- 当日已停售的比赛自动隐藏
- 未来比赛显示"已停售"状态但可查看