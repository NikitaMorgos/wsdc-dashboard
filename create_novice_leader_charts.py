#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создаёт набор диаграмм для танцоров дивизиона Novice в роли Leader.
Генерирует HTML файлы с интерактивными диаграммами используя Chart.js.

Использование:
    python create_novice_leader_charts.py <csv_file>
"""

import sys
import pandas as pd
import json
import os
from datetime import datetime


def load_and_filter_data(csv_file: str):
    """
    Загружает данные и фильтрует по Novice Leader.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    # Определяем столбец с очками
    points_col = None
    for col in df.columns:
        if 'points' in col.lower():
            points_col = col
            break
    
    if points_col is None:
        raise ValueError("Не найден столбец с очками (points)")
    
    print(f"Используется столбец с очками: {points_col}")
    
    # Фильтруем по Novice Leader
    filtered = df[
        (df['division'] == 'Novice') & 
        (df['role'] == 'Leader')
    ].copy()
    
    # Преобразуем очки в числовой формат
    filtered[points_col] = pd.to_numeric(filtered[points_col], errors='coerce').fillna(0)
    
    # Сортируем по очкам
    filtered = filtered.sort_values(points_col, ascending=False)
    
    # Создаём поле для отображения имени
    filtered['display_name'] = filtered['name_ru'].fillna(filtered['name_en'])
    
    print(f"Найдено {len(filtered)} танцоров Novice Leader")
    print(f"Диапазон очков: {filtered[points_col].min()} - {filtered[points_col].max()}")
    
    return filtered, points_col


def create_html_dashboard(df: pd.DataFrame, points_col: str, output_file: str = "charts/novice_leader_dashboard.html"):
    """
    Создаёт HTML файл с интерактивными диаграммами.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Подготовка данных
    top_20 = df.head(20)
    top_20_names = top_20['display_name'].tolist()
    top_20_points = top_20[points_col].astype(int).tolist()
    
    # Категории
    df['category'] = pd.cut(
        df[points_col],
        bins=[-1, 15, 30, 1000],
        labels=['Novice (< 16)', 'Allowed (16-30)', 'Advanced (> 30)']
    )
    category_counts = df['category'].value_counts()
    
    # Гистограмма данные
    hist_bins = 30
    hist_data, hist_edges = pd.cut(df[points_col], bins=hist_bins, retbins=True)
    hist_counts = hist_data.value_counts().sort_index()
    hist_labels = [f"{int(hist_edges[i])}-{int(hist_edges[i+1])}" for i in range(len(hist_edges)-1)]
    
    # Статистика
    stats = {
        'total': len(df),
        'mean': round(df[points_col].mean(), 2),
        'median': round(df[points_col].median(), 2),
        'min': int(df[points_col].min()),
        'max': int(df[points_col].max()),
        'std': round(df[points_col].std(), 2),
        'novice': len(df[df[points_col] < 16]),
        'allowed': len(df[(df[points_col] >= 16) & (df[points_col] <= 30)]),
        'advanced': len(df[df[points_col] > 30])
    }
    
    # HTML шаблон
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Анализ Novice Leader</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        .chart-container {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-container h2 {{
            margin-top: 0;
            color: #333;
            font-size: 1.3em;
            margin-bottom: 15px;
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        canvas {{
            max-height: 400px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Анализ Novice Leader</h1>
        <p class="subtitle">Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Всего танцоров</h3>
                <div class="value">{stats['total']}</div>
            </div>
            <div class="stat-card">
                <h3>Среднее очков</h3>
                <div class="value">{stats['mean']}</div>
            </div>
            <div class="stat-card">
                <h3>Медиана</h3>
                <div class="value">{stats['median']}</div>
            </div>
            <div class="stat-card">
                <h3>Максимум</h3>
                <div class="value">{stats['max']}</div>
            </div>
            <div class="stat-card">
                <h3>Novice (&lt; 16)</h3>
                <div class="value">{stats['novice']}</div>
            </div>
            <div class="stat-card">
                <h3>Allowed (16-30)</h3>
                <div class="value">{stats['allowed']}</div>
            </div>
            <div class="stat-card">
                <h3>Advanced (&gt; 30)</h3>
                <div class="value">{stats['advanced']}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h2>📈 Распределение очков</h2>
                <canvas id="histogramChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>🥇 Топ-20 танцоров</h2>
                <canvas id="top20Chart"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>📊 Распределение по категориям</h2>
                <canvas id="pieChart"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>📉 Столбчатая диаграмма категорий</h2>
                <canvas id="barChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Гистограмма
        const histCtx = document.getElementById('histogramChart').getContext('2d');
        new Chart(histCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(hist_labels[:20])},
                datasets: [{{
                    label: 'Количество танцоров',
                    data: {json.dumps(hist_counts.tolist()[:20])},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Количество' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Диапазон очков' }},
                        ticks: {{ maxRotation: 45, minRotation: 45 }}
                    }}
                }}
            }}
        }});
        
        // Топ-20
        const top20Ctx = document.getElementById('top20Chart').getContext('2d');
        new Chart(top20Ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_20_names, ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(top_20_points)},
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Очки' }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Танцор' }}
                    }}
                }}
            }}
        }});
        
        // Круговая диаграмма
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(category_counts.index.tolist(), ensure_ascii=False)},
                datasets: [{{
                    data: {json.dumps(category_counts.values.tolist())},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{ display: false }}
                }}
            }}
        }});
        
        // Столбчатая диаграмма категорий
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(category_counts.index.tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Количество танцоров',
                    data: {json.dumps(category_counts.values.tolist())},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Количество танцоров' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Категория' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Создан HTML дашборд: {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_novice_leader_charts.py <csv_file>")
        print("\nПример:")
        print("  python create_novice_leader_charts.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл не найден: {csv_file}", flush=True)
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ ДИАГРАММ ДЛЯ NOVICE LEADER")
    print("=" * 60)
    print()
    
    try:
        df, points_col = load_and_filter_data(csv_file)
        create_html_dashboard(df, points_col)
        print("\nГотово! Откройте HTML файл в браузере для просмотра диаграмм.", flush=True)
    except Exception as e:
        print(f"\nОшибка: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
