#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавляет столбцы с информацией о событиях:
- last_event_date: дата последнего заработанного пойнта
- last_event_name: название ивента последнего пойнта
- first_event_date: дата первого заработанного пойнта в дивизионе
- novice_closed_date: дата закрытия новисов (ивент, где заработан 16-й пойнт)
- months_to_close_novice: количество месяцев между первым пойнтом и закрытием новисов
"""

import sys
import pandas as pd
import requests
import time
import random
from bs4 import BeautifulSoup
import re
from datetime import datetime
try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
from wsdc_from_google_sheet import WSDC_LOOKUP_URL, HEADERS, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


def get_all_events_info(wsdc_id: int, session: requests.Session):
    """
    Получает информацию о всех событиях для танцора (для всех дивизионов и ролей).
    
    Returns:
        Словарь {(division, role): {
            'last_event': (date, name),
            'first_event': (date, name),
            'all_events': [(date, name, points), ...]  # отсортированы по дате
        }}
    """
    result = {}
    
    try:
        # Получаем CSRF токен
        response = session.get(WSDC_LOOKUP_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        if not token_input:
            return result
        
        token = token_input.get('value', '')
        if not token:
            return result
        
        # Делаем POST запрос
        find_url = "https://points.worldsdc.com/lookup2020/find"
        data = {
            '_token': token,
            'num': wsdc_id
        }
        
        response = session.post(find_url, data=data, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Парсим JSON ответ
        try:
            json_data = response.json()
        except:
            # Если не JSON, пробуем HTML (fallback)
            return result
        
        # Структура JSON:
        # {"leader": {"placements": {"West Coast Swing": {"INT": {"competitions": [...]}, "NOV": {...}}}}, "follower": {...}}
        
        def parse_date(date_str):
            """Парсит дату в разных форматах"""
            if not date_str:
                return None
            date_str = str(date_str).strip()
            # Форматы: "August 2016", "March 2015", "February 2016", etc.
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
            
            if role_data.get('type') != 'dancer':
                continue
            
            placements = role_data.get('placements', {})
            if not isinstance(placements, dict):
                continue
            
            # Обрабатываем "West Coast Swing" и другие типы танцев
            for dance_type, divisions in placements.items():
                if not isinstance(divisions, dict):
                    continue
                
                # Обрабатываем каждый дивизион (INT, NOV, ADV, etc.)
                for div_abbr, div_data in divisions.items():
                    if not isinstance(div_data, dict):
                        continue
                    
                    # Получаем название дивизиона
                    division_info = div_data.get('division', {})
                    division_name = division_info.get('name', div_abbr)
                    
                    # Получаем competitions
                    competitions = div_data.get('competitions', [])
                    if not competitions:
                        continue
                    
                    # Собираем все события
                    all_events = []
                    for comp in competitions:
                        event_info = comp.get('event', {})
                        event_name = event_info.get('name', '')
                        event_date = event_info.get('date', '')
                        points = comp.get('points', 0)
                        
                        if points > 0 and event_name and event_date:
                            all_events.append((event_date, event_name, points))
                    
                    if all_events:
                        # Сортируем события по дате (от старых к новым)
                        all_events.sort(key=lambda x: parse_date(x[0]) or datetime.min)
                        
                        first_event = all_events[0] if all_events else None
                        last_event = all_events[-1] if all_events else None
                        
                        result[(division_name, role_name)] = {
                            'last_event': (last_event[0], last_event[1]) if last_event else (None, None),
                            'first_event': (first_event[0], first_event[1]) if first_event else (None, None),
                            'all_events': all_events
                        }
        
        return result
    
    except Exception as e:
        print(f"    Ошибка получения данных для ID {wsdc_id}: {e}", flush=True)
        return result


def get_last_event_info(wsdc_id: int, division: str, role: str, session: requests.Session):
    """
    Получает информацию о последнем заработанном пойнте для конкретного дивизиона и роли.
    Устаревшая функция - используйте get_all_events_info для оптимизации.
    
    Returns:
        (last_event_date, last_event_name) или (None, None)
    """
    try:
        # Получаем CSRF токен
        response = session.get(WSDC_LOOKUP_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        token_input = soup.find('input', {'name': '_token'})
        if not token_input:
            return None, None
        
        token = token_input.get('value', '')
        if not token:
            return None, None
        
        # Делаем POST запрос
        find_url = "https://points.worldsdc.com/lookup2020/find"
        data = {
            '_token': token,
            'num': wsdc_id
        }
        
        response = session.post(find_url, data=data, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Парсим HTML ответ
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем секцию с нужной ролью
        h2_elements = soup.find_all('h2')
        target_role = None
        
        for h2 in h2_elements:
            h2_text = h2.get_text(strip=True)
            if role in h2_text:
                target_role = h2
                break
        
        if not target_role:
            return None, None
        
        # Ищем h3 с нужным дивизионом
        next_elem = target_role.find_next_sibling()
        target_division = None
        
        while next_elem and next_elem.name != 'h2':
            if next_elem.name == 'h3':
                div_text = next_elem.get_text(strip=True)
                # Проверяем, соответствует ли дивизион
                if division.upper() in div_text.upper() or div_text.upper() in division.upper():
                    target_division = next_elem
                    break
            next_elem = next_elem.find_next_sibling()
        
        if not target_division:
            return None, None
        
        # Ищем таблицу с событиями после h3
        table = target_division.find_next_sibling('table')
        if not table:
            # Может быть обёрнут в div
            parent = target_division.parent
            if parent:
                table = parent.find('table')
        
        if not table:
            return None, None
        
        # Парсим таблицу - ищем последнюю строку с очками
        rows = table.find_all('tr')
        last_event_date = None
        last_event_name = None
        
        # Пропускаем заголовок
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                # Обычно структура: Event Name | Date | Points | ...
                event_name = cells[0].get_text(strip=True) if len(cells) > 0 else ''
                event_date = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                points = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                
                # Проверяем, есть ли очки
                try:
                    points_val = int(re.search(r'\d+', points).group()) if re.search(r'\d+', points) else 0
                    if points_val > 0 and event_name and event_date:
                        last_event_date = event_date
                        last_event_name = event_name
                except:
                    pass
        
        return last_event_date, last_event_name
    
    except Exception as e:
        print(f"    Ошибка получения данных для ID {wsdc_id}: {e}", flush=True)
        return None, None


def add_event_info_to_csv(csv_file: str):
    """
    Добавляет столбцы с информацией о последнем ивенте.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    # Добавляем новые столбцы
    df['last_event_date'] = ''
    df['last_event_name'] = ''
    df['first_event_date'] = ''
    df['novice_closed_date'] = ''  # Дата закрытия новисов (16-й пойнт)
    df['months_to_close_novice'] = ''  # Количество месяцев до закрытия новисов
    
    # Группируем по уникальным wsdc_id (делаем один запрос на танцора)
    unique_ids = df['wsdc_id'].dropna().unique()
    
    print(f"\nОбрабатываю {len(unique_ids)} уникальных танцоров...")
    
    session = requests.Session()
    session.trust_env = False
    
    event_info_cache = {}  # Кэш по wsdc_id
    
    for wsdc_id_val in unique_ids:
        wsdc_id = int(wsdc_id_val) if pd.notna(wsdc_id_val) else None
        
        if not wsdc_id:
            continue
        
        # Получаем информацию для всех дивизионов/ролей этого танцора одним запросом
        print(f"  ID {wsdc_id}...", flush=True)
        events_info = get_all_events_info(wsdc_id, session)
        event_info_cache[wsdc_id] = events_info
        
        # Пауза между запросами
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        
        # Выводим найденную информацию
        if events_info:
            for (div, rol), info in events_info.items():
                if info.get('last_event'):
                    date, name = info['last_event']
                    print(f"    {div} {rol}: {name} ({date})", flush=True)
    
    # Применяем кешированные данные ко всем записям
    print("\nПрименяю данные к записям...", flush=True)
    
    def parse_date(date_str):
        """Парсит дату в разных форматах"""
        if not date_str or pd.isna(date_str):
            return None
        date_str = str(date_str).strip()
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%B %d, %Y', '%b %d, %Y', '%m-%d-%Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    
    def calculate_months_diff(date1, date2):
        """Вычисляет разницу в месяцах между двумя датами"""
        if not date1 or not date2:
            return None
        d1 = parse_date(date1)
        d2 = parse_date(date2)
        if not d1 or not d2:
            return None
        
        if HAS_DATEUTIL:
            # Используем relativedelta для точного расчета месяцев
            try:
                delta = relativedelta(d2, d1)
                months = delta.years * 12 + delta.months
                # Если дни тоже важны, можно добавить части месяца
                if delta.days > 15:  # Если больше половины месяца
                    months += 1
                return months
            except:
                pass
        
        # Fallback на простой расчет
        months = (d2.year - d1.year) * 12 + (d2.month - d1.month)
        if d2.day < d1.day:
            months -= 1
        return months
    
    for idx, row in df.iterrows():
        wsdc_id = int(row['wsdc_id']) if pd.notna(row['wsdc_id']) else None
        division = str(row['division']) if pd.notna(row['division']) else ''
        role = str(row['role']) if pd.notna(row['role']) else ''
        
        if wsdc_id and wsdc_id in event_info_cache:
            events_info = event_info_cache[wsdc_id]
            # Ищем точное совпадение или частичное
            key = None
            for (div, rol), info in events_info.items():
                if (division.upper() in div.upper() or div.upper() in division.upper()) and role == rol:
                    key = (div, rol)
                    break
            
            if key and events_info[key]:
                info = events_info[key]
                
                # Последнее событие
                if info.get('last_event'):
                    last_event_date, last_event_name = info['last_event']
                    df.loc[idx, 'last_event_date'] = last_event_date if last_event_date else ''
                    df.loc[idx, 'last_event_name'] = last_event_name if last_event_name else ''
                
                # Первое событие
                if info.get('first_event'):
                    first_event_date, first_event_name = info['first_event']
                    df.loc[idx, 'first_event_date'] = first_event_date if first_event_date else ''
                
                # Для Novice дивизиона: находим событие, где было заработано 16 очков
                if division.upper() == 'NOVICE' and info.get('all_events'):
                    all_events = info['all_events']
                    # Накапливаем очки по порядку событий
                    total_points = 0
                    novice_closed_date = None
                    
                    for event_date, event_name, points in all_events:
                        total_points += points
                        if total_points >= 16 and not novice_closed_date:
                            novice_closed_date = event_date
                            break
                    
                    if novice_closed_date:
                        df.loc[idx, 'novice_closed_date'] = novice_closed_date
                        
                        # Вычисляем количество месяцев
                        first_date = info.get('first_event', (None, None))[0]
                        if first_date:
                            months = calculate_months_diff(first_date, novice_closed_date)
                            if months is not None:
                                df.loc[idx, 'months_to_close_novice'] = months
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_with_events.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nРезультат сохранен: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    
    # Статистика
    filled_dates = df['last_event_date'].notna() & (df['last_event_date'] != '')
    filled_names = df['last_event_name'].notna() & (df['last_event_name'] != '')
    print(f"Заполнено дат: {filled_dates.sum()}")
    print(f"Заполнено названий: {filled_names.sum()}")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Использование: python add_event_info.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("ДОБАВЛЕНИЕ ИНФОРМАЦИИ О ПОСЛЕДНЕМ ИВЕНТЕ")
    print("=" * 60)
    print()
    print("ВНИМАНИЕ: Это может занять много времени из-за запросов к API")
    print()
    
    try:
        add_event_info_to_csv(csv_file)
        print()
        print("=" * 60)
        print("ГОТОВО!")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
