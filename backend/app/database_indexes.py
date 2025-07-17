"""
Индексы для оптимизации базы данных
"""
from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession
from .core.models import Request, Transaction, Master, Employee, Administrator, File
from .core.database import engine
import logging

logger = logging.getLogger(__name__)

# Определение индексов для оптимизации запросов
DATABASE_INDEXES = [
    # Индексы для таблицы requests (основные запросы)
    Index('idx_requests_created_at', Request.created_at.desc()),  # Сортировка по дате создания
    Index('idx_requests_status', Request.status),  # Фильтрация по статусу
    Index('idx_requests_city_id', Request.city_id),  # Фильтрация по городу
    Index('idx_requests_client_phone', Request.client_phone),  # Поиск по телефону
    Index('idx_requests_master_id', Request.master_id),  # Фильтрация по мастеру
    Index('idx_requests_request_type_id', Request.request_type_id),  # Фильтрация по типу
    Index('idx_requests_advertising_campaign_id', Request.advertising_campaign_id),  # Фильтрация по РК
    
    # Составные индексы для частых комбинаций
    Index('idx_requests_phone_created', Request.client_phone, Request.created_at.desc()),  # Поиск дубликатов
    Index('idx_requests_city_status', Request.city_id, Request.status),  # Отчеты по городам
    Index('idx_requests_city_created', Request.city_id, Request.created_at.desc()),  # Отчеты по городам с датой
    Index('idx_requests_status_created', Request.status, Request.created_at.desc()),  # Отчеты по статусам
    Index('idx_requests_master_status', Request.master_id, Request.status),  # Заявки мастера по статусу
    
    # Индексы для таблицы transactions
    Index('idx_transactions_created_at', Transaction.created_at.desc()),  # Сортировка по дате
    Index('idx_transactions_city_id', Transaction.city_id),  # Фильтрация по городу
    Index('idx_transactions_type_id', Transaction.transaction_type_id),  # Фильтрация по типу
    Index('idx_transactions_specified_date', Transaction.specified_date.desc()),  # Фильтрация по дате операции
    Index('idx_transactions_amount', Transaction.amount),  # Фильтрация по сумме
    
    # Составные индексы для transactions
    Index('idx_transactions_city_date', Transaction.city_id, Transaction.specified_date.desc()),  # Отчеты по городам
    Index('idx_transactions_type_date', Transaction.transaction_type_id, Transaction.specified_date.desc()),  # Отчеты по типам
    Index('idx_transactions_city_type', Transaction.city_id, Transaction.transaction_type_id),  # Комбинированная фильтрация
    
    # Индексы для таблицы masters
    Index('idx_masters_city_id', Master.city_id),  # Фильтрация по городу
    Index('idx_masters_status', Master.status),  # Фильтрация по статусу
    Index('idx_masters_login', Master.login),  # Уникальный поиск по логину (уже есть unique, но для оптимизации)
    Index('idx_masters_phone', Master.phone_number),  # Поиск по телефону
    Index('idx_masters_created_at', Master.created_at.desc()),  # Сортировка по дате создания
    
    # Составные индексы для masters
    Index('idx_masters_city_status', Master.city_id, Master.status),  # Активные мастера по городам
    
    # Индексы для таблицы employees
    Index('idx_employees_city_id', Employee.city_id),  # Фильтрация по городу
    Index('idx_employees_role_id', Employee.role_id),  # Фильтрация по роли
    Index('idx_employees_status', Employee.status),  # Фильтрация по статусу
    Index('idx_employees_login', Employee.login),  # Уникальный поиск по логину
    Index('idx_employees_created_at', Employee.created_at.desc()),  # Сортировка по дате создания
    
    # Составные индексы для employees
    Index('idx_employees_role_city', Employee.role_id, Employee.city_id),  # Сотрудники по роли и городу
    Index('idx_employees_city_status', Employee.city_id, Employee.status),  # Активные сотрудники по городам
    
    # Индексы для таблицы administrators
    Index('idx_administrators_role_id', Administrator.role_id),  # Фильтрация по роли
    Index('idx_administrators_status', Administrator.status),  # Фильтрация по статусу
    Index('idx_administrators_login', Administrator.login),  # Уникальный поиск по логину
    Index('idx_administrators_created_at', Administrator.created_at.desc()),  # Сортировка по дате создания
    
    # Индексы для таблицы files
    Index('idx_files_request_id', File.request_id),  # Файлы по заявке
    Index('idx_files_transaction_id', File.transaction_id),  # Файлы по транзакции
    Index('idx_files_type', File.file_type),  # Фильтрация по типу файла
    Index('idx_files_uploaded_at', File.uploaded_at.desc()),  # Сортировка по дате загрузки
    
    # Составные индексы для files
    Index('idx_files_request_type', File.request_id, File.file_type),  # Файлы заявки по типу
    Index('idx_files_transaction_type', File.transaction_id, File.file_type),  # Файлы транзакции по типу
]

# Дополнительные индексы для специфических запросов
PERFORMANCE_INDEXES = [
    # Индекс для поиска дубликатов заявок (защита от Mango Office)
    # Убираем WHERE условие с NOW() так как оно не IMMUTABLE
    Index('idx_requests_phone_time_window', 
          Request.client_phone, 
          Request.created_at.desc()),
    
    # Индекс для отчета колл-центра
    Index('idx_requests_callcenter_report', 
          Request.city_id, 
          Request.status, 
          Request.created_at.desc()),
    
    # Индекс для поиска записей звонков
    Index('idx_requests_phone_datetime', 
          Request.client_phone, 
          Request.created_at),
    
    # Индекс для финансовых отчетов
    Index('idx_transactions_financial_report', 
          Transaction.city_id, 
          Transaction.specified_date.desc(), 
          Transaction.amount),
    
    # Индекс для поиска активных мастеров
    Index('idx_masters_active', 
          Master.city_id, 
          Master.status,
          postgresql_where=text("status = 'active'")),
    
    # Индекс для поиска активных сотрудников
    Index('idx_employees_active', 
          Employee.city_id, 
          Employee.role_id,
          Employee.status,
          postgresql_where=text("status = 'active'")),
]

async def create_database_indexes():
    """Создание всех индексов для оптимизации производительности"""
    logger.info("Creating database indexes for performance optimization...")
    
    async with engine.begin() as conn:
        try:
            # Создаем основные индексы
            for index in DATABASE_INDEXES:
                try:
                    await conn.run_sync(index.create, checkfirst=True)
                    logger.info(f"Created index: {index.name}")
                except Exception as e:
                    logger.warning(f"Index {index.name} already exists or failed to create: {e}")
            
            # Создаем индексы для производительности
            for index in PERFORMANCE_INDEXES:
                try:
                    await conn.run_sync(index.create, checkfirst=True)
                    logger.info(f"Created performance index: {index.name}")
                except Exception as e:
                    logger.warning(f"Performance index {index.name} already exists or failed to create: {e}")
            
            logger.info("Database indexes creation completed!")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise

async def drop_database_indexes():
    """Удаление всех созданных индексов"""
    logger.info("Dropping database indexes...")
    
    async with engine.begin() as conn:
        try:
            # Удаляем индексы для производительности
            for index in reversed(PERFORMANCE_INDEXES):
                try:
                    await conn.run_sync(index.drop, checkfirst=True)
                    logger.info(f"Dropped performance index: {index.name}")
                except Exception as e:
                    logger.warning(f"Performance index {index.name} doesn't exist or failed to drop: {e}")
            
            # Удаляем основные индексы
            for index in reversed(DATABASE_INDEXES):
                try:
                    await conn.run_sync(index.drop, checkfirst=True)
                    logger.info(f"Dropped index: {index.name}")
                except Exception as e:
                    logger.warning(f"Index {index.name} doesn't exist or failed to drop: {e}")
            
            logger.info("Database indexes removal completed!")
            
        except Exception as e:
            logger.error(f"Error dropping database indexes: {e}")
            raise

async def analyze_query_performance():
    """Анализ производительности запросов"""
    logger.info("Analyzing query performance...")
    
    async with engine.begin() as conn:
        try:
            # Анализируем самые медленные запросы
            slow_queries = await conn.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    min_time,
                    max_time
                FROM pg_stat_statements 
                WHERE mean_time > 100 
                ORDER BY mean_time DESC 
                LIMIT 10
            """))
            
            logger.info("Top 10 slowest queries:")
            for row in slow_queries.fetchall():
                logger.info(f"Query: {row[0][:100]}... | Calls: {row[1]} | Mean time: {row[2]:.2f}ms")
                
            # Анализируем использование индексов
            index_usage = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
                LIMIT 20
            """))
            
            logger.info("Top 20 most used indexes:")
            for row in index_usage.fetchall():
                logger.info(f"Table: {row[1]} | Index: {row[2]} | Scans: {row[3]} | Tuples read: {row[4]}")
                
        except Exception as e:
            logger.warning(f"Query performance analysis failed (pg_stat_statements might not be enabled): {e}")

async def get_database_statistics():
    """Получение статистики базы данных"""
    async with engine.begin() as conn:
        try:
            # Размеры таблиц
            table_sizes = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC
            """))
            
            stats = {
                "table_sizes": [
                    {
                        "schema": row[0],
                        "table": row[1], 
                        "size": row[2],
                        "size_bytes": row[3]
                    }
                    for row in table_sizes.fetchall()
                ],
                "total_connections": 0,
                "active_connections": 0
            }
            
            # Информация о соединениях
            connections = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            
            conn_data = connections.fetchone()
            if conn_data:
                stats["total_connections"] = conn_data[0]
                stats["active_connections"] = conn_data[1]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {"error": str(e)} 