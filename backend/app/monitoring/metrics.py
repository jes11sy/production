"""
Система сбора метрик производительности и бизнес-показателей
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from contextlib import asynccontextmanager
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

from sqlalchemy import text, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Response

from app.core.database import get_db
from app.core.models import Request as RequestModel, Transaction, City, Master, Employee, Administrator
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Типы метрик"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    BUSINESS = "business"


@dataclass
class MetricDefinition:
    """Определение метрики"""
    name: str
    type: MetricType
    description: str
    unit: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class MetricValue:
    """Значение метрики"""
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TimerContext:
    """Контекстный менеджер для измерения времени"""
    
    def __init__(self, collector: 'MetricsCollector', name: str, tags: Dict[str, str]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record(self.name, duration, self.tags)


class MetricsCollector:
    """Основной класс для сбора метрик с улучшенной thread-safety"""
    
    def __init__(self, max_values: int = 1000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_values))
        self.definitions: Dict[str, MetricDefinition] = {}
        self._lock = threading.RLock()  # Используем RLock для избежания deadlock
        self._running = False
        self._background_task: Optional[asyncio.Task] = None
        self._db_operation_semaphore = asyncio.Semaphore(5)  # Ограничиваем concurrent DB операции
        
    def register_metric(self, definition: MetricDefinition):
        """Регистрация метрики"""
        with self._lock:
            self.definitions[definition.name] = definition
            logger.info(f"Registered metric: {definition.name}")
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Запись значения метрики"""
        tags = tags or {}
        metadata = metadata or {}
        
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags,
            metadata=metadata
        )
        
        with self._lock:
            self.metrics[name].append(metric_value)
    
    def increment(self, name: str, value: float = 1, tags: Optional[Dict[str, str]] = None):
        """Увеличение счетчика"""
        with self._lock:
            current = self.get_latest_value_unsafe(name) or 0
            self.record(name, current + value, tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Установка значения gauge"""
        self.record(name, value, tags or {})
    
    def time_operation(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Контекстный менеджер для измерения времени операций"""
        return TimerContext(self, name, tags or {})
    
    def get_latest_value_unsafe(self, name: str) -> Optional[float]:
        """Получение последнего значения метрики БЕЗ блокировки (для внутреннего использования)"""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1].value
        return None
    
    def get_latest_value(self, name: str) -> Optional[float]:
        """Получение последнего значения метрики"""
        with self._lock:
            return self.get_latest_value_unsafe(name)
    
    def get_values(self, name: str, since: Optional[datetime] = None, limit: Optional[int] = None) -> List[MetricValue]:
        """Получение значений метрики"""
        with self._lock:
            if name not in self.metrics:
                return []
            
            values = list(self.metrics[name])
            
            if since:
                values = [v for v in values if v.timestamp >= since]
            
            if limit:
                values = values[-limit:]
            
            return values
    
    def get_statistics(self, name: str, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Получение статистики по метрике"""
        values = self.get_values(name, since)
        if not values:
            return {}
        
        numeric_values = [v.value for v in values]
        
        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "sum": sum(numeric_values),
            "latest": numeric_values[-1],
            "first_timestamp": values[0].timestamp.isoformat(),
            "latest_timestamp": values[-1].timestamp.isoformat()
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Получение всех метрик"""
        result = {}
        with self._lock:
            for name in self.metrics:
                result[name] = {
                    "definition": self.definitions.get(name),
                    "latest_value": self.get_latest_value_unsafe(name),
                    "count": len(self.metrics[name]),
                    "statistics": self.get_statistics(name)
                }
        return result
    
    def clear_old_metrics(self, older_than: timedelta = timedelta(hours=24)):
        """Очистка старых метрик"""
        cutoff_time = datetime.utcnow() - older_than
        
        with self._lock:
            for name in self.metrics:
                original_count = len(self.metrics[name])
                # Фильтруем значения, оставляя только новые
                filtered_values = deque(
                    [v for v in self.metrics[name] if v.timestamp >= cutoff_time],
                    maxlen=self.metrics[name].maxlen
                )
                self.metrics[name] = filtered_values
                
                cleaned_count = original_count - len(filtered_values)
                if cleaned_count > 0:
                    logger.info(f"Cleaned {cleaned_count} old values for metric {name}")


class BusinessMetricsCollector:
    """Сборщик бизнес-метрик с улучшенной thread-safety"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self._collection_lock = asyncio.Lock()  # Async lock для DB операций
        self.register_business_metrics()
    
    def register_business_metrics(self):
        """Регистрация бизнес-метрик"""
        business_metrics = [
            MetricDefinition("requests_total", MetricType.COUNTER, "Общее количество заявок"),
            MetricDefinition("requests_by_status", MetricType.COUNTER, "Заявки по статусам", tags=["status"]),
            MetricDefinition("requests_by_city", MetricType.COUNTER, "Заявки по городам", tags=["city"]),
            MetricDefinition("transactions_total", MetricType.COUNTER, "Общее количество транзакций"),
            MetricDefinition("transactions_amount", MetricType.GAUGE, "Сумма транзакций", "RUB"),
            MetricDefinition("active_users", MetricType.GAUGE, "Активные пользователи"),
            MetricDefinition("conversion_rate", MetricType.GAUGE, "Конверсия заявок", "%"),
            MetricDefinition("avg_processing_time", MetricType.GAUGE, "Среднее время обработки", "seconds"),
            MetricDefinition("revenue_daily", MetricType.GAUGE, "Дневная выручка", "RUB"),
            MetricDefinition("calls_total", MetricType.COUNTER, "Общее количество звонков"),
            MetricDefinition("call_duration_avg", MetricType.GAUGE, "Средняя длительность звонка", "seconds"),
        ]
        
        for metric in business_metrics:
            self.metrics.register_metric(metric)
    
    async def collect_request_metrics(self, db: AsyncSession):
        """Сбор метрик по заявкам с Redis кешированием и улучшенной thread-safety"""
        async with self.metrics._db_operation_semaphore:
            try:
                # Пытаемся получить из кеша
                cached_metrics = await cache_manager.get("request_metrics")
                if cached_metrics:
                    logger.debug("Using cached request metrics")
                    for metric_name, value in cached_metrics.items():
                        if isinstance(value, dict):
                            for tag_key, tag_value in value.items():
                                self.metrics.set_gauge(metric_name, tag_value, {"status": tag_key} if metric_name == "requests_by_status" else {"city": tag_key})
                        else:
                            self.metrics.set_gauge(metric_name, value)
                    return
                
                # Собираем метрики из БД
                logger.debug("Collecting fresh request metrics from database")
                
                # Общее количество заявок
                total_requests = await db.scalar(
                    text("SELECT COUNT(*) FROM requests")
                )
                self.metrics.set_gauge("requests_total", total_requests)
                
                # Заявки по статусам
                status_counts = await db.execute(
                    text("SELECT status, COUNT(*) FROM requests GROUP BY status")
                )
                status_data = {}
                for status, count in status_counts:
                    self.metrics.set_gauge("requests_by_status", count, {"status": status})
                    status_data[status] = count
                
                # Заявки по городам
                city_counts = await db.execute(
                    text("""
                        SELECT c.name, COUNT(r.id) 
                        FROM requests r 
                        JOIN cities c ON r.city_id = c.id 
                        GROUP BY c.name
                    """)
                )
                city_data = {}
                for city, count in city_counts:
                    self.metrics.set_gauge("requests_by_city", count, {"city": city})
                    city_data[city] = count
                
                # Конверсия заявок
                completed_requests = await db.scalar(
                    text("SELECT COUNT(*) FROM requests WHERE status = 'completed'")
                )
                conversion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
                self.metrics.set_gauge("conversion_rate", conversion_rate)
                
                # Среднее время обработки
                avg_processing_time = await db.scalar(
                    text("""
                        SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)))
                        FROM requests 
                        WHERE status = 'completed' AND updated_at IS NOT NULL
                    """)
                )
                processing_time = float(avg_processing_time) if avg_processing_time else 0
                if processing_time > 0:
                    self.metrics.set_gauge("avg_processing_time", processing_time)
                
                # Кешируем результаты на 5 минут
                cache_data = {
                    "requests_total": total_requests,
                    "requests_by_status": status_data,
                    "requests_by_city": city_data,
                    "conversion_rate": conversion_rate,
                    "avg_processing_time": processing_time
                }
                await cache_manager.set("request_metrics", cache_data, ttl=300)
                
            except Exception as e:
                logger.error(f"Error collecting request metrics: {e}")
    
    async def collect_transaction_metrics(self, db: AsyncSession):
        """Сбор метрик по транзакциям с Redis кешированием и улучшенной thread-safety"""
        async with self.metrics._db_operation_semaphore:
            try:
                # Пытаемся получить из кеша
                cached_metrics = await cache_manager.get("transaction_metrics")
                if cached_metrics:
                    logger.debug("Using cached transaction metrics")
                    for metric_name, value in cached_metrics.items():
                        self.metrics.set_gauge(metric_name, value)
                    return
                
                logger.debug("Collecting fresh transaction metrics from database")
                
                # Общее количество транзакций
                total_transactions = await db.scalar(
                    text("SELECT COUNT(*) FROM transactions")
                )
                self.metrics.set_gauge("transactions_total", total_transactions)
                
                # Общая сумма транзакций
                total_amount = await db.scalar(
                    text("SELECT COALESCE(SUM(amount), 0) FROM transactions")
                )
                amount_value = float(total_amount or 0)
                self.metrics.set_gauge("transactions_amount", amount_value)
                
                # Дневная выручка
                today_revenue = await db.scalar(
                    text("""
                        SELECT COALESCE(SUM(amount), 0) 
                        FROM transactions 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)
                )
                revenue_value = float(today_revenue or 0)
                self.metrics.set_gauge("revenue_daily", revenue_value)
                
                # Кешируем результаты на 5 минут
                cache_data = {
                    "transactions_total": total_transactions,
                    "transactions_amount": amount_value,
                    "revenue_daily": revenue_value
                }
                await cache_manager.set("transaction_metrics", cache_data, ttl=300)
                
            except Exception as e:
                logger.error(f"Error collecting transaction metrics: {e}")
    
    async def collect_user_metrics(self, db: AsyncSession):
        """Сбор метрик по пользователям с Redis кешированием и улучшенной thread-safety"""
        async with self.metrics._db_operation_semaphore:
            try:
                # Пытаемся получить из кеша
                cached_metrics = await cache_manager.get("user_metrics")
                if cached_metrics:
                    logger.debug("Using cached user metrics")
                    for metric_name, value in cached_metrics.items():
                        self.metrics.set_gauge(metric_name, value)
                    return
                
                logger.debug("Collecting fresh user metrics from database")
                
                # Активные пользователи (Masters + Employees + Administrators)
                active_masters = await db.scalar(
                    text("SELECT COUNT(*) FROM masters WHERE status = 'active'")
                ) or 0
                
                active_employees = await db.scalar(
                    text("SELECT COUNT(*) FROM employees WHERE status = 'active'")
                ) or 0
                
                active_administrators = await db.scalar(
                    text("SELECT COUNT(*) FROM administrators WHERE status = 'active'")
                ) or 0
                
                total_active_users = active_masters + active_employees + active_administrators
                self.metrics.set_gauge("active_users", total_active_users)
                
                # Кешируем результаты на 10 минут (пользователи меняются реже)
                cache_data = {
                    "active_users": total_active_users,
                    "active_masters": active_masters,
                    "active_employees": active_employees,
                    "active_administrators": active_administrators
                }
                await cache_manager.set("user_metrics", cache_data, ttl=600)
                
            except Exception as e:
                logger.error(f"Error collecting user metrics: {e}")
    
    async def collect_call_metrics(self, db: AsyncSession):
        """Сбор метрик по звонкам с Redis кешированием и улучшенной thread-safety"""
        async with self.metrics._db_operation_semaphore:
            try:
                # Пытаемся получить из кеша
                cached_metrics = await cache_manager.get("call_metrics")
                if cached_metrics:
                    logger.debug("Using cached call metrics")
                    for metric_name, value in cached_metrics.items():
                        if value > 0:  # Записываем только положительные значения
                            self.metrics.set_gauge(metric_name, value)
                    return
                
                logger.debug("Collecting fresh call metrics from database")
                
                # Общее количество звонков (из таблицы requests, где есть запись)
                total_calls = await db.scalar(
                    text("SELECT COUNT(*) FROM requests WHERE recording_file_path IS NOT NULL AND recording_file_path != ''")
                )
                calls_count = total_calls or 0
                if calls_count > 0:
                    self.metrics.set_gauge("calls_total", calls_count)
                
                # Для средней длительности звонков - пока не реализовано, 
                # так как длительность не хранится в текущей схеме
                duration_value = 0
                if duration_value > 0:
                    self.metrics.set_gauge("call_duration_avg", duration_value)
                
                # Кешируем результаты на 5 минут
                cache_data = {
                    "calls_total": calls_count,
                    "call_duration_avg": duration_value
                }
                await cache_manager.set("call_metrics", cache_data, ttl=300)
                
            except Exception as e:
                logger.error(f"Error collecting call metrics: {e}")
    
    async def collect_all_business_metrics(self, db: AsyncSession):
        """Сбор всех бизнес-метрик с блокировкой для предотвращения concurrent operations"""
        async with self._collection_lock:
            try:
                # Выполняем последовательно, чтобы избежать concurrent operations
                await self.collect_request_metrics(db)
                await self.collect_transaction_metrics(db)
                await self.collect_user_metrics(db)
                await self.collect_call_metrics(db)
            except Exception as e:
                logger.error(f"Error in collect_all_business_metrics: {e}")


class PerformanceMetricsCollector:
    """Сборщик метрик производительности"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.register_performance_metrics()
    
    def register_performance_metrics(self):
        """Регистрация метрик производительности"""
        performance_metrics = [
            MetricDefinition("http_requests_total", MetricType.COUNTER, "HTTP запросы", tags=["method", "endpoint", "status"]),
            MetricDefinition("http_request_duration", MetricType.HISTOGRAM, "Время HTTP запросов", "seconds", ["method", "endpoint"]),
            MetricDefinition("db_queries_total", MetricType.COUNTER, "Количество DB запросов"),
            MetricDefinition("db_query_duration", MetricType.HISTOGRAM, "Время DB запросов", "seconds", ["operation"]),
            MetricDefinition("db_connections_active", MetricType.GAUGE, "Активные DB соединения"),
            MetricDefinition("memory_usage", MetricType.GAUGE, "Использование памяти", "MB"),
            MetricDefinition("cpu_usage", MetricType.GAUGE, "Использование CPU", "%"),
            MetricDefinition("response_size", MetricType.HISTOGRAM, "Размер ответа", "bytes", ["endpoint"]),
            MetricDefinition("error_rate", MetricType.GAUGE, "Частота ошибок", "%"),
            MetricDefinition("cache_hits", MetricType.COUNTER, "Попадания в кэш"),
            MetricDefinition("cache_misses", MetricType.COUNTER, "Промахи кэша"),
        ]
        
        for metric in performance_metrics:
            self.metrics.register_metric(metric)
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float, response_size: int):
        """Запись HTTP запроса"""
        tags = {"method": method, "endpoint": endpoint, "status": str(status_code)}
        
        self.metrics.increment("http_requests_total", tags=tags)
        self.metrics.record("http_request_duration", duration, {"method": method, "endpoint": endpoint})
        self.metrics.record("response_size", response_size, {"endpoint": endpoint})
    
    def record_db_query(self, operation: str, duration: float):
        """Запись DB запроса"""
        self.metrics.increment("db_queries_total")
        self.metrics.record("db_query_duration", duration, {"operation": operation})
    
    def record_system_metrics(self):
        """Запись системных метрик"""
        try:
            import psutil
            
            # Использование памяти
            memory = psutil.virtual_memory()
            self.metrics.set_gauge("memory_usage", memory.used / 1024 / 1024)  # MB
            
            # Использование CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.set_gauge("cpu_usage", cpu_percent)
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_cache_hit(self):
        """Запись попадания в кэш"""
        self.metrics.increment("cache_hits")
    
    def record_cache_miss(self):
        """Запись промаха кэша"""
        self.metrics.increment("cache_misses")


class MetricsMiddleware:
    """Middleware для сбора метрик HTTP запросов"""
    
    def __init__(self, performance_collector: PerformanceMetricsCollector):
        self.performance_collector = performance_collector
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Измеряем время выполнения
        duration = time.time() - start_time
        
        # Записываем метрики
        self.performance_collector.record_http_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            duration=duration,
            response_size=int(response.headers.get("content-length", 0))
        )
        
        return response


def metrics_decorator(metric_name: str, metric_type: MetricType = MetricType.TIMER):
    """Декоратор для автоматического сбора метрик"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with metrics_collector.time_operation(metric_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with metrics_collector.time_operation(metric_name):
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Глобальные экземпляры
metrics_collector = MetricsCollector()
performance_collector = PerformanceMetricsCollector(metrics_collector)
business_collector = BusinessMetricsCollector(metrics_collector)


async def collect_metrics_background():
    """Фоновая задача для сбора метрик с улучшенной стабильностью"""
    while True:
        try:
            async for db in get_db():
                # Сбор бизнес-метрик
                await business_collector.collect_all_business_metrics(db)
                
                # Сбор системных метрик
                performance_collector.record_system_metrics()
                
                # Очистка старых метрик
                metrics_collector.clear_old_metrics()
                
                break  # Выходим из цикла async for
                
        except Exception as e:
            logger.error(f"Error in metrics collection background task: {e}")
        
        # Ждем 60 секунд до следующего сбора
        await asyncio.sleep(60)


async def start_metrics_collection():
    """Запуск фоновой задачи сбора метрик"""
    global metrics_collector
    if not metrics_collector._running:
        metrics_collector._running = True
        metrics_collector._background_task = asyncio.create_task(collect_metrics_background())
        logger.info("Metrics collection started")


async def stop_metrics_collection():
    """Остановка фоновой задачи сбора метрик"""
    global metrics_collector
    if metrics_collector._running:
        metrics_collector._running = False
        if metrics_collector._background_task:
            metrics_collector._background_task.cancel()
            try:
                await metrics_collector._background_task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collection stopped")


# Экспорт для использования в других модулях
__all__ = [
    'metrics_collector',
    'performance_collector', 
    'business_collector',
    'MetricsMiddleware',
    'metrics_decorator',
    'start_metrics_collection'
] 