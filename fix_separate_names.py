#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разделяет некорректно связанные имена на отдельных танцоров.

Для указанных имён:
1. Удаляет все записи с неправильными соответствиями
2. Создаёт отдельные записи для каждого имени (без данных, если не найдено в WSDC)

Использование:
    python fix_separate_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice.csv 2026-01-28
"""

import sys
import pandas as pd

# Имена, которые нужно разделить на отдельных танцоров
NAMES_TO_SEPARATE = [
    "Александров Дмитрий",
    "Александров Сергей",
    "Аляпкин Алексей",
    "Арефьев Николай",
]


def separate_names(csv_file: str, as_of_date: str):
    """
    Разделяет некорректно связанные имена.
    """
    print("=" * 60)
    print("РАЗДЕЛЕНИЕ НЕКОРРЕКТНО СВЯЗАННЫХ ИМЁН")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Дата: {as_of_date}")
    print()

    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")

    # Находим и удаляем неправильные записи
    incorrect_mask = df['name_ru'].isin(NAMES_TO_SEPARATE)
    incorrect_count = incorrect_mask.sum()
    
    print(f"Найдено записей для удаления: {incorrect_count}")
    
    # Удаляем неправильные записи
    df_corrected = df[~incorrect_mask].copy()
    print(f"Записей после удаления: {len(df_corrected)}")
    print()

    # Создаём отдельные записи для каждого имени (без данных, так как не найдены в WSDC)
    new_records = []
    
    for name_ru in NAMES_TO_SEPARATE:
        # Транслитерируем имя
        from wsdc_from_google_sheet import ru_to_en
        name_en = ru_to_en(name_ru)
        
        # Создаём запись без данных (не найдено в WSDC)
        new_records.append({
            'name_ru': name_ru,
            'name_en': name_en,
            'wsdc_id': None,
            'division': '',
            'role': '',
            'points': 0,
            'as_of_date': as_of_date,
            'Novice': '',
            'Allowed': ''
        })
        
        print(f"Создана отдельная запись: {name_ru} -> {name_en}")

    # Добавляем новые записи
    new_df = pd.DataFrame(new_records)
    combined = pd.concat([df_corrected, new_df], ignore_index=True)
    
    # Упорядочиваем столбцы
    final_columns = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points', 'as_of_date', 'Novice', 'Allowed']
    combined = combined[[c for c in final_columns if c in combined.columns]]
    
    # Сохраняем
    output_file = csv_file.replace('.csv', '_separated.csv')
    combined.to_csv(output_file, index=False, encoding='utf-8')
    
    print()
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(combined)}")
    print(f"Удалено неправильных записей: {incorrect_count}")
    print(f"Добавлено отдельных записей: {len(new_records)}")
    print("=" * 60)
    print()
    print("Примечание: Эти имена не найдены в WSDC, поэтому созданы записи без данных.")
    print("Если у вас есть правильные английские имена для этих танцоров, можно")
    print("вручную обновить name_en и запустить retry_missing_data.py для поиска данных.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python fix_separate_names.py <csv_file> <as_of_date>")
        print("Пример: python fix_separate_names.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice.csv 2026-01-28")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    
    separate_names(csv_file, as_of_date)
