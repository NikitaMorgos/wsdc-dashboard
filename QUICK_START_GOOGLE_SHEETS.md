# Быстрый старт: Загрузка данных в Google Таблицу

## Краткая инструкция (5 минут)

### 1. Создайте Service Account в Google Cloud

1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект (или выберите существующий)
3. Включите **Google Sheets API** и **Google Drive API**:
   - "APIs & Services" > "Library"
   - Найдите и включите оба API
4. Создайте Service Account:
   - "APIs & Services" > "Credentials" > "Create Credentials" > "Service Account"
   - Название: `wsdc-uploader`
   - Нажмите "Create and Continue" > "Done"
5. Создайте ключ:
   - Откройте созданный Service Account
   - Вкладка "Keys" > "Add Key" > "Create new key"
   - Формат: **JSON**
   - Файл скачается автоматически

### 2. Сохраните credentials

1. Переименуйте скачанный файл в `credentials.json`
2. Переместите его в папку с проектом (рядом с `upload_to_google_sheets.py`)

### 3. Дайте доступ к таблице

1. Откройте `credentials.json` в текстовом редакторе
2. Найдите `"client_email"` (например: `wsdc-uploader@project-123.iam.gserviceaccount.com`)
3. Откройте вашу Google Таблицу
4. Нажмите "Поделиться" (Share)
5. Вставьте email из `client_email`
6. Дайте права "Редактор" (Editor)
7. Нажмите "Отправить"

### 4. Используйте скрипт

```bash
# Загрузить данные в таблицу
python upload_to_google_sheets.py wsdc_points_finalized.csv

# Или с указанием конкретного листа
python upload_to_google_sheets.py wsdc_points_finalized.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE "WSDC Points"
```

## Полная инструкция

См. файл `GOOGLE_SHEETS_SETUP.md` для подробной инструкции.

## Что делает скрипт?

- Читает CSV файл
- Подключается к Google Таблице через API
- Загружает данные в указанный лист
- Сохраняет форматирование (заголовки, данные)

## Параметры скрипта

```bash
python upload_to_google_sheets.py <csv_file> [sheet_id] [sheet_name] [start_cell]
```

- `csv_file` - путь к CSV файлу (обязательно)
- `sheet_id` - ID Google Таблицы (опционально, по умолчанию из DEFAULT_SHEET_ID)
- `sheet_name` - название листа (опционально, по умолчанию первый лист)
- `start_cell` - начальная ячейка (опционально, по умолчанию A1)

## Примеры

```bash
# Простой вариант (использует DEFAULT_SHEET_ID)
python upload_to_google_sheets.py data.csv

# С указанием таблицы
python upload_to_google_sheets.py data.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE

# С указанием листа
python upload_to_google_sheets.py data.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE "WSDC Points"

# С указанием начальной ячейки
python upload_to_google_sheets.py data.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE "WSDC Points" A1
```

## Автоматическая загрузка после обработки

Вы можете интегрировать загрузку в процесс обработки данных, добавив в конец скрипта `finalize_data.py`:

```python
# В конце функции finalize_data()
if upload_to_sheets:
    from auto_upload_to_sheets import auto_upload
    auto_upload(output_file, sheet_id="YOUR_SHEET_ID", sheet_name="WSDC Points")
```

## Устранение проблем

**Ошибка: "FileNotFoundError: credentials.json"**
- Убедитесь, что файл `credentials.json` находится в папке со скриптом

**Ошибка: "Permission denied"**
- Проверьте, что вы дали доступ Service Account к таблице (см. шаг 3)

**Ошибка: "API not enabled"**
- Убедитесь, что Google Sheets API и Google Drive API включены в Google Cloud Console
