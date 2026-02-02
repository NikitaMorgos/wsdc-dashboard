#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Комплексное исправление данных:
1. Добавляет данные для указанных танцоров по ID
2. Расклеивает неправильные пары
3. Удаляет записи без данных и указанные пары
4. Проверяет соответствие русских и английских имен
5. Склеивает дубли по ID
"""

import sys
import time
import random
import pandas as pd
import requests
from typing import Dict, List, Any, Tuple

from wsdc_from_google_sheet import (
    get_dancer_points_via_api,
    search_wsdc_dancer,
    ru_to_en,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)

# Танцоры для добавления данных по ID
DANCERS_TO_ADD = [
    ("Бурш Дмитрий", "Dmitry Bursh", 26198),
    ("Бугаев Сергей", "Sergey Bugaev", 22564),
    ("Аляпкин Алексей", "Alexey Alyapkin", 25407),
    ("Александров Сергей", "Sergey Aleksandrov", 9205),
    ("", "Taisiya Afanasyeva", 26213),
    ("", "Dariya Bisovko", 25012),
    ("", "Varya Khavtorina", 26057),
    ("Пронина Гульнара", "Gulnara Pronina", 21956),
]

# Неправильные пары для расклейки: (name_en, неправильный wsdc_id) -> нужно удалить и найти правильные
WRONG_PAIRS_TO_FIX = [
    ("Denis Gorbanyov", 20787, "Denis Balakin", 16081),
    ("Alena Dobromyslova", None, "Alena Abrazhenina", 22980),
    ("Marina Suslova", None, "Marina Cameron", 21442),
    ("Svetlana Aleksandrova", None, "Arina Aleksandrova", 26220),
    ("Anna Ubaseva", None, "Anna Arispe", None),
    ("Svetlana Budzinskaya", None, "Svetlana Alexandrova", None),
    ("Valeriya Efanova", None, "Valeriya Glukhova", 15252),
    ("Yana Grebennikova", None, "Yana Buramenskaya", 24701),
    ("Alina Yafasova", None, "Alina Abrosimovia", 12119),
    ("Alyona Kostochkina", None, "Alyona Orekhova", 9890),
    ("Aleksei Iakshin", None, "Aleksei Aliapkin", 25407),
    ("Denis Yudayev", None, "Denis Balakin", 16081),
    ("Sergey Dyachenko", None, "Sergey Agranovskly", 12327),
    ("Yuri Lubomirski", None, "Yuri Baranow", 12439),
    ("Anastasiya Kobyakova", None, "Anastasiya Adamova", 22571),
    ("Maksim Dashko", None, "Maksim Anisimov", 14285),
    ("Ilya Chulkov", None, "Ilya Duplin", 20711),
    ("Alexander Isaev", None, "Alexander Annenkov", 19235),
    ("Renat Makhiuddin", None, "Renata Kiss", 19709),
    ("Tatyana Boykova", None, "Tatyana Bills", 8712),
    ("Гатауллина Лариса", None, "Larisa Bratkovskaya", 16036),
    ("Polina Ivanova", None, "Alena Ivanova", 23440),
    ("Осминина Анастасия", None, "Anastasia Andreeva", 16632),
    ("Охапкина Вера", None, "Vera Brovkina", 24699),
    ("Семенова Юлия", None, "Yulia Fedorova", 15923),
    ("Солонкина Мария", None, "Maria Afanador", 19250),
    ("Сучкова Александра", None, "Alexandra Besnard", 20890),
]

# Пары для удаления
PAIRS_TO_DELETE = [
    ("Lara Yakovleva", "Lara Anderson"),
    ("Kristina Istomina", "Kristina Aleksofyte"),
    ("Yuliya Guryanova", "Yuliya Binda"),
    ("Anna Volodina", "Anna Arispe"),
]


def get_dancer_by_id(wsdc_id: int, session: requests.Session) -> dict:
    """Получает данные танцора по WSDC ID."""
    return get_dancer_points_via_api(wsdc_id, session)


def comprehensive_fix(csv_file: str, as_of_date: str):
    """
    Комплексное исправление данных.
    """
    print("=" * 60)
    print("КОМПЛЕКСНОЕ ИСПРАВЛЕНИЕ ДАННЫХ")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Дата: {as_of_date}")
    print()

    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")
    print()

    # Создаём сессию
    session = requests.Session()
    session.trust_env = False

    all_new_results = []

    # 1. Добавляем данные для указанных танцоров
    print("1. Добавляю данные для указанных танцоров:")
    print("-" * 60)
    for name_ru, name_en, wsdc_id in DANCERS_TO_ADD:
        print(f"{name_ru or name_en} (ID: {wsdc_id})...")
        dancer_data = get_dancer_by_id(wsdc_id, session)
        
        if dancer_data.get("name"):
            found_name_en = dancer_data["name"]
            final_name_ru = name_ru if name_ru else ""
            final_name_en = name_en if name_en else found_name_en
            
            print(f"  Найден: {found_name_en}")
            
            if dancer_data.get("divisions"):
                for div in dancer_data["divisions"]:
                    all_new_results.append({
                        "name_ru": final_name_ru,
                        "name_en": final_name_en,
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
                all_new_results.append({
                    "name_ru": final_name_ru,
                    "name_en": final_name_en,
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
            print(f"  Не удалось получить данные для ID {wsdc_id}")
        
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        print()

    # 2. Обрабатываем неправильные пары: удаляем неправильные, ищем правильные данные
    print("2. Обрабатываю неправильные пары:")
    print("-" * 60)
    
    wrong_names_to_remove = set()  # Неправильные имена для удаления
    wrong_ids_to_remove = set()  # Неправильные ID для удаления
    correct_names_to_find = []  # Список правильных имен для поиска
    
    for wrong_name, wrong_id, correct_name, correct_id in WRONG_PAIRS_TO_FIX:
        # Добавляем неправильные имена/ID для удаления
        if wrong_id:
            wrong_ids_to_remove.add(wrong_id)
        if wrong_name:
            # Проверяем, русское ли имя
            if any(ord(c) > 127 for c in wrong_name):
                # Русское имя - добавляем в name_ru для удаления
                wrong_names_to_remove.add(('ru', wrong_name))
            else:
                # Английское имя - добавляем в name_en для удаления
                wrong_names_to_remove.add(('en', wrong_name))
        
        # Если указан неправильный ID для правильного имени, тоже удаляем
        if correct_id and wrong_id and correct_id == wrong_id:
            # Это означает, что правильное имя было связано с неправильным ID
            pass  # Уже добавили в wrong_ids_to_remove
        
        # Добавляем правильное имя для поиска
        if correct_name:
            # Определяем, есть ли русское имя
            name_ru = ""
            name_en = correct_name
            if any(ord(c) > 127 for c in correct_name):  # Проверка на кириллицу
                name_ru = correct_name
                name_en = ru_to_en(name_ru)
            else:
                name_en = correct_name
            
            correct_names_to_find.append((name_ru, name_en, correct_id))
    
    # Удаляем записи с неправильными именами или ID
    mask_to_remove = pd.Series([False] * len(df))
    
    for name_type, name in wrong_names_to_remove:
        if name_type == 'ru':
            mask_to_remove |= (df['name_ru'] == name)
        else:
            mask_to_remove |= (df['name_en'] == name)
    
    # Удаляем записи с неправильными ID
    if wrong_ids_to_remove:
        mask_to_remove |= (df['wsdc_id'].notna() & df['wsdc_id'].isin(wrong_ids_to_remove))
    
    removed_count = mask_to_remove.sum()
    print(f"Удалено записей с неправильными парами: {removed_count}")
    df = df[~mask_to_remove].copy()
    
    # Ищем правильные данные для правильных имен
    print("Ищу правильные данные для правильных имен:")
    for name_ru, name_en, correct_id in correct_names_to_find:
        print(f"  {name_ru or name_en}...")
        
        if correct_id:
            # Используем указанный ID
            dancer_data = get_dancer_by_id(correct_id, session)
            found_name = dancer_data.get("name", name_en)
            found_id = correct_id
        else:
            # Ищем по имени
            search_results = search_wsdc_dancer(name_en, session)
            if search_results:
                # Берем первый результат
                first_result = search_results[0]
                found_id = first_result.get("wsdc_id")
                if found_id:
                    dancer_data = get_dancer_by_id(found_id, session)
                    found_name = dancer_data.get("name", name_en)
                else:
                    dancer_data = {"name": name_en, "divisions": []}
                    found_name = name_en
                    found_id = None
            else:
                dancer_data = {"name": name_en, "divisions": []}
                found_name = name_en
                found_id = None
        
        if dancer_data.get("divisions"):
            for div in dancer_data["divisions"]:
                all_new_results.append({
                    "name_ru": name_ru,
                    "name_en": found_name,
                    "wsdc_id": found_id if found_id else None,
                    "division": div.get("division", ""),
                    "role": div.get("role", ""),
                    "points": div.get("points", 0),
                    "as_of_date": as_of_date,
                    "Novice": "",
                    "Allowed": ""
                })
            print(f"    Найдено: {found_name} (ID: {found_id}), добавлено записей: {len(dancer_data['divisions'])}")
        else:
            all_new_results.append({
                "name_ru": name_ru,
                "name_en": found_name,
                "wsdc_id": found_id if found_id else None,
                "division": "",
                "role": "",
                "points": 0,
                "as_of_date": as_of_date,
                "Novice": "",
                "Allowed": ""
            })
            print(f"    Найдено: {found_name} (ID: {found_id}), но нет данных")
        
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
    
    print()

    # 3. Удаляем указанные пары
    print("3. Удаляю указанные пары для удаления:")
    print("-" * 60)
    
    delete_names = set()
    for name_en1, name_en2 in PAIRS_TO_DELETE:
        delete_names.add(name_en1)
        delete_names.add(name_en2)
    
    mask_delete = df['name_en'].isin(delete_names)
    delete_count = mask_delete.sum()
    print(f"Удалено записей: {delete_count}")
    df = df[~mask_delete].copy()
    print()

    # 4. Удаляем записи без данных (wsdc_id пустой или 0, division пустой)
    print("4. Удаляю записи без данных:")
    print("-" * 60)
    
    mask_no_data = (
        (df['wsdc_id'].isna()) |
        (df['wsdc_id'] == 0) |
        (df['wsdc_id'] == '') |
        ((df['division'].isna()) | (df['division'] == ''))
    )
    
    no_data_count = mask_no_data.sum()
    print(f"Удалено записей без данных: {no_data_count}")
    df = df[~mask_no_data].copy()
    print()

    # 5. Проверяем соответствие русских и английских имен
    print("5. Проверяю соответствие русских и английских имен:")
    print("-" * 60)
    
    # Группируем по wsdc_id и проверяем, что для каждого ID есть согласованные имена
    id_to_names = {}
    for idx, row in df.iterrows():
        wsdc_id = row.get('wsdc_id')
        if pd.notna(wsdc_id) and wsdc_id != 0:
            wsdc_id = int(float(wsdc_id))
            name_ru = str(row.get('name_ru', '')).strip()
            name_en = str(row.get('name_en', '')).strip()
            
            if wsdc_id not in id_to_names:
                id_to_names[wsdc_id] = {'name_ru': set(), 'name_en': set()}
            
            if name_ru:
                id_to_names[wsdc_id]['name_ru'].add(name_ru)
            if name_en:
                id_to_names[wsdc_id]['name_en'].add(name_en)
    
    # Проверяем, что для каждого ID есть только один вариант имени
    inconsistencies = []
    for wsdc_id, names in id_to_names.items():
        if len(names['name_ru']) > 1 or len(names['name_en']) > 1:
            inconsistencies.append((wsdc_id, names))
    
    if inconsistencies:
        print(f"Найдено {len(inconsistencies)} ID с несоответствиями имен")
        for wsdc_id, names in inconsistencies[:5]:  # Показываем первые 5
            print(f"  ID {wsdc_id}: RU={names['name_ru']}, EN={names['name_en']}")
        
        # Исправляем несоответствия: для каждого ID выбираем наиболее часто встречающееся имя
        print("Исправляю несоответствия...")
        for wsdc_id, names in inconsistencies:
            # Подсчитываем частоту каждого имени в данных
            name_ru_counts = {}
            name_en_counts = {}
            
            for idx, row in df.iterrows():
                row_id = row.get('wsdc_id')
                if pd.notna(row_id) and row_id != 0:
                    row_id = int(float(row_id))
                    if row_id == wsdc_id:
                        name_ru = str(row.get('name_ru', '')).strip()
                        name_en = str(row.get('name_en', '')).strip()
                        if name_ru:
                            name_ru_counts[name_ru] = name_ru_counts.get(name_ru, 0) + 1
                        if name_en:
                            name_en_counts[name_en] = name_en_counts.get(name_en, 0) + 1
            
            # Выбираем наиболее часто встречающееся имя
            correct_name_ru = max(name_ru_counts.items(), key=lambda x: x[1])[0] if name_ru_counts else ""
            correct_name_en = max(name_en_counts.items(), key=lambda x: x[1])[0] if name_en_counts else ""
            
            # Обновляем все записи с этим ID
            mask_id = (df['wsdc_id'].notna()) & (df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id)
            if correct_name_ru:
                df.loc[mask_id, 'name_ru'] = correct_name_ru
            if correct_name_en:
                df.loc[mask_id, 'name_en'] = correct_name_en
            
            print(f"  ID {wsdc_id}: исправлено на RU='{correct_name_ru}', EN='{correct_name_en}'")
    else:
        print("Несоответствий не найдено")
    print()

    # 6. Склеиваем дубли по ID
    print("6. Склеиваю дубли по ID:")
    print("-" * 60)
    
    # Группируем по wsdc_id
    grouped = df.groupby(df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None))
    
    # Для каждого ID объединяем уникальные комбинации division+role+points
    deduplicated_rows = []
    seen_combinations = {}
    
    for wsdc_id, group in grouped:
        if wsdc_id is None:
            # Записи без ID оставляем как есть, но тоже дедуплицируем
            for _, row in group.iterrows():
                combo = (row.get('name_ru', ''), row.get('name_en', ''), row.get('division', ''), row.get('role', ''), row.get('points', 0))
                if combo not in seen_combinations:
                    seen_combinations[combo] = True
                    deduplicated_rows.append(row.to_dict())
            continue
        
        # Группируем по division+role+points и выбираем лучшую запись (с name_ru, если есть)
        id_grouped = group.groupby(['division', 'role', 'points'])
        for (div, role, points), sub_group in id_grouped:
            combo = (wsdc_id, div, role, points)
            
            if combo not in seen_combinations:
                seen_combinations[combo] = True
                # Выбираем запись с name_ru, если есть, иначе первую
                row_with_ru = sub_group[sub_group['name_ru'].notna() & (sub_group['name_ru'] != '')]
                if len(row_with_ru) > 0:
                    best_row = row_with_ru.iloc[0]
                else:
                    best_row = sub_group.iloc[0]
                deduplicated_rows.append(best_row.to_dict())
    
    df_dedup = pd.DataFrame(deduplicated_rows)
    
    duplicates_removed = len(df) - len(df_dedup)
    print(f"Удалено дублей: {duplicates_removed}")
    print()

    # Объединяем с новыми данными
    if all_new_results:
        new_df = pd.DataFrame(all_new_results)
        columns_order = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date', 'Novice', 'Allowed']
        new_df = new_df[[c for c in columns_order if c in new_df.columns]]
        
        combined = pd.concat([df_dedup, new_df], ignore_index=True)
    else:
        combined = df_dedup
    
    # Финальная дедупликация: удаляем полные дубли (ID+division+role+points)
    print("8. Финальная дедупликация полных дублей...")
    print("-" * 60)
    
    before_count = len(combined)
    
    # Для записей с ID: группируем по ID+division+role+points, оставляем запись с name_ru, если есть
    combined_with_id = combined[combined['wsdc_id'].notna()].copy()
    combined_without_id = combined[combined['wsdc_id'].isna()].copy()
    
    if len(combined_with_id) > 0:
        combined_with_id['wsdc_id'] = combined_with_id['wsdc_id'].astype(int)
        
        # Группируем и выбираем лучшую запись
        deduped_with_id = []
        for (wsdc_id, div, role, points), group in combined_with_id.groupby(['wsdc_id', 'division', 'role', 'points']):
            # Выбираем запись с name_ru, если есть
            row_with_ru = group[group['name_ru'].notna() & (group['name_ru'] != '')]
            if len(row_with_ru) > 0:
                best_row = row_with_ru.iloc[0]
            else:
                best_row = group.iloc[0]
            deduped_with_id.append(best_row.to_dict())
        
        combined_with_id = pd.DataFrame(deduped_with_id)
    
    # Для записей без ID: дедуплицируем по name_ru+name_en+division+role+points
    if len(combined_without_id) > 0:
        deduped_without_id = []
        seen = set()
        for _, row in combined_without_id.iterrows():
            key = (row.get('name_ru', ''), row.get('name_en', ''), row.get('division', ''), row.get('role', ''), row.get('points', 0))
            if key not in seen:
                seen.add(key)
                deduped_without_id.append(row.to_dict())
        combined_without_id = pd.DataFrame(deduped_without_id)
    
    # Объединяем обратно
    if len(combined_with_id) > 0 and len(combined_without_id) > 0:
        combined = pd.concat([combined_with_id, combined_without_id], ignore_index=True)
    elif len(combined_with_id) > 0:
        combined = combined_with_id
    elif len(combined_without_id) > 0:
        combined = combined_without_id
    
    after_count = len(combined)
    final_duplicates_removed = before_count - after_count
    print(f"Удалено полных дублей: {final_duplicates_removed}")
    print()

    # Пересчитываем столбцы Novice и Allowed
    print("7. Пересчитываю столбцы Novice и Allowed...")
    
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
    output_file = csv_file.replace('.csv', '_comprehensive_fixed.csv')
    combined.to_csv(output_file, index=False, encoding='utf-8')
    
    print()
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(combined)}")
    print(f"Удалено записей: {removed_count + delete_count + no_data_count + duplicates_removed}")
    print(f"Добавлено новых записей: {len(all_new_results)}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python comprehensive_fix.py <csv_file> <as_of_date>")
        print("Пример: python comprehensive_fix.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific.csv 2026-01-28")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    
    comprehensive_fix(csv_file, as_of_date)
