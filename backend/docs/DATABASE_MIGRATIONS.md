# 🗄️ Система миграций базы данных

## Обзор

Система миграций позволяет безопасно версионировать схему базы данных, отслеживать изменения и применять их в различных средах.

## 🔧 Настройка

### Конфигурация Alembic

Файл `alembic.ini` содержит основные настройки:

```ini
# Путь к скриптам миграций
script_location = alembic

# Формат имен файлов миграций (с датой и временем)
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# Максимальная длина slug
truncate_slug_length = 40

# Формат номера версии
version_num_format = %04d
```

### Конфигурация env.py

Файл `alembic/env.py` настроен для работы с:
- Асинхронным PostgreSQL
- Автоматическим сравнением типов
- Сравнением значений по умолчанию
- Импортом моделей из приложения

## 📋 Основные команды

### CLI утилита (manage_migrations.py)

```bash
# Активация виртуального окружения
venv\Scripts\activate

# Статус миграций
python manage_migrations.py status

# Валидация схемы
python manage_migrations.py validate

# Инициализация системы миграций
python manage_migrations.py init

# Создание новой миграции
python manage_migrations.py create "Описание изменений"

# Применение миграций
python manage_migrations.py apply

# Откат миграции
python manage_migrations.py rollback <revision>

# История миграций
python manage_migrations.py history

# Неприменённые миграции
python manage_migrations.py pending

# Резервная копия
python manage_migrations.py backup

# Текущая ревизия
python manage_migrations.py current

# Комплексная проверка
python manage_migrations.py check
```

### Прямые команды Alembic

```bash
# Создание миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# Просмотр истории
alembic history

# Текущая ревизия
alembic current

# Инициализация
alembic stamp head
```

## 🚀 API эндпоинты

### Статус миграций
```
GET /api/v1/migrations/status
```

**Ответ:**
```json
{
  "status": "success",
  "data": {
    "current_revision": "001_initial_migration",
    "head_revision": "002_add_indexes",
    "is_up_to_date": false,
    "pending_migrations": ["002_add_indexes"],
    "pending_count": 1,
    "total_migrations": 2
  }
}
```

### Применение миграций
```
POST /api/v1/migrations/apply
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Миграции успешно применены",
  "data": {
    "backup_file": "/path/to/backup.sql",
    "applied_migrations": ["002_add_indexes"]
  }
}
```

### Создание миграции
```
POST /api/v1/migrations/create?message=Описание&autogenerate=true
```

### Валидация схемы
```
GET /api/v1/migrations/validate
```

### История миграций
```
GET /api/v1/migrations/history?limit=10
```

### Неприменённые миграции
```
GET /api/v1/migrations/pending
```

### Откат миграции
```
POST /api/v1/migrations/rollback?revision=001
```

### Резервная копия
```
POST /api/v1/migrations/backup
```

## 📝 Создание миграций

### Автоматическое создание

```bash
# Создание миграции с автоматическим определением изменений
python manage_migrations.py create "Add user avatar field"
```

Alembic автоматически обнаружит изменения в моделях и создаст соответствующую миграцию.

### Ручное создание

```bash
# Создание пустой миграции для ручного заполнения
python manage_migrations.py create "Custom data migration" --no-autogenerate
```

### Пример миграции

```python
"""Add user avatar field

Revision ID: 002
Revises: 001
Create Date: 2025-01-15 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Добавление нового поля
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))
    
    # Создание индекса
    op.create_index('ix_users_avatar_url', 'users', ['avatar_url'])

def downgrade():
    # Удаление индекса
    op.drop_index('ix_users_avatar_url', table_name='users')
    
    # Удаление поля
    op.drop_column('users', 'avatar_url')
```

## 🔄 Применение миграций

### Разработка

```bash
# Проверка статуса
python manage_migrations.py status

# Применение всех неприменённых миграций
python manage_migrations.py apply

# Применение до конкретной ревизии
python manage_migrations.py apply --revision 002
```

### Продакшн

```bash
# Создание резервной копии
python manage_migrations.py backup

# Комплексная проверка
python manage_migrations.py check

# Применение с автоматическим бэкапом
python manage_migrations.py apply --backup
```

## ⏪ Откат миграций

### Откат к предыдущей ревизии

```bash
python manage_migrations.py rollback -1
```

### Откат к конкретной ревизии

```bash
python manage_migrations.py rollback 001
```

### Откат с резервной копией

```bash
python manage_migrations.py rollback 001 --backup
```

## 💾 Резервное копирование

### Автоматическое создание резервных копий

Система автоматически создаёт резервные копии перед:
- Применением миграций
- Откатом миграций
- Критическими операциями

### Ручное создание резервной копии

```bash
python manage_migrations.py backup
```

### Расположение резервных копий

Резервные копии сохраняются в `backend/backups/` с именем формата:
```
backup_20250115_153000.sql
```

## 🔍 Валидация и проверка

### Валидация схемы

```bash
python manage_migrations.py validate
```

Проверяет:
- Существование таблицы `alembic_version`
- Наличие всех необходимых таблиц
- Соответствие схемы ожидаемой структуре

### Комплексная проверка

```bash
python manage_migrations.py check
```

Выполняет:
- Валидацию схемы
- Проверку статуса миграций
- Предложение применения неприменённых миграций

## 📊 Мониторинг

### Через API

```bash
# Статус миграций
curl -X GET "http://localhost:8000/api/v1/migrations/status" \
  -H "Authorization: Bearer <admin_token>"

# Неприменённые миграции
curl -X GET "http://localhost:8000/api/v1/migrations/pending" \
  -H "Authorization: Bearer <admin_token>"
```

### Через CLI

```bash
# Краткий статус
python manage_migrations.py current

# Подробный статус
python manage_migrations.py status

# История
python manage_migrations.py history --limit 20
```

## 🚨 Устранение проблем

### Проблема: "Таблица alembic_version не найдена"

**Решение:**
```bash
python manage_migrations.py init
```

### Проблема: "Конфликт ревизий"

**Решение:**
```bash
# Просмотр истории
python manage_migrations.py history

# Откат к стабильной ревизии
python manage_migrations.py rollback <stable_revision>

# Пересоздание миграции
python manage_migrations.py create "Fix migration conflict"
```

### Проблема: "Ошибка применения миграции"

**Решение:**
```bash
# Проверка валидации
python manage_migrations.py validate

# Восстановление из резервной копии
psql -h localhost -U user -d database -f backup_file.sql

# Ручное исправление схемы
```

### Проблема: "Несинхронизированная схема"

**Решение:**
```bash
# Проверка текущего состояния
python manage_migrations.py current

# Принудительная установка ревизии
alembic stamp head

# Создание миграции для синхронизации
python manage_migrations.py create "Sync schema"
```

## 🔧 Настройка для разных сред

### Разработка

```python
# app/config.py
class DevelopmentConfig:
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dev_db"
    MIGRATION_AUTO_APPLY = True
    MIGRATION_BACKUP = False
```

### Тестирование

```python
class TestingConfig:
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/test_db"
    MIGRATION_AUTO_APPLY = True
    MIGRATION_BACKUP = False
```

### Продакшн

```python
class ProductionConfig:
    DATABASE_URL = "postgresql+asyncpg://user:pass@prod-host/prod_db"
    MIGRATION_AUTO_APPLY = False
    MIGRATION_BACKUP = True
```

## 📋 Лучшие практики

### Создание миграций

1. **Описательные имена:** Используйте понятные описания
   ```bash
   python manage_migrations.py create "Add user profile fields"
   ```

2. **Проверка изменений:** Всегда просматривайте созданную миграцию
   ```bash
   # Проверить последнюю миграцию
   ls -la alembic/versions/ | tail -1
   ```

3. **Тестирование:** Тестируйте миграции на копии продакшн данных

### Применение миграций

1. **Резервные копии:** Всегда создавайте резервные копии в продакшне
   ```bash
   python manage_migrations.py apply --backup
   ```

2. **Поэтапное применение:** В критических системах применяйте по одной миграции
   ```bash
   python manage_migrations.py apply --revision 002
   ```

3. **Мониторинг:** Отслеживайте время выполнения миграций

### Откат миграций

1. **Тестирование отката:** Тестируйте откат на копии данных
2. **Быстрый откат:** Подготовьте план быстрого отката
3. **Документация:** Документируйте критические точки отката

## 🔄 Автоматизация

### CI/CD интеграция

```yaml
# .github/workflows/deploy.yml
- name: Run migrations
  run: |
    python manage_migrations.py check
    python manage_migrations.py apply --backup
```

### Автоматические проверки

```bash
# Скрипт для регулярной проверки
#!/bin/bash
cd /path/to/backend
python manage_migrations.py status
if [ $? -ne 0 ]; then
    echo "Migration check failed"
    exit 1
fi
```

## 📈 Метрики и мониторинг

### Ключевые метрики

- Количество неприменённых миграций
- Время выполнения миграций
- Частота откатов
- Размер резервных копий

### Алерты

Настройте алерты на:
- Неприменённые миграции > 0
- Время выполнения миграции > 5 минут
- Ошибки применения миграций
- Превышение размера резервных копий

## 🔒 Безопасность

### Разрешения

- Только администраторы могут управлять миграциями
- API требует токен администратора
- Резервные копии защищены от несанкционированного доступа

### Аудит

- Все операции с миграциями логируются
- Отслеживание изменений схемы
- История резервных копий

## 📚 Дополнительные ресурсы

- [Документация Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Migrations](https://docs.sqlalchemy.org/en/14/core/constraints.html)
- [PostgreSQL Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

## 🎯 Заключение

Система миграций обеспечивает:
- ✅ Безопасное версионирование схемы
- ✅ Автоматическое создание резервных копий
- ✅ Удобное управление через CLI и API
- ✅ Валидацию и мониторинг
- ✅ Поддержку отката изменений
- ✅ Интеграцию с CI/CD

Используйте систему миграций для поддержания актуальности и целостности схемы базы данных во всех средах разработки. 