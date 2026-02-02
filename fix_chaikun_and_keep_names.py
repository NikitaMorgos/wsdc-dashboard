#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для:
1. Добавления данных по Konstantin Chaikun (ID 26615) через API
2. Копирования name_en в name_ru для записей с комментарием "оставить только"
"""

import sys
import pandas as pd
import requests
from wsdc_from_google_sheet import get_dancer_points_via_api, GOOGLE_SHEET_ID
from apply_google_sheet_comments import read_google_sheet_with_comments, parse_comment

# Используем правильный ID Google Sheet
GOOGLE_SHEET_ID_COMMENTS = "1H4_s-hwIWLt7t-f_-dAn-gtUIRM7nyEGYKWBAu647H4"


def add_chaikun_data(df, wsdc_id=26615):
    """Добавляет данные по Konstantin Chaikun через API"""
    print(f"\nДобавляю данные по ID {wsdc_id} (Konstantin Chaikun)...")
    
    # Проверяем, есть ли уже записи с этим ID
    existing = df[df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id]
    
    if len(existing) > 0:
        print(f"  Найдено {len(existing)} существующих записей для ID {wsdc_id}")
        # Обновляем name_ru на "Чайкун Константин" если его нет
        for idx in existing.index:
            if not df.loc[idx, 'name_ru'] or df.loc[idx, 'name_ru'] == df.loc[idx, 'name_en']:
                df.loc[idx, 'name_ru'] = 'Чайкун Константин'
        print(f"  Обновлено name_ru на 'Чайкун Константин' для существующих записей")
        return df
    
    # Если записей нет, получаем данные через API
    print(f"  Получаю данные через API...")
    session = requests.Session()
    session.trust_env = False
    
    dancer_data = get_dancer_points_via_api(wsdc_id, session)
    
    if not dancer_data or not dancer_data.get("divisions"):
        print(f"  Предупреждение: не удалось получить данные для ID {wsdc_id}")
        return df
    
    # Определяем столбец с датой
    points_col = None
    for col in df.columns:
        if col.startswith('points_'):
            points_col = col
            break
    
    if not points_col:
        print("  Ошибка: не найден столбец с датой points_*")
        return df
    
    name_en = dancer_data.get("name", "Konstantin Chaikun")
    name_ru = "Чайкун Константин"
    
    # Добавляем записи для каждого дивизиона
    new_rows = []
    for div_info in dancer_data.get("divisions", []):
        division = div_info.get("division", "")
        role = div_info.get("role", "")
        points = div_info.get("points", 0)
        
        new_row = {
            'name_ru': name_ru,
            'name_en': name_en,
            'wsdc_id': float(wsdc_id),
            'division': division,
            'role': role,
            points_col: points,
            'Novice': 'X' if division == 'Novice' and points < 16 else '',
            'Allowed': 'X' if division == 'Novice' and 16 <= points <= 30 else ''
        }
        new_rows.append(new_row)
        print(f"    Добавлена запись: {division} {role} - {points} очков")
    
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
        print(f"  Добавлено {len(new_rows)} новых записей для ID {wsdc_id}")
    
    return df


def copy_en_to_ru_for_keep(df, sheet_id=GOOGLE_SHEET_ID_COMMENTS):
    """Копирует name_en в name_ru для записей с комментарием 'оставить только'"""
    print("\nКопирую name_en в name_ru для записей с комментарием 'оставить только'...")
    
    # Читаем комментарии из Google Sheet
    try:
        comments_df = read_google_sheet_with_comments(sheet_id)
    except Exception as e:
        print(f"Ошибка загрузки Google Sheet: {e}")
        return df
    
    # Находим столбцы - проверяем по индексу, если нет заголовков
    # Обычно: 0=name_ru, 1=name_en, 2=wsdc_id, 3=comment (столбец D)
    name_ru_col = None
    name_en_col = None
    wsdc_id_col = None
    comment_col = None
    
    # Сначала пробуем найти по названиям
    for col in comments_df.columns:
        col_lower = str(col).lower()
        if 'name_ru' in col_lower or ('имя' in col_lower and name_ru_col is None):
            name_ru_col = col
        elif 'name_en' in col_lower:
            name_en_col = col
        elif 'wsdc_id' in col_lower or ('id' in col_lower and wsdc_id_col is None):
            wsdc_id_col = col
        elif 'comment' in col_lower or 'комментарий' in col_lower or col == 'D':
            comment_col = col
    
    # Если не нашли по названиям, используем индексы (0, 1, 2, 3)
    if not comment_col and len(comments_df.columns) >= 4:
        comment_col = comments_df.columns[3]  # Столбец D (индекс 3)
    if not name_ru_col and len(comments_df.columns) >= 1:
        name_ru_col = comments_df.columns[0]  # Столбец A (индекс 0)
    if not name_en_col and len(comments_df.columns) >= 2:
        name_en_col = comments_df.columns[1]  # Столбец B (индекс 1)
    if not wsdc_id_col and len(comments_df.columns) >= 3:
        wsdc_id_col = comments_df.columns[2]  # Столбец C (индекс 2)
    
    if not comment_col:
        print("  Не найден столбец с комментариями")
        print(f"  Доступные столбцы: {list(comments_df.columns)}")
        return df
    
    print(f"  Найден столбец комментариев: {comment_col} (индекс {list(comments_df.columns).index(comment_col)})")
    
    # Создаем карту комментариев - собираем все ID, которые были обработаны с "keep"
    keep_ids = set()
    print(f"  Проверяю {len(comments_df)} строк на наличие комментариев 'keep'...")
    
    for idx, row in comments_df.iterrows():
        comment = str(row[comment_col]).strip() if comment_col and comment_col in row else ''
        
        if pd.isna(comment) or not comment or str(comment).strip() == '':
            continue
        
        # Парсим комментарий
        action, params = parse_comment(comment)
        
        if action == 'keep':
            wsdc_id = params
            if wsdc_id:
                keep_ids.add(wsdc_id)
                # Не выводим name_en, так как там могут быть проблемные символы
    
    print(f"  Всего найдено {len(keep_ids)} ID с комментарием 'keep': {sorted(keep_ids)}")
    
    # Применяем изменения - для всех записей с этими ID копируем name_en в name_ru
    updated_count = 0
    for wsdc_id in keep_ids:
        # Находим все записи с этим ID
        mask = df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id
        matching_rows = df[mask]
        
        if len(matching_rows) > 0:
            # Копируем name_en в name_ru
            for idx in matching_rows.index:
                name_en_val = df.loc[idx, 'name_en']
                if pd.notna(name_en_val) and str(name_en_val).strip():
                    old_name_ru = df.loc[idx, 'name_ru']
                    df.loc[idx, 'name_ru'] = str(name_en_val).strip()
                    if old_name_ru != df.loc[idx, 'name_ru']:
                        updated_count += 1
                        print(f"  ID {wsdc_id}: скопировано '{name_en_val}' в name_ru (было: '{old_name_ru}')")
    
    print(f"  Обновлено {updated_count} записей")
    return df


def main():
    if len(sys.argv) < 2:
        print("Использование: python fix_chaikun_and_keep_names.py <input_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    print("=" * 60)
    print("ДОБАВЛЕНИЕ ДАННЫХ ПО CHAIKUN И КОПИРОВАНИЕ ИМЕН")
    print("=" * 60)
    
    # Читаем CSV
    print(f"\nЧитаю файл: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    # Добавляем данные по Chaikun
    df = add_chaikun_data(df, wsdc_id=26615)
    
    # Копируем name_en в name_ru для "keep"
    df = copy_en_to_ru_for_keep(df)
    
    # Сохраняем результат
    output_file = input_file.replace('.csv', '_fixed_names.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print("\n" + "=" * 60)
    print(f"Готово! Результат сохранен в: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
