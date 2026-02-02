#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sys

csv_file = sys.argv[1] if len(sys.argv) > 1 else 'wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed.csv'

df = pd.read_csv(csv_file)
print(f'Всего записей: {len(df)}')

# Проверяем полные дубли (ID+division+role+points)
df_with_id = df[df['wsdc_id'].notna()].copy()
df_with_id['wsdc_id'] = df_with_id['wsdc_id'].astype(int)

# Группируем по ID+division+role+points
grouped = df_with_id.groupby(['wsdc_id', 'division', 'role', 'points']).size()
duplicates = grouped[grouped > 1]

if len(duplicates) > 0:
    print(f'\nНайдено {len(duplicates)} полных дублей (ID+division+role+points):')
    print(duplicates.head(10))
    
    # Показываем примеры
    print('\nПримеры дублей:')
    for (wsdc_id, div, role, points), count in duplicates.head(5).items():
        mask = (df_with_id['wsdc_id'] == wsdc_id) & (df_with_id['division'] == div) & (df_with_id['role'] == role) & (df_with_id['points'] == points)
        examples = df_with_id[mask][['name_ru', 'name_en', 'wsdc_id', 'division', 'role', 'points']].head(2)
        print(f'\nID {wsdc_id}, {div}, {role}, {points} points ({count} записей):')
        print(examples.to_string(index=False))
else:
    print('\nПолных дублей не найдено!')
