#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощённый скрипт для автоматической загрузки данных в Google Таблицу.
Использует настройки из comprehensive_fix.py или finalize_data.py.
"""

import sys
import os
import pandas as pd

# Пытаемся импортировать upload_to_google_sheets
try:
    from upload_to_google_sheets import upload_csv_to_sheet, DEFAULT_SHEET_ID
except ImportError:
    print("Ошибка: не найден модуль upload_to_google_sheets")
    print("Убедитесь, что файл upload_to_google_sheets.py находится в той же папке")
    sys.exit(1)


def auto_upload(csv_file: str, sheet_id: str = None, sheet_name: str = "WSDC Points"):
    """
    Автоматически загружает CSV в Google Таблицу.
    
    Args:
        csv_file: Путь к CSV файлу
        sheet_id: ID Google Таблицы (если None, используется DEFAULT_SHEET_ID)
        sheet_name: Название листа
    """
    if not os.path.exists(csv_file):
        print(f"❌ Файл не найден: {csv_file}")
        return False
    
    sheet_id = sheet_id or DEFAULT_SHEET_ID
    
    print("\n" + "=" * 60)
    print("АВТОМАТИЧЕСКАЯ ЗАГРУЗКА В GOOGLE ТАБЛИЦУ")
    print("=" * 60)
    
    return upload_csv_to_sheet(
        csv_file=csv_file,
        sheet_id=sheet_id,
        sheet_name=sheet_name,
        start_cell="A1",
        clear_existing=True  # Очищаем старые данные перед загрузкой новых
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python auto_upload_to_sheets.py <csv_file> [sheet_id] [sheet_name]")
        print()
        print("Пример:")
        print("  python auto_upload_to_sheets.py wsdc_points_finalized.csv")
        print("  python auto_upload_to_sheets.py wsdc_points_finalized.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE 'WSDC Points'")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    sheet_id = sys.argv[2] if len(sys.argv) > 2 else None
    sheet_name = sys.argv[3] if len(sys.argv) > 3 else "WSDC Points"
    
    success = auto_upload(csv_file, sheet_id, sheet_name)
    sys.exit(0 if success else 1)
