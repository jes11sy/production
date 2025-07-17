# 📊 НАСТРОЙКА GRAFANA И PROMETHEUS

## 🎯 Обзор

Система визуализации метрик состоит из:
- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация и дашборды
- **FastAPI** - экспорт метрик в формате Prometheus

---

## 📋 Требования

- Python 3.8+
- Docker (опционально, для быстрого запуска)
- Prometheus
- Grafana

---

## 🚀 Быстрый запуск с Docker

### 1. Создайте docker-compose.yml:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana_dashboards:/etc/grafana/provisioning/dashboards

volumes:
  prometheus_data:
  grafana_data:
```

### 2. Запустите сервисы:

```bash
docker-compose up -d
```

---

## ⚙️ Ручная настройка

### Шаг 1: Установка Prometheus

#### Windows:
1. Скачайте Prometheus с https://prometheus.io/download/
2. Распакуйте в `C:\prometheus`
3. Скопируйте `prometheus.yml` в папку с Prometheus
4. Запустите: `prometheus.exe --config.file=prometheus.yml`

#### Linux/macOS:
```bash
# Скачайте и установите Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvf prometheus-2.45.0.linux-amd64.tar.gz
cd prometheus-2.45.0

# Скопируйте конфигурацию
cp ../backend/prometheus.yml .

# Запустите
./prometheus --config.file=prometheus.yml
```

### Шаг 2: Установка Grafana

#### Windows:
1. Скачайте Grafana с https://grafana.com/grafana/download
2. Установите и запустите службу
3. Откройте http://localhost:3000
4. Логин: `admin`, пароль: `admin`

#### Linux/macOS:
```bash
# Ubuntu/Debian
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana

# Запустите
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

---

## 🔧 Настройка

### 1. Настройка Prometheus

Проверьте файл `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'request-backend'
    static_configs:
      - targets: ['localhost:8000']  # Адрес вашего бэкенда
    metrics_path: '/api/v1/metrics/prometheus'
    scrape_interval: 30s
```

### 2. Настройка Grafana

1. **Добавьте источник данных Prometheus:**
   - Откройте Grafana (http://localhost:3000)
   - Перейдите в Configuration → Data Sources
   - Добавьте Prometheus
   - URL: `http://localhost:9090`

2. **Импортируйте дашборд:**
   - Перейдите в Dashboards → Import
   - Загрузите файл `grafana_dashboards/request-system-dashboard.json`

---

## 📊 Доступные метрики

### HTTP метрики:
- `http_requests_total` - общее количество HTTP запросов
- `http_request_duration_seconds` - время выполнения запросов

### Системные метрики:
- `system_cpu_usage_percent` - использование CPU
- `system_memory_usage_bytes` - использование памяти
- `system_disk_usage_percent` - использование диска

### Бизнес метрики:
- `requests_created_total` - созданные заявки
- `transactions_processed_total` - обработанные транзакции
- `users_registered_total` - зарегистрированные пользователи

### База данных:
- `database_connections` - активные соединения
- `database_query_duration_seconds` - время выполнения запросов

### Redis:
- `redis_operations_total` - операции Redis
- `redis_memory_usage_bytes` - использование памяти Redis

### Аутентификация:
- `auth_attempts_total` - попытки аутентификации
- `auth_success_rate` - успешность аутентификации

### Файлы:
- `file_uploads_total` - загрузки файлов
- `file_storage_usage_bytes` - использование файлового хранилища

### Health Checks:
- `health_check_status` - статус проверок здоровья
- `health_check_duration_seconds` - время выполнения проверок

---

## 🔍 Полезные запросы Prometheus

### Топ-5 самых медленных эндпоинтов:
```promql
topk(5, rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))
```

### Ошибки по эндпоинтам:
```promql
sum(rate(http_requests_total{status=~"4..|5.."}[5m])) by (endpoint)
```

### Использование CPU за последний час:
```promql
system_cpu_usage_percent
```

### Количество запросов в секунду:
```promql
rate(http_requests_total[5m])
```

### Успешность аутентификации:
```promql
rate(auth_attempts_total{status="success"}[5m]) / rate(auth_attempts_total[5m])
```

---

## 🚨 Алерты в Grafana

### Пример алерта на высокое использование CPU:

1. Создайте новый алерт в Grafana
2. Условие: `system_cpu_usage_percent > 80`
3. Действие: отправка уведомления в Telegram

### Пример алерта на ошибки:

1. Условие: `rate(http_requests_total{status=~"5.."}[5m]) > 0.1`
2. Действие: отправка уведомления

---

## 🔧 Интеграция с существующими алертами

Метрики Prometheus можно интегрировать с существующей системой Telegram алертов:

```python
# В telegram_alerts.py добавить:
from app.monitoring.prometheus_metrics import metrics_collector

# При превышении порогов отправлять алерты
if cpu_usage > 80:
    await send_telegram_alert("system", f"High CPU usage: {cpu_usage}%")
```

---

## 📈 Расширение метрик

### Добавление новой метрики:

```python
# В prometheus_metrics.py
new_metric = Counter(
    'custom_metric_total',
    'Description of custom metric',
    ['label1', 'label2'],
    registry=registry
)

# Использование
new_metric.labels(label1="value1", label2="value2").inc()
```

### Интеграция в существующий код:

```python
from app.monitoring.prometheus_metrics import metrics_collector

# В вашем API эндпоинте
@router.post("/requests")
async def create_request():
    # ... ваш код ...
    metrics_collector.record_request_created("new", "success")
```

---

## 🐛 Устранение неполадок

### Prometheus не собирает метрики:
1. Проверьте доступность эндпоинта: `curl http://localhost:8000/api/v1/metrics/prometheus`
2. Проверьте конфигурацию в `prometheus.yml`
3. Проверьте логи Prometheus

### Grafana не показывает данные:
1. Проверьте подключение к Prometheus
2. Проверьте правильность запросов PromQL
3. Проверьте временной диапазон

### Метрики не обновляются:
1. Проверьте, что бэкенд запущен
2. Проверьте интервал сбора в Prometheus
3. Проверьте логи приложения

---

## 📚 Полезные ссылки

- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)

---

## ✅ Проверка работы

1. **Проверьте эндпоинт метрик:**
   ```bash
   curl http://localhost:8000/api/v1/metrics/prometheus
   ```

2. **Проверьте Prometheus:**
   - Откройте http://localhost:9090
   - Перейдите в Status → Targets
   - Убедитесь, что target "request-backend" в состоянии UP

3. **Проверьте Grafana:**
   - Откройте http://localhost:3000
   - Импортируйте дашборд
   - Убедитесь, что данные отображаются

---

**Система готова к использованию!** 🎉 