#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания инструкции по вставке данных в Google Sheets из существующего CSV файла.

Использование:
    python create_gs_instructions.py wsdc_points_2026-01-28.csv
"""

import sys
import pandas as pd
import time

# ID Google Sheets (из основного скрипта)
GOOGLE_SHEET_ID = "1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE"


def create_google_sheets_instructions(csv_file: str):
    """
    Создаёт инструкцию и форматированные данные для вставки в Google Sheets.
    
    Args:
        csv_file: Путь к CSV файлу
    """
    # Читаем CSV файл
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except Exception as e:
        print(f"Ошибка чтения CSV файла: {e}", flush=True)
        sys.exit(1)
    
    # Извлекаем дату из имени файла
    import re
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', csv_file)
    as_of_date = date_match.group(1) if date_match else time.strftime('%Y-%m-%d')
    
    print("=" * 60, flush=True)
    print("СОЗДАНИЕ ИНСТРУКЦИИ ДЛЯ GOOGLE SHEETS", flush=True)
    print("=" * 60, flush=True)
    print(f"CSV файл: {csv_file}", flush=True)
    print(f"Записей: {len(df)}", flush=True)
    print(flush=True)
    
    # Форматируем данные для таблицы в HTML
    html_rows = []
    for idx, row in df.iterrows():
        cells = []
        for col in df.columns:
            value = str(row[col]) if pd.notna(row[col]) else ""
            # Экранируем HTML символы
            value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(f"<td>{value}</td>")
        html_rows.append(f"<tr>{''.join(cells)}</tr>")
    
    html_file = csv_file.replace('.csv', '_instructions.html')
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WSDC Points - Инструкция для Google Sheets</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            border-bottom: 3px solid #1a73e8;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34a853;
            margin-top: 30px;
        }}
        .step {{
            background: #f8f9fa;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #1a73e8;
            border-radius: 4px;
        }}
        .step-number {{
            font-weight: bold;
            color: #1a73e8;
            font-size: 1.2em;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
            max-height: 600px;
            overflow-y: auto;
            display: block;
        }}
        .data-table thead {{
            display: table;
            width: 100%;
            table-layout: fixed;
        }}
        .data-table tbody {{
            display: block;
            max-height: 500px;
            overflow-y: auto;
        }}
        .data-table tr {{
            display: table;
            width: 100%;
            table-layout: fixed;
        }}
        .data-table th {{
            background: #1a73e8;
            color: white;
            padding: 10px;
            text-align: left;
            position: sticky;
            top: 0;
        }}
        .data-table td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        .data-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .data-table tr:hover {{
            background: #e8f0fe;
        }}
        .info-box {{
            background: #e8f0fe;
            border-left: 4px solid #1a73e8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        code {{
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .link {{
            color: #1a73e8;
            text-decoration: none;
        }}
        .link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 WSDC Points - Инструкция для вставки в Google Sheets</h1>
        
        <div class="info-box">
            <strong>📅 Дата данных:</strong> {as_of_date}<br>
            <strong>📝 Всего записей:</strong> {len(df)}<br>
            <strong>📁 CSV файл:</strong> <code>{csv_file}</code>
        </div>
        
        <h2>📋 Способ 1: Импорт CSV файла (Рекомендуется)</h2>
        
        <div class="step">
            <span class="step-number">Шаг 1:</span> Откройте Google Sheets по ссылке:<br>
            <a href="https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit" target="_blank" class="link">
                https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit
            </a>
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 2:</span> Создайте новый лист (или выберите существующий) для данных WSDC Points
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 3:</span> В меню выберите <strong>Файл → Импортировать</strong>
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 4:</span> Выберите вкладку <strong>"Загрузить"</strong> и загрузите файл <code>{csv_file}</code>
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 5:</span> В настройках импорта выберите:
            <ul>
                <li><strong>Разделитель:</strong> Запятая</li>
                <li><strong>Преобразовать текст в числа, даты и формулы:</strong> Да</li>
            </ul>
        </div>
        
        <h2>📋 Способ 2: Копирование через буфер обмена</h2>
        
        <div class="step">
            <span class="step-number">Шаг 1:</span> Откройте файл <code>{csv_file}</code> в Excel, Notepad++ или другом редакторе
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 2:</span> Выделите все данные (Ctrl+A) и скопируйте (Ctrl+C)
        </div>
        
        <div class="step">
            <span class="step-number">Шаг 3:</span> Откройте Google Sheets и вставьте данные (Ctrl+V) в нужную ячейку
        </div>
        
        <div class="warning-box">
            <strong>⚠️ Важно:</strong> При копировании через буфер обмена убедитесь, что кодировка UTF-8 сохранена, 
            иначе русские имена могут отображаться некорректно.
        </div>
        
        <h2>📊 Предварительный просмотр данных</h2>
        
        <p>Ниже показаны все данные. Для удобства используйте прокрутку таблицы.</p>
        
        <table class="data-table">
            <thead>
                <tr>
                    {' '.join([f'<th>{col}</th>' for col in df.columns])}
                </tr>
            </thead>
            <tbody>
                {''.join(html_rows)}
            </tbody>
        </table>
        
        <div class="info-box">
            <strong>💡 Совет:</strong> После импорта данных вы можете:
            <ul>
                <li>Отформатировать заголовки (жирный шрифт, цвет фона)</li>
                <li>Добавить фильтры (Данные → Создать фильтр)</li>
                <li>Создать сводные таблицы для анализа</li>
                <li>Добавить условное форматирование для визуализации поинтов</li>
            </ul>
        </div>
        
        <hr style="margin: 30px 0; border: none; border-top: 2px solid #ddd;">
        
        <p style="text-align: center; color: #666;">
            Сгенерировано автоматически скриптом <code>create_gs_instructions.py</code><br>
            Дата: {time.strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>"""
    
    # Сохраняем HTML файл
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[OK] Создан файл с инструкцией: {html_file}", flush=True)
    print(flush=True)
    print("КРАТКАЯ ИНСТРУКЦИЯ:", flush=True)
    print(f"   1. Откройте Google Sheets: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit", flush=True)
    print(f"   2. Создайте новый лист для данных WSDC Points", flush=True)
    print(f"   3. Файл -> Импортировать -> Загрузить -> выберите '{csv_file}'", flush=True)
    print(f"   4. Или откройте '{html_file}' в браузере для подробной инструкции", flush=True)
    print(flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python create_gs_instructions.py <csv_file>", flush=True)
        print("Пример: python create_gs_instructions.py wsdc_points_2026-01-28.csv", flush=True)
        sys.exit(1)
    
    csv_file = sys.argv[1]
    create_google_sheets_instructions(csv_file)
