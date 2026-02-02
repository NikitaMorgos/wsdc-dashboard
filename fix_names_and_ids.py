#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправляет имена и формат ID в CSV файле.

1. Заменяет русское имя на английское для указанных записей
2. Убирает .0 из ID (делает пятизначным числом)
"""

import sys
import pandas as pd


def fix_names_and_ids(csv_file: str):
    """
    Исправляет имена и формат ID.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    # Словарь для замены name_ru на name_en для указанных ID
    name_replacements = {
        16034: 'Anastasia Babushkina',
        16081: 'Denis Balakin',
        16632: 'Anastasia Andreeva',
        18109: 'Artem Bolshakov',
        19237: 'Alexey Artemov',
        20711: 'Ilya Duplin',
        22571: 'Anastasiya Adamova'
    }
    
    # Заменяем name_ru на name_en для указанных ID
    print("\nЗаменяю русские имена на английские...")
    updated_count = 0
    for wsdc_id, name_en in name_replacements.items():
        mask = df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else None) == wsdc_id
        matching_rows = df[mask]
        
        if len(matching_rows) > 0:
            for idx in matching_rows.index:
                old_name_ru = df.loc[idx, 'name_ru']
                df.loc[idx, 'name_ru'] = name_en
                updated_count += 1
                print(f"  ID {wsdc_id}: '{old_name_ru}' -> '{name_en}'")
        else:
            print(f"  Предупреждение: не найдено записей с ID {wsdc_id}")
    
    print(f"Обновлено {updated_count} записей")
    
    # Убираем .0 из ID (преобразуем в целое число)
    print("\nИсправляю формат ID (убираю .0)...")
    df['wsdc_id'] = df['wsdc_id'].apply(lambda x: int(float(x)) if pd.notna(x) and x != 0 else x)
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_fixed_names_ids.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nРезультат сохранен: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Использование: python fix_names_and_ids.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ ИМЕН И ID")
    print("=" * 60)
    print()
    
    try:
        fix_names_and_ids(csv_file)
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
