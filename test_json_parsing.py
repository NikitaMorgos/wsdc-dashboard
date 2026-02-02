#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирует парсинг JSON для одного танцора.
"""

import requests
import json
from datetime import datetime
from wsdc_from_google_sheet import WSDC_LOOKUP_URL, HEADERS

def test_json_parsing(wsdc_id=10581):
    """Тестирует парсинг JSON"""
    session = requests.Session()
    session.trust_env = False
    
    print(f"Тестирую парсинг JSON для ID {wsdc_id}...")
    
    # Получаем CSRF токен
    response = session.get(WSDC_LOOKUP_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': '_token'})
    if not token_input:
        print("Не найден CSRF токен")
        return
    
    token = token_input.get('value', '')
    
    # Делаем POST запрос
    find_url = "https://points.worldsdc.com/lookup2020/find"
    data = {
        '_token': token,
        'num': wsdc_id
    }
    
    response = session.post(find_url, data=data, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    # Парсим JSON
    try:
        json_data = response.json()
    except:
        print("Не удалось распарсить JSON")
        return
    
    print("\n=== Структура данных ===")
    
    def parse_date(date_str):
        """Парсит дату в разных форматах"""
        if not date_str:
            return None
        date_str = str(date_str).strip()
        for fmt in ['%B %Y', '%b %Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    
    # Обрабатываем leader и follower
    for role_key in ['leader', 'follower']:
        if role_key not in json_data:
            continue
        
        role_data = json_data[role_key]
        role_name = 'Leader' if role_key == 'leader' else 'Follower'
        
        print(f"\n{role_name}:")
        
        if role_data.get('type') != 'dancer':
            print("  Не танцор")
            continue
        
        placements = role_data.get('placements', {})
        if not isinstance(placements, dict):
            print("  Нет placements")
            continue
        
        # Обрабатываем "West Coast Swing"
        for dance_type, divisions in placements.items():
            print(f"  {dance_type}:")
            
            for div_abbr, div_data in divisions.items():
                if not isinstance(div_data, dict):
                    continue
                
                division_info = div_data.get('division', {})
                division_name = division_info.get('name', div_abbr)
                competitions = div_data.get('competitions', [])
                
                print(f"    {division_name} ({div_abbr}): {len(competitions)} соревнований")
                
                all_events = []
                for comp in competitions:
                    event_info = comp.get('event', {})
                    event_name = event_info.get('name', '')
                    event_date = event_info.get('date', '')
                    points = comp.get('points', 0)
                    
                    if points > 0 and event_name and event_date:
                        all_events.append((event_date, event_name, points))
                        print(f"      - {event_name} ({event_date}): {points} очков")
                
                if all_events:
                    all_events.sort(key=lambda x: parse_date(x[0]) or datetime.min)
                    first_event = all_events[0]
                    last_event = all_events[-1]
                    print(f"      Первое: {first_event[1]} ({first_event[0]})")
                    print(f"      Последнее: {last_event[1]} ({last_event[0]})")

if __name__ == "__main__":
    test_json_parsing()
