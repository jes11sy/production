"""
Улучшенные индексы для оптимизации производительности базы данных
Версия 2.0 - с дополнительными оптимизациями
"""
from sqlalchemy import Index, text
from sqlalchemy.ext.asyncio import AsyncSession
from .core.models import Request, Transaction, Master, Employee, Administrator, File, City, RequestType, TransactionType
from .core.database import engine
import logging

logger = logging.getLogger(__name__)

# Основные индексы для оптимизации запросов
PERFORMANCE_INDEXES_V2 = [
    # === ЗАЯВКИ (REQUESTS) ===
    
    # Основные индексы для фильтрации
    Index('idx_requests_created_at_v2', Request.created_at.desc()),
    Index('idx_requests_status_v2', Request.status),
    Index('idx_requests_city_id_v2', Request.city_id),
    Index('idx_requests_client_phone_v2', Request.client_phone),
    Index('idx_requests_master_id_v2', Request.master_id),
    Index('idx_requests_request_type_id_v2', Request.request_type_id),
    Index('idx_requests_advertising_campaign_id_v2', Request.advertising_campaign_id),
    
    # Составные индексы для частых комбинаций запросов
    Index('idx_requests_phone_created_v2', Request.client_phone, Request.created_at.desc()),
    Index('idx_requests_city_status_v2', Request.city_id, Request.status),
    Index('idx_requests_city_created_v2', Request.city_id, Request.created_at.desc()),
    Index('idx_requests_status_created_v2', Request.status, Request.created_at.desc()),
    Index('idx_requests_master_status_v2', Request.master_id, Request.status),
    Index('idx_requests_city_type_v2', Request.city_id, Request.request_type_id),
    
    # Специальные индексы для бизнес-логики
    # Убираем WHERE условие с NOW() так как оно не IMMUTABLE
    Index('idx_requests_phone_time_window_v2', 
          Request.client_phone, 
          Request.created_at.desc()),
    
    Index('idx_requests_callcenter_report_v2', 
          Request.city_id, 
          Request.status, 
          Request.created_at.desc()),
    
    Index('idx_requests_master_assignment_v2',
          Request.city_id,
          Request.status,
          Request.master_id,
          postgresql_where=text("status IN ('new', 'assigned')")),
    
    # Индекс для поиска записей звонков
    Index('idx_requests_phone_datetime_v2', 
          Request.client_phone, 
          Request.created_at),
    
    # Индекс для статистики конверсии
    Index('idx_requests_conversion_stats_v2',
          Request.city_id,
          Request.status,
          Request.created_at.desc(),
          postgresql_where=text("status IN ('done', 'cancelled')")),
    
    # === ТРАНЗАКЦИИ (TRANSACTIONS) ===
    
    # Основные индексы для транзакций
    Index('idx_transactions_created_at_v2', Transaction.created_at.desc()),
    Index('idx_transactions_city_id_v2', Transaction.city_id),
    Index('idx_transactions_type_id_v2', Transaction.transaction_type_id),
    Index('idx_transactions_specified_date_v2', Transaction.specified_date.desc()),
    Index('idx_transactions_amount_v2', Transaction.amount),
    
    # Составные индексы для финансовых отчетов
    Index('idx_transactions_city_date_v2', Transaction.city_id, Transaction.specified_date.desc()),
    Index('idx_transactions_type_date_v2', Transaction.transaction_type_id, Transaction.specified_date.desc()),
    Index('idx_transactions_city_type_v2', Transaction.city_id, Transaction.transaction_type_id),
    Index('idx_transactions_city_amount_v2', Transaction.city_id, Transaction.amount),
    
    # Индекс для финансовых сводок
    Index('idx_transactions_financial_report_v2', 
          Transaction.city_id, 
          Transaction.specified_date.desc(), 
          Transaction.amount),
    
    # Индекс для поиска по диапазону сумм
    Index('idx_transactions_amount_range_v2',
          Transaction.city_id,
          Transaction.amount,
          Transaction.specified_date.desc()),
    
    # === МАСТЕРА (MASTERS) ===
    
    # Основные индексы для мастеров
    Index('idx_masters_city_id_v2', Master.city_id),
    Index('idx_masters_status_v2', Master.status),
    Index('idx_masters_login_v2', Master.login),
    Index('idx_masters_phone_v2', Master.phone_number),
    Index('idx_masters_created_at_v2', Master.created_at.desc()),
    
    # Составные индексы
    Index('idx_masters_city_status_v2', Master.city_id, Master.status),
    Index('idx_masters_active_v2', 
          Master.city_id, 
          Master.status,
          postgresql_where=text("status = 'active'")),
    
    # === СОТРУДНИКИ (EMPLOYEES) ===
    
    # Основные индексы для сотрудников
    Index('idx_employees_city_id_v2', Employee.city_id),
    Index('idx_employees_role_id_v2', Employee.role_id),
    Index('idx_employees_status_v2', Employee.status),
    Index('idx_employees_login_v2', Employee.login),
    Index('idx_employees_created_at_v2', Employee.created_at.desc()),
    
    # Составные индексы
    Index('idx_employees_role_city_v2', Employee.role_id, Employee.city_id),
    Index('idx_employees_city_status_v2', Employee.city_id, Employee.status),
    Index('idx_employees_active_v2', 
          Employee.city_id, 
          Employee.role_id,
          Employee.status,
          postgresql_where=text("status = 'active'")),
    
    # === АДМИНИСТРАТОРЫ (ADMINISTRATORS) ===
    
    # Основные индексы для администраторов
    Index('idx_administrators_role_id_v2', Administrator.role_id),
    Index('idx_administrators_status_v2', Administrator.status),
    Index('idx_administrators_login_v2', Administrator.login),
    Index('idx_administrators_created_at_v2', Administrator.created_at.desc()),
    
    # === ФАЙЛЫ (FILES) ===
    
    # Основные индексы для файлов
    Index('idx_files_request_id_v2', File.request_id),
    Index('idx_files_transaction_id_v2', File.transaction_id),
    Index('idx_files_type_v2', File.file_type),
    Index('idx_files_uploaded_at_v2', File.uploaded_at.desc()),
    
    # Составные индексы
    Index('idx_files_request_type_v2', File.request_id, File.file_type),
    Index('idx_files_transaction_type_v2', File.transaction_id, File.file_type),
]

# Дополнительные индексы для специфических запросов
SPECIALIZED_INDEXES = [
    # Индексы для поиска дубликатов
    Index('idx_requests_duplicate_check_v2',
          Request.client_phone,
          Request.status,
          Request.created_at.desc(),
          postgresql_where=text("status = 'new'")),
    
    # Индексы для Mango Office интеграции
    Index('idx_requests_mango_integration_v2',
          Request.client_phone,
          Request.ats_number,
          Request.created_at.desc()),
    
    # Индексы для отчетов по производительности
    Index('idx_requests_performance_report_v2',
          Request.city_id,
          Request.master_id,
          Request.status,
          Request.created_at.desc()),
    
    # Индексы для поиска по диапазону дат
    Index('idx_requests_date_range_v2',
          Request.created_at,
          Request.city_id,
          Request.status),
    
    # Индексы для финансовой аналитики
    Index('idx_transactions_analytics_v2',
          Transaction.city_id,
          Transaction.transaction_type_id,
          Transaction.specified_date.desc(),
          Transaction.amount),
    
    # Индексы для поиска по результатам заявок
    Index('idx_requests_results_v2',
          Request.city_id,
          Request.result,
          Request.created_at.desc(),
          postgresql_where=text("result IS NOT NULL")),
]

# Функциональные индексы для оптимизации специфических запросов
FUNCTIONAL_INDEXES = [
    # Индекс для поиска по части телефона
    Index('idx_requests_phone_partial_v2',
          text("substring(client_phone, 1, 10)"),
          Request.created_at.desc()),
    
    # Индекс для поиска по дате без времени
    Index('idx_requests_date_only_v2',
          text("DATE(created_at)"),
          Request.city_id),
    
    # Индекс для поиска по месяцу и году
    Index('idx_transactions_month_year_v2',
          text("EXTRACT(YEAR FROM specified_date)"),
          text("EXTRACT(MONTH FROM specified_date)"),
          Transaction.city_id),
]

async def create_performance_indexes_v2():
    """Создание улучшенных индексов для производительности"""
    logger.info("Создание индексов производительности v2...")
    
    async with engine.begin() as conn:
        try:
            # Создаем основные индексы
            for index in PERFORMANCE_INDEXES_V2:
                try:
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table.name} {index._create_index_sql()}"))
                    logger.info(f"Создан индекс: {index.name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Ошибка создания индекса {index.name}: {e}")
            
            # Создаем специализированные индексы
            for index in SPECIALIZED_INDEXES:
                try:
                    await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table.name} {index._create_index_sql()}"))
                    logger.info(f"Создан специализированный индекс: {index.name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Ошибка создания специализированного индекса {index.name}: {e}")
            
            # Создаем функциональные индексы
            functional_index_queries = [
                """
                CREATE INDEX IF NOT EXISTS idx_requests_phone_partial_v2 
                ON requests (substring(client_phone, 1, 10), created_at DESC)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_requests_date_only_v2 
                ON requests (DATE(created_at), city_id)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_month_year_v2 
                ON transactions (EXTRACT(YEAR FROM specified_date), EXTRACT(MONTH FROM specified_date), city_id)
                """
            ]
            
            for query in functional_index_queries:
                try:
                    await conn.execute(text(query))
                    logger.info("Создан функциональный индекс")
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Ошибка создания функционального индекса: {e}")
            
            # Обновляем статистику таблиц
            await conn.execute(text("ANALYZE requests"))
            await conn.execute(text("ANALYZE transactions"))
            await conn.execute(text("ANALYZE masters"))
            await conn.execute(text("ANALYZE employees"))
            await conn.execute(text("ANALYZE files"))
            
            logger.info("Индексы производительности v2 созданы успешно")
            
        except Exception as e:
            logger.error(f"Ошибка создания индексов: {e}")
            raise

async def optimize_database_settings():
    """Оптимизация настроек PostgreSQL для производительности"""
    logger.info("Оптимизация настроек базы данных...")
    
    async with engine.begin() as conn:
        try:
            # Настройки для оптимизации производительности
            optimization_queries = [
                # Увеличиваем shared_buffers для кеширования
                "ALTER SYSTEM SET shared_buffers = '256MB'",
                
                # Оптимизируем work_mem для сортировки
                "ALTER SYSTEM SET work_mem = '16MB'",
                
                # Увеличиваем effective_cache_size
                "ALTER SYSTEM SET effective_cache_size = '1GB'",
                
                # Оптимизируем random_page_cost для SSD
                "ALTER SYSTEM SET random_page_cost = 1.1",
                
                # Включаем автовакуум агрессивнее
                "ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1",
                "ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05",
                
                # Оптимизируем checkpoint
                "ALTER SYSTEM SET checkpoint_completion_target = 0.7",
                "ALTER SYSTEM SET wal_buffers = '16MB'",
                
                # Включаем статистику запросов
                "ALTER SYSTEM SET track_activity_query_size = 2048",
                "ALTER SYSTEM SET log_min_duration_statement = 1000",
            ]
            
            for query in optimization_queries:
                try:
                    await conn.execute(text(query))
                    logger.info(f"Применена настройка: {query}")
                except Exception as e:
                    logger.warning(f"Не удалось применить настройку {query}: {e}")
            
            # Перезагружаем конфигурацию
            await conn.execute(text("SELECT pg_reload_conf()"))
            
            logger.info("Настройки базы данных оптимизированы")
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации настроек: {e}")

async def create_materialized_views():
    """Создание материализованных представлений для быстрой аналитики"""
    logger.info("Создание материализованных представлений...")
    
    async with engine.begin() as conn:
        try:
            # Материализованное представление для статистики заявок
            await conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_requests_stats AS
                SELECT 
                    r.city_id,
                    c.name as city_name,
                    r.status,
                    rt.name as request_type,
                    DATE(r.created_at) as request_date,
                    COUNT(*) as requests_count,
                    AVG(r.result) as avg_result,
                    SUM(CASE WHEN r.result IS NOT NULL THEN 1 ELSE 0 END) as completed_count
                FROM requests r
                JOIN cities c ON r.city_id = c.id
                LEFT JOIN request_types rt ON r.request_type_id = rt.id
                GROUP BY r.city_id, c.name, r.status, rt.name, DATE(r.created_at)
            """))
            
            # Материализованное представление для финансовой статистики
            await conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_transactions_stats AS
                SELECT 
                    t.city_id,
                    c.name as city_name,
                    tt.name as transaction_type,
                    DATE(t.specified_date) as transaction_date,
                    COUNT(*) as transactions_count,
                    SUM(t.amount) as total_amount,
                    AVG(t.amount) as avg_amount,
                    MIN(t.amount) as min_amount,
                    MAX(t.amount) as max_amount
                FROM transactions t
                JOIN cities c ON t.city_id = c.id
                JOIN transaction_types tt ON t.transaction_type_id = tt.id
                GROUP BY t.city_id, c.name, tt.name, DATE(t.specified_date)
            """))
            
            # Создаем индексы для материализованных представлений
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_mv_requests_stats_city_date 
                ON mv_requests_stats (city_id, request_date DESC)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_mv_transactions_stats_city_date 
                ON mv_transactions_stats (city_id, transaction_date DESC)
            """))
            
            # Обновляем представления
            await conn.execute(text("REFRESH MATERIALIZED VIEW mv_requests_stats"))
            await conn.execute(text("REFRESH MATERIALIZED VIEW mv_transactions_stats"))
            
            logger.info("Материализованные представления созданы успешно")
            
        except Exception as e:
            logger.error(f"Ошибка создания материализованных представлений: {e}")

async def analyze_query_performance_v2():
    """Улучшенный анализ производительности запросов"""
    logger.info("Анализ производительности запросов v2...")
    
    async with engine.begin() as conn:
        try:
            # Включаем расширение pg_stat_statements если не включено
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
            except Exception as e:
                logger.warning(f"Не удалось включить pg_stat_statements: {e}")
            
            # Анализируем самые медленные запросы
            slow_queries = await conn.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    min_time,
                    max_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_time > 50
                ORDER BY mean_time DESC 
                LIMIT 10
            """))
            
            logger.info("Топ 10 самых медленных запросов:")
            for row in slow_queries.fetchall():
                logger.info(f"Запрос: {row[0][:100]}... | Вызовы: {row[1]} | Среднее время: {row[3]:.2f}мс | Hit%: {row[7]:.1f}%")
            
            # Анализируем использование индексов
            index_usage = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes 
                WHERE idx_scan > 0
                ORDER BY idx_scan DESC
                LIMIT 20
            """))
            
            logger.info("Топ 20 наиболее используемых индексов:")
            for row in index_usage.fetchall():
                logger.info(f"Таблица: {row[1]} | Индекс: {row[2]} | Сканирований: {row[3]} | Размер: {row[6]}")
            
            # Анализируем неиспользуемые индексы
            unused_indexes = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0
                AND schemaname = 'public'
                ORDER BY pg_relation_size(indexrelid) DESC
            """))
            
            logger.info("Неиспользуемые индексы:")
            for row in unused_indexes.fetchall():
                logger.info(f"Таблица: {row[1]} | Индекс: {row[2]} | Размер: {row[3]}")
            
            # Анализируем размеры таблиц
            table_sizes = await conn.execute(text("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size,
                    pg_size_pretty(pg_relation_size(tablename::regclass)) as table_size,
                    pg_size_pretty(pg_indexes_size(tablename::regclass)) as indexes_size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(tablename::regclass) DESC
            """))
            
            logger.info("Размеры таблиц:")
            for row in table_sizes.fetchall():
                logger.info(f"Таблица: {row[0]} | Общий размер: {row[1]} | Таблица: {row[2]} | Индексы: {row[3]}")
                
        except Exception as e:
            logger.warning(f"Анализ производительности не удался: {e}")

# Функция для полной оптимизации базы данных
async def full_database_optimization():
    """Полная оптимизация базы данных"""
    logger.info("Запуск полной оптимизации базы данных...")
    
    try:
        # 1. Создаем улучшенные индексы
        await create_performance_indexes_v2()
        
        # 2. Создаем материализованные представления
        await create_materialized_views()
        
        # 3. Оптимизируем настройки
        await optimize_database_settings()
        
        # 4. Анализируем производительность
        await analyze_query_performance_v2()
        
        logger.info("Полная оптимизация базы данных завершена успешно")
        
    except Exception as e:
        logger.error(f"Ошибка полной оптимизации: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(full_database_optimization()) 