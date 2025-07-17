"""
Расширенный мониторинг connection pool с метриками и алертами
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, event
from collections import deque, defaultdict
import threading

from app.core.database import engine, get_db
from app.core.cache import cache_manager
from app.monitoring.metrics import metrics_collector, MetricType, MetricDefinition

logger = logging.getLogger(__name__)


class PoolStatus(Enum):
    """Статусы состояния пула соединений"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ConnectionPoolMetrics:
    """Метрики пула соединений"""
    timestamp: datetime
    pool_size: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    available_connections: int
    utilization_percent: float
    wait_time_ms: float
    connection_errors: int
    status: PoolStatus
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "pool_size": self.pool_size,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "invalid": self.invalid,
            "total_connections": self.total_connections,
            "available_connections": self.available_connections,
            "utilization_percent": self.utilization_percent,
            "wait_time_ms": self.wait_time_ms,
            "connection_errors": self.connection_errors,
            "status": self.status.value
        }


@dataclass
class SlowQueryInfo:
    """Информация о медленном запросе"""
    query: str
    duration_ms: float
    timestamp: datetime
    connection_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:200] + "..." if len(self.query) > 200 else self.query,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "connection_id": self.connection_id
        }


class ConnectionPoolMonitor:
    """Мониторинг пула соединений с детальной статистикой"""
    
    def __init__(self, slow_query_threshold_ms: float = 1000):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.metrics_history: deque = deque(maxlen=1000)
        self.slow_queries: deque = deque(maxlen=100)
        self.connection_events: deque = deque(maxlen=500)
        self.alerts_sent: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)
        self._lock = threading.RLock()
        
        # Счетчики событий
        self.connection_counters = defaultdict(int)
        self.query_counters = defaultdict(int)
        
        # Регистрируем метрики
        self._register_metrics()
        
        # Подписываемся на события пула
        self._setup_pool_events()
    
    def _register_metrics(self):
        """Регистрация метрик пула соединений"""
        pool_metrics = [
            MetricDefinition("db_pool_size", MetricType.GAUGE, "Размер пула соединений"),
            MetricDefinition("db_pool_checked_out", MetricType.GAUGE, "Активные соединения"),
            MetricDefinition("db_pool_overflow", MetricType.GAUGE, "Overflow соединения"),
            MetricDefinition("db_pool_invalid", MetricType.GAUGE, "Недействительные соединения"),
            MetricDefinition("db_pool_utilization", MetricType.GAUGE, "Использование пула", "%"),
            MetricDefinition("db_pool_wait_time", MetricType.HISTOGRAM, "Время ожидания соединения", "ms"),
            MetricDefinition("db_connection_errors", MetricType.COUNTER, "Ошибки соединений"),
            MetricDefinition("db_connection_created", MetricType.COUNTER, "Созданные соединения"),
            MetricDefinition("db_connection_closed", MetricType.COUNTER, "Закрытые соединения"),
            MetricDefinition("db_slow_queries", MetricType.COUNTER, "Медленные запросы"),
            MetricDefinition("db_query_duration", MetricType.HISTOGRAM, "Время выполнения запросов", "ms"),
            MetricDefinition("db_pool_status", MetricType.GAUGE, "Статус пула (0=healthy, 1=warning, 2=critical)")
        ]
        
        for metric in pool_metrics:
            metrics_collector.register_metric(metric)
    
    def _setup_pool_events(self):
        """Настройка событий пула соединений"""
        pool = engine.pool
        
        @event.listens_for(pool, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Событие подключения"""
            with self._lock:
                self.connection_counters["created"] += 1
                self.connection_events.append({
                    "event": "connect",
                    "timestamp": datetime.now(),
                    "connection_id": id(dbapi_connection)
                })
                metrics_collector.increment("db_connection_created")
        
        @event.listens_for(pool, "close")
        def on_close(dbapi_connection, connection_record):
            """Событие закрытия соединения"""
            with self._lock:
                self.connection_counters["closed"] += 1
                self.connection_events.append({
                    "event": "close",
                    "timestamp": datetime.now(),
                    "connection_id": id(dbapi_connection)
                })
                metrics_collector.increment("db_connection_closed")
        
        @event.listens_for(pool, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Событие получения соединения из пула"""
            with self._lock:
                self.connection_counters["checkout"] += 1
                self.connection_events.append({
                    "event": "checkout",
                    "timestamp": datetime.now(),
                    "connection_id": id(dbapi_connection)
                })
        
        @event.listens_for(pool, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Событие возврата соединения в пул"""
            with self._lock:
                self.connection_counters["checkin"] += 1
                self.connection_events.append({
                    "event": "checkin",
                    "timestamp": datetime.now(),
                    "connection_id": id(dbapi_connection)
                })
    
    def get_pool_metrics(self) -> ConnectionPoolMetrics:
        """Получение текущих метрик пула"""
        pool = engine.pool
        
        # Получаем базовые метрики
        pool_size = getattr(pool, 'size', lambda: 0)()
        checked_out = getattr(pool, 'checkedout', lambda: 0)()
        overflow = getattr(pool, 'overflow', lambda: 0)()
        invalid = getattr(pool, 'invalid', lambda: 0)()
        
        total_connections = pool_size + overflow
        available_connections = max(0, pool_size - checked_out)
        utilization_percent = (checked_out / max(1, pool_size)) * 100
        
        # Определяем статус пула
        status = self._determine_pool_status(utilization_percent, available_connections, invalid)
        
        # Время ожидания (приблизительное)
        wait_time_ms = self._estimate_wait_time(utilization_percent)
        
        metrics = ConnectionPoolMetrics(
            timestamp=datetime.now(),
            pool_size=pool_size,
            checked_out=checked_out,
            overflow=overflow,
            invalid=invalid,
            total_connections=total_connections,
            available_connections=available_connections,
            utilization_percent=utilization_percent,
            wait_time_ms=wait_time_ms,
            connection_errors=self.connection_counters.get("errors", 0),
            status=status
        )
        
        # Сохраняем в историю
        with self._lock:
            self.metrics_history.append(metrics)
        
        # Записываем метрики
        self._record_metrics(metrics)
        
        return metrics
    
    def _determine_pool_status(self, utilization_percent: float, available_connections: int, invalid: int) -> PoolStatus:
        """Определение статуса пула"""
        if invalid > 0:
            return PoolStatus.CRITICAL
        
        if utilization_percent > 90 or available_connections < 2:
            return PoolStatus.CRITICAL
        elif utilization_percent > 70 or available_connections < 5:
            return PoolStatus.WARNING
        else:
            return PoolStatus.HEALTHY
    
    def _estimate_wait_time(self, utilization_percent: float) -> float:
        """Оценка времени ожидания соединения"""
        if utilization_percent < 50:
            return 0.1
        elif utilization_percent < 80:
            return 1.0
        elif utilization_percent < 95:
            return 10.0
        else:
            return 100.0
    
    def _record_metrics(self, metrics: ConnectionPoolMetrics):
        """Запись метрик в систему мониторинга"""
        metrics_collector.set_gauge("db_pool_size", metrics.pool_size)
        metrics_collector.set_gauge("db_pool_checked_out", metrics.checked_out)
        metrics_collector.set_gauge("db_pool_overflow", metrics.overflow)
        metrics_collector.set_gauge("db_pool_invalid", metrics.invalid)
        metrics_collector.set_gauge("db_pool_utilization", metrics.utilization_percent)
        metrics_collector.record("db_pool_wait_time", metrics.wait_time_ms)
        
        # Статус как число
        status_value = {
            PoolStatus.HEALTHY: 0,
            PoolStatus.WARNING: 1,
            PoolStatus.CRITICAL: 2,
            PoolStatus.UNKNOWN: 3
        }[metrics.status]
        metrics_collector.set_gauge("db_pool_status", status_value)
    
    def record_slow_query(self, query: str, duration_ms: float, connection_id: Optional[str] = None):
        """Запись медленного запроса"""
        if duration_ms >= self.slow_query_threshold_ms:
            slow_query = SlowQueryInfo(
                query=query,
                duration_ms=duration_ms,
                timestamp=datetime.now(),
                connection_id=connection_id
            )
            
            with self._lock:
                self.slow_queries.append(slow_query)
                self.query_counters["slow"] += 1
            
            metrics_collector.increment("db_slow_queries")
            metrics_collector.record("db_query_duration", duration_ms, {"type": "slow"})
            
            logger.warning(f"Slow query detected: {duration_ms:.2f}ms - {query[:100]}...")
    
    def record_connection_error(self, error: Exception):
        """Запись ошибки соединения"""
        with self._lock:
            self.connection_counters["errors"] += 1
            self.connection_events.append({
                "event": "error",
                "timestamp": datetime.now(),
                "error": str(error)
            })
        
        metrics_collector.increment("db_connection_errors")
        logger.error(f"Connection error: {error}")
    
    async def check_pool_health(self) -> Dict[str, Any]:
        """Проверка здоровья пула соединений"""
        metrics = self.get_pool_metrics()
        
        # Проверяем алерты
        alerts = self._check_alerts(metrics)
        
        # Получаем статистику
        stats = self.get_pool_statistics()
        
        return {
            "status": metrics.status.value,
            "metrics": metrics.to_dict(),
            "statistics": stats,
            "alerts": alerts,
            "recent_events": list(self.connection_events)[-10:],
            "slow_queries": [q.to_dict() for q in list(self.slow_queries)[-5:]]
        }
    
    def _check_alerts(self, metrics: ConnectionPoolMetrics) -> List[Dict[str, Any]]:
        """Проверка алертов"""
        alerts = []
        now = datetime.now()
        
        # Алерт высокого использования
        if metrics.utilization_percent > 90:
            alert_key = "high_utilization"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "high_utilization",
                    "severity": "critical",
                    "message": f"High pool utilization: {metrics.utilization_percent:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        # Алерт недоступных соединений
        if metrics.available_connections < 2:
            alert_key = "low_connections"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "low_connections",
                    "severity": "critical",
                    "message": f"Low available connections: {metrics.available_connections}",
                    "timestamp": now.isoformat()
                })
        
        # Алерт недействительных соединений
        if metrics.invalid > 0:
            alert_key = "invalid_connections"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "invalid_connections",
                    "severity": "warning",
                    "message": f"Invalid connections detected: {metrics.invalid}",
                    "timestamp": now.isoformat()
                })
        
        # Алерт медленных запросов
        recent_slow_queries = len([q for q in self.slow_queries if now - q.timestamp < timedelta(minutes=5)])
        if recent_slow_queries > 5:
            alert_key = "many_slow_queries"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "many_slow_queries",
                    "severity": "warning",
                    "message": f"Many slow queries in last 5 minutes: {recent_slow_queries}",
                    "timestamp": now.isoformat()
                })
        
        return alerts
    
    def _should_send_alert(self, alert_key: str, now: datetime) -> bool:
        """Проверка, нужно ли отправлять алерт (с учетом cooldown)"""
        last_sent = self.alerts_sent.get(alert_key)
        if last_sent is None or now - last_sent > self.alert_cooldown:
            self.alerts_sent[alert_key] = now
            return True
        return False
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Получение статистики пула"""
        with self._lock:
            recent_metrics = [m for m in self.metrics_history if datetime.now() - m.timestamp < timedelta(hours=1)]
        
        if not recent_metrics:
            return {"error": "No recent metrics available"}
        
        utilizations = [m.utilization_percent for m in recent_metrics]
        wait_times = [m.wait_time_ms for m in recent_metrics]
        
        return {
            "total_connections_created": self.connection_counters.get("created", 0),
            "total_connections_closed": self.connection_counters.get("closed", 0),
            "total_connection_errors": self.connection_counters.get("errors", 0),
            "total_slow_queries": self.query_counters.get("slow", 0),
            "avg_utilization_1h": sum(utilizations) / len(utilizations),
            "max_utilization_1h": max(utilizations),
            "avg_wait_time_1h": sum(wait_times) / len(wait_times),
            "max_wait_time_1h": max(wait_times),
            "metrics_collected": len(self.metrics_history),
            "events_recorded": len(self.connection_events)
        }
    
    async def get_cached_metrics(self) -> Optional[Dict[str, Any]]:
        """Получение кешированных метрик"""
        return await cache_manager.get("pool_metrics")
    
    async def cache_metrics(self, metrics: Dict[str, Any], ttl: int = 30):
        """Кеширование метрик"""
        await cache_manager.set("pool_metrics", metrics, ttl)


# Глобальный экземпляр монитора
pool_monitor = ConnectionPoolMonitor()


async def start_pool_monitoring():
    """Запуск мониторинга пула соединений"""
    logger.info("Starting connection pool monitoring")
    
    while True:
        try:
            # Собираем метрики
            health_info = await pool_monitor.check_pool_health()
            
            # Кешируем результаты
            await pool_monitor.cache_metrics(health_info)
            
            # Логируем критические состояния
            if health_info["status"] == "critical":
                logger.error(f"Critical pool status: {health_info['metrics']}")
            elif health_info["status"] == "warning":
                logger.warning(f"Warning pool status: {health_info['metrics']}")
            
        except Exception as e:
            logger.error(f"Error in pool monitoring: {e}")
        
        await asyncio.sleep(30)  # Проверяем каждые 30 секунд


def track_query_performance(query: str, duration_ms: float, connection_id: Optional[str] = None):
    """Трекинг производительности запросов"""
    metrics_collector.record("db_query_duration", duration_ms, {"type": "normal"})
    
    # Записываем медленные запросы
    pool_monitor.record_slow_query(query, duration_ms, connection_id) 