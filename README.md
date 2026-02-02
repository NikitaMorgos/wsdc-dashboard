# 📊 Метрики Отдела Контента - Dashboard

Интерактивный Streamlit дашборд для анализа метрик отдела контента.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

## 🚀 Демо

После деплоя на Streamlit Cloud ваш дашборд будет доступен по публичному URL.

## ✨ Возможности

- **Hero-секция с KPI** - общий ФОТ, средняя ЗП, количество сотрудников
- **Интерактивные фильтры** - по датам, отделам, типу занятости
- **Plotly графики**:
  - Bar chart - ФОТ по отделам
  - Pie chart - распределение по типу занятости
  - Line chart - динамика по месяцам
  - Heatmap - ФОТ по отделам и месяцам
- **Responsive таблицы** - данные по сотрудникам с сортировкой
- **Экспорт отчетов** - скачивание в CSV
- **Landing page дизайн** - градиенты, анимации, современный UI

## 📋 Разделы

| Раздел | Описание |
|--------|----------|
| 🏠 Главная | Обзор KPI, основные графики, таблица сотрудников |
| 📈 Аналитика | Детальный анализ по отделам, тепловая карта |
| 👥 Сотрудники | Топ исполнителей по ФОТ и производительности |
| 📋 Отчеты | Скачивание отчетов в различных разрезах |

## 🛠 Локальная установка

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/dashboard-content.git
cd dashboard-content

# Установить зависимости
pip install -r requirements.txt

# Запустить
streamlit run app.py
```

## ☁️ Деплой на Streamlit Cloud

1. Загрузите этот репозиторий на GitHub
2. Перейдите на [streamlit.io/cloud](https://streamlit.io/cloud)
3. Нажмите "New app"
4. Выберите репозиторий и файл `app.py`
5. Нажмите "Deploy"

Приложение будет доступно по URL: `https://YOUR_APP.streamlit.app`

## 📊 Загрузка данных

### Из Google Sheets (лист "ЗПсв")

1. Откройте таблицу [Метрики отдел Контента](https://docs.google.com/spreadsheets/d/1R-8INGzA2xPJfAnQvdR-IZgFy4aD5Z2irbdUbIRVviU/)
2. Перейдите на лист **"ЗПсв"**
3. **Файл → Скачать → CSV**
4. Загрузите файл через sidebar в приложении

### Поддерживаемый формат

Приложение автоматически распознает формат листа ЗПсв:
- Зарплаты в формате `р.XXX XXX`
- Месяцы: `авг.2025`, `сент.2025` и т.д.
- Отделы: 3D, Инфографика, Фоторедакция, Менеджерский состав
- Типы занятости: СМЗ, Штат

## 🎨 Дизайн

- **Цветовая схема**: Purple gradient (#667eea → #764ba2)
- **Шрифт**: Inter (Google Fonts)
- **Анимации**: CSS transitions и keyframes
- **Адаптивность**: Mobile-first responsive

## 📁 Структура проекта

```
dashboard-content/
├── app.py                 # Основное приложение
├── requirements.txt       # Python зависимости
├── README.md             # Документация
├── .gitignore            # Игнорируемые файлы
└── .streamlit/
    └── config.toml       # Настройки Streamlit
```

## 📝 Лицензия

MIT License

---

Создано с ❤️ используя [Streamlit](https://streamlit.io) и [Plotly](https://plotly.com)
