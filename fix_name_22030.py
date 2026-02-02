#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Заменяет русское имя на английское для ID 22030.
"""

import sys
import pandas as pd


def fix_name_22030(csv_file: str):
    """
    Заменяет name_ru на name_en для ID 22030.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    wsdc_id = 22030
    new_name_ru = 'Zlata Cheremnykh'
    
    # Находим записи с этим ID
    mask = df['wsdc_id'].apply(lambda x: int(x) if pd.notna(x) and x != 0 else None) == wsdc_id
    matching_rows = df[mask]
    
    if len(matching_rows) == 0:
        print(f"Не найдено записей с ID {wsdc_id}")
        return csv_file
    
    print(f"\nНайдено {len(matching_rows)} записей с ID {wsdc_id}")
    
    # Заменяем name_ru
    updated_count = 0
    for idx in matching_rows.index:
        old_name_ru = df.loc[idx, 'name_ru']
        df.loc[idx, 'name_ru'] = new_name_ru
        updated_count += 1
        print(f"  Запись {idx}: '{old_name_ru}' -> '{new_name_ru}'")
    
    print(f"\nОбновлено {updated_count} записей")
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_fixed_22030.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nРезультат сохранен: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Использование: python fix_name_22030.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ ИМЕНИ ДЛЯ ID 22030")
    print("=" * 60)
    print()
    
    try:
        fix_name_22030(csv_file)
        print()
        print("=" * 60)
        print("ГОТОВО!")
        print("=" * 60)
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
