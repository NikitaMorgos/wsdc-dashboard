#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для повторной обработки записей без данных из существующего CSV.

Использование:
    python retry_missing_data.py wsdc_points_2026-01-28.csv 2026-01-28
"""

import sys
import pandas as pd
import time
from typing import Optional

# Импортируем функции из основного скрипта
from wsdc_from_google_sheet import (
    get_dancer_data, 
    WSDC_SEARCH_API,
    HEADERS,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX
)
import requests
import random


def retry_missing_data(csv_file: str, as_of_date: str, limit: Optional[int] = None):
    """
    Повторно обрабатывает записи без данных из CSV файла.
    
    Args:
        csv_file: Путь к CSV файлу
        as_of_date: Дата в формате YYYY-MM-DD
    """
    print("=" * 60, flush=True)
    print("ПОВТОРНАЯ ОБРАБОТКА ЗАПИСЕЙ БЕЗ ДАННЫХ", flush=True)
    print("=" * 60, flush=True)
    print(f"CSV файл: {csv_file}", flush=True)
    print(f"Дата: {as_of_date}", flush=True)
    print(flush=True)
    
    # Читаем CSV
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except Exception as e:
        print(f"Ошибка чтения CSV файла: {e}", flush=True)
        sys.exit(1)
    
    print(f"Всего записей в CSV: {len(df)}", flush=True)
    
    # Находим записи без данных (wsdc_id пустой или None, или points = 0)
    missing_mask = (
        (df['wsdc_id'].isna()) | 
        (df['wsdc_id'] == '') | 
        (df['points'] == 0) |
        (df['division'].isna()) |
        (df['division'] == '')
    )
    
    missing_df = df[missing_mask].copy()
    print(f"Записей без данных: {len(missing_df)}", flush=True)
    
    if len(missing_df) == 0:
        print("Все записи имеют данные. Повторная обработка не требуется.", flush=True)
        return
    
    # Убираем дубликаты по name_ru
    unique_names = missing_df[['name_ru', 'name_en']].drop_duplicates()
    
    # Ограничение для теста (если указано)
    if limit and limit > 0:
        unique_names = unique_names.head(limit)
        print(f"Обработка ограничена {limit} записями (для теста)", flush=True)
    
    print(f"Уникальных имён для обработки: {len(unique_names)}", flush=True)
    print(flush=True)
    
    # Проверяем, установлен ли Playwright
    try:
        from playwright.sync_api import sync_playwright
        use_js_render = True
        print("Playwright найден, будет использоваться JS-рендеринг", flush=True)
    except ImportError:
        use_js_render = False
        print("Playwright не установлен, используется базовый парсинг", flush=True)
    
    print(flush=True)
    
    # Создаём сессию
    session = requests.Session()
    # Отключаем использование переменных окружения прокси (HTTP(S)_PROXY),
    # чтобы requests ходил напрямую.
    session.trust_env = False
    
    # Обрабатываем каждое уникальное имя
    updated_count = 0
    new_results = []
    
    for idx, row in unique_names.iterrows():
        name_ru = str(row['name_ru']).strip()
        name_en = str(row['name_en']).strip()
        
        print(f"[{updated_count + 1}/{len(unique_names)}] Обрабатываю: {name_ru} ({name_en})", flush=True)
        
        # Получаем данные
        results = get_dancer_data(name_ru, name_en, session, use_js_render)
        
        # Добавляем дату
        for r in results:
            r["as_of_date"] = as_of_date
        
        new_results.extend(results)
        updated_count += 1
        
        # Пауза между запросами
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        
        print(flush=True)
    
    if not new_results:
        print("Не удалось получить новые данные.", flush=True)
        return
    
    # Объединяем результаты
    # Сначала удаляем старые записи без данных
    df_with_data = df[~missing_mask].copy()
    
    # Добавляем новые результаты
    new_df = pd.DataFrame(new_results)
    
    # Объединяем
    final_df = pd.concat([df_with_data, new_df], ignore_index=True)
    
    # Упорядочиваем столбцы
    columns_order = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date']
    final_df = final_df[[c for c in columns_order if c in final_df.columns]]
    
    # Сохраняем обновлённый файл
    output_file = csv_file.replace('.csv', '_updated.csv')
    final_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(flush=True)
    print("=" * 60, flush=True)
    print(f"Готово! Обновлённые данные сохранены в: {output_file}", flush=True)
    print(f"Всего записей: {len(final_df)}", flush=True)
    print(f"Записей с данными: {len(final_df[final_df['wsdc_id'].notna() & (final_df['points'] > 0)])}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python retry_missing_data.py <csv_file> <as_of_date> [limit]", flush=True)
        print("Пример: python retry_missing_data.py wsdc_points_2026-01-28.csv 2026-01-28", flush=True)
        print("Пример (только первые 10): python retry_missing_data.py wsdc_points_2026-01-28.csv 2026-01-28 10", flush=True)
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # Проверяем формат даты
    import re
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', as_of_date):
        print(f"Ошибка: дата должна быть в формате YYYY-MM-DD, получено: {as_of_date}", flush=True)
        sys.exit(1)
    
    from typing import Optional
    retry_missing_data(csv_file, as_of_date, limit)
