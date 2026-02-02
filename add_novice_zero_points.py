#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавляет записи Novice с 0 очками для танцоров, у которых есть Newcomer, но нет Novice.

Использование:
    python add_novice_zero_points.py <csv_file>
"""

import sys
import pandas as pd
import os
from datetime import datetime


def add_novice_zero_points(csv_file: str):
    """
    Добавляет записи Novice с 0 очками для танцоров с Newcomer, но без Novice.
    """
    print("=" * 60)
    print("ДОБАВЛЕНИЕ NOVICE С 0 ОЧКАМИ")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print()
    
    # Читаем CSV
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Всего записей: {len(df)}")
    
    # Определяем столбец с очками
    points_col = None
    for col in df.columns:
        if 'points' in col.lower():
            points_col = col
            break
    
    if points_col is None:
        raise ValueError("Не найден столбец с очками (points)")
    
    print(f"Столбец с очками: {points_col}")
    
    # Преобразуем очки в числовой формат
    df[points_col] = pd.to_numeric(df[points_col], errors='coerce').fillna(0)
    
    # Находим всех танцоров с Newcomer
    newcomer_df = df[df['division'] == 'Newcomer'].copy()
    print(f"Найдено записей Newcomer: {len(newcomer_df)}")
    
    # Находим всех танцоров с Novice
    novice_df = df[df['division'] == 'Novice'].copy()
    print(f"Найдено записей Novice: {len(novice_df)}")
    
    # Создаём ключ для идентификации танцора (wsdc_id или name_en)
    def create_dancer_key(row):
        if pd.notna(row.get('wsdc_id')) and row.get('wsdc_id') != 0:
            return f"id_{int(float(row['wsdc_id']))}"
        else:
            name_en = str(row.get('name_en', '')).strip()
            name_ru = str(row.get('name_ru', '')).strip()
            return f"name_{name_en or name_ru}"
    
    newcomer_df['dancer_key'] = newcomer_df.apply(create_dancer_key, axis=1)
    novice_df['dancer_key'] = novice_df.apply(create_dancer_key, axis=1)
    
    # Находим уникальных танцоров с Newcomer
    newcomer_dancers = newcomer_df['dancer_key'].unique()
    novice_dancers = set(novice_df['dancer_key'].unique())
    
    print(f"Уникальных танцоров с Newcomer: {len(newcomer_dancers)}")
    print(f"Уникальных танцоров с Novice: {len(novice_dancers)}")
    
    # Находим танцоров с Newcomer, но без Novice
    dancers_to_add = [d for d in newcomer_dancers if d not in novice_dancers]
    print(f"Танцоров с Newcomer, но без Novice: {len(dancers_to_add)}")
    print()
    
    # Создаём новые записи
    new_rows = []
    
    print("Создаю записи Novice с 0 очками...")
    for dancer_key in dancers_to_add:
        # Берём все записи Newcomer для этого танцора
        dancer_newcomer = newcomer_df[newcomer_df['dancer_key'] == dancer_key]
        
        # Для каждой роли (Leader/Follower) создаём запись Novice с 0 очками
        for _, row in dancer_newcomer.iterrows():
            new_row = row.copy()
            new_row['division'] = 'Novice'
            new_row[points_col] = 0
            new_row['dancer_key'] = None  # Удаляем временный ключ
            new_rows.append(new_row)
    
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        # Удаляем временный ключ из новых записей
        if 'dancer_key' in new_df.columns:
            new_df = new_df.drop(columns=['dancer_key'])
        
        # Удаляем временный ключ из исходного датафрейма
        if 'dancer_key' in df.columns:
            df = df.drop(columns=['dancer_key'])
        
        # Объединяем
        result_df = pd.concat([df, new_df], ignore_index=True)
        
        print(f"Добавлено новых записей: {len(new_df)}")
        
        # Показываем примеры
        print("\nПримеры добавленных записей:")
        for i, (_, row) in enumerate(new_df.head(5).iterrows(), 1):
            name = row.get('name_ru') or row.get('name_en', 'N/A')
            role = row.get('role', 'N/A')
            print(f"  {i}. {name} - {role} - Novice - 0 очков")
        
        if len(new_df) > 5:
            print(f"  ... и еще {len(new_df) - 5} записей")
    else:
        result_df = df
        print("Новых записей не требуется - у всех танцоров с Newcomer уже есть Novice")
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_with_novice_zero.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print()
    print("=" * 60)
    print(f"Готово! Результат сохранён: {output_file}")
    print(f"Всего записей: {len(result_df)}")
    print(f"Добавлено записей: {len(new_rows)}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python add_novice_zero_points.py <csv_file>")
        print("\nПример:")
        print("  python add_novice_zero_points.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл не найден: {csv_file}", flush=True)
        sys.exit(1)
    
    try:
        add_novice_zero_points(csv_file)
    except Exception as e:
        print(f"\nОшибка: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
