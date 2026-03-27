#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
篮球比分直播数据爬虫 - 完整版
支持实时比分、状态判断、虚拟倒计时
"""

import json
import os
import re
from datetime import datetime, timedelta
import urllib.request
import ssl
import gzip

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 球队名别名映射
TEAM_ALIASES = {
    # 欧篮联
    '维图斯': ['博洛尼亚', '博洛尼', '博洛尼亚维图斯'],
    '博洛尼亚': ['维图斯', '博洛尼'],
    '米兰': ['米兰奥林匹亚', '奥林匹亚米兰', '阿玛尼米兰'],
    '拜仁': ['拜仁慕尼黑'],
    '阿斯维尔': ['里昂维勒班', '维勒班'],
    '皇马': ['皇家马德里'],
    '皇家马德里': ['皇马'],
    '埃菲斯': ['艾菲斯', '阿纳多卢埃菲斯', '安纳托利亚艾菲斯'],
    '艾菲斯': ['埃菲斯', '阿纳多卢埃菲斯', '安纳托利亚艾菲斯'],
    '特马卡比': ['特拉维夫马卡比', '马卡比'],
    '迪拜': ['迪拜篮球俱乐部', '迪拜BC'],
    '巴萨': ['巴塞罗那', 'FC巴塞罗那'],
    '巴塞罗那': ['巴萨', 'FC巴塞罗那'],
    '贝红星': ['贝尔格莱德红星', '红星', '贝尔格莱德'],
    '贝尔格莱德红星': ['贝红星', '红星'],
    '帕纳辛纳': ['帕纳辛奈科斯', '帕纳辛纳科斯'],
    '摩纳哥': ['AS摩纳哥'],
    '贝游击': ['贝尔格莱德游击队', '游击队'],
    '巴伦西亚': ['瓦伦西亚'],
    
    # NBA
    '活塞': ['底特律活塞'],
    '鹈鹕': ['新奥尔良鹈鹕'],
    '尼克斯': ['纽约尼克斯'],
    '黄蜂': ['夏洛特黄蜂'],
    '国王': ['萨克拉门托国王'],
    '魔术': ['奥兰多魔术'],
    '快船': ['洛杉矶快船'],
    '步行者': ['印第安纳步行者'],
    '热火': ['迈阿密热火'],
    '骑士': ['克利夫兰骑士'],
    '老鹰': ['亚特兰大老鹰'],
    '凯尔特人': ['波士顿凯尔特人'],
    '公牛': ['芝加哥公牛'],
    '雷霆': ['俄克拉荷马雷霆'],
    '火箭': ['休斯顿火箭'],
    '灰熊': ['孟菲斯灰熊'],
    '猛龙': ['多伦多猛龙'],
    '爵士': ['犹他爵士'],
    '掘金': '丹佛掘金',
    '奇才': ['华盛顿奇才'],
    '勇士': ['金州勇士'],
    '独行侠': ['达拉斯独行侠', '达拉斯'],
    '开拓者': ['波特兰开拓者'],
    '篮网': ['布鲁克林篮网'],
    '湖人': ['洛杉矶湖人'],
}


def get_aliases(team_name):
    """获取球队的所有别名"""
    aliases = [team_name]
    for key, values in TEAM_ALIASES.items():
        if team_name in values or team_name == key:
            aliases.extend(values)
            aliases.append(key)
    return list(set(aliases))


def fetch_basketball_data():
    """获取篮球比分数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = 'https://webapi.sporttery.cn/gateway/uniform/basketball/getMatchCalculatorV1.qry?channel=1'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://www.sporttery.cn/'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return parse_basketball_data(data)
    except Exception as e:
        print(f'获取篮球数据失败: {e}')
        return None


def fetch_500_all_matches():
    """从500彩票网获取所有篮球比赛详情 - 使用单个Playwright浏览器"""
    from playwright.sync_api import sync_playwright
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # 获取所有fid
    url = 'https://live.500.com/static/info/bifen/xml/livedata/lq/FullJson.txt'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
    
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = resp.read()
        try:
            data = gzip.decompress(data)
        except:
            pass
        match_list = json.loads(data.decode('utf-8', errors='ignore'))
        fids = [str(m[0]) for m in match_list if len(m) > 0 and m[0]]
    
    print(f"    500彩票网共有 {len(fids)} 场篮球比赛")
    
    matches_500 = []
    now = datetime.now()
    current_year = now.year
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)')
        
        for i, fid in enumerate(fids):
            try:
                page.goto(f'https://app-live-m.500.com/detail/basketball/{fid}/', timeout=15000)
                page.wait_for_timeout(800)
                
                html = page.content()
                text = page.inner_text('body')
                
                # 提取日期时间 - 格式: "03-27 07:00"
                date_match = re.search(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', html)
                match_date = ''
                match_time = ''
                if date_match:
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    match_time = f"{date_match.group(3)}:{date_match.group(4)}"
                    
                    if month < now.month:
                        year = current_year
                    elif month == now.month and day <= now.day:
                        year = current_year
                    elif month > now.month:
                        year = current_year - 1
                    else:
                        year = current_year
                    
                    match_date = f"{year}-{month:02d}-{day:02d}"
                
                # 从标题提取球队
                title_match = re.search(r'【(.+?)】vs【(.+?)】', html)
                
                # 提取namitiyu ID
                namitiyu = re.search(r'tracker\.namitiyu\.com[^"\'<>]*id=(\d+)', html)
                
                # 从页面提取比分和判断状态
                home_score = 0
                away_score = 0
                status = 'upcoming'
                
                # 首先检查明确的状态文字
                if '完场' in text or '已结束' in text or '全场结束' in text:
                    status = 'finished'
                elif '进行中' in text or ('第' in text and '节' in text):
                    status = 'live'
                
                # 提取比分
                score_pattern = r'(\d{2,3})\s*[:\uff1a]\s*(\d{2,3})'
                score_matches = re.findall(score_pattern, text[:500])
                
                # 过滤时间格式
                valid_scores = []
                for s in score_matches:
                    # 时间格式：HH:MM，都小于24且第二个<60
                    if int(s[0]) < 24 and int(s[1]) < 60:
                        continue
                    valid_scores.append(s)
                
                if valid_scores:
                    away_score = int(valid_scores[0][0])
                    home_score = int(valid_scores[0][1])
                    
                    # 如果有有效比分，判断为已结束或进行中
                    if status == 'upcoming' and (away_score > 0 or home_score > 0):
                        # 根据日期判断
                        if match_date:
                            try:
                                match_dt = datetime.strptime(match_date, '%Y-%m-%d')
                                if match_dt.date() < now.date():
                                    status = 'finished'
                                elif match_dt.date() == now.date():
                                    # 今天的比赛，检查时间
                                    if match_time:
                                        try:
                                            h, m = map(int, match_time.split(':'))
                                            match_datetime = match_dt.replace(hour=h, minute=m)
                                            # NBA比赛约2.5小时，CBA约2小时
                                            if now > match_datetime + timedelta(hours=3):
                                                status = 'finished'
                                            elif now >= match_datetime:
                                                status = 'live'
                                        except:
                                            status = 'finished'
                            except:
                                pass
                
                info = None
                if title_match:
                    info = {
                        'fid': fid,
                        'away_team': title_match.group(1),
                        'home_team': title_match.group(2),
                        'namitiyuId': namitiyu.group(1) if namitiyu else None,
                        'match_date': match_date,
                        'match_time': match_time,
                        'home_score': home_score,
                        'away_score': away_score,
                        'status': status
                    }
                else:
                    teams = re.findall(r'class="[^"]*team[^"]*"[^>]*>([^<]+)<', html)
                    if len(teams) >= 2:
                        info = {
                            'fid': fid,
                            'away_team': teams[0],
                            'home_team': teams[1],
                            'namitiyuId': namitiyu.group(1) if namitiyu else None,
                            'match_date': match_date,
                            'match_time': match_time,
                            'home_score': home_score,
                            'away_score': away_score,
                            'status': status
                        }
                
                if info:
                    matches_500.append(info)
                    
            except Exception as e:
                pass
        
        browser.close()
    
    return matches_500


def get_fid_detail(fid):
    """从500彩票网移动端详情页获取比赛信息 - 使用Playwright"""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)')
        
        try:
            page.goto(f'https://app-live-m.500.com/detail/basketball/{fid}/recommend/predict', timeout=15000)
            page.wait_for_timeout(2000)
            
            html = page.content()
            browser.close()
            
            # 从标题提取 (最可靠)
            title_match = re.search(r'【(.+?)】vs【(.+?)】', html)
            
            # 从team class提取
            teams = re.findall(r'class="[^"]*team[^"]*"[^>]*>([^<]+)<', html)
            
            # 提取namitiyu ID
            namitiyu = re.search(r'tracker\.namitiyu\.com[^"\'<>]*id=(\d+)', html)
            
            # 优先使用标题中的球队名
            if title_match:
                return {
                    'away_team': title_match.group(1),
                    'home_team': title_match.group(2),
                    'namitiyuId': namitiyu.group(1) if namitiyu else None
                }
            elif len(teams) >= 2:
                return {
                    'away_team': teams[0],
                    'home_team': teams[1],
                    'namitiyuId': namitiyu.group(1) if namitiyu else None
                }
        except Exception as e:
            browser.close()
    
    return None


def parse_basketball_data(data):
    """解析篮球数据"""
    matches = []
    
    if not data.get('success') or not data.get('value', {}).get('matchInfoList'):
        return None
    
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    for day_match in data['value']['matchInfoList']:
        if not day_match.get('subMatchList'):
            continue
        
        business_date = day_match.get('businessDate', '')
        
        for match in day_match['subMatchList']:
            match_num = match.get('matchNumStr', '')
            match_id = str(match.get('matchId', ''))
            match_time = match.get('matchTime', '')
            hour = 0
            if match_time:
                try:
                    hour = int(match_time.split(':')[0])
                except:
                    pass
            
            # 凌晨0-12点的比赛，实际日期是businessDate的下一天
            if business_date:
                try:
                    year, month, day = business_date.split('-')
                    date_obj = datetime(int(year), int(month), int(day))
                    
                    # 凌晨比赛（0-12点），日期+1天
                    if 0 <= hour < 12:
                        date_obj = date_obj + timedelta(days=1)
                    
                    actual_date_str = date_obj.strftime('%Y-%m-%d')
                    weekday_name = weekdays[date_obj.weekday()]
                    
                    if actual_date_str == today_str:
                        match_date_display = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日 今天 {weekday_name}"
                    else:
                        match_date_display = f"{date_obj.year}年{date_obj.month}月{date_obj.day}日 {weekday_name}"
                except:
                    match_date_display = ''
            else:
                match_date_display = ''
            
            matches.append({
                'id': match_id,
                'matchNum': match_num,
                'league': match.get('leagueAbbName', ''),
                'date': match_date_display,
                'time': match_time[:5] if match_time else '',
                'home': match.get('homeTeamAbbName', ''),
                'away': match.get('awayTeamAbbName', ''),
                'homeScore': 0,
                'awayScore': 0,
                'status': 'upcoming',
                'minute': '',
                'statusOrder': 2
            })
    
    matches.sort(key=lambda x: (
        0 if '今天' in x.get('date', '') else 1,
        x.get('date', ''),
        x.get('time', '')
    ))
    
    return matches


def fetch_500_live_scores():
    """从500彩票网FullJson获取篮球实时比分和状态"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    now = datetime.now()
    
    # 星期映射
    weekday_map = {'周一': 0, '周二': 1, '周三': 2, '周四': 3, '周五': 4, '周六': 5, '周日': 6}
    today_weekday = now.weekday()
    
    live_data = {}
    
    # 使用FullJson接口获取比赛数据
    url = 'https://live.500.com/static/info/bifen/xml/livedata/lq/FullJson.txt'
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
            try:
                data = gzip.decompress(data)
            except:
                pass
            
            match_list = json.loads(data.decode('utf-8', errors='ignore'))
            
            for m in match_list:
                if len(m) < 5:
                    continue
                
                fid = str(m[0])
                status_code = str(m[1]) if len(m) > 1 else '0'
                home_scores_str = str(m[2]) if len(m) > 2 else ''
                away_scores_str = str(m[3]) if len(m) > 3 else ''
                time_str = str(m[4]) if len(m) > 4 else ''
                
                # 解析比分
                # 格式: '33-23-30-22' 或 '33-23-30-22/12' (加时赛)
                home_total = 0
                away_total = 0
                
                if home_scores_str and home_scores_str != '---':
                    # 移除加时赛分数
                    home_main = home_scores_str.split('/')[0]
                    home_parts = home_main.split('-')
                    home_total = sum(int(x) for x in home_parts if x.isdigit())
                
                if away_scores_str and away_scores_str != '---':
                    away_main = away_scores_str.split('/')[0]
                    away_parts = away_main.split('-')
                    away_total = sum(int(x) for x in away_parts if x.isdigit())
                
                # 判断状态
                # 状态码: 1=未开始, 11=已结束, 其他=进行中
                status = 'upcoming'
                minute = ''
                
                if status_code == '11':
                    status = 'finished'
                elif status_code == '1':
                    status = 'upcoming'
                elif home_total > 0 or away_total > 0:
                    status = 'live'
                    # time_str可能是 '00:13' 这样的时间
                    if time_str and ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) == 2:
                            try:
                                mins = int(parts[0])
                                secs = int(parts[1])
                                minute = str(mins * 60 + secs)
                            except:
                                minute = ''
                
                # 保存数据
                key = fid
                live_data[key] = {
                    'fid': fid,
                    'homeScore': home_total,
                    'awayScore': away_total,
                    'status': status,
                    'minute': minute,
                    'homeScores': home_scores_str,
                    'awayScores': away_scores_str,
                    'time': time_str
                }
            
            print(f"    获取 {len(live_data)} 场篮球实时比分")
            
    except Exception as e:
        print(f"    获取实时比分失败: {e}")
    
    return live_data


def match_teams_flexible(sporttery_home, sporttery_away, matches_500):
    """灵活匹配球队名 - 要求主客队都匹配"""
    home_aliases = get_aliases(sporttery_home)
    away_aliases = get_aliases(sporttery_away)
    
    best_match = None
    best_score = 0
    
    for m in matches_500:
        fid_home = m.get('home_team', '')
        fid_away = m.get('away_team', '')
        
        fid_home_aliases = get_aliases(fid_home)
        fid_away_aliases = get_aliases(fid_away)
        
        home_score = 0
        away_score = 0
        
        # 主队匹配评分
        if sporttery_home == fid_home:
            home_score = 2
        elif sporttery_home in fid_home or fid_home in sporttery_home:
            home_score = 1
        else:
            for alias in home_aliases:
                if alias == fid_home or fid_home in alias or alias in fid_home:
                    home_score = 1
                    break
        
        # 客队匹配评分
        if sporttery_away == fid_away:
            away_score = 2
        elif sporttery_away in fid_away or fid_away in sporttery_away:
            away_score = 1
        else:
            for alias in away_aliases:
                if alias == fid_away or fid_away in alias or alias in fid_away:
                    away_score = 1
                    break
        
        # 主客队都必须匹配（至少各得1分）
        if home_score >= 1 and away_score >= 1:
            total = home_score + away_score
            if total > best_score:
                best_score = total
                best_match = m
    
    return best_match


def save_data(data, filename):
    """保存数据到多个位置"""
    paths = [
        os.path.join(BASE_DIR, 'dist', filename),
        os.path.join(BASE_DIR, 'dist', 'data', filename),
        os.path.join(BASE_DIR, 'data', filename)
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f'数据已保存到 {len(paths)} 个位置')


if __name__ == '__main__':
    print('=' * 50)
    print('篮球比分直播爬虫')
    print('=' * 50)
    
    # 1. 从sporttery获取赛程
    print('\n>>> 从sporttery获取赛程...')
    sporttery_matches = fetch_basketball_data()
    
    # 2. 从500彩票网获取比赛详情（包含比分、状态、日期）
    print('\n>>> 从500彩票网获取比赛详情...')
    matches_500 = fetch_500_all_matches()
    
    # 合并数据
    matches = []
    processed_fids = set()
    
    # 处理sporttery的比赛
    if sporttery_matches:
        for m in sporttery_matches:
            home = m.get('home', '')
            away = m.get('away', '')
            
            # 匹配500详情获取fid、比分、状态等
            matched = match_teams_flexible(home, away, matches_500)
            fid = ''
            namitiyuId = ''
            
            if matched:
                fid = matched.get('fid', '')
                namitiyuId = matched.get('namitiyuId', '')
                processed_fids.add(fid)
                
                # 使用500.com的比分和状态
                m['fid'] = fid
                m['homeScore'] = matched.get('home_score', 0)
                m['awayScore'] = matched.get('away_score', 0)
                m['status'] = matched.get('status', 'upcoming')
                m['minute'] = matched.get('minute', '')
                
                if namitiyuId:
                    m['namitiyuId'] = namitiyuId
            else:
                m['fid'] = ''
            
            # 设置saleDateDisplay
            if not m.get('saleDateDisplay'):
                date_str = m.get('date', '')
                if date_str:
                    match = re.search(r'(\d{4})年(\d+)月(\d+)日', date_str)
                    if match:
                        year, month, day = match.groups()
                        m['saleDateDisplay'] = f"{year}-{int(month):02d}-{int(day):02d}"
            
            matches.append(m)
    
    # 统计状态
    live_count = len([m for m in matches if m.get('status') == 'live'])
    finished_count = len([m for m in matches if m.get('status') == 'finished'])
    upcoming_count = len([m for m in matches if m.get('status') == 'upcoming'])
    
    print(f"\n>>> 支持动画直播: {len([m for m in matches if m.get('fid')])}场")
    print(f">>> 支持namitiyu动画: {len([m for m in matches if m.get('namitiyuId')])}场")
    print(f">>> 进行中: {live_count}场, 已结束: {finished_count}场, 未开始: {upcoming_count}场")
    
    # 构建输出数据
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'matches': matches,
        'total': len(matches),
        'live': live_count,
        'upcoming': upcoming_count,
        'finished': finished_count
    }
    
    # 保存数据
    save_data(output, 'live_basketball_data.json')
    
    # 按开售日期统计
    by_date = {}
    for m in matches:
        sd = m.get('saleDateDisplay', 'N/A')
        by_date[sd] = by_date.get(sd, 0) + 1
    
    print("\n按开售日期统计:")
    for sd, count in sorted(by_date.items()):
        print(f"  {sd}: {count}场")