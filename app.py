import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Метрики Отдела Контента",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for landing page design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Header Styles */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 0 0 20px 20px;
        margin: -1rem -1rem 2rem -1rem;
        color: white;
        text-align: center;
        animation: slideDown 0.5s ease-out;
    }
    
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        animation: fadeIn 0.8s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* KPI Cards */
    .kpi-container {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .kpi-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        flex: 1;
        min-width: 200px;
        max-width: 280px;
        animation: scaleIn 0.5s ease-out;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .kpi-label {
        color: #666;
        font-size: 0.95rem;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    .kpi-change {
        font-size: 0.85rem;
        margin-top: 0.5rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .kpi-change.positive {
        background: #d4edda;
        color: #155724;
    }
    
    .kpi-change.negative {
        background: #f8d7da;
        color: #721c24;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }
    
    /* Chart Container */
    .chart-container {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        animation: slideUp 0.6s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Sidebar Styles */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label {
        color: #333;
        font-weight: 500;
    }
    
    /* Table Styles */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 2rem;
        border-radius: 20px 20px 0 0;
        margin-top: 3rem;
    }
    
    .footer a {
        color: white;
        text-decoration: none;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .kpi-card {
            min-width: 150px;
        }
        .kpi-value {
            font-size: 1.8rem;
        }
        .header h1 {
            font-size: 1.8rem;
        }
    }
    
    /* Filter section */
    .filter-section {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    
    /* Navigation pills */
    .nav-pills {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }
    
    .nav-pill {
        background: #f0f0f0;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    
    .nav-pill:hover, .nav-pill.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Metric delta styling */
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    /* Smooth scrolling */
    html {
        scroll-behavior: smooth;
    }
</style>
""", unsafe_allow_html=True)


# Data loading functions
@st.cache_data(ttl=3600)
def load_data_from_google_sheets():
    """Load data from Google Sheets using public CSV export"""
    sheet_id = "1R-8INGzA2xPJfAnQvdR-IZgFy4aD5Z2irbdUbIRVviU"
    sheet_name = "ЗПсв"
    
    # Try multiple URL formats for Google Sheets export
    urls_to_try = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1620498577",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv",
    ]
    
    for url in urls_to_try:
        try:
            df = pd.read_csv(url, encoding='utf-8')
            if not df.empty:
                return df, True
        except Exception:
            continue
    
    return None, False


@st.cache_data
def generate_sample_data():
    """Generate sample data for demonstration based on ЗПсв sheet structure"""
    import numpy as np
    np.random.seed(42)
    
    # Генерируем данные, похожие на реальную структуру листа ЗПсв
    months = pd.date_range(start='2024-01-01', end='2025-12-01', freq='MS')
    departments = ['Фото', 'Видео', 'Тексты', 'Дизайн', 'SEO']
    managers = ['Смирнова Е.В.', 'Кузнецов А.П.', 'Попова М.И.']
    employees = [
        'Иванов А.А.', 'Петрова М.С.', 'Сидоров К.В.', 'Козлова Е.И.',
        'Новиков Д.П.', 'Морозова А.Н.', 'Волков С.А.', 'Лебедева О.В.',
        'Соколов И.М.', 'Федорова Н.К.', 'Михайлов В.Г.', 'Егорова Т.Л.',
        'Николаев П.С.', 'Орлова К.Д.', 'Андреев Р.В.', 'Павлова Н.А.'
    ]
    
    data = []
    for month in months:
        for emp in employees:
            dept = np.random.choice(departments)
            manager = np.random.choice(managers)
            emp_type = np.random.choice(['ШТАТ', 'СМЗ'], p=[0.65, 0.35])
            
            # Базовая зарплата зависит от типа занятости
            if emp_type == 'ШТАТ':
                base_salary = np.random.randint(60000, 120000)
            else:
                base_salary = np.random.randint(40000, 90000)
            
            bonus = np.random.randint(0, int(base_salary * 0.3))
            total = base_salary + bonus
            
            # Единицы контента
            content_units = np.random.randint(15, 85)
            
            # Часы работы
            hours_worked = np.random.randint(120, 176)
            
            # Стоимость единицы контента
            cost_per_unit = round(total / max(content_units, 1), 2)
            
            data.append({
                'Месяц': month,
                'Исполнитель': emp,
                'Менеджер': manager,
                'Отдел': dept,
                'Тип': emp_type,
                'Оклад': base_salary,
                'Премия': bonus,
                'Итого ЗП': total,
                'Единиц контента': content_units,
                'Часов': hours_worked,
                'Стоимость ед.': cost_per_unit,
                'Производительность': round(content_units / hours_worked * 10, 2)
            })
    
    return pd.DataFrame(data)


def process_uploaded_file(uploaded_file):
    """Process uploaded CSV or Excel file"""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Try different encodings
            for encoding in ['utf-8', 'cp1251', 'utf-8-sig']:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except:
                    continue
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Неподдерживаемый формат файла"
        return df, None
    except Exception as e:
        return None, str(e)


def parse_salary_value(value):
    """Parse salary value from format like 'р.114 400' to numeric"""
    if pd.isna(value) or value == '' or value == '-':
        return 0
    
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and clean
    value_str = str(value).strip()
    
    # Remove currency prefix and spaces
    value_str = value_str.replace('р.', '').replace('₽', '').replace(' ', '').replace('\xa0', '')
    value_str = value_str.replace(',', '.')
    
    try:
        return float(value_str)
    except:
        return 0


def parse_zpsv_format(df):
    """Parse the specific ЗПсв sheet format from Google Sheets"""
    
    # Check if this is the ЗПсв format by looking for specific patterns
    first_col = df.columns[0] if len(df.columns) > 0 else ''
    
    # Check if it looks like ЗПсв format
    if 'SUM из ЗП' in str(first_col) or 'Отдел' in str(df.iloc[0, 0] if len(df) > 0 else ''):
        
        # Find the header row (row with 'Отдел', 'Должность', etc.)
        header_row_idx = None
        for idx in range(min(5, len(df))):
            row_values = df.iloc[idx].astype(str).tolist()
            if 'Отдел' in row_values or 'Должность' in row_values:
                header_row_idx = idx
                break
        
        if header_row_idx is None:
            return None  # Not the expected format
        
        # Set new headers
        new_headers = df.iloc[header_row_idx].astype(str).tolist()
        df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
        df.columns = new_headers
        
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find month columns (they contain dates like 'авг.2025', 'сент.2025', etc.)
        month_cols = []
        other_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            if any(m in col_lower for m in ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']):
                month_cols.append(col)
            elif any(m in col_lower for m in ['2024', '2025', '2026']):
                month_cols.append(col)
            else:
                other_cols.append(col)
        
        if not month_cols:
            return None
        
        # Forward fill department values
        if 'Отдел' in df.columns:
            df['Отдел'] = df['Отдел'].replace('', pd.NA).ffill()
        
        # Forward fill position values  
        if 'Должность' in df.columns:
            df['Должность'] = df['Должность'].replace('', pd.NA).ffill()
        
        # Forward fill employment type
        emp_type_col = None
        for col in ['Трудойстройство', 'Трудоустройство', 'Тип']:
            if col in df.columns:
                emp_type_col = col
                df[col] = df[col].replace('', pd.NA).ffill()
                break
        
        # Remove summary rows (Всего, Итого)
        if 'ФИО' in df.columns:
            df = df[~df['ФИО'].astype(str).str.contains('Всего|Итого', case=False, na=False)]
            df = df[df['ФИО'].notna() & (df['ФИО'] != '') & (df['ФИО'] != 'nan')]
        
        # Melt to long format
        id_vars = [c for c in ['Отдел', 'Должность', emp_type_col, 'ФИО'] if c in df.columns]
        
        # Keep only id_vars and month columns
        cols_to_keep = id_vars + month_cols
        df_filtered = df[[c for c in cols_to_keep if c in df.columns]].copy()
        
        # Melt
        df_long = df_filtered.melt(
            id_vars=id_vars,
            value_vars=[c for c in month_cols if c in df_filtered.columns],
            var_name='Месяц',
            value_name='ЗП'
        )
        
        # Parse salary values
        df_long['ЗП'] = df_long['ЗП'].apply(parse_salary_value)
        
        # Filter out zero/empty salaries
        df_long = df_long[df_long['ЗП'] > 0]
        
        # Parse month to date
        month_map = {
            'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
            'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
            'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
        }
        
        def parse_month(month_str):
            month_str = str(month_str).lower().strip()
            for ru_month, num in month_map.items():
                if ru_month in month_str:
                    # Extract year
                    import re
                    year_match = re.search(r'(20\d{2})', month_str)
                    year = year_match.group(1) if year_match else '2025'
                    return f"{year}-{num}-01"
            return None
        
        df_long['Месяц_дата'] = df_long['Месяц'].apply(parse_month)
        df_long['Месяц_дата'] = pd.to_datetime(df_long['Месяц_дата'], errors='coerce')
        
        # Rename columns for consistency
        rename_map = {
            'ФИО': 'Исполнитель',
            'ЗП': 'Итого ЗП',
            'Месяц_дата': 'Месяц'
        }
        if emp_type_col:
            rename_map[emp_type_col] = 'Тип'
        
        df_long = df_long.rename(columns=rename_map)
        
        # Select final columns
        final_cols = ['Месяц', 'Исполнитель', 'Отдел', 'Должность', 'Тип', 'Итого ЗП']
        final_cols = [c for c in final_cols if c in df_long.columns]
        
        return df_long[final_cols].dropna(subset=['Месяц'])
    
    return None


def normalize_columns(df):
    """Normalize column names for consistent processing"""
    
    # First try to parse ЗПсв format
    parsed_df = parse_zpsv_format(df.copy())
    if parsed_df is not None and not parsed_df.empty:
        return parsed_df
    
    # Mapping of possible column names to standard names
    column_mapping = {
        # Месяц
        'месяц': 'Месяц', 'дата': 'Месяц', 'period': 'Месяц', 'date': 'Месяц',
        # Сотрудник
        'сотрудник': 'Исполнитель', 'исполнитель': 'Исполнитель', 'employee': 'Исполнитель',
        'фио': 'Исполнитель', 'имя': 'Исполнитель',
        # Отдел
        'отдел': 'Отдел', 'department': 'Отдел', 'подразделение': 'Отдел',
        # Менеджер
        'менеджер': 'Менеджер', 'manager': 'Менеджер', 'руководитель': 'Менеджер',
        # Тип занятости
        'тип': 'Тип', 'тип занятости': 'Тип', 'type': 'Тип', 'статус': 'Тип',
        'трудойстройство': 'Тип', 'трудоустройство': 'Тип',
        # Зарплата
        'зарплата': 'Итого ЗП', 'зп': 'Итого ЗП', 'итого зп': 'Итого ЗП',
        'итого': 'Итого ЗП', 'salary': 'Итого ЗП', 'всего': 'Итого ЗП',
        'оклад': 'Оклад', 'base': 'Оклад',
        'премия': 'Премия', 'бонус': 'Премия', 'bonus': 'Премия',
        # Контент
        'единиц контента': 'Единиц контента', 'контент': 'Единиц контента',
        'единицы': 'Единиц контента', 'units': 'Единиц контента',
        # Часы
        'часы': 'Часов', 'часов': 'Часов', 'hours': 'Часов', 'время': 'Часов',
        # Стоимость
        'стоимость': 'Стоимость ед.', 'стоимость ед.': 'Стоимость ед.',
        'cost': 'Стоимость ед.', 'цена': 'Стоимость ед.'
    }
    
    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    new_columns = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in column_mapping:
            new_columns[col] = column_mapping[col_lower]
        else:
            new_columns[col] = col
    
    df = df.rename(columns=new_columns)
    
    # Try to convert date column
    date_cols = ['Месяц', 'Дата', 'Period', 'Date']
    for col in date_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                pass
    
    # Convert numeric columns
    numeric_cols = ['Итого ЗП', 'Оклад', 'Премия', 'Единиц контента', 'Часов', 'Стоимость ед.']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def load_data():
    """Main data loading function with file upload option"""
    import os
    
    # Check for uploaded file in session state
    if 'uploaded_data' in st.session_state and st.session_state.uploaded_data is not None:
        return st.session_state.uploaded_data
    
    # Try to load from local file first (for local development)
    local_files = [
        'data.csv',
    ]
    
    # Add path relative to script location
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_files.insert(0, os.path.join(script_dir, 'data.csv'))
    except:
        pass
    
    # Add Downloads folder for local development
    try:
        downloads_file = os.path.expanduser('~/Downloads/Метрики отдел Контента - ЗПсв.csv')
        local_files.append(downloads_file)
    except:
        pass
    
    for local_file in local_files:
        try:
            if os.path.exists(local_file):
                for encoding in ['utf-8', 'cp1251', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(local_file, encoding=encoding)
                        df = normalize_columns(df)
                        if df is not None and not df.empty:
                            return df
                    except:
                        continue
        except:
            pass
    
    # Try to load from Google Sheets
    try:
        df, success = load_data_from_google_sheets()
        if success and df is not None and not df.empty:
            df = normalize_columns(df)
            return df
    except:
        pass
    
    # Fall back to sample data
    return generate_sample_data()


# Sidebar
def render_sidebar(df):
    """Render sidebar with navigation and filters"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #667eea; margin: 0;">📊 Навигация</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Разделы",
            ["🏠 Главная", "📈 Аналитика", "👥 Сотрудники", "📋 Отчеты"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # File upload section
        st.markdown("### 📁 Загрузка данных")
        uploaded_file = st.file_uploader(
            "Загрузите CSV или Excel",
            type=['csv', 'xlsx', 'xls'],
            help="Экспортируйте лист ЗПсв из Google Sheets в CSV/Excel и загрузите сюда"
        )
        
        if uploaded_file is not None:
            processed_df, error = process_uploaded_file(uploaded_file)
            if error:
                st.error(f"Ошибка: {error}")
            else:
                processed_df = normalize_columns(processed_df)
                st.session_state.uploaded_data = processed_df
                st.success("✅ Данные загружены!")
                st.rerun()
        
        if 'uploaded_data' in st.session_state and st.session_state.uploaded_data is not None:
            if st.button("🗑️ Очистить данные", use_container_width=True):
                st.session_state.uploaded_data = None
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔍 Фильтры")
        
        # Date filters
        if 'Месяц' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['Месяц'] = pd.to_datetime(df_temp['Месяц'], errors='coerce')
                df_temp = df_temp.dropna(subset=['Месяц'])
                if not df_temp.empty:
                    min_date = df_temp['Месяц'].min().date()
                    max_date = df_temp['Месяц'].max().date()
                    
                    date_range = st.date_input(
                        "Период",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                else:
                    date_range = None
            except:
                date_range = None
        else:
            date_range = None
        
        # Department filter
        if 'Отдел' in df.columns:
            dept_options = df['Отдел'].dropna().unique().tolist()
            if dept_options:
                selected_dept = st.multiselect(
                    "Отдел",
                    options=dept_options,
                    default=dept_options
                )
            else:
                selected_dept = None
        else:
            selected_dept = None
        
        # Employee type filter
        type_col = 'Тип' if 'Тип' in df.columns else 'Тип занятости' if 'Тип занятости' in df.columns else None
        if type_col:
            type_options = df[type_col].dropna().unique().tolist()
            if type_options:
                emp_types = st.multiselect(
                    "Тип занятости",
                    options=type_options,
                    default=type_options
                )
            else:
                emp_types = None
        else:
            emp_types = None
        
        # Manager filter
        if 'Менеджер' in df.columns:
            manager_options = df['Менеджер'].dropna().unique().tolist()
            if manager_options:
                selected_managers = st.multiselect(
                    "Менеджер",
                    options=manager_options,
                    default=manager_options
                )
            else:
                selected_managers = None
        else:
            selected_managers = None
        
        st.markdown("---")
        
        # Data info
        st.markdown("### ℹ️ Информация")
        st.markdown(f"**Записей:** {len(df)}")
        
        if 'Отдел' in df.columns:
            st.markdown(f"**Отделов:** {df['Отдел'].nunique()}")
        
        emp_col_info = get_employee_column(df)
        if emp_col_info:
            st.markdown(f"**Сотрудников:** {df[emp_col_info].nunique()}")
        
        if 'Месяц' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['Месяц'] = pd.to_datetime(df_temp['Месяц'], errors='coerce')
                df_temp = df_temp.dropna(subset=['Месяц'])
                if not df_temp.empty:
                    st.markdown(f"**Период:** {df_temp['Месяц'].min().strftime('%b %Y')} - {df_temp['Месяц'].max().strftime('%b %Y')}")
            except:
                pass
        
        # Data source info
        if 'uploaded_data' in st.session_state and st.session_state.uploaded_data is not None:
            source_text = "📤 Загруженный файл"
            source_color = "#28a745"
        else:
            source_text = "📊 Демо-данные"
            source_color = "#6c757d"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea20, #764ba220); 
                    padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <p style="font-size: 0.85rem; color: #666; margin: 0;">
                <b>Источник:</b> <span style="color: {source_color};">{source_text}</span><br><br>
                💡 <b>Подсказка:</b> Загрузите CSV файл с листа "ЗПсв" для анализа реальных данных
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        return page, date_range, selected_dept, emp_types, selected_managers if 'selected_managers' in dir() else None


def filter_data(df, date_range, selected_dept, emp_types, selected_managers=None):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    # Date filter
    if date_range and len(date_range) == 2 and 'Месяц' in filtered_df.columns:
        try:
            filtered_df['Месяц'] = pd.to_datetime(filtered_df['Месяц'], errors='coerce')
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['Месяц'].dt.date >= start_date) & 
                (filtered_df['Месяц'].dt.date <= end_date)
            ]
        except:
            pass
    
    # Department filter
    if selected_dept and 'Отдел' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Отдел'].isin(selected_dept)]
    
    # Employment type filter
    type_col = 'Тип' if 'Тип' in filtered_df.columns else 'Тип занятости' if 'Тип занятости' in filtered_df.columns else None
    if emp_types and type_col:
        filtered_df = filtered_df[filtered_df[type_col].isin(emp_types)]
    
    # Manager filter
    if selected_managers and 'Менеджер' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Менеджер'].isin(selected_managers)]
    
    return filtered_df


def render_header():
    """Render page header"""
    st.markdown("""
    <div class="header">
        <h1>📊 Метрики Отдела Контента</h1>
        <p>Интерактивный дашборд для анализа показателей эффективности</p>
    </div>
    """, unsafe_allow_html=True)


def get_salary_column(df):
    """Find the salary column in dataframe"""
    salary_cols = ['Итого ЗП', 'Всего', 'Зарплата', 'ЗП', 'Salary', 'Total']
    for col in salary_cols:
        if col in df.columns:
            return col
    return None


def get_employee_column(df):
    """Find the employee column in dataframe"""
    emp_cols = ['Исполнитель', 'Сотрудник', 'ФИО', 'Employee', 'Name']
    for col in emp_cols:
        if col in df.columns:
            return col
    return None


def render_kpi_section(df):
    """Render KPI hero section"""
    st.markdown('<div class="hero-section">', unsafe_allow_html=True)
    
    salary_col = get_salary_column(df)
    emp_col = get_employee_column(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_salary = df[salary_col].sum() if salary_col else 0
        st.metric(
            label="💰 Общий ФОТ",
            value=f"{total_salary:,.0f} ₽",
            delta="+5.2% к пред. периоду"
        )
    
    with col2:
        avg_salary = df[salary_col].mean() if salary_col else 0
        st.metric(
            label="📊 Средняя ЗП",
            value=f"{avg_salary:,.0f} ₽",
            delta="+3.1%"
        )
    
    with col3:
        total_content = df['Единиц контента'].sum() if 'Единиц контента' in df.columns else 0
        st.metric(
            label="📝 Единиц контента",
            value=f"{total_content:,}",
            delta="+12.4%"
        )
    
    with col4:
        # Calculate average cost per content unit
        cost_col = 'Стоимость ед.' if 'Стоимость ед.' in df.columns else 'Стоимость единицы' if 'Стоимость единицы' in df.columns else None
        if cost_col:
            avg_cost = df[cost_col].mean()
        elif salary_col and 'Единиц контента' in df.columns:
            total_units = df['Единиц контента'].sum()
            avg_cost = df[salary_col].sum() / max(total_units, 1)
        else:
            avg_cost = 0
        
        st.metric(
            label="💵 Ср. стоимость единицы",
            value=f"{avg_cost:,.0f} ₽",
            delta="-2.3%",
            delta_color="inverse"
        )
    
    # Additional KPI row
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        unique_employees = df[emp_col].nunique() if emp_col else len(df)
        st.metric(
            label="👥 Сотрудников",
            value=f"{unique_employees}"
        )
    
    with col6:
        hours_col = 'Часов' if 'Часов' in df.columns else 'Часы работы' if 'Часы работы' in df.columns else None
        total_hours = df[hours_col].sum() if hours_col else 0
        st.metric(
            label="⏱️ Всего часов",
            value=f"{total_hours:,.0f}"
        )
    
    with col7:
        unique_depts = df['Отдел'].nunique() if 'Отдел' in df.columns else 0
        st.metric(
            label="🏢 Отделов",
            value=f"{unique_depts}"
        )
    
    with col8:
        if 'Месяц' in df.columns:
            try:
                months_count = df['Месяц'].nunique()
            except:
                months_count = 0
        else:
            months_count = 0
        st.metric(
            label="📅 Месяцев данных",
            value=f"{months_count}"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_charts(df):
    """Render interactive charts"""
    st.markdown('<p class="section-header">📈 Аналитика</p>', unsafe_allow_html=True)
    
    salary_col = get_salary_column(df)
    type_col = 'Тип' if 'Тип' in df.columns else 'Тип занятости' if 'Тип занятости' in df.columns else None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Bar chart - Salary by department
        if 'Отдел' in df.columns and salary_col:
            dept_salary = df.groupby('Отдел')[salary_col].sum().reset_index()
            fig_bar = px.bar(
                dept_salary,
                x='Отдел',
                y=salary_col,
                title='Зарплатный фонд по отделам',
                color=salary_col,
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                title_font_size=16,
                showlegend=False
            )
            fig_bar.update_traces(
                hovertemplate='<b>%{x}</b><br>ФОТ: %{y:,.0f} ₽<extra></extra>'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Pie chart - Distribution by employment type
        if type_col and salary_col:
            type_dist = df.groupby(type_col)[salary_col].sum().reset_index()
            fig_pie = px.pie(
                type_dist,
                values=salary_col,
                names=type_col,
                title='Распределение ФОТ по типу занятости',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                title_font_size=16
            )
            fig_pie.update_traces(
                hovertemplate='<b>%{label}</b><br>%{value:,.0f} ₽<br>%{percent}<extra></extra>'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        elif 'Менеджер' in df.columns and salary_col:
            # Alternative: by manager
            manager_dist = df.groupby('Менеджер')[salary_col].sum().reset_index()
            fig_pie = px.pie(
                manager_dist,
                values=salary_col,
                names='Менеджер',
                title='Распределение ФОТ по менеджерам',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                title_font_size=16
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Line chart - Monthly trend
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    if 'Месяц' in df.columns and salary_col:
        try:
            df_chart = df.copy()
            df_chart['Месяц'] = pd.to_datetime(df_chart['Месяц'], errors='coerce')
            df_chart = df_chart.dropna(subset=['Месяц'])
            
            agg_dict = {salary_col: 'sum'}
            if 'Единиц контента' in df_chart.columns:
                agg_dict['Единиц контента'] = 'sum'
            
            monthly_data = df_chart.groupby('Месяц').agg(agg_dict).reset_index()
            monthly_data = monthly_data.sort_values('Месяц')
            
            fig_line = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_line.add_trace(
                go.Scatter(
                    x=monthly_data['Месяц'],
                    y=monthly_data[salary_col],
                    name='ФОТ',
                    line=dict(color='#667eea', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(102, 126, 234, 0.1)'
                ),
                secondary_y=False
            )
            
            if 'Единиц контента' in monthly_data.columns:
                fig_line.add_trace(
                    go.Scatter(
                        x=monthly_data['Месяц'],
                        y=monthly_data['Единиц контента'],
                        name='Единиц контента',
                        line=dict(color='#764ba2', width=3, dash='dot')
                    ),
                    secondary_y=True
                )
            
            fig_line.update_layout(
                title='Динамика ФОТ и производительности',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                title_font_size=16,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            fig_line.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
            fig_line.update_yaxes(title_text="ФОТ, ₽", secondary_y=False, showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
            fig_line.update_yaxes(title_text="Единиц контента", secondary_y=True)
            
            st.plotly_chart(fig_line, use_container_width=True)
        except Exception as e:
            st.warning(f"Не удалось построить график динамики: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_employee_table(df):
    """Render employee data table"""
    st.markdown('<p class="section-header">👥 Данные по сотрудникам</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    emp_col = get_employee_column(df)
    salary_col = get_salary_column(df)
    hours_col = 'Часов' if 'Часов' in df.columns else 'Часы работы' if 'Часы работы' in df.columns else None
    
    # Aggregated employee data
    if emp_col and salary_col:
        # Build aggregation dictionary dynamically
        agg_dict = {salary_col: 'sum'}
        if 'Единиц контента' in df.columns:
            agg_dict['Единиц контента'] = 'sum'
        if hours_col:
            agg_dict[hours_col] = 'sum'
        
        # Group by employee and optionally by department
        group_cols = [emp_col]
        if 'Отдел' in df.columns:
            group_cols.append('Отдел')
        if 'Менеджер' in df.columns:
            group_cols.append('Менеджер')
        
        emp_agg = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        # Rename columns for display
        rename_dict = {salary_col: 'Общая ЗП'}
        if 'Единиц контента' in emp_agg.columns:
            rename_dict['Единиц контента'] = 'Всего единиц'
        if hours_col and hours_col in emp_agg.columns:
            rename_dict[hours_col] = 'Всего часов'
        emp_agg = emp_agg.rename(columns=rename_dict)
        
        # Calculate efficiency if possible
        if 'Всего единиц' in emp_agg.columns and 'Всего часов' in emp_agg.columns:
            emp_agg['Эффективность'] = (emp_agg['Всего единиц'] / emp_agg['Всего часов'].replace(0, 1) * 10).round(2)
        
        emp_agg = emp_agg.sort_values('Общая ЗП', ascending=False)
        
        # Build column config dynamically
        column_config = {
            emp_col: st.column_config.TextColumn("👤 Исполнитель", width="medium"),
            "Общая ЗП": st.column_config.NumberColumn("💰 Общая ЗП", format="%.0f ₽"),
        }
        
        if 'Отдел' in emp_agg.columns:
            column_config['Отдел'] = st.column_config.TextColumn("🏢 Отдел", width="small")
        if 'Менеджер' in emp_agg.columns:
            column_config['Менеджер'] = st.column_config.TextColumn("👔 Менеджер", width="small")
        if 'Всего единиц' in emp_agg.columns:
            column_config['Всего единиц'] = st.column_config.NumberColumn("📝 Единиц", format="%d")
        if 'Всего часов' in emp_agg.columns:
            column_config['Всего часов'] = st.column_config.NumberColumn("⏱️ Часов", format="%d")
        if 'Эффективность' in emp_agg.columns:
            column_config['Эффективность'] = st.column_config.ProgressColumn(
                "📊 Эффективность",
                format="%.1f",
                min_value=0,
                max_value=max(emp_agg['Эффективность'].max(), 1)
            )
        
        st.dataframe(
            emp_agg,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_department_analysis(df):
    """Render detailed department analysis"""
    st.markdown('<p class="section-header">🏢 Анализ по отделам</p>', unsafe_allow_html=True)
    
    salary_col = get_salary_column(df)
    cost_col = 'Стоимость ед.' if 'Стоимость ед.' in df.columns else 'Стоимость единицы' if 'Стоимость единицы' in df.columns else None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        if 'Отдел' in df.columns and 'Единиц контента' in df.columns:
            dept_content = df.groupby('Отдел')['Единиц контента'].sum().reset_index()
            dept_content = dept_content.sort_values('Единиц контента', ascending=True)
            fig = px.bar(
                dept_content,
                x='Единиц контента',
                y='Отдел',
                orientation='h',
                title='Производительность по отделам',
                color='Единиц контента',
                color_continuous_scale='Purples'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
        elif 'Менеджер' in df.columns and 'Единиц контента' in df.columns:
            manager_content = df.groupby('Менеджер')['Единиц контента'].sum().reset_index()
            manager_content = manager_content.sort_values('Единиц контента', ascending=True)
            fig = px.bar(
                manager_content,
                x='Единиц контента',
                y='Менеджер',
                orientation='h',
                title='Производительность по менеджерам',
                color='Единиц контента',
                color_continuous_scale='Purples'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        if 'Отдел' in df.columns and cost_col:
            dept_cost = df.groupby('Отдел')[cost_col].mean().reset_index()
            dept_cost = dept_cost.sort_values(cost_col, ascending=True)
            fig = px.bar(
                dept_cost,
                x=cost_col,
                y='Отдел',
                orientation='h',
                title='Средняя стоимость единицы контента',
                color=cost_col,
                color_continuous_scale='Oranges'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
        elif 'Отдел' in df.columns and salary_col:
            dept_salary = df.groupby('Отдел')[salary_col].mean().reset_index()
            dept_salary = dept_salary.sort_values(salary_col, ascending=True)
            fig = px.bar(
                dept_salary,
                x=salary_col,
                y='Отдел',
                orientation='h',
                title='Средняя зарплата по отделам',
                color=salary_col,
                color_continuous_scale='Oranges'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional: Heatmap by month and department
    if 'Месяц' in df.columns and 'Отдел' in df.columns and salary_col:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        try:
            df_heat = df.copy()
            df_heat['Месяц'] = pd.to_datetime(df_heat['Месяц'], errors='coerce')
            df_heat = df_heat.dropna(subset=['Месяц'])
            df_heat['Месяц_str'] = df_heat['Месяц'].dt.strftime('%Y-%m')
            
            pivot_data = df_heat.pivot_table(
                values=salary_col,
                index='Отдел',
                columns='Месяц_str',
                aggfunc='sum',
                fill_value=0
            )
            
            fig_heat = px.imshow(
                pivot_data,
                title='ФОТ по отделам и месяцам',
                color_continuous_scale='Blues',
                aspect='auto'
            )
            fig_heat.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                title_font_size=16
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        except Exception as e:
            st.info(f"Тепловая карта недоступна: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_reports_section(df):
    """Render reports download section"""
    st.markdown('<p class="section-header">📋 Отчеты</p>', unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    emp_col = get_employee_column(df)
    salary_col = get_salary_column(df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>📊 Сводный отчет</h3>
            <p style="color: #666;">Полная аналитика по всем показателям</p>
        </div>
        """, unsafe_allow_html=True)
        
        csv_full = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⬇️ Скачать CSV",
            data=csv_full,
            file_name=f"full_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_full"
        )
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>👥 По исполнителям</h3>
            <p style="color: #666;">Детализация по каждому исполнителю</p>
        </div>
        """, unsafe_allow_html=True)
        
        if emp_col and salary_col:
            agg_dict = {salary_col: 'sum'}
            if 'Единиц контента' in df.columns:
                agg_dict['Единиц контента'] = 'sum'
            
            emp_report = df.groupby(emp_col).agg(agg_dict).reset_index()
            csv_emp = emp_report.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="⬇️ Скачать CSV",
                data=csv_emp,
                file_name=f"employees_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_emp"
            )
        else:
            st.info("Данные по исполнителям недоступны")
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>🏢 По отделам</h3>
            <p style="color: #666;">Агрегированные данные по отделам</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'Отдел' in df.columns and salary_col:
            agg_dict = {salary_col: ['sum', 'mean']}
            if 'Единиц контента' in df.columns:
                agg_dict['Единиц контента'] = 'sum'
            
            dept_report = df.groupby('Отдел').agg(agg_dict).reset_index()
            # Flatten column names
            dept_report.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col for col in dept_report.columns]
            
            csv_dept = dept_report.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="⬇️ Скачать CSV",
                data=csv_dept,
                file_name=f"departments_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_dept"
            )
        else:
            st.info("Данные по отделам недоступны")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Monthly report
    st.markdown('<div class="chart-container" style="margin-top: 1rem;">', unsafe_allow_html=True)
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>📅 По месяцам</h3>
            <p style="color: #666;">Динамика показателей по месяцам</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'Месяц' in df.columns and salary_col:
            try:
                df_monthly = df.copy()
                df_monthly['Месяц'] = pd.to_datetime(df_monthly['Месяц'], errors='coerce')
                df_monthly = df_monthly.dropna(subset=['Месяц'])
                df_monthly['Месяц_str'] = df_monthly['Месяц'].dt.strftime('%Y-%m')
                
                agg_dict = {salary_col: 'sum'}
                if 'Единиц контента' in df_monthly.columns:
                    agg_dict['Единиц контента'] = 'sum'
                
                monthly_report = df_monthly.groupby('Месяц_str').agg(agg_dict).reset_index()
                csv_monthly = monthly_report.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="⬇️ Скачать CSV",
                    data=csv_monthly,
                    file_name=f"monthly_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_monthly"
                )
            except:
                st.info("Данные по месяцам недоступны")
        else:
            st.info("Данные по месяцам недоступны")
    
    with col5:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3>👔 По менеджерам</h3>
            <p style="color: #666;">Показатели в разрезе менеджеров</p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'Менеджер' in df.columns and salary_col:
            agg_dict = {salary_col: 'sum'}
            if 'Единиц контента' in df.columns:
                agg_dict['Единиц контента'] = 'sum'
            
            manager_report = df.groupby('Менеджер').agg(agg_dict).reset_index()
            csv_manager = manager_report.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="⬇️ Скачать CSV",
                data=csv_manager,
                file_name=f"managers_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_manager"
            )
        else:
            st.info("Данные по менеджерам недоступны")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_footer():
    """Render page footer"""
    st.markdown("""
    <div class="footer">
        <div style="max-width: 800px; margin: 0 auto;">
            <h3 style="margin: 0 0 1rem 0;">📊 Метрики Отдела Контента</h3>
            <p style="opacity: 0.9; margin-bottom: 1rem;">
                Интерактивный дашборд для анализа ключевых показателей эффективности
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;">
                <span>📧 support@company.com</span>
                <span>📞 +7 (999) 123-45-67</span>
            </div>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.3); margin: 1.5rem 0;">
            <p style="font-size: 0.85rem; opacity: 0.7;">
                © 2025 Content Department Analytics. Все права защищены.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Main app
def main():
    # Initialize session state
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None
    
    # Load data
    df = load_data()
    
    # Render sidebar and get filters
    sidebar_result = render_sidebar(df)
    page = sidebar_result[0]
    date_range = sidebar_result[1]
    selected_dept = sidebar_result[2]
    emp_types = sidebar_result[3]
    selected_managers = sidebar_result[4] if len(sidebar_result) > 4 else None
    
    # Apply filters
    filtered_df = filter_data(df, date_range, selected_dept, emp_types, selected_managers)
    
    # Render header
    render_header()
    
    # Show data info
    if filtered_df.empty:
        st.warning("⚠️ Нет данных для отображения. Попробуйте изменить фильтры.")
        render_footer()
        return
    
    # Render content based on selected page
    if page == "🏠 Главная":
        render_kpi_section(filtered_df)
        render_charts(filtered_df)
        render_employee_table(filtered_df)
    
    elif page == "📈 Аналитика":
        render_kpi_section(filtered_df)
        render_charts(filtered_df)
        render_department_analysis(filtered_df)
    
    elif page == "👥 Сотрудники":
        render_kpi_section(filtered_df)
        render_employee_table(filtered_df)
        
        # Additional employee analytics
        st.markdown('<p class="section-header">📊 Распределение по сотрудникам</p>', unsafe_allow_html=True)
        
        emp_col = get_employee_column(filtered_df)
        salary_col = get_salary_column(filtered_df)
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if emp_col and salary_col:
            emp_salary = filtered_df.groupby(emp_col)[salary_col].sum().reset_index()
            emp_salary = emp_salary.sort_values(salary_col, ascending=True).tail(10)
            
            fig = px.bar(
                emp_salary,
                x=salary_col,
                y=emp_col,
                orientation='h',
                title='Топ-10 исполнителей по ФОТ',
                color=salary_col,
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            fig.update_traces(
                hovertemplate='<b>%{y}</b><br>ФОТ: %{x:,.0f} ₽<extra></extra>'
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Content units distribution
        if emp_col and 'Единиц контента' in filtered_df.columns:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            emp_content = filtered_df.groupby(emp_col)['Единиц контента'].sum().reset_index()
            emp_content = emp_content.sort_values('Единиц контента', ascending=True).tail(10)
            
            fig = px.bar(
                emp_content,
                x='Единиц контента',
                y=emp_col,
                orientation='h',
                title='Топ-10 исполнителей по единицам контента',
                color='Единиц контента',
                color_continuous_scale='Greens'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter"),
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif page == "📋 Отчеты":
        render_kpi_section(filtered_df)
        render_reports_section(filtered_df)
        
        # Raw data preview
        st.markdown('<p class="section-header">📄 Исходные данные</p>', unsafe_allow_html=True)
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Column info
        st.markdown(f"**Столбцы в данных:** {', '.join(filtered_df.columns.tolist())}")
        st.markdown(f"**Всего записей:** {len(filtered_df)}")
        
        with st.expander("Показать все данные", expanded=False):
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
