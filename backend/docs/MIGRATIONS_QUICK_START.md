# 🚀 Быстрый старт: Миграции базы данных

## Основные команды

### Проверка статуса
```bash
python migration_utils.py status
```

### Создание миграции
```bash
python migration_utils.py create "Описание изменений"
```

### Применение миграций
```bash
python migration_utils.py apply
```

### Откат миграции
```bash
python migration_utils.py rollback <revision>
```

### Комплексная проверка
```bash
python migration_utils.py check
```

## API эндпоинты

### Статус миграций
```
GET /api/v1/migrations/status
```

### Применение миграций
```
POST /api/v1/migrations/apply
```

### Создание миграции
```
POST /api/v1/migrations/create?message=Описание
```

## Настройка Alembic

Файл `alembic.ini` настроен для:
- Автоматической генерации миграций
- Именования файлов с датой и временем
- Работы с PostgreSQL

Файл `alembic/env.py` настроен для:
- Асинхронной работы с PostgreSQL
- Автоматического импорта моделей
- Сравнения типов и значений по умолчанию

## Безопасность

- Автоматическое создание резервных копий
- Валидация схемы перед применением
- Доступ только для администраторов (API)
- Логирование всех операций

## Структура файлов

```
backend/
├── alembic.ini              # Конфигурация Alembic
├── alembic/
│   ├── env.py              # Настройки окружения
│   └── versions/           # Файлы миграций
├── migration_utils.py      # CLI утилита
├── app/
│   ├── migrations.py       # Менеджер миграций
│   └── api/
│       └── migrations.py   # API эндпоинты
├── backups/                # Резервные копии
└── DATABASE_MIGRATIONS.md  # Полная документация
```

## Примеры использования

### Создание и применение миграции
```bash
# Создание миграции
python migration_utils.py create "Add user avatar field"

# Проверка статуса
python migration_utils.py status

# Применение миграций
python migration_utils.py apply
```

### Откат миграции
```bash
# Просмотр истории
python migration_utils.py history

# Откат к предыдущей ревизии
python migration_utils.py rollback -1
```

### Работа с резервными копиями
```bash
# Создание резервной копии
python migration_utils.py backup

# Применение с автоматическим бэкапом
python migration_utils.py apply --backup
```

## Устранение проблем

### Инициализация системы
```bash
python migration_utils.py init
```

### Валидация схемы
```bash
python migration_utils.py validate
```

### Комплексная проверка
```bash
python migration_utils.py check
```

## Полная документация

Для подробной информации см. [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) 