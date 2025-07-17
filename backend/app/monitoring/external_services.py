"""
Система health checks для внешних сервисов
"""
import asyncio
import aiohttp
import psutil
import os
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..core.config import settings
from ..core.database import engine, get_db
from ..core.cache import cache_manager
from .telegram_alerts import create_topic_and_alert

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Статусы внешних сервисов"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealthCheck:
    """Результат проверки здоровья сервиса"""
    service_name: str
    status: ServiceStatus
    response_time: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    last_check: datetime


class ExternalServicesHealthChecker:
    """Проверка здоровья внешних сервисов"""
    
    def __init__(self):
        self.checks: Dict[str, ServiceHealthCheck] = {}
        self.check_interval = 60  # секунды
        self.timeout = 10  # секунды
    
    async def check_redis_health(self) -> ServiceHealthCheck:
        """Проверка здоровья Redis"""
        start_time = time.time()
        
        try:
            # Проверяем подключение к Redis
            if cache_manager.redis_client:
                await cache_manager.redis_client.ping()
                response_time = time.time() - start_time
                
                # Проверяем производительность
                test_key = "health_check_test"
                await cache_manager.redis_client.set(test_key, "test_value", ex=60)
                await cache_manager.redis_client.get(test_key)
                await cache_manager.redis_client.delete(test_key)
                
                status = ServiceStatus.HEALTHY if response_time < 1.0 else ServiceStatus.DEGRADED
                
                return ServiceHealthCheck(
                    service_name="redis",
                    status=status,
                    response_time=response_time,
                    message="Redis is operational",
                    details={
                        "connected": True,
                        "response_time_ms": round(response_time * 1000, 2),
                        "memory_usage": await self._get_redis_memory_usage(),
                        "connected_clients": await self._get_redis_connected_clients()
                    },
                    timestamp=datetime.now(),
                    last_check=datetime.now()
                )
            else:
                return ServiceHealthCheck(
                    service_name="redis",
                    status=ServiceStatus.UNHEALTHY,
                    response_time=time.time() - start_time,
                    message="Redis client not initialized",
                    details={"connected": False},
                    timestamp=datetime.now(),
                    last_check=datetime.now()
                )
                
        except Exception as e:
            return ServiceHealthCheck(
                service_name="redis",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Redis connection failed: {str(e)}",
                details={"connected": False, "error": str(e)},
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
    
    async def check_database_health(self) -> ServiceHealthCheck:
        """Проверка здоровья базы данных"""
        start_time = time.time()
        
        try:
            async with engine.begin() as conn:
                # Простой запрос для проверки подключения
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Проверяем производительность
                result = await conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_requests
                    FROM requests
                """))
                data = result.fetchone()
                
                response_time = time.time() - start_time
                status = ServiceStatus.HEALTHY if response_time < 2.0 else ServiceStatus.DEGRADED
                
                return ServiceHealthCheck(
                    service_name="database",
                    status=status,
                    response_time=response_time,
                    message="Database is operational",
                    details={
                        "connected": True,
                        "response_time_ms": round(response_time * 1000, 2),
                        "total_requests": data[0] if data else 0,
                        "recent_requests": data[1] if data else 0,
                        "pool_size": engine.pool.size(),
                        "checked_in": engine.pool.checkedin(),
                        "checked_out": engine.pool.checkedout(),
                        "overflow": engine.pool.overflow()
                    },
                    timestamp=datetime.now(),
                    last_check=datetime.now()
                )
                
        except Exception as e:
            return ServiceHealthCheck(
                service_name="database",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Database connection failed: {str(e)}",
                details={"connected": False, "error": str(e)},
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
    
    async def check_file_system_health(self) -> ServiceHealthCheck:
        """Проверка здоровья файловой системы"""
        start_time = time.time()
        
        try:
            # Проверяем доступность директорий
            media_dir = os.path.join(os.getcwd(), "media")
            upload_dir = os.path.join(media_dir, "gorod", "rashod")
            recordings_dir = os.path.join(media_dir, "zayvka", "zapis")
            
            # Создаем директории если их нет
            os.makedirs(upload_dir, exist_ok=True)
            os.makedirs(recordings_dir, exist_ok=True)
            
            # Проверяем права на запись
            test_file = os.path.join(upload_dir, ".health_check")
            with open(test_file, 'w') as f:
                f.write("health_check")
            os.remove(test_file)
            
            # Проверяем свободное место
            disk_usage = psutil.disk_usage(media_dir)
            free_space_gb = disk_usage.free / (1024**3)
            
            response_time = time.time() - start_time
            status = ServiceStatus.HEALTHY if free_space_gb > 1.0 else ServiceStatus.DEGRADED
            
            return ServiceHealthCheck(
                service_name="file_system",
                status=status,
                response_time=response_time,
                message="File system is operational",
                details={
                    "writable": True,
                    "response_time_ms": round(response_time * 1000, 2),
                    "free_space_gb": round(free_space_gb, 2),
                    "total_space_gb": round(disk_usage.total / (1024**3), 2),
                    "used_percent": round(disk_usage.percent, 2),
                    "media_dir": media_dir,
                    "upload_dir": upload_dir,
                    "recordings_dir": recordings_dir
                },
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="file_system",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"File system check failed: {str(e)}",
                details={"writable": False, "error": str(e)},
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
    
    async def check_external_api_health(self) -> ServiceHealthCheck:
        """Проверка здоровья внешних API"""
        start_time = time.time()
        
        try:
            # Проверяем доступность внешних сервисов
            external_services = [
                {"name": "rambler_imap", "url": "https://imap.rambler.ru", "timeout": 5},
                {"name": "email_service", "url": "https://api.emailservice.com/health", "timeout": 3},
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for service in external_services:
                    try:
                        async with session.get(service["url"], timeout=service["timeout"]) as response:
                            results.append({
                                "service": service["name"],
                                "status": response.status,
                                "response_time": response.headers.get("X-Response-Time", "unknown")
                            })
                    except Exception as e:
                        results.append({
                            "service": service["name"],
                            "status": "error",
                            "error": str(e)
                        })
            
            response_time = time.time() - start_time
            healthy_services = len([r for r in results if r.get("status") == 200])
            total_services = len(results)
            
            if healthy_services == total_services:
                status = ServiceStatus.HEALTHY
            elif healthy_services > 0:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.UNHEALTHY
            
            return ServiceHealthCheck(
                service_name="external_apis",
                status=status,
                response_time=response_time,
                message=f"External APIs: {healthy_services}/{total_services} healthy",
                details={
                    "total_services": total_services,
                    "healthy_services": healthy_services,
                    "response_time_ms": round(response_time * 1000, 2),
                    "services": results
                },
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="external_apis",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"External API check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
    
    async def check_system_resources(self) -> ServiceHealthCheck:
        """Проверка системных ресурсов"""
        start_time = time.time()
        
        try:
            # CPU использование
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Память
            memory = psutil.virtual_memory()
            
            # Диск
            disk = psutil.disk_usage('/')
            
            # Сетевые соединения
            network = psutil.net_io_counters()
            
            response_time = time.time() - start_time
            
            # Определяем статус на основе использования ресурсов
            if cpu_percent < 70 and memory.percent < 80 and disk.percent < 85:
                status = ServiceStatus.HEALTHY
            elif cpu_percent < 90 and memory.percent < 90 and disk.percent < 95:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.UNHEALTHY
            
            return ServiceHealthCheck(
                service_name="system_resources",
                status=status,
                response_time=response_time,
                message="System resources are within acceptable limits",
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory.percent, 2),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk.percent, 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                    "network_bytes_sent": network.bytes_sent,
                    "network_bytes_recv": network.bytes_recv,
                    "response_time_ms": round(response_time * 1000, 2)
                },
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
            
        except Exception as e:
            return ServiceHealthCheck(
                service_name="system_resources",
                status=ServiceStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"System resources check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                last_check=datetime.now()
            )
    
    async def run_all_checks(self) -> Dict[str, ServiceHealthCheck]:
        """Запуск всех проверок здоровья и отправка алертов в Telegram при проблемах"""
        logger.info("Running external services health checks")
        
        checks = await asyncio.gather(
            self.check_redis_health(),
            self.check_database_health(),
            self.check_file_system_health(),
            self.check_external_api_health(),
            self.check_system_resources(),
            return_exceptions=True
        )
        
        results = {}
        for check in checks:
            if isinstance(check, ServiceHealthCheck):
                results[check.service_name] = check
                self.checks[check.service_name] = check
                # Отправляем алерт если статус degraded или unhealthy
                if check.status in (ServiceStatus.DEGRADED, ServiceStatus.UNHEALTHY):
                    msg = f"Статус: <b>{check.status.value.upper()}</b>\n" \
                          f"Время ответа: {round(check.response_time*1000, 2)} мс\n" \
                          f"Сообщение: {check.message}\n" \
                          f"Детали: <pre>{check.details}</pre>"
                    asyncio.create_task(create_topic_and_alert(check.service_name, msg))
            else:
                logger.error(f"Health check failed with exception: {check}")
        
        return results
    
    async def _get_redis_memory_usage(self) -> Optional[Dict[str, Any]]:
        """Получить информацию об использовании памяти Redis"""
        try:
            if cache_manager.redis_client:
                info = await cache_manager.redis_client.info("memory")
                return {
                    "used_memory_human": info.get("used_memory_human"),
                    "used_memory_peak_human": info.get("used_memory_peak_human"),
                    "used_memory_rss_human": info.get("used_memory_rss_human")
                }
        except Exception:
            pass
        return None
    
    async def _get_redis_connected_clients(self) -> Optional[int]:
        """Получить количество подключенных клиентов Redis"""
        try:
            if cache_manager.redis_client:
                info = await cache_manager.redis_client.info("clients")
                return info.get("connected_clients", 0)
        except Exception:
            pass
        return None


# Глобальный экземпляр
external_services_checker = ExternalServicesHealthChecker()


async def start_external_services_monitoring():
    """Запуск мониторинга внешних сервисов"""
    logger.info("Starting external services monitoring")
    
    while True:
        try:
            await external_services_checker.run_all_checks()
            await asyncio.sleep(external_services_checker.check_interval)
        except Exception as e:
            logger.error(f"External services monitoring error: {e}")
            await asyncio.sleep(30)  # Пауза при ошибке


async def get_external_services_status() -> Dict[str, Any]:
    """Получить статус всех внешних сервисов"""
    checks = await external_services_checker.run_all_checks()
    
    # Подсчитываем общую статистику
    total_checks = len(checks)
    healthy_checks = len([c for c in checks.values() if c.status == ServiceStatus.HEALTHY])
    degraded_checks = len([c for c in checks.values() if c.status == ServiceStatus.DEGRADED])
    unhealthy_checks = len([c for c in checks.values() if c.status == ServiceStatus.UNHEALTHY])
    
    return {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy" if unhealthy_checks == 0 else "degraded" if degraded_checks > 0 else "unhealthy",
        "summary": {
            "total": total_checks,
            "healthy": healthy_checks,
            "degraded": degraded_checks,
            "unhealthy": unhealthy_checks
        },
        "services": {
            name: {
                "status": check.status.value,
                "response_time_ms": round(check.response_time * 1000, 2),
                "message": check.message,
                "details": check.details,
                "last_check": check.last_check.isoformat()
            }
            for name, check in checks.items()
        }
    } 