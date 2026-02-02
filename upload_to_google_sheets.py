#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для загрузки данных из CSV в Google Таблицу.

Использование:
    python upload_to_google_sheets.py <csv_file> <sheet_id> [sheet_name] [start_cell]

Пример:
    python upload_to_google_sheets.py wsdc_points_finalized.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE "WSDC Points" A1
"""

import sys
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ID вашей Google Таблицы
DEFAULT_SHEET_ID = "1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE"

# Путь к файлу с credentials (Service Account JSON)
CREDENTIALS_FILE = "credentials.json"

# Область доступа для Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_google_sheets_client(credentials_file: str = None):
    """
    Создаёт клиент для работы с Google Sheets API.
    
    Args:
        credentials_file: Путь к JSON файлу с credentials Service Account.
                         Если не указан или файл не найден, пробует credentials.json и credentials.json.json.
    
    Returns:
        gspread.Client объект
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    to_try = [credentials_file] if credentials_file else []
    to_try.extend([os.path.join(script_dir, "credentials.json"), os.path.join(script_dir, "credentials.json.json")])
    for path in to_try:
        if path and os.path.exists(path):
            credentials_file = path
            break
    else:
        raise FileNotFoundError(
            "Файл credentials не найден (ожидается credentials.json или credentials.json.json в папке скрипта).\n"
            "См. инструкцию в GOOGLE_SHEETS_SETUP.md"
        )
    
    creds = Credentials.from_service_account_file(
        credentials_file,
        scopes=SCOPES
    )
    
    client = gspread.authorize(creds)
    return client


def upload_csv_to_sheet(
    csv_file: str,
    sheet_id: str,
    sheet_name: str = None,
    start_cell: str = "A1",
    clear_existing: bool = False
):
    """
    Загружает данные из CSV в Google Таблицу.
    
    Args:
        csv_file: Путь к CSV файлу
        sheet_id: ID Google Таблицы
        sheet_name: Название листа (если None, используется первый лист)
        start_cell: Ячейка, с которой начинать запись (например, "A1")
        clear_existing: Очистить существующие данные перед записью
    """
    print("=" * 60)
    print("ЗАГРУЗКА ДАННЫХ В GOOGLE ТАБЛИЦУ")
    print("=" * 60)
    print(f"CSV файл: {csv_file}")
    print(f"Sheet ID: {sheet_id}")
    print(f"Лист: {sheet_name or 'первый лист'}")
    print(f"Начальная ячейка: {start_cell}")
    print()
    
    # Читаем CSV
    print("Читаю CSV файл...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Загружено {len(df)} строк, {len(df.columns)} столбцов")
    print(f"Столбцы: {', '.join(df.columns)}")
    print()
    
    # Подключаемся к Google Sheets
    print("Подключаюсь к Google Sheets...")
    try:
        client = get_google_sheets_client()
        spreadsheet = client.open_by_key(sheet_id)
        print(f"Открыта таблица: {spreadsheet.title}")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        print("\nПроверьте:")
        print("1. Файл credentials.json существует и корректен")
        print("2. Service Account имеет доступ к таблице")
        print("3. Sheet ID правильный")
        return False
    
    # Выбираем лист
    if sheet_name:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            print(f"Открыт лист: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            print(f"Лист '{sheet_name}' не найден. Создаю новый лист...")
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
            print(f"Создан лист: {sheet_name}")
    else:
        worksheet = spreadsheet.sheet1
        print(f"Используется первый лист: {worksheet.title}")
    
    print()
    
    # Очищаем существующие данные, если нужно
    if clear_existing:
        print("Очищаю существующие данные...")
        worksheet.clear()
        print("Данные очищены")
        print()
    
    # Подготавливаем данные для записи
    print("Подготавливаю данные...")
    
    # Заменяем NaN на пустые строки
    df = df.fillna('')
    
    # Конвертируем DataFrame в список списков
    # Первая строка - заголовки
    values = [df.columns.tolist()]
    # Остальные строки - данные
    values.extend(df.values.tolist())
    
    print(f"Готово к записи: {len(values)} строк (включая заголовок)")
    print()
    
    # Записываем данные
    print(f"Записываю данные начиная с ячейки {start_cell}...")
    try:
        worksheet.update(start_cell, values, value_input_option='USER_ENTERED')
        print("✅ Данные успешно загружены!")
        print()
        print(f"Ссылка на таблицу: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return False
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python upload_to_google_sheets.py <csv_file> [sheet_id] [sheet_name] [start_cell] [--clear]")
        print()
        print("Параметры:")
        print("  csv_file   - Путь к CSV файлу (обязательно)")
        print("  sheet_id   - ID Google Таблицы (опционально, по умолчанию из DEFAULT_SHEET_ID)")
        print("  sheet_name - Название листа (опционально, по умолчанию первый лист)")
        print("  start_cell - Начальная ячейка (опционально, по умолчанию A1)")
        print("  --clear    - Сначала очистить лист (опционально)")
        print()
        print("Примеры:")
        print("  python upload_to_google_sheets.py data.csv")
        print("  python upload_to_google_sheets.py data.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE 'WSDC Points' --clear")
        sys.exit(1)
    
    args = [a for a in sys.argv[1:] if a != "--clear"]
    clear_existing = "--clear" in sys.argv
    
    csv_file = args[0]
    sheet_id = args[1] if len(args) > 1 else DEFAULT_SHEET_ID
    sheet_name = args[2] if len(args) > 2 else None
    start_cell = args[3] if len(args) > 3 else "A1"
    
    if not os.path.exists(csv_file):
        print(f"Файл не найден: {csv_file}")
        sys.exit(1)
    
    ok = upload_csv_to_sheet(csv_file, sheet_id, sheet_name, start_cell, clear_existing=clear_existing)
    sys.exit(0 if ok else 1)
