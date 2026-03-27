# 数据爬取 RCA (Root Cause Analysis)

## 问题记录

### 问题1: 页面类型判断错误 - 静态 vs 动态

**现象：**
- 使用urllib获取500彩票网移动端页面，返回空数据或缺少关键信息
- 正则表达式匹配不到球队名、namitiyu ID等

**原因：**
- 没有先判断目标页面是静态HTML还是JavaScript渲染
- urllib只能获取静态HTML，无法执行JavaScript
- 移动端页面 `app-live-m.500.com` 需要JavaScript渲染

**解决方案：**
```python
# 判断方法：用urllib获取后检查内容
import urllib.request
html = response.read().decode('utf-8')

# 如果关键内容缺失 → 页面需要JavaScript渲染 → 改用Playwright
if '关键内容' not in html:
    # 改用Playwright
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(3000)  # 等待JS渲染
        html = page.content()
        browser.close()
```

**经验教训：**
- PC端页面通常是静态HTML（如 `odds.500.com`）
- 移动端页面通常需要JavaScript渲染（如 `app-live-m.500.com`）
- 先用urllib试一下，如果内容不对再用Playwright

---

### 问题2: 竞彩篮球数据格式 - 主客队顺序

**现象：**
- 匹配不到比赛数据，明明两队名都有

**原因：**
- 竞彩篮球显示格式：**客队在左，主队在右**
- 500彩票网移动端：`teams[0]`=客队, `teams[1]`=主队
- sporttery API：`homeTeamAbbName`=主队, `awayTeamAbbName`=客队
- 匹配时主队要对应主队，客队要对应客队

**正确理解：**
```
竞彩显示: 客队 vs 主队 (客在左，主在右)
500彩票网: teams[0]=客队, teams[1]=主队
sporttery: home=主队, away=客队
```

**解决方案：**
```python
# 500彩票网移动端
teams = re.findall(r'class="team"[^>]*>([^<]+)<', html)
away_team = teams[0]  # 客队
home_team = teams[1]  # 主队

# sporttery
home = match.get('homeTeamAbbName')  # 主队
away = match.get('awayTeamAbbName')  # 客队

# 匹配逻辑：主队对主队，客队对客队
if sporttery_home == fid_home and sporttery_away == fid_away:
    return matched
```

---

### 问题3: 球队名不一致 - 别名映射

**现象：**
- `皇马` 匹配不到 `皇家马德里`
- `埃菲斯` 匹配不到 `艾菲斯`

**原因：**
- 不同数据源使用不同的球队名
- 简称 vs 全称

**解决方案：**
```python
TEAM_ALIASES = {
    '皇马': ['皇家马德里'],
    '皇家马德里': ['皇马'],
    '埃菲斯': ['艾菲斯', '安纳托利亚艾菲斯'],
    '艾菲斯': ['埃菲斯', '安纳托利亚艾菲斯'],
    '活塞': ['底特律活塞'],
    '鹈鹕': ['新奥尔良鹈鹕'],
    # ... 更多别名
}

def match_with_aliases(team1, team2):
    """使用别名匹配"""
    aliases1 = TEAM_ALIASES.get(team1, []) + [team1]
    aliases2 = TEAM_ALIASES.get(team2, []) + [team2]
    
    for a1 in aliases1:
        for a2 in aliases2:
            if a1 == a2 or a1 in a2 or a2 in a1:
                return True
    return False
```

---

### 问题4: 日期计算越界

**现象：**
- `day is out of range for month` 错误

**原因：**
- 使用 `today.replace(day=today.day + days_diff)` 计算日期
- 当 `today.day + days_diff` 超过当月天数时越界

**错误代码：**
```python
match_date_calc = today.replace(day=today.day + days_diff)  # ❌ 可能越界
```

**正确代码：**
```python
from datetime import timedelta
match_date_calc = today + timedelta(days=days_diff)  # ✅ 使用timedelta
```

---

### 问题5: 数据文件路径不一致

**现象：**
- 页面获取不到数据
- 检查数据文件发现缺少字段

**原因：**
- `dist/live_data.json` 和 `dist/data/live_data.json` 是两个文件
- 爬虫更新了 `dist/` 目录，但页面从 `dist/data/` 读取

**解决方案：**
```python
def save_data(data, filename):
    # 同时保存到两个位置
    with open(os.path.join(DIST_DIR, filename), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(DIST_DIR, 'data', filename), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

---

### 问题6: Playwright性能问题

**现象：**
- 每次获取详情页都启动新浏览器，速度很慢

**原因：**
- 在循环中每次调用 `get_fid_detail()` 都启动新的Playwright浏览器

**错误代码：**
```python
for fid in fids:
    info = get_fid_detail(fid)  # 每次都启动新浏览器
```

**正确代码：**
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for fid in fids:
        page.goto(f'{url}/{fid}')
        # ... 提取数据
    
    browser.close()  # 只启动一次浏览器
```

---

## 最佳实践

### 1. 爬取流程

```
1. 先用urllib尝试获取页面
2. 检查关键内容是否存在
3. 如果不存在 → 改用Playwright
4. 如果是JavaScript渲染页面，直接用Playwright
```

### 2. 数据源优先级

```
1. API接口（最快，数据结构清晰）
2. 静态HTML页面（urllib即可）
3. JavaScript渲染页面（需要Playwright）
```

### 3. 球队名匹配

```
1. 精确匹配
2. 包含匹配（A in B 或 B in A）
3. 别名匹配
4. 模糊匹配（主队对主队，客队对客队）
```

### 4. 测试验证

```python
# 每次爬取后验证
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 测试动画是否正确
    page.goto(f'https://tracker.namitiyu.com/...&id={nid}')
    content = page.inner_text('body')
    
    if home in content and away in content:
        print(f'✅ {home} vs {away}: 动画正确')
    else:
        print(f'❌ 动画错误')
```

---

## 快速检查清单

- [ ] 页面是静态还是动态？（urllib试试）
- [ ] 主客队顺序正确吗？（客在左，主在右）
- [ ] 球队名有别名吗？（添加别名映射）
- [ ] 日期计算用timedelta了吗？
- [ ] 数据保存到两个位置了吗？
- [ ] Playwright浏览器复用了吗？
- [ ] 测试验证动画内容了吗？