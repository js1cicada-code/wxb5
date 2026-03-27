# 竞彩足球单关状态功能

## 功能概述

在混合过关页面增加了单关状态显示功能，用户可以清楚地看到：
- 哪些比赛支持单关投注
- 每个玩法是否支持单关
- 支持单关的玩法会显示醒目的红色边框
- 实时更新的单关状态

## 视觉效果

### 单关标识
- **标签**: 浅粉背景的"单关"标签
- **边框**: 1px 粉红色边框 (#ffb3b3)
- **背景**: 渐变背景 (#fff8f8 到 #ffffff)
- **圆角**: 4px
- **效果**: 细线边框，清晰可见但不显眼

### 显示位置
1. **混合过关主页面**: 玩法标签旁显示"单关"，选项区域显示红色边框
2. **单独玩法页面**: 支持单关的玩法整体显示红色边框
3. **更多玩法弹窗**: Tab标签显示"单"标识，支持单关的玩法显示红色边框

## 快速开始

### 1. 更新单关状态数据
```bash
# 方式1: 使用快速脚本
./update_single_pass.sh

# 方式2: 直接运行爬虫
python3 single_pass_crawler.py
```

### 2. 启动服务
```bash
npm run dev
```

### 3. 查看效果
访问 http://localhost:8082，在混合过关页面可以看到：
- 支持单关的玩法会显示红色"单关"标签
- 更多玩法弹窗中会显示"单"标识

## 文件说明

### 核心文件
- `single_pass_crawler.py` - 单关状态爬虫脚本
- `index.html` - 前端页面（已集成单关状态显示）
- `update_single_pass.sh` - 快速更新脚本
- `test_single_pass.py` - 功能测试脚本

### 数据文件
- `single_pass_status.json` - 完整的单关状态数据
- `dist/single_pass.json` - 前端使用的精简数据

### 文档
- `SINGLE_PASS_README.md` - 详细技术文档

## 技术实现

### 数据源
- **API**: `https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001`
- **更新频率**: 每30秒自动更新一次
- **数据字段**: `poolList.cbtSingle` (1=可单关, 0=不可单关)

### 前端集成
```javascript
// 判断是否支持单关
function isSinglePassAvailable(matchId, playType) {
    const poolCodeMap = {
        'spf': 'HAD',    // 胜平负
        'rqspf': 'HHAD', // 让球胜平负
        'bf': 'CRS',     // 比分
        'zjq': 'TTG',    // 总进球
        'bqc': 'HAFU'    // 半全场
    };
    return singlePassStatus[matchId][poolCode].singlePass;
}
```

### UI展示
- **主页面**: 胜平负/让球胜平负标签旁显示"单关"标识
- **弹窗页面**: 更多玩法tab显示"单"标识
- **样式**: 红色背景，白色文字，醒目易识别
- **边框**: 支持单关的玩法选项区域整体显示红色边框

### 边框样式
```css
.odds-row.single-pass {
    border: 1px solid #ffb3b3;        /* 粉红色边框 */
    border-radius: 4px;                /* 小圆角 */
    padding: 4px 4px;                  /* 内边距 */
    background: linear-gradient(
        to bottom, 
        #fff8f8,                       /* 浅粉背景 */
        #ffffff                        /* 白色背景 */
    );
}
```

## 测试

运行完整功能测试：
```bash
python3 test_single_pass.py
```

测试内容：
1. ✅ API是否可访问
2. ✅ 爬虫是否正常工作
3. ✅ 数据文件是否存在
4. ✅ 前端代码是否完整

## 使用示例

### Python爬虫
```python
from single_pass_crawler import SinglePassCrawler

crawler = SinglePassCrawler()
data = crawler.get_single_pass_status()

for match in data['matches']:
    if any(sp['singlePass'] for sp in match['singlePass'].values()):
        print(f"{match['matchNumStr']} 支持单关")
```

### JavaScript前端
```javascript
// 自动获取单关状态
await fetchSinglePassStatus();

// 检查是否支持单关
if (isSinglePassAvailable(matchId, 'spf')) {
    console.log('胜平负支持单关投注');
}
```

## 数据统计

当前数据示例：
- 总比赛数: 21场
- 支持单关: 19场
- 更新时间: 2026-03-18 16:55:35

## 注意事项

1. **实时更新**: 单关状态会实时变化，建议定期运行爬虫更新
2. **网络要求**: 需要能够访问竞彩网API
3. **玩法差异**: 同一场比赛，不同玩法的单关状态可能不同
4. **标识说明**: 
   - 显示"单关"表示可以单独投注该玩法
   - 不显示表示只能串关投注

## 常见问题

**Q: 为什么有些比赛不支持单关？**  
A: 竞彩足球并非所有比赛都支持单关投注，这由体彩中心决定。

**Q: 多久更新一次数据？**  
A: 页面每30秒自动更新一次，也可以手动运行爬虫更新。

**Q: 如何判断某个玩法是否支持单关？**  
A: 查看 `poolList` 中的 `cbtSingle` 字段，1表示支持，0表示不支持。

## 更新日志

### 2026-03-18 (第四次优化)
- ✅ 调整边框颜色，从过淡的#ffd0d0改为适中的#ffb3b3
- ✅ 边框清晰可见，但不会过于显眼
- ✅ 标签背景从#ffd0d0改为#ffe5e5，文字保持深红色
- ✅ 渐变背景调整为#fff8f8，更易识别

### 2026-03-18 (第三次优化)
- ✅ 弱化边框颜色，从红色(#ff6b6b)改为淡粉色(#ffd0d0)
- ✅ 边框宽度从2px减为1px，更细更低调
- ✅ 优化渐变背景，使用更淡的颜色(#fffbfb)
- ✅ 减小圆角从6px到4px，更加精致
- ✅ 标签颜色也相应弱化，整体视觉更协调

## 技术支持

如遇问题，请运行测试脚本诊断：
```bash
python3 test_single_pass.py
```