# Инструкция по настройке Google Sheets API

Эта инструкция поможет настроить автоматическую загрузку данных в Google Таблицы.

## Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Войдите в свой Google аккаунт
3. Создайте новый проект:
   - Нажмите на выпадающий список проектов вверху
   - Нажмите "New Project"
   - Введите название проекта (например, "WSDC Points Uploader")
   - Нажмите "Create"

## Шаг 2: Включение Google Sheets API

1. В Google Cloud Console перейдите в "APIs & Services" > "Library"
2. Найдите "Google Sheets API"
3. Нажмите на него и нажмите "Enable"
4. Также включите "Google Drive API" (нужен для доступа к таблицам)

## Шаг 3: Создание Service Account

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "Service Account"
3. Заполните:
   - **Service account name**: например, "wsdc-uploader"
   - **Service account ID**: автоматически заполнится
   - **Description**: опционально
4. Нажмите "Create and Continue"
5. На шаге "Grant this service account access to project":
   - Роль: "Editor" (или можно оставить без роли)
   - Нажмите "Continue"
6. На шаге "Grant users access to this service account" можно пропустить, нажмите "Done"

## Шаг 4: Создание ключа (Credentials)

1. В списке Service Accounts найдите созданный аккаунт и нажмите на него
2. Перейдите на вкладку "Keys"
3. Нажмите "Add Key" > "Create new key"
4. Выберите формат "JSON"
5. Нажмите "Create"
6. Файл автоматически скачается (обычно называется `project-name-xxxxx.json`)

## Шаг 5: Сохранение credentials файла

1. Переименуйте скачанный JSON файл в `credentials.json`
2. Переместите его в папку с проектом (туда же, где `upload_to_google_sheets.py`)
3. **ВАЖНО**: Не коммитьте этот файл в git! Добавьте в `.gitignore`:
   ```
   credentials.json
   *.json
   ```

## Шаг 6: Предоставление доступа к таблице

1. Откройте скачанный JSON файл `credentials.json`
2. Найдите поле `"client_email"` - это email вашего Service Account (например, `wsdc-uploader@project-name.iam.gserviceaccount.com`)
3. Откройте вашу Google Таблицу
4. Нажмите кнопку "Share" (Поделиться) в правом верхнем углу
5. Вставьте email из `client_email` в поле "Add people and groups"
6. Дайте права "Editor" (Редактор)
7. Нажмите "Send" (Отправить)

## Шаг 7: Проверка установки библиотек

Убедитесь, что установлены необходимые библиотеки:

```bash
pip install gspread google-auth google-auth-oauthlib
```

Или используйте ваш `requirements.txt` (там уже есть эти библиотеки).

## Шаг 8: Использование

Теперь вы можете использовать скрипт:

```bash
python upload_to_google_sheets.py wsdc_points_finalized.csv
```

Или с указанием конкретной таблицы и листа:

```bash
python upload_to_google_sheets.py wsdc_points_finalized.csv 1ZaJXXCGQl8a1nrn1Bq6Wf2HjMI3dUGVLdb5vHT0P3LE "WSDC Points"
```

## Устранение проблем

### Ошибка: "FileNotFoundError: credentials.json"
- Убедитесь, что файл `credentials.json` находится в той же папке, что и скрипт
- Проверьте правильность имени файла

### Ошибка: "Permission denied" или "Access denied"
- Убедитесь, что вы предоставили доступ Service Account к таблице (Шаг 6)
- Проверьте, что email из `client_email` в credentials.json совпадает с тем, кому вы дали доступ

### Ошибка: "API not enabled"
- Убедитесь, что Google Sheets API и Google Drive API включены (Шаг 2)

### Ошибка: "Invalid credentials"
- Убедитесь, что JSON файл не повреждён
- Попробуйте создать новый ключ в Google Cloud Console

## Безопасность

⚠️ **ВАЖНО**: 
- Никогда не публикуйте файл `credentials.json` в открытом доступе
- Не коммитьте его в публичные репозитории
- Если файл был скомпрометирован, немедленно удалите ключ в Google Cloud Console и создайте новый

## Альтернативный способ: OAuth2 (для личного использования)

Если вы хотите использовать свой личный Google аккаунт вместо Service Account:

1. Создайте OAuth 2.0 Client ID в Google Cloud Console
2. Используйте библиотеку `google-auth-oauthlib` для авторизации
3. При первом запуске откроется браузер для авторизации
4. Токен будет сохранён для последующих использований

Но для автоматизации лучше использовать Service Account, так как он не требует интерактивной авторизации.
