#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比赛数据匹配引擎
================

功能：
    1. 从多个数据源爬取比赛数据
    2. 自动建立比赛之间的映射关系
    3. 标准化球队名称
    4. 保存映射关系供其他模块使用

数据源：
    - sporttery: 竞彩网（比赛基础信息、赔率）
    - 500com: 500彩票网（fixtureId、分析数据、动画直播）
    - okooo: 澳客网（比分、身价）
    - namitiyu: 动画直播ID

匹配策略：
    1. 精确匹配：球队名称完全相同
    2. 标准化匹配：标准化后名称相同
    3. 模糊匹配：相似度评分 > 0.8
    4. 时间+联赛匹配：同时间同联赛的比赛

使用方法：
    python match_engine.py
"""

import json
import os
import re
import time
import ssl
import urllib.request
from datetime import datetime, timedelta
from difflib import SequenceMatcher

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, 'dist')
DATA_DIR = os.path.join(BASE_DIR, 'dist', 'data')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


class TeamNameNormalizer:
    """球队名称标准化器"""
    
    ALIASES = {
        '曼联': ['曼彻斯特联', 'Manchester United', 'Man Utd', 'Man United'],
        '曼城': ['曼彻斯特城', 'Manchester City', 'Man City'],
        '利物浦': ['Liverpool', '利華浦'],
        '切尔西': ['车路士', 'Chelsea', '切爾西'],
        '阿森纳': ['阿仙奴', 'Arsenal', '阿仙奴'],
        '热刺': ['托特纳姆', 'Tottenham', '熱刺'],
        '纽卡斯尔': ['纽卡素', 'Newcastle', '紐卡素'],
        '埃弗顿': ['爱华顿', 'Everton', '愛華頓'],
        '西汉姆': ['韦斯咸', 'West Ham', '韋斯咸'],
        '莱斯特城': ['李斯特城', 'Leicester', '李斯特城'],
        '阿斯顿维拉': ['维拉', 'Aston Villa', '阿士东维拉', '阿士東維拉'],
        '布莱顿': ['白礼顿', 'Brighton', '白禮頓'],
        '狼队': ['伍尔弗汉普顿', 'Wolves', '狼隊'],
        '富勒姆': ['富咸', 'Fulham', '富咸'],
        '布伦特福德': ['宾福特', 'Brentford', '賓福特'],
        '伯恩茅斯': ['般尼茅夫', 'Bournemouth'],
        '诺丁汉森林': ['诺定咸森林', 'Nottingham Forest', '諾定咸森林'],
        '南安普顿': ['修咸顿', 'Southampton', '修咸頓'],
        '水晶宫': ['Crystal Palace', '水晶宮'],
        
        '皇马': ['皇家马德里', 'Real Madrid', '皇家馬德里'],
        '巴萨': ['巴塞罗那', 'Barcelona', '巴塞隆拿'],
        '马竞': ['马德里竞技', 'Atletico Madrid', '馬德里體育會'],
        '塞维利亚': ['西维尔', 'Sevilla', '西維爾'],
        '瓦伦西亚': ['华伦西亚', 'Valencia', '華倫西亞'],
        '比利亚雷亚尔': ['维拉利尔', 'Villarreal', '維拉利爾'],
        '皇家社会': ['皇家苏斯达', 'Real Sociedad', '皇家蘇斯達'],
        '毕尔巴鄂': ['毕尔包', 'Athletic Bilbao', '畢爾包'],
        '贝蒂斯': ['贝迪斯', 'Real Betis', '貝迪斯'],
        '赫罗纳': ['杰罗纳', 'Girona', '傑羅納'],
        
        '拜仁': ['拜仁慕尼黑', 'Bayern Munich', '拜仁慕尼黑'],
        '多特': ['多特蒙德', 'Dortmund', '多蒙特'],
        '勒沃库森': ['利华古逊', 'Leverkusen', '利華古遜'],
        '莱比锡': ['RB莱比锡', 'RB Leipzig', 'RB萊比錫'],
        '斯图加特': ['Stuttgart', '史特加'],
        '法兰克福': ['Frankfurt', '法蘭克福'],
        '沃尔夫斯堡': ['Wolfsburg', '禾夫斯堡'],
        '门兴': ['门兴格拉德巴赫', 'Monchengladbach', '慕遜加柏'],
        '弗赖堡': ['Freiburg', '费雷堡', '費雷堡'],
        '霍芬海姆': ['Hoffenheim', '贺芬咸', '賀芬咸'],
        '美因茨': ['Mainz', '缅恩斯', '緬恩斯'],
        '不来梅': ['云达不来梅', 'Werder Bremen', '雲達不萊梅'],
        '柏林联合': ['Berlin Union', '柏林聯'],
        
        '尤文图斯': ['祖云达斯', 'Juventus', '祖雲達斯'],
        '国米': ['国际米兰', 'Inter Milan', '國際米蘭'],
        'AC米兰': ['AC Milan', 'AC米蘭'],
        '那不勒斯': ['拿玻里', 'Napoli', '拿玻里'],
        '罗马': ['Roma', '羅馬'],
        '拉齐奥': ['Lazio', '拉素'],
        '亚特兰大': ['Atalanta', '亞特蘭大'],
        '佛罗伦萨': ['Fiorentina', '佛罗伦萨'],
        '博洛尼亚': ['Bologna', '博洛尼亞'],
        '都灵': ['Torino', '拖连奴', '拖連奴'],
        '乌迪内斯': ['Udinese', '乌甸尼斯', '烏甸尼斯'],
        
        '巴黎': ['巴黎圣日耳曼', 'PSG', 'Paris Saint-Germain', '巴黎聖日耳曼'],
        '马赛': ['Marseille', '馬賽'],
        '里昂': ['Lyon', '里昂'],
        '摩纳哥': ['Monaco', '摩納哥'],
        '里尔': ['Lille', '里爾'],
        '尼斯': ['Nice', '尼斯'],
        '朗斯': ['Lens', '朗斯'],
        '雷恩': ['Rennes', '雷恩'],
        
        '本菲卡': ['宾菲加', 'Benfica', '賓菲加'],
        '波尔图': ['Porto', '波圖', '波圖'],
        '葡萄牙体育': ['士砵亭', 'Sporting Lisbon', '士砵亭'],
        '布拉加': ['Braga', '布拉加'],
        
        '阿贾克斯': ['阿积士', 'Ajax', '阿積士'],
        '埃因霍温': ['燕豪芬', 'PSV', 'PSV埃因霍温', 'PSV燕豪芬'],
        '费耶诺德': ['飞燕诺', 'Feyenoord', '飛燕諾'],
        '阿尔克马尔': ['AZ阿尔克马尔', 'AZ Alkmaar', '艾克马亚', '艾克馬亞'],
        '乌得勒支': ['Utrecht', '乌德勒支', '烏德勒支'],
        '格罗宁根': ['Groningen', '高宁根', '高寧根'],
        '海伦芬': ['Heerenveen', '海伦维恩', '海倫維恩'],
        '维特斯': ['Vitesse', '维迪斯', '維迪斯'],
        '兹沃勒': ['Zwolle', '施禾利', '施禾利'],
        '奈梅亨': ['NEC Nijmegen', '奈梅亨'],
        '福图纳': ['Fortuna Sittard', '福图纳', '福圖納'],
        '威廉二世': ['Willem II', '威廉二世'],
        '埃门': ['Emmen', '安曼', '埃門'],
        '坎布尔': ['Cambuur', '甘堡尔', '甘堡爾'],
        
        '中国': ['China', '中國'],
        '日本': ['Japan', '日本'],
        '韩国': ['South Korea', '韩国', '韓國'],
        '澳大利亚': ['Australia', '澳洲', '澳大利亞'],
        '新西兰': ['New Zealand', '新西蘭'],
        '芬兰': ['Finland', '芬蘭'],
        '奥地利': ['Austria', '奧地利'],
        '荷兰': ['Netherlands', '荷蘭'],
        '英格兰': ['England', '英格蘭'],
        '苏格兰': ['Scotland', '蘇格蘭'],
        '威尔士': ['Wales', '威爾斯'],
        '北爱尔兰': ['Northern Ireland', '北愛爾蘭'],
        '爱尔兰': ['Ireland', '愛爾蘭'],
        '德国': ['Germany', '德國'],
        '法国': ['France', '法國'],
        '西班牙': ['Spain', '西班牙'],
        '意大利': ['Italy', '意大利'],
        '葡萄牙': ['Portugal', '葡萄牙'],
        '巴西': ['Brazil', '巴西'],
        '阿根廷': ['Argentina', '阿根廷'],
        '乌拉圭': ['Uruguay', '烏拉圭'],
        '巴拉圭': ['Paraguay', '巴拉圭'],
        '哥伦比亚': ['Colombia', '哥倫比亞'],
        '智利': ['Chile', '智利'],
        '秘鲁': ['Peru', '秘魯'],
        '厄瓜多尔': ['Ecuador', '厄瓜多爾'],
        '墨西哥': ['Mexico', '墨西哥'],
        '美国': ['USA', 'United States', '美國'],
        '加拿大': ['Canada', '加拿大'],
        '加纳': ['Ghana', '加納'],
        '喀麦隆': ['Cameroon', '喀麥隆'],
        '尼日利亚': ['Nigeria', '尼日利亞'],
        '南非': ['South Africa', '南非'],
        '挪威': ['Norway', '挪威'],
        '瑞典': ['Sweden', '瑞典'],
        '丹麦': ['Denmark', '丹麥'],
        '冰岛': ['Iceland', '冰島'],
        '波兰': ['Poland', '波蘭'],
        '捷克': ['Czech Republic', '捷克'],
        '斯洛伐克': ['Slovakia', '斯洛伐克'],
        '匈牙利': ['Hungary', '匈牙利'],
        '希腊': ['Greece', '希臘'],
        '塞尔维亚': ['Serbia', '塞爾維亞'],
        '克罗地亚': ['Croatia', '克羅地亞'],
        '斯洛文尼亚': ['Slovenia', '斯洛文尼亞'],
        '波黑': ['Bosnia', '波斯尼亚', '波黑'],
        '科索沃': ['Kosovo', '科索沃'],
        '北马其顿': ['North Macedonia', '北馬其頓'],
        '阿尔巴尼亚': ['Albania', '阿爾巴尼亞'],
        '土耳其': ['Turkey', '土耳其'],
        '俄罗斯': ['Russia', '俄羅斯'],
        '乌克兰': ['Ukraine', '烏克蘭'],
        '比利时': ['Belgium', '比利時'],
        '瑞士': ['Switzerland', '瑞士'],
        '摩洛哥': ['Morocco', '摩洛哥'],
        '埃及': ['Egypt', '埃及'],
        '突尼斯': ['Tunisia', '突尼西亞'],
        '沙特': ['Saudi Arabia', '沙特阿拉伯', '沙特'],
        '阿联酋': ['UAE', '阿聯酋'],
        '卡塔尔': ['Qatar', '卡塔爾'],
        '以色列': ['Israel', '以色列'],
        
        '神户胜利': ['神户胜利船', 'Vissel Kobe', '神戶勝利船'],
        '广岛三箭': ['Sanfrecce Hiroshima', '廣島三箭'],
        '川崎前锋': ['Kawasaki Frontale', '川崎前鋒'],
        '町田泽维': ['町田泽维亚', 'Machida Zelvia', '町田澤維'],
        '浦项制铁': ['Pohang Steelers', '浦項制鐵'],
        '江原FC': ['Gangwon FC', '江原FC'],
    }
    
    LEAGUE_ALIASES = {
        '英超': ['Premier League', 'EPL', '英格蘭超級聯賽', '英格蘭超'],
        '西甲': ['La Liga', '西班牙甲組聯賽', '西班牙甲'],
        '德甲': ['Bundesliga', '德國甲組聯賽', '德國甲'],
        '意甲': ['Serie A', '意大利甲組聯賽', '意大利甲'],
        '法甲': ['Ligue 1', '法國甲組聯賽', '法國甲'],
        '荷甲': ['Eredivisie', '荷蘭甲組聯賽', '荷蘭甲'],
        '荷乙': ['Eerste Divisie', '荷蘭乙組聯賽', '荷蘭乙'],
        '葡超': ['Primeira Liga', '葡萄牙超級聯賽', '葡萄牙超'],
        '日职': ['J1 League', 'J-League', '日本職業聯賽', 'J1'],
        '韩职': ['K League 1', 'K-League', '韓國職業聯賽', 'K1'],
        '中超': ['Chinese Super League', 'CSL', '中國超級聯賽'],
        '英甲': ['League One', '英格蘭甲組聯賽'],
        '英冠': ['Championship', '英格蘭冠軍聯賽'],
        '世界杯': ['World Cup', '世界盃'],
        '欧洲杯': ['Euro', 'European Championship', '歐洲盃', '歐國盃'],
        '欧冠': ['Champions League', 'UCL', '歐洲冠軍聯賽', '歐聯'],
        '欧联': ['Europa League', 'UEL', '歐洲聯賽'],
        '世预赛': ['World Cup Qualifier', 'World Cup Qualifying', '世界盃外圍賽', 'FIFA预赛'],
        '国际赛': ['International Friendly', 'Friendly', '友誼賽', '国际友谊'],
    }
    
    def __init__(self):
        self.name_to_standard = {}
        self._build_index()
    
    def _build_index(self):
        for standard, aliases in self.ALIASES.items():
            self.name_to_standard[standard] = standard
            for alias in aliases:
                self.name_to_standard[alias.lower()] = standard
                self.name_to_standard[alias] = standard
    
    def normalize(self, name):
        if not name:
            return ''
        name = name.strip()
        if name in self.name_to_standard:
            return self.name_to_standard[name]
        name_lower = name.lower()
        if name_lower in self.name_to_standard:
            return self.name_to_standard[name_lower]
        name = re.sub(r'\s+', '', name)
        name = re.sub(r'\(.*?\)', '', name)
        name = re.sub(r'\[.*?\]', '', name)
        return name.strip()
    
    def normalize_league(self, league):
        if not league:
            return ''
        league = league.strip()
        if league in self.LEAGUE_ALIASES:
            return league
        for standard, aliases in self.LEAGUE_ALIASES.items():
            if league in aliases or league.lower() in [a.lower() for a in aliases]:
                return standard
        league = re.sub(r'\d{2}/\d{2}', '', league)
        league = re.sub(r'第\d+轮', '', league)
        league = re.sub(r'20\d{2}年?', '', league)
        return league.strip()
    
    def similarity(self, name1, name2):
        if not name1 or not name2:
            return 0.0
        n1 = self.normalize(name1)
        n2 = self.normalize(name2)
        if n1 == n2:
            return 1.0
        if n1 in n2 or n2 in n1:
            return 0.9
        return SequenceMatcher(None, n1, n2).ratio()


class MatchEngine:
    """比赛匹配引擎"""
    
    def __init__(self):
        self.normalizer = TeamNameNormalizer()
        self.matches = {}
        self.mappings = {}
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
    
    def fetch_sporttery_matches(self):
        """从竞彩网获取比赛"""
        print(">>> 获取竞彩网数据...")
        url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=1'
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=self.ctx, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                
                if not data.get('success'):
                    return []
                
                matches = []
                for day in data.get('value', {}).get('matchInfoList', []):
                    for m in day.get('subMatchList', []):
                        home = m.get('homeTeamAbbName', '')
                        away = m.get('awayTeamAbbName', '')
                        
                        match_key = self._create_match_key(home, away, m.get('matchTime', ''))
                        
                        matches.append({
                            'source': 'sporttery',
                            'matchId': str(m.get('matchId', '')),
                            'matchNum': m.get('matchNumStr', ''),
                            'home': home,
                            'away': away,
                            'homeNorm': self.normalizer.normalize(home),
                            'awayNorm': self.normalizer.normalize(away),
                            'league': m.get('leagueAbbName', ''),
                            'time': m.get('matchTime', '')[:5],
                            'date': m.get('matchDate', ''),
                            'matchKey': match_key,
                        })
                
                print(f"    获取 {len(matches)} 场比赛")
                return matches
        except Exception as e:
            print(f"    竞彩网获取失败: {e}")
            return []
    
    def fetch_500_matches(self):
        """从500.com获取比赛"""
        print(">>> 获取500.com数据...")
        url = 'https://trade.500.com/jczq/index.php?playid=312&g=2'
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=self.ctx, timeout=30) as resp:
                html = resp.read().decode('gb2312', errors='ignore')
                
                matches = []
                pattern = r'data-fixtureid="(\d+)"[^>]*data-homesxname="([^"]*)"[^>]*data-awaysxname="([^"]*)"'
                
                for m in re.finditer(pattern, html):
                    fid, home, away = m.groups()
                    home = home.strip()
                    away = away.strip()
                    
                    context = html[max(0, m.start()-500):m.end()+500]
                    league = re.search(r'data-simpleleague="([^"]*)"', context)
                    date = re.search(r'data-matchdate="([^"]*)"', context)
                    time = re.search(r'data-matchtime="([^"]*)"', context)
                    
                    match_key = self._create_match_key(home, away, time.group(1) if time else '')
                    
                    matches.append({
                        'source': '500com',
                        'fixtureId': fid,
                        'home': home,
                        'away': away,
                        'homeNorm': self.normalizer.normalize(home),
                        'awayNorm': self.normalizer.normalize(away),
                        'league': league.group(1) if league else '',
                        'date': date.group(1) if date else '',
                        'time': time.group(1)[:5] if time else '',
                        'matchKey': match_key,
                    })
                
                print(f"    获取 {len(matches)} 场比赛")
                return matches
        except Exception as e:
            print(f"    500.com获取失败: {e}")
            return []
    
    def fetch_live_500_matches(self):
        """从500.com直播页获取比赛（包含比分）"""
        print(">>> 获取500.com直播数据...")
        url = 'https://live.500.com/'
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=self.ctx, timeout=30) as resp:
                html = resp.read().decode('gb2312', errors='ignore')
                
                matches = []
                pattern = r'<tr[^>]*fid=["\']?(\d+)["\']?[^>]*>(.*?)</tr>'
                
                for fid, row in re.findall(pattern, html, re.DOTALL | re.IGNORECASE):
                    team_pattern = r'<a[^>]*href="//liansai\.500\.com/team/\d+/"[^>]*>([^<]+)</a>'
                    teams = re.findall(team_pattern, row)
                    
                    if len(teams) >= 2:
                        home = teams[0].strip()
                        away = teams[1].strip()
                        
                        # 比分解析
                        home_score = 0
                        away_score = 0
                        
                        # 方式1: <td class="red"> 2 </td>
                        score_tds = re.findall(r'<td[^>]*class="red"[^>]*>\s*(\d+)\s*</td>', row)
                        if len(score_tds) >= 2:
                            home_score = int(score_tds[0])
                            away_score = int(score_tds[1])
                        
                        # 方式2: <b class="score">2</b>
                        if home_score == 0 and away_score == 0:
                            score_pattern = r'<b[^>]*class="[^"]*score[^"]*"[^>]*>(\d+)</b>'
                            scores = re.findall(score_pattern, row)
                            if len(scores) >= 2:
                                home_score = int(scores[0])
                                away_score = int(scores[1])
                        
                        status = 'upcoming'
                        if '完场' in row or '完' in row:
                            status = 'finished'
                        elif '进行中' in row or 'class="live"' in row:
                            status = 'live'
                        
                        match_key = self._create_match_key(home, away, '')
                        
                        matches.append({
                            'source': '500live',
                            'fixtureId': fid,
                            'home': home,
                            'away': away,
                            'homeNorm': self.normalizer.normalize(home),
                            'awayNorm': self.normalizer.normalize(away),
                            'homeScore': home_score,
                            'awayScore': away_score,
                            'status': status,
                            'matchKey': match_key,
                        })
                
                print(f"    获取 {len(matches)} 场比赛")
                return matches
        except Exception as e:
            print(f"    500.com直播获取失败: {e}")
            return []
    
    def fetch_namitiyu_ids(self, fixture_ids):
        """从500.com分析页获取namitiyu动画ID"""
        print(">>> 获取namitiyu动画ID...")
        namitiyu_map = {}
        
        for fid in fixture_ids:
            if not fid:
                continue
            url = f'https://odds.500.com/fenxi/stat-{fid}.shtml'
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=self.ctx, timeout=10) as resp:
                    html = resp.read().decode('gb2312', errors='ignore')
                    match = re.search(r'namitiyu\.com[^"\']+id=(\d+)', html)
                    if match:
                        namitiyu_map[fid] = match.group(1)
            except:
                pass
        
        print(f"    获取 {len(namitiyu_map)} 个动画ID")
        return namitiyu_map
    
    def _create_match_key(self, home, away, time_str):
        """创建比赛唯一标识"""
        home_norm = self.normalizer.normalize(home)
        away_norm = self.normalizer.normalize(away)
        time_part = time_str[:5] if time_str else ''
        return f"{home_norm}_{away_norm}_{time_part}"
    
    def match_matches(self, sporttery_matches, matches_500, live_matches):
        """匹配比赛"""
        print(">>> 建立匹配关系...")
        
        unified_matches = {}
        
        for m in sporttery_matches:
            key = m['matchKey']
            if key not in unified_matches:
                unified_matches[key] = {
                    'matchId': m['matchId'],
                    'matchNum': m['matchNum'],
                    'home': m['home'],
                    'away': m['away'],
                    'homeNorm': m['homeNorm'],
                    'awayNorm': m['awayNorm'],
                    'league': m['league'],
                    'date': m['date'],
                    'time': m['time'],
                    'fixtureId': '',
                    'namitiyuId': '',
                    'homeScore': 0,
                    'awayScore': 0,
                    'status': 'upcoming',
                    'sources': ['sporttery'],
                }
        
        for m in matches_500:
            key = m['matchKey']
            if key in unified_matches:
                unified_matches[key]['fixtureId'] = m['fixtureId']
                unified_matches[key]['sources'].append('500com')
            else:
                best_match = self._find_best_match(m, unified_matches)
                if best_match:
                    unified_matches[best_match]['fixtureId'] = m['fixtureId']
                    unified_matches[best_match]['sources'].append('500com')
                else:
                    unified_matches[key] = {
                        'matchId': '',
                        'matchNum': '',
                        'home': m['home'],
                        'away': m['away'],
                        'homeNorm': m['homeNorm'],
                        'awayNorm': m['awayNorm'],
                        'league': m['league'],
                        'date': m['date'],
                        'time': m['time'],
                        'fixtureId': m['fixtureId'],
                        'namitiyuId': '',
                        'homeScore': 0,
                        'awayScore': 0,
                        'status': 'upcoming',
                        'sources': ['500com'],
                    }
        
        for m in live_matches:
            key = m['matchKey']
            if key in unified_matches:
                um = unified_matches[key]
                if not um['fixtureId']:
                    um['fixtureId'] = m['fixtureId']
                um['homeScore'] = m['homeScore']
                um['awayScore'] = m['awayScore']
                um['status'] = m['status']
                um['sources'].append('500live')
            else:
                best_match = self._find_best_match(m, unified_matches)
                if best_match:
                    um = unified_matches[best_match]
                    if not um['fixtureId']:
                        um['fixtureId'] = m['fixtureId']
                    um['homeScore'] = m['homeScore']
                    um['awayScore'] = m['awayScore']
                    um['status'] = m['status']
                    um['sources'].append('500live')
        
        print(f"    统一后共 {len(unified_matches)} 场比赛")
        return unified_matches
    
    def _find_best_match(self, match, unified_matches):
        """查找最佳匹配"""
        best_key = None
        best_score = 0.0
        
        for key, um in unified_matches.items():
            home_sim = self.normalizer.similarity(match['homeNorm'], um['homeNorm'])
            away_sim = self.normalizer.similarity(match['awayNorm'], um['awayNorm'])
            avg_sim = (home_sim + away_sim) / 2
            
            if avg_sim > best_score and avg_sim >= 0.8:
                best_score = avg_sim
                best_key = key
        
        return best_key
    
    def build_mappings(self, unified_matches):
        """构建映射关系"""
        print(">>> 构建映射关系...")
        
        mapping_by_matchId = {}
        mapping_by_fixtureId = {}
        mapping_by_name = {}
        
        for key, m in unified_matches.items():
            if m['matchId']:
                mapping_by_matchId[m['matchId']] = {
                    'fixtureId': m['fixtureId'],
                    'namitiyuId': m['namitiyuId'],
                    'matchNum': m['matchNum'],
                    'home': m['home'],
                    'away': m['away'],
                    'league': m['league'],
                }
            
            if m['fixtureId']:
                mapping_by_fixtureId[m['fixtureId']] = {
                    'matchId': m['matchId'],
                    'namitiyuId': m['namitiyuId'],
                    'matchNum': m['matchNum'],
                    'home': m['home'],
                    'away': m['away'],
                    'league': m['league'],
                }
            
            name_key = f"{m['home']}_{m['away']}"
            mapping_by_name[name_key] = {
                'matchId': m['matchId'],
                'fixtureId': m['fixtureId'],
                'namitiyuId': m['namitiyuId'],
                'matchNum': m['matchNum'],
                'league': m['league'],
            }
        
        print(f"    matchId映射: {len(mapping_by_matchId)} 条")
        print(f"    fixtureId映射: {len(mapping_by_fixtureId)} 条")
        print(f"    名称映射: {len(mapping_by_name)} 条")
        
        return {
            'mapping': mapping_by_name,
            'byMatchId': mapping_by_matchId,
            'byFixtureId': mapping_by_fixtureId,
        }
    
    def save_all(self, unified_matches, mappings):
        """保存所有数据"""
        print(">>> 保存数据...")
        
        os.makedirs(DIST_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        
        matches_list = list(unified_matches.values())
        
        live_data = {
            'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matches': [{
                'id': m['matchId'] or m['fixtureId'],
                'fid': m['fixtureId'],
                'matchNum': m['matchNum'],
                'league': m['league'],
                'date': m['date'],
                'time': m['time'],
                'home': m['home'],
                'away': m['away'],
                'homeScore': m['homeScore'],
                'awayScore': m['awayScore'],
                'status': m['status'],
                'minute': '',
                'statusOrder': 2 if m['status'] == 'upcoming' else 1,
                'namitiyuId': m['namitiyuId'],
            } for m in matches_list],
            'total': len(matches_list),
            'live': len([m for m in matches_list if m['status'] == 'live']),
            'finished': len([m for m in matches_list if m['status'] == 'finished']),
            'upcoming': len([m for m in matches_list if m['status'] == 'upcoming']),
        }
        
        self._save_to_all_locations('live_data.json', live_data)
        self._save_to_all_locations('fixture_mapping.json', mappings)
        
        print(f"    已保存 {len(matches_list)} 场比赛数据")
    
    def _save_to_all_locations(self, filename, data):
        """保存到多个位置"""
        paths = [
            os.path.join(BASE_DIR, 'dist', filename),
            os.path.join(BASE_DIR, 'dist', 'data', filename),
            os.path.join(BASE_DIR, 'data', filename),
        ]
        
        for path in paths:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def run(self):
        """运行匹配引擎"""
        print("=" * 60)
        print("比赛数据匹配引擎")
        print("=" * 60)
        
        sporttery_matches = self.fetch_sporttery_matches()
        matches_500 = self.fetch_500_matches()
        live_matches = self.fetch_live_500_matches()
        
        unified_matches = self.match_matches(sporttery_matches, matches_500, live_matches)
        
        # 获取namitiyuId
        fixture_ids = [m['fixtureId'] for m in unified_matches.values() if m['fixtureId']]
        namitiyu_map = self.fetch_namitiyu_ids(fixture_ids)
        
        # 应用namitiyuId
        for key, m in unified_matches.items():
            if m['fixtureId'] and m['fixtureId'] in namitiyu_map:
                m['namitiyuId'] = namitiyu_map[m['fixtureId']]
        
        mappings = self.build_mappings(unified_matches)
        
        self.save_all(unified_matches, mappings)
        
        print("\n" + "=" * 60)
        print("匹配完成")
        print("=" * 60)
        
        with_score = len([m for m in unified_matches.values() if m['homeScore'] > 0 or m['awayScore'] > 0])
        with_fid = len([m for m in unified_matches.values() if m['fixtureId']])
        with_namitiyu = len([m for m in unified_matches.values() if m['namitiyuId']])
        
        print(f"有fixtureId: {with_fid} 场")
        print(f"有namitiyuId: {with_namitiyu} 场")
        print(f"有比分: {with_score} 场")


if __name__ == '__main__':
    engine = MatchEngine()
    engine.run()