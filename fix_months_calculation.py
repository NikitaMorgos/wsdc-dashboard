#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправляет расчет months_to_close_novice для записей Novice.
"""

import sys
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta


def parse_date(date_str):
    """Парсит дату в разных форматах"""
    if not date_str or pd.isna(date_str) or str(date_str).strip() == '':
        return None
    date_str = str(date_str).strip()
    
    # Форматы дат, которые могут быть в данных
    formats = [
        '%B %Y',        # "March 2015", "September 2013"
        '%b %Y',        # "Mar 2015", "Sep 2013"
        '%Y-%m-%d',     # "2015-03-15"
        '%m/%d/%Y',     # "03/15/2015"
        '%d/%m/%Y',     # "15/03/2015"
        '%Y/%m/%d',     # "2015/03/15"
        '%B %d, %Y',    # "March 15, 2015"
        '%b %d, %Y',    # "Mar 15, 2015"
        '%d %B %Y',     # "15 March 2015"
        '%d %b %Y',     # "15 Mar 2015"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None


def calculate_months_diff(date1_str, date2_str):
    """Вычисляет разницу в месяцах между двумя датами"""
    if not date1_str or not date2_str:
        return None
    
    d1 = parse_date(date1_str)
    d2 = parse_date(date2_str)
    
    if not d1 or not d2:
        return None
    
    try:
        # Используем relativedelta для точного расчета
        delta = relativedelta(d2, d1)
        months = delta.years * 12 + delta.months
        
        # Если разница отрицательная, возвращаем None
        if months < 0:
            return None
        
        return months
    except Exception as e:
        print(f"Ошибка расчета месяцев между '{date1_str}' и '{date2_str}': {e}")
        return None


def fix_months_calculation(csv_file: str):
    """
    Заполняет столбец months_to_close_novice для записей Novice.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    # Фильтруем только Novice записи
    novice_df = df[df['division'] == 'Novice'].copy()
    print(f"Записей Novice: {len(novice_df)}")
    
    # Заполняем months_to_close_novice
    updated_count = 0
    for idx in novice_df.index:
        first_date = df.loc[idx, 'first_event_date']
        closed_date = df.loc[idx, 'novice_closed_date']
        current_months = df.loc[idx, 'months_to_close_novice']
        
        # Пропускаем, если уже заполнено
        if pd.notna(current_months) and str(current_months).strip() != '':
            try:
                int(current_months)
                continue  # Уже заполнено
            except:
                pass
        
        # Вычисляем месяцы
        if first_date and closed_date:
            months = calculate_months_diff(first_date, closed_date)
            if months is not None:
                df.loc[idx, 'months_to_close_novice'] = months
                updated_count += 1
                name = df.loc[idx, 'name_ru'] or df.loc[idx, 'name_en']
                print(f"  {name} (ID {df.loc[idx, 'wsdc_id']}): {first_date} -> {closed_date} = {months} месяцев")
    
    print(f"\nОбновлено записей: {updated_count}")
    
    # Сохраняем результат
    output_file = csv_file.replace('.csv', '_months_fixed.csv')
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nРезультат сохранен: {output_file}")
    print(f"Итоговых записей: {len(df)}")
    
    # Статистика
    novice_with_months = df[(df['division'] == 'Novice') & 
                            (df['months_to_close_novice'].notna()) & 
                            (df['months_to_close_novice'] != '')]
    print(f"Novice записей с заполненным months_to_close_novice: {len(novice_with_months)}")
    
    return output_file


def main():
    if len(sys.argv) < 2:
        print("Использование: python fix_months_calculation.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("ИСПРАВЛЕНИЕ РАСЧЕТА МЕСЯЦЕВ ДО ЗАКРЫТИЯ NOVICE")
    print("=" * 60)
    print()
    
    try:
        fix_months_calculation(csv_file)
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
