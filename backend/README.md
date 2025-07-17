# Backend API

Это бэкенд-часть приложения, построенная на FastAPI.

## Структура проекта

```
backend/
├── app/                    # Основной код приложения
│   ├── api/               # API роутеры
│   ├── core/              # Основные модули (auth, config, etc.)
│   ├── middleware/        # Middleware
│   ├── monitoring/        # Мониторинг и метрики
│   ├── services/          # Бизнес-логика
│   └── utils/             # Утилиты
├── alembic/               # Миграции базы данных
├── config/                # Конфигурационные файлы
├── deployment/            # Docker и deployment файлы
├── docs/                  # Документация
├── logs/                  # Логи приложения
├── media/                 # Загруженные файлы
├── monitoring/            # Настройки мониторинга
├── scripts/               # Скрипты для разработки
├── tests/                 # Тесты
└── requirements.txt       # Python зависимости
```

## Установка и запуск

### Локальная разработка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Скопируйте файл конфигурации:
```bash
cp config/env.example .env
```

4. Настройте переменные окружения в `.env` файле

5. Запустите приложение:
```bash
python run.py
```

### Запуск через Docker

1. Запустите все сервисы:
```bash
cd deployment
docker-compose up -d
```

2. Для остановки:
```bash
docker-compose down
```

## API Документация

После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Тестирование

Запуск тестов:
```bash
pytest
```

Запуск тестов с покрытием:
```bash
pytest --cov=app
```

## Мониторинг

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## Разработка

### Миграции базы данных

Создание новой миграции:
```bash
alembic revision --autogenerate -m "описание изменений"
```

Применение миграций:
```bash
alembic upgrade head
```

### Скрипты

- `scripts/check_coverage.py` - Проверка покрытия тестами
- `scripts/optimize_performance.py` - Оптимизация производительности
- `scripts/run_advanced_tests.py` - Расширенные тесты

## Конфигурация

Основные переменные окружения:
- `DATABASE_URL` - URL подключения к базе данных
- `REDIS_URL` - URL подключения к Redis
- `SECRET_KEY` - Секретный ключ для JWT
- `DEBUG` - Режим отладки

## Логирование

Логи сохраняются в папке `logs/`:
- `app.log` - Основные логи приложения
- `app_error.log` - Логи ошибок
- `app_security.log` - Логи безопасности 