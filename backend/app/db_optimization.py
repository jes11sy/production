"""
Скрипт для оптимизации базы данных
"""
import asyncio
import logging
from typing import Dict, Any
from sqlalchemy import text
from .core.database import engine
from .database_indexes import (
    create_database_indexes, 
    drop_database_indexes,
    analyze_query_performance,
    get_database_statistics
)

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Класс для оптимизации базы данных"""
    
    def __init__(self):
        self.engine = engine
    
    async def initialize_optimization(self):
        """Полная инициализация оптимизации БД"""
        logger.info("Starting database optimization...")
        
        try:
            # 1. Создаем индексы
            await create_database_indexes()
            
            # 2. Обновляем статистику PostgreSQL
            await self._update_table_statistics()
            
            # 3. Анализируем производительность
            await analyze_query_performance()
            
            # 4. Получаем статистику
            stats = await get_database_statistics()
            logger.info(f"Database statistics: {stats}")
            
            logger.info("Database optimization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False
    
    async def _update_table_statistics(self):
        """Обновление статистики таблиц PostgreSQL"""
        logger.info("Updating table statistics...")
        
        tables = [
            'requests', 'transactions', 'masters', 'employees', 
            'administrators', 'cities', 'request_types', 'directions',
            'advertising_campaigns', 'transaction_types', 'files', 'roles'
        ]
        
        async with self.engine.begin() as conn:
            for table in tables:
                try:
                    await conn.execute(text(f"ANALYZE {table}"))
                    logger.info(f"Updated statistics for table: {table}")
                except Exception as e:
                    logger.warning(f"Failed to update statistics for {table}: {e}")
    
    async def optimize_postgresql_settings(self):
        """Оптимизация настроек PostgreSQL"""
        logger.info("Optimizing PostgreSQL settings...")
        
        # Настройки для оптимизации производительности
        optimizations = [
            # Увеличиваем shared_buffers (если возможно)
            "SET shared_buffers = '256MB'",
            # Оптимизируем work_mem для сортировки
            "SET work_mem = '4MB'",
            # Увеличиваем maintenance_work_mem
            "SET maintenance_work_mem = '64MB'",
            # Оптимизируем настройки для SSD
            "SET random_page_cost = 1.1",
            # Включаем эффективное использование индексов
            "SET effective_cache_size = '1GB'",
            # Оптимизируем checkpoint настройки
            "SET checkpoint_completion_target = 0.9",
        ]
        
        async with self.engine.begin() as conn:
            for setting in optimizations:
                try:
                    await conn.execute(text(setting))
                    logger.info(f"Applied setting: {setting}")
                except Exception as e:
                    logger.warning(f"Failed to apply setting {setting}: {e}")
    
    async def create_materialized_views(self):
        """Создание материализованных представлений для отчетов"""
        logger.info("Creating materialized views...")
        
        views = [
            {
                "name": "mv_requests_summary",
                "sql": """
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_requests_summary AS
                SELECT 
                    r.city_id,
                    c.name as city_name,
                    r.status,
                    rt.name as request_type,
                    DATE(r.created_at) as request_date,
                    COUNT(*) as request_count,
                    COUNT(CASE WHEN r.master_id IS NOT NULL THEN 1 END) as assigned_count,
                    AVG(r.result) as avg_result,
                    SUM(r.expenses) as total_expenses
                FROM requests r
                JOIN cities c ON r.city_id = c.id
                JOIN request_types rt ON r.request_type_id = rt.id
                WHERE r.created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY r.city_id, c.name, r.status, rt.name, DATE(r.created_at)
                WITH DATA;
                
                CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_requests_summary 
                ON mv_requests_summary (city_id, status, request_type, request_date);
                """
            },
            {
                "name": "mv_financial_summary",
                "sql": """
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_financial_summary AS
                SELECT 
                    t.city_id,
                    c.name as city_name,
                    tt.name as transaction_type,
                    DATE(t.specified_date) as transaction_date,
                    COUNT(*) as transaction_count,
                    SUM(t.amount) as total_amount,
                    SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
                    SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) as expenses
                FROM transactions t
                JOIN cities c ON t.city_id = c.id
                JOIN transaction_types tt ON t.transaction_type_id = tt.id
                WHERE t.specified_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY t.city_id, c.name, tt.name, DATE(t.specified_date)
                WITH DATA;
                
                CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_financial_summary 
                ON mv_financial_summary (city_id, transaction_type, transaction_date);
                """
            }
        ]
        
        async with self.engine.begin() as conn:
            for view in views:
                try:
                    await conn.execute(text(view["sql"]))
                    logger.info(f"Created materialized view: {view['name']}")
                except Exception as e:
                    logger.warning(f"Failed to create view {view['name']}: {e}")
    
    async def refresh_materialized_views(self):
        """Обновление материализованных представлений"""
        logger.info("Refreshing materialized views...")
        
        views = ["mv_requests_summary", "mv_financial_summary"]
        
        async with self.engine.begin() as conn:
            for view in views:
                try:
                    await conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                    logger.info(f"Refreshed materialized view: {view}")
                except Exception as e:
                    logger.warning(f"Failed to refresh view {view}: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 365):
        """Очистка старых данных"""
        logger.info(f"Cleaning up data older than {days_to_keep} days...")
        
        cleanup_queries = [
            # Удаляем старые файлы без связанных записей
            f"""
            DELETE FROM files 
            WHERE uploaded_at < NOW() - INTERVAL '{days_to_keep} days'
            AND request_id IS NULL 
            AND transaction_id IS NULL
            """,
            # Архивируем старые заявки (можно настроить логику)
            f"""
            UPDATE requests 
            SET status = 'archived' 
            WHERE created_at < NOW() - INTERVAL '{days_to_keep} days'
            AND status IN ('done', 'cancelled')
            """,
        ]
        
        async with self.engine.begin() as conn:
            for query in cleanup_queries:
                try:
                    result = await conn.execute(text(query))
                    logger.info(f"Cleanup query affected {result.rowcount} rows")
                except Exception as e:
                    logger.warning(f"Cleanup query failed: {e}")
    
    async def vacuum_analyze_tables(self):
        """VACUUM и ANALYZE для всех таблиц"""
        logger.info("Running VACUUM ANALYZE on all tables...")
        
        tables = [
            'requests', 'transactions', 'masters', 'employees', 
            'administrators', 'cities', 'request_types', 'directions',
            'advertising_campaigns', 'transaction_types', 'files', 'roles'
        ]
        
        # VACUUM ANALYZE требует отдельного соединения
        async with self.engine.connect() as conn:
            for table in tables:
                try:
                    await conn.execute(text(f"VACUUM ANALYZE {table}"))
                    logger.info(f"VACUUM ANALYZE completed for table: {table}")
                except Exception as e:
                    logger.warning(f"VACUUM ANALYZE failed for {table}: {e}")
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Получение отчета об оптимизации"""
        logger.info("Generating optimization report...")
        
        report = {
            "timestamp": asyncio.get_event_loop().time(),
            "database_statistics": await get_database_statistics(),
            "index_usage": await self._get_index_usage(),
            "slow_queries": await self._get_slow_queries(),
            "connection_info": await self._get_connection_info()
        }
        
        return report
    
    async def _get_index_usage(self) -> Dict[str, Any]:
        """Статистика использования индексов"""
        async with self.engine.begin() as conn:
            try:
                result = await conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_scan DESC
                    LIMIT 20
                """))
                
                return {
                    "top_indexes": [
                        {
                            "schema": row[0],
                            "table": row[1],
                            "index": row[2],
                            "scans": row[3],
                            "tuples_read": row[4],
                            "tuples_fetched": row[5]
                        }
                        for row in result.fetchall()
                    ]
                }
            except Exception as e:
                logger.error(f"Failed to get index usage: {e}")
                return {"error": str(e)}
    
    async def _get_slow_queries(self) -> Dict[str, Any]:
        """Медленные запросы"""
        async with self.engine.begin() as conn:
            try:
                result = await conn.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    WHERE mean_time > 100
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """))
                
                return {
                    "slow_queries": [
                        {
                            "query": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                            "calls": row[1],
                            "total_time": row[2],
                            "mean_time": row[3],
                            "rows": row[4]
                        }
                        for row in result.fetchall()
                    ]
                }
            except Exception as e:
                logger.warning(f"pg_stat_statements not available: {e}")
                return {"slow_queries": []}
    
    async def _get_connection_info(self) -> Dict[str, Any]:
        """Информация о соединениях"""
        async with self.engine.begin() as conn:
            try:
                result = await conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_connections,
                        COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
                        COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """))
                
                row = result.fetchone()
                if row:
                    return {
                        "total_connections": row[0],
                        "active_connections": row[1],
                        "idle_connections": row[2]
                    }
                else:
                    return {
                        "total_connections": 0,
                        "active_connections": 0,
                        "idle_connections": 0
                    }
            except Exception as e:
                logger.error(f"Failed to get connection info: {e}")
                return {"error": str(e)}

# Создаем глобальный экземпляр
db_optimizer = DatabaseOptimizer()

# Функции для удобного использования
async def initialize_database_optimization():
    """Инициализация оптимизации базы данных"""
    return await db_optimizer.initialize_optimization()

async def refresh_database_views():
    """Обновление материализованных представлений"""
    await db_optimizer.refresh_materialized_views()

async def cleanup_database(days_to_keep: int = 365):
    """Очистка старых данных"""
    await db_optimizer.cleanup_old_data(days_to_keep)

async def get_database_optimization_report():
    """Получение отчета об оптимизации"""
    return await db_optimizer.get_optimization_report() 