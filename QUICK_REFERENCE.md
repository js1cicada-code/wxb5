# 单关边框功能 - 快速参考

## 一、查看效果

### 方法1: 测试页面
```bash
open test_border.html
```

### 方法2: 完整服务
```bash
npm run dev
# 访问 http://localhost:8082
```

## 二、验证功能

```bash
python3 verify_border.py
```

## 三、更新单关数据

```bash
python3 single_pass_crawler.py
# 或
./update_single_pass.sh
```

## 四、边框样式

```css
/* 颜色方案 */
边框颜色: #ffb3b3        /* 粉红色，清晰可见 */
渐变开始: #fff8f8        /* 浅粉 */
渐变结束: #ffffff        /* 白色 */
文字颜色: #c41230        /* 深红 */

/* 尺寸参数 */
边框宽度: 1px            /* 细线 */
圆角半径: 4px            /* 小圆角 */
内边距:   4px 4px        /* 紧凑 */
```

## 五、适用玩法

| 玩法类型 | 代码标识 | 是否支持 |
|---------|---------|---------|
| 胜平负   | spf     | ✅      |
| 让球胜平负| rqspf   | ✅      |
| 比分     | bf      | ✅      |
| 总进球   | zjq     | ✅      |
| 半全场   | bqc     | ✅      |

## 六、判断逻辑

```javascript
// 判断是否支持单关
if (isSinglePassAvailable(matchId, playType)) {
    // 显示红色边框
}
```

## 七、显示位置

1. **混合过关主页** - 胜平负/让球胜平负
2. **单独玩法页** - 所有玩法
3. **更多玩法弹窗** - 比分/总进球/半全场

## 八、视觉效果

```
不支持单关: 普通显示，无特殊标识
支持单关:   细线粉红边框 + 单关标签（清晰可见但不显眼）
```

## 九、相关文件

- `index.html` - 主页面（含CSS和JS）
- `single_pass_crawler.py` - 数据爬虫
- `test_border.html` - 效果测试页
- `verify_border.py` - 功能验证
- `demo_border.sh` - 演示脚本

## 十、常见问题

**Q: 边框不显示？**
A: 运行 `python3 verify_border.py` 检查

**Q: 如何修改颜色？**
A: 编辑 index.html 中的 `.odds-row.single-pass` 样式

**Q: 数据如何更新？**
A: 每30秒自动更新，或手动运行爬虫

---

更多信息请查看:
- `README_SINGLE_PASS.md` - 完整使用说明
- `BORDER_FEATURE_SUMMARY.md` - 功能实现总结