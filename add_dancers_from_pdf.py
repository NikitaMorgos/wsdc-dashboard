#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Добавляет танцоров из PDF-файла (результаты Moscow Westie Fest и т.п.) в список
и заполняет для них wsdc_id, division, role, points через WSDC API.

Использование:
    python add_dancers_from_pdf.py <pdf_or_txt> <csv> <as_of_date>
    python add_dancers_from_pdf.py moscow_westie_fest_301051061.txt wsdc_points_2026-01-28_updated.csv 2026-01-28
"""

import re
import sys
import time
import random
from pathlib import Path

import pandas as pd
import requests

# Импорт из основного скрипта
from wsdc_from_google_sheet import (
    ru_to_en,
    get_dancer_data,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)


def extract_text_from_file(path: str) -> str:
    """Извлекает текст из PDF или читает .txt."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Поддерживаются только .pdf и .txt")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text_parts = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(text_parts)
    except ImportError:
        raise ImportError(
            "Для чтения PDF установите pypdf: pip install pypdf. "
            "Либо сохраните текст из PDF в .txt и укажите путь к .txt"
        )


def extract_dancer_names_from_text(text: str) -> list[str]:
    """
    Извлекает имена танцоров из текста результатов.
    Формат строк: "438 Natallia Mironova 10 10 10 10 10 50 -> след.тур"
    или "101 Никита Моргось 10 10 10 10 10 50 -> след.тур"
    """
    names = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Пропускаем заголовки и служебные строки
        if line.startswith("#") or "Имя" in line and "Сумма" in line:
            continue
        if "danceConvention" in line or "Обозначения" in line or "Партнер" in line:
            continue
        if "Moscow Westie" in line or "Novice Jack" in line:
            continue
        # Строка данных: начинается с номера (цифры), затем имя, затем оценки
        parts = line.split()
        if len(parts) < 3:
            continue
        if not parts[0].isdigit():
            continue
        # Собираем имя: все слова до первого числа (оценки 10, 4.5, 0 и т.д.)
        name_parts = []
        for i in range(1, len(parts)):
            token = parts[i]
            # Оценка: число или число.число
            if re.match(r"^\d+\.?\d*$", token):
                break
            if token in ("->", "след.тур", "Альт.", "-", "(*)"):
                break
            name_parts.append(token)
        if name_parts:
            name = " ".join(name_parts).strip()
            if len(name) > 2 and not name.isdigit():
                names.append(name)
    return names


def normalize_name_for_wsdc(name: str) -> tuple[str, str]:
    """
    Возвращает (name_ru, name_en) для поиска в WSDC.
    В PDF имена: "Имя Фамилия" (рус) или "FirstName LastName" (лат).
    В CSV храним name_ru как "Фамилия Имя" для единообразия.
    """
    name = name.strip()
    if not name:
        return "", ""
    parts = name.split()
    # Если уже латиница — name_en как есть, name_ru тоже (FirstName LastName)
    if all(ord(c) < 128 for c in name):
        if len(parts) >= 2:
            # Для единообразия с листом: "Фамилия Имя" -> name_ru = "LastName FirstName" нет, в CSV латиница как есть
            return name, name
        return name, name
    # Русское: в PDF "Имя Фамилия", для CSV и ru_to_en нужен "Фамилия Имя"
    if len(parts) >= 2:
        name_ru = f"{parts[1]} {parts[0]}"
        name_en = ru_to_en(name_ru)
        return name_ru, name_en
    return name, ru_to_en(name)


def main():
    if len(sys.argv) < 4:
        print(
            "Использование: python add_dancers_from_pdf.py <pdf_file> <csv_file> <as_of_date>"
        )
        print(
            'Пример: python add_dancers_from_pdf.py moscow_westie_fest_301051061.txt wsdc_points_2026-01-28_updated.csv 2026-01-28'
        )
        sys.exit(1)

    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    as_of_date = sys.argv[3]

    if not Path(pdf_path).exists():
        print(f"Файл не найден: {pdf_path}")
        sys.exit(1)
    if not Path(csv_path).exists():
        print(f"CSV не найден: {csv_path}")
        sys.exit(1)

    print("=" * 60)
    print("ДОБАВЛЕНИЕ ТАНЦОРОВ ИЗ PDF")
    print("=" * 60)
    print(f"PDF: {pdf_path}")
    print(f"CSV: {csv_path}")
    print(f"Дата: {as_of_date}")
    print()

    # Извлекаем имена из PDF или .txt
    print("Извлекаю текст из файла...")
    text = extract_text_from_file(pdf_path)
    raw_names = extract_dancer_names_from_text(text)
    unique_raw = list(dict.fromkeys(raw_names))
    print(f"Найдено уникальных имён в PDF: {len(unique_raw)}")
    print()

    # Загружаем существующий CSV
    df_existing = pd.read_csv(csv_path, encoding="utf-8")
    existing_names_ru = set(df_existing["name_ru"].dropna().astype(str).str.strip())
    existing_names_en = set(df_existing["name_en"].dropna().astype(str).str.strip())

    # Определяем, кого добавлять (по name_en, чтобы не дублировать)
    to_process = []
    for raw in unique_raw:
        name_ru, name_en = normalize_name_for_wsdc(raw)
        if not name_en:
            continue
        if name_en in existing_names_en or name_ru in existing_names_ru:
            continue
        to_process.append((name_ru, name_en))

    print(f"Новых имён для обработки (ещё нет в CSV): {len(to_process)}")
    if not to_process:
        print("Все танцоры из PDF уже есть в списке.")
        sys.exit(0)
    print()

    session = requests.Session()
    session.trust_env = False

    try:
        from playwright.sync_api import sync_playwright
        use_js = True
    except ImportError:
        use_js = False

    all_results = []
    for idx, (name_ru, name_en) in enumerate(to_process, 1):
        print(f"[{idx}/{len(to_process)}] {name_ru} -> {name_en}")
        results = get_dancer_data(name_ru, name_en, session, use_js_render=use_js)
        for r in results:
            r["as_of_date"] = as_of_date
        all_results.extend(results)
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        print()

    if not all_results:
        print("Не удалось получить данные ни по одному танцору.")
        sys.exit(1)

    # Объединяем с существующим CSV
    new_df = pd.DataFrame(all_results)
    columns_order = ["name_ru", "name_en", "wsdc_id", "division", "role", "points", "as_of_date"]
    new_df = new_df[[c for c in columns_order if c in new_df.columns]]

    combined = pd.concat([df_existing, new_df], ignore_index=True)
    combined = combined[[c for c in columns_order if c in combined.columns]]

    out_path = csv_path.replace(".csv", "_with_pdf.csv")
    combined.to_csv(out_path, index=False, encoding="utf-8")

    print("=" * 60)
    print(f"Готово. Результат сохранён: {out_path}")
    print(f"Всего записей: {len(combined)}")
    print(f"Добавлено записей: {len(new_df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
