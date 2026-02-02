#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск правильных танцоров для указанных русских имён, пробуя разные варианты.
"""

import requests
import json
import time
from bs4 import BeautifulSoup

LOOKUP_URL = "https://points.worldsdc.com/lookup2020"

# Варианты поиска для каждого имени
SEARCH_VARIANTS = {
    "Александров Дмитрий": [
        "Dmitry Aleksandrov",
        "Dmitry Alexandrov", 
        "Dmitriy Aleksandrov",
        "Dmitriy Alexandrov",
        "Aleksandrov Dmitry",
        "Aleksandrov Dmitriy"
    ],
    "Александров Сергей": [
        "Sergey Aleksandrov",
        "Sergey Alexandrov",
        "Sergei Aleksandrov", 
        "Sergei Alexandrov",
        "Aleksandrov Sergey",
        "Aleksandrov Sergei"
    ],
    "Аляпкин Алексей": [
        "Alexey Alyapkin",
        "Aleksey Alyapkin",
        "Alexei Alyapkin",
        "Alyapkin Alexey",
        "Alyapkin Aleksey"
    ],
    "Арефьев Николай": [
        "Nikolay Arefev",
        "Nikolai Arefev",
        "Arefev Nikolay",
        "Arefev Nikolai"
    ]
}

s = requests.Session()
s.trust_env = False

# Получаем токен
print("Получаю CSRF токен...")
r1 = s.get(LOOKUP_URL, timeout=30)
soup = BeautifulSoup(r1.text, 'html.parser')
token = soup.find('input', {'name': '_token'}).get('value')

print("\nПоиск правильных имён в WSDC:")
print("=" * 60)

for name_ru, variants in SEARCH_VARIANTS.items():
    print(f"\n{name_ru}:")
    found = False
    
    for variant in variants:
        print(f"  Пробую: {variant}...", end=" ")
        try:
            r2 = s.post(f"{LOOKUP_URL}/find", data={'_token': token, 'q': variant}, timeout=30)
            data = r2.json()
            
            if 'leader' in data and data['leader'].get('type') == 'dancer':
                d = data['leader']['dancer']
                found_name = f"{d.get('first_name')} {d.get('last_name')}"
                wsdc_id = d.get('wscid')
                print(f"✓ Найден: {found_name} (ID: {wsdc_id})")
                found = True
                break
            elif 'follower' in data and data['follower'].get('type') == 'dancer':
                d = data['follower']['dancer']
                found_name = f"{d.get('first_name')} {d.get('last_name')}"
                wsdc_id = d.get('wscid')
                print(f"✓ Найден: {found_name} (ID: {wsdc_id})")
                found = True
                break
            elif 'names' in data and len(data['names']) > 0:
                print(f"Найдено {len(data['names'])} совпадений:")
                for n in data['names'][:3]:
                    print(f"    - {n.get('dancer_name')} (ID: {n.get('wsdc_id')})")
                # Берём первое совпадение, если оно похоже
                first = data['names'][0]
                if first.get('dancer_name'):
                    print(f"  → Использую: {first.get('dancer_name')} (ID: {first.get('wsdc_id')})")
                    found = True
                    break
            else:
                print("не найдено")
            
            time.sleep(0.5)  # Пауза между запросами
        except Exception as e:
            print(f"ошибка: {e}")
    
    if not found:
        print("  [X] Не найдено ни одного совпадения")
