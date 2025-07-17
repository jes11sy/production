# Инструкция по созданию .env файла

## Шаг 1: Создайте файл .env

Создайте файл `.env` в папке `backend/` со следующим содержимым:

```env
# Настройки базы данных (используйте ваши существующие данные)
POSTGRESQL_HOST=74ac89b6f8cc981b84f28f3b.twc1.net
POSTGRESQL_PORT=5432
POSTGRESQL_USER=gen_user
POSTGRESQL_PASSWORD=YOUR_SECURE_PASSWORD_CHANGE_ME
POSTGRESQL_DBNAME=default_db

# Настройки безопасности
SECRET_KEY=замените-на-сгенерированный-ключ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Настройки окружения
ENVIRONMENT=development

# Настройки файлов
UPLOAD_DIR=media
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=jpg,jpeg,png,gif,pdf,doc,docx,mp3,wav
MAX_FILES_PER_USER=100

# Настройки CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=app.log

# Настройки Rate Limiting
RATE_LIMIT_PER_MINUTE=100
LOGIN_ATTEMPTS_PER_HOUR=5

# Настройки IMAP для записей звонков (если используете)
RAMBLER_IMAP_USERNAME=your_email@rambler.ru
RAMBLER_IMAP_PASSWORD=your_password
```

## Шаг 2: Сгенерируйте SECRET_KEY

Выполните команду для генерации SECRET_KEY:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Скопируйте результат и замените `замените-на-сгенерированный-ключ` в файле .env.

## Шаг 3: Проверьте работу

Теперь приложение должно работать корректно. Если SECRET_KEY не установлен, система автоматически сгенерирует временный ключ с предупреждением.

## Альтернативный способ

Если вы не хотите устанавливать SECRET_KEY прямо сейчас, система будет работать с автоматически сгенерированным ключом, но будет показывать предупреждение.

Для продакшена обязательно установите постоянный SECRET_KEY! 