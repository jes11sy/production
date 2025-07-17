# Docker Deployment

## Статус сервисов

✅ **Grafana** - http://localhost:3000 (admin/admin123)
✅ **Prometheus** - http://localhost:9090  
✅ **PostgreSQL** - localhost:5432
✅ **Redis** - localhost:6379
✅ **Backend API** - http://localhost:8000 (полностью работает!)

## Запуск

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs backend

# Остановка
docker-compose down
```

## Тестирование

```bash
# Тест всех сервисов
python test_services.py
```

## Переменные окружения

Настройки находятся в файле `docker.env`:

- `POSTGRES_DB=backend_db`
- `POSTGRES_USER=backend_user`
- `POSTGRES_PASSWORD=backend_password`
- `SECRET_KEY=xhdPjRQzxl6wm4rIQPTw0cSKkdaMowBYzB-rzaQ_Zxw`

## Решенные проблемы

1. **Backend API**: ✅ Исправлена ошибка с индексом базы данных
   - Проблема была в использовании функции `NOW()` в условии WHERE индекса
   - Решение: Убрали WHERE условие с `NOW()` из индексов, так как оно не IMMUTABLE
   - Результат: Backend API теперь полностью работает

## Работающие сервисы

- **Grafana**: Веб-интерфейс для мониторинга
- **Prometheus**: Сбор метрик
- **PostgreSQL**: База данных
- **Redis**: Кеширование
- **Backend API**: Полнофункциональное REST API

## Порты

- 3000: Grafana
- 8000: Backend API (полностью работает)
- 5432: PostgreSQL
- 6379: Redis
- 9090: Prometheus

## Доступные endpoints

- **http://localhost:8000/health** - проверка здоровья API
- **http://localhost:8000/docs** - интерактивная документация API
- **http://localhost:8000/redoc** - альтернативная документация API
2. Настроить healthcheck для всех сервисов
3. Добавить автоматические миграции при запуске 