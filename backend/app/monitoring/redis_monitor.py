"""
Мониторинг Redis с детальными метриками и алертами
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import deque, defaultdict
import threading
import json

from app.core.cache import cache_manager
from app.core.config import settings
from app.monitoring.metrics import metrics_collector, MetricType, MetricDefinition

logger = logging.getLogger(__name__)


class RedisStatus(Enum):
    """Статусы состояния Redis"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DISCONNECTED = "disconnected"


@dataclass
class RedisMetrics:
    """Метрики Redis"""
    timestamp: datetime
    connected: bool
    uptime_seconds: int
    used_memory_mb: float
    used_memory_peak_mb: float
    memory_usage_percent: float
    total_connections: int
    connected_clients: int
    blocked_clients: int
    keyspace_hits: int
    keyspace_misses: int
    hit_rate_percent: float
    total_commands_processed: int
    instantaneous_ops_per_sec: int
    evicted_keys: int
    expired_keys: int
    keyspace_size: int
    status: RedisStatus
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "connected": self.connected,
            "uptime_seconds": self.uptime_seconds,
            "used_memory_mb": self.used_memory_mb,
            "used_memory_peak_mb": self.used_memory_peak_mb,
            "memory_usage_percent": self.memory_usage_percent,
            "total_connections": self.total_connections,
            "connected_clients": self.connected_clients,
            "blocked_clients": self.blocked_clients,
            "keyspace_hits": self.keyspace_hits,
            "keyspace_misses": self.keyspace_misses,
            "hit_rate_percent": self.hit_rate_percent,
            "total_commands_processed": self.total_commands_processed,
            "instantaneous_ops_per_sec": self.instantaneous_ops_per_sec,
            "evicted_keys": self.evicted_keys,
            "expired_keys": self.expired_keys,
            "keyspace_size": self.keyspace_size,
            "status": self.status.value
        }


@dataclass
class RedisSlowLog:
    """Информация о медленной команде Redis"""
    id: int
    timestamp: datetime
    duration_microseconds: int
    command: str
    client_ip: str
    client_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "duration_microseconds": self.duration_microseconds,
            "duration_ms": self.duration_microseconds / 1000,
            "command": self.command,
            "client_ip": self.client_ip,
            "client_name": self.client_name
        }


class RedisMonitor:
    """Мониторинг Redis с детальной статистикой"""
    
    def __init__(self, slow_log_threshold_ms: int = 100):
        self.slow_log_threshold_ms = slow_log_threshold_ms
        self.metrics_history: deque = deque(maxlen=1000)
        self.slow_commands: deque = deque(maxlen=100)
        self.alerts_sent: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)
        self._lock = threading.RLock()
        
        # Счетчики операций
        self.operation_counters = defaultdict(int)
        self.error_counters = defaultdict(int)
        
        # Регистрируем метрики
        self._register_metrics()
        
        # Предыдущие значения для вычисления дельт
        self.previous_stats = {}
    
    def _register_metrics(self):
        """Регистрация метрик Redis"""
        redis_metrics = [
            MetricDefinition("redis_connected", MetricType.GAUGE, "Redis подключение (1=connected, 0=disconnected)"),
            MetricDefinition("redis_uptime", MetricType.GAUGE, "Время работы Redis", "seconds"),
            MetricDefinition("redis_memory_used", MetricType.GAUGE, "Используемая память", "MB"),
            MetricDefinition("redis_memory_peak", MetricType.GAUGE, "Пиковое использование памяти", "MB"),
            MetricDefinition("redis_memory_usage", MetricType.GAUGE, "Использование памяти", "%"),
            MetricDefinition("redis_connections_total", MetricType.GAUGE, "Общее количество соединений"),
            MetricDefinition("redis_connections_active", MetricType.GAUGE, "Активные соединения"),
            MetricDefinition("redis_connections_blocked", MetricType.GAUGE, "Заблокированные соединения"),
            MetricDefinition("redis_keyspace_hits", MetricType.COUNTER, "Попадания в кеш"),
            MetricDefinition("redis_keyspace_misses", MetricType.COUNTER, "Промахи кеша"),
            MetricDefinition("redis_hit_rate", MetricType.GAUGE, "Коэффициент попаданий", "%"),
            MetricDefinition("redis_commands_processed", MetricType.COUNTER, "Обработанные команды"),
            MetricDefinition("redis_ops_per_sec", MetricType.GAUGE, "Операций в секунду"),
            MetricDefinition("redis_evicted_keys", MetricType.COUNTER, "Вытесненные ключи"),
            MetricDefinition("redis_expired_keys", MetricType.COUNTER, "Просроченные ключи"),
            MetricDefinition("redis_keyspace_size", MetricType.GAUGE, "Размер keyspace"),
            MetricDefinition("redis_slow_commands", MetricType.COUNTER, "Медленные команды"),
            MetricDefinition("redis_status", MetricType.GAUGE, "Статус Redis (0=healthy, 1=warning, 2=critical, 3=disconnected)")
        ]
        
        for metric in redis_metrics:
            metrics_collector.register_metric(metric)
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Получение информации о Redis"""
        try:
            if not cache_manager.redis_client:
                return {}
            
            # Получаем базовую информацию
            info = await cache_manager.redis_client.info()
            
            # Получаем статистику keyspace
            keyspace_info = await cache_manager.redis_client.info("keyspace")
            
            # Получаем информацию о памяти
            memory_info = await cache_manager.redis_client.info("memory")
            
            # Получаем статистику клиентов
            clients_info = await cache_manager.redis_client.info("clients")
            
            # Получаем статистику команд
            stats_info = await cache_manager.redis_client.info("stats")
            
            return {
                **info,
                **keyspace_info,
                **memory_info,
                **clients_info,
                **stats_info
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}
    
    async def get_redis_metrics(self) -> RedisMetrics:
        """Получение метрик Redis"""
        info = await self.get_redis_info()
        
        if not info:
            # Redis недоступен
            return RedisMetrics(
                timestamp=datetime.now(),
                connected=False,
                uptime_seconds=0,
                used_memory_mb=0,
                used_memory_peak_mb=0,
                memory_usage_percent=0,
                total_connections=0,
                connected_clients=0,
                blocked_clients=0,
                keyspace_hits=0,
                keyspace_misses=0,
                hit_rate_percent=0,
                total_commands_processed=0,
                instantaneous_ops_per_sec=0,
                evicted_keys=0,
                expired_keys=0,
                keyspace_size=0,
                status=RedisStatus.DISCONNECTED
            )
        
        # Извлекаем метрики
        used_memory = info.get("used_memory", 0)
        used_memory_peak = info.get("used_memory_peak", 0)
        used_memory_mb = used_memory / (1024 * 1024)
        used_memory_peak_mb = used_memory_peak / (1024 * 1024)
        
        # Вычисляем процент использования памяти (приблизительно)
        maxmemory = info.get("maxmemory", 0)
        if maxmemory > 0:
            memory_usage_percent = (used_memory / maxmemory) * 100
        else:
            # Если maxmemory не установлен, используем системную память
            memory_usage_percent = min(used_memory_mb / 512, 100)  # Предполагаем 512MB как базовый лимит
        
        # Статистика кеша
        keyspace_hits = info.get("keyspace_hits", 0)
        keyspace_misses = info.get("keyspace_misses", 0)
        total_requests = keyspace_hits + keyspace_misses
        hit_rate_percent = (keyspace_hits / max(1, total_requests)) * 100
        
        # Размер keyspace
        keyspace_size = 0
        for key, value in info.items():
            if key.startswith("db"):
                # Формат: "keys=123,expires=45,avg_ttl=678"
                if "keys=" in str(value):
                    keys_part = str(value).split("keys=")[1].split(",")[0]
                    keyspace_size += int(keys_part)
        
        # Определяем статус
        status = self._determine_redis_status(
            memory_usage_percent,
            info.get("connected_clients", 0),
            hit_rate_percent,
            info.get("instantaneous_ops_per_sec", 0)
        )
        
        metrics = RedisMetrics(
            timestamp=datetime.now(),
            connected=True,
            uptime_seconds=info.get("uptime_in_seconds", 0),
            used_memory_mb=used_memory_mb,
            used_memory_peak_mb=used_memory_peak_mb,
            memory_usage_percent=memory_usage_percent,
            total_connections=info.get("total_connections_received", 0),
            connected_clients=info.get("connected_clients", 0),
            blocked_clients=info.get("blocked_clients", 0),
            keyspace_hits=keyspace_hits,
            keyspace_misses=keyspace_misses,
            hit_rate_percent=hit_rate_percent,
            total_commands_processed=info.get("total_commands_processed", 0),
            instantaneous_ops_per_sec=info.get("instantaneous_ops_per_sec", 0),
            evicted_keys=info.get("evicted_keys", 0),
            expired_keys=info.get("expired_keys", 0),
            keyspace_size=keyspace_size,
            status=status
        )
        
        # Сохраняем в историю
        with self._lock:
            self.metrics_history.append(metrics)
        
        # Записываем метрики
        self._record_metrics(metrics)
        
        return metrics
    
    def _determine_redis_status(self, memory_usage: float, connected_clients: int, hit_rate: float, ops_per_sec: int) -> RedisStatus:
        """Определение статуса Redis"""
        if memory_usage > 90:
            return RedisStatus.CRITICAL
        elif memory_usage > 75:
            return RedisStatus.WARNING
        
        if connected_clients > 100:
            return RedisStatus.WARNING
        elif connected_clients > 200:
            return RedisStatus.CRITICAL
        
        if hit_rate < 80:
            return RedisStatus.WARNING
        elif hit_rate < 50:
            return RedisStatus.CRITICAL
        
        if ops_per_sec > 10000:
            return RedisStatus.WARNING
        elif ops_per_sec > 20000:
            return RedisStatus.CRITICAL
        
        return RedisStatus.HEALTHY
    
    def _record_metrics(self, metrics: RedisMetrics):
        """Запись метрик в систему мониторинга"""
        metrics_collector.set_gauge("redis_connected", 1 if metrics.connected else 0)
        metrics_collector.set_gauge("redis_uptime", metrics.uptime_seconds)
        metrics_collector.set_gauge("redis_memory_used", metrics.used_memory_mb)
        metrics_collector.set_gauge("redis_memory_peak", metrics.used_memory_peak_mb)
        metrics_collector.set_gauge("redis_memory_usage", metrics.memory_usage_percent)
        metrics_collector.set_gauge("redis_connections_total", metrics.total_connections)
        metrics_collector.set_gauge("redis_connections_active", metrics.connected_clients)
        metrics_collector.set_gauge("redis_connections_blocked", metrics.blocked_clients)
        metrics_collector.set_gauge("redis_hit_rate", metrics.hit_rate_percent)
        metrics_collector.set_gauge("redis_ops_per_sec", metrics.instantaneous_ops_per_sec)
        metrics_collector.set_gauge("redis_keyspace_size", metrics.keyspace_size)
        
        # Счетчики (записываем только если есть изменения)
        if metrics.keyspace_hits > self.previous_stats.get("keyspace_hits", 0):
            metrics_collector.increment("redis_keyspace_hits", 
                                      metrics.keyspace_hits - self.previous_stats.get("keyspace_hits", 0))
        
        if metrics.keyspace_misses > self.previous_stats.get("keyspace_misses", 0):
            metrics_collector.increment("redis_keyspace_misses", 
                                      metrics.keyspace_misses - self.previous_stats.get("keyspace_misses", 0))
        
        if metrics.total_commands_processed > self.previous_stats.get("total_commands_processed", 0):
            metrics_collector.increment("redis_commands_processed", 
                                      metrics.total_commands_processed - self.previous_stats.get("total_commands_processed", 0))
        
        if metrics.evicted_keys > self.previous_stats.get("evicted_keys", 0):
            metrics_collector.increment("redis_evicted_keys", 
                                      metrics.evicted_keys - self.previous_stats.get("evicted_keys", 0))
        
        if metrics.expired_keys > self.previous_stats.get("expired_keys", 0):
            metrics_collector.increment("redis_expired_keys", 
                                      metrics.expired_keys - self.previous_stats.get("expired_keys", 0))
        
        # Статус как число
        status_value = {
            RedisStatus.HEALTHY: 0,
            RedisStatus.WARNING: 1,
            RedisStatus.CRITICAL: 2,
            RedisStatus.DISCONNECTED: 3
        }[metrics.status]
        metrics_collector.set_gauge("redis_status", status_value)
        
        # Обновляем предыдущие значения
        self.previous_stats = {
            "keyspace_hits": metrics.keyspace_hits,
            "keyspace_misses": metrics.keyspace_misses,
            "total_commands_processed": metrics.total_commands_processed,
            "evicted_keys": metrics.evicted_keys,
            "expired_keys": metrics.expired_keys
        }
    
    async def get_slow_log(self) -> List[RedisSlowLog]:
        """Получение медленных команд из Redis"""
        try:
            if not cache_manager.redis_client:
                return []
            
            # Получаем медленные команды
            slow_log = await cache_manager.redis_client.slowlog_get(10)
            
            result = []
            for entry in slow_log:
                slow_cmd = RedisSlowLog(
                    id=entry["id"],
                    timestamp=datetime.fromtimestamp(entry["start_time"]),
                    duration_microseconds=entry["duration"],
                    command=" ".join(str(arg) for arg in entry["command"]),
                    client_ip=entry.get("client_addr", "unknown"),
                    client_name=entry.get("client_name", "unknown")
                )
                result.append(slow_cmd)
            
            # Сохраняем в историю
            with self._lock:
                self.slow_commands.extend(result)
            
            # Записываем метрику
            if result:
                metrics_collector.increment("redis_slow_commands", len(result))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Redis slow log: {e}")
            return []
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Проверка здоровья Redis"""
        metrics = await self.get_redis_metrics()
        
        # Получаем медленные команды
        slow_log = await self.get_slow_log()
        
        # Проверяем алерты
        alerts = self._check_alerts(metrics)
        
        # Получаем статистику
        stats = self.get_redis_statistics()
        
        # Получаем информацию о кеше приложения
        app_cache_stats = cache_manager.get_stats()
        
        return {
            "status": metrics.status.value,
            "metrics": metrics.to_dict(),
            "statistics": stats,
            "alerts": alerts,
            "slow_log": [cmd.to_dict() for cmd in slow_log[-5:]],
            "app_cache_stats": app_cache_stats
        }
    
    def _check_alerts(self, metrics: RedisMetrics) -> List[Dict[str, Any]]:
        """Проверка алертов Redis"""
        alerts = []
        now = datetime.now()
        
        # Алерт отключения
        if not metrics.connected:
            alert_key = "redis_disconnected"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "redis_disconnected",
                    "severity": "critical",
                    "message": "Redis disconnected",
                    "timestamp": now.isoformat()
                })
        
        # Алерт высокого использования памяти
        if metrics.memory_usage_percent > 90:
            alert_key = "high_memory_usage"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "high_memory_usage",
                    "severity": "critical",
                    "message": f"High Redis memory usage: {metrics.memory_usage_percent:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        # Алерт низкого hit rate
        if metrics.hit_rate_percent < 80:
            alert_key = "low_hit_rate"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "low_hit_rate",
                    "severity": "warning",
                    "message": f"Low Redis hit rate: {metrics.hit_rate_percent:.1f}%",
                    "timestamp": now.isoformat()
                })
        
        # Алерт высокой нагрузки
        if metrics.instantaneous_ops_per_sec > 10000:
            alert_key = "high_load"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "high_load",
                    "severity": "warning",
                    "message": f"High Redis load: {metrics.instantaneous_ops_per_sec} ops/sec",
                    "timestamp": now.isoformat()
                })
        
        # Алерт много соединений
        if metrics.connected_clients > 100:
            alert_key = "many_connections"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "many_connections",
                    "severity": "warning",
                    "message": f"Many Redis connections: {metrics.connected_clients}",
                    "timestamp": now.isoformat()
                })
        
        # Алерт вытеснения ключей
        recent_evictions = self._get_recent_evictions()
        if recent_evictions > 100:
            alert_key = "key_evictions"
            if self._should_send_alert(alert_key, now):
                alerts.append({
                    "type": "key_evictions",
                    "severity": "warning",
                    "message": f"Many key evictions in last 5 minutes: {recent_evictions}",
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
    
    def _get_recent_evictions(self) -> int:
        """Получение количества недавних вытеснений"""
        now = datetime.now()
        recent_metrics = [m for m in self.metrics_history if now - m.timestamp < timedelta(minutes=5)]
        
        if len(recent_metrics) < 2:
            return 0
        
        return recent_metrics[-1].evicted_keys - recent_metrics[0].evicted_keys
    
    def get_redis_statistics(self) -> Dict[str, Any]:
        """Получение статистики Redis"""
        with self._lock:
            recent_metrics = [m for m in self.metrics_history if datetime.now() - m.timestamp < timedelta(hours=1)]
        
        if not recent_metrics:
            return {"error": "No recent metrics available"}
        
        memory_usage = [m.memory_usage_percent for m in recent_metrics]
        hit_rates = [m.hit_rate_percent for m in recent_metrics]
        ops_per_sec = [m.instantaneous_ops_per_sec for m in recent_metrics]
        
        return {
            "uptime_hours": recent_metrics[-1].uptime_seconds / 3600 if recent_metrics else 0,
            "avg_memory_usage_1h": sum(memory_usage) / len(memory_usage),
            "max_memory_usage_1h": max(memory_usage),
            "avg_hit_rate_1h": sum(hit_rates) / len(hit_rates),
            "min_hit_rate_1h": min(hit_rates),
            "avg_ops_per_sec_1h": sum(ops_per_sec) / len(ops_per_sec),
            "max_ops_per_sec_1h": max(ops_per_sec),
            "total_slow_commands": len(self.slow_commands),
            "metrics_collected": len(self.metrics_history)
        }
    
    async def get_cached_metrics(self) -> Optional[Dict[str, Any]]:
        """Получение кешированных метрик"""
        return await cache_manager.get("redis_metrics")
    
    async def cache_metrics(self, metrics: Dict[str, Any], ttl: int = 30):
        """Кеширование метрик"""
        await cache_manager.set("redis_metrics", metrics, ttl)


# Глобальный экземпляр монитора
redis_monitor = RedisMonitor()


async def start_redis_monitoring():
    """Запуск мониторинга Redis"""
    logger.info("Starting Redis monitoring")
    
    while True:
        try:
            # Собираем метрики
            health_info = await redis_monitor.check_redis_health()
            
            # Кешируем результаты
            await redis_monitor.cache_metrics(health_info)
            
            # Логируем критические состояния
            if health_info["status"] == "critical":
                logger.error(f"Critical Redis status: {health_info['metrics']}")
            elif health_info["status"] == "warning":
                logger.warning(f"Warning Redis status: {health_info['metrics']}")
            elif health_info["status"] == "disconnected":
                logger.error("Redis disconnected")
            
        except Exception as e:
            logger.error(f"Error in Redis monitoring: {e}")
        
        await asyncio.sleep(30)  # Проверяем каждые 30 секунд


def record_cache_operation(operation: str, hit: bool = False, duration_ms: float = 0):
    """Запись операции с кешем"""
    redis_monitor.operation_counters[operation] += 1
    
    if hit:
        redis_monitor.operation_counters["hits"] += 1
    else:
        redis_monitor.operation_counters["misses"] += 1
    
    if duration_ms > 0:
        metrics_collector.record("redis_operation_duration", duration_ms, {"operation": operation})


def record_cache_error(operation: str, error: Exception):
    """Запись ошибки кеша"""
    redis_monitor.error_counters[operation] += 1
    logger.error(f"Redis {operation} error: {error}")
    metrics_collector.increment("redis_errors", tags={"operation": operation}) 