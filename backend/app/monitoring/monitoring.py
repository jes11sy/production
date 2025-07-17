"""
Система мониторинга и health checks
"""
import asyncio
import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.exc import SQLAlchemyError
from ..core.database import engine, get_db
from ..core.config import settings
from ..services.recording_service import recording_service
import os

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Статусы здоровья сервисов"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Результат проверки здоровья"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: datetime


@dataclass
class SystemMetrics:
    """Системные метрики"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: List[float]
    uptime_seconds: float
    timestamp: datetime


class DatabaseHealthChecker:
    """Проверка здоровья базы данных"""
    
    async def check_connection(self) -> HealthCheck:
        """Проверка подключения к БД"""
        start_time = time.time()
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_connection",
                status=HealthStatus.HEALTHY,
                message="Database connection is healthy",
                details={"response_time_ms": duration},
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_connection",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )
    
    async def check_query_performance(self) -> HealthCheck:
        """Проверка производительности запросов"""
        start_time = time.time()
        try:
            async with engine.begin() as conn:
                # Тестовый запрос для проверки производительности
                result = await conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_requests
                    FROM requests
                """))
                data = result.fetchone()
            
            duration = (time.time() - start_time) * 1000
            
            # Определяем статус на основе времени выполнения
            if duration < 100:
                status = HealthStatus.HEALTHY
                message = "Query performance is excellent"
            elif duration < 500:
                status = HealthStatus.HEALTHY
                message = "Query performance is good"
            elif duration < 1000:
                status = HealthStatus.DEGRADED
                message = "Query performance is degraded"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Query performance is poor"
            
            return HealthCheck(
                name="database_performance",
                status=status,
                message=message,
                details={
                    "query_time_ms": duration,
                    "total_requests": data[0] if data else 0,
                    "recent_requests": data[1] if data else 0
                },
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_performance",
                status=HealthStatus.UNHEALTHY,
                message=f"Query performance check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )
    
    async def check_pool_status(self) -> HealthCheck:
        """Проверка состояния пула соединений"""
        start_time = time.time()
        try:
            pool = engine.pool
            
            # Получаем статистику пула (используем безопасные методы)
            pool_status = {
                "size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "invalid": getattr(pool, 'invalid', lambda: 0)()
            }
            
            # Определяем статус на основе использования пула
            utilization = pool_status["checked_out"] / max(pool_status["size"], 1)
            
            if utilization < 0.7:
                status = HealthStatus.HEALTHY
                message = "Connection pool is healthy"
            elif utilization < 0.9:
                status = HealthStatus.DEGRADED
                message = "Connection pool utilization is high"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Connection pool is nearly exhausted"
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_pool",
                status=status,
                message=message,
                details=pool_status,
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_pool",
                status=HealthStatus.UNKNOWN,
                message=f"Pool status check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )


class SystemHealthChecker:
    """Проверка здоровья системы"""
    
    def get_system_metrics(self) -> SystemMetrics:
        """Получение системных метрик"""
        try:
            # Используем interval=None для неблокирующего вызова
            # Первый вызов может быть неточным, но последующие будут корректными
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0.0, 0.0, 0.0]
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                load_average=list(load_avg),
                uptime_seconds=uptime,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                load_average=[0.0, 0.0, 0.0],
                uptime_seconds=0.0,
                timestamp=datetime.now()
            )
    
    async def check_system_resources(self) -> HealthCheck:
        """Проверка системных ресурсов"""
        start_time = time.time()
        try:
            metrics = self.get_system_metrics()
            
            # Определяем статус на основе использования ресурсов
            issues = []
            if metrics.cpu_percent > 90:
                issues.append("High CPU usage")
            if metrics.memory_percent > 90:
                issues.append("High memory usage")
            if metrics.disk_percent > 90:
                issues.append("High disk usage")
            
            if not issues:
                status = HealthStatus.HEALTHY
                message = "System resources are healthy"
            elif len(issues) == 1:
                status = HealthStatus.DEGRADED
                message = f"System resources degraded: {issues[0]}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"System resources critical: {', '.join(issues)}"
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": metrics.cpu_percent,
                    "memory_percent": metrics.memory_percent,
                    "disk_percent": metrics.disk_percent,
                    "load_average": metrics.load_average,
                    "uptime_hours": metrics.uptime_seconds / 3600
                },
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"System resources check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )


class ServiceHealthChecker:
    """Проверка здоровья сервисов"""
    
    async def check_recording_service(self) -> HealthCheck:
        """Проверка сервиса записей"""
        start_time = time.time()
        try:
            is_running = recording_service.is_running
            task_active = recording_service.task is not None and not recording_service.task.done()
            
            if is_running and task_active:
                status = HealthStatus.HEALTHY
                message = "Recording service is running"
            elif is_running and not task_active:
                status = HealthStatus.DEGRADED
                message = "Recording service is enabled but task is not active"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Recording service is not running"
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="recording_service",
                status=status,
                message=message,
                details={
                    "is_running": is_running,
                    "task_active": task_active,
                    "service_configured": bool(settings.RAMBLER_IMAP_USERNAME)
                },
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="recording_service",
                status=HealthStatus.UNKNOWN,
                message=f"Recording service check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )
    
    async def check_file_storage(self) -> HealthCheck:
        """Проверка файлового хранилища"""
        start_time = time.time()
        try:
            # Проверяем доступность директорий
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            media_dir = os.path.join(base_dir, "media")
            
            issues = []
            if not os.path.exists(media_dir):
                issues.append("Media directory does not exist")
            elif not os.access(media_dir, os.R_OK | os.W_OK):
                issues.append("Media directory is not accessible")
            
            # Проверяем место на диске
            if os.path.exists(media_dir):
                disk_usage = psutil.disk_usage(media_dir)
                free_percent = (disk_usage.free / disk_usage.total) * 100
                
                if free_percent < 5:
                    issues.append("Very low disk space")
                elif free_percent < 15:
                    issues.append("Low disk space")
            
            if not issues:
                status = HealthStatus.HEALTHY
                message = "File storage is healthy"
            elif len(issues) == 1 and "Low disk space" in issues[0]:
                status = HealthStatus.DEGRADED
                message = f"File storage degraded: {issues[0]}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"File storage issues: {', '.join(issues)}"
            
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="file_storage",
                status=status,
                message=message,
                details={
                    "media_dir": media_dir,
                    "exists": os.path.exists(media_dir),
                    "writable": os.access(media_dir, os.W_OK) if os.path.exists(media_dir) else False,
                    "free_space_percent": free_percent if os.path.exists(media_dir) else 0
                },
                duration_ms=duration,
                timestamp=datetime.now()
            )
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return HealthCheck(
                name="file_storage",
                status=HealthStatus.UNKNOWN,
                message=f"File storage check failed: {str(e)}",
                details={"error": str(e)},
                duration_ms=duration,
                timestamp=datetime.now()
            )


class HealthMonitor:
    """Основной класс мониторинга здоровья"""
    
    def __init__(self):
        self.db_checker = DatabaseHealthChecker()
        self.system_checker = SystemHealthChecker()
        self.service_checker = ServiceHealthChecker()
        self.last_full_check: Optional[datetime] = None
        self.cached_results: Dict[str, HealthCheck] = {}
        self.cache_duration = timedelta(seconds=60)  # Кеш на 60 секунд
    
    async def run_all_checks(self, use_cache: bool = True) -> Dict[str, HealthCheck]:
        """Запуск всех проверок здоровья"""
        now = datetime.now()
        
        # Проверяем кеш
        if (use_cache and self.last_full_check and 
            now - self.last_full_check < self.cache_duration and 
            self.cached_results):
            return self.cached_results
        
        logger.info("Running comprehensive health checks")
        
        # Запускаем все проверки параллельно
        checks = await asyncio.gather(
            self.db_checker.check_connection(),
            self.db_checker.check_query_performance(),
            self.db_checker.check_pool_status(),
            self.system_checker.check_system_resources(),
            self.service_checker.check_recording_service(),
            self.service_checker.check_file_storage(),
            return_exceptions=True
        )
        
        # Обрабатываем результаты
        results = {}
        check_names = [
            "database_connection",
            "database_performance", 
            "database_pool",
            "system_resources",
            "recording_service",
            "file_storage"
        ]
        
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                # Если проверка упала с исключением
                results[check_names[i]] = HealthCheck(
                    name=check_names[i],
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check failed: {str(check)}",
                    details={"error": str(check)},
                    duration_ms=0,
                    timestamp=now
                )
            else:
                # check is HealthCheck instance
                if isinstance(check, HealthCheck):
                    results[check.name] = check
        
        # Обновляем кеш
        self.cached_results = results
        self.last_full_check = now
        
        return results
    
    def get_overall_status(self, checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Определение общего статуса здоровья"""
        statuses = [check.status for check in checks.values()]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        elif any(status == HealthStatus.UNKNOWN for status in statuses):
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    async def get_health_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """Получение сводки о здоровье системы"""
        checks = await self.run_all_checks(use_cache)
        overall_status = self.get_overall_status(checks)
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "duration_ms": check.duration_ms,
                    "details": check.details
                }
                for name, check in checks.items()
            },
            "system_metrics": self.system_checker.get_system_metrics().__dict__,
            "summary": {
                "total_checks": len(checks),
                "healthy": sum(1 for c in checks.values() if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in checks.values() if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in checks.values() if c.status == HealthStatus.UNHEALTHY),
                "unknown": sum(1 for c in checks.values() if c.status == HealthStatus.UNKNOWN)
            }
        }


# Глобальный экземпляр монитора
health_monitor = HealthMonitor() 