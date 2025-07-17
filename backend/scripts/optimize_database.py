#!/usr/bin/env python3
"""
CLI скрипт для оптимизации базы данных
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Добавляем путь к app модулю
sys.path.append(str(Path(__file__).parent))

from app.db_optimization import (
    initialize_database_optimization,
    refresh_database_views,
    cleanup_database,
    get_database_optimization_report,
    db_optimizer
)
from app.database_indexes import (
    create_database_indexes,
    drop_database_indexes,
    analyze_query_performance
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Database optimization tool')
    parser.add_argument('command', choices=[
        'init', 'indexes', 'refresh', 'cleanup', 'report', 'analyze', 'vacuum', 'full'
    ], help='Command to execute')
    parser.add_argument('--days', type=int, default=365, help='Days to keep for cleanup')
    parser.add_argument('--drop', action='store_true', help='Drop indexes before creating')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'init':
            logger.info("Initializing database optimization...")
            success = await initialize_database_optimization()
            if success:
                logger.info("✅ Database optimization initialized successfully!")
            else:
                logger.error("❌ Database optimization failed!")
                sys.exit(1)
        
        elif args.command == 'indexes':
            if args.drop:
                logger.info("Dropping existing indexes...")
                await drop_database_indexes()
            
            logger.info("Creating database indexes...")
            await create_database_indexes()
            logger.info("✅ Database indexes created successfully!")
        
        elif args.command == 'refresh':
            logger.info("Refreshing materialized views...")
            await refresh_database_views()
            logger.info("✅ Materialized views refreshed successfully!")
        
        elif args.command == 'cleanup':
            logger.info(f"Cleaning up data older than {args.days} days...")
            await cleanup_database(args.days)
            logger.info("✅ Database cleanup completed!")
        
        elif args.command == 'report':
            logger.info("Generating optimization report...")
            report = await get_database_optimization_report()
            
            print("\n" + "="*60)
            print("DATABASE OPTIMIZATION REPORT")
            print("="*60)
            
            # Database statistics
            if 'database_statistics' in report:
                stats = report['database_statistics']
                print(f"\n📊 Database Statistics:")
                if 'table_sizes' in stats:
                    print("  Top 5 largest tables:")
                    for table in stats['table_sizes'][:5]:
                        print(f"    {table['table']}: {table['size']}")
                
                print(f"  Total connections: {stats.get('total_connections', 'N/A')}")
                print(f"  Active connections: {stats.get('active_connections', 'N/A')}")
            
            # Index usage
            if 'index_usage' in report:
                index_usage = report['index_usage']
                if 'top_indexes' in index_usage:
                    print(f"\n🔍 Top 5 Most Used Indexes:")
                    for idx in index_usage['top_indexes'][:5]:
                        print(f"    {idx['table']}.{idx['index']}: {idx['scans']} scans")
            
            # Slow queries
            if 'slow_queries' in report:
                slow_queries = report['slow_queries']
                if 'slow_queries' in slow_queries and slow_queries['slow_queries']:
                    print(f"\n🐌 Slow Queries (>100ms):")
                    for query in slow_queries['slow_queries'][:3]:
                        print(f"    {query['mean_time']:.2f}ms avg: {query['query']}")
                else:
                    print(f"\n✅ No slow queries detected!")
            
            print("\n" + "="*60)
        
        elif args.command == 'analyze':
            logger.info("Analyzing query performance...")
            await analyze_query_performance()
            logger.info("✅ Query performance analysis completed!")
        
        elif args.command == 'vacuum':
            logger.info("Running VACUUM ANALYZE on all tables...")
            await db_optimizer.vacuum_analyze_tables()
            logger.info("✅ VACUUM ANALYZE completed!")
        
        elif args.command == 'full':
            logger.info("Running full database optimization...")
            
            # 1. Initialize optimization
            await initialize_database_optimization()
            
            # 2. Create materialized views
            await db_optimizer.create_materialized_views()
            
            # 3. Optimize PostgreSQL settings
            await db_optimizer.optimize_postgresql_settings()
            
            # 4. VACUUM ANALYZE
            await db_optimizer.vacuum_analyze_tables()
            
            logger.info("✅ Full database optimization completed!")
        
    except Exception as e:
        logger.error(f"❌ Error executing command '{args.command}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 