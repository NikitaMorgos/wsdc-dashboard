#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавляет столбцы "Novice" и "Allowed" в CSV файл на основе поинтов в дивизионе Novice.

- Столбец "Novice": отметка для танцоров с Novice < 16 points
- Столбец "Allowed": отметка для танцоров с Novice от 16 до 30 points

Использование:
    python add_novice_columns.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf.csv
"""

import sys
import pandas as pd


def add_novice_columns(csv_file: str):
    """
    Добавляет столбцы Novice и Allowed в CSV файл.
    """
    print("=" * 60)
    print("ДОБАВЛЕНИЕ СТОЛБЦОВ NOVICE И ALLOWED")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print()
    
    # Читаем CSV
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")
    
    # Находим максимальные поинты в Novice для каждого танцора
    # Группируем по name_en (или name_ru, если name_en пусто)
    df['dancer_key'] = df['name_en'].fillna(df['name_ru'])
    
    # Фильтруем только записи с Novice
    novice_df = df[df['division'] == 'Novice'].copy()
    
    # Находим максимальные поинты в Novice для каждого танцора
    max_novice_points = novice_df.groupby('dancer_key')['points'].max().to_dict()
    
    print(f"Танцоров с Novice: {len(max_novice_points)}")
    print()
    
    # Добавляем столбцы
    df['Novice'] = ''
    df['Allowed'] = ''
    
    # Для каждой строки проверяем поинты танцора в Novice
    for idx, row in df.iterrows():
        dancer_key = row['dancer_key']
        novice_points = max_novice_points.get(dancer_key, None)
        
        if novice_points is not None:
            if novice_points < 16:
                df.at[idx, 'Novice'] = 'X'
            elif 16 <= novice_points <= 30:
                df.at[idx, 'Allowed'] = 'X'
    
    # Удаляем временный столбец
    df = df.drop(columns=['dancer_key'])
    
    # Сохраняем обновлённый файл
    output_file = csv_file.replace('.csv', '_with_novice.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # Статистика
    novice_count = (df['Novice'] == 'X').sum()
    allowed_count = (df['Allowed'] == 'X').sum()
    unique_novice = df[df['Novice'] == 'X']['name_en'].nunique()
    unique_allowed = df[df['Allowed'] == 'X']['name_en'].nunique()
    
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(df)}")
    print(f"Записей с отметкой 'Novice' (< 16 points): {novice_count}")
    print(f"Уникальных танцоров в 'Novice': {unique_novice}")
    print(f"Записей с отметкой 'Allowed' (16-30 points): {allowed_count}")
    print(f"Уникальных танцоров в 'Allowed': {unique_allowed}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python add_novice_columns.py <csv_file>")
        print("Пример: python add_novice_columns.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    add_novice_columns(csv_file)
