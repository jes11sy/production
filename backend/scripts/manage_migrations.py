#!/usr/bin/env python3
"""
CLI утилита для управления миграциями базы данных
"""
import asyncio
import sys
import os
from typing import Optional
import click
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.migrations import (
    migration_manager,
    check_migration_status,
    apply_pending_migrations,
    create_new_migration,
    validate_schema,
    initialize_migration_system
)


@click.group()
def cli():
    """Управление миграциями базы данных"""
    pass


@cli.command()
def status():
    """Показать статус миграций"""
    click.echo("🔍 Проверка статуса миграций...")
    
    try:
        status_data = migration_manager.get_migration_status()
        
        click.echo(f"\n📊 Статус миграций:")
        click.echo(f"   Текущая ревизия: {status_data['current_revision'] or 'Не инициализирована'}")
        click.echo(f"   Последняя ревизия: {status_data['head_revision'] or 'Не найдена'}")
        click.echo(f"   Актуальность: {'✅ Актуальна' if status_data['is_up_to_date'] else '❌ Требуется обновление'}")
        click.echo(f"   Неприменённых миграций: {status_data['pending_count']}")
        click.echo(f"   Всего миграций: {status_data['total_migrations']}")
        
        if status_data['pending_migrations']:
            click.echo(f"\n⏳ Неприменённые миграции:")
            for migration in status_data['pending_migrations']:
                click.echo(f"   - {migration}")
        
        if status_data['history']:
            click.echo(f"\n📜 Последние миграции:")
            for migration in status_data['history'][:5]:
                click.echo(f"   - {migration['revision']}: {migration['doc'] or 'Без описания'}")
        
    except Exception as e:
        click.echo(f"❌ Ошибка получения статуса: {e}", err=True)
        sys.exit(1)


@cli.command()
def validate():
    """Валидация схемы базы данных"""
    click.echo("🔍 Валидация схемы базы данных...")
    
    try:
        validation_result = migration_manager.validate_database_schema()
        
        if validation_result['valid']:
            click.echo(f"✅ {validation_result['message']}")
            click.echo(f"   Проверено таблиц: {validation_result['tables_count']}")
            click.echo(f"   Таблица alembic_version: {'✅ Найдена' if validation_result['has_alembic_table'] else '❌ Не найдена'}")
        else:
            click.echo(f"❌ {validation_result['error']}")
            
            if 'missing_tables' in validation_result:
                click.echo(f"   Отсутствующие таблицы: {', '.join(validation_result['missing_tables'])}")
            
            if 'suggestions' in validation_result:
                click.echo(f"\n💡 Рекомендации:")
                for suggestion in validation_result['suggestions']:
                    click.echo(f"   - {suggestion}")
    
    except Exception as e:
        click.echo(f"❌ Ошибка валидации: {e}", err=True)
        sys.exit(1)


@cli.command()
def init():
    """Инициализация системы миграций"""
    click.echo("🚀 Инициализация системы миграций...")
    
    try:
        result = migration_manager.initialize_migrations()
        click.echo(f"✅ {result}")
        
    except Exception as e:
        click.echo(f"❌ Ошибка инициализации: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('message')
@click.option('--autogenerate/--no-autogenerate', default=True, help='Автоматическое создание миграции')
def create(message: str, autogenerate: bool):
    """Создать новую миграцию"""
    click.echo(f"📝 Создание миграции: {message}")
    
    try:
        result = migration_manager.create_migration(message, autogenerate)
        click.echo(f"✅ Миграция создана успешно")
        click.echo(f"Вывод команды:\n{result}")
        
    except Exception as e:
        click.echo(f"❌ Ошибка создания миграции: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--revision', default='head', help='Ревизия для применения (по умолчанию: head)')
@click.option('--backup/--no-backup', default=True, help='Создать резервную копию перед применением')
def apply(revision: str, backup: bool):
    """Применить миграции"""
    click.echo(f"🔄 Применение миграций до ревизии: {revision}")
    
    try:
        # Проверяем статус
        status_data = migration_manager.get_migration_status()
        
        if status_data['is_up_to_date'] and revision == 'head':
            click.echo("✅ База данных уже актуальна")
            return
        
        if backup:
            click.echo("💾 Создание резервной копии...")
            backup_file = migration_manager.backup_database()
            click.echo(f"✅ Резервная копия создана: {backup_file}")
        
        click.echo("🔄 Применение миграций...")
        result = migration_manager.apply_migrations(revision)
        
        click.echo(f"✅ Миграции применены успешно")
        click.echo(f"Вывод команды:\n{result}")
        
    except Exception as e:
        click.echo(f"❌ Ошибка применения миграций: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('revision')
@click.option('--backup/--no-backup', default=True, help='Создать резервную копию перед откатом')
def rollback(revision: str, backup: bool):
    """Откатить миграцию"""
    click.echo(f"⏪ Откат миграции до ревизии: {revision}")
    
    if not click.confirm(f"Вы уверены, что хотите откатить миграцию до {revision}?"):
        click.echo("Отмена операции")
        return
    
    try:
        if backup:
            click.echo("💾 Создание резервной копии...")
            backup_file = migration_manager.backup_database()
            click.echo(f"✅ Резервная копия создана: {backup_file}")
        
        click.echo("⏪ Откат миграции...")
        result = migration_manager.rollback_migration(revision)
        
        click.echo(f"✅ Миграция откачена успешно")
        click.echo(f"Вывод команды:\n{result}")
        
    except Exception as e:
        click.echo(f"❌ Ошибка отката миграции: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', default=10, help='Количество миграций для показа')
def history(limit: int):
    """Показать историю миграций"""
    click.echo(f"📜 История миграций (последние {limit}):")
    
    try:
        history_data = migration_manager.get_migration_history()
        
        if not history_data:
            click.echo("   Миграции не найдены")
            return
        
        for i, migration in enumerate(history_data[:limit], 1):
            click.echo(f"   {i}. {migration['revision']}")
            click.echo(f"      Описание: {migration['doc'] or 'Без описания'}")
            click.echo(f"      Родительская: {migration['down_revision'] or 'Корневая'}")
            click.echo(f"      Файл: {os.path.basename(migration['path']) if migration['path'] else 'Не найден'}")
            click.echo()
        
        if len(history_data) > limit:
            click.echo(f"   ... и ещё {len(history_data) - limit} миграций")
    
    except Exception as e:
        click.echo(f"❌ Ошибка получения истории: {e}", err=True)
        sys.exit(1)


@cli.command()
def pending():
    """Показать неприменённые миграции"""
    click.echo("⏳ Неприменённые миграции:")
    
    try:
        pending_migrations = migration_manager.get_pending_migrations()
        
        if not pending_migrations:
            click.echo("   Нет неприменённых миграций")
            return
        
        for i, migration in enumerate(pending_migrations, 1):
            click.echo(f"   {i}. {migration}")
    
    except Exception as e:
        click.echo(f"❌ Ошибка получения неприменённых миграций: {e}", err=True)
        sys.exit(1)


@cli.command()
def backup():
    """Создать резервную копию базы данных"""
    click.echo("💾 Создание резервной копии базы данных...")
    
    try:
        backup_file = migration_manager.backup_database()
        click.echo(f"✅ Резервная копия создана: {backup_file}")
        
        # Показываем размер файла
        if os.path.exists(backup_file):
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            click.echo(f"   Размер файла: {size_mb:.2f} MB")
        
    except Exception as e:
        click.echo(f"❌ Ошибка создания резервной копии: {e}", err=True)
        sys.exit(1)


@cli.command()
def current():
    """Показать текущую ревизию"""
    click.echo("🔍 Текущая ревизия базы данных:")
    
    try:
        current_revision = migration_manager.get_current_revision()
        head_revision = migration_manager.get_head_revision()
        
        click.echo(f"   Текущая: {current_revision or 'Не инициализирована'}")
        click.echo(f"   Последняя: {head_revision or 'Не найдена'}")
        
        if current_revision and head_revision:
            if current_revision == head_revision:
                click.echo("   Статус: ✅ Актуальна")
            else:
                click.echo("   Статус: ❌ Требуется обновление")
        
    except Exception as e:
        click.echo(f"❌ Ошибка получения ревизии: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--auto-apply/--no-auto-apply', default=False, help='Автоматически применить миграции')
def check(auto_apply: bool):
    """Комплексная проверка системы миграций"""
    click.echo("🔍 Комплексная проверка системы миграций...")
    
    try:
        # Валидация схемы
        click.echo("\n1. Валидация схемы базы данных:")
        validation_result = migration_manager.validate_database_schema()
        
        if validation_result['valid']:
            click.echo(f"   ✅ {validation_result['message']}")
        else:
            click.echo(f"   ❌ {validation_result['error']}")
            if validation_result.get('suggestions'):
                for suggestion in validation_result['suggestions']:
                    click.echo(f"      💡 {suggestion}")
        
        # Статус миграций
        click.echo("\n2. Статус миграций:")
        status_data = migration_manager.get_migration_status()
        
        click.echo(f"   Текущая ревизия: {status_data['current_revision'] or 'Не инициализирована'}")
        click.echo(f"   Последняя ревизия: {status_data['head_revision'] or 'Не найдена'}")
        click.echo(f"   Неприменённых миграций: {status_data['pending_count']}")
        
        if status_data['is_up_to_date']:
            click.echo("   ✅ База данных актуальна")
        else:
            click.echo("   ❌ Требуется применение миграций")
            
            if status_data['pending_migrations']:
                click.echo("   Неприменённые миграции:")
                for migration in status_data['pending_migrations']:
                    click.echo(f"      - {migration}")
                
                if click.confirm("\nПрименить неприменённые миграции?") or auto_apply:
                    click.echo("🔄 Применение миграций...")
                    
                    # Создаем резервную копию
                    backup_file = migration_manager.backup_database()
                    click.echo(f"💾 Резервная копия: {backup_file}")
                    
                    # Применяем миграции
                    result = migration_manager.apply_migrations()
                    click.echo("✅ Миграции применены успешно")
        
        click.echo("\n✅ Проверка завершена")
        
    except Exception as e:
        click.echo(f"❌ Ошибка проверки: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli() 