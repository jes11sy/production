"""
Система базовых алертов для мониторинга критических метрик
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import threading
import json

from app.core.cache import cache_manager
from app.core.config import settings
from app.monitoring.metrics import metrics_collector
from app.monitoring.connection_pool_monitor import pool_monitor
from app.monitoring.redis_monitor import redis_monitor

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Уровни серьезности алертов"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Статусы алертов"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Структура алерта"""
    id: str
    type: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    status: AlertStatus
    source: str
    tags: Dict[str, str]
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    silenced_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "source": self.source,
            "tags": self.tags,
            "threshold_value": self.threshold_value,
            "current_value": self.current_value,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "silenced_until": self.silenced_until.isoformat() if self.silenced_until else None
        }


@dataclass
class AlertRule:
    """Правило алерта"""
    id: str
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne"
    threshold: float
    severity: AlertSeverity
    duration_minutes: int = 1  # Время, в течение которого условие должно выполняться
    cooldown_minutes: int = 5  # Время между повторными алертами
    enabled: bool = True
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


class AlertManager:
    """Менеджер алертов"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.last_alert_times: Dict[str, datetime] = {}
        self.notification_handlers: List[Callable] = []
        self._lock = threading.RLock()
        
        # Статистика алертов
        self.alert_stats = defaultdict(int)
        
        # Настройка базовых правил
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Настройка базовых правил алертов"""
        default_rules = [
            # Алерты базы данных
            AlertRule(
                id="db_pool_high_utilization",
                name="Высокое использование пула соединений БД",
                metric_name="db_pool_utilization",
                condition="gt",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=2,
                cooldown_minutes=5,
                tags={"component": "database", "type": "performance"}
            ),
            AlertRule(
                id="db_pool_low_connections",
                name="Мало доступных соединений БД",
                metric_name="db_pool_checked_out",
                condition="gt",
                threshold=8.0,  # Из 10 соединений используется > 8
                severity=AlertSeverity.WARNING,
                duration_minutes=1,
                cooldown_minutes=3,
                tags={"component": "database", "type": "capacity"}
            ),
            AlertRule(
                id="db_slow_queries",
                name="Много медленных запросов БД",
                metric_name="db_slow_queries",
                condition="gt",
                threshold=5.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=5,
                cooldown_minutes=10,
                tags={"component": "database", "type": "performance"}
            ),
            AlertRule(
                id="db_connection_errors",
                name="Ошибки соединения с БД",
                metric_name="db_connection_errors",
                condition="gt",
                threshold=3.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
                cooldown_minutes=5,
                tags={"component": "database", "type": "error"}
            ),
            
            # Алерты Redis
            AlertRule(
                id="redis_disconnected",
                name="Redis отключен",
                metric_name="redis_connected",
                condition="eq",
                threshold=0.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
                cooldown_minutes=2,
                tags={"component": "redis", "type": "availability"}
            ),
            AlertRule(
                id="redis_high_memory",
                name="Высокое использование памяти Redis",
                metric_name="redis_memory_usage",
                condition="gt",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=3,
                cooldown_minutes=5,
                tags={"component": "redis", "type": "memory"}
            ),
            AlertRule(
                id="redis_low_hit_rate",
                name="Низкий коэффициент попаданий Redis",
                metric_name="redis_hit_rate",
                condition="lt",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=10,
                cooldown_minutes=15,
                tags={"component": "redis", "type": "performance"}
            ),
            AlertRule(
                id="redis_high_load",
                name="Высокая нагрузка на Redis",
                metric_name="redis_ops_per_sec",
                condition="gt",
                threshold=5000.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=5,
                cooldown_minutes=10,
                tags={"component": "redis", "type": "performance"}
            ),
            
            # Системные алерты
            AlertRule(
                id="high_cpu_usage",
                name="Высокое использование CPU",
                metric_name="cpu_usage",
                condition="gt",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=5,
                cooldown_minutes=10,
                tags={"component": "system", "type": "cpu"}
            ),
            AlertRule(
                id="high_memory_usage",
                name="Высокое использование памяти",
                metric_name="memory_usage",
                condition="gt",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                duration_minutes=3,
                cooldown_minutes=5,
                tags={"component": "system", "type": "memory"}
            ),
            AlertRule(
                id="high_error_rate",
                name="Высокая частота ошибок",
                metric_name="error_rate",
                condition="gt",
                threshold=5.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=2,
                cooldown_minutes=5,
                tags={"component": "application", "type": "error"}
            ),
            
            # Бизнес-алерты
            AlertRule(
                id="low_active_users",
                name="Мало активных пользователей",
                metric_name="active_users",
                condition="lt",
                threshold=5.0,
                severity=AlertSeverity.INFO,
                duration_minutes=30,
                cooldown_minutes=60,
                tags={"component": "business", "type": "users"}
            ),
            AlertRule(
                id="no_new_requests",
                name="Нет новых заявок",
                metric_name="requests_total",
                condition="eq",
                threshold=0.0,  # Проверяется изменение за период
                severity=AlertSeverity.WARNING,
                duration_minutes=60,
                cooldown_minutes=120,
                tags={"component": "business", "type": "requests"}
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
    
    def add_rule(self, rule: AlertRule):
        """Добавление правила алерта"""
        with self._lock:
            self.alert_rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Удаление правила алерта"""
        with self._lock:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
    
    def add_notification_handler(self, handler: Callable):
        """Добавление обработчика уведомлений"""
        self.notification_handlers.append(handler)
    
    async def check_alerts(self):
        """Проверка всех правил алертов"""
        now = datetime.now()
        
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Проверяем cooldown
                last_alert = self.last_alert_times.get(rule_id)
                if last_alert and now - last_alert < timedelta(minutes=rule.cooldown_minutes):
                    continue
                
                # Получаем текущее значение метрики
                current_value = metrics_collector.get_latest_value(rule.metric_name)
                if current_value is None:
                    continue
                
                # Проверяем условие
                if self._evaluate_condition(current_value, rule.condition, rule.threshold):
                    # Создаем или обновляем алерт
                    await self._create_alert(rule, current_value, now)
                else:
                    # Проверяем, нужно ли разрешить существующий алерт
                    await self._resolve_alert(rule_id, now)
                    
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_id}: {e}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Оценка условия алерта"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001  # Для float сравнения
        elif condition == "ne":
            return abs(value - threshold) >= 0.001
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False
    
    async def _create_alert(self, rule: AlertRule, current_value: float, timestamp: datetime):
        """Создание алерта"""
        alert_id = f"{rule.id}_{int(timestamp.timestamp())}"
        
        # Проверяем, есть ли уже активный алерт для этого правила
        existing_alert = None
        for alert in self.active_alerts.values():
            if alert.type == rule.id and alert.status == AlertStatus.ACTIVE:
                existing_alert = alert
                break
        
        if existing_alert:
            # Обновляем существующий алерт
            existing_alert.current_value = current_value
            existing_alert.timestamp = timestamp
        else:
            # Создаем новый алерт
            alert = Alert(
                id=alert_id,
                type=rule.id,
                severity=rule.severity,
                title=rule.name,
                message=f"{rule.name}: {current_value:.2f} (порог: {rule.threshold:.2f})",
                timestamp=timestamp,
                status=AlertStatus.ACTIVE,
                source="alert_manager",
                tags=rule.tags.copy(),
                threshold_value=rule.threshold,
                current_value=current_value
            )
            
            with self._lock:
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                self.alert_stats[rule.severity.value] += 1
                self.last_alert_times[rule.id] = timestamp
            
            # Отправляем уведомления
            await self._send_notifications(alert)
            
            logger.warning(f"Alert created: {alert.title} - {alert.message}")
    
    async def _resolve_alert(self, rule_id: str, timestamp: datetime):
        """Разрешение алерта"""
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.type == rule_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = timestamp
                
                with self._lock:
                    del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title}")
                break
    
    async def _send_notifications(self, alert: Alert):
        """Отправка уведомлений"""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Подтверждение алерта"""
        if alert_id in self.active_alerts:
            with self._lock:
                self.active_alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
                self.active_alerts[alert_id].acknowledged_at = datetime.now()
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def silence_alert(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """Заглушение алерта"""
        if alert_id in self.active_alerts:
            with self._lock:
                self.active_alerts[alert_id].status = AlertStatus.SILENCED
                self.active_alerts[alert_id].silenced_until = datetime.now() + timedelta(minutes=duration_minutes)
            logger.info(f"Alert silenced for {duration_minutes} minutes: {alert_id}")
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Получение активных алертов"""
        with self._lock:
            return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Получение истории алертов"""
        with self._lock:
            return list(self.alert_history)[-limit:]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Получение статистики алертов"""
        with self._lock:
            active_by_severity = defaultdict(int)
            for alert in self.active_alerts.values():
                active_by_severity[alert.severity.value] += 1
            
            return {
                "active_alerts": len(self.active_alerts),
                "total_alerts_created": len(self.alert_history),
                "active_by_severity": dict(active_by_severity),
                "total_by_severity": dict(self.alert_stats),
                "rules_configured": len(self.alert_rules),
                "rules_enabled": sum(1 for r in self.alert_rules.values() if r.enabled)
            }
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Получение сводки здоровья системы"""
        active_alerts = self.get_active_alerts()
        
        # Группируем алерты по компонентам
        alerts_by_component = defaultdict(list)
        for alert in active_alerts:
            component = alert.tags.get("component", "unknown")
            alerts_by_component[component].append(alert)
        
        # Определяем общий статус системы
        system_status = "healthy"
        if any(alert.severity == AlertSeverity.EMERGENCY for alert in active_alerts):
            system_status = "emergency"
        elif any(alert.severity == AlertSeverity.CRITICAL for alert in active_alerts):
            system_status = "critical"
        elif any(alert.severity == AlertSeverity.WARNING for alert in active_alerts):
            system_status = "warning"
        
        return {
            "system_status": system_status,
            "timestamp": datetime.now().isoformat(),
            "active_alerts_count": len(active_alerts),
            "alerts_by_component": {
                component: len(alerts) for component, alerts in alerts_by_component.items()
            },
            "critical_alerts": [
                alert.to_dict() for alert in active_alerts 
                if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
            ],
            "statistics": self.get_alert_statistics()
        }


# Глобальный экземпляр менеджера алертов
alert_manager = AlertManager()


async def log_notification_handler(alert: Alert):
    """Обработчик уведомлений - логирование"""
    logger.log(
        logging.CRITICAL if alert.severity == AlertSeverity.CRITICAL else logging.WARNING,
        f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}"
    )


async def cache_notification_handler(alert: Alert):
    """Обработчик уведомлений - кеширование"""
    try:
        # Кешируем алерт для внешних систем
        await cache_manager.set(f"alert:{alert.id}", alert.to_dict(), ttl=3600)
        
        # Обновляем список активных алертов в кеше
        active_alerts = [alert.to_dict() for alert in alert_manager.get_active_alerts()]
        await cache_manager.set("active_alerts", active_alerts, ttl=300)
        
    except Exception as e:
        logger.error(f"Error caching alert notification: {e}")


async def start_alert_monitoring():
    """Запуск мониторинга алертов"""
    logger.info("Starting alert monitoring")
    
    # Добавляем обработчики уведомлений
    alert_manager.add_notification_handler(log_notification_handler)
    alert_manager.add_notification_handler(cache_notification_handler)
    
    while True:
        try:
            # Проверяем алерты
            await alert_manager.check_alerts()
            
            # Очищаем заглушенные алерты
            await _cleanup_silenced_alerts()
            
        except Exception as e:
            logger.error(f"Error in alert monitoring: {e}")
        
        await asyncio.sleep(60)  # Проверяем каждую минуту


async def _cleanup_silenced_alerts():
    """Очистка заглушенных алертов"""
    now = datetime.now()
    
    for alert_id, alert in list(alert_manager.active_alerts.items()):
        if (alert.status == AlertStatus.SILENCED and 
            alert.silenced_until and 
            now > alert.silenced_until):
            
            alert.status = AlertStatus.ACTIVE
            alert.silenced_until = None
            logger.info(f"Alert unsilenced: {alert_id}")


def create_custom_alert(
    title: str, 
    message: str, 
    severity: AlertSeverity = AlertSeverity.INFO,
    tags: Dict[str, str] = None
) -> Alert:
    """Создание кастомного алерта"""
    alert = Alert(
        id=f"custom_{int(datetime.now().timestamp())}",
        type="custom",
        severity=severity,
        title=title,
        message=message,
        timestamp=datetime.now(),
        status=AlertStatus.ACTIVE,
        source="manual",
        tags=tags or {}
    )
    
    with alert_manager._lock:
        alert_manager.active_alerts[alert.id] = alert
        alert_manager.alert_history.append(alert)
        alert_manager.alert_stats[severity.value] += 1
    
    logger.info(f"Custom alert created: {title}")
    return alert 