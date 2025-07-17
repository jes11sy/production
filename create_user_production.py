#!/usr/bin/env python3
"""
Скрипт для создания пользователя admin в production базе данных
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    """Создание администратора"""
    # Используем переменные окружения вместо хардкод паролей
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Проверим, какие таблицы есть в базе
            result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            print(f"Таблицы в базе: {tables}")
            
            # Создадим таблицы если их нет
            if 'users' not in tables:
                print("Создаем таблицы...")
                # Здесь должны быть команды создания таблиц
                print("⚠️ Сначала запустите migrations для создания таблиц")
                return
                
            # Проверим, есть ли уже admin
            result = await session.execute(text("SELECT id FROM users WHERE username = 'admin'"))
            existing_admin = result.fetchone()
            
            if existing_admin:
                print("⚠️ Пользователь admin уже существует!")
                return
            
            # Создаем пользователя admin (пароль из переменной окружения)
            password = os.getenv("ADMIN_PASSWORD", "change_me_password")
            password_hash = pwd_context.hash(password)
            
            await session.execute(text("""
                INSERT INTO users (username, email, password_hash, is_active, role)
                VALUES ('admin', 'admin@lead-schem.ru', :password_hash, true, 'admin')
            """), {"password_hash": password_hash})
            
            await session.commit()
            
            print("✅ Пользователь admin успешно создан!")
            print(f"📋 Логин: admin")
            print(f"🔑 Пароль: {password}")
            print(f"📧 Email: admin@lead-schem.ru")
            print(f"🔐 Роль: admin")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    print("🚀 Создание администратора...")
    asyncio.run(create_admin_user()) 