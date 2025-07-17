"""
Конфигурация для uvicorn с настройками watchfiles
"""
import os
from pathlib import Path

# Получаем корневую директорию проекта
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Директории и файлы для игнорирования
IGNORE_PATTERNS = [
    "media/*",
    "*.log*",
    "*.tmp*",
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    ".git/*",
    "venv/*",
    "env/*",
    ".env*",
    "*.sqlite*",
    "*.db*",
    "alembic/versions/*",
    "backup/*",
    "docs/*",
    "frontend/*",
    "*.md",
    "app.log*",
    "*.log.*",
    "logs/*"
]

# Конфигурация для uvicorn
UVICORN_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
    "reload_dirs": [str(current_dir / "app")],  # Отслеживаем только app директорию
    "reload_excludes": IGNORE_PATTERNS,
    "log_level": "info",
    "access_log": True,
    "use_colors": True,
}

def get_reload_excludes():
    """Получить список паттернов для исключения из отслеживания"""
    return IGNORE_PATTERNS

def get_reload_dirs():
    """Получить список директорий для отслеживания"""
    return [str(current_dir / "app")] 