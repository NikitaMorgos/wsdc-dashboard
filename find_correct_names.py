#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск правильных имён в WSDC для указанных русских имён.
"""

import requests
import json
from bs4 import BeautifulSoup

LOOKUP_URL = "https://points.worldsdc.com/lookup2020"

names_to_check = [
    "Dmitry Aleksandrov",
    "Sergey Aleksandrov", 
    "Alexey Alyapkin",
    "Nikolay Arefev"
]

s = requests.Session()
s.trust_env = False

# Получаем токен
r1 = s.get(LOOKUP_URL, timeout=30)
soup = BeautifulSoup(r1.text, 'html.parser')
token = soup.find('input', {'name': '_token'}).get('value')

print("Поиск правильных имён в WSDC:")
print("=" * 60)

for q in names_to_check:
    print(f"\n{q}:")
    r2 = s.post(f"{LOOKUP_URL}/find", data={'_token': token, 'q': q}, timeout=30)
    data = r2.json()
    
    if 'leader' in data and data['leader'].get('type') == 'dancer':
        d = data['leader']['dancer']
        print(f"  Найден: {d.get('first_name')} {d.get('last_name')} (ID: {d.get('wscid')})")
    elif 'follower' in data and data['follower'].get('type') == 'dancer':
        d = data['follower']['dancer']
        print(f"  Найден: {d.get('first_name')} {d.get('last_name')} (ID: {d.get('wscid')})")
    elif 'names' in data:
        print(f"  Найдено {len(data['names'])} совпадений:")
        for n in data['names'][:5]:
            print(f"    - {n.get('dancer_name')} (ID: {n.get('wsdc_id')})")
    else:
        print("  Не найдено")
