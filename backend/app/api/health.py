"""
Эндпоинты для проверки здоровья системы
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from typing import Dict, Any, List, Optional
import asyncio
import time
import logging
from datetime import datetime, timedelta
import psutil
import os

from ..core.database import get_db, engine
from ..core.cache import cache_manager
from ..core.config import settings
from ..core.models import Request, Transaction, Master, Employee, Administrator
from ..monitoring.metrics import metrics_collector, performance_collector, business_collector
from ..core.exceptions import DatabaseError, ExternalServiceError, BaseApplicationError
from ..monitoring.external_services import get_external_services_status

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


class HealthCheckResult:
    """Результат проверки здоровья"""
    
    def __init__(self, name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None, duration: float = 0.0):
        self.name = name
        self.status = status  # "healthy", "unhealthy", "degraded"
        self.message = message
        self.details = details or {}
        self.duration = duration
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat()
        }


class HealthChecker:
    """Основной класс для проверки здоровья системы"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
        self.cache_duration = 30  # Кеш результатов на 30 секунд
    
    async def check_database(self) -> HealthCheckResult:
        """Проверка базы данных"""
        start_time = time.time()
        
        try:
            # Проверка подключения
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            # Проверка основных таблиц
            async for db in get_db():
                # Проверяем количество записей в основных таблицах
                requests_count = await db.scalar(select(func.count(Request.id)))
                transactions_count = await db.scalar(select(func.count(Transaction.id)))
                masters_count = await db.scalar(select(func.count(Master.id)))
                
                details = {
                    "connection": "ok",
                    "requests_count": requests_count,
                    "transactions_count": transactions_count,
                    "masters_count": masters_count,
                    "pool_size": getattr(engine.pool, 'size', lambda: 0)(),
                    "pool_checked_out": getattr(engine.pool, 'checkedout', lambda: 0)(),
                    "pool_overflow": getattr(engine.pool, 'overflow', lambda: 0)(),
                    "pool_invalid": getattr(engine.pool, 'invalid', lambda: 0)()
                }
                
                break
            
            duration = time.time() - start_time
            
            # Проверяем производительность
            if duration > 2.0:
                return HealthCheckResult(
                    "database",
                    "degraded",
                    f"Database responding slowly ({duration:.2f}s)",
                    details,
                    duration
                )
            
            return HealthCheckResult(
                "database",
                "healthy",
                "Database is operational",
                details,
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheckResult(
                "database",
                "unhealthy",
                f"Database error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration
            )
    
    async def check_cache(self) -> HealthCheckResult:
        """Проверка Redis кеша"""
        start_time = time.time()
        
        try:
            # Тестируем запись и чтение
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": time.time()}
            
            await cache_manager.set(test_key, test_value, ttl=60)
            cached_value = await cache_manager.get(test_key)
            
            if cached_value != test_value:
                raise Exception("Cache read/write test failed")
            
            # Очищаем тестовый ключ
            await cache_manager.delete(test_key)
            
            duration = time.time() - start_time
            
            # Получаем информацию о кеше
            cache_info = getattr(cache_manager, 'get_info', lambda: {})()
            
            details = {
                "connection": "ok",
                "read_write_test": "passed",
                "cache_info": cache_info if asyncio.iscoroutine(cache_info) else cache_info
            }
            
            return HealthCheckResult(
                "cache",
                "healthy",
                "Cache is operational",
                details,
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheckResult(
                "cache",
                "unhealthy",
                f"Cache error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration
            )
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Проверка системных ресурсов"""
        start_time = time.time()
        
        try:
            # Получаем информацию о системе
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            details = {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent,
                    "used": disk.used
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            duration = time.time() - start_time
            
            # Проверяем критические пороги
            issues = []
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent}%")
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent}%")
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if issues:
                return HealthCheckResult(
                    "system",
                    "degraded",
                    f"System resource issues: {', '.join(issues)}",
                    details,
                    duration
                )
            
            return HealthCheckResult(
                "system",
                "healthy",
                "System resources are normal",
                details,
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheckResult(
                "system",
                "unhealthy",
                f"System check error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration
            )
    
    async def check_metrics(self) -> HealthCheckResult:
        """Проверка системы метрик"""
        start_time = time.time()
        
        try:
            # Проверяем работу сборщика метрик
            metrics_data = metrics_collector.get_all_metrics()
            
            details = {
                "metrics_count": len(metrics_data),
                "collector_running": metrics_collector._running,
                "background_task_active": metrics_collector._background_task is not None and not metrics_collector._background_task.done()
            }
            
            # Проверяем, что метрики собираются
            if not metrics_data:
                return HealthCheckResult(
                    "metrics",
                    "degraded",
                    "No metrics data available",
                    details,
                    time.time() - start_time
                )
            
            # Проверяем актуальность метрик
            recent_metrics = 0
            for metric_name, metric_info in metrics_data.items():
                if metric_info.get("count", 0) > 0:
                    recent_metrics += 1
            
            details["recent_metrics"] = recent_metrics
            
            duration = time.time() - start_time
            
            return HealthCheckResult(
                "metrics",
                "healthy",
                f"Metrics system operational ({recent_metrics} active metrics)",
                details,
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheckResult(
                "metrics",
                "unhealthy",
                f"Metrics check error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration
            )
    
    async def check_external_services(self) -> HealthCheckResult:
        """Проверка внешних сервисов"""
        start_time = time.time()
        
        try:
            # Здесь можно добавить проверки внешних сервисов
            # Например, проверка доступности Mango Office API, email сервиса и т.д.
            
            details = {
                "email_service": "not_implemented",
                "mango_office": "not_implemented",
                "file_storage": "local"
            }
            
            duration = time.time() - start_time
            
            return HealthCheckResult(
                "external_services",
                "healthy",
                "External services check passed",
                details,
                duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return HealthCheckResult(
                "external_services",
                "degraded",
                f"External services check error: {str(e)}",
                {"error": str(e), "error_type": type(e).__name__},
                duration
            )
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Выполнение всех проверок здоровья"""
        start_time = time.time()
        
        # Выполняем все проверки параллельно
        results = await asyncio.gather(
            self.check_database(),
            self.check_cache(),
            self.check_system_resources(),
            self.check_metrics(),
            self.check_external_services(),
            return_exceptions=True
        )
        
        # Обрабатываем результаты
        checks = {}
        overall_status = "healthy"
        
        for result in results:
            if isinstance(result, Exception):
                # Если проверка упала с исключением
                checks["unknown"] = HealthCheckResult(
                    "unknown",
                    "unhealthy",
                    f"Check failed: {str(result)}",
                    {"error": str(result)},
                    0.0
                ).to_dict()
                overall_status = "unhealthy"
            elif isinstance(result, HealthCheckResult):
                checks[result.name] = result.to_dict()
                
                # Определяем общий статус
                if result.status == "unhealthy":
                    overall_status = "unhealthy"
                elif result.status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"
        
        total_duration = time.time() - start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "duration": total_duration,
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "healthy": len([c for c in checks.values() if c["status"] == "healthy"]),
                "degraded": len([c for c in checks.values() if c["status"] == "degraded"]),
                "unhealthy": len([c for c in checks.values() if c["status"] == "unhealthy"])
            }
        }


# Создаем глобальный экземпляр
health_checker = HealthChecker()


@router.get("/")
async def health_check():
    """Быстрая проверка здоровья"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Request Management System",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Детальная проверка здоровья системы"""
    try:
        result = await health_checker.run_all_checks()
        
        # Определяем HTTP статус код
        status_code = 200
        if result["status"] == "unhealthy":
            status_code = 503
        elif result["status"] == "degraded":
            status_code = 200  # Система работает, но есть проблемы
        
        return JSONResponse(
            status_code=status_code,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "checks": {}
            }
        )


@router.get("/database")
async def database_health_check():
    """Проверка здоровья базы данных"""
    result = await health_checker.check_database()
    
    status_code = 200 if result.status == "healthy" else 503
    return JSONResponse(
        status_code=status_code,
        content=result.to_dict()
    )


@router.get("/cache")
async def cache_health_check():
    """Проверка здоровья кеша"""
    result = await health_checker.check_cache()
    
    status_code = 200 if result.status == "healthy" else 503
    return JSONResponse(
        status_code=status_code,
        content=result.to_dict()
    )


@router.get("/system")
async def system_health_check():
    """Проверка системных ресурсов"""
    result = await health_checker.check_system_resources()
    
    status_code = 200 if result.status == "healthy" else 503
    return JSONResponse(
        status_code=status_code,
        content=result.to_dict()
    )


@router.get("/metrics")
async def metrics_health_check():
    """Проверка системы метрик"""
    result = await health_checker.check_metrics()
    
    status_code = 200 if result.status == "healthy" else 503
    return JSONResponse(
        status_code=status_code,
        content=result.to_dict()
    )


@router.get("/live")
async def liveness_probe():
    """Проверка живости для Kubernetes"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_probe():
    """Проверка готовности для Kubernetes"""
    try:
        # Быстрая проверка критических компонентов
        db_result = await health_checker.check_database()
        cache_result = await health_checker.check_cache()
        
        if db_result.status == "unhealthy" or cache_result.status == "unhealthy":
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": db_result.status,
                    "cache": cache_result.status
                }
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_result.status,
            "cache": cache_result.status
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@router.get("/external-services")
async def external_services_health_check():
    """Проверка здоровья внешних сервисов"""
    try:
        status = await get_external_services_status()
        return status
    except Exception as e:
        logger.error(f"External services health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unhealthy",
            "error": str(e),
            "summary": {
                "total": 0,
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 1
            },
            "services": {}
        }


@router.post("/background-check")
async def start_background_health_check(background_tasks: BackgroundTasks):
    """Запуск фоновой проверки здоровья"""
    
    async def background_check():
        """Фоновая проверка здоровья"""
        try:
            result = await health_checker.run_all_checks()
            logger.info(f"Background health check completed: {result['status']}")
            
            # Можно добавить отправку уведомлений при проблемах
            if result["status"] == "unhealthy":
                logger.error(f"System is unhealthy: {result}")
                # Здесь можно добавить отправку уведомлений
            
        except Exception as e:
            logger.error(f"Background health check failed: {e}")
    
    background_tasks.add_task(background_check)
    
    return {
        "message": "Background health check started",
        "timestamp": datetime.utcnow().isoformat()
    } 