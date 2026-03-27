# 竞彩足球单关状态功能说明

## 功能概述
在混合过关页面增加了单关状态显示，让用户可以清楚地看到哪些比赛、哪些玩法支持单关投注。

## 技术实现

### 1. 数据获取
- **API接口**: `https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001`
- **数据字段**: 每场比赛的 `poolList` 数组中包含单关状态信息
  - `cbtSingle`: 1=可单关，0=不可单关
  - `cbtValue`: 1=已开售，0=未开售

### 2. 爬虫脚本
- 文件: `single_pass_crawler.py`
- 功能: 
  - 从竞彩网获取单关状态数据
  - 解析并保存为JSON格式
  - 生成统计数据

### 3. 前端显示
- 在混合过关页面，每个玩法标签旁边显示"单关"标识
- 在更多玩法弹窗中，支持单关的玩法tab会显示"单"标识
- 红色背景的"单关"标签，醒目易识别

## 使用方法

### 运行爬虫
```bash
python3 single_pass_crawler.py
```

爬虫会：
1. 获取最新的单关状态数据
2. 保存到 `single_pass_status.json` (完整数据)
3. 保存到 `dist/single_pass.json` (前端数据)

### 前端集成
页面会自动：
1. 初始化时获取单关状态
2. 每30秒更新一次数据
3. 在界面上显示单关标识

## 玩法代码对照表

| 代码 | 玩法名称 | 前端标识 |
|------|---------|---------|
| HAD | 胜平负 | spf |
| HHAD | 让球胜平负 | rqspf |
| CRS | 比分 | bf |
| TTG | 总进球 | zjq |
| HAFU | 半全场 | bqc |

## 数据示例

```json
{
  "2038420": {
    "matchNumStr": "周三001",
    "home": "韩国女",
    "away": "日本女",
    "singlePass": {
      "HAD": {
        "available": true,
        "singlePass": true
      },
      "HHAD": {
        "available": true,
        "singlePass": false
      }
    }
  }
}
```

## 单关判断逻辑
```javascript
// 判断是否可单关
const isSinglePass = pool.cbtValue == 1 && pool.cbtSingle == 1;
```

## 页面展示效果

### 混合过关主页面
- 胜平负玩法标签: `胜平负 [单关]`
- 让球胜平负玩法标签: `让球胜平负（让+1）`

### 更多玩法弹窗
- 支持单关的tab会显示: `比分 [单] (2)`
- 不支持单关的tab正常显示: `总进球 (3)`

## 更新日志

### 2026-03-18
- ✅ 新增单关状态爬虫脚本
- ✅ 前端页面增加单关状态显示
- ✅ 自动定时更新单关数据（每30秒）
- ✅ 优化显示样式，使用醒目的红色标签

## 注意事项

1. 单关状态实时变化，建议定期更新
2. 并非所有比赛都支持单关投注
3. 同一场比赛，不同玩法的单关状态可能不同
4. 爬虫需要网络连接，确保可以访问竞彩网API

## 测试命令

```bash
# 测试爬虫
python3 single_pass_crawler.py

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```