#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создаёт дашборд-рейтинг для дивизиона Novice с акцентом на рейтинг по очкам в разрезе ролей.

Использование:
    python create_novice_rating_dashboard.py <csv_file>
"""

import sys
import pandas as pd
import json
import os
from datetime import datetime


def load_and_filter_novice(csv_file: str):
    """
    Загружает данные и фильтрует только Novice дивизион.
    """
    print("Загружаю данные...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    # Определяем столбец с очками
    points_col = None
    for col in df.columns:
        if 'points' in col.lower() and col.startswith('points_'):
            points_col = col
            break
    
    if points_col is None:
        raise ValueError("Не найден столбец с очками (points_*)")
    
    print(f"Используется столбец с очками: {points_col}")
    
    # Фильтруем только Novice
    filtered = df[df['division'] == 'Novice'].copy()
    
    # Преобразуем очки в числовой формат
    filtered[points_col] = pd.to_numeric(filtered[points_col], errors='coerce').fillna(0)
    
    # Фильтруем только танцоров с < 16 очками
    filtered = filtered[filtered[points_col] < 16].copy()
    
    # Удаляем Артема Шаповалова
    filtered = filtered[
        ~(
            (filtered['name_ru'].str.contains('Шаповалов', na=False)) |
            (filtered['name_en'].str.contains('Shapovalov', na=False))
        )
    ]
    
    print(f"Найдено {len(filtered)} записей Novice (с < 16 очками)")
    
    return filtered, points_col


def create_rating_data(df, points_col, role):
    """
    Создает рейтинг для указанной роли.
    """
    role_df = df[df['role'] == role].copy()
    
    # Группируем по танцору (берем максимальные очки для каждого танцора)
    dancer_max_points = role_df.groupby(['wsdc_id', 'name_ru', 'name_en'])[points_col].max().reset_index()
    
    # Сортируем по очкам (по убыванию)
    dancer_max_points = dancer_max_points.sort_values(points_col, ascending=False)
    
    # Добавляем рейтинг
    dancer_max_points['rating'] = range(1, len(dancer_max_points) + 1)
    
    # Переименовываем столбец с очками для удобства
    dancer_max_points = dancer_max_points.rename(columns={points_col: 'points'})
    
    return dancer_max_points


def generate_dashboard(df, points_col, output_file='novice_rating_dashboard.html'):
    """
    Генерирует HTML дашборд с рейтингами.
    """
    print("Генерирую дашборд...")
    
    # Создаем рейтинги для Leader и Follower
    leader_rating = create_rating_data(df, points_col, 'Leader')
    follower_rating = create_rating_data(df, points_col, 'Follower')
    
    print(f"Leader: {len(leader_rating)} танцоров")
    print(f"Follower: {len(follower_rating)} танцоров")
    
    # Подготавливаем данные для графиков
    leader_chart_data = {
        'labels': leader_rating['name_ru'].fillna(leader_rating['name_en']).tolist(),
        'points': leader_rating['points'].tolist(),
        'ratings': leader_rating['rating'].tolist()
    }
    
    follower_chart_data = {
        'labels': follower_rating['name_ru'].fillna(follower_rating['name_en']).tolist(),
        'points': follower_rating['points'].tolist(),
        'ratings': follower_rating['rating'].tolist()
    }
    
    # Статистика
    total_leader = len(leader_rating)
    total_follower = len(follower_rating)
    avg_points_leader = leader_rating['points'].mean()
    avg_points_follower = follower_rating['points'].mean()
    max_points_leader = leader_rating['points'].max()
    max_points_follower = follower_rating['points'].max()
    
    # HTML шаблон
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Рейтинг Novice - WSDC Points</title>
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
            max-width: 1400px;
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
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
        
        .role-section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }}
        
        .role-section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart-container {{
            position: relative;
            height: 600px;
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
        
        .rating-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .points-value {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .top-3 {{
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            color: white;
        }}
        
        .top-3 .rating-badge {{
            background: rgba(255,255,255,0.3);
        }}
        
        .top-3 .points-value {{
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Рейтинг Novice</h1>
            <p>Рейтинг танцоров по количеству очков в разрезе ролей</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Лидеры</h3>
                <div class="value">{total_leader}</div>
                <p>танцоров</p>
            </div>
            <div class="stat-card">
                <h3>Фолловеры</h3>
                <div class="value">{total_follower}</div>
                <p>танцоров</p>
            </div>
            <div class="stat-card">
                <h3>Средние очки (Лидеры)</h3>
                <div class="value">{avg_points_leader:.1f}</div>
                <p>очков</p>
            </div>
            <div class="stat-card">
                <h3>Средние очки (Фолловеры)</h3>
                <div class="value">{avg_points_follower:.1f}</div>
                <p>очков</p>
            </div>
            <div class="stat-card">
                <h3>Максимум (Лидеры)</h3>
                <div class="value">{max_points_leader}</div>
                <p>очков</p>
            </div>
            <div class="stat-card">
                <h3>Максимум (Фолловеры)</h3>
                <div class="value">{max_points_follower}</div>
                <p>очков</p>
            </div>
        </div>
        
        <div class="role-section">
            <h2>👔 Лидеры (Leader)</h2>
            <div class="chart-container">
                <canvas id="leaderChart"></canvas>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Рейтинг</th>
                            <th>Имя (RU)</th>
                            <th>Имя (EN)</th>
                            <th>Очки</th>
                            <th>ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_table_rows(leader_rating)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="role-section">
            <h2>👗 Фолловеры (Follower)</h2>
            <div class="chart-container">
                <canvas id="followerChart"></canvas>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Рейтинг</th>
                            <th>Имя (RU)</th>
                            <th>Имя (EN)</th>
                            <th>Очки</th>
                            <th>ID</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_table_rows(follower_rating)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        // Данные для графиков
        const leaderData = {json.dumps(leader_chart_data)};
        const followerData = {json.dumps(follower_chart_data)};
        
        // Настройки для графиков
        const chartOptions = {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: false
                }},
                title: {{
                    display: true,
                    text: 'Рейтинг по очкам',
                    font: {{
                        size: 18,
                        weight: 'bold'
                    }},
                    color: '#667eea'
                }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const dataIndex = context.dataIndex;
                            const ratings = context.chart.canvas.id === 'leaderChart' ? leaderData.ratings : followerData.ratings;
                            return 'Очки: ' + context.parsed.x + ' (Рейтинг: #' + ratings[dataIndex] + ')';
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: 'Очки',
                        font: {{
                            size: 14,
                            weight: 'bold'
                        }}
                    }},
                    ticks: {{
                        stepSize: 1
                    }}
                }},
                y: {{
                    ticks: {{
                        maxRotation: 0,
                        minRotation: 0,
                        autoSkip: false,
                        font: {{
                            size: 10
                        }}
                    }},
                    afterFit: function(scale) {{
                        scale.width = Math.max(scale.width, 250);
                    }}
                }}
            }}
        }};
        
        // График для лидеров
        const leaderCtx = document.getElementById('leaderChart').getContext('2d');
        new Chart(leaderCtx, {{
            type: 'bar',
            data: {{
                labels: leaderData.labels,
                datasets: [{{
                    label: 'Очки',
                    data: leaderData.points,
                    backgroundColor: leaderData.points.map((p, i) => 
                        i < 3 ? 'rgba(246, 211, 101, 0.8)' : 'rgba(102, 126, 234, 0.6)'
                    ),
                    borderColor: leaderData.points.map((p, i) => 
                        i < 3 ? 'rgba(246, 211, 101, 1)' : 'rgba(102, 126, 234, 1)'
                    ),
                    borderWidth: 2
                }}]
            }},
            options: chartOptions
        }});
        
        // График для фолловеров
        const followerCtx = document.getElementById('followerChart').getContext('2d');
        new Chart(followerCtx, {{
            type: 'bar',
            data: {{
                labels: followerData.labels,
                datasets: [{{
                    label: 'Очки',
                    data: followerData.points,
                    backgroundColor: followerData.points.map((p, i) => 
                        i < 3 ? 'rgba(246, 211, 101, 0.8)' : 'rgba(102, 126, 234, 0.6)'
                    ),
                    borderColor: followerData.points.map((p, i) => 
                        i < 3 ? 'rgba(246, 211, 101, 1)' : 'rgba(102, 126, 234, 1)'
                    ),
                    borderWidth: 2
                }}]
            }},
            options: chartOptions
        }});
    </script>
</body>
</html>"""
    
    # Сохраняем файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Дашборд сохранен: {output_file}")
    return output_file


def generate_table_rows(rating_df):
    """
    Генерирует HTML строки для таблицы рейтинга.
    """
    rows = []
    for idx, row in rating_df.iterrows():
        rating = int(row['rating'])
        name_ru = str(row['name_ru']) if pd.notna(row['name_ru']) else ''
        name_en = str(row['name_en']) if pd.notna(row['name_en']) else ''
        points = int(row['points'])
        wsdc_id = int(row['wsdc_id']) if pd.notna(row['wsdc_id']) else ''
        
        # Выделяем топ-3
        row_class = 'top-3' if rating <= 3 else ''
        
        rows.append(f"""
            <tr class="{row_class}">
                <td><span class="rating-badge">#{rating}</span></td>
                <td>{name_ru}</td>
                <td>{name_en}</td>
                <td><span class="points-value">{points}</span></td>
                <td>{wsdc_id}</td>
            </tr>
        """)
    
    return ''.join(rows)


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_novice_rating_dashboard.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: файл {csv_file} не найден")
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ ДАШБОРДА РЕЙТИНГА NOVICE")
    print("=" * 60)
    print()
    
    try:
        df, points_col = load_and_filter_novice(csv_file)
        output_file = generate_dashboard(df, points_col)
        
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
