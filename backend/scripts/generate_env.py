#!/usr/bin/env python3
"""
Скрипт для генерации безопасного .env файла
"""

import secrets
import os


def generate_secret_key():
    """Генерация криптографически стойкого SECRET_KEY"""
    return secrets.token_urlsafe(32)


def create_env_file():
    """Создание .env файла с безопасными настройками"""
    
    # Проверяем, существует ли .env файл
    if os.path.exists('.env'):
        response = input("⚠️  Файл .env уже существует. Заменить? (y/N): ")
        if response.lower() != 'y':
            print("Отменено.")
            return
    
    # Генерируем SECRET_KEY
    secret_key = generate_secret_key()
    
    # Запрашиваем данные для БД
    print("🔐 Настройка базы данных:")
    db_host = input("Хост БД (localhost): ") or "localhost"
    db_port = input("Порт БД (5432): ") or "5432"
    db_user = input("Пользователь БД: ")
    db_password = input("Пароль БД: ")
    db_name = input("Имя БД: ")
    
    # Выбираем окружение
    print("\n🌍 Окружение:")
    environment = input("Окружение (development/production) [development]: ") or "development"
    
    # Создаем содержимое .env файла
    env_content = f"""# Database settings
POSTGRESQL_HOST={db_host}
POSTGRESQL_PORT={db_port}
POSTGRESQL_USER={db_user}
POSTGRESQL_PASSWORD={db_password}
POSTGRESQL_DBNAME={db_name}

# Security settings
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT={environment}

# File upload settings
UPLOAD_DIR=media
MAX_FILE_SIZE=10485760

# CORS settings (comma-separated list)
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# Автоматически сгенерировано {secrets.token_hex(8)}
"""
    
    # Записываем в файл
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"""
✅ Файл .env успешно создан!

📋 Настройки:
- SECRET_KEY: {secret_key[:10]}...
- Environment: {environment}
- Database: {db_user}@{db_host}:{db_port}/{db_name}

🔒 Важные замечания:
1. Никогда не коммитьте .env файл в git
2. Используйте разные SECRET_KEY для разных окружений
3. Убедитесь, что .env добавлен в .gitignore
4. Для продакшена используйте HTTPS
""")


if __name__ == "__main__":
    create_env_file() 