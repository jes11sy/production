"""
Интеграция системы метрик с существующими функциями
"""

import time
import asyncio
from functools import wraps
from typing import Callable, Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.monitoring.metrics import (
    metrics_collector,
    performance_collector,
    business_collector
)

logger = logging.getLogger(__name__)


def track_database_operation(operation_name: str):
    """Декоратор для отслеживания операций с базой данных"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Записываем успешную операцию
                performance_collector.record_db_query(operation_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Записываем неуспешную операцию
                performance_collector.record_db_query(f"{operation_name}_error", duration)
                
                # Увеличиваем счетчик ошибок
                metrics_collector.increment("db_errors_total", tags={"operation": operation_name})
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                performance_collector.record_db_query(operation_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_collector.record_db_query(f"{operation_name}_error", duration)
                metrics_collector.increment("db_errors_total", tags={"operation": operation_name})
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_api_endpoint(endpoint_name: str):
    """Декоратор для отслеживания API endpoints"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Записываем успешный запрос
                metrics_collector.record(
                    "api_endpoint_duration",
                    duration,
                    tags={"endpoint": endpoint_name, "status": "success"}
                )
                
                metrics_collector.increment(
                    "api_endpoint_calls",
                    tags={"endpoint": endpoint_name, "status": "success"}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Записываем неуспешный запрос
                metrics_collector.record(
                    "api_endpoint_duration",
                    duration,
                    tags={"endpoint": endpoint_name, "status": "error"}
                )
                
                metrics_collector.increment(
                    "api_endpoint_calls",
                    tags={"endpoint": endpoint_name, "status": "error"}
                )
                
                # Записываем тип ошибки
                metrics_collector.increment(
                    "api_errors_total",
                    tags={"endpoint": endpoint_name, "error_type": type(e).__name__}
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics_collector.record(
                    "api_endpoint_duration",
                    duration,
                    tags={"endpoint": endpoint_name, "status": "success"}
                )
                
                metrics_collector.increment(
                    "api_endpoint_calls",
                    tags={"endpoint": endpoint_name, "status": "success"}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                metrics_collector.record(
                    "api_endpoint_duration",
                    duration,
                    tags={"endpoint": endpoint_name, "status": "error"}
                )
                
                metrics_collector.increment(
                    "api_endpoint_calls",
                    tags={"endpoint": endpoint_name, "status": "error"}
                )
                
                metrics_collector.increment(
                    "api_errors_total",
                    tags={"endpoint": endpoint_name, "error_type": type(e).__name__}
                )
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_business_event(event_name: str, value: float = 1):
    """Декоратор для отслеживания бизнес-событий"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Записываем успешное бизнес-событие
                metrics_collector.increment(
                    f"business_event_{event_name}",
                    value,
                    tags={"status": "success"}
                )
                
                return result
            except Exception as e:
                # Записываем неуспешное бизнес-событие
                metrics_collector.increment(
                    f"business_event_{event_name}",
                    value,
                    tags={"status": "error", "error_type": type(e).__name__}
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                metrics_collector.increment(
                    f"business_event_{event_name}",
                    value,
                    tags={"status": "success"}
                )
                
                return result
            except Exception as e:
                metrics_collector.increment(
                    f"business_event_{event_name}",
                    value,
                    tags={"status": "error", "error_type": type(e).__name__}
                )
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_cache_operation(cache_name: str):
    """Декоратор для отслеживания операций с кэшем"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Определяем, было ли это попадание или промах
                if result is not None:
                    performance_collector.record_cache_hit()
                    metrics_collector.increment(
                        "cache_operations",
                        tags={"cache": cache_name, "result": "hit"}
                    )
                else:
                    performance_collector.record_cache_miss()
                    metrics_collector.increment(
                        "cache_operations",
                        tags={"cache": cache_name, "result": "miss"}
                    )
                
                return result
            except Exception as e:
                metrics_collector.increment(
                    "cache_errors",
                    tags={"cache": cache_name, "error_type": type(e).__name__}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                if result is not None:
                    performance_collector.record_cache_hit()
                    metrics_collector.increment(
                        "cache_operations",
                        tags={"cache": cache_name, "result": "hit"}
                    )
                else:
                    performance_collector.record_cache_miss()
                    metrics_collector.increment(
                        "cache_operations",
                        tags={"cache": cache_name, "result": "miss"}
                    )
                
                return result
            except Exception as e:
                metrics_collector.increment(
                    "cache_errors",
                    tags={"cache": cache_name, "error_type": type(e).__name__}
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_file_operation(operation_type: str):
    """Декоратор для отслеживания файловых операций"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Записываем успешную файловую операцию
                metrics_collector.record(
                    "file_operation_duration",
                    duration,
                    tags={"operation": operation_type, "status": "success"}
                )
                
                metrics_collector.increment(
                    "file_operations_total",
                    tags={"operation": operation_type, "status": "success"}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                metrics_collector.record(
                    "file_operation_duration",
                    duration,
                    tags={"operation": operation_type, "status": "error"}
                )
                
                metrics_collector.increment(
                    "file_operations_total",
                    tags={"operation": operation_type, "status": "error"}
                )
                
                metrics_collector.increment(
                    "file_operation_errors",
                    tags={"operation": operation_type, "error_type": type(e).__name__}
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                metrics_collector.record(
                    "file_operation_duration",
                    duration,
                    tags={"operation": operation_type, "status": "success"}
                )
                
                metrics_collector.increment(
                    "file_operations_total",
                    tags={"operation": operation_type, "status": "success"}
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                metrics_collector.record(
                    "file_operation_duration",
                    duration,
                    tags={"operation": operation_type, "status": "error"}
                )
                
                metrics_collector.increment(
                    "file_operations_total",
                    tags={"operation": operation_type, "status": "error"}
                )
                
                metrics_collector.increment(
                    "file_operation_errors",
                    tags={"operation": operation_type, "error_type": type(e).__name__}
                )
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class MetricsContext:
    """Контекстный менеджер для группировки метрик"""
    
    def __init__(self, context_name: str, tags: Optional[Dict[str, str]] = None):
        self.context_name = context_name
        self.tags = tags or {}
        self.start_time = None
        self.metrics_recorded = []
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Записываем общую продолжительность контекста
            metrics_collector.record(
                f"context_{self.context_name}_duration",
                duration,
                self.tags
            )
            
            # Записываем количество метрик в контексте
            metrics_collector.record(
                f"context_{self.context_name}_metrics_count",
                len(self.metrics_recorded),
                self.tags
            )
            
            # Записываем статус выполнения
            status = "error" if exc_type else "success"
            metrics_collector.increment(
                f"context_{self.context_name}_executions",
                tags={**self.tags, "status": status}
            )
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Запись метрики в контексте"""
        combined_tags = {**self.tags, **(tags or {})}
        metrics_collector.record(name, value, combined_tags)
        self.metrics_recorded.append(name)
    
    def increment_metric(self, name: str, value: float = 1, tags: Optional[Dict[str, str]] = None):
        """Увеличение метрики в контексте"""
        combined_tags = {**self.tags, **(tags or {})}
        metrics_collector.increment(name, value, combined_tags)
        self.metrics_recorded.append(name)


async def collect_request_lifecycle_metrics(
    request_id: str,
    user_id: Optional[str] = None,
    city_id: Optional[str] = None
):
    """Сбор метрик жизненного цикла заявки"""
    tags = {"request_id": request_id}
    
    if user_id:
        tags["user_id"] = user_id
    if city_id:
        tags["city_id"] = city_id
    
    # Увеличиваем счетчик создания заявок
    metrics_collector.increment("request_lifecycle_created", tags=tags)
    
    # Записываем время создания для последующего анализа
    metrics_collector.record(
        "request_lifecycle_timestamp",
        time.time(),
        tags={**tags, "stage": "created"}
    )


async def collect_transaction_metrics(
    transaction_id: str,
    amount: float,
    transaction_type: str,
    user_id: Optional[str] = None
):
    """Сбор метрик транзакций"""
    tags = {
        "transaction_id": transaction_id,
        "type": transaction_type
    }
    
    if user_id:
        tags["user_id"] = user_id
    
    # Увеличиваем счетчик транзакций
    metrics_collector.increment("transaction_created", tags=tags)
    
    # Записываем сумму транзакции
    metrics_collector.record("transaction_amount", amount, tags)
    
    # Обновляем общую сумму транзакций
    current_total = metrics_collector.get_latest_value("transactions_total_amount") or 0
    metrics_collector.set_gauge("transactions_total_amount", current_total + amount)


async def collect_user_activity_metrics(
    user_id: str,
    activity_type: str,
    duration: Optional[float] = None
):
    """Сбор метрик активности пользователей"""
    tags = {
        "user_id": user_id,
        "activity": activity_type
    }
    
    # Увеличиваем счетчик активности
    metrics_collector.increment("user_activity", tags=tags)
    
    if duration:
        # Записываем продолжительность активности
        metrics_collector.record("user_activity_duration", duration, tags)
    
    # Обновляем время последней активности пользователя
    metrics_collector.record(
        "user_last_activity",
        time.time(),
        {"user_id": user_id}
    )


# Экспорт декораторов и функций
__all__ = [
    'track_database_operation',
    'track_api_endpoint',
    'track_business_event',
    'track_cache_operation',
    'track_file_operation',
    'MetricsContext',
    'collect_request_lifecycle_metrics',
    'collect_transaction_metrics',
    'collect_user_activity_metrics'
] 