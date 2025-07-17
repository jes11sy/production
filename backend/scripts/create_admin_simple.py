#!/usr/bin/env python3
"""
Простой скрипт для создания администратора в системе
"""
import sys
import os

# Добавляем путь к модулю app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.models import Administrator, Role
from app.core.config import settings

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_administrator():
    """Создание администратора"""
    # Создаем синхронное подключение к базе данных
    # Заменяем asyncpg на psycopg2 для синхронной работы
    sync_url = settings.DATABASE_URL.replace("asyncpg", "psycopg2")
    engine = create_engine(sync_url)
    
    with Session(engine) as session:
        try:
            # Проверяем, существует ли роль admin
            result = session.execute(select(Role).where(Role.name == "admin"))
            admin_role = result.scalar_one_or_none()
            
            if not admin_role:
                print("❌ Роль 'admin' не найдена в таблице roles!")
                print("Убедитесь, что база данных инициализирована корректно.")
                return
            
            # Проверяем, существует ли уже администратор
            result = session.execute(select(Administrator).where(Administrator.login == "admin"))
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("❌ Администратор с логином 'admin' уже существует!")
                return
            
            # Создаем нового администратора
            admin_password = os.getenv("ADMIN_PASSWORD", "CHANGE_ME_NOW")  # Используем переменную окружения
            hashed_password = get_password_hash(admin_password)
            
            new_admin = Administrator(
                name="Главный Администратор",
                role_id=admin_role.id,
                status="active",
                login="admin",
                password_hash=hashed_password,
                notes="Создан автоматически через скрипт"
            )
            
            session.add(new_admin)
            session.commit()
            
            print("✅ Администратор успешно создан!")
            print(f"📋 Логин: admin")
            print(f"🔑 Пароль: {admin_password}")
            print(f"👤 Имя: {new_admin.name}")
            print(f"🔐 Роль: admin")
            print(f"📝 Статус: {new_admin.status}")
            print("\n⚠️  ВАЖНО: Измените пароль после первого входа!")
            
        except Exception as e:
            print(f"❌ Ошибка при создании администратора: {e}")
            session.rollback()


if __name__ == "__main__":
    print("🚀 Создание администратора...")
    create_administrator() 