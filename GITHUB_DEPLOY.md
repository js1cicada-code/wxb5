# GitHub 自动部署说明

## 自动爬虫
项目已配置GitHub Actions，每10分钟自动运行所有爬虫：

### 运行的爬虫
- 比分直播-足球 (live_crawler_final.py)
- 比分直播-篮球 (live_basketball_crawler.py)  
- 竞彩足球/篮球 (data_fetcher.py)
- 北京单场 (bjdc_crawler.py)
- 大乐透 (dlt_crawler.py)
- 七星彩 (qxc_crawler.py)
- 传统足彩 (ctzc_crawler.py)
- 6场半全场 (bqc6_crawler.py)
- 4场总进球 (zjq4_crawler.py)
- 篮球分析 (basketball_analysis_crawler.py)

### 查看运行状态
访问: https://github.com/js1cicada-code/wxb5/actions

### 手动触发
在Actions页面选择"Update Data" workflow，点击"Run workflow"

## 数据访问
所有数据存储在 `data/` 目录，自动提交到GitHub

## 监控页面
访问: https://js1cicada-code.github.io/wxb5/all_crawlers_monitor.html
