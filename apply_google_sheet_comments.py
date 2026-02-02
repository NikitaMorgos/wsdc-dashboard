#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обрабатывает комментарии из столбца D Google Таблицы и применяет изменения.

Использование:
    python apply_google_sheet_comments.py <csv_file> <google_sheet_id>
"""

import sys
import pandas as pd
import requests
import time
import random
import os
from urllib.parse import quote

from wsdc_from_google_sheet import (
    get_dancer_points_via_api,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)

GOOGLE_SHEET_ID = "1H4_s-hwIWLt7t-f_-dAn-gtUIRM7nyEGYKWBAu647H4"


def read_google_sheet_with_comments(sheet_id: str):
    """
    Читает Google Sheet с комментариями из столбца D.
    """
    print("Загружаю данные из Google Sheets...")
    
    # Пробуем несколько вариантов URL
    urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
    ]
    
    for url in urls:
        try:
            print(f"Пробую URL: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Сохраняем во временный файл для чтения
                temp_file = "temp_google_sheet.csv"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                
                # Читаем CSV
                df = pd.read_csv(temp_file, encoding='utf-8')
                os.remove(temp_file)
                
                print(f"Загружено {len(df)} строк")
                return df
        except Exception as e:
            print(f"Ошибка с URL {url}: {e}")
            continue
    
    raise Exception("Не удалось загрузить данные из Google Sheets")


def parse_comment(comment: str):
    """
    Парсит комментарий и возвращает действие.
    
    Возвращает:
    - ('delete', None) - удалить
    - ('keep', wsdc_id) - оставить только с этим ID
    - ('split', [(name_ru, name_en, wsdc_id), ...]) - разделить на несколько
    - ('ok', None) - оставить без изменений
    """
    if pd.isna(comment) or not comment or str(comment).strip() == '':
        return ('ok', None)
    
    comment = str(comment).strip()
    
    if 'удали из таблицы' in comment.lower():
        return ('delete', None)
    
    if 'все ок' in comment.lower() or 'все оk' in comment.lower():
        return ('ok', None)
    
    if 'оставь только' in comment.lower():
        # Формат: "оставь только [имя] с номером [ID]"
        import re
        match = re.search(r'номером\s+(\d+(?:\.\d+)?)', comment)
        if match:
            wsdc_id = int(float(match.group(1)))
            return ('keep', wsdc_id)
    
    if 'раздели на' in comment.lower() or 'раздели' in comment.lower():
        # Формат: "раздели на [имя1] с номером [ID1] и [имя2] с номером [ID2]"
        import re
        # Ищем все пары "имя с номером ID"
        # Паттерн: имя (может быть на русском или английском) + "с номером" + ID
        # Разделяем по "и" для нескольких танцоров
        parts = re.split(r'\s+и\s+', comment, flags=re.IGNORECASE)
        result = []
        for part in parts:
            # Убираем "раздели на" в начале
            part = re.sub(r'^раздели\s+на\s+', '', part, flags=re.IGNORECASE).strip()
            # Ищем "с номером ID" или "номером ID"
            match = re.search(r'(.+?)\s+с\s+номером\s+(\d+(?:\.\d+)?)', part, re.IGNORECASE)
            if match:
                name_part = match.group(1).strip()
                id_part = match.group(2)
                wsdc_id = int(float(id_part))
                # Определяем, русское это имя или английское
                name_ru = ""
                name_en = ""
                if any(ord(c) > 127 and ord(c) < 2048 for c in name_part):
                    # Кириллица
                    name_ru = name_part
                else:
                    # Латиница
                    name_en = name_part
                result.append((name_ru, name_en, wsdc_id))
        if result:
            return ('split', result)
    
    # Если не распознано, оставляем без изменений
    return ('ok', None)


def apply_comments(csv_file: str, sheet_id: str = GOOGLE_SHEET_ID):
    """
    Применяет комментарии из Google Таблицы к CSV файлу.
    """
    print("=" * 60)
    print("ОБРАБОТКА КОММЕНТАРИЕВ ИЗ GOOGLE ТАБЛИЦЫ")
    print("=" * 60)
    print()
    
    # Читаем исходный CSV
    print("Читаю исходный CSV...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    print()
    
    # Читаем Google Sheet с комментариями
    try:
        comments_df = read_google_sheet_with_comments(sheet_id)
    except Exception as e:
        print(f"Ошибка загрузки Google Sheet: {e}")
        print("Попробую прочитать из локального файла, если он есть...")
        # Пробуем прочитать из локального файла
        local_file = "temp_google_sheet.csv"
        if os.path.exists(local_file):
            comments_df = pd.read_csv(local_file, encoding='utf-8')
        else:
            raise
    
    print(f"Загружено строк с комментариями: {len(comments_df)}")
    
    # Проверяем наличие столбца D (комментарии)
    comment_col = None
    for col in comments_df.columns:
        if 'D' in str(col) or 'комментар' in str(col).lower() or len(comments_df.columns) >= 4:
            # Столбец D обычно 4-й (индекс 3)
            if comments_df.columns.get_loc(col) == 3 or 'комментар' in str(col).lower():
                comment_col = col
                break
    
    if comment_col is None and len(comments_df.columns) >= 4:
        comment_col = comments_df.columns[3]  # Столбец D (индекс 3)
    
    if comment_col is None:
        raise ValueError("Не найден столбец D с комментариями")
    
    print(f"Столбец с комментариями: {comment_col}")
    print()
    
    # Определяем столбец с очками в исходном CSV
    points_col = None
    for col in df.columns:
        if 'points' in col.lower():
            points_col = col
            break
    
    if points_col is None:
        raise ValueError("Не найден столбец с очками")
    
    # Создаём ключ для сопоставления записей
    def create_key(row):
        name_ru = str(row.get('name_ru', '')).strip()
        name_en = str(row.get('name_en', '')).strip()
        wsdc_id = row.get('wsdc_id')
        if pd.notna(wsdc_id) and wsdc_id != 0:
            return f"id_{int(float(wsdc_id))}"
        return f"name_{name_ru or name_en}"
    
    # Создаём словарь комментариев по ключам
    comments_map = {}
    
    # Определяем столбцы по именам или позициям
    name_ru_col = comments_df.columns[0] if len(comments_df.columns) > 0 else None
    name_en_col = comments_df.columns[1] if len(comments_df.columns) > 1 else None
    wsdc_id_col = comments_df.columns[2] if len(comments_df.columns) > 2 else None
    
    print(f"Столбцы: name_ru={name_ru_col}, name_en={name_en_col}, wsdc_id={wsdc_id_col}, comment={comment_col}")
    print()
    
    for _, row in comments_df.iterrows():
        name_ru = str(row[name_ru_col]).strip() if name_ru_col and name_ru_col in row else ''
        name_en = str(row[name_en_col]).strip() if name_en_col and name_en_col in row else ''
        wsdc_id_val = row[wsdc_id_col] if wsdc_id_col and wsdc_id_col in row else None
        comment = str(row[comment_col]).strip() if comment_col and comment_col in row else ''
        
        # Пропускаем заголовки
        if name_ru.lower() in ['name_ru', 'имя'] or name_en.lower() in ['name_en']:
            continue
        
        # Пропускаем пустые строки
        if not name_ru and not name_en:
            continue
        
        # Обрабатываем wsdc_id
        wsdc_id = None
        if pd.notna(wsdc_id_val) and str(wsdc_id_val).strip() != '':
            try:
                wsdc_id = int(float(str(wsdc_id_val).strip()))
            except:
                pass
        
        # Создаём ключ
        key = None
        if wsdc_id:
            key = f"id_{wsdc_id}"
        else:
            key = f"name_{name_ru or name_en}"
        
        if key and comment and comment.lower() not in ['', 'nan', 'none']:
            comments_map[key] = comment
    
    print(f"Найдено комментариев: {len(comments_map)}")
    print()
    
    # Применяем изменения
    print("Применяю изменения...")
    print("-" * 60)
    
    rows_to_delete = []
    rows_to_keep = []
    rows_to_add = []
    
    # Группируем по ключам для обработки
    df['_key'] = df.apply(create_key, axis=1)
    
    for key, group in df.groupby('_key'):
        comment = comments_map.get(key, '')
        if not comment:
            # Нет комментария - оставляем как есть
            rows_to_keep.extend(group.to_dict('records'))
            continue
        
        action, params = parse_comment(comment)
        
        if action == 'delete':
            print(f"  Удаляю: {key} ({len(group)} записей)")
            # Не добавляем в rows_to_keep
            continue
        
        elif action == 'keep':
            wsdc_id = params
            # Оставляем только записи с этим ID
            filtered = group[group['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id]
            if len(filtered) > 0:
                print(f"  Оставляю только ID {wsdc_id} для: {key} ({len(filtered)} записей)")
                rows_to_keep.extend(filtered.to_dict('records'))
            else:
                print(f"  Предупреждение: не найдено записей с ID {wsdc_id} для {key}")
        
        elif action == 'split':
            # Удаляем все старые записи
            print(f"  Разделяю: {key} на {len(params)} танцоров")
            # Добавляем новые записи для каждого ID
            session = requests.Session()
            session.trust_env = False
            
            for name_ru, name_en, wsdc_id in params:
                print(f"    Обрабатываю ID {wsdc_id}: RU='{name_ru}', EN='{name_en}'")
                
                # Сначала проверяем, есть ли уже записи с этим ID в исходном файле
                existing_records = df[df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id]
                
                if len(existing_records) > 0:
                    # Используем существующие записи, обновляя имена
                    print(f"      Найдено {len(existing_records)} существующих записей, обновляю имена")
                    for _, row in existing_records.iterrows():
                        new_row = row.to_dict()
                        # Обновляем имена согласно комментарию
                        # Если в комментарии указано русское имя - используем его (всегда перезаписываем)
                        if name_ru:
                            new_row['name_ru'] = name_ru
                        # Если в комментарии указано английское имя - используем его, иначе оставляем существующее
                        if name_en:
                            new_row['name_en'] = name_en
                        # Если после обновления нет русского имени, но есть английское - копируем
                        if not new_row.get('name_ru') and new_row.get('name_en'):
                            new_row['name_ru'] = new_row['name_en']
                        rows_to_add.append(new_row)
                else:
                    # Если нет существующих записей, получаем данные через API
                    dancer_data = get_dancer_points_via_api(wsdc_id, session)
                    
                    # Определяем финальные имена (приоритет - имена из комментария)
                    found_name_en = dancer_data.get("name", "") if dancer_data else ""
                    final_name_ru = name_ru if name_ru else ""
                    # Для английского: используем из комментария, если есть, иначе из API, иначе пустое
                    if name_en:
                        final_name_en = name_en
                    elif found_name_en:
                        final_name_en = found_name_en
                    else:
                        final_name_en = ""
                    
                    # Если нет русского имени, но есть английское - копируем
                    if not final_name_ru and final_name_en:
                        final_name_ru = final_name_en
                    
                    if dancer_data and dancer_data.get("divisions"):
                        for div in dancer_data["divisions"]:
                            rows_to_add.append({
                                "name_ru": final_name_ru,
                                "name_en": final_name_en,
                                "wsdc_id": wsdc_id,
                                "division": div.get("division", ""),
                                "role": div.get("role", ""),
                                points_col: div.get("points", 0),
                                "as_of_date": group.iloc[0].get('as_of_date', '2026-01-28'),
                                "Novice": "",
                                "Allowed": ""
                            })
                        print(f"      Добавлено {len(dancer_data['divisions'])} записей через API")
                    else:
                        # Если нет дивизионов, создаём запись без данных
                        rows_to_add.append({
                            "name_ru": final_name_ru,
                            "name_en": final_name_en,
                            "wsdc_id": wsdc_id,
                            "division": "",
                            "role": "",
                            points_col: 0,
                            "as_of_date": group.iloc[0].get('as_of_date', '2026-01-28'),
                            "Novice": "",
                            "Allowed": ""
                        })
                        print(f"      Добавлена запись без дивизионов")
                
                time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        
        else:  # 'ok'
            # Оставляем без изменений
            rows_to_keep.extend(group.to_dict('records'))
    
    # Объединяем результаты
    result_df = pd.DataFrame(rows_to_keep)
    if rows_to_add:
        new_df = pd.DataFrame(rows_to_add)
        result_df = pd.concat([result_df, new_df], ignore_index=True)
    
    # Удаляем временный столбец
    if '_key' in result_df.columns:
        result_df = result_df.drop(columns=['_key'])
    
    # Удаляем дубликаты (по wsdc_id + division + role + points)
    print("\nУдаляю дубликаты...")
    before_dedup = len(result_df)
    result_df = result_df.drop_duplicates(subset=['wsdc_id', 'division', 'role', points_col], keep='first')
    after_dedup = len(result_df)
    duplicates_removed = before_dedup - after_dedup
    if duplicates_removed > 0:
        print(f"Удалено дубликатов: {duplicates_removed}")
    
    # Заполняем пустые name_ru копией name_en (если name_en есть, а name_ru пустое)
    print("\nЗаполняю пустые name_ru копией name_en...")
    mask_empty_ru = (result_df['name_ru'].isna()) | (result_df['name_ru'] == '')
    mask_has_en = (result_df['name_en'].notna()) & (result_df['name_en'] != '')
    mask_to_fill = mask_empty_ru & mask_has_en
    result_df.loc[mask_to_fill, 'name_ru'] = result_df.loc[mask_to_fill, 'name_en']
    print(f"Заполнено {mask_to_fill.sum()} записей")
    
    # Пересчитываем столбцы Novice и Allowed
    print("Пересчитываю столбцы Novice и Allowed...")
    result_df['dancer_key'] = result_df['name_en'].fillna(result_df['name_ru'])
    novice_df = result_df[result_df['division'] == 'Novice'].copy()
    max_novice_points = novice_df.groupby('dancer_key')[points_col].max().to_dict()
    
    if 'Novice' not in result_df.columns:
        result_df['Novice'] = ''
    if 'Allowed' not in result_df.columns:
        result_df['Allowed'] = ''
    
    result_df['Novice'] = ''
    result_df['Allowed'] = ''
    
    for idx, row in result_df.iterrows():
        dancer_key = row['dancer_key']
        novice_points = max_novice_points.get(dancer_key, None)
        
        if novice_points is not None:
            if novice_points < 16:
                result_df.at[idx, 'Novice'] = 'X'
            elif 16 <= novice_points <= 30:
                result_df.at[idx, 'Allowed'] = 'X'
    
    result_df = result_df.drop(columns=['dancer_key'])
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_with_comments_applied.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print()
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Исходных записей: {len(df)}")
    print(f"Результирующих записей: {len(result_df)}")
    print(f"Удалено записей: {len(df) - len(rows_to_keep)}")
    print(f"Добавлено новых записей: {len(rows_to_add)}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python apply_google_sheet_comments.py <csv_file> [sheet_id]")
        print("\nПример:")
        print("  python apply_google_sheet_comments.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized_with_novice_zero.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    sheet_id = sys.argv[2] if len(sys.argv) > 2 else GOOGLE_SHEET_ID
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл не найден: {csv_file}", flush=True)
        sys.exit(1)
    
    try:
        apply_comments(csv_file, sheet_id)
    except Exception as e:
        print(f"\nОшибка: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
