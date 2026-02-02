#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загружает последний актуальный CSV (со всеми комментариями и полями) в Google Таблицу.

Использование:
    python upload_latest_to_sheets.py
    python upload_latest_to_sheets.py <csv_file>   # загрузить конкретный файл
    python upload_latest_to_sheets.py <csv_file> <sheet_id> [sheet_name]
"""

import os
import sys
import glob

# Папка со скриптами и CSV
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Последний файл со всеми комментариями и полями (events + months)
LATEST_CSV = "wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized_with_novice_zero_with_comments_applied_fixed_names_fixed_names_ids_cleaned_fixed_22030_with_events_months_fixed.csv"

# ID таблицы по умолчанию (из upload_to_google_sheets.py)
DEFAULT_SHEET_ID = "1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE"
DEFAULT_SHEET_NAME = "WSDC Points"


def find_latest_csv():
    """Ищет последний CSV: сначала короткое имя wsdc_latest.csv, иначе по маске."""
    short_path = os.path.join(SCRIPT_DIR, "wsdc_latest.csv")
    if os.path.exists(short_path):
        return short_path
    pattern = os.path.join(SCRIPT_DIR, "*with_events_months_fixed.csv")
    files = glob.glob(pattern)
    if not files:
        path = os.path.join(SCRIPT_DIR, LATEST_CSV)
        if os.path.exists(path):
            return path
        return None
    return max(files, key=os.path.getmtime)


def main():
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        csv_file = sys.argv[1]
        if not os.path.isabs(csv_file):
            csv_file = os.path.join(SCRIPT_DIR, csv_file)
    else:
        csv_file = find_latest_csv()
        if not csv_file:
            print("Не найден CSV файл (ожидается *with_events_months_fixed.csv или", LATEST_CSV[:50] + "...)")
            sys.exit(1)
        print("Используется файл:", os.path.basename(csv_file))

    sheet_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SHEET_ID
    sheet_name = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_SHEET_NAME

    if not os.path.exists(csv_file):
        print("Файл не найден:", csv_file)
        sys.exit(1)

    from upload_to_google_sheets import upload_csv_to_sheet

    ok = upload_csv_to_sheet(
        csv_file,
        sheet_id=sheet_id,
        sheet_name=sheet_name,
        start_cell="A1",
        clear_existing=True,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
