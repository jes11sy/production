"""
API для мониторинга и управления оптимизацией базы данных
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from ..core.auth import require_admin
from ..core.models import Administrator
from ..db_optimization import (
    get_database_optimization_report,
    refresh_database_views,
    cleanup_database,
    db_optimizer
)
from ..database_indexes import (
    create_database_indexes,
    analyze_query_performance,
    get_database_statistics
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["database"])

@router.get("/statistics")
async def get_database_stats(
    current_user: Administrator = Depends(require_admin)
):
    """Получение статистики базы данных"""
    try:
        stats = await get_database_statistics()
        return {
            "status": "success",
            "data": stats,
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get database statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database statistics: {str(e)}")

@router.get("/optimization-report")
async def get_optimization_report(
    current_user: Administrator = Depends(require_admin)
):
    """Получение полного отчета об оптимизации"""
    try:
        report = await get_database_optimization_report()
        return {
            "status": "success",
            "data": report,
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to generate optimization report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate optimization report: {str(e)}")

@router.post("/create-indexes")
async def create_indexes(
    current_user: Administrator = Depends(require_admin)
):
    """Создание индексов для оптимизации"""
    try:
        await create_database_indexes()
        return {
            "status": "success",
            "message": "Database indexes created successfully",
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create indexes: {str(e)}")

@router.post("/refresh-views")
async def refresh_views(
    current_user: Administrator = Depends(require_admin)
):
    """Обновление материализованных представлений"""
    try:
        await refresh_database_views()
        return {
            "status": "success",
            "message": "Materialized views refreshed successfully",
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to refresh views: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh views: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_data(
    days_to_keep: int = Query(365, ge=30, le=3650, description="Days to keep data"),
    current_user: Administrator = Depends(require_admin)
):
    """Очистка старых данных"""
    try:
        await cleanup_database(days_to_keep)
        return {
            "status": "success",
            "message": f"Database cleanup completed, kept data for {days_to_keep} days",
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup database: {str(e)}")

@router.post("/analyze-performance")
async def analyze_performance(
    current_user: Administrator = Depends(require_admin)
):
    """Анализ производительности запросов"""
    try:
        await analyze_query_performance()
        return {
            "status": "success",
            "message": "Query performance analysis completed",
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to analyze performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze performance: {str(e)}")

@router.post("/vacuum-analyze")
async def vacuum_analyze_tables(
    current_user: Administrator = Depends(require_admin)
):
    """VACUUM ANALYZE всех таблиц"""
    try:
        await db_optimizer.vacuum_analyze_tables()
        return {
            "status": "success",
            "message": "VACUUM ANALYZE completed for all tables",
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to vacuum analyze: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to vacuum analyze: {str(e)}")

@router.get("/connection-pool-status")
async def get_connection_pool_status(
    current_user: Administrator = Depends(require_admin)
):
    """Статус пула соединений"""
    try:
        from ..core.database import engine
        
        pool = engine.pool
        try:
            pool_status = {
                "size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "invalid": getattr(pool, 'invalid', lambda: 0)(),
                "utilization": getattr(pool, 'checkedout', lambda: 0)() / max(getattr(pool, 'size', lambda: 1)(), 1) * 100
            }
        except Exception:
            pool_status = {
                "size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
                "invalid": 0,
                "utilization": 0.0
            }
        
        return {
            "status": "success",
            "data": pool_status,
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get connection pool status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection pool status: {str(e)}")

@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=50, description="Number of slow queries to return"),
    min_time: float = Query(100.0, ge=0.0, description="Minimum query time in milliseconds"),
    current_user: Administrator = Depends(require_admin)
):
    """Получение медленных запросов"""
    try:
        from ..core.database import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text(f"""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_time > {min_time}
                ORDER BY mean_time DESC 
                LIMIT {limit}
            """))
            
            slow_queries = [
                {
                    "query": row[0][:500] + "..." if len(row[0]) > 500 else row[0],
                    "calls": row[1],
                    "total_time": float(row[2]),
                    "mean_time": float(row[3]),
                    "rows": row[4],
                    "hit_percent": float(row[5] or 0)
                }
                for row in result.fetchall()
            ]
            
            return {
                "status": "success",
                "data": {
                    "slow_queries": slow_queries,
                    "total_found": len(slow_queries),
                    "min_time_threshold": min_time
                },
                "timestamp": "2025-01-15T15:00:00Z"
            }
    except Exception as e:
        logger.warning(f"pg_stat_statements not available or failed: {e}")
        return {
            "status": "warning",
            "data": {
                "slow_queries": [],
                "total_found": 0,
                "message": "pg_stat_statements extension not available"
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }

@router.get("/index-usage")
async def get_index_usage(
    limit: int = Query(20, ge=1, le=100, description="Number of indexes to return"),
    current_user: Administrator = Depends(require_admin)
):
    """Статистика использования индексов"""
    try:
        from ..core.database import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text(f"""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelname::regclass)) as index_size
                FROM pg_stat_user_indexes 
                JOIN pg_indexes ON pg_indexes.indexname = pg_stat_user_indexes.indexname
                ORDER BY idx_scan DESC
                LIMIT {limit}
            """))
            
            index_usage = [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                    "tuples_read": row[4],
                    "tuples_fetched": row[5],
                    "size": row[6]
                }
                for row in result.fetchall()
            ]
            
            return {
                "status": "success",
                "data": {
                    "index_usage": index_usage,
                    "total_found": len(index_usage)
                },
                "timestamp": "2025-01-15T15:00:00Z"
            }
    except Exception as e:
        logger.error(f"Failed to get index usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get index usage: {str(e)}")

@router.get("/table-sizes")
async def get_table_sizes(
    current_user: Administrator = Depends(require_admin)
):
    """Размеры таблиц"""
    try:
        from ..core.database import engine
        from sqlalchemy import text
        
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY total_bytes DESC
            """))
            
            table_sizes = [
                {
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "index_size": row[4],
                    "total_bytes": row[5]
                }
                for row in result.fetchall()
            ]
            
            return {
                "status": "success",
                "data": {
                    "table_sizes": table_sizes,
                    "total_tables": len(table_sizes)
                },
                "timestamp": "2025-01-15T15:00:00Z"
            }
    except Exception as e:
        logger.error(f"Failed to get table sizes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get table sizes: {str(e)}")

@router.post("/optimize-full")
async def optimize_full(
    current_user: Administrator = Depends(require_admin)
):
    """Полная оптимизация базы данных"""
    try:
        # 1. Создаем индексы
        await create_database_indexes()
        
        # 2. Создаем материализованные представления
        await db_optimizer.create_materialized_views()
        
        # 3. Обновляем статистику
        await db_optimizer._update_table_statistics()
        
        # 4. VACUUM ANALYZE
        await db_optimizer.vacuum_analyze_tables()
        
        return {
            "status": "success",
            "message": "Full database optimization completed successfully",
            "actions_performed": [
                "Created/updated indexes",
                "Created materialized views",
                "Updated table statistics",
                "Performed VACUUM ANALYZE"
            ],
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to perform full optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform full optimization: {str(e)}") 