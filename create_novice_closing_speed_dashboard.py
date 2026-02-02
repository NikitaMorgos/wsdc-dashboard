#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создаёт дашборд с анализом скорости закрытия новисов.

Использование:
    python create_novice_closing_speed_dashboard.py <csv_file>
"""

import sys
import pandas as pd
import json
import os
from datetime import datetime


def load_novice_data(csv_file: str):
    """
    Загружает данные и фильтрует только Novice записи с закрытыми новисами.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"Исходных записей: {len(df)}")
    
    # Фильтруем только Novice с заполненным months_to_close_novice
    novice_df = df[
        (df['division'] == 'Novice') & 
        (df['months_to_close_novice'].notna()) & 
        (df['months_to_close_novice'] != '') &
        (df['months_to_close_novice'] != 0)
    ].copy()
    
    # Преобразуем months_to_close_novice в числовой формат
    novice_df['months_to_close_novice'] = pd.to_numeric(novice_df['months_to_close_novice'], errors='coerce')
    
    # Удаляем записи с некорректными значениями
    novice_df = novice_df[novice_df['months_to_close_novice'] > 0].copy()
    
    print(f"Найдено {len(novice_df)} записей Novice с закрытыми новисами")
    
    return novice_df


def generate_dashboard(df, output_file='novice_closing_speed_dashboard.html'):
    """
    Генерирует HTML дашборд с анализом скорости закрытия новисов.
    """
    print("Генерирую дашборд...")
    
    # Разделяем по ролям
    leader_df = df[df['role'] == 'Leader'].copy()
    follower_df = df[df['role'] == 'Follower'].copy()
    
    print(f"Leader: {len(leader_df)} записей")
    print(f"Follower: {len(follower_df)} записей")
    
    # Статистика
    def calculate_stats(data_df, role_name):
        if len(data_df) == 0:
            return {
                'count': 0,
                'mean': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'std': 0,
                'q25': 0,
                'q75': 0
            }
        
        months_series = data_df['months_to_close_novice']
        return {
            'count': len(data_df),
            'mean': float(months_series.mean()),
            'median': float(months_series.median()),
            'min': float(months_series.min()),
            'max': float(months_series.max()),
            'std': float(months_series.std()),
            'q25': float(months_series.quantile(0.25)),
            'q75': float(months_series.quantile(0.75))
        }
    
    leader_stats = calculate_stats(leader_df, 'Leader')
    follower_stats = calculate_stats(follower_df, 'Follower')
    all_stats = calculate_stats(df, 'All')
    
    # Топ быстрых закрытий (меньше месяцев)
    top_fast_leader = leader_df.nsmallest(20, 'months_to_close_novice') if len(leader_df) > 0 else pd.DataFrame()
    top_fast_follower = follower_df.nsmallest(20, 'months_to_close_novice') if len(follower_df) > 0 else pd.DataFrame()
    
    # Топ медленных закрытий (больше месяцев)
    top_slow_leader = leader_df.nlargest(20, 'months_to_close_novice') if len(leader_df) > 0 else pd.DataFrame()
    top_slow_follower = follower_df.nlargest(20, 'months_to_close_novice') if len(follower_df) > 0 else pd.DataFrame()
    
    # Распределение по диапазонам месяцев
    def create_distribution(data_df):
        if len(data_df) == 0:
            return {'labels': [], 'data': []}
        
        bins = [0, 3, 6, 9, 12, 18, 24, 36, 60, 120, float('inf')]
        labels = ['0-3', '3-6', '6-9', '9-12', '12-18', '18-24', '24-36', '36-60', '60-120', '120+']
        
        data_df['range'] = pd.cut(data_df['months_to_close_novice'], bins=bins, labels=labels, right=False)
        distribution = data_df['range'].value_counts().sort_index()
        
        return {
            'labels': distribution.index.tolist(),
            'data': distribution.values.tolist()
        }
    
    leader_dist = create_distribution(leader_df)
    follower_dist = create_distribution(follower_df)
    all_dist = create_distribution(df)
    
    # Подготовка данных для графиков
    leader_chart_data = {
        'labels': leader_df['name_ru'].fillna(leader_df['name_en']).tolist() if len(leader_df) > 0 else [],
        'months': leader_df['months_to_close_novice'].tolist() if len(leader_df) > 0 else [],
        'names': leader_df['name_en'].tolist() if len(leader_df) > 0 else []
    }
    
    follower_chart_data = {
        'labels': follower_df['name_ru'].fillna(follower_df['name_en']).tolist() if len(follower_df) > 0 else [],
        'months': follower_df['months_to_close_novice'].tolist() if len(follower_df) > 0 else [],
        'names': follower_df['name_en'].tolist() if len(follower_df) > 0 else []
    }
    
    # HTML шаблон
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Анализ скорости закрытия Novice - WSDC Points</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        
        .stat-card .subtitle {{
            font-size: 0.85em;
            color: #666;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart-container {{
            position: relative;
            height: 500px;
            margin-bottom: 30px;
        }}
        
        .chart-container-large {{
            position: relative;
            height: 700px;
            margin-bottom: 30px;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}
        
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        tbody tr:hover {{
            background: #f5f5f5;
        }}
        
        .months-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .fast {{
            background: #4caf50;
        }}
        
        .slow {{
            background: #f44336;
        }}
        
        .two-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}
        
        @media (max-width: 1200px) {{
            .two-columns {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Анализ скорости закрытия Novice</h1>
            <p>Сколько месяцев требуется танцорам для закрытия новисов (16 очков)</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Всего закрытий</h3>
                <div class="value">{all_stats['count']}</div>
                <p class="subtitle">танцоров</p>
            </div>
            <div class="stat-card">
                <h3>Среднее (все)</h3>
                <div class="value">{all_stats['mean']:.1f}</div>
                <p class="subtitle">месяцев</p>
            </div>
            <div class="stat-card">
                <h3>Медиана (все)</h3>
                <div class="value">{all_stats['median']:.1f}</div>
                <p class="subtitle">месяцев</p>
            </div>
            <div class="stat-card">
                <h3>Минимум</h3>
                <div class="value">{all_stats['min']:.0f}</div>
                <p class="subtitle">месяцев</p>
            </div>
            <div class="stat-card">
                <h3>Максимум</h3>
                <div class="value">{all_stats['max']:.0f}</div>
                <p class="subtitle">месяцев</p>
            </div>
            <div class="stat-card">
                <h3>Среднее (Лидеры)</h3>
                <div class="value">{leader_stats['mean']:.1f}</div>
                <p class="subtitle">месяцев</p>
            </div>
            <div class="stat-card">
                <h3>Среднее (Фолловеры)</h3>
                <div class="value">{follower_stats['mean']:.1f}</div>
                <p class="subtitle">месяцев</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Распределение по диапазонам месяцев</h2>
            <div class="chart-container">
                <canvas id="distributionChart"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Сравнение по ролям</h2>
            <div class="two-columns">
                <div>
                    <h3 style="color: #667eea; margin-bottom: 15px;">Лидеры</h3>
                    <div class="chart-container">
                        <canvas id="leaderDistributionChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3 style="color: #667eea; margin-bottom: 15px;">Фолловеры</h3>
                    <div class="chart-container">
                        <canvas id="followerDistributionChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Топ-20 быстрых закрытий (Лидеры)</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Место</th>
                            <th>Имя</th>
                            <th>Месяцев</th>
                            <th>Первый пойнт</th>
                            <th>Закрытие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_top_table_rows(top_fast_leader, 'fast')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Топ-20 быстрых закрытий (Фолловеры)</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Место</th>
                            <th>Имя</th>
                            <th>Месяцев</th>
                            <th>Первый пойнт</th>
                            <th>Закрытие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_top_table_rows(top_fast_follower, 'fast')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>⏳ Топ-20 медленных закрытий (Лидеры)</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Место</th>
                            <th>Имя</th>
                            <th>Месяцев</th>
                            <th>Первый пойнт</th>
                            <th>Закрытие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_top_table_rows(top_slow_leader, 'slow')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>⏳ Топ-20 медленных закрытий (Фолловеры)</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Место</th>
                            <th>Имя</th>
                            <th>Месяцев</th>
                            <th>Первый пойнт</th>
                            <th>Закрытие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_top_table_rows(top_slow_follower, 'slow')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>📉 Все закрытия (сортировка по скорости)</h2>
            <div class="chart-container-large">
                <canvas id="allClosingsChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Данные для графиков
        const allDistribution = {json.dumps(all_dist)};
        const leaderDistribution = {json.dumps(leader_dist)};
        const followerDistribution = {json.dumps(follower_dist)};
        const leaderData = {json.dumps(leader_chart_data)};
        const followerData = {json.dumps(follower_chart_data)};
        
        // График распределения (все)
        const distCtx = document.getElementById('distributionChart').getContext('2d');
        new Chart(distCtx, {{
            type: 'bar',
            data: {{
                labels: allDistribution.labels,
                datasets: [{{
                    label: 'Количество танцоров',
                    data: allDistribution.data,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{
                        display: true,
                        text: 'Распределение по диапазонам месяцев',
                        font: {{ size: 18, weight: 'bold' }},
                        color: '#667eea'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Количество танцоров'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Месяцев до закрытия'
                        }}
                    }}
                }}
            }}
        }});
        
        // График распределения лидеров
        const leaderDistCtx = document.getElementById('leaderDistributionChart').getContext('2d');
        new Chart(leaderDistCtx, {{
            type: 'bar',
            data: {{
                labels: leaderDistribution.labels,
                datasets: [{{
                    label: 'Лидеры',
                    data: leaderDistribution.data,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }},
                    x: {{ title: {{ display: true, text: 'Месяцев' }} }}
                }}
            }}
        }});
        
        // График распределения фолловеров
        const followerDistCtx = document.getElementById('followerDistributionChart').getContext('2d');
        new Chart(followerDistCtx, {{
            type: 'bar',
            data: {{
                labels: followerDistribution.labels,
                datasets: [{{
                    label: 'Фолловеры',
                    data: followerDistribution.data,
                    backgroundColor: 'rgba(118, 75, 162, 0.6)',
                    borderColor: 'rgba(118, 75, 162, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }},
                    x: {{ title: {{ display: true, text: 'Месяцев' }} }}
                }}
            }}
        }});
        
        // График всех закрытий
        const allCtx = document.getElementById('allClosingsChart').getContext('2d');
        const allLabels = [...leaderData.labels, ...followerData.labels];
        const allMonths = [...leaderData.months, ...followerData.months];
        const allColors = [
            ...Array(leaderData.months.length).fill('rgba(102, 126, 234, 0.6)'),
            ...Array(followerData.months.length).fill('rgba(118, 75, 162, 0.6)')
        ];
        
        // Сортируем по месяцам
        const sorted = allLabels.map((label, i) => ({{
            label: label,
            months: allMonths[i],
            color: allColors[i]
        }})).sort((a, b) => a.months - b.months);
        
        new Chart(allCtx, {{
            type: 'bar',
            data: {{
                labels: sorted.map(s => s.label),
                datasets: [{{
                    label: 'Месяцев до закрытия',
                    data: sorted.map(s => s.months),
                    backgroundColor: sorted.map(s => s.color),
                    borderColor: sorted.map(s => s.color.replace('0.6', '1')),
                    borderWidth: 2
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{
                        display: true,
                        text: 'Все закрытия (от быстрых к медленным)',
                        font: {{ size: 18, weight: 'bold' }},
                        color: '#667eea'
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Месяцев: ' + context.parsed.x;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Месяцев до закрытия'
                        }}
                    }},
                    y: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{ size: 9 }}
                        }},
                        afterFit: function(scale) {{
                            scale.width = Math.max(scale.width, 200);
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    # Сохраняем файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Дашборд сохранен: {output_file}")
    return output_file


def generate_top_table_rows(df, style=''):
    """
    Генерирует HTML строки для таблицы топ закрытий.
    """
    rows = []
    for idx, (i, row) in enumerate(df.iterrows(), 1):
        name_ru = str(row['name_ru']) if pd.notna(row['name_ru']) else ''
        name_en = str(row['name_en']) if pd.notna(row['name_en']) else ''
        name = name_ru if name_ru else name_en
        months = int(row['months_to_close_novice']) if pd.notna(row['months_to_close_novice']) else 0
        first_date = str(row['first_event_date']) if pd.notna(row['first_event_date']) else ''
        closed_date = str(row['novice_closed_date']) if pd.notna(row['novice_closed_date']) else ''
        
        badge_class = 'fast' if style == 'fast' else 'slow'
        
        rows.append(f"""
            <tr>
                <td><strong>#{idx}</strong></td>
                <td>{name}</td>
                <td><span class="months-badge {badge_class}">{months}</span></td>
                <td>{first_date}</td>
                <td>{closed_date}</td>
            </tr>
        """)
    
    if not rows:
        rows.append('<tr><td colspan="5" style="text-align: center; padding: 20px;">Нет данных</td></tr>')
    
    return ''.join(rows)


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_novice_closing_speed_dashboard.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: файл {csv_file} не найден")
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ ДАШБОРДА АНАЛИЗА СКОРОСТИ ЗАКРЫТИЯ NOVICE")
    print("=" * 60)
    print()
    
    try:
        df = load_novice_data(csv_file)
        output_file = generate_dashboard(df)
        
        print()
        print("=" * 60)
        print("ГОТОВО!")
        print(f"Дашборд сохранен: {output_file}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
