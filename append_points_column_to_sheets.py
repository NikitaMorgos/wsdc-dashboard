#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавляет новый столбец с поинтами (points_<дата>) в Google Таблицу рядом с points_2026-01-28.
При каждом запуске добавляется новый соседний столбец с текущей датой.

Использование:
    python append_points_column_to_sheets.py
    python append_points_column_to_sheets.py <csv_file>
"""

import os
import sys
import re
from datetime import datetime

import pandas as pd
import gspread

# ID таблицы из ссылки пользователя
SHEET_ID = "1kYXHQ8aJUMKzECWh2h5zofyq5Bch2gcgvx8EHpBV_PA"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_CSV = "wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized_with_novice_zero_with_comments_applied_fixed_names_fixed_names_ids_cleaned_fixed_22030_with_events_months_fixed.csv"


def col_index_to_letter(n: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA, ..."""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def find_credentials():
    for name in ("credentials.json", "credentials.json.json"):
        path = os.path.join(SCRIPT_DIR, name)
        if os.path.exists(path):
            return path
    return os.path.join(SCRIPT_DIR, "credentials.json")


def get_client():
    from upload_to_google_sheets import get_google_sheets_client
    cred_path = find_credentials()
    return get_google_sheets_client(credentials_file=cred_path)


def get_points_column_name(df: pd.DataFrame) -> str:
    """Имя столбца с поинтами в CSV (последний points_*)."""
    points_cols = [c for c in df.columns if c and str(c).strip().lower().startswith("points_")]
    if not points_cols:
        raise ValueError("В CSV нет столбца points_*")
    return points_cols[-1]


def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    if not csv_file:
        short_path = os.path.join(SCRIPT_DIR, "wsdc_latest.csv")
        if os.path.exists(short_path):
            path = short_path
        else:
            path = os.path.join(SCRIPT_DIR, LATEST_CSV)
            if not os.path.exists(path):
                import glob
                files = glob.glob(os.path.join(SCRIPT_DIR, "*with_events_months_fixed.csv"))
                path = max(files, key=os.path.getmtime) if files else None
        if not path or not os.path.exists(path):
            print("Не найден CSV файл. Укажите: python append_points_column_to_sheets.py <csv_file>")
            sys.exit(1)
        csv_file = path
    else:
        if not os.path.isabs(csv_file):
            csv_file = os.path.join(SCRIPT_DIR, csv_file)
        if not os.path.exists(csv_file):
            print("Файл не найден:", csv_file)
            sys.exit(1)

    print("CSV:", os.path.basename(csv_file))
    df = pd.read_csv(csv_file, encoding="utf-8")
    points_col = get_points_column_name(df)
    print("Столбец поинтов в CSV:", points_col)

    # Ключ (wsdc_id, division, role) -> points
    def row_key(r):
        wid = r.get("wsdc_id", "")
        if pd.isna(wid):
            wid = ""
        try:
            wid = int(float(wid))
        except (ValueError, TypeError):
            wid = str(wid).strip()
        return (wid, str(r.get("division", "") or "").strip(), str(r.get("role", "") or "").strip())

    df["_key"] = df.apply(row_key, axis=1)
    points_by_key = dict(zip(df["_key"], df[points_col].astype(str).replace("nan", "")))

    today = datetime.now().strftime("%Y-%m-%d")
    new_header = f"points_{today}"
    print("Новый столбец:", new_header)

    cred_path = find_credentials()
    if not os.path.exists(cred_path):
        print("Файл credentials не найден. Ожидается credentials.json или credentials.json.json в папке скрипта.")
        sys.exit(1)

    from upload_to_google_sheets import get_google_sheets_client
    client = get_google_sheets_client(credentials_file=cred_path)
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = spreadsheet.sheet1

    # Все данные листа
    all_data = worksheet.get_all_values()
    if not all_data:
        print("Таблица пуста.")
        sys.exit(1)

    headers = [str(h).strip() for h in all_data[0]]
    # Индекс последнего столбца points_*
    points_col_idx = None
    for i, h in enumerate(headers):
        if h and re.match(r"points_\d{4}-\d{2}-\d{2}", h, re.I):
            points_col_idx = i
    if points_col_idx is None:
        for i, h in enumerate(headers):
            if h and "points" in h.lower():
                points_col_idx = i
    if points_col_idx is None:
        points_col_idx = len(headers) - 1

    new_col_idx = points_col_idx + 1  # следующий столбец (0-based)
    new_col_letter = col_index_to_letter(new_col_idx + 1)  # 1-based для A1

    # Индексы для ключа в листе
    idx_wsdc = next((i for i, h in enumerate(headers) if str(h).strip().lower() == "wsdc_id"), None)
    idx_division = next((i for i, h in enumerate(headers) if str(h).strip().lower() == "division"), None)
    idx_role = next((i for i, h in enumerate(headers) if str(h).strip().lower() == "role"), None)
    if idx_wsdc is None or idx_division is None or idx_role is None:
        print("В таблице не найдены столбцы wsdc_id, division, role. Буду подставлять по порядку строк.")
        match_by_order = True
    else:
        match_by_order = False

    # Значения для нового столбца: заголовок + по одной ячейке на строку
    new_values = [new_header]
    for row in all_data[1:]:
        while len(row) <= max(idx_wsdc or 0, idx_division or 0, idx_role or 0):
            row.append("")
        if match_by_order:
            # Совпадение по номеру строки (индекс в CSV = индекс в листе - 1)
            idx = len(new_values) - 1
            if idx < len(df):
                val = df.iloc[idx][points_col]
                new_values.append("" if pd.isna(val) else str(int(val)) if isinstance(val, float) and val == int(val) else str(val))
            else:
                new_values.append("")
        else:
            try:
                wid = row[idx_wsdc]
                if isinstance(wid, str) and wid.isdigit():
                    wid = int(wid)
                else:
                    try:
                        wid = int(float(wid))
                    except (ValueError, TypeError):
                        wid = str(wid).strip()
                key = (wid, str(row[idx_division] if idx_division < len(row) else "").strip(), str(row[idx_role] if idx_role < len(row) else "").strip())
                val = points_by_key.get(key, "")
                new_values.append("" if (val is None or (isinstance(val, float) and pd.isna(val))) else str(int(float(val))) if isinstance(val, (int, float)) and float(val) == int(float(val)) else str(val))
            except Exception:
                new_values.append("")
    # Запись одного столбца
    range_str = f"{new_col_letter}1:{new_col_letter}{len(new_values)}"
    cell_list = [[v] for v in new_values]
    worksheet.update(values=cell_list, range_name=range_str, value_input_option="USER_ENTERED")
    print("Готово. Добавлен столбец", new_header, "в диапазон", range_str)
    print("Таблица:", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()
