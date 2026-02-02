#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправляет некорректные соответствия русских и английских имён.

Для указанных имён:
1. Удаляет неправильные записи
2. Ищет правильных танцоров в WSDC
3. Добавляет правильные записи с данными

Использование:
    python fix_incorrect_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice.csv 2026-01-28
"""

import sys
import time
import random
import pandas as pd
import requests

from wsdc_from_google_sheet import (
    ru_to_en,
    get_dancer_data,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)

# Список имён для исправления: (name_ru, правильное name_en или None для поиска)
NAMES_TO_FIX = [
    ("Александров Дмитрий", None),  # None = искать автоматически
    ("Александров Сергей", None),
    ("Аляпкин Алексей", None),
    ("Арефьев Николай", None),
]


def fix_incorrect_names(csv_file: str, as_of_date: str):
    """
    Исправляет некорректные соответствия имён.
    """
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ НЕКОРРЕКТНЫХ СООТВЕТСТВИЙ ИМЁН")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Дата: {as_of_date}")
    print()

    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")

    # Собираем неправильные записи для удаления
    incorrect_name_ru = [name_ru for name_ru, _ in NAMES_TO_FIX]
    incorrect_mask = df['name_ru'].isin(incorrect_name_ru)
    incorrect_count = incorrect_mask.sum()
    
    print(f"Найдено неправильных записей для удаления: {incorrect_count}")
    
    # Удаляем неправильные записи
    df_corrected = df[~incorrect_mask].copy()
    print(f"Записей после удаления: {len(df_corrected)}")
    print()

    # Создаём сессию
    session = requests.Session()
    session.trust_env = False

    try:
        from playwright.sync_api import sync_playwright
        use_js = True
    except ImportError:
        use_js = False

    # Обрабатываем каждое имя
    all_new_results = []
    
    for name_ru, correct_name_en in NAMES_TO_FIX:
        print(f"Обрабатываю: {name_ru}")
        
        # Если указано правильное английское имя, используем его
        if correct_name_en:
            name_en = correct_name_en
        else:
            # Иначе транслитерируем
            name_en = ru_to_en(name_ru)
        
        print(f"  Ищу: {name_en}...")
        
        # Получаем данные из WSDC
        results = get_dancer_data(name_ru, name_en, session, use_js_render=use_js)
        
        # Добавляем дату
        for r in results:
            r["as_of_date"] = as_of_date
        
        all_new_results.extend(results)
        print(f"  Найдено записей: {len(results)}")
        
        # Пауза между запросами
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        print()

    if not all_new_results:
        print("Не удалось получить новые данные.")
        return

    # Добавляем новые записи
    new_df = pd.DataFrame(all_new_results)
    columns_order = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date']
    new_df = new_df[[c for c in columns_order if c in new_df.columns]]

    # Объединяем
    combined = pd.concat([df_corrected, new_df], ignore_index=True)
    
    # Пересчитываем столбцы Novice и Allowed
    print("Пересчитываю столбцы Novice и Allowed...")
    
    # Находим максимальные поинты в Novice для каждого танцора
    combined['dancer_key'] = combined['name_en'].fillna(combined['name_ru'])
    novice_df = combined[combined['division'] == 'Novice'].copy()
    max_novice_points = novice_df.groupby('dancer_key')['points'].max().to_dict()
    
    # Добавляем/обновляем столбцы
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
    
    # Удаляем временный столбец
    combined = combined.drop(columns=['dancer_key'])
    
    # Упорядочиваем столбцы
    final_columns = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date', 'Novice', 'Allowed']
    combined = combined[[c for c in final_columns if c in combined.columns]]
    
    # Сохраняем
    output_file = csv_file.replace('.csv', '_fixed.csv')
    combined.to_csv(output_file, index=False, encoding='utf-8')
    
    # Статистика
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(combined)}")
    print(f"Удалено неправильных записей: {incorrect_count}")
    print(f"Добавлено правильных записей: {len(new_df)}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python fix_incorrect_names.py <csv_file> <as_of_date>")
        print("Пример: python fix_incorrect_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice.csv 2026-01-28")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    
    fix_incorrect_names(csv_file, as_of_date)
