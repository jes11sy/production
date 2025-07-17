"""
Система управления миграциями базы данных
"""
import os
import sys
import subprocess
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Исправляем конфликт имен с локальной папкой alembic
import importlib.util
import sys
from pathlib import Path

# Находим системный пакет alembic
alembic_spec = importlib.util.find_spec("alembic")
if alembic_spec and alembic_spec.origin:
    alembic_path = Path(alembic_spec.origin).parent
    if str(alembic_path) not in sys.path:
        sys.path.insert(0, str(alembic_path.parent))

try:
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from alembic.runtime.environment import EnvironmentContext
except ImportError as e:
    print(f"Ошибка импорта alembic: {e}")
    # Fallback - попробуем импортировать напрямую
    import importlib
    command = importlib.import_module("alembic.command")
    Config = importlib.import_module("alembic.config").Config
    ScriptDirectory = importlib.import_module("alembic.script").ScriptDirectory
    MigrationContext = importlib.import_module("alembic.runtime.migration").MigrationContext
    EnvironmentContext = importlib.import_module("alembic.runtime.environment").EnvironmentContext
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from .config import settings
from .database import engine

logger = logging.getLogger(__name__)

class MigrationManager:
    """Менеджер миграций базы данных"""
    
    def __init__(self):
        self.alembic_cfg_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "alembic.ini"
        )
        self.alembic_cfg = Config(self.alembic_cfg_path)
        self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)
        
    def get_current_revision(self) -> Optional[str]:
        """Получение текущей ревизии базы данных"""
        try:
            # Создаем синхронный движок для миграций
            sync_engine = create_engine(
                settings.DATABASE_URL.replace("+asyncpg", "")
            )
            
            with sync_engine.connect() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            logger.error(f"Ошибка получения текущей ревизии: {e}")
            return None
    
    def get_head_revision(self) -> Optional[str]:
        """Получение последней ревизии из скриптов"""
        try:
            return self.script_dir.get_current_head()
        except Exception as e:
            logger.error(f"Ошибка получения head ревизии: {e}")
            return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Получение истории миграций"""
        try:
            revisions = []
            for revision in self.script_dir.walk_revisions():
                revisions.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "depends_on": revision.depends_on,
                    "doc": revision.doc,
                    "module": revision.module,
                    "path": revision.path
                })
            return revisions
        except Exception as e:
            logger.error(f"Ошибка получения истории миграций: {e}")
            return []
    
    def get_pending_migrations(self) -> List[str]:
        """Получение списка неприменённых миграций"""
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()
            
            if current == head:
                return []
            
            pending = []
            for revision in self.script_dir.walk_revisions(current, head):
                if revision.revision != current:
                    pending.append(revision.revision)
            
            return pending
        except Exception as e:
            logger.error(f"Ошибка получения неприменённых миграций: {e}")
            return []
    
    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Создание новой миграции"""
        try:
            # Формируем команду для создания миграции
            cmd = [
                sys.executable, "-m", "alembic", 
                "-c", self.alembic_cfg_path,
                "revision"
            ]
            
            if autogenerate:
                cmd.append("--autogenerate")
            
            cmd.extend(["-m", message])
            
            # Выполняем команду
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd=os.path.dirname(self.alembic_cfg_path)
            )
            
            if result.returncode != 0:
                raise Exception(f"Ошибка создания миграции: {result.stderr}")
            
            logger.info(f"Миграция создана: {message}")
            return result.stdout
            
        except Exception as e:
            logger.error(f"Ошибка создания миграции: {e}")
            raise
    
    def apply_migrations(self, revision: str = "head") -> str:
        """Применение миграций"""
        try:
            cmd = [
                sys.executable, "-m", "alembic",
                "-c", self.alembic_cfg_path,
                "upgrade", revision
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.alembic_cfg_path)
            )
            
            if result.returncode != 0:
                raise Exception(f"Ошибка применения миграций: {result.stderr}")
            
            logger.info(f"Миграции применены до ревизии: {revision}")
            return result.stdout
            
        except Exception as e:
            logger.error(f"Ошибка применения миграций: {e}")
            raise
    
    def rollback_migration(self, revision: str) -> str:
        """Откат миграции"""
        try:
            cmd = [
                sys.executable, "-m", "alembic",
                "-c", self.alembic_cfg_path,
                "downgrade", revision
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(self.alembic_cfg_path)
            )
            
            if result.returncode != 0:
                raise Exception(f"Ошибка отката миграции: {result.stderr}")
            
            logger.info(f"Миграция откачена до ревизии: {revision}")
            return result.stdout
            
        except Exception as e:
            logger.error(f"Ошибка отката миграции: {e}")
            raise
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Получение статуса миграций"""
        try:
            current = self.get_current_revision()
            head = self.get_head_revision()
            pending = self.get_pending_migrations()
            history = self.get_migration_history()
            
            return {
                "current_revision": current,
                "head_revision": head,
                "is_up_to_date": current == head,
                "pending_migrations": pending,
                "pending_count": len(pending),
                "total_migrations": len(history),
                "history": history[:10]  # Последние 10 миграций
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса миграций: {e}")
            return {
                "error": str(e),
                "current_revision": None,
                "head_revision": None,
                "is_up_to_date": False,
                "pending_migrations": [],
                "pending_count": 0,
                "total_migrations": 0,
                "history": []
            }
    
    def validate_database_schema(self) -> Dict[str, Any]:
        """Валидация схемы базы данных"""
        try:
            # Создаем синхронный движок для валидации
            sync_engine = create_engine(
                settings.DATABASE_URL.replace("+asyncpg", "")
            )
            
            with sync_engine.connect() as conn:
                # Проверяем существование таблицы alembic_version
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'alembic_version'
                    )
                """))
                
                has_alembic_table = result.scalar()
                
                if not has_alembic_table:
                    return {
                        "valid": False,
                        "error": "Таблица alembic_version не найдена. Необходимо инициализировать миграции.",
                        "suggestions": [
                            "Выполните: alembic stamp head",
                            "Или создайте начальную миграцию: alembic revision --autogenerate -m 'Initial migration'"
                        ]
                    }
                
                # Проверяем основные таблицы
                required_tables = [
                    'cities', 'roles', 'request_types', 'directions', 
                    'transaction_types', 'advertising_campaigns',
                    'masters', 'employees', 'administrators',
                    'requests', 'transactions', 'files'
                ]
                
                missing_tables = []
                for table in required_tables:
                    result = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table}'
                        )
                    """))
                    
                    if not result.scalar():
                        missing_tables.append(table)
                
                if missing_tables:
                    return {
                        "valid": False,
                        "error": f"Отсутствуют таблицы: {', '.join(missing_tables)}",
                        "missing_tables": missing_tables,
                        "suggestions": [
                            "Создайте миграцию для недостающих таблиц",
                            "Или примените существующие миграции: alembic upgrade head"
                        ]
                    }
                
                return {
                    "valid": True,
                    "message": "Схема базы данных корректна",
                    "tables_count": len(required_tables),
                    "has_alembic_table": True
                }
                
        except Exception as e:
            logger.error(f"Ошибка валидации схемы: {e}")
            return {
                "valid": False,
                "error": f"Ошибка валидации: {str(e)}",
                "suggestions": [
                    "Проверьте подключение к базе данных",
                    "Убедитесь, что база данных существует"
                ]
            }
    
    def initialize_migrations(self) -> str:
        """Инициализация системы миграций"""
        try:
            # Создаем директорию для миграций если её нет
            versions_dir = os.path.join(
                os.path.dirname(self.alembic_cfg_path),
                "alembic", "versions"
            )
            os.makedirs(versions_dir, exist_ok=True)
            
            # Проверяем текущее состояние
            current = self.get_current_revision()
            
            if current is None:
                # Инициализируем Alembic
                cmd = [
                    sys.executable, "-m", "alembic",
                    "-c", self.alembic_cfg_path,
                    "stamp", "head"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.alembic_cfg_path)
                )
                
                if result.returncode != 0:
                    raise Exception(f"Ошибка инициализации: {result.stderr}")
                
                logger.info("Система миграций инициализирована")
                return "Система миграций успешно инициализирована"
            else:
                return f"Система миграций уже инициализирована (текущая ревизия: {current})"
                
        except Exception as e:
            logger.error(f"Ошибка инициализации миграций: {e}")
            raise
    
    def backup_database(self) -> str:
        """Создание резервной копии базы данных перед миграцией"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(
                os.path.dirname(self.alembic_cfg_path),
                "backups"
            )
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            
            # Команда для создания дампа PostgreSQL
            cmd = [
                "pg_dump",
                "--host", settings.POSTGRESQL_HOST,
                "--port", str(settings.POSTGRESQL_PORT),
                "--username", settings.POSTGRESQL_USER,
                "--dbname", settings.POSTGRESQL_DBNAME,
                "--file", backup_file,
                "--verbose"
            ]
            
            # Устанавливаем пароль через переменную окружения
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.POSTGRESQL_PASSWORD
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                raise Exception(f"Ошибка создания резервной копии: {result.stderr}")
            
            logger.info(f"Резервная копия создана: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            raise


# Глобальный экземпляр менеджера миграций
migration_manager = MigrationManager()


# Утилитные функции для работы с миграциями
async def check_migration_status() -> Dict[str, Any]:
    """Проверка статуса миграций"""
    return migration_manager.get_migration_status()


async def apply_pending_migrations() -> Dict[str, Any]:
    """Применение неприменённых миграций"""
    try:
        status = migration_manager.get_migration_status()
        
        if status["is_up_to_date"]:
            return {
                "success": True,
                "message": "База данных уже обновлена до последней версии",
                "current_revision": status["current_revision"]
            }
        
        # Создаем резервную копию перед миграцией
        backup_file = migration_manager.backup_database()
        
        # Применяем миграции
        result = migration_manager.apply_migrations()
        
        return {
            "success": True,
            "message": "Миграции успешно применены",
            "backup_file": backup_file,
            "migration_output": result,
            "applied_migrations": status["pending_migrations"]
        }
        
    except Exception as e:
        logger.error(f"Ошибка применения миграций: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка применения миграций"
        }


async def create_new_migration(message: str, autogenerate: bool = True) -> Dict[str, Any]:
    """Создание новой миграции"""
    try:
        result = migration_manager.create_migration(message, autogenerate)
        
        return {
            "success": True,
            "message": f"Миграция '{message}' успешно создана",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка создания миграции: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка создания миграции"
        }


async def validate_schema() -> Dict[str, Any]:
    """Валидация схемы базы данных"""
    return migration_manager.validate_database_schema()


async def initialize_migration_system() -> Dict[str, Any]:
    """Инициализация системы миграций"""
    try:
        result = migration_manager.initialize_migrations()
        
        return {
            "success": True,
            "message": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка инициализации системы миграций"
        } 