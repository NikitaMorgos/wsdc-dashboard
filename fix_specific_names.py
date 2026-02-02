#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправляет конкретные некорректные соответствия имён по указанным ID.

Использование:
    python fix_specific_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated.csv 2026-01-28
"""

import sys
import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup

from wsdc_from_google_sheet import (
    get_dancer_points_via_api,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)

# Имена для исправления: (name_ru, правильный wsdc_id)
NAMES_TO_FIX = [
    ("Артемьев Алексей", 16925),
    ("Бойкова Татьяна", 19101),
    ("Борисов Евгений", 25590),
]

# Имена для удаления
NAMES_TO_DELETE = [
    "Ахтемиров Евгений",
    "Бабин Сергей",
]

# Имена для проверки и разделения
NAMES_TO_CHECK = [
    "Ботаногова Полина",
    "Бустерьяков Андрей",
    "Бугаев Сергей",
    "Бурш Дмитрий",
    "Бухтияров Иван",
    "Быков Дмитрий",
    "Вайншток Александр",
]


def get_dancer_by_id(wsdc_id: int, session: requests.Session) -> dict:
    """Получает данные танцора по WSDC ID."""
    return get_dancer_points_via_api(wsdc_id, session)


def fix_specific_names(csv_file: str, as_of_date: str):
    """
    Исправляет конкретные некорректные соответствия.
    """
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ КОНКРЕТНЫХ ИМЁН")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Дата: {as_of_date}")
    print()

    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")

    # 1. Удаляем записи для удаления
    delete_mask = df['name_ru'].isin(NAMES_TO_DELETE)
    delete_count = delete_mask.sum()
    print(f"Удаляю {len(NAMES_TO_DELETE)} имён: {delete_count} записей")
    df = df[~delete_mask].copy()
    print(f"Записей после удаления: {len(df)}")
    print()

    # 2. Удаляем неправильные записи для исправляемых имён
    fix_names_ru = [name_ru for name_ru, _ in NAMES_TO_FIX]
    fix_mask = df['name_ru'].isin(fix_names_ru)
    fix_count = fix_mask.sum()
    print(f"Удаляю неправильные записи для исправления: {fix_count} записей")
    df = df[~fix_mask].copy()
    print(f"Записей после удаления неправильных: {len(df)}")
    print()

    # 3. Удаляем неправильные записи для проверяемых имён
    check_mask = df['name_ru'].isin(NAMES_TO_CHECK)
    check_count = check_mask.sum()
    print(f"Удаляю записи для проверки: {check_count} записей")
    df = df[~check_mask].copy()
    print(f"Записей после удаления проверяемых: {len(df)}")
    print()

    # Создаём сессию
    session = requests.Session()
    session.trust_env = False

    all_new_results = []

    # 4. Добавляем правильные данные для исправляемых имён
    print("Добавляю правильные данные для исправляемых имён:")
    print("-" * 60)
    for name_ru, wsdc_id in NAMES_TO_FIX:
        print(f"{name_ru} (ID: {wsdc_id})...")
        dancer_data = get_dancer_by_id(wsdc_id, session)
        
        if dancer_data.get("name"):
            name_en = dancer_data["name"]
            print(f"  Найден: {name_en}")
            
            if dancer_data.get("divisions"):
                for div in dancer_data["divisions"]:
                    all_new_results.append({
                        "name_ru": name_ru,
                        "name_en": name_en,
                        "wsdc_id": wsdc_id,
                        "division": div.get("division", ""),
                        "role": div.get("role", ""),
                        "points": div.get("points", 0),
                        "as_of_date": as_of_date,
                        "Novice": "",
                        "Allowed": ""
                    })
                print(f"  Добавлено записей: {len(dancer_data['divisions'])}")
            else:
                # Если нет дивизионов, создаём запись без данных
                all_new_results.append({
                    "name_ru": name_ru,
                    "name_en": name_en,
                    "wsdc_id": wsdc_id,
                    "division": "",
                    "role": "",
                    "points": 0,
                    "as_of_date": as_of_date,
                    "Novice": "",
                    "Allowed": ""
                })
                print(f"  Добавлена запись без дивизионов")
        else:
            print(f"  Не удалось получить имя для ID {wsdc_id}")
        
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        print()

    # 5. Создаём отдельные записи для проверяемых имён (без данных, так как неправильно склеены)
    print("Создаю отдельные записи для проверяемых имён (без данных):")
    print("-" * 60)
    
    for name_ru in NAMES_TO_CHECK:
        from wsdc_from_google_sheet import ru_to_en
        name_en = ru_to_en(name_ru)
        
        # Создаём запись без данных (неправильно склеены, нужно разделить)
        all_new_results.append({
            "name_ru": name_ru,
            "name_en": name_en,
            "wsdc_id": None,
            "division": "",
            "role": "",
            "points": 0,
            "as_of_date": as_of_date,
            "Novice": "",
            "Allowed": ""
        })
        print(f"{name_ru} -> {name_en} (без данных, разделено)")
    
    print()

    # Объединяем
    if all_new_results:
        new_df = pd.DataFrame(all_new_results)
        columns_order = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date', 'Novice', 'Allowed']
        new_df = new_df[[c for c in columns_order if c in new_df.columns]]
        
        combined = pd.concat([df, new_df], ignore_index=True)
    else:
        combined = df

    # Пересчитываем столбцы Novice и Allowed
    print("Пересчитываю столбцы Novice и Allowed...")
    
    combined['dancer_key'] = combined['name_en'].fillna(combined['name_ru'])
    novice_df = combined[combined['division'] == 'Novice'].copy()
    max_novice_points = novice_df.groupby('dancer_key')['points'].max().to_dict()
    
    if 'Novice' not in combined.columns:
        combined['Novice'] = ''
    if 'Allowed' not in combined.columns:
        combined['Allowed'] = ''
    
    combined['Novice'] = ''
    combined['Allowed'] = ''
    
    for idx, row in combined.iterrows():
        dancer_key = row['dancer_key']
        novice_points = max_novice_points.get(dancer_key, None)
        
        if novice_points is not None:
            if novice_points < 16:
                combined.at[idx, 'Novice'] = 'X'
            elif 16 <= novice_points <= 30:
                combined.at[idx, 'Allowed'] = 'X'
    
    combined = combined.drop(columns=['dancer_key'])
    
    # Упорядочиваем столбцы
    final_columns = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date', 'Novice', 'Allowed']
    combined = combined[[c for c in final_columns if c in combined.columns]]
    
    # Сохраняем
    output_file = csv_file.replace('.csv', '_fixed_specific.csv')
    combined.to_csv(output_file, index=False, encoding='utf-8')
    
    print()
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(combined)}")
    print(f"Удалено записей: {delete_count + fix_count + check_count}")
    print(f"Добавлено правильных записей: {len(all_new_results)}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python fix_specific_names.py <csv_file> <as_of_date>")
        print("Пример: python fix_specific_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated.csv 2026-01-28")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    
    fix_specific_names(csv_file, as_of_date)
