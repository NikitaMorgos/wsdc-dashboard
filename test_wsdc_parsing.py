#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки структуры HTML страницы WSDC.
"""

import requests
from bs4 import BeautifulSoup
from wsdc_from_google_sheet import WSDC_LOOKUP_URL, HEADERS

def test_parsing(wsdc_id=10581):
    """Тестирует парсинг для одного танцора"""
    session = requests.Session()
    session.trust_env = False
    
    print(f"Тестирую парсинг для ID {wsdc_id}...")
    
    # Получаем CSRF токен
    response = session.get(WSDC_LOOKUP_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': '_token'})
    if not token_input:
        print("Не найден CSRF токен")
        return
    
    token = token_input.get('value', '')
    print(f"CSRF токен получен: {token[:20]}...")
    
    # Делаем POST запрос
    find_url = "https://points.worldsdc.com/lookup2020/find"
    data = {
        '_token': token,
        'num': wsdc_id
    }
    
    response = session.post(find_url, data=data, headers=HEADERS, timeout=30)
    response.raise_for_status()
    
    # Сохраняем HTML для анализа
    with open('test_wsdc_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML сохранен в test_wsdc_page.html")
    
    # Парсим HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n=== Анализ структуры ===")
    
    # Ищем все h2
    h2_elements = soup.find_all('h2')
    print(f"\nНайдено h2 элементов: {len(h2_elements)}")
    for i, h2 in enumerate(h2_elements[:5]):
        print(f"  h2[{i}]: {h2.get_text(strip=True)}")
    
    # Ищем все h3
    h3_elements = soup.find_all('h3')
    print(f"\nНайдено h3 элементов: {len(h3_elements)}")
    for i, h3 in enumerate(h3_elements[:10]):
        print(f"  h3[{i}]: {h3.get_text(strip=True)}")
    
    # Ищем все таблицы
    tables = soup.find_all('table')
    print(f"\nНайдено таблиц: {len(tables)}")
    for i, table in enumerate(tables[:3]):
        print(f"\n  Таблица {i}:")
        rows = table.find_all('tr')
        print(f"    Строк: {len(rows)}")
        if len(rows) > 0:
            # Показываем заголовок
            header = rows[0]
            cells = header.find_all(['th', 'td'])
            print(f"    Заголовок: {[cell.get_text(strip=True) for cell in cells]}")
            # Показываем первые 3 строки данных
            for j, row in enumerate(rows[1:4]):
                cells = row.find_all(['td', 'th'])
                print(f"    Строка {j+1}: {[cell.get_text(strip=True)[:50] for cell in cells]}")
    
    # Ищем структуру вокруг h3
    print("\n=== Структура вокруг h3 ===")
    for h3 in h3_elements[:3]:
        print(f"\n  h3: {h3.get_text(strip=True)}")
        # Ищем следующую таблицу
        next_elem = h3.find_next_sibling()
        print(f"    Следующий элемент: {next_elem.name if next_elem else 'None'}")
        if next_elem and next_elem.name == 'table':
            print(f"    Найдена таблица сразу после h3")
        else:
            # Ищем в родителе
            parent = h3.parent
            if parent:
                table = parent.find('table')
                if table:
                    print(f"    Найдена таблица в родителе")
                else:
                    # Ищем дальше
                    current = h3
                    for _ in range(5):
                        current = current.find_next_sibling()
                        if not current:
                            break
                        if current.name == 'table':
                            print(f"    Найдена таблица через {_} элементов")
                            break

if __name__ == "__main__":
    test_parsing()
