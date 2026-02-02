#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Удаляет указанные столбцы из CSV файла.
"""

import sys
import pandas as pd


def remove_columns(csv_file: str, columns_to_remove: list):
    """
    Удаляет указанные столбцы из CSV.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    print(f"Исходных столбцов: {list(df.columns)}")
    
    # Удаляем столбцы
    print(f"\nУдаляю столбцы: {', '.join(columns_to_remove)}")
    columns_existing = [col for col in columns_to_remove if col in df.columns]
    columns_not_found = [col for col in columns_to_remove if col not in df.columns]
    
    if columns_not_found:
        print(f"  Предупреждение: столбцы не найдены: {', '.join(columns_not_found)}")
    
    if columns_existing:
        df = df.drop(columns=columns_existing)
        print(f"  Удалено столбцов: {len(columns_existing)}")
    else:
        print("  Нечего удалять")
    
    print(f"Оставшихся столбцов: {list(df.columns)}")
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_cleaned.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nРезультат сохранен: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Использование: python remove_columns.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    columns_to_remove = ['as_of_date', 'Novice', 'Allowed']
    
    print("=" * 60)
    print("УДАЛЕНИЕ СТОЛБЦОВ")
    print("=" * 60)
    print()
    
    try:
        remove_columns(csv_file, columns_to_remove)
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
