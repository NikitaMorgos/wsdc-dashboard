#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создаёт расширенный анализ диаграмм:
- Анализ по ролям (Leader/Follower)
- Только танцоры с < 16 очков
- Анализ дивизиона Newcomer

Использование:
    python create_advanced_charts.py <csv_file>
"""

import sys
import pandas as pd
import json
import os
from datetime import datetime


def load_and_filter_data(csv_file: str):
    """
    Загружает данные и фильтрует по условиям.
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
    
    # Преобразуем очки в числовой формат
    df[points_col] = pd.to_numeric(df[points_col], errors='coerce').fillna(0)
    
    # Фильтруем: только танцоры с < 16 очков в Novice или с очками в Newcomer
    filtered = df[
        (
            (df['division'] == 'Novice') & (df[points_col] < 16)
        ) | (
            (df['division'] == 'Newcomer') & (df[points_col] > 0)
        )
    ].copy()
    
    # Создаём поле для отображения имени
    filtered['display_name'] = filtered['name_ru'].fillna(filtered['name_en'])
    
    print(f"\nНайдено записей:")
    print(f"  - Novice (< 16 очков): {len(filtered[filtered['division'] == 'Novice'])}")
    print(f"  - Newcomer (с очками): {len(filtered[filtered['division'] == 'Newcomer'])}")
    print(f"  - Leader: {len(filtered[filtered['role'] == 'Leader'])}")
    print(f"  - Follower: {len(filtered[filtered['role'] == 'Follower'])}")
    
    return filtered, points_col


def create_html_dashboard(df: pd.DataFrame, points_col: str, output_file: str = "charts/advanced_analysis_dashboard.html"):
    """
    Создаёт HTML файл с расширенными интерактивными диаграммами.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Разделяем по дивизионам
    novice_df = df[df['division'] == 'Novice'].copy()
    newcomer_df = df[df['division'] == 'Newcomer'].copy()
    
    # Разделяем по ролям
    leader_novice = novice_df[novice_df['role'] == 'Leader']
    follower_novice = novice_df[novice_df['role'] == 'Follower']
    leader_newcomer = newcomer_df[newcomer_df['role'] == 'Leader']
    follower_newcomer = newcomer_df[newcomer_df['role'] == 'Follower']
    
    # Статистика по ролям в Novice
    stats_novice_leader = {
        'total': len(leader_novice),
        'mean': round(leader_novice[points_col].mean(), 2) if len(leader_novice) > 0 else 0,
        'median': round(leader_novice[points_col].median(), 2) if len(leader_novice) > 0 else 0,
        'min': int(leader_novice[points_col].min()) if len(leader_novice) > 0 else 0,
        'max': int(leader_novice[points_col].max()) if len(leader_novice) > 0 else 0,
    }
    
    stats_novice_follower = {
        'total': len(follower_novice),
        'mean': round(follower_novice[points_col].mean(), 2) if len(follower_novice) > 0 else 0,
        'median': round(follower_novice[points_col].median(), 2) if len(follower_novice) > 0 else 0,
        'min': int(follower_novice[points_col].min()) if len(follower_novice) > 0 else 0,
        'max': int(follower_novice[points_col].max()) if len(follower_novice) > 0 else 0,
    }
    
    # Статистика по Newcomer
    stats_newcomer_leader = {
        'total': len(leader_newcomer),
        'mean': round(leader_newcomer[points_col].mean(), 2) if len(leader_newcomer) > 0 else 0,
        'median': round(leader_newcomer[points_col].median(), 2) if len(leader_newcomer) > 0 else 0,
        'min': int(leader_newcomer[points_col].min()) if len(leader_newcomer) > 0 else 0,
        'max': int(leader_newcomer[points_col].max()) if len(leader_newcomer) > 0 else 0,
    }
    
    stats_newcomer_follower = {
        'total': len(follower_newcomer),
        'mean': round(follower_newcomer[points_col].mean(), 2) if len(follower_newcomer) > 0 else 0,
        'median': round(follower_newcomer[points_col].median(), 2) if len(follower_newcomer) > 0 else 0,
        'min': int(follower_newcomer[points_col].min()) if len(follower_newcomer) > 0 else 0,
        'max': int(follower_newcomer[points_col].max()) if len(follower_newcomer) > 0 else 0,
    }
    
    # Топ-15 по ролям в Novice
    top_15_leader_novice = leader_novice.nlargest(15, points_col)
    top_15_follower_novice = follower_novice.nlargest(15, points_col)
    
    # Топ-15 по ролям в Newcomer
    top_15_leader_newcomer = leader_newcomer.nlargest(15, points_col) if len(leader_newcomer) > 0 else pd.DataFrame()
    top_15_follower_newcomer = follower_newcomer.nlargest(15, points_col) if len(follower_newcomer) > 0 else pd.DataFrame()
    
    # Сравнение Leader vs Follower в Novice
    role_comparison_novice = {
        'Leader': len(leader_novice),
        'Follower': len(follower_novice)
    }
    
    # Сравнение Leader vs Follower в Newcomer
    role_comparison_newcomer = {
        'Leader': len(leader_newcomer),
        'Follower': len(follower_newcomer)
    }
    
    # Распределение очков по ролям (для гистограммы)
    leader_points_novice = leader_novice[points_col].tolist()
    follower_points_novice = follower_novice[points_col].tolist()
    leader_points_newcomer = leader_newcomer[points_col].tolist() if len(leader_newcomer) > 0 else []
    follower_points_newcomer = follower_newcomer[points_col].tolist() if len(follower_newcomer) > 0 else []
    
    # HTML шаблон
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Расширенный анализ: Novice & Newcomer</title>
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
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
        canvas {{
            max-height: 400px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Расширенный анализ: Novice & Newcomer</h1>
        <p class="subtitle">Анализ по ролям (Leader/Follower) | Танцоры с < 16 очков в Novice | Все с очками в Newcomer</p>
        <p class="subtitle">Дата анализа: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <h2 class="section-title">📈 Novice Division (< 16 очков)</h2>
        
        <div class="stats-grid">
            <div class="stat-card leader">
                <h3>Leader: Всего</h3>
                <div class="value">{stats_novice_leader['total']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Среднее</h3>
                <div class="value">{stats_novice_leader['mean']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Медиана</h3>
                <div class="value">{stats_novice_leader['median']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Максимум</h3>
                <div class="value">{stats_novice_leader['max']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Всего</h3>
                <div class="value">{stats_novice_follower['total']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Среднее</h3>
                <div class="value">{stats_novice_follower['mean']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Медиана</h3>
                <div class="value">{stats_novice_follower['median']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Максимум</h3>
                <div class="value">{stats_novice_follower['max']}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h2>Сравнение Leader vs Follower (Novice)</h2>
                <canvas id="roleComparisonNovice"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>Распределение очков по ролям (Novice)</h2>
                <canvas id="distributionByRoleNovice"></canvas>
            </div>
            
            <div class="chart-container full-width">
                <h2>Топ-15 Leader (Novice)</h2>
                <canvas id="top15LeaderNovice"></canvas>
            </div>
            
            <div class="chart-container full-width">
                <h2>Топ-15 Follower (Novice)</h2>
                <canvas id="top15FollowerNovice"></canvas>
            </div>
        </div>
        
        <h2 class="section-title">🌟 Newcomer Division</h2>
        
        <div class="stats-grid">
            <div class="stat-card leader">
                <h3>Leader: Всего</h3>
                <div class="value">{stats_newcomer_leader['total']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Среднее</h3>
                <div class="value">{stats_newcomer_leader['mean']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Медиана</h3>
                <div class="value">{stats_newcomer_leader['median']}</div>
            </div>
            <div class="stat-card leader">
                <h3>Leader: Максимум</h3>
                <div class="value">{stats_newcomer_leader['max']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Всего</h3>
                <div class="value">{stats_newcomer_follower['total']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Среднее</h3>
                <div class="value">{stats_newcomer_follower['mean']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Медиана</h3>
                <div class="value">{stats_newcomer_follower['median']}</div>
            </div>
            <div class="stat-card follower">
                <h3>Follower: Максимум</h3>
                <div class="value">{stats_newcomer_follower['max']}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <h2>Сравнение Leader vs Follower (Newcomer)</h2>
                <canvas id="roleComparisonNewcomer"></canvas>
            </div>
            
            <div class="chart-container">
                <h2>Распределение очков по ролям (Newcomer)</h2>
                <canvas id="distributionByRoleNewcomer"></canvas>
            </div>
            
            {f'<div class="chart-container full-width"><h2>Топ-15 Leader (Newcomer)</h2><canvas id="top15LeaderNewcomer"></canvas></div>' if len(top_15_leader_newcomer) > 0 else ''}
            {f'<div class="chart-container full-width"><h2>Топ-15 Follower (Newcomer)</h2><canvas id="top15FollowerNewcomer"></canvas></div>' if len(top_15_follower_newcomer) > 0 else ''}
        </div>
    </div>
    
    <script>
        // Сравнение ролей в Novice
        const roleCompNoviceCtx = document.getElementById('roleComparisonNovice').getContext('2d');
        new Chart(roleCompNoviceCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    data: [{role_comparison_novice['Leader']}, {role_comparison_novice['Follower']}],
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
        
        // Распределение по ролям в Novice
        const distRoleNoviceCtx = document.getElementById('distributionByRoleNovice').getContext('2d');
        new Chart(distRoleNoviceCtx, {{
            type: 'bar',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    label: 'Среднее очков',
                    data: [{stats_novice_leader['mean']}, {stats_novice_follower['mean']}],
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
        
        // Топ-15 Leader Novice
        const top15LeaderNoviceCtx = document.getElementById('top15LeaderNovice').getContext('2d');
        new Chart(top15LeaderNoviceCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_15_leader_novice['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(top_15_leader_novice[points_col].astype(int).tolist())},
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
                    }}
                }}
            }}
        }});
        
        // Топ-15 Follower Novice
        const top15FollowerNoviceCtx = document.getElementById('top15FollowerNovice').getContext('2d');
        new Chart(top15FollowerNoviceCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_15_follower_novice['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(top_15_follower_novice[points_col].astype(int).tolist())},
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
                    }}
                }}
            }}
        }});
        
        // Сравнение ролей в Newcomer
        const roleCompNewcomerCtx = document.getElementById('roleComparisonNewcomer').getContext('2d');
        new Chart(roleCompNewcomerCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    data: [{role_comparison_newcomer['Leader']}, {role_comparison_newcomer['Follower']}],
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
        
        // Распределение по ролям в Newcomer
        const distRoleNewcomerCtx = document.getElementById('distributionByRoleNewcomer').getContext('2d');
        new Chart(distRoleNewcomerCtx, {{
            type: 'bar',
            data: {{
                labels: ['Leader', 'Follower'],
                datasets: [{{
                    label: 'Среднее очков',
                    data: [{stats_newcomer_leader['mean']}, {stats_newcomer_follower['mean']}],
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
        
        {f'''
        // Топ-15 Leader Newcomer
        const top15LeaderNewcomerCtx = document.getElementById('top15LeaderNewcomer').getContext('2d');
        new Chart(top15LeaderNewcomerCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_15_leader_newcomer['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(top_15_leader_newcomer[points_col].astype(int).tolist())},
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
                    }}
                }}
            }}
        }});
        ''' if len(top_15_leader_newcomer) > 0 else ''}
        
        {f'''
        // Топ-15 Follower Newcomer
        const top15FollowerNewcomerCtx = document.getElementById('top15FollowerNewcomer').getContext('2d');
        new Chart(top15FollowerNewcomerCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_15_follower_newcomer['display_name'].tolist(), ensure_ascii=False)},
                datasets: [{{
                    label: 'Очки',
                    data: {json.dumps(top_15_follower_newcomer[points_col].astype(int).tolist())},
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
                    }}
                }}
            }}
        }});
        ''' if len(top_15_follower_newcomer) > 0 else ''}
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Создан HTML дашборд: {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Использование: python create_advanced_charts.py <csv_file>")
        print("\nПример:")
        print("  python create_advanced_charts.py wsdc_points_2026-01-28_updated_with_pdf_with_pdf_with_novice_separated_fixed_specific_comprehensive_fixed_finalized.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл не найден: {csv_file}", flush=True)
        sys.exit(1)
    
    print("=" * 60)
    print("СОЗДАНИЕ РАСШИРЕННОГО АНАЛИЗА")
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
