# 数据源规范

## 重要原则

**体育比赛赛程**必须从官方来源获取，**开奖数据**可从专业彩票网站获取，**比赛分析**可从第三方网站获取。

## 彩票种类与数据源

### 竞彩足球 (sporttery.cn) ✅

| 玩法 | 数据字段 | API |
|-----|---------|-----|
| 胜平负 | had | getMatchCalculatorV1.qry |
| 让球胜平负 | hhad | getMatchCalculatorV1.qry |
| 比分 | crs | getMatchCalculatorV1.qry |
| 总进球 | ttg | getMatchCalculatorV1.qry |
| 半全场 | hafu | getMatchCalculatorV1.qry |

**API地址**: `https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1`

**结论**: 竞彩足球的所有玩法都在一个API中，无需单独爬取！

### 竞彩篮球 (sporttery.cn) ✅

**API地址**: `https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1`

### 传统足彩（胜负彩14场、任选9场、6场半全场、4场总进球）

| 彩种 | 说明 | 来源 |
|-----|------|------|
| 胜负彩14场 | 选14场 | 500.com/trade/sfc/ |
| 任选9场 | 选9场 | 500.com/trade/sfc/ |
| 6场半全场 | 选6场半全场 | 500.com/trade/bqc/ |
| 4场总进球 | 选4场总进球 | 500.com/trade/jqc/ |

**说明**: 传统足彩是"选场次"玩法，不是每场独立投注。500.com是传统足彩的权威数据来源。

### 北京单场 (bjlot.com.cn) ✅

| 玩法 | 页面 |
|-----|------|
| 单场胜平负 | /ssm/dc200_spf.shtml |
| 单场比分 | /ssm/dc200_bf.shtml |
| 单场总进球 | /ssm/dc200_tgg.shtml |
| 单场半全场 | /ssm/dc200_bqc.shtml |

### 开奖数据（大乐透、七星彩等）

| 彩种 | 来源 |
|-----|------|
| 大乐透 | 500.com/datachart |
| 七星彩 | 500.com/datachart |
| 排列三/五 | 500.com/datachart |

**说明**: 开奖数据可从专业彩票网站获取。

### 分析数据

| 数据类型 | 来源 |
|---------|------|
| 比赛分析 | 500.com/odds, okooo.com |
| 亚盘数据 | 500.com/odds |
| 欧赔数据 | 500.com/odds |
| 球队排名 | 500.com, okooo.com |
| 实时比分 | sporttery.cn + 500.com补充 |

## 现有爬虫状态

| 爬虫 | 数据类型 | 当前来源 | 状态 |
|-----|---------|---------|------|
| live_crawler_final.py | 竞彩足球 | sporttery.cn | ✅ 正确 |
| football.html | 竞彩足球 | sporttery.cn | ✅ 正确 |
| basketball_analysis_crawler.py | 竞彩篮球 | sporttery.cn | ✅ 正确 |
| bjdc_crawler.py | 北京单场 | bjlot.com.cn | ✅ 正确 |
| sggg_crawler.py | 胜负过关 | bjlot.com.cn | ✅ 正确 |
| bqc6_crawler.py | 6场半全场 | 500.com | ✅ 正确（传统足彩） |
| ctzc_crawler.py | 胜负彩14场 | 500.com | ✅ 正确（传统足彩） |
| zjq4_crawler.py | 4场总进球 | 500.com | ✅ 正确（传统足彩） |
| dlt_crawler.py | 大乐透开奖 | 500.com | ✅ 正确（开奖数据） |
| qxc_crawler.py | 七星彩开奖 | 500.com | ✅ 正确（开奖数据） |

## 官方API

### 竞彩官网 (sporttery.cn)
```
比分直播（包含已结束比赛）:
  https://webapi.sporttery.cn/gateway/uniform/fb/getMatchDataPageListV1.qry?method=all&pageSize=200
  - 比分字段: sectionsNo999 (格式: "2:1")
  - 状态字段: matchStatus (1=待开售, 3=暂停销售, 11=已完成)
  - 返回所有竞彩比赛（包括历史比赛）

足球比赛计算器(当前可投注):
  https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1
  - 包含胜平负、让球、比分、总进球、半全场赔率
  - 只返回当前可投注的比赛

篮球比赛:
  https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1

单关状态:
  https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001
```

### 北京体彩网 (bjlot.com.cn)
```
北京单场: https://www.bjlot.com.cn/ssm/dc200_spf.shtml
胜负过关: 需要查找具体页面
```

### 传统足彩 (500.com)
```
胜负彩14场/任选9场: https://trade.500.com/sfc/
4场总进球: https://trade.500.com/jqc/
6场半全场: https://trade.500.com/bqc/
```

## 分析数据来源

### 500.com
```
比赛分析: https://odds.500.com/fenxi/shuju-{fixture_id}.shtml
亚盘数据: https://odds.500.com/fenxi/yapan-{fixture_id}.shtml
欧赔数据: https://odds.500.com/fenxi/ouzhi-{fixture_id}.shtml
```

### okooo.com
```
球队身价: https://www.okooo.com/match/{fid}/
```

## 修改记录

- 2026-03-31: 创建规范文档
- 2026-03-31: 确认竞彩足球API包含所有玩法，传统足彩500.com是正确来源