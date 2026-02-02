#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sys

csv_file = sys.argv[1] if len(sys.argv) > 1 else 'wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed.csv'

df = pd.read_csv(csv_file)
print(f'Всего записей: {len(df)}')
print(f'Записей с ID: {df["wsdc_id"].notna().sum()}')
print(f'Уникальных ID: {df["wsdc_id"].nunique()}')

# Проверяем дубли по ID
duplicates = df[df['wsdc_id'].notna()].groupby('wsdc_id').size()
duplicates = duplicates[duplicates > 1].sort_values(ascending=False)
print(f'\nID с дублями (топ 10):')
print(duplicates.head(10))

# Проверяем, что для каждого ID есть уникальные комбинации division+role
print('\nПроверка уникальности division+role для каждого ID:')
for wsdc_id in duplicates.head(5).index:
    group = df[df['wsdc_id'] == wsdc_id]
    combos = group.groupby(['division', 'role']).size()
    if len(combos) < len(group):
        print(f'  ID {wsdc_id}: {len(group)} записей, {len(combos)} уникальных комбинаций division+role')
