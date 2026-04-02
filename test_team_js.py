#!/usr/bin/env python3
import requests
import re

url = 'https://zq.titan007.com/jsData/teamInfo/teamDetail/tdl7.js'
resp = requests.get(url, timeout=10)
content = resp.text

print('JS内容长度:', len(content))
print('前500字符:', content[:500])

pattern = r"var teamDetail\s*=\s*\[(\d+),(.+?),\'',\s*([\d.]+),\s*(\d+)\];"
team_detail_match = re.search(pattern, content, re.DOTALL)
print('正则匹配结果:', team_detail_match is not None)

if not team_detail_match:
    if 'teamDetail' in content:
        idx = content.index('teamDetail')
        print('teamDetail位置:', idx)
        print('teamDetail附近:', content[idx:idx+200])