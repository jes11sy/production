#!/usr/bin/env python3
"""
Скрипт для запуска приложения в режиме разработки
с оптимизированными настройками watchfiles
"""
import uvicorn
from uvicorn_config import UVICORN_CONFIG

if __name__ == "__main__":
    print("🚀 Запуск сервера разработки...")
    print("📁 Отслеживаемые директории:", UVICORN_CONFIG["reload_dirs"])
    print("🚫 Игнорируемые паттерны:", UVICORN_CONFIG["reload_excludes"][:5], "...")
    
    uvicorn.run(
        "app.main:app",
        **UVICORN_CONFIG
    ) 