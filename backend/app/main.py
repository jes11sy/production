from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import asyncio
import signal
import logging
from contextlib import asynccontextmanager
from .core.config import settings
from .core.database import engine, Base
from .api import auth, requests, transactions, users
from .api import files
from .api import file_access
from .api import mango
from .api import recordings
from .api import health
from .api import database
# from .api import migrations  # Временно отключено из-за конфликта с alembic
from .api import metrics
from .api import prometheus_metrics
from .api import security
from .api import monitoring
from .middleware import (
    RateLimitMiddleware,
    CacheMiddleware
)
try:
    from .middleware.error_handler import (
        ErrorHandlingMiddleware,
        RequestLoggingMiddleware,
        setup_error_handlers
    )
except ImportError:
    # Fallback для совместимости
    from .middleware import (
        ErrorHandlingMiddleware,
        RequestLoggingMiddleware
    )
    def setup_error_handlers(app):
        pass
from .core.security import (
    CSRFMiddleware,
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
    cleanup_security_data
)
from .logging_config import setup_logging
from .api_docs import setup_api_documentation
from .monitoring.metrics import start_metrics_collection, stop_metrics_collection, MetricsMiddleware, performance_collector
from .monitoring.connection_pool_monitor import start_pool_monitoring
from .monitoring.redis_monitor import start_redis_monitoring
from .monitoring.alerts import start_alert_monitoring
from .monitoring.external_services import start_external_services_monitoring

# Инициализация логирования
setup_logging()
logger = logging.getLogger(__name__)

# Глобальные переменные для управления фоновыми задачами
background_tasks = []
shutdown_event = asyncio.Event()

# Периодическая очистка данных безопасности
async def periodic_security_cleanup():
    """Периодическая очистка данных безопасности каждые 30 минут"""
    while not shutdown_event.is_set():
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=1800)  # 30 минут
            break  # Выходим если получили сигнал shutdown
        except asyncio.TimeoutError:
            # Время вышло, выполняем очистку
            try:
                await cleanup_security_data()
                logger.info("Security data cleanup completed")
            except Exception as e:
                logger.error(f"Error during security cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения с graceful shutdown"""
    logger.info("Starting application...")
    
    try:
        # Создание таблиц в базе данных
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Инициализация Redis кеша
        from .core.cache import cache_manager
        await cache_manager.initialize()
        logger.info("Redis cache initialized")
        
        # Запуск сервиса записей звонков
        from .services.recording_service import start_recording_service
        await start_recording_service()
        logger.info("Recording service started")
        
        # Запуск сбора метрик
        await start_metrics_collection()
        logger.info("Metrics collection started")
        
        # Запуск мониторинга connection pool
        pool_monitoring_task = asyncio.create_task(start_pool_monitoring())
        background_tasks.append(pool_monitoring_task)
        logger.info("Connection pool monitoring started")
        
        # Запуск мониторинга Redis
        redis_monitoring_task = asyncio.create_task(start_redis_monitoring())
        background_tasks.append(redis_monitoring_task)
        logger.info("Redis monitoring started")
        
        # Запуск системы алертов
        alert_monitoring_task = asyncio.create_task(start_alert_monitoring())
        background_tasks.append(alert_monitoring_task)
        logger.info("Alert monitoring started")
        
        # Запуск мониторинга внешних сервисов
        external_services_task = asyncio.create_task(start_external_services_monitoring())
        background_tasks.append(external_services_task)
        logger.info("External services monitoring started")
        
        # Запуск периодической очистки данных безопасности
        security_cleanup_task = asyncio.create_task(periodic_security_cleanup())
        background_tasks.append(security_cleanup_task)
        logger.info("Security cleanup task started")
        
        logger.info("Application startup completed successfully")
        
        yield  # Приложение работает
        
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    
    finally:
        # Graceful shutdown
        logger.info("Starting graceful shutdown...")
        
        # Устанавливаем событие shutdown
        shutdown_event.set()
        
        # Останавливаем фоновые задачи
        logger.info("Stopping background tasks...")
        for task in background_tasks:
            if not task.done():
                task.cancel()
        
        # Ждем завершения всех задач с таймаутом
        if background_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*background_tasks, return_exceptions=True),
                    timeout=30.0
                )
                logger.info("Background tasks stopped successfully")
            except asyncio.TimeoutError:
                logger.warning("Background tasks shutdown timeout - forcing termination")
        
        # Остановка сервиса записей звонков
        try:
            from .services.recording_service import stop_recording_service
            await stop_recording_service()
            logger.info("Recording service stopped")
        except Exception as e:
            logger.error(f"Error stopping recording service: {e}")
        
        # Остановка сбора метрик
        try:
            await stop_metrics_collection()
            logger.info("Metrics collection stopped")
        except Exception as e:
            logger.error(f"Error stopping metrics collection: {e}")
        
        # Закрытие Redis соединения
        try:
            from .core.cache import cache_manager
            await cache_manager.close()
            logger.info("Redis cache closed")
        except Exception as e:
            logger.error(f"Error closing Redis cache: {e}")
        
        # Закрытие соединений с базой данных
        try:
            await engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
        
        logger.info("Graceful shutdown completed")


# Создание экземпляра FastAPI с lifespan
app = FastAPI(
    title="Система управления заявками",
    description="API для управления заявками, транзакциями и пользователями",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ВКЛЮЧАЕМ CORS MIDDLEWARE ПЕРВЫМ!
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "DNT", "Cache-Control", "X-Mx-ReqToken", "Keep-Alive", "X-Requested-With", "If-Modified-Since"]
)

# Настройка интерактивной документации
setup_api_documentation(app)

# Security и Performance Middleware для Production
if settings.ENVIRONMENT == "production":
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_size=100 * 1024 * 1024)  # 100MB
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    )
    app.add_middleware(CacheMiddleware, cache_ttl=settings.CACHE_TTL)
    app.middleware("http")(MetricsMiddleware(performance_collector))

# Базовые middleware для всех сред
try:
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
except Exception as e:
    logger.warning(f"Could not add error handling middleware: {e}")

# CSRF только для production (может конфликтовать с API тестированием)
if settings.ENVIRONMENT == "production":
    try:
        app.add_middleware(CSRFMiddleware)
    except Exception as e:
        logger.warning(f"Could not add CSRF middleware: {e}")

# Подключение статических файлов
if os.path.exists("media"):
    app.mount("/media", StaticFiles(directory="media"), name="media")

# Подключение версионированных роутеров
from .api.v1.router import v1_router
from .api.v2.router import v2_router
from .core.versioning import version_middleware

# Настраиваем улучшенную обработку ошибок
setup_error_handlers(app)

# Добавляем middleware для версионирования
app.middleware("http")(version_middleware)

# Подключаем версионированные роутеры
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

# Обратная совместимость - роутеры без версии направляем в v1
app.include_router(auth.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(file_access.router, prefix="/api")
app.include_router(mango.router, prefix="/api")
app.include_router(recordings.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(database.router, prefix="/api")
# app.include_router(migrations.router, prefix="/api")  # Временно отключено
app.include_router(metrics.router, prefix="/api")
app.include_router(prometheus_metrics.router, prefix="/api")
app.include_router(security.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])


# Обработчик сигналов для graceful shutdown
def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


# Регистрация обработчиков сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    from fastapi.responses import JSONResponse
    return JSONResponse(content={
        "message": "Система управления заявками",
        "api_versions": {
            "v1": {
                "version": "1.0.0",
                "status": "stable",
                "docs": "/docs",
                "health": "/api/v1/health"
            },
            "v2": {
                "version": "2.0.0",
                "status": "beta",
                "docs": "/docs",
                "health": "/api/v2/health",
                "features": "/api/v2/features"
            }
        },
        "default_version": "v1",
        "versioning": {
            "header": "API-Version",
            "path": "/api/v{version}",
            "supported": ["1.0", "2.0"]
        }
    })


@app.get("/health")
async def health_check():
    """Быстрая проверка здоровья приложения"""
    return {"status": "healthy", "timestamp": "2025-01-15T21:54:09Z"}


@app.get("/metrics/prometheus")
async def prometheus_metrics():
    """Публичный эндпоинт для Prometheus метрик"""
    from app.monitoring.prometheus_metrics import get_metrics, get_metrics_content_type
    from fastapi.responses import Response
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_graceful_shutdown=30,  # Graceful shutdown timeout
        limit_concurrency=1000,  # Ограничиваем количество одновременных соединений
        backlog=2048  # Размер очереди соединений
    ) 