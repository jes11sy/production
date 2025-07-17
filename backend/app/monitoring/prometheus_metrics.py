"""
Prometheus метрики для мониторинга системы
"""
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess
)
import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Создаем registry для метрик
registry = CollectorRegistry()

# HTTP метрики
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# Бизнес метрики
requests_created_total = Counter(
    'requests_created_total',
    'Total number of requests created',
    ['request_type', 'status'],
    registry=registry
)

transactions_processed_total = Counter(
    'transactions_processed_total',
    'Total number of transactions processed',
    ['transaction_type', 'status'],
    registry=registry
)

users_registered_total = Counter(
    'users_registered_total',
    'Total number of users registered',
    ['user_type'],
    registry=registry
)

# Системные метрики
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

system_disk_usage = Gauge(
    'system_disk_usage_percent',
    'Disk usage percentage',
    registry=registry
)

# База данных метрики
database_connections = Gauge(
    'database_connections',
    'Number of active database connections',
    ['state'],
    registry=registry
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    registry=registry
)

# Redis метрики
redis_operations_total = Counter(
    'redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status'],
    registry=registry
)

redis_memory_usage_bytes = Gauge(
    'redis_memory_usage_bytes',
    'Redis memory usage in bytes',
    registry=registry
)

# Аутентификация метрики
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['method', 'status'],
    registry=registry
)

auth_success_rate = Gauge(
    'auth_success_rate',
    'Authentication success rate',
    registry=registry
)

# Файловые операции
file_uploads_total = Counter(
    'file_uploads_total',
    'Total number of file uploads',
    ['file_type', 'status'],
    registry=registry
)

file_storage_usage_bytes = Gauge(
    'file_storage_usage_bytes',
    'File storage usage in bytes',
    registry=registry
)

# Кастомные метрики для health checks
health_check_status = Gauge(
    'health_check_status',
    'Health check status (1 = healthy, 0 = unhealthy)',
    ['service'],
    registry=registry
)

health_check_duration_seconds = Histogram(
    'health_check_duration_seconds',
    'Health check duration in seconds',
    ['service'],
    registry=registry
)


class MetricsCollector:
    """Сборщик метрик для системы"""
    
    def __init__(self):
        self.last_update = time.time()
        self.update_interval = 60  # Обновляем каждые 60 секунд
    
    def update_system_metrics(self):
        """Обновление системных метрик"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # Память
            memory = psutil.virtual_memory()
            system_memory_usage.set(memory.used)
            
            # Диск
            disk = psutil.disk_usage('/')
            system_disk_usage.set(disk.percent)
            
            logger.debug(f"System metrics updated: CPU={cpu_percent}%, Memory={memory.percent}%, Disk={disk.percent}%")
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Записать метрику HTTP запроса"""
        try:
            http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        except Exception as e:
            logger.error(f"Error recording HTTP metric: {e}")
    
    def record_request_created(self, request_type: str, status: str):
        """Записать метрику создания заявки"""
        try:
            requests_created_total.labels(request_type=request_type, status=status).inc()
        except Exception as e:
            logger.error(f"Error recording request metric: {e}")
    
    def record_transaction_processed(self, transaction_type: str, status: str):
        """Записать метрику обработки транзакции"""
        try:
            transactions_processed_total.labels(transaction_type=transaction_type, status=status).inc()
        except Exception as e:
            logger.error(f"Error recording transaction metric: {e}")
    
    def record_user_registered(self, user_type: str):
        """Записать метрику регистрации пользователя"""
        try:
            users_registered_total.labels(user_type=user_type).inc()
        except Exception as e:
            logger.error(f"Error recording user metric: {e}")
    
    def record_auth_attempt(self, method: str, status: str):
        """Записать метрику попытки аутентификации"""
        try:
            auth_attempts_total.labels(method=method, status=status).inc()
        except Exception as e:
            logger.error(f"Error recording auth metric: {e}")
    
    def record_file_upload(self, file_type: str, status: str):
        """Записать метрику загрузки файла"""
        try:
            file_uploads_total.labels(file_type=file_type, status=status).inc()
        except Exception as e:
            logger.error(f"Error recording file upload metric: {e}")
    
    def record_redis_operation(self, operation: str, status: str):
        """Записать метрику операции Redis"""
        try:
            redis_operations_total.labels(operation=operation, status=status).inc()
        except Exception as e:
            logger.error(f"Error recording Redis metric: {e}")
    
    def record_database_connection(self, state: str, count: int):
        """Записать метрику соединений с базой данных"""
        try:
            database_connections.labels(state=state).set(count)
        except Exception as e:
            logger.error(f"Error recording database connection metric: {e}")
    
    def record_health_check(self, service: str, status: bool, duration: float):
        """Записать метрику health check"""
        try:
            health_check_status.labels(service=service).set(1 if status else 0)
            health_check_duration_seconds.labels(service=service).observe(duration)
        except Exception as e:
            logger.error(f"Error recording health check metric: {e}")
    
    def update_auth_success_rate(self, success_rate: float):
        """Обновить метрику успешности аутентификации"""
        try:
            auth_success_rate.set(success_rate)
        except Exception as e:
            logger.error(f"Error updating auth success rate: {e}")
    
    def update_redis_memory_usage(self, memory_bytes: int):
        """Обновить метрику использования памяти Redis"""
        try:
            redis_memory_usage_bytes.set(memory_bytes)
        except Exception as e:
            logger.error(f"Error updating Redis memory usage: {e}")
    
    def update_file_storage_usage(self, storage_bytes: int):
        """Обновить метрику использования файлового хранилища"""
        try:
            file_storage_usage_bytes.set(storage_bytes)
        except Exception as e:
            logger.error(f"Error updating file storage usage: {e}")


# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()


def get_metrics():
    """Получить метрики в формате Prometheus"""
    return generate_latest(registry)


def get_metrics_content_type():
    """Получить content type для метрик"""
    return CONTENT_TYPE_LATEST 