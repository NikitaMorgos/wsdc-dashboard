#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная обработка данных:
1. Заполняет пустые name_ru копией name_en
2. Переименовывает столбец points в points_<дата>
"""

import sys
import pandas as pd
from datetime import datetime

def finalize_data(csv_file: str, as_of_date: str):
    """
    Финальная обработка данных.
    """
    print("=" * 60)
    print("ФИНАЛЬНАЯ ОБРАБОТКА ДАННЫХ")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Дата: {as_of_date}")
    print()

    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")
    print()

    # 1. Заполняем пустые name_ru копией name_en
    print("1. Заполняю пустые name_ru копией name_en:")
    print("-" * 60)
    
    mask_empty_ru = (df['name_ru'].isna()) | (df['name_ru'] == '')
    mask_has_en = (df['name_en'].notna()) & (df['name_en'] != '')
    
    mask_to_fill = mask_empty_ru & mask_has_en
    count_to_fill = mask_to_fill.sum()
    
    df.loc[mask_to_fill, 'name_ru'] = df.loc[mask_to_fill, 'name_en']
    
    print(f"Заполнено записей: {count_to_fill}")
    print()

    # 2. Переименовываем столбец points в points_<дата>
    print("2. Переименовываю столбец points:")
    print("-" * 60)
    
    new_points_column = f"points_{as_of_date}"
    df = df.rename(columns={'points': new_points_column})
    
    print(f"Столбец 'points' переименован в '{new_points_column}'")
    print()

    # Упорядочиваем столбцы
    # Порядок: name_ru, name_en, wsdc_id, division, role, points_<дата>, as_of_date, Novice, Allowed
    columns_order = ['name_ru', 'name_en', 'wsdc_id', 'division', 'role', new_points_column, 'as_of_date', 'Novice', 'Allowed']
    df = df[[c for c in columns_order if c in df.columns]]
    
    # Сохраняем
    output_file = csv_file.replace('.csv', '_finalized.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(df)}")
    print(f"Заполнено пустых name_ru: {count_to_fill}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python finalize_data.py <csv_file> <as_of_date>")
        print("Пример: python finalize_data.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed.csv 2026-01-28")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    as_of_date = sys.argv[2]
    
    finalize_data(csv_file, as_of_date)
