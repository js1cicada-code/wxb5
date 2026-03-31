# 目录结构规范

## 数据目录
- **HTML页面**: 根目录 (live.html, match_analysis.html, basketball_analysis.html等)
- **数据文件**: `dist/data/` (HTML通过相对路径 `data/xxx.json` 访问)
- **备份目录**: `data/` (爬虫同时备份到这里)

## 爬虫输出位置
所有爬虫必须同时写入以下位置：
1. `dist/data/xxx.json` - 主数据目录（HTML读取）
2. `dist/xxx.json` - 兼容旧页面
3. `data/xxx.json` - 备份目录

## 关键文件说明
| 文件名 | 说明 | 来源 |
|--------|------|------|
| live_data.json | 足球比分直播 | live_crawler_final.py |
| live_basketball_data.json | 篮球比分直播 | live_basketball_crawler.py |
| jczq_data.json | 竞彩足球比赛列表 | data_fetcher.py |
| jclq_data.json | 竞彩篮球比赛列表 | data_fetcher.py |
| fixture_mapping.json | 竞彩与500.com映射 | live_crawler_final.py |
| analysis_*.json | 足球比赛分析数据 | analysis_crawler.py |
| basketball_analysis_*.json | 篮球比赛分析数据 | basketball_analysis_crawler.py |

## HTTP服务器
启动命令: `cd dist && python3 -m http.server 8080`
访问: `http://localhost:8080/live.html`