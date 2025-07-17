# Система мониторинга и Health Checks

## Обзор

Система мониторинга предоставляет комплексную проверку здоровья всех компонентов приложения:

- **База данных**: подключение, производительность, пул соединений
- **Система**: CPU, память, диск, uptime
- **Сервисы**: сервис записей, файловое хранилище
- **Общий статус**: агрегированная информация

## API Endpoints

### Публичные endpoints

#### `GET /health`
Базовая проверка состояния приложения (публичный доступ)

**Ответ:**
```json
{
  "status": "healthy|degraded|unhealthy|unknown",
  "timestamp": "2025-01-15T15:00:00Z",
  "service": "Request Management System",
  "version": "1.0.0"
}
```

#### `GET /api/v1/health/`
Альтернативный базовый endpoint

#### `GET /api/v1/health/status`
Общий статус системы с минимальной информацией

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T15:00:00Z",
  "checks_count": 6,
  "healthy_count": 6
}
```

### Защищенные endpoints (требуют авторизации администратора)

#### `GET /api/v1/health/detailed`
Детальная проверка здоровья всех систем

**Параметры:**
- `use_cache` (bool): использовать кешированные результаты (по умолчанию true)

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T15:00:00Z",
  "checks": {
    "database_connection": {
      "status": "healthy",
      "message": "Database connection is healthy",
      "duration_ms": 45.2,
      "details": {
        "response_time_ms": 45.2
      }
    },
    "database_performance": {
      "status": "healthy",
      "message": "Query performance is excellent",
      "duration_ms": 89.1,
      "details": {
        "query_time_ms": 89.1,
        "total_requests": 1250,
        "recent_requests": 45
      }
    },
    "database_pool": {
      "status": "healthy",
      "message": "Connection pool is healthy",
      "duration_ms": 2.1,
      "details": {
        "size": 10,
        "checked_in": 8,
        "checked_out": 2,
        "overflow": 0,
        "invalid": 0
      }
    },
    "system_resources": {
      "status": "healthy",
      "message": "System resources are healthy",
      "duration_ms": 15.3,
      "details": {
        "cpu_percent": 25.4,
        "memory_percent": 68.2,
        "disk_percent": 45.8,
        "load_average": [0.5, 0.3, 0.2],
        "uptime_hours": 72.5
      }
    },
    "recording_service": {
      "status": "healthy",
      "message": "Recording service is running",
      "duration_ms": 1.2,
      "details": {
        "is_running": true,
        "task_active": true,
        "service_configured": true
      }
    },
    "file_storage": {
      "status": "healthy",
      "message": "File storage is healthy",
      "duration_ms": 8.7,
      "details": {
        "media_dir": "/path/to/media",
        "exists": true,
        "writable": true,
        "free_space_percent": 85.3
      }
    }
  },
  "system_metrics": {
    "cpu_percent": 25.4,
    "memory_percent": 68.2,
    "disk_percent": 45.8,
    "load_average": [0.5, 0.3, 0.2],
    "uptime_seconds": 261000,
    "timestamp": "2025-01-15T15:00:00Z"
  },
  "summary": {
    "total_checks": 6,
    "healthy": 6,
    "degraded": 0,
    "unhealthy": 0,
    "unknown": 0
  }
}
```

#### `GET /api/v1/health/database`
Проверка здоровья базы данных

**Ответ:**
```json
{
  "database_health": {
    "connection": {
      "status": "healthy",
      "message": "Database connection is healthy",
      "duration_ms": 45.2,
      "details": {
        "response_time_ms": 45.2
      }
    },
    "performance": {
      "status": "healthy",
      "message": "Query performance is excellent",
      "duration_ms": 89.1,
      "details": {
        "query_time_ms": 89.1,
        "total_requests": 1250,
        "recent_requests": 45
      }
    },
    "pool": {
      "status": "healthy",
      "message": "Connection pool is healthy",
      "duration_ms": 2.1,
      "details": {
        "size": 10,
        "checked_in": 8,
        "checked_out": 2,
        "overflow": 0,
        "invalid": 0
      }
    }
  },
  "timestamp": "2025-01-15T15:00:00Z"
}
```

#### `GET /api/v1/health/system`
Проверка здоровья системы

**Ответ:**
```json
{
  "system_health": {
    "status": "healthy",
    "message": "System resources are healthy",
    "duration_ms": 15.3,
    "details": {
      "cpu_percent": 25.4,
      "memory_percent": 68.2,
      "disk_percent": 45.8,
      "load_average": [0.5, 0.3, 0.2],
      "uptime_hours": 72.5
    }
  },
  "system_metrics": {
    "cpu_percent": 25.4,
    "memory_percent": 68.2,
    "disk_percent": 45.8,
    "load_average": [0.5, 0.3, 0.2],
    "uptime_hours": 72.5,
    "timestamp": "2025-01-15T15:00:00Z"
  }
}
```

#### `GET /api/v1/health/services`
Проверка здоровья сервисов

**Ответ:**
```json
{
  "services_health": {
    "recording_service": {
      "status": "healthy",
      "message": "Recording service is running",
      "duration_ms": 1.2,
      "details": {
        "is_running": true,
        "task_active": true,
        "service_configured": true
      }
    },
    "file_storage": {
      "status": "healthy",
      "message": "File storage is healthy",
      "duration_ms": 8.7,
      "details": {
        "media_dir": "/path/to/media",
        "exists": true,
        "writable": true,
        "free_space_percent": 85.3
      }
    }
  },
  "timestamp": "2025-01-15T15:00:00Z"
}
```

#### `GET /api/v1/health/metrics`
Получение метрик производительности

**Ответ:**
```json
{
  "metrics": {
    "system": {
      "cpu_percent": 25.4,
      "memory_percent": 68.2,
      "disk_percent": 45.8,
      "load_average": [0.5, 0.3, 0.2],
      "uptime_seconds": 261000
    },
    "timestamp": "2025-01-15T15:00:00Z"
  }
}
```

#### `POST /api/v1/health/refresh`
Принудительное обновление кеша health checks

**Ответ:**
```json
{
  "message": "Health cache refreshed successfully",
  "health_summary": {
    // ... полная информация о здоровье
  }
}
```

## Статусы здоровья

### Уровни статусов

1. **HEALTHY** (`healthy`) - Все системы работают нормально
2. **DEGRADED** (`degraded`) - Есть проблемы, но система функционирует
3. **UNHEALTHY** (`unhealthy`) - Критические проблемы, требующие немедленного внимания
4. **UNKNOWN** (`unknown`) - Не удалось определить статус

### Критерии оценки

#### База данных
- **Connection**: Успешное подключение к БД
- **Performance**: 
  - < 100ms - excellent (healthy)
  - < 500ms - good (healthy)
  - < 1000ms - degraded
  - >= 1000ms - unhealthy
- **Pool**: Использование пула соединений
  - < 70% - healthy
  - < 90% - degraded
  - >= 90% - unhealthy

#### Система
- **CPU**: > 90% - проблема
- **Memory**: > 90% - проблема
- **Disk**: > 90% - проблема

#### Сервисы
- **Recording Service**: Статус работы фонового сервиса
- **File Storage**: Доступность и место на диске
  - < 5% свободного места - unhealthy
  - < 15% свободного места - degraded

## Кеширование

- Результаты проверок кешируются на **30 секунд**
- Можно принудительно обновить кеш через `POST /api/v1/health/refresh`
- Параметр `use_cache=false` заставляет выполнить новые проверки

## Мониторинг в продакшене

### Рекомендации по мониторингу

1. **Автоматические проверки**
   ```bash
   # Проверка каждые 30 секунд
   curl -f http://localhost:8000/health || exit 1
   ```

2. **Детальный мониторинг**
   ```bash
   # Каждые 5 минут
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/v1/health/detailed
   ```

3. **Метрики для Prometheus**
   ```bash
   # Экспорт метрик
   curl -H "Authorization: Bearer $TOKEN" \
        http://localhost:8000/api/v1/health/metrics
   ```

### Алерты

Настройте алерты для:
- Статус `unhealthy` или `unknown`
- Высокое использование ресурсов (CPU > 80%, Memory > 85%)
- Медленные запросы к БД (> 500ms)
- Проблемы с файловым хранилищем

### Логирование

Все health checks логируются:
```
2025-01-15 15:00:00 - app.monitoring - INFO - Running comprehensive health checks
2025-01-15 15:00:00 - app.monitoring - INFO - Database connection check completed in 45.2ms
2025-01-15 15:00:00 - app.monitoring - WARNING - High CPU usage detected: 95%
```

## Интеграция с внешними системами

### Kubernetes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/health/status
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Docker Compose
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Nginx
```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

## Расширение системы

### Добавление новых проверок

1. Создайте новый checker в `monitoring.py`
2. Добавьте проверку в `HealthMonitor.run_all_checks()`
3. Обновите API endpoints при необходимости

### Пример нового checker'а

```python
class CustomHealthChecker:
    async def check_external_api(self) -> HealthCheck:
        start_time = time.time()
        try:
            # Ваша проверка
            response = await external_api_call()
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="external_api",
                status=HealthStatus.HEALTHY,
                message="External API is responding",
                details={"response_time_ms": duration},
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="external_api",
                status=HealthStatus.UNHEALTHY,
                message=f"External API failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )
```

## Безопасность

- Публичные endpoints возвращают минимальную информацию
- Детальная информация доступна только администраторам
- Логирование всех обращений к health checks
- Защита от DDoS через rate limiting

## Производительность

- **Кеширование**: Результаты кешируются на 60 секунд
- **Параллельное выполнение**: Все проверки выполняются одновременно
- **Быстрые проверки**: Базовые endpoint'ы отвечают за ~5ms
- **Детальные проверки**: Полная проверка занимает ~50ms (с кешем)
- **Неблокирующие операции**: psutil вызывается без блокировки
- **Минимальное влияние**: Таймауты для предотвращения зависания 