#!/bin/bash

# =========================================
# 👤 СОЗДАНИЕ АДМИН ПОЛЬЗОВАТЕЛЯ
# =========================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

PROJECT_DIR="/opt/leadschem"

# Проверка что мы на production сервере
if [ ! -d "$PROJECT_DIR" ]; then
    error "❌ Директория проекта $PROJECT_DIR не найдена"
fi

cd $PROJECT_DIR

log "👤 Создание админ пользователя..."

# Получение данных от пользователя
echo ""
read -p "📝 Введите логин админа: " ADMIN_LOGIN
read -s -p "🔐 Введите пароль админа: " ADMIN_PASSWORD
echo ""
read -p "📧 Введите email админа: " ADMIN_EMAIL
read -p "👤 Введите имя админа: " ADMIN_NAME

# Проверка данных
if [ -z "$ADMIN_LOGIN" ] || [ -z "$ADMIN_PASSWORD" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_NAME" ]; then
    error "❌ Все поля обязательны для заполнения"
fi

# Проверка длины пароля
if [ ${#ADMIN_PASSWORD} -lt 8 ]; then
    error "❌ Пароль должен содержать минимум 8 символов"
fi

log "🔍 Проверка состояния контейнеров..."

# Проверка что backend контейнер запущен
if ! docker compose -f deployment/docker-compose.production.yml ps | grep -q "leadschem_backend.*Up"; then
    error "❌ Backend контейнер не запущен. Запустите сначала: docker compose -f deployment/docker-compose.production.yml up -d"
fi

# Создание временного скрипта для выполнения внутри контейнера
cat > /tmp/create_admin.py << EOF
import asyncio
import os
import sys
sys.path.append('/app')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_async_session
from app.core.security import get_password_hash

async def create_admin():
    async for session in get_async_session():
        try:
            # Проверяем существует ли пользователь
            result = await session.execute(
                text("SELECT id FROM users WHERE login = :login"),
                {"login": "$ADMIN_LOGIN"}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print("⚠️  Пользователь с таким логином уже существует!")
                return False
            
            # Получаем ID роли admin
            result = await session.execute(text("SELECT id FROM roles WHERE name = 'admin'"))
            admin_role = result.fetchone()
            
            if not admin_role:
                print("❌ Роль 'admin' не найдена в базе данных")
                return False
            
            admin_role_id = admin_role[0]
            
            # Хешируем пароль
            password_hash = get_password_hash("$ADMIN_PASSWORD")
            
            # Создаем пользователя
            await session.execute(text("""
                INSERT INTO users (login, password_hash, email, name, role_id, is_active, created_at, updated_at)
                VALUES (:login, :password_hash, :email, :name, :role_id, true, NOW(), NOW())
            """), {
                "login": "$ADMIN_LOGIN",
                "password_hash": password_hash,
                "email": "$ADMIN_EMAIL", 
                "name": "$ADMIN_NAME",
                "role_id": admin_role_id
            })
            
            await session.commit()
            print("✅ Админ пользователь успешно создан!")
            print(f"📝 Логин: $ADMIN_LOGIN")
            print(f"📧 Email: $ADMIN_EMAIL")
            print(f"👤 Имя: $ADMIN_NAME")
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(create_admin())
    sys.exit(0 if success else 1)
EOF

log "🚀 Создание админ пользователя в базе данных..."

# Выполнение скрипта внутри контейнера
if docker compose -f deployment/docker-compose.production.yml exec -T backend python /tmp/create_admin.py; then
    log "✅ Админ пользователь успешно создан!"
    echo ""
    info "🌐 Теперь вы можете войти в систему:"
    info "   URL: https://lead-schem.ru"
    info "   Логин: $ADMIN_LOGIN"
    info "   Пароль: [указанный вами]"
    echo ""
else
    error "❌ Ошибка при создании админ пользователя"
fi

# Удаление временного файла
rm -f /tmp/create_admin.py

log "🎉 Готово!" 