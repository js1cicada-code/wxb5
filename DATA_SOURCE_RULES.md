# 数据源规范

## 重要原则

**体育比赛赛程**必须从官方来源获取，**开奖数据**可从专业彩票网站获取，**比赛分析**可从第三方网站获取。

## 数据类型说明

| 类型 | 说明 | 来源要求 |
|-----|------|---------|
| 体育比赛赛程 | 有具体比赛时间、对阵的 | 必须官方 |
| 开奖数据 | 数字彩开奖结果 | 可用专业网站 |
| 分析数据 | 赔率、排名、历史等 | 可用第三方 |

## 数据源规范表

### 体育比赛类（必须官方来源）

| 彩种 | 主来源 | 备用来源 | 说明 |
|-----|-------|---------|------|
| 竞彩足球 | sporttery.cn | - | 足球比赛赛程 |
| 竞彩篮球 | sporttery.cn | - | 篮球比赛赛程 |
| 北京单场 | bjlot.com.cn | sporttery.cn | 足球/篮球比赛 |
| 传统足彩 | bjlot.com.cn | sporttery.cn | 14场比赛 |
| 4场总进球 | bjlot.com.cn | sporttery.cn | 4场比赛 |
| 6场半全场 | bjlot.com.cn | sporttery.cn | 6场比赛 |
| 胜负过关 | bjlot.com.cn | sporttery.cn | 多场比赛 |

### 开奖类（可用专业网站）

| 彩种 | 推荐来源 | 说明 |
|-----|---------|------|
| 大乐透 | 500.com | 开奖数据 |
| 七星彩 | 500.com | 开奖数据 |
| 排列三 | 500.com | 开奖数据 |
| 排列五 | 500.com | 开奖数据 |

### 分析数据（第三方来源）

| 数据类型 | 来源 |
|---------|------|
| 比赛分析 | 500.com, okooo.com |
| 亚盘数据 | 500.com |
| 欧赔数据 | 500.com |
| 球队排名 | 500.com, okooo.com |
| 实时比分 | sporttery.cn, 500.com |

## 官方API

### 竞彩官网 (sporttery.cn)
```
足球比赛列表: https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1
篮球比赛列表: https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1
单关状态: https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001
```

### 北京体彩网 (bjlot.com.cn)
```
北京单场: https://www.bjlot.com.cn/ssm/dc200_spf.shtml
胜负过关: https://www.bjlot.com.cn/ssm/270.shtml
传统足彩: 需要查找具体页面
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

## 现有爬虫状态

| 爬虫 | 数据类型 | 当前来源 | 状态 |
|-----|---------|---------|------|
| live_crawler_final.py | 足球赛程 | sporttery.cn + 500.com补充 | ✅ 符合 |
| football.html | 足球赛程 | sporttery.cn | ✅ 符合 |
| basketball_analysis_crawler.py | 篮球赛程 | sporttery.cn + 500.com补充 | ✅ 符合 |
| bjdc_crawler.py | 北京单场 | bjlot.com.cn | ✅ 符合 |
| sggg_crawler.py | 胜负过关 | bjlot.com.cn | ✅ 符合 |
| bqc6_crawler.py | 6场半全场 | 500.com | ❌ 需修改 |
| ctzc_crawler.py | 传统足彩 | 500.com | ❌ 需修改 |
| zjq4_crawler.py | 4场总进球 | 500.com | ❌ 需修改 |
| dlt_crawler.py | 大乐透开奖 | 500.com | ✅ 符合（开奖数据） |
| qxc_crawler.py | 七星彩开奖 | 500.com | ✅ 符合（开奖数据） |

## 北京体彩网页面发现

```
北京单场: https://www.bjlot.com.cn/ssm/dc200_spf.shtml ✅
胜负过关: https://www.bjlot.com.cn/ssm/270.shtml ❌ (404)
6场半全场: https://www.bjlot.com.cn/ssm/dc240_bqc.shtml ✅ (期号变化)
传统足彩: 待查找
4场总进球: 待查找
```

## 修改计划

1. bqc6_crawler.py - 改为从 bjlot.com.cn/ssm/dc240_bqc.shtml 获取
2. ctzc_crawler.py - 查找北京体彩网页面后修改
3. zjq4_crawler.py - 查找北京体彩网页面后修改

**注意**: 现有爬虫虽然使用500.com，但已正常工作。修改需谨慎。

## 修改记录

- 2026-03-31: 创建规范文档