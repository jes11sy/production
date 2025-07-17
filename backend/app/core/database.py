from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import event, text
import logging
import asyncio
from typing import AsyncGenerator
from .config import settings

logger = logging.getLogger(__name__)

# Создание асинхронного движка базы данных с оптимизированным пулом соединений
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",  # Логирование только в разработке
    future=True,
    # Оптимизированные настройки пула соединений
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.DB_POOL_SIZE,  # Базовый размер пула
    max_overflow=settings.DB_MAX_OVERFLOW,  # Дополнительные соединения при пиковой нагрузке
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Таймаут ожидания соединения
    pool_recycle=settings.DB_POOL_RECYCLE,  # Время жизни соединения (3600 = 1 час)
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_reset_on_return='commit',  # Сброс состояния при возврате соединения
    # Настройки для PostgreSQL
    connect_args={
        "server_settings": {
            "jit": "off",  # Отключаем JIT для стабильности
            "statement_timeout": "30s",  # Таймаут для запросов
            "lock_timeout": "10s",  # Таймаут для блокировок
            "idle_in_transaction_session_timeout": "60s",  # Таймаут для неактивных транзакций
            "tcp_keepalives_idle": "600",  # TCP keepalive настройки
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "3",
        },
        "command_timeout": 30,  # Таймаут команд
        "prepared_statement_cache_size": 0,  # Отключаем кеш prepared statements для стабильности
    }
)

# Создание фабрики сессий с оптимизированными настройками
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Отключаем автоматический flush для лучшего контроля
    autocommit=False
)

# Базовый класс для моделей
Base = declarative_base()


# Статистика пула соединений
class ConnectionPoolStats:
    """Класс для сбора статистики пула соединений"""
    
    @staticmethod
    def get_pool_stats():
        """Получение статистики пула соединений"""
        pool = engine.pool
        return {
            "size": getattr(pool, 'size', lambda: 0)(),
            "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
            "overflow": getattr(pool, 'overflow', lambda: 0)(),
            "invalid": getattr(pool, 'invalid', lambda: 0)(),
            "total_connections": getattr(pool, 'size', lambda: 0)() + getattr(pool, 'overflow', lambda: 0)(),
            "available_connections": getattr(pool, 'size', lambda: 0)() - getattr(pool, 'checkedout', lambda: 0)()
        }
    
    @staticmethod
    def log_pool_stats():
        """Логирование статистики пула"""
        stats = ConnectionPoolStats.get_pool_stats()
        logger.info(f"DB Pool Stats: {stats}")


# Event listeners для мониторинга пула соединений
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Настройка соединения при подключении"""
    if settings.DATABASE_URL.startswith("sqlite"):
        # Настройки для SQLite
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Обработка получения соединения из пула"""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Обработка возврата соединения в пул"""
    logger.debug("Connection checked in to pool")


@event.listens_for(engine.sync_engine, "invalidate")
def receive_invalidate(dbapi_connection, connection_record, exception):
    """Обработка инвалидации соединения"""
    logger.warning(f"Connection invalidated: {exception}")


# Dependency для получения сессии базы данных с улучшенной обработкой ошибок
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных
    
    Включает:
    - Автоматическое управление транзакциями
    - Обработку ошибок соединения
    - Мониторинг производительности
    - Graceful cleanup
    """
    session = None
    start_time = asyncio.get_event_loop().time()
    
    try:
        session = AsyncSessionLocal()
        logger.debug("Database session created")
        
        yield session
        
        # Если не было исключений, коммитим транзакцию
        if session.in_transaction():
            await session.commit()
            logger.debug("Transaction committed")
            
    except Exception as e:
        # В случае ошибки откатываем транзакцию
        if session and session.in_transaction():
            await session.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
        raise
        
    finally:
        # Всегда закрываем сессию
        if session:
            await session.close()
            duration = asyncio.get_event_loop().time() - start_time
            logger.debug(f"Database session closed (duration: {duration:.3f}s)")


# Функция для проверки здоровья базы данных
async def check_database_health() -> dict:
    """Проверка здоровья базы данных"""
    try:
        async with AsyncSessionLocal() as session:
            # Простой запрос для проверки соединения
            result = await session.execute(text("SELECT 1"))
            await session.commit()
            
            # Получаем статистику пула
            pool_stats = ConnectionPoolStats.get_pool_stats()
            
            return {
                "status": "healthy",
                "connection_test": "passed",
                "pool_stats": pool_stats
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_stats": ConnectionPoolStats.get_pool_stats()
        }


# Функция для оптимизации производительности
async def optimize_database_performance():
    """Оптимизация производительности базы данных"""
    try:
        async with AsyncSessionLocal() as session:
            if settings.DATABASE_URL.startswith("postgresql"):
                # Оптимизации для PostgreSQL
                await session.execute(text("ANALYZE;"))  # Обновляем статистику
                logger.info("Database statistics updated")
                
            await session.commit()
            
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")


# Функция для мониторинга долгих запросов
async def monitor_slow_queries():
    """Мониторинг медленных запросов"""
    try:
        async with AsyncSessionLocal() as session:
            if settings.DATABASE_URL.startswith("postgresql"):
                # Запрос для получения медленных запросов
                slow_queries = await session.execute(text("""
                    SELECT query, mean_time, calls, total_time
                    FROM pg_stat_statements
                    WHERE mean_time > 1000  -- запросы дольше 1 секунды
                    ORDER BY mean_time DESC
                    LIMIT 10;
                """))
                
                for query in slow_queries:
                    logger.warning(f"Slow query detected: {query}")
                    
            await session.commit()
            
    except Exception as e:
        logger.debug(f"Slow query monitoring failed (this is normal if pg_stat_statements is not enabled): {e}")


# Функция для очистки соединений
async def cleanup_connections():
    """Очистка соединений при завершении работы"""
    try:
        # Закрываем все соединения в пуле
        await engine.dispose()
        logger.info("Database connections cleaned up")
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")


# Периодическая задача для мониторинга пула
async def monitor_connection_pool():
    """Периодический мониторинг пула соединений"""
    while True:
        try:
            # Логируем статистику каждые 5 минут
            await asyncio.sleep(300)
            ConnectionPoolStats.log_pool_stats()
            
            # Проверяем здоровье базы данных
            health = await check_database_health()
            if health["status"] != "healthy":
                logger.error(f"Database health check failed: {health}")
                
        except asyncio.CancelledError:
            logger.info("Connection pool monitoring stopped")
            break
        except Exception as e:
            logger.error(f"Connection pool monitoring error: {e}")
            await asyncio.sleep(60)  # Ждем минуту перед повторной попыткой 