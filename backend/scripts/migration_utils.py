#!/usr/bin/env python3
"""
Упрощенная утилита для управления миграциями базы данных
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.subprocess_security import safe_subprocess_run, SubprocessSecurityError
import click

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimpleMigrationManager:
    """Упрощенный менеджер миграций"""
    
    def __init__(self):
        self.alembic_ini = "alembic.ini"
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def run_alembic_command(self, command: List[str]) -> Dict[str, Any]:
        """Выполнение команды Alembic"""
        try:
            full_command = ["python", "-m", "alembic"] + command
            result = safe_subprocess_run(
                full_command,
                cwd=self.base_dir
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса миграций"""
        # Получаем текущую ревизию
        current_result = self.run_alembic_command(["current"])
        
        # Получаем head ревизию
        head_result = self.run_alembic_command(["heads"])
        
        # Получаем историю
        history_result = self.run_alembic_command(["history"])
        
        current_revision = None
        if current_result["success"] and current_result["stdout"]:
            # Парсим вывод current
            lines = current_result["stdout"].strip().split('\n')
            for line in lines:
                if line.strip() and not line.startswith('INFO'):
                    current_revision = line.strip().split()[0] if line.strip() else None
                    break
        
        head_revision = None
        if head_result["success"] and head_result["stdout"]:
            # Парсим вывод heads
            lines = head_result["stdout"].strip().split('\n')
            for line in lines:
                if line.strip() and not line.startswith('INFO'):
                    head_revision = line.strip().split()[0] if line.strip() else None
                    break
        
        return {
            "current_revision": current_revision,
            "head_revision": head_revision,
            "is_up_to_date": current_revision == head_revision,
            "current_output": current_result["stdout"],
            "head_output": head_result["stdout"],
            "history_output": history_result["stdout"] if history_result["success"] else None
        }
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Dict[str, Any]:
        """Создание новой миграции"""
        command = ["revision"]
        if autogenerate:
            command.append("--autogenerate")
        command.extend(["-m", message])
        
        result = self.run_alembic_command(command)
        return result
    
    def apply_migrations(self, revision: str = "head") -> Dict[str, Any]:
        """Применение миграций"""
        result = self.run_alembic_command(["upgrade", revision])
        return result
    
    def rollback_migration(self, revision: str) -> Dict[str, Any]:
        """Откат миграции"""
        result = self.run_alembic_command(["downgrade", revision])
        return result
    
    def get_history(self) -> Dict[str, Any]:
        """Получение истории миграций"""
        result = self.run_alembic_command(["history", "--verbose"])
        return result
    
    def initialize(self) -> Dict[str, Any]:
        """Инициализация миграций"""
        result = self.run_alembic_command(["stamp", "head"])
        return result
    
    def validate_schema(self) -> Dict[str, Any]:
        """Базовая валидация схемы"""
        try:
            from app.core.config import settings
            from sqlalchemy import create_engine, text
            
            # Создаем синхронный движок
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
                
                return {
                    "valid": has_alembic_table,
                    "has_alembic_table": has_alembic_table,
                    "message": "Схема валидна" if has_alembic_table else "Требуется инициализация"
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "Ошибка валидации схемы"
            }
    
    def create_backup(self) -> Dict[str, Any]:
        """Создание резервной копии"""
        try:
            from app.core.config import settings
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.base_dir, "backups")
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
            
            return {
                "success": result.returncode == 0,
                "backup_file": backup_file if result.returncode == 0 else None,
                "output": result.stdout,
                "error": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backup_file": None
            }


# Создаем глобальный экземпляр
migration_manager = SimpleMigrationManager()


@click.group()
def cli():
    """Управление миграциями базы данных"""
    pass


@cli.command()
def status():
    """Показать статус миграций"""
    click.echo("🔍 Проверка статуса миграций...")
    
    status_data = migration_manager.get_status()
    
    click.echo(f"\n📊 Статус миграций:")
    click.echo(f"   Текущая ревизия: {status_data['current_revision'] or 'Не инициализирована'}")
    click.echo(f"   Последняя ревизия: {status_data['head_revision'] or 'Не найдена'}")
    click.echo(f"   Актуальность: {'✅ Актуальна' if status_data['is_up_to_date'] else '❌ Требуется обновление'}")
    
    if status_data['current_output']:
        click.echo(f"\n📋 Текущее состояние:")
        click.echo(f"   {status_data['current_output']}")
    
    if status_data['head_output']:
        click.echo(f"\n🔝 Последняя ревизия:")
        click.echo(f"   {status_data['head_output']}")


@cli.command()
def validate():
    """Валидация схемы базы данных"""
    click.echo("🔍 Валидация схемы базы данных...")
    
    validation_result = migration_manager.validate_schema()
    
    if validation_result['valid']:
        click.echo(f"✅ {validation_result['message']}")
    else:
        click.echo(f"❌ {validation_result['message']}")
        if 'error' in validation_result:
            click.echo(f"   Ошибка: {validation_result['error']}")


@cli.command()
def init():
    """Инициализация системы миграций"""
    click.echo("🚀 Инициализация системы миграций...")
    
    result = migration_manager.initialize()
    
    if result['success']:
        click.echo(f"✅ Система миграций инициализирована")
        click.echo(f"   Вывод: {result['stdout']}")
    else:
        click.echo(f"❌ Ошибка инициализации: {result['stderr']}")


@cli.command()
@click.argument('message')
@click.option('--autogenerate/--no-autogenerate', default=True, help='Автоматическое создание миграции')
def create(message: str, autogenerate: bool):
    """Создать новую миграцию"""
    click.echo(f"📝 Создание миграции: {message}")
    
    result = migration_manager.create_migration(message, autogenerate)
    
    if result['success']:
        click.echo(f"✅ Миграция создана успешно")
        click.echo(f"   Вывод: {result['stdout']}")
    else:
        click.echo(f"❌ Ошибка создания миграции: {result['stderr']}")


@cli.command()
@click.option('--revision', default='head', help='Ревизия для применения')
@click.option('--backup/--no-backup', default=True, help='Создать резервную копию')
def apply(revision: str, backup: bool):
    """Применить миграции"""
    click.echo(f"🔄 Применение миграций до ревизии: {revision}")
    
    if backup:
        click.echo("💾 Создание резервной копии...")
        backup_result = migration_manager.create_backup()
        if backup_result['success']:
            click.echo(f"✅ Резервная копия создана: {backup_result['backup_file']}")
        else:
            click.echo(f"⚠️ Ошибка создания резервной копии: {backup_result['error']}")
    
    result = migration_manager.apply_migrations(revision)
    
    if result['success']:
        click.echo(f"✅ Миграции применены успешно")
        click.echo(f"   Вывод: {result['stdout']}")
    else:
        click.echo(f"❌ Ошибка применения миграций: {result['stderr']}")


@cli.command()
@click.argument('revision')
@click.option('--backup/--no-backup', default=True, help='Создать резервную копию')
def rollback(revision: str, backup: bool):
    """Откатить миграцию"""
    click.echo(f"⏪ Откат миграции до ревизии: {revision}")
    
    if not click.confirm(f"Вы уверены, что хотите откатить миграцию до {revision}?"):
        click.echo("Отмена операции")
        return
    
    if backup:
        click.echo("💾 Создание резервной копии...")
        backup_result = migration_manager.create_backup()
        if backup_result['success']:
            click.echo(f"✅ Резервная копия создана: {backup_result['backup_file']}")
        else:
            click.echo(f"⚠️ Ошибка создания резервной копии: {backup_result['error']}")
    
    result = migration_manager.rollback_migration(revision)
    
    if result['success']:
        click.echo(f"✅ Миграция откачена успешно")
        click.echo(f"   Вывод: {result['stdout']}")
    else:
        click.echo(f"❌ Ошибка отката миграции: {result['stderr']}")


@cli.command()
def history():
    """Показать историю миграций"""
    click.echo("📜 История миграций:")
    
    result = migration_manager.get_history()
    
    if result['success']:
        click.echo(result['stdout'])
    else:
        click.echo(f"❌ Ошибка получения истории: {result['stderr']}")


@cli.command()
def backup():
    """Создать резервную копию базы данных"""
    click.echo("💾 Создание резервной копии базы данных...")
    
    result = migration_manager.create_backup()
    
    if result['success']:
        click.echo(f"✅ Резервная копия создана: {result['backup_file']}")
        
        # Показываем размер файла
        if result['backup_file'] and os.path.exists(result['backup_file']):
            size_mb = os.path.getsize(result['backup_file']) / (1024 * 1024)
            click.echo(f"   Размер файла: {size_mb:.2f} MB")
    else:
        click.echo(f"❌ Ошибка создания резервной копии: {result['error']}")


@cli.command()
def check():
    """Комплексная проверка системы миграций"""
    click.echo("🔍 Комплексная проверка системы миграций...")
    
    # Валидация схемы
    click.echo("\n1. Валидация схемы базы данных:")
    validation_result = migration_manager.validate_schema()
    
    if validation_result['valid']:
        click.echo(f"   ✅ {validation_result['message']}")
    else:
        click.echo(f"   ❌ {validation_result['message']}")
        if 'error' in validation_result:
            click.echo(f"      Ошибка: {validation_result['error']}")
    
    # Статус миграций
    click.echo("\n2. Статус миграций:")
    status_data = migration_manager.get_status()
    
    click.echo(f"   Текущая ревизия: {status_data['current_revision'] or 'Не инициализирована'}")
    click.echo(f"   Последняя ревизия: {status_data['head_revision'] or 'Не найдена'}")
    
    if status_data['is_up_to_date']:
        click.echo("   ✅ База данных актуальна")
    else:
        click.echo("   ❌ Требуется применение миграций")
        
        if click.confirm("\nПрименить миграции?"):
            click.echo("🔄 Применение миграций...")
            
            # Создаем резервную копию
            backup_result = migration_manager.create_backup()
            if backup_result['success']:
                click.echo(f"💾 Резервная копия: {backup_result['backup_file']}")
            
            # Применяем миграции
            apply_result = migration_manager.apply_migrations()
            if apply_result['success']:
                click.echo("✅ Миграции применены успешно")
            else:
                click.echo(f"❌ Ошибка применения миграций: {apply_result['stderr']}")
    
    click.echo("\n✅ Проверка завершена")


if __name__ == '__main__':
    cli() 