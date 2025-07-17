# Система сбора метрик производительности и бизнес-показателей

## Обзор

Система метрик предоставляет комплексное решение для сбора, хранения и анализа метрик производительности и бизнес-показателей вашего приложения.

## Основные компоненты

### 1. MetricsCollector
Основной класс для сбора и хранения метрик в памяти.

**Возможности:**
- Запись значений метрик с временными метками
- Поддержка тегов и метаданных
- Автоматическая очистка старых данных
- Потокобезопасность

### 2. BusinessMetricsCollector
Специализированный сборщик для бизнес-метрик.

**Собираемые метрики:**
- Общее количество заявок
- Заявки по статусам и городам
- Транзакции и суммы
- Активные пользователи
- Конверсия заявок
- Среднее время обработки
- Дневная выручка
- Статистика звонков

### 3. PerformanceMetricsCollector
Сборщик метрик производительности системы.

**Собираемые метрики:**
- HTTP запросы и время ответа
- Запросы к базе данных
- Использование памяти и CPU
- Активные соединения БД
- Попадания/промахи кэша
- Частота ошибок

## Типы метрик

### COUNTER
Счетчик, который только увеличивается.
```python
metrics_collector.increment("api_requests_total", tags={"endpoint": "/users"})
```

### GAUGE
Значение, которое может увеличиваться и уменьшаться.
```python
metrics_collector.set_gauge("memory_usage", 512.5)
```

### HISTOGRAM
Распределение значений (время выполнения, размеры).
```python
metrics_collector.record("request_duration", 0.125, tags={"method": "GET"})
```

### TIMER
Измерение времени выполнения операций.
```python
with metrics_collector.time_operation("database_query"):
    result = await db.execute(query)
```

## API Endpoints

### Основные endpoints

#### GET /api/v1/metrics/
Получение всех метрик с их определениями и статистикой.

#### GET /api/v1/metrics/overview
Общий обзор системы метрик.

#### GET /api/v1/metrics/business
Актуальные бизнес-метрики.

#### GET /api/v1/metrics/performance
Метрики производительности системы.

#### GET /api/v1/metrics/dashboard/summary
Сводка для дашборда с основными показателями.

### Работа с конкретными метриками

#### GET /api/v1/metrics/{metric_name}
Получение информации о конкретной метрике.

#### GET /api/v1/metrics/{metric_name}/values
Получение значений метрики с фильтрацией.

**Параметры:**
- `since`: Дата начала (YYYY-MM-DD)
- `limit`: Максимальное количество значений

#### GET /api/v1/metrics/{metric_name}/statistics
Статистика по метрике (мин, макс, среднее, сумма).

#### POST /api/v1/metrics/{metric_name}/record
Запись значения метрики.

**Тело запроса:**
```json
{
  "value": 42.5,
  "tags": {"user_id": "123", "action": "login"},
  "metadata": {"source": "manual"}
}
```

### Управление метриками

#### POST /api/v1/metrics/collect/business
Принудительный сбор бизнес-метрик.

#### POST /api/v1/metrics/collect/performance
Принудительный сбор метрик производительности.

#### POST /api/v1/metrics/cleanup
Очистка старых метрик.

#### DELETE /api/v1/metrics/{metric_name}/clear
Очистка конкретной метрики (только для админов).

#### GET /api/v1/metrics/export/json
Экспорт метрик в JSON формате.

## Декораторы для интеграции

### @track_database_operation
Автоматическое отслеживание операций с базой данных.

```python
from app.metrics_integration import track_database_operation

@track_database_operation("user_create")
async def create_user(db: AsyncSession, user_data: UserCreate):
    # Автоматически записывает время выполнения и ошибки
    return await db.execute(insert_query)
```

### @track_api_endpoint
Отслеживание производительности API endpoints.

```python
from app.metrics_integration import track_api_endpoint

@track_api_endpoint("user_registration")
async def register_user(user_data: UserCreate):
    # Записывает время выполнения, успешность, ошибки
    return await create_user_logic(user_data)
```

### @track_business_event
Отслеживание бизнес-событий.

```python
from app.metrics_integration import track_business_event

@track_business_event("order_placed", value=1)
async def place_order(order_data: OrderCreate):
    # Увеличивает счетчик бизнес-событий
    return await process_order(order_data)
```

### @track_cache_operation
Отслеживание операций с кэшем.

```python
from app.metrics_integration import track_cache_operation

@track_cache_operation("user_cache")
async def get_user_from_cache(user_id: str):
    # Автоматически записывает попадания/промахи
    return cache.get(f"user:{user_id}")
```

### @track_file_operation
Отслеживание файловых операций.

```python
from app.metrics_integration import track_file_operation

@track_file_operation("file_upload")
async def upload_file(file: UploadFile):
    # Записывает время и статус файловых операций
    return await save_file_logic(file)
```

## Контекстные менеджеры

### MetricsContext
Группировка связанных метрик.

```python
from app.metrics_integration import MetricsContext

async def process_request(request_id: str):
    with MetricsContext("request_processing", {"request_id": request_id}) as ctx:
        # Все метрики в этом контексте будут помечены тегом request_id
        ctx.record_metric("validation_time", 0.05)
        ctx.increment_metric("validation_steps", 3)
        
        # Обработка запроса
        result = await process_logic()
        
        ctx.record_metric("processing_time", 0.15)
        return result
```

## CLI инструмент

### Установка
```bash
pip install -r requirements.txt
```

### Основные команды

#### Просмотр метрик
```bash
# Список всех метрик
python manage_metrics.py list-metrics

# Конкретная метрика
python manage_metrics.py show-metric requests_total --limit 20

# Статистика по метрике
python manage_metrics.py stats requests_total --since 2025-01-01
```

#### Сводки
```bash
# Бизнес-метрики
python manage_metrics.py business-summary

# Производительность
python manage_metrics.py performance-summary

# Дашборд
python manage_metrics.py dashboard
```

#### Управление данными
```bash
# Запись метрики
python manage_metrics.py record custom_metric 42.5 --tags env=prod

# Увеличение счетчика
python manage_metrics.py increment api_calls --value 5

# Очистка старых данных
python manage_metrics.py cleanup --hours 48 --confirm

# Экспорт в файл
python manage_metrics.py export --output metrics_backup.json
```

#### Сбор метрик
```bash
# Принудительный сбор всех метрик
python manage_metrics.py collect-all
```

## Автоматический сбор

### Настройка
Система автоматически собирает метрики каждые 60 секунд:

- Бизнес-метрики из базы данных
- Системные метрики (CPU, память)
- Очистка старых данных (старше 24 часов)

### Middleware
HTTP middleware автоматически записывает:
- Время выполнения запросов
- Коды ответов
- Размер ответов
- Количество запросов по endpoints

## Интеграция с существующим кодом

### Пример интеграции в API endpoint
```python
from app.metrics_integration import track_api_endpoint, collect_request_lifecycle_metrics

@router.post("/requests/")
@track_api_endpoint("create_request")
async def create_request(
    request_data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Создание заявки
    new_request = await create_request_logic(db, request_data, current_user)
    
    # Сбор метрик жизненного цикла
    await collect_request_lifecycle_metrics(
        request_id=str(new_request.id),
        user_id=str(current_user.id),
        city_id=str(request_data.city_id)
    )
    
    return new_request
```

### Пример интеграции в бизнес-логику
```python
from app.metrics_integration import track_business_event, collect_transaction_metrics

@track_business_event("payment_processed")
async def process_payment(transaction_data: TransactionCreate):
    # Обработка платежа
    transaction = await create_transaction(transaction_data)
    
    # Сбор метрик транзакции
    await collect_transaction_metrics(
        transaction_id=str(transaction.id),
        amount=float(transaction.amount),
        transaction_type=transaction.type,
        user_id=str(transaction.user_id)
    )
    
    return transaction
```

## Мониторинг и алерты

### Ключевые метрики для мониторинга

#### Бизнес-метрики
- `conversion_rate` < 5% - низкая конверсия
- `revenue_daily` - отклонение от нормы
- `avg_processing_time` > 300 сек - медленная обработка

#### Производительность
- `memory_usage` > 1000 MB - высокое потребление памяти
- `cpu_usage` > 80% - высокая нагрузка на CPU
- `error_rate` > 5% - высокая частота ошибок

#### Система
- `db_connections_active` > 50 - много активных соединений
- `cache_hit_rate` < 70% - низкая эффективность кэша

### Настройка алертов
```python
# Пример проверки критических метрик
async def check_critical_metrics():
    error_rate = metrics_collector.get_latest_value("error_rate") or 0
    memory_usage = metrics_collector.get_latest_value("memory_usage") or 0
    
    if error_rate > 5:
        await send_alert("High error rate", f"Error rate: {error_rate}%")
    
    if memory_usage > 1000:
        await send_alert("High memory usage", f"Memory: {memory_usage} MB")
```

## Производительность

### Оптимизация
- Метрики хранятся в памяти с автоматической очисткой
- Потокобезопасные операции
- Асинхронный сбор данных
- Настраиваемый размер буфера (по умолчанию 1000 значений)

### Рекомендации
- Используйте теги для группировки метрик
- Регулярно очищайте старые данные
- Мониторьте использование памяти системой метрик
- Настройте экспорт важных метрик во внешние системы

## Безопасность

### Доступ к метрикам
- Все endpoints требуют аутентификации
- Административные операции требуют роль admin
- Экспорт метрик доступен только авторизованным пользователям

### Конфиденциальность
- Не записывайте чувствительные данные в теги или метаданные
- Используйте хеширование для идентификаторов пользователей
- Регулярно очищайте персональные данные

## Расширение системы

### Добавление новых метрик
```python
from app.metrics import MetricDefinition, MetricType, metrics_collector

# Регистрация новой метрики
custom_metric = MetricDefinition(
    name="custom_business_metric",
    type=MetricType.GAUGE,
    description="Описание кастомной метрики",
    unit="units",
    tags=["category", "source"]
)

metrics_collector.register_metric(custom_metric)

# Запись значений
metrics_collector.record(
    "custom_business_metric",
    42.5,
    tags={"category": "sales", "source": "api"}
)
```

### Интеграция с внешними системами
```python
# Экспорт в Prometheus
async def export_to_prometheus():
    all_metrics = metrics_collector.get_all_metrics()
    # Преобразование в формат Prometheus
    return prometheus_format(all_metrics)

# Экспорт в InfluxDB
async def export_to_influxdb():
    all_metrics = metrics_collector.get_all_metrics()
    # Отправка в InfluxDB
    await influxdb_client.write(influxdb_format(all_metrics))
```

## Troubleshooting

### Частые проблемы

#### Метрики не собираются
1. Проверьте, запущен ли фоновый сборщик
2. Убедитесь в корректности подключения к БД
3. Проверьте логи на ошибки

#### Высокое потребление памяти
1. Уменьшите `max_values` в MetricsCollector
2. Сократите интервал очистки старых данных
3. Используйте более агрессивную очистку

#### Медленная работа API
1. Проверьте количество активных метрик
2. Оптимизируйте запросы к базе данных
3. Используйте кэширование для часто запрашиваемых метрик

### Логирование
Система метрик использует стандартное Python логирование:
```python
import logging
logging.getLogger("app.metrics").setLevel(logging.DEBUG)
```

## Примеры использования

### Дашборд реального времени
```python
@router.get("/dashboard/realtime")
async def get_realtime_dashboard():
    # Обновляем все метрики
    await business_collector.collect_all_business_metrics(db)
    performance_collector.record_system_metrics()
    
    return {
        "timestamp": datetime.utcnow(),
        "business": {
            "requests_today": get_requests_today(),
            "conversion_rate": metrics_collector.get_latest_value("conversion_rate"),
            "revenue_daily": metrics_collector.get_latest_value("revenue_daily")
        },
        "performance": {
            "memory_usage": metrics_collector.get_latest_value("memory_usage"),
            "cpu_usage": metrics_collector.get_latest_value("cpu_usage"),
            "response_time_avg": get_avg_response_time()
        }
    }
```

### Отчеты по периодам
```python
async def generate_weekly_report():
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    report = {}
    for metric_name in ["requests_total", "revenue_daily", "conversion_rate"]:
        stats = metrics_collector.get_statistics(metric_name, week_ago)
        report[metric_name] = stats
    
    return report
```

### A/B тестирование
```python
@track_business_event("feature_usage")
async def use_feature(feature_variant: str, user_id: str):
    # Записываем использование функции с вариантом
    metrics_collector.increment(
        "feature_usage",
        tags={"variant": feature_variant, "user_id": user_id}
    )
    
    # Бизнес-логика
    return await process_feature(feature_variant)
```

Система метрик предоставляет мощный инструмент для мониторинга и анализа вашего приложения, помогая принимать обоснованные решения на основе данных. 