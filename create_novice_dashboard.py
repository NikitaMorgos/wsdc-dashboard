#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создаёт дашборд-анализ для дивизиона Novice с таблицами, топ-20 и разделением по ролям.

Использование:
    python create_novice_dashboard.py <csv_file>
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
        if 'points' in col.lower():
            points_col = col
            break
    
    if points_col is None:
        raise ValueError("Не найден столбец с очками (points)")
    
    print(f"Используется столбец с очками: {points_col}")
    
    # Фильтруем только Novice с < 16 очками
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
    ].copy()
    
    # Создаём поле для отображения имени
    filtered['display_name'] = filtered['name_ru'].fillna(filtered['name_en'])
    
    # Сортируем по очкам
    filtered = filtered.sort_values(points_col, ascending=False)
    
    print(f"Найдено {len(filtered)} записей Novice (< 16 очков)")
    print(f"  - Leader: {len(filtered[filtered['role'] == 'Leader'])}")
    print(f"  - Follower: {len(filtered[filtered['role'] == 'Follower'])}")
    if len(filtered) > 0:
        print(f"Диапазон очков: {filtered[points_col].min()} - {filtered[points_col].max()}")
    else:
        print("Диапазон очков: нет данных")
    
    return filtered, points_col


def create_novice_dashboard(df: pd.DataFrame, points_col: str, output_file: str = "charts/novice_dashboard.html"):
    """
    Создаёт HTML дашборд для Novice дивизиона.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Разделяем по ролям
    leader_df = df[df['role'] == 'Leader'].copy()
    follower_df = df[df['role'] == 'Follower'].copy()
    
    # Статистика по Leader
    stats_leader = {
        'total': len(leader_df),
        'mean': round(leader_df[points_col].mean(), 2) if len(leader_df) > 0 else 0,
        'median': round(leader_df[points_col].median(), 2) if len(leader_df) > 0 else 0,
        'min': int(leader_df[points_col].min()) if len(leader_df) > 0 else 0,
        'max': int(leader_df[points_col].max()) if len(leader_df) > 0 else 0,
        'std': round(leader_df[points_col].std(), 2) if len(leader_df) > 0 else 0,
        'zero_points': len(leader_df[leader_df[points_col] == 0]),
        'with_points': len(leader_df[leader_df[points_col] > 0])
    }
    
    # Статистика по Follower
    stats_follower = {
        'total': len(follower_df),
        'mean': round(follower_df[points_col].mean(), 2) if len(follower_df) > 0 else 0,
        'median': round(follower_df[points_col].median(), 2) if len(follower_df) > 0 else 0,
        'min': int(follower_df[points_col].min()) if len(follower_df) > 0 else 0,
        'max': int(follower_df[points_col].max()) if len(follower_df) > 0 else 0,
        'std': round(follower_df[points_col].std(), 2) if len(follower_df) > 0 else 0,
        'zero_points': len(follower_df[follower_df[points_col] == 0]),
        'with_points': len(follower_df[follower_df[points_col] > 0])
    }
    
    # Общая статистика
    stats_overall = {
        'total': len(df),
        'mean': round(df[points_col].mean(), 2),
        'median': round(df[points_col].median(), 2),
        'min': int(df[points_col].min()),
        'max': int(df[points_col].max()),
        'std': round(df[points_col].std(), 2),
        'zero_points': len(df[df[points_col] == 0]),
        'with_points': len(df[df[points_col] > 0])
    }
    
    # Все по ролям (включая 0 очков)
    all_leader = leader_df.copy()
    all_follower = follower_df.copy()
    
    # Все общий (сортировка по очкам, но включая всех)
    all_overall = df.copy()
    
    # Распределение по категориям
    df['category'] = pd.cut(
        df[points_col],
        bins=[-1, 0, 5, 10, 15, 20, 25, 30, 1000],
        labels=['0 очков', '1-5', '6-10', '11-15', '16-20', '21-25', '26-30', '> 30']
    )
    category_counts = df['category'].value_counts().sort_index()
    
    # Распределение по ролям
    role_comparison = {
        'Leader': len(leader_df),
        'Follower': len(follower_df)
    }
    
    # Средние очки по ролям
    avg_by_role = {
        'Leader': stats_leader['mean'],
        'Follower': stats_follower['mean']
    }
    
    # HTML шаблон
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дашборд: Novice Division</title>
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
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin: 40px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
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
        .stat-card.leader {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.follower {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
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
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        tbody tr:hover {{
            background: #f5f5f5;
        }}
        tbody tr:nth-child(even) {{
            background: #fafafa;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        canvas {{
            max-height: 500px;
        }}
        .chart-container.full-width {{
            min-height: 400px;
        }}
        .chart-container.full-width canvas {{
            max-height: none;
            height: auto !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Дашборд: Novice Division</h1>
        <p class="subtitle">Анализ дивизиона Novice с разделением по ролям (только < 16 очков)</p>
        <p class="subtitle">Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <h2 class="section-title">📈 Общая статистика</h2>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Всего записей</h3>
                <div class="value">{stats_overall['total']}</div>
            </div>
            <div class="stat-card">
                <h3>Среднее очков</h3>
                <div class="value">{stats_overall['mean']}</div>
            </div>
            <div class="stat-card">
                <h3>Медиана</h3>
                <div class="value">{stats_overall['median']}</div>
            </div>
            <div class="stat-card">
                <h3>Максимум</h3>
                <div class="value">{stats_overall['max']}</div>
            </div>
            <div class="stat-card">
                <h3>С очками</h3>
                <div class="value">{stats_overall['with_points']}</div>
            </div>
            <div class="stat-card">
                <h3>С 0 очками</h3>
                <div class="value">{stats_overall['zero_points']}</div>
            </div>
        </div>
        
        <h2 class="section-title">👥 Статистика по ролям</h2>
        
        <div class="stats-grid">
            <div class="stat-card leader">
                <h3>Leader: Всего</h3>
                <div class="value">{stats_leader['total']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Среднее</h3>
                <div class="value">{stats_leader['mean']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Медиана</h3>
                <div class="value">{stats_leader['median']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Максимум</h3>
                <div class="value">{stats_leader['max']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Всего</h3>
                <div class="value">{stats_follower['total']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Среднее</h3>
                <div class="value">{stats_follower['mean']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Медиана</h3>
                <div class="value">{stats_follower['median']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Максимум</h3>
                <div class="value">{stats_follower['max']}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h2>Сравнение Leader vs Follower</h2>
                <canvas id="roleComparison"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>Средние очки по ролям</h2>
                <canvas id="avgByRole"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>Распределение по категориям очков</h2>
                <canvas id="categoryDistribution"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>Распределение очков (гистограмма)</h2>
                <canvas id="pointsHistogram"></canvas>
            </div>
        </div>
        
        <h2 class="section-title">🏆 Все танцоры Novice (общий список)</h2>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Место</th>
                        <th>Имя</th>
                        <th>Роль</th>
                        <th>Очки</th>
                        <th>WSDC ID</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Добавляем строки таблицы для всех
    for i, (_, row) in enumerate(all_overall.iterrows(), 1):
        name = row['display_name']
        role = row['role']
        points = int(row[points_col])
        wsdc_id = int(row['wsdc_id']) if pd.notna(row['wsdc_id']) else '-'
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{name}</td>
                        <td>{role}</td>
                        <td><strong>{points}</strong></td>
                        <td>{wsdc_id}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <h2 class="section-title">🥇 Все Leader ({len(all_leader)} танцоров)</h2>
        
        <div class="chart-container full-width">
            <canvas id="allLeader"></canvas>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Место</th>
                        <th>Имя</th>
                        <th>Очки</th>
                        <th>WSDC ID</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Таблица всех Leader
    for i, (_, row) in enumerate(all_leader.iterrows(), 1):
        name = row['display_name']
        points = int(row[points_col])
        wsdc_id = int(row['wsdc_id']) if pd.notna(row['wsdc_id']) else '-'
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{name}</td>
                        <td><strong>{points}</strong></td>
                        <td>{wsdc_id}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <h2 class="section-title">🥈 Все Follower ({len(all_follower)} танцоров)</h2>
        
        <div class="chart-container full-width">
            <canvas id="allFollower"></canvas>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Место</th>
                        <th>Имя</th>
                        <th>Очки</th>
                        <th>WSDC ID</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Таблица всех Follower
    for i, (_, row) in enumerate(all_follower.iterrows(), 1):
        name = row['display_name']
        points = int(row[points_col])
        wsdc_id = int(row['wsdc_id']) if pd.notna(row['wsdc_id']) else '-'
        html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{name}</td>
                        <td><strong>{points}</strong></td>
                        <td>{wsdc_id}</td>
                    </tr>
"""
    
    html_content += f"""
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Сравнение ролей
        const roleCompCtx = document.getElementById('roleComparison').getContext('2d');
        new Chart(roleCompCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    data: [{role_comparison['Leader']}, {role_comparison['Follower']}],
                    backgroundColor: ['rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)'],
                    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{ position: 'bottom' }}
                }}
            }}
        }});
        
        // Средние очки по ролям
        const avgRoleCtx = document.getElementById('avgByRole').getContext('2d');
        new Chart(avgRoleCtx, {{
            type: 'bar',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    label: 'Среднее очков',
                    data: [{avg_by_role['Leader']}, {avg_by_role['Follower']}],
                    backgroundColor: ['rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)'],
                    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Среднее очков' }}
                    }}
                }}
            }}
        }});
        
        // Распределение по категориям
        const catDistCtx = document.getElementById('categoryDistribution').getContext('2d');
        new Chart(catDistCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(category_counts.index.tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Количество',
                    data: {json.dumps(category_counts.values.tolist())},
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Количество танцоров' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Диапазон очков' }}
                    }}
                }}
            }}
        }});
        
        // Гистограмма распределения очков
        const histCtx = document.getElementById('pointsHistogram').getContext('2d');
        const histData = {json.dumps(df[points_col].tolist())};
        new Chart(histCtx, {{
            type: 'bar',
            data: {{
                labels: Array.from({{length: Math.max(...histData) + 1}}, (_, i) => i),
                datasets: [{{
                    label: 'Количество танцоров',
                    data: histData.reduce((acc, val) => {{
                        acc[val] = (acc[val] || 0) + 1;
                        return acc;
                    }}, []),
                    backgroundColor: 'rgba(153, 102, 255, 0.6)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Количество' }}
                    }},
                    x: {{
                        title: {{ display: true, text: 'Очки' }}
                    }}
                }}
            }}
        }});
        
        // Все Leader
        const allLeaderCtx = document.getElementById('allLeader').getContext('2d');
        new Chart(allLeaderCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(all_leader['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(all_leader[points_col].astype(int).tolist())},
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Очки' }}
                    }},
                    y: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{
                                size: 11
                            }}
                        }},
                        afterFit: function(scale) {{
                            scale.width = Math.max(scale.width, 200);
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Все Follower
        const allFollowerCtx = document.getElementById('allFollower').getContext('2d');
        new Chart(allFollowerCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(all_follower['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(all_follower[points_col].astype(int).tolist())},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{ display: true, text: 'Очки' }}
                    }},
                    y: {{
                        ticks: {{
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: false,
                            font: {{
                                size: 11
                            }}
                        }},
                        afterFit: function(scale) {{
                            scale.width = Math.max(scale.width, 200);
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
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
        print("Использование: python create_novice_dashboard.py <csv_file>")
        print("\nПример:")
        print("  python create_novice_dashboard.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized_with_novice_zero.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл не найден: {csv_file}", flush=True)
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ ДАШБОРДА NOVICE")
    print("=" * 60)
    print()
    
    try:
        df, points_col = load_and_filter_novice(csv_file)
        create_novice_dashboard(df, points_col)
        print("\nГотово! Откройте HTML файл в браузере для просмотра дашборда.", flush=True)
    except Exception as e:
        print(f"\nОшибка: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
