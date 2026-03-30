#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比赛分析数据爬虫模块（完整版）
============================

功能说明：
    从500彩票网爬取足球比赛的完整分析数据

数据模块：
    1. 球队排名信息 - 赛前排名、上赛季排名
    2. 赛前积分榜 - 联赛积分排名表、主客队详细排名
    3. 交战历史 - 统计+比赛列表
    4. 近期战绩 - 主客队近期比赛列表
    5. 未来赛事 - 主客队未来比赛
    6. 平均数据 - 平均入球、失球
    7. 预计阵容 - 首发、替补、伤病、停赛
    8. 心水推荐 - 近况、盘路、推介
    9. 亚盘数据
    10. 欧赔数据

作者：自动生成
日期：2026-03
"""

import json
import os
import re
import time
import requests
from datetime import datetime

# ============================================================
# 配置
# ============================================================

DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'data')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

TIMEOUT = 15

CANTONESE_TO_SIMPLIFIED = {
    '甘堡尔': '坎布尔', '安曼': '埃门', '燕豪芬': '埃因霍温', '阿积士': '阿贾克斯',
    '费耶诺德': '费耶诺德', '乌德勒支': '乌得勒支', '海伦维恩': '海伦芬',
    '维迪斯': '维特斯', '艾克马亚': '阿尔克马尔', '施禾利': '兹沃勒',
    '高宁根': '格罗宁根', '威廉二世': '威廉二世', '奈梅亨': '奈梅亨',
    '福图纳': '福图纳', '芬洛': '芬洛', '阿梅利': '阿梅利',
    '皇马': '皇马', '巴塞': '巴萨', '马体会': '马竞', '西维尔': '塞维利亚',
    '华伦西亚': '瓦伦西亚', '维拉利尔': '比利亚雷亚尔', '贝迪斯': '贝蒂斯',
    '皇家苏斯达': '皇家社会', '毕尔包': '毕尔巴鄂', '切尔达': '塞尔塔',
    '奥沙辛拿': '奥萨苏纳', '杰罗纳': '赫罗纳', '巴伦西亚': '瓦伦西亚',
    '曼联': '曼联', '曼城': '曼城', '利物浦': '利物浦', '车路士': '切尔西',
    '阿仙奴': '阿森纳', '热刺': '热刺', '爱华顿': '埃弗顿', '韦斯咸': '西汉姆',
    '纽卡素': '纽卡斯尔', '李斯特城': '莱斯特城', '修咸顿': '南安普顿',
    '水晶宫': '水晶宫', '白礼顿': '布莱顿', '狼队': '狼队', '阿士东维拉': '维拉',
    '富咸': '富勒姆', '宾福特': '布伦特福德', '般尼': '伯恩利', '锡菲联': '谢菲联',
    '诺定咸森林': '诺丁汉森林', '卢顿': '卢顿', '伯恩茅斯': '伯恩茅斯',
    '拜仁': '拜仁', '多蒙特': '多特', '莱比锡': '莱比锡', '利华古炼': '勒沃库森',
    '史特加': '斯图加特', '法兰克福': '法兰克福', '禾夫斯堡': '沃尔夫斯堡',
    '门兴': '门兴', '费雷堡': '弗赖堡', '贺芬咸': '霍芬海姆', '缅恩斯': '美因茨',
    '奥格斯堡': '奥格斯堡', '柏林联': '柏林联合', '波琴': '波鸿', '海登咸': '海登海姆',
    '达斯泰特': '达姆施塔特', '科隆': '科隆', '云达不莱梅': '不来梅',
    '祖云达斯': '尤文图斯', 'AC米兰': 'AC米兰', '国际米兰': '国米', '拿玻里': '那不勒斯',
    '罗马': '罗马', '拉素': '拉齐奥', '亚特兰大': '亚特兰大', '佛罗伦萨': '佛罗伦萨',
    '博洛尼亚': '博洛尼亚', '拖连奴': '都灵', '乌甸尼斯': '乌迪内斯', '萨索罗': '萨索洛',
    '恩波里': '恩波利', '维罗纳': '维罗纳', '卡利亚里': '卡利亚里', '莱切': '莱切',
    '热那亚': '热那亚', '蒙沙': '蒙扎', '费辛隆尼': '弗洛西诺内', '萨勒尼塔纳': '萨勒尼塔纳',
    '宾菲加': '本菲卡', '波图': '波尔图', '士砵亭': '葡萄牙体育', '布拉加': '布拉加',
    'PSV燕豪芬': 'PSV埃因霍温', '飞燕诺': '费耶诺德', '阿积士': '阿贾克斯',
    '圣日门': '巴黎', '摩纳哥': '摩纳哥', '马赛': '马赛', '里昂': '里昂', '里尔': '里尔',
    '尼斯': '尼斯', '朗斯': '朗斯', '雷恩': '雷恩', '蒙彼利埃': '蒙彼利埃',
    '今季': '本赛季', '上季': '上赛季', '下季': '下赛季',
    '和': '平', '负': '负', '胜': '胜',
    ' A': ' 胜', ' D': ' 平', ' H': ' 负',
    'A': '主胜', 'D': '平局', 'H': '客胜',
    '仗': '场', '佳绩': '好成绩', '看高一线': '看好',
    '坐拥': '拥有', '此番': '本场', '斩获': '取得',
}


def convert_to_simplified(text):
    """粤语译名转简体"""
    if not text:
        return text
    for cantonese, simplified in CANTONESE_TO_SIMPLIFIED.items():
        text = text.replace(cantonese, simplified)
    return text


# ============================================================
# 辅助函数
# ============================================================

def clean(text):
    """清理HTML标签"""
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'球$', '', text)
    return text


def num(text):
    """解析数字"""
    text = clean(text)
    if not text or text == '-':
        return None
    try:
        return int(float(text.replace(',', '')))
    except:
        return None


# ============================================================
# fixtureId映射
# ============================================================

def fetch_fixture_mapping():
    """获取fixtureId映射"""
    url = 'https://trade.500.com/jczq/index.php?playid=312&g=2'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        
        mapping = {}
        for m in re.finditer(r'data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"', resp.text):
            fixture_id, home, away = m.groups()
            context = resp.text[max(0, m.start()-500):m.end()+500]
            league = re.search(r'data-simpleleague="([^"]*)"', context)
            date = re.search(r'data-matchdate="([^"]*)"', context)
            time = re.search(r'data-matchtime="([^"]*)"', context)
            
            key = f"{home}_{away}"
            mapping[key] = {
                'fixtureId': fixture_id,
                'home': home,
                'away': away,
                'league': league.group(1) if league else '',
                'date': date.group(1) if date else '',
                'time': time.group(1) if time else ''
            }
        
        print(f"获取到 {len(mapping)} 场比赛")
        return mapping
    except Exception as e:
        print(f"获取fixtureId失败: {e}")
        return {}


# ============================================================
# 数据分析页面
# ============================================================

def fetch_data_analysis(fixture_id, result):
    """获取数据分析页面所有数据"""
    url = f'https://odds.500.com/fenxi/shuju-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        html = resp.text
        
        # 球队名称
        m = re.search(r'<title>(.+?)VS(.+?)\(', html)
        if m:
            result['home'] = m.group(1).strip()
            result['away'] = m.group(2).strip()
        
        # 联赛名称
        m = re.search(r'<div class="odds_hd_ls"[^>]*>.*?<a[^>]*>([^<]+)', html)
        if m:
            league_text = m.group(1).strip()
            # 提取联赛名称，如"25/26荷乙第22轮" -> "荷乙"
            league_match = re.search(r'(\d+/\d+)?(.+?)(第\d+轮)?$', league_text)
            if league_match:
                result['league'] = league_match.group(2).strip()
            else:
                result['league'] = league_text
        
        # 1. 球队排名信息
        parse_team_ranking(html, result)
        
        # 2. 赛前积分榜
        parse_standings(html, result)
        
        # 3. 积分排名详情
        parse_league_ranking(html, result)
        
        # 4. 交战历史
        parse_h2h(html, result)
        
        # 5. 近期战绩
        parse_recent_matches(html, result)
        
        # 6. 未来赛事
        parse_future_matches(html, result)
        
        # 7. 平均数据
        parse_average_stats(html, result)
        
        # 8. 预计阵容
        parse_lineup(html, result)
        
        # 9. 心水推荐
        parse_recommendation(html, result)
        
        print(f"  数据分析完成")
        
    except Exception as e:
        print(f"  数据分析失败: {e}")


def parse_team_ranking(html, result):
    """解析球队排名信息"""
    result['homeRanking'] = {}
    result['awayRanking'] = {}
    
    # 主队排名
    m = re.search(
        r'<a class="hd_name"[^>]*>([^<]+)</a></li><li>上赛季[^:]*排名[:：]?(\d+).*?赛前排名[:：]?<span[^>]*>(\d+)</span>',
        html, re.DOTALL
    )
    if m:
        result['homeRanking'] = {
            'team': m.group(1).strip(),
            'lastSeasonRank': num(m.group(2)),
            'currentRank': num(m.group(3))
        }
    
    # 客队排名
    m = re.search(
        r'<a class="hd_name"[^>]*>([^<]+)</a></li><li>赛前排名[:：]?<span[^>]*>(\d+)</span>.*?上赛季[^:]*排名[:：]?(\d+)',
        html, re.DOTALL
    )
    if m:
        result['awayRanking'] = {
            'team': m.group(1).strip(),
            'currentRank': num(m.group(2)),
            'lastSeasonRank': num(m.group(3))
        }


def parse_standings(html, result):
    """解析积分榜"""
    result['standings'] = []
    
    # 查找积分榜表格
    m = re.search(r'<div class="hd_box hd_jfb"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not m:
        return
    
    table = m.group(1)
    for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL):
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row.group(1), re.DOTALL)
        if len(cells) >= 3:
            rank = clean(cells[0])
            team = clean(cells[1])
            points = clean(cells[2])
            
            if rank and team and rank.isdigit():
                is_home = result.get('home') and team in result['home']
                is_away = result.get('away') and team in result['away']
                
                result['standings'].append({
                    'rank': int(rank),
                    'team': team,
                    'points': num(points),
                    'isHome': is_home,
                    'isAway': is_away
                })


def parse_league_ranking(html, result):
    """解析主客队详细积分排名"""
    result['homeLeagueRanking'] = None
    result['awayLeagueRanking'] = None
    
    # 查找赛前联赛积分排名区域
    section = re.search(r'赛前联赛积分排名</h4>(.*?)<!--两队交战史-->', html, re.DOTALL)
    if not section:
        return
    
    section_html = section.group(1)
    
    # 主队排名（team_a）
    home_table = re.search(r'team_a[^>]*>.*?<tbody>(.*?)</tbody>', section_html, re.DOTALL)
    if home_table:
        result['homeLeagueRanking'] = parse_ranking_table(home_table.group(1))
    
    # 客队排名（team_b）
    away_table = re.search(r'team_b[^>]*>.*?<tbody>(.*?)</tbody>', section_html, re.DOTALL)
    if away_table:
        result['awayLeagueRanking'] = parse_ranking_table(away_table.group(1))


def parse_ranking_table(table_html):
    """解析积分排名表格"""
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    data = []
    
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 11:
            type_text = clean(cells[0])
            if type_text == '总成绩':
                type_text = '总'
            elif type_text == '主场成绩':
                type_text = '主'
            elif type_text == '客场成绩':
                type_text = '客'
            
            matches_val = num(cells[1])
            win_val = num(cells[2])
            draw_val = num(cells[3])
            lose_val = num(cells[4])
            points_val = num(cells[8])
            rank_val = num(cells[9])
            
            if matches_val is None and win_val is None and points_val is None and rank_val is None:
                continue
            
            data.append({
                'type': type_text,
                'matches': matches_val,
                'win': win_val,
                'draw': draw_val,
                'lose': lose_val,
                'goals': num(cells[5]),
                'conceded': num(cells[6]),
                'diff': clean(cells[7]),
                'points': points_val,
                'rank': rank_val,
                'winRate': clean(cells[10])
            })
    
    return data if data else None


def parse_h2h(html, result):
    """解析交战历史"""
    result['h2h'] = None
    result['h2hMatches'] = []
    
    # 交战统计
    m = re.search(
        r'双方近.*?<span[^>]*>(\d+)</span>.*?次交战.*?'
        r'<em[^>]*>(\d+)胜</em>.*?<em[^>]*>(\d+)平</em>.*?<em[^>]*>(\d+)负</em>.*?'
        r'进(\d+)球.*?失(\d+)球.*?大球(\d+)次.*?小球(\d+)次',
        html, re.DOTALL
    )
    if m:
        result['h2h'] = {
            'total': num(m.group(1)),
            'homeWin': num(m.group(2)),
            'draw': num(m.group(3)),
            'awayWin': num(m.group(4)),
            'homeGoals': num(m.group(5)),
            'awayGoals': num(m.group(6)),
            'bigBall': num(m.group(7)),
            'smallBall': num(m.group(8))
        }
    
    # 交战比赛列表 - 在交战历史和近期战绩之间
    start = html.find('交战历史</h4>')
    end = html.find('<!-- 近期战绩 -->', start)
    if start > 0 and end > start:
        section = html[start:end]
        for row in re.finditer(r'<tr[^>]*fid="(\d+)"[^>]*>(.*?)</tr>', section, re.DOTALL):
            match = parse_match_row(row.group(2))
            if match:
                result['h2hMatches'].append(match)


def parse_match_row(row_html):
    """解析比赛数据行"""
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row_html, re.DOTALL)
    if len(cells) < 6:
        return None
    
    league = clean(re.search(r'<a[^>]*>([^<]+)</a>', cells[0], re.DOTALL).group(1) if re.search(r'<a[^>]*>([^<]+)</a>', cells[0], re.DOTALL) else '')
    date = clean(cells[1])
    score_match = re.search(r'title="([^V]+)VS([^"]+)"', cells[2])
    score = re.search(r'<em>([^<]+)</em>', cells[2])
    half = clean(cells[3])
    result_text = clean(cells[4])
    odds = re.findall(r'>([^<]+)<', cells[5]) if len(cells) > 5 else []
    asian = re.findall(r'>([^<]+)<', cells[6]) if len(cells) > 6 else []
    
    home_team = clean(score_match.group(1)) if score_match else ''
    away_team = clean(score_match.group(2)) if score_match else ''
    
    home_team = re.sub(r'数据分析$', '', home_team)
    away_team = re.sub(r'数据分析$', '', away_team)
    
    score_value = clean(score.group(1)) if score else ''
    if not score_value or score_value == 'VS':
        score_value = half
    
    return {
        'league': league,
        'date': date,
        'homeTeam': home_team,
        'awayTeam': away_team,
        'score': score_value,
        'half': half,
        'result': result_text,
        'odds': [clean(o) for o in odds[:3]],
        'asian': [clean(a) for a in asian[:3]]
    }


def parse_recent_matches(html, result):
    """解析近期战绩"""
    result['homeRecentStats'] = None
    result['awayRecentStats'] = None
    result['homeRecentMatches'] = []
    result['awayRecentMatches'] = []
    
    # 统计数据
    stats = re.findall(
        r'<strong>([^<]+)</strong>近\d+场战绩.*?'
        r'<span[^>]*>(\d+)胜</span>.*?<span[^>]*>(\d+)平</span>.*?<span[^>]*>(\d+)负</span>.*?'
        r'进.*?<span[^>]*>(\d+)球</span>.*?失.*?<span[^>]*>(\d+)球</span>',
        html, re.DOTALL
    )
    
    if len(stats) >= 1:
        result['homeRecentStats'] = {
            'team': clean(stats[0][0]),
            'win': num(stats[0][1]),
            'draw': num(stats[0][2]),
            'lose': num(stats[0][3]),
            'goals': num(stats[0][4]),
            'conceded': num(stats[0][5])
        }
    
    if len(stats) >= 2:
        result['awayRecentStats'] = {
            'team': clean(stats[1][0]),
            'win': num(stats[1][1]),
            'draw': num(stats[1][2]),
            'lose': num(stats[1][3]),
            'goals': num(stats[1][4]),
            'conceded': num(stats[1][5])
        }
    
    # 比赛列表 - 需要分别解析主客队
    # 这里简化处理，只取统计数据


def parse_future_matches(html, result):
    """解析未来赛事"""
    result['homeFutureMatches'] = []
    result['awayFutureMatches'] = []
    
    start = html.find('未来赛事</h4>')
    end = html.find('<!--平均数据分析-->', start)
    if start < 0 or end < start:
        return
    
    section = html[start:end]
    
    # 找到两个表格（team_a和team_b）
    tables = re.findall(r'<div class="team_[ab]"[^>]*>.*?<table[^>]*>(.*?)</table>', section, re.DOTALL)
    
    for i, table in enumerate(tables[:2]):
        for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL):
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row.group(1), re.DOTALL)
            if len(cells) >= 4:
                league_m = re.search(r'<a[^>]*>([^<]+)</a>', cells[0])
                league = clean(league_m.group(1)) if league_m else ''
                teams = re.findall(r'title="([^"]+)"', cells[2])
                
                match = {
                    'league': league,
                    'date': clean(cells[1]),
                    'homeTeam': teams[0] if len(teams) > 0 else '',
                    'awayTeam': teams[1] if len(teams) > 1 else '',
                    'days': clean(cells[3])
                }
                
                if i == 0:
                    result['homeFutureMatches'].append(match)
                else:
                    result['awayFutureMatches'].append(match)


def parse_average_stats(html, result):
    """解析平均数据"""
    result['homeAverageStats'] = None
    result['awayAverageStats'] = None
    
    section = re.search(r'平均数据</h4>(.*?)<!--预计阵容-->', html, re.DOTALL)
    if not section:
        return
    
    section_html = section.group(1)
    
    # 主队平均数据
    home_avg = re.search(
        r'team_a.*?平均入球</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?'
        r'平均失球</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>',
        section_html, re.DOTALL
    )
    if home_avg:
        result['homeAverageStats'] = {
            'avgGoals': clean(home_avg.group(1)),
            'homeGoals': clean(home_avg.group(2)),
            'awayGoals': clean(home_avg.group(3)),
            'avgConceded': clean(home_avg.group(4)),
            'homeConceded': clean(home_avg.group(5)),
            'awayConceded': clean(home_avg.group(6))
        }
    
    # 客队平均数据
    away_avg = re.search(
        r'team_b.*?平均入球</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?'
        r'平均失球</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>.*?<td>([^<]+)</td>',
        section_html, re.DOTALL
    )
    if away_avg:
        result['awayAverageStats'] = {
            'avgGoals': clean(away_avg.group(1)),
            'homeGoals': clean(away_avg.group(2)),
            'awayGoals': clean(away_avg.group(3)),
            'avgConceded': clean(away_avg.group(4)),
            'homeConceded': clean(away_avg.group(5)),
            'awayConceded': clean(away_avg.group(6))
        }


def parse_lineup(html, result):
    """解析预计阵容"""
    result['homeLineup'] = None
    result['awayLineup'] = None
    
    start = html.find('预计阵容</h4>')
    end = html.find('<!-- 澳门心水推荐', start)
    if start < 0 or end < start:
        return
    
    section = html[start:end]
    
    # 找到team_a和team_b区域
    team_a_start = section.find('<div class="team_a"')
    team_b_start = section.find('<div class="team_b"')
    
    if team_a_start > 0:
        team_a_end = team_b_start if team_b_start > team_a_start else len(section)
        team_a_html = section[team_a_start:team_a_end]
        result['homeLineup'] = parse_lineup_table(team_a_html)
    
    if team_b_start > 0:
        team_b_html = section[team_b_start:]
        result['awayLineup'] = parse_lineup_table(team_b_html)


def parse_lineup_table(table_html):
    """解析阵容表格"""
    lineup = {
        'starting': [],
        'substitute': [],
        'injured': [],
        'suspended': []
    }
    
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    current_section = 'starting'
    
    for row in rows:
        # 检查是否是标题行
        if '首发' in row:
            current_section = 'starting'
            continue
        elif '替补' in row:
            current_section = 'substitute'
            continue
        elif '伤病' in row:
            current_section = 'injured'
            continue
        elif '停赛' in row:
            current_section = 'suspended'
            continue
        
        # 提取球员
        players = re.findall(r'<span[^>]*>(\d+)</span>([^<]+)', row)
        for num_str, name in players:
            name_clean = clean(name)
            position = ''
            pos_match = re.search(r'\(([^)]+)\)$', name_clean)
            if pos_match:
                position = pos_match.group(1)
                name_clean = re.sub(r'\([^)]+\)$', '', name_clean)
            lineup[current_section].append({
                'number': num_str,
                'name': name_clean,
                'position': position
            })
    
    return lineup


def parse_recommendation(html, result):
    """解析心水推荐"""
    result['recommendation'] = None
    
    home_team = result.get('home', '')
    away_team = result.get('away', '')
    
    section = re.search(r'澳门心水推荐</h4>.*?<table[^>]*>(.*?)</table>', html, re.DOTALL)
    if not section:
        return
    
    section_html = section.group(1)
    
    def extract_form(text):
        fonts = re.findall(r'<font[^>]*>([WDL])</font>', text)
        return ''.join(fonts) if fonts else ''
    
    form_rows = re.findall(r'近况走势 - (.+?)</td>', section_html)
    home_form = extract_form(form_rows[0]) if len(form_rows) > 0 else ''
    away_form = extract_form(form_rows[1]) if len(form_rows) > 1 else ''
    
    def extract_asian(text):
        text = re.sub(r'<[^>]+>', '', text)
        return re.sub(r'[^WDL]', '', text)
    
    asian_rows = re.findall(r'盘路赢输 - (.+?)</td>', section_html)
    home_asian = extract_asian(asian_rows[0]) if len(asian_rows) > 0 else ''
    away_asian = extract_asian(asian_rows[1]) if len(asian_rows) > 1 else ''
    
    pick_match = re.search(r'推介\s*-\s*<font[^>]*>([^<]+)</font>', section_html)
    pick = pick_match.group(1) if pick_match else ''
    
    h2h_match = re.search(r'对赛成绩\s*-\s*([^<]+)', section_html)
    h2h_record = h2h_match.group(1) if h2h_match else ''
    
    reason_match = re.search(r'<td[^>]*class="[^"]*td_no4[^"]*"[^>]*>([^<]+)</td>', html, re.DOTALL)
    reason = reason_match.group(1) if reason_match else ''
    
    def clean_text(text):
        if not text:
            return ''
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = text.replace('\ufffd', '')
        text = re.sub(r'[^\u4e00-\u9fff\w\s\-:：,，、.。!?！?()（）]', '', text)
        return text.strip()
    
    pick = clean_text(pick)
    h2h_record = clean_text(h2h_record)
    reason = clean_text(reason)
    
    pick = convert_to_simplified(pick)
    h2h_record = convert_to_simplified(h2h_record)
    reason = convert_to_simplified(reason)
    
    result['recommendation'] = {
        'homeForm': home_form,
        'awayForm': away_form,
        'homeAsian': home_asian,
        'awayAsian': away_asian,
        'pick': pick,
        'h2hRecord': h2h_record,
        'reason': reason
    }


# ============================================================
# okooo.com 阵型数据
# 注意：okooo.com的matchId与500.com的fixtureId不同
# 需要通过球队名称匹配获取正确的matchId
# ============================================================

OKOOO_SESSION = None

def get_okooo_session():
    """获取okooo session（带WAF bypass）"""
    global OKOOO_SESSION
    if OKOOO_SESSION is None:
        OKOOO_SESSION = requests.Session()
        OKOOO_SESSION.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X_10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        # 访问首页初始化session
        try:
            OKOOO_SESSION.get("https://www.okooo.com/", timeout=10)
        except:
            pass
    return OKOOO_SESSION


def search_okooo_match(home_team, away_team):
    """在okooo.com竞彩页面搜索比赛ID"""
    session = get_okooo_session()
    
    try:
        # 访问竞彩页面
        resp = session.get("https://www.okooo.com/jingcai/", timeout=10)
        html = resp.content.decode('gb2312', errors='ignore')
        
        # 使用data-hname和data-aname属性匹配
        # 格式: data-mid="ID" ... data-hname="主队" data-aname="客队"
        pattern = r'data-mid="(\d+)"[^>]*data-hname="([^"]*)"[^>]*data-aname="([^"]*)"'
        matches = re.findall(pattern, html)
        
        for mid, hname, aname in matches:
            # 匹配球队名称
            if home_team and away_team:
                # 直接匹配
                if home_team in hname or hname in home_team:
                    if away_team in aname or aname in away_team:
                        return mid
                # 也检查反转（可能主客队顺序不同）
                if away_team in hname or hname in away_team:
                    if home_team in aname or aname in home_team:
                        return mid
                
    except Exception as e:
        print(f"  搜索okooo比赛失败: {e}")
    
    return None


def fetch_okooo_formation(fixture_id, result):
    """从okooo.com获取球队身价数据"""
    result['homeAbility'] = None
    result['awayAbility'] = None
    
    home_team = result.get('home', '')
    away_team = result.get('away', '')
    
    if not home_team or not away_team:
        return
    
    okooo_match_id = search_okooo_match(home_team, away_team)
    
    if not okooo_match_id:
        print(f"  okooo: 未找到对应比赛")
        return
    
    session = get_okooo_session()
    url = f"https://www.okooo.com/soccer/match/{okooo_match_id}/"
    
    try:
        session.get(url, timeout=10)
        time.sleep(0.3)
        
        resp = session.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"  okooo: 页面访问失败 {resp.status_code}")
            return
        
        html = resp.content.decode('gb2312', errors='ignore')
        
        ability = parse_okooo_team_value(html, result)
        
        if ability:
            result['homeAbility'] = ability['home']
            result['awayAbility'] = ability['away']
            home_val = ability['home'].get('totalValue', {}).get('raw', 'N/A')
            away_val = ability['away'].get('totalValue', {}).get('raw', 'N/A')
            print(f"  okooo身价: 主{home_val} vs 客{away_val}")
        else:
            print(f"  okooo: 未找到身价数据")
            
    except Exception as e:
        print(f"  okooo获取失败: {e}")


def parse_okooo_team_value(html, result=None):
    """解析okooo球队身价数据，并根据阵容计算锋线/中场/防线身价"""
    start = html.find('<!--球队身价-->')
    if start < 0:
        return None
    
    section = html[start:start+2000]
    
    left_match = re.search(r'N_data_l[^>]*>([^<]+)', section)
    right_match = re.search(r'N_data_r[^>]*>([^<]+)', section)
    
    if not left_match:
        return None
    
    def parse_value(text):
        if not text:
            return None
        text = text.replace('&euro;', '').strip()
        if '亿' in text:
            try:
                return {'value': float(re.search(r'([\d.]+)', text).group(1)) * 10000, 'unit': '万', 'raw': text}
            except:
                return {'raw': text}
        elif '万' in text:
            try:
                return {'value': float(re.search(r'([\d.]+)', text).group(1)), 'unit': '万', 'raw': text}
            except:
                return {'raw': text}
        return {'raw': text}
    
    home_total = parse_value(left_match.group(1) if left_match else None)
    away_total = parse_value(right_match.group(1) if right_match else None)
    
    home_ability = {'totalValue': home_total}
    away_ability = {'totalValue': away_total}
    
    if result:
        home_lineup = result.get('homeLineup')
        away_lineup = result.get('awayLineup')
        
        if home_lineup:
            home_ability.update(calculate_position_values(home_lineup, home_total))
        elif home_total and home_total.get('value'):
            default_dist = get_default_position_distribution(home_total['value'])
            home_ability.update(default_dist)
        
        if away_lineup:
            away_ability.update(calculate_position_values(away_lineup, away_total))
        elif away_total and away_total.get('value'):
            default_dist = get_default_position_distribution(away_total['value'])
            away_ability.update(default_dist)
    
    return {
        'home': home_ability,
        'away': away_ability
    }


def calculate_position_values(lineup, total_value):
    """根据阵容计算锋线/中场/防线身价"""
    if not lineup:
        return {}
    
    starting = lineup.get('starting', [])
    substitute = lineup.get('substitute', [])
    all_players = starting + substitute
    
    attack_count = 0
    midfield_count = 0
    defense_count = 0
    goalkeeper_count = 0
    
    attack_positions = ['前锋', '边锋', '影锋', '中锋', '前锋', 'Winger', 'Forward', 'Striker']
    midfield_positions = ['中场', '前腰', '后腰', '边前卫', '中前卫', 'Midfielder']
    defense_positions = ['后卫', '中后卫', '边后卫', '左后卫', '右后卫', 'Defender', 'Back']
    goalkeeper_positions = ['守门员', '门将', 'Goalkeeper']
    
    for player in all_players:
        pos = player.get('position', '').lower()
        
        if any(p in pos for p in attack_positions):
            attack_count += 1
        elif any(p in pos for p in midfield_positions):
            midfield_count += 1
        elif any(p in pos for p in defense_positions):
            defense_count += 1
        elif any(p in pos for p in goalkeeper_positions):
            goalkeeper_count += 1
    
    total_count = attack_count + midfield_count + defense_count + goalkeeper_count
    
    if total_count == 0:
        return get_default_position_distribution(total_value['value'] if total_value and total_value.get('value') else 1000)
    
    if total_value and total_value.get('value'):
        total_val = total_value['value']
        attack_val = round(total_val * attack_count / total_count * 1.2) if attack_count > 0 else 0
        midfield_val = round(total_val * midfield_count / total_count * 1.1) if midfield_count > 0 else 0
        defense_val = round(total_val * defense_count / total_count * 0.9) if defense_count > 0 else 0
    else:
        attack_val = attack_count * 100
        midfield_val = midfield_count * 100
        defense_val = defense_count * 100
    
    return {
        'attackValue': {'value': attack_val, 'unit': '万', 'count': attack_count},
        'midfieldValue': {'value': midfield_val, 'unit': '万', 'count': midfield_count},
        'defenseValue': {'value': defense_val, 'unit': '万', 'count': defense_count}
    }


def get_default_position_distribution(total_value):
    """返回默认的位置身价分布"""
    return {
        'attackValue': {'value': round(total_value * 0.35), 'unit': '万'},
        'midfieldValue': {'value': round(total_value * 0.30), 'unit': '万'},
        'defenseValue': {'value': round(total_value * 0.25), 'unit': '万'}
    }


# ============================================================
# 亚盘和欧赔
# ============================================================

def fetch_handicap_odds(fixture_id, result):
    """获取让球指数数据"""
    from bs4 import BeautifulSoup
    
    url = f'https://odds.500.com/fenxi/rangqiu-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        odds_list = []
        
        datatb = soup.find('table', id='datatb')
        if not datatb:
            result['handicapOdds'] = []
            return
        
        tbody = datatb.find('tbody')
        if not tbody:
            tbody = datatb
        
        for tr in tbody.find_all('tr', recursive=False):
            cid = tr.get('cid')
            if not cid:
                continue
            
            company_td = tr.find('td', class_='tb_plgs')
            if not company_td:
                continue
            
            company = company_td.get('title', '')
            if not company:
                company_span = company_td.find('span', class_='quancheng')
                company = company_span.get_text(strip=True) if company_span else ''
            
            if not company:
                continue
            
            handicap = tr.get('handicapline', '')
            
            pl_tables = tr.find_all('table', class_='pl_table_data')
            
            instant_home = instant_draw = instant_away = ''
            initial_home = initial_draw = initial_away = ''
            instant_home_prob = instant_draw_prob = instant_away_prob = ''
            initial_home_prob = initial_draw_prob = initial_away_prob = ''
            instant_return = initial_return = ''
            instant_home_kelly = instant_draw_kelly = instant_away_kelly = ''
            initial_home_kelly = initial_draw_kelly = initial_away_kelly = ''
            
            if len(pl_tables) >= 1:
                tds = pl_tables[0].find_all('td')
                if len(tds) >= 6:
                    instant_home = tds[0].get_text(strip=True)
                    instant_draw = tds[1].get_text(strip=True)
                    instant_away = tds[2].get_text(strip=True)
                    initial_home = tds[3].get_text(strip=True)
                    initial_draw = tds[4].get_text(strip=True)
                    initial_away = tds[5].get_text(strip=True)
                elif len(tds) >= 3:
                    instant_home = tds[0].get_text(strip=True)
                    instant_draw = tds[1].get_text(strip=True)
                    instant_away = tds[2].get_text(strip=True)
                    initial_home = instant_home
                    initial_draw = instant_draw
                    initial_away = instant_away
            
            if len(pl_tables) >= 2:
                tds = pl_tables[1].find_all('td')
                if len(tds) >= 6:
                    instant_home_prob = tds[0].get_text(strip=True).replace('%', '')
                    instant_draw_prob = tds[1].get_text(strip=True).replace('%', '')
                    instant_away_prob = tds[2].get_text(strip=True).replace('%', '')
                    initial_home_prob = tds[3].get_text(strip=True).replace('%', '')
                    initial_draw_prob = tds[4].get_text(strip=True).replace('%', '')
                    initial_away_prob = tds[5].get_text(strip=True).replace('%', '')
            
            if len(pl_tables) >= 3:
                tds = pl_tables[2].find_all('td')
                if len(tds) >= 2:
                    instant_return = tds[0].get_text(strip=True).replace('%', '')
                    initial_return = tds[1].get_text(strip=True).replace('%', '')
            
            if len(pl_tables) >= 4:
                tds = pl_tables[3].find_all('td')
                if len(tds) >= 6:
                    instant_home_kelly = tds[0].get_text(strip=True)
                    instant_draw_kelly = tds[1].get_text(strip=True)
                    instant_away_kelly = tds[2].get_text(strip=True)
                    initial_home_kelly = tds[3].get_text(strip=True)
                    initial_draw_kelly = tds[4].get_text(strip=True)
                    initial_away_kelly = tds[5].get_text(strip=True)
            
            odds_list.append({
                'company': company[:15],
                'handicap': handicap,
                'instant': {
                    'homeOdds': instant_home,
                    'drawOdds': instant_draw,
                    'awayOdds': instant_away,
                    'homeProb': instant_home_prob,
                    'drawProb': instant_draw_prob,
                    'awayProb': instant_away_prob,
                    'returnRate': instant_return,
                    'homeKelly': instant_home_kelly,
                    'drawKelly': instant_draw_kelly,
                    'awayKelly': instant_away_kelly
                },
                'initial': {
                    'homeOdds': initial_home,
                    'drawOdds': initial_draw,
                    'awayOdds': initial_away,
                    'homeProb': initial_home_prob,
                    'drawProb': initial_draw_prob,
                    'awayProb': initial_away_prob,
                    'returnRate': initial_return,
                    'homeKelly': initial_home_kelly,
                    'drawKelly': initial_draw_kelly,
                    'awayKelly': initial_away_kelly
                }
            })
        
        result['handicapOdds'] = odds_list[:30]
        print(f"  让球: {len(odds_list)} 家")
        
    except Exception as e:
        print(f"  让球失败: {e}")


def fetch_asian_odds(fixture_id, result):
    """获取亚盘数据"""
    from bs4 import BeautifulSoup
    
    url = f'https://odds.500.com/fenxi/yazhi-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        odds_list = []
        
        datatb = soup.find('table', id='datatb')
        if not datatb:
            result['asianOdds'] = []
            print(f"  亚盘: 0 家")
            return
        
        for tr in datatb.find_all('tr'):
            cid = tr.get('id')
            if not cid or not cid.isdigit():
                continue
            
            company_td = tr.find('td', class_='tb_plgs')
            if not company_td:
                continue
            
            company_a = company_td.find('a')
            company = company_a.get('title', '') if company_a else ''
            if not company:
                company_span = company_td.find('span', class_='quancheng')
                company = company_span.get_text(strip=True) if company_span else ''
            
            if not company:
                continue
            
            pl_tables = tr.find_all('table', class_='pl_table_data')
            
            instant_home = instant_away = instant_handicap = instant_trend = ''
            initial_home = initial_away = initial_handicap = ''
            
            if len(pl_tables) >= 1:
                tds = pl_tables[0].find_all('td')
                if len(tds) >= 3:
                    instant_home = re.sub(r'[↑↓]', '', tds[0].get_text(strip=True))
                    instant_handicap = tds[1].get_text(strip=True)
                    if '<font' in str(tds[1]):
                        instant_handicap = re.sub(r'升.*$', '', instant_handicap).strip()
                    instant_away = re.sub(r'[↑↓]', '', tds[2].get_text(strip=True))
                    
                    if '升' in str(tds[1]):
                        instant_trend = '升'
                    elif '↓' in tds[0].get_text():
                        instant_trend = '降'
            
            if len(pl_tables) >= 2:
                tds = pl_tables[1].find_all('td')
                if len(tds) >= 3:
                    initial_home = tds[0].get_text(strip=True)
                    initial_handicap = tds[1].get_text(strip=True)
                    initial_away = tds[2].get_text(strip=True)
            
            time_tags = tr.find_all('time')
            instant_time = time_tags[0].get_text(strip=True) if len(time_tags) > 0 else ''
            initial_time = time_tags[1].get_text(strip=True) if len(time_tags) > 1 else ''
            
            odds_list.append({
                'company': company[:15],
                'instant': {
                    'homeWater': instant_home,
                    'handicap': instant_handicap,
                    'awayWater': instant_away,
                    'time': instant_time,
                    'trend': instant_trend
                },
                'initial': {
                    'homeWater': initial_home,
                    'handicap': initial_handicap,
                    'awayWater': initial_away,
                    'time': initial_time
                }
            })
        
        result['asianOdds'] = odds_list[:30]
        print(f"  亚盘: {len(odds_list)} 家")
        
    except Exception as e:
        print(f"  亚盘失败: {e}")


def fetch_size_odds(fixture_id, result):
    """获取大小球数据"""
    from bs4 import BeautifulSoup
    
    url = f'https://odds.500.com/fenxi/daxiao-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        odds_list = []
        
        datatb = soup.find('table', id='datatb')
        if not datatb:
            result['sizeOdds'] = []
            print(f"  大小: 0 家")
            return
        
        for tr in datatb.find_all('tr'):
            cid = tr.get('id')
            if not cid or not cid.isdigit():
                continue
            
            company_td = tr.find('td', class_='tb_plgs')
            if not company_td:
                continue
            
            company_a = company_td.find('a')
            company = company_a.get('title', '') if company_a else ''
            if not company:
                company_span = company_td.find('span', class_='quancheng')
                company = company_span.get_text(strip=True) if company_span else ''
            
            if not company:
                continue
            
            pl_tables = tr.find_all('table', class_='pl_table_data')
            
            instant_big = instant_small = instant_handicap = instant_trend = ''
            initial_big = initial_small = initial_handicap = ''
            
            if len(pl_tables) >= 1:
                tds = pl_tables[0].find_all('td')
                if len(tds) >= 3:
                    instant_big = re.sub(r'[↑↓]', '', tds[0].get_text(strip=True))
                    instant_handicap = tds[1].get_text(strip=True)
                    instant_small = re.sub(r'[↑↓]', '', tds[2].get_text(strip=True))
                    
                    if '↑' in tds[0].get_text():
                        instant_trend = '升'
                    elif '↓' in tds[0].get_text():
                        instant_trend = '降'
            
            if len(pl_tables) >= 2:
                tds = pl_tables[1].find_all('td')
                if len(tds) >= 3:
                    initial_big = tds[0].get_text(strip=True)
                    initial_handicap = tds[1].get_text(strip=True)
                    initial_small = tds[2].get_text(strip=True)
            
            time_tags = tr.find_all('time')
            instant_time = time_tags[0].get_text(strip=True) if len(time_tags) > 0 else ''
            initial_time = time_tags[1].get_text(strip=True) if len(time_tags) > 1 else ''
            
            odds_list.append({
                'company': company[:15],
                'instant': {
                    'bigWater': instant_big,
                    'handicap': instant_handicap,
                    'smallWater': instant_small,
                    'time': instant_time,
                    'trend': instant_trend
                },
                'initial': {
                    'bigWater': initial_big,
                    'handicap': initial_handicap,
                    'smallWater': initial_small,
                    'time': initial_time
                }
            })
        
        result['sizeOdds'] = odds_list[:30]
        print(f"  大小: {len(odds_list)} 家")
        
    except Exception as e:
        print(f"  大小失败: {e}")


def fetch_european_odds(fixture_id, result):
    """获取欧赔数据"""
    from bs4 import BeautifulSoup
    
    url = f'https://odds.500.com/fenxi/ouzhi-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        odds_list = []
        european_avg = None
        
        datatb = soup.find('table', id='datatb')
        if not datatb:
            result['europeanOdds'] = []
            print(f"  欧赔: 0 家")
            return
        
        for tr in datatb.find_all('tr'):
            cid = tr.get('id')
            if not cid:
                continue
            
            company_td = tr.find('td', class_='tb_plgs')
            if not company_td:
                continue
            
            company_a = company_td.find('a')
            company = company_a.get('title', '') if company_a else ''
            if not company:
                company_span = company_td.find('span', class_='quancheng')
                company = company_span.get_text(strip=True) if company_span else ''
            
            if not company:
                continue
            
            pl_tables = tr.find_all('table', class_='pl_table_data')
            
            instant_home = instant_draw = instant_away = ''
            initial_home = initial_draw = initial_away = ''
            instant_return = initial_return = ''
            instant_home_prob = instant_draw_prob = instant_away_prob = ''
            initial_home_prob = initial_draw_prob = initial_away_prob = ''
            
            if len(pl_tables) >= 1:
                tds = pl_tables[0].find_all('td')
                if len(tds) >= 6:
                    instant_home = tds[0].get_text(strip=True)
                    instant_draw = tds[1].get_text(strip=True)
                    instant_away = tds[2].get_text(strip=True)
                    initial_home = tds[3].get_text(strip=True)
                    initial_draw = tds[4].get_text(strip=True)
                    initial_away = tds[5].get_text(strip=True)
            
            if len(pl_tables) >= 2:
                tds = pl_tables[1].find_all('td')
                if len(tds) >= 6:
                    instant_home_prob = tds[0].get_text(strip=True)
                    instant_draw_prob = tds[1].get_text(strip=True)
                    instant_away_prob = tds[2].get_text(strip=True)
                    initial_home_prob = tds[3].get_text(strip=True)
                    initial_draw_prob = tds[4].get_text(strip=True)
                    initial_away_prob = tds[5].get_text(strip=True)
            
            if len(pl_tables) >= 3:
                tds = pl_tables[2].find_all('td')
                if len(tds) >= 2:
                    instant_return = tds[0].get_text(strip=True)
                    initial_return = tds[1].get_text(strip=True)
            
            odds_data = {
                'company': company[:15],
                'instant': {
                    'homeWin': instant_home,
                    'draw': instant_draw,
                    'awayWin': instant_away,
                    'homeProb': instant_home_prob,
                    'drawProb': instant_draw_prob,
                    'awayProb': instant_away_prob,
                    'returnRate': instant_return
                },
                'initial': {
                    'homeWin': initial_home,
                    'draw': initial_draw,
                    'awayWin': initial_away,
                    'homeProb': initial_home_prob,
                    'drawProb': initial_draw_prob,
                    'awayProb': initial_away_prob,
                    'returnRate': initial_return
                }
            }
            
            if company == '平均值':
                european_avg = odds_data
            else:
                odds_list.append(odds_data)
        
        result['europeanOdds'] = odds_list[:30]
        result['europeanAvg'] = european_avg
        print(f"  欧赔: {len(odds_list)} 家")
        
    except Exception as e:
        print(f"  欧赔失败: {e}")


def fetch_betting_analysis(fixture_id, result):
    """获取投注分析数据"""
    result['bettingAnalysis'] = None
    
    url = f'https://odds.500.com/fenxi/touzhu-{fixture_id}.shtml'
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.encoding = 'gb2312'
        html = resp.text
        
        betting_data = {
            'probabilities': [],
            'bigDeals': [],
            'betfairVolume': [],
            'bookieProfit': [],
            'summary': ''
        }
        
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        
        for table in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)
            clean_rows = []
            for row in rows:
                cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
                clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                clean_rows.append(clean_cells)
            
            if not clean_rows:
                continue
            
            table_text = str(clean_rows[0]) + str(clean_rows[1] if len(clean_rows) > 1 else '')
            
            if '百家欧赔' in table_text and '概率' in table_text:
                for row in clean_rows:
                    if len(row) >= 8:
                        first_cell = row[0]
                        if first_cell and first_cell not in ['', '&nbsp', '数据提点'] and not first_cell.startswith('本场比赛'):
                            if '%' in row[2] or '.' in row[1]:
                                betting_data['probabilities'].append({
                                    'result': first_cell,
                                    'odds': row[1],
                                    'probability': row[2],
                                    'betfairRatio': row[4] if len(row) > 4 else '-',
                                    'betfairPrice': row[5] if len(row) > 5 else '-',
                                    'volume': row[6] if len(row) > 6 else '-',
                                    'bookieProfit': row[7] if len(row) > 7 else '-',
                                    'hotIndex': row[9] if len(row) > 9 else '-',
                                    'profitIndex': row[10] if len(row) > 10 else '-'
                                })
            
            elif '属性' in table_text and '成交量' in table_text:
                for row in clean_rows[1:]:
                    if len(row) >= 5 and row[0] in ['主', '平', '客', '综合']:
                        betting_data['bigDeals'].append({
                            'type': row[0],
                            'action': row[1],
                            'volume': row[2],
                            'time': row[3],
                            'ratio': row[4]
                        })
            
            elif '必发交易量' in table_text:
                for row in clean_rows[1:]:
                    if len(row) >= 3 and row[0] in ['主胜', '平局', '客胜']:
                        betting_data['betfairVolume'].append({
                            'result': row[0],
                            'volume': row[1],
                            'price': row[2] if len(row) > 2 else '-'
                        })
            
            elif '庄家盈亏' in table_text:
                for row in clean_rows[1:]:
                    if len(row) >= 3 and row[0] in ['主胜', '平局', '客胜']:
                        betting_data['bookieProfit'].append({
                            'result': row[0],
                            'profit': row[1],
                            'index': row[2]
                        })
        
        summary_match = re.search(r'本场比赛[^<，。]+[，。]', html)
        if summary_match:
            betting_data['summary'] = summary_match.group(0)
        
        if any([betting_data['probabilities'], betting_data['bigDeals'], 
                betting_data['betfairVolume'], betting_data['bookieProfit']]):
            result['bettingAnalysis'] = betting_data
            print(f"  投注分析: 已获取")
        
    except Exception as e:
        print(f"  投注分析失败: {e}")


# ============================================================
# 情报数据生成
# 基于已爬取的数据自动生成SWOT分析
# ============================================================

def generate_intelligence(result):
    """基于已有数据生成情报分析"""
    intel = {
        'homeStrength': [],
        'homeWeakness': [],
        'homeOpportunity': [],
        'homeThreat': [],
        'awayStrength': [],
        'awayWeakness': [],
        'awayOpportunity': [],
        'awayThreat': [],
        'summary': ''
    }
    
    home = result.get('home', '主队')
    away = result.get('away', '客队')
    
    home_stats = result.get('homeRecentStats') or {}
    away_stats = result.get('awayRecentStats') or {}
    
    home_rank = result.get('homeRanking') or {}
    away_rank = result.get('awayRanking') or {}
    
    home_avg = result.get('homeAverageStats') or {}
    away_avg = result.get('awayAverageStats') or {}
    
    home_ability = result.get('homeAbility') or {}
    away_ability = result.get('awayAbility') or {}
    
    h2h = result.get('h2h') or {}
    rec = result.get('recommendation') or {}
    
    home_win = home_stats.get('win', 0) or 0
    home_draw = home_stats.get('draw', 0) or 0
    home_lose = home_stats.get('lose', 0) or 0
    home_goals = home_stats.get('goals', 0) or 0
    home_conceded = home_stats.get('conceded', 0) or 0
    
    away_win = away_stats.get('win', 0) or 0
    away_draw = away_stats.get('draw', 0) or 0
    away_lose = away_stats.get('lose', 0) or 0
    away_goals = away_stats.get('goals', 0) or 0
    away_conceded = away_stats.get('conceded', 0) or 0
    
    home_total = home_win + home_draw + home_lose
    away_total = away_win + away_draw + away_lose
    
    home_avg_goals = None
    home_avg_conceded = None
    away_avg_goals = None
    away_avg_conceded = None
    
    home_current_rank = home_rank.get('currentRank')
    away_current_rank = away_rank.get('currentRank')
    
    home_total_val = home_ability.get('totalValue', {}).get('value', 0) or 0
    away_total_val = away_ability.get('totalValue', {}).get('value', 0) or 0
    
    home_attack_val = home_ability.get('attackValue', {}).get('value', 0) or 0
    away_attack_val = away_ability.get('attackValue', {}).get('value', 0) or 0
    
    home_defense_val = home_ability.get('defenseValue', {}).get('value', 0) or 0
    away_defense_val = away_ability.get('defenseValue', {}).get('value', 0) or 0
    
    if home_current_rank and home_current_rank <= 5:
        intel['homeStrength'].append(f'联赛排名第{home_current_rank}位，处于上游水平')
    elif home_current_rank and home_current_rank <= 10:
        intel['homeStrength'].append(f'联赛排名第{home_current_rank}位，处于中上游')
    
    if away_current_rank and away_current_rank <= 5:
        intel['awayStrength'].append(f'联赛排名第{away_current_rank}位，处于上游水平')
    elif away_current_rank and away_current_rank <= 10:
        intel['awayStrength'].append(f'联赛排名第{away_current_rank}位，处于中上游')
    
    if home_total >= 5:
        home_win_rate = home_win / home_total
        if home_win_rate >= 0.6:
            intel['homeStrength'].append(f'近{home_total}场胜率{int(home_win_rate*100)}%，状态火热')
        elif home_win_rate >= 0.4:
            intel['homeStrength'].append(f'近{home_total}场胜率{int(home_win_rate*100)}%，表现稳定')
        elif home_win_rate < 0.3:
            intel['homeWeakness'].append(f'近{home_total}场胜率仅{int(home_win_rate*100)}%，状态低迷')
    
    if away_total >= 5:
        away_win_rate = away_win / away_total
        if away_win_rate >= 0.6:
            intel['awayStrength'].append(f'近{away_total}场胜率{int(away_win_rate*100)}%，状态火热')
        elif away_win_rate >= 0.4:
            intel['awayStrength'].append(f'近{away_total}场胜率{int(away_win_rate*100)}%，表现稳定')
        elif away_win_rate < 0.3:
            intel['awayWeakness'].append(f'近{away_total}场胜率仅{int(away_win_rate*100)}%，状态低迷')
    
    if home_goals and home_total:
        home_avg_goals = home_goals / home_total
        if home_avg_goals >= 2:
            intel['homeStrength'].append(f'场均进球{home_avg_goals:.1f}个，进攻火力强劲')
        elif home_avg_goals < 1:
            intel['homeWeakness'].append(f'场均进球仅{home_avg_goals:.1f}个，进攻乏力')
    
    if away_goals and away_total:
        away_avg_goals = away_goals / away_total
        if away_avg_goals >= 2:
            intel['awayStrength'].append(f'场均进球{away_avg_goals:.1f}个，进攻火力强劲')
        elif away_avg_goals < 1:
            intel['awayWeakness'].append(f'场均进球仅{away_avg_goals:.1f}个，进攻乏力')
    
    if home_conceded and home_total:
        home_avg_conceded = home_conceded / home_total
        if home_avg_conceded < 1:
            intel['homeStrength'].append(f'场均失球{home_avg_conceded:.1f}个，防守稳固')
        elif home_avg_conceded >= 2:
            intel['homeWeakness'].append(f'场均失球{home_avg_conceded:.1f}个，防守漏洞大')
    
    if away_conceded and away_total:
        away_avg_conceded = away_conceded / away_total
        if away_avg_conceded < 1:
            intel['awayStrength'].append(f'场均失球{away_avg_conceded:.1f}个，防守稳固')
        elif away_avg_conceded >= 2:
            intel['awayWeakness'].append(f'场均失球{away_avg_conceded:.1f}个，防守漏洞大')
    
    if home_total_val and away_total_val:
        if home_total_val > away_total_val * 1.5:
            intel['homeStrength'].append(f'球队身价{home_total_val}万欧，远超对手')
            intel['awayThreat'].append(f'对手身价是对手{home_total_val/away_total_val:.1f}倍，实力差距明显')
        elif away_total_val > home_total_val * 1.5:
            intel['awayStrength'].append(f'球队身价{away_total_val}万欧，远超对手')
            intel['homeThreat'].append(f'对手身价是对手{away_total_val/home_total_val:.1f}倍，实力差距明显')
    
    if home_attack_val and away_defense_val:
        if home_attack_val > away_defense_val * 1.3:
            intel['homeOpportunity'].append(f'锋线身价({home_attack_val}万)优于对手防线({away_defense_val}万)')
        if away_defense_val > home_attack_val * 1.3:
            intel['homeThreat'].append(f'对手防线({away_defense_val}万)优于己方锋线({home_attack_val}万)')
    
    if away_attack_val and home_defense_val:
        if away_attack_val > home_defense_val * 1.3:
            intel['awayOpportunity'].append(f'锋线身价({away_attack_val}万)优于对手防线({home_defense_val}万)')
        if home_defense_val > away_attack_val * 1.3:
            intel['awayThreat'].append(f'对手防线({home_defense_val}万)优于己方锋线({away_attack_val}万)')
    
    h2h_total = h2h.get('total', 0) or 0
    h2h_home_win = h2h.get('homeWin', 0) or 0
    h2h_away_win = h2h.get('awayWin', 0) or 0
    
    if h2h_total > 0:
        if h2h_home_win > h2h_away_win:
            intel['homeOpportunity'].append(f'历史交锋{h2h_home_win}胜{h2h_total-h2h_home_win-h2h_away_win}平{h2h_away_win}负，占据心理优势')
            intel['awayThreat'].append(f'历史交锋处于下风，心理压力较大')
        elif h2h_away_win > h2h_home_win:
            intel['awayOpportunity'].append(f'历史交锋{h2h_away_win}胜{h2h_total-h2h_home_win-h2h_away_win}平{h2h_home_win}负，占据心理优势')
            intel['homeThreat'].append(f'历史交锋处于下风，心理压力较大')
    
    home_form = rec.get('homeForm', '')
    away_form = rec.get('awayForm', '')
    
    def check_consecutive(form, char):
        max_count = 0
        current_count = 0
        for c in form:
            if c == char:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        return max_count
    
    if home_form:
        form_display = home_form.replace("W","胜").replace("D","平").replace("L","负")
        win_streak = max(check_consecutive(home_form, 'W'), check_consecutive(home_form, '胜'))
        lose_streak = max(check_consecutive(home_form, 'L'), check_consecutive(home_form, '负'))
        if win_streak >= 3:
            intel['homeStrength'].append(f'近期走势: {form_display}，{win_streak}连胜')
        elif lose_streak >= 3:
            intel['homeWeakness'].append(f'近期走势: {form_display}，{lose_streak}连败')
    
    if away_form:
        form_display = away_form.replace("W","胜").replace("D","平").replace("L","负")
        win_streak = max(check_consecutive(away_form, 'W'), check_consecutive(away_form, '胜'))
        lose_streak = max(check_consecutive(away_form, 'L'), check_consecutive(away_form, '负'))
        if win_streak >= 3:
            intel['awayStrength'].append(f'近期走势: {form_display}，{win_streak}连胜')
        elif lose_streak >= 3:
            intel['awayWeakness'].append(f'近期走势: {form_display}，{lose_streak}连败')
    
    if away_avg_conceded and away_avg_conceded >= 1.5:
        intel['homeOpportunity'].append(f'对手场均失球{away_avg_conceded:.1f}个，防线存在漏洞')
    
    if home_avg_conceded and home_avg_conceded >= 1.5:
        intel['awayOpportunity'].append(f'对手场均失球{home_avg_conceded:.1f}个，防线存在漏洞')
    
    if away_avg_goals and away_avg_goals >= 2:
        intel['homeThreat'].append(f'对手场均进球{away_avg_goals:.1f}个，进攻威胁大')
    
    if home_avg_goals and home_avg_goals >= 2:
        intel['awayThreat'].append(f'对手场均进球{home_avg_goals:.1f}个，进攻威胁大')
    
    home_lineup = result.get('homeLineup') or {}
    away_lineup = result.get('awayLineup') or {}
    
    home_injured = len(home_lineup.get('injured', []))
    home_suspended = len(home_lineup.get('suspended', []))
    away_injured = len(away_lineup.get('injured', []))
    away_suspended = len(away_lineup.get('suspended', []))
    
    if home_injured > 0:
        intel['homeWeakness'].append(f'{home_injured}名球员伤病，阵容不整')
    if home_suspended > 0:
        intel['homeWeakness'].append(f'{home_suspended}名球员停赛，战力受损')
    if away_injured > 0:
        intel['awayWeakness'].append(f'{away_injured}名球员伤病，阵容不整')
    if away_suspended > 0:
        intel['awayWeakness'].append(f'{away_suspended}名球员停赛，战力受损')
    
    if home_injured > 0 or home_suspended > 0:
        intel['awayOpportunity'].append('对手存在伤病/停赛，阵容不整')
    if away_injured > 0 or away_suspended > 0:
        intel['homeOpportunity'].append('对手存在伤病/停赛，阵容不整')
    
    summary_parts = []
    if home_current_rank and away_current_rank:
        if home_current_rank < away_current_rank:
            summary_parts.append(f'{home}联赛排名({home_current_rank})优于{away}({away_current_rank})')
        else:
            summary_parts.append(f'{away}联赛排名({away_current_rank})优于{home}({home_current_rank})')
    
    if home_total >= 5 and away_total >= 5:
        home_wr = home_win / home_total if home_total > 0 else 0
        away_wr = away_win / away_total if away_total > 0 else 0
        if home_wr > away_wr + 0.1:
            summary_parts.append(f'{home}近期状态更佳')
        elif away_wr > home_wr + 0.1:
            summary_parts.append(f'{away}近期状态更佳')
    
    if rec.get('pick'):
        summary_parts.append(f'推荐: {rec["pick"]}')
    
    intel['summary'] = '。'.join(summary_parts) if summary_parts else ''
    
    print(f"  情报生成: 主队优势{len(intel['homeStrength'])}条, 劣势{len(intel['homeWeakness'])}条")
    
    return intel


# ============================================================
# 主函数
# ============================================================

def fetch_match_analysis(fixture_id, home_name='', away_name=''):
    """获取完整比赛分析数据"""
    result = {
        'fixtureId': fixture_id,
        'home': home_name,
        'away': away_name,
        'league': '',
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        
        # 排名信息
        'homeRanking': {},
        'awayRanking': {},
        
        # 积分榜
        'standings': [],
        'homeLeagueRanking': None,
        'awayLeagueRanking': None,
        
        # 交战历史
        'h2h': None,
        'h2hMatches': [],
        
        # 近期战绩
        'homeRecentStats': None,
        'awayRecentStats': None,
        
        # 未来赛事
        'homeFutureMatches': [],
        'awayFutureMatches': [],
        
        # 平均数据
        'homeAverageStats': None,
        'awayAverageStats': None,
        
        # 阵容
        'homeLineup': None,
        'awayLineup': None,
        
        # 能力数据
        'homeAbility': None,
        'awayAbility': None,
        
        # 推荐
        'recommendation': None,
        
        # 情报
        'intelligence': None,
        
        # 赔率
        'asianOdds': [],
        'europeanOdds': [],
        'handicapOdds': [],
        'europeanAvg': None,
        
        # 投注分析
        'bettingAnalysis': None
    }
    
    fetch_data_analysis(fixture_id, result)
    fetch_asian_odds(fixture_id, result)
    fetch_size_odds(fixture_id, result)
    fetch_european_odds(fixture_id, result)
    fetch_handicap_odds(fixture_id, result)
    fetch_betting_analysis(fixture_id, result)
    fetch_okooo_formation(fixture_id, result)
    
    result['intelligence'] = generate_intelligence(result)
    
    # 添加排名字段
    home_ranking = result.get('homeRanking', {})
    away_ranking = result.get('awayRanking', {})
    result['homeRank'] = home_ranking.get('currentRank', '')
    result['awayRank'] = away_ranking.get('currentRank', '')
    
    return result


def save_fixture_mapping(mapping):
    """保存映射到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(mapping),
        'mapping': mapping
    }
    
    paths = [
        os.path.join(base_dir, 'dist', 'fixture_mapping.json'),
        os.path.join(base_dir, 'dist', 'data', 'fixture_mapping.json'),
        os.path.join(base_dir, 'data', 'fixture_mapping.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"映射已保存到 {len(paths)} 个位置")


def save_analysis_data(fixture_id, data):
    """保存分析数据到多个位置"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', f'analysis_{fixture_id}.json'),
        os.path.join(base_dir, 'dist', 'data', f'analysis_{fixture_id}.json'),
        os.path.join(base_dir, 'data', f'analysis_{fixture_id}.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return paths[0]


def save_football_rankings():
    """从已爬取的分析数据中提取排名，保存为首页使用的格式"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # 从竞彩API获取当前比赛列表
    try:
        url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1'
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        api_data = resp.json()
    except Exception as e:
        print(f"获取竞彩API数据失败: {e}")
        return
    
    if not api_data.get('success'):
        print("竞彩API返回失败")
        return
    
    # 构建比赛映射
    match_mapping = {}
    for day_match in api_data['value']['matchInfoList']:
        for match in day_match['subMatchList']:
            match_num = match.get('matchNumStr', '')
            home = match.get('homeTeamAbbName', '')
            away = match.get('awayTeamAbbName', '')
            match_id = match.get('matchId', '')
            
            if match_num and home and away:
                key = f"{home}_{away}"
                match_mapping[key] = {
                    'matchNum': match_num,
                    'matchId': match_id,
                    'home': home,
                    'away': away,
                    'league': match.get('leagueAbbName', '')
                }
    
    # 从fixture_mapping获取比赛映射
    mapping_file = os.path.join(DATA_DIR, 'fixture_mapping.json')
    if not os.path.exists(mapping_file):
        mapping_file = os.path.join(DIST_DIR, 'fixture_mapping.json')
    
    if not os.path.exists(mapping_file):
        print("未找到fixture_mapping.json")
        return
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping_data = json.load(f)
    
    rankings = {}
    
    for key, info in mapping_data.get('mapping', {}).items():
        fixture_id = info.get('fixtureId')
        if not fixture_id:
            continue
        
        # 读取分析数据
        analysis_file = os.path.join(DATA_DIR, f'analysis_{fixture_id}.json')
        if not os.path.exists(analysis_file):
            analysis_file = os.path.join(DIST_DIR, f'analysis_{fixture_id}.json')
        
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
            
            home_rank = analysis.get('homeRank', '')
            away_rank = analysis.get('awayRank', '')
            
            if home_rank or away_rank:
                # 通过球队名称匹配比赛编号
                home = info.get('home', '')
                away = info.get('away', '')
                match_key = f"{home}_{away}"
                
                if match_key in match_mapping:
                    match_num = match_mapping[match_key]['matchNum']
                    rankings[match_num] = {
                        'homeTeam': home,
                        'awayTeam': away,
                        'homeRank': str(home_rank) if home_rank else '',
                        'awayRank': str(away_rank) if away_rank else '',
                        'league': info.get('league', '')
                    }
    
    # 保存排名数据
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'count': len(rankings),
        'rankings': rankings
    }
    
    # 保存数据到多个位置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, 'dist', 'football_rankings.json'),
        os.path.join(base_dir, 'dist', 'data', 'football_rankings.json'),
        os.path.join(base_dir, 'data', 'football_rankings.json')
    ]
    
    for filepath in paths:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"排名数据已保存到 {len(paths)} 个位置")
    print(f"共 {len(rankings)} 场比赛有排名数据")


def fetch_all_analysis(limit=None):
    """批量获取"""
    mapping = fetch_fixture_mapping()
    if not mapping:
        return
    
    print(f"\n开始爬取...")
    count = 0
    
    for key, info in mapping.items():
        if limit is not None and count >= limit:
            break
        
        print(f"\n[{count+1}] {info['home']} vs {info['away']}")
        data = fetch_match_analysis(info['fixtureId'], info['home'], info['away'])
        filepath = save_analysis_data(info['fixtureId'], data)
        print(f"已保存: {filepath}")
        count += 1
    
    # 保存排名数据
    save_football_rankings()
    
    print(f"\n完成! 共 {count} 场")


if __name__ == '__main__':
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    fetch_all_analysis(limit)