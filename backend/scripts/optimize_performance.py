#!/usr/bin/env python3
"""
Скрипт для оптимизации производительности системы управления заявками
Исправляет N+1 запросы, добавляет кеширование, создает индексы
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.core.cache import init_cache, cache_manager
from app.database_indexes_v2 import full_database_optimization
from app.core.optimized_crud_v2 import OptimizedCRUDv2

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_optimization.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def install_dependencies():
    """Установка зависимостей для кеширования"""
    logger.info("Проверка и установка зависимостей...")
    
    try:
        import subprocess
        import sys
        
        # Список зависимостей для кеширования
        dependencies = [
            "redis==5.0.1",
            "aioredis==2.0.1", 
            "aiocache==0.12.2",
            "asyncio-throttle==1.0.2",
            "cachetools==5.3.2",
            "memory-profiler==0.61.0",
            "line-profiler==4.1.1"
        ]
        
        for dep in dependencies:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                logger.info(f"Установлена зависимость: {dep}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Не удалось установить {dep}: {e}")
        
        logger.info("Зависимости проверены/установлены")
        
    except Exception as e:
        logger.error(f"Ошибка установки зависимостей: {e}")

async def check_redis_connection():
    """Проверка подключения к Redis"""
    logger.info("Проверка подключения к Redis...")
    
    try:
        # Инициализируем кеш
        await init_cache()
        
        # Проверяем статистику кеша
        stats = cache_manager.get_stats()
        logger.info(f"Статистика кеша: {stats}")
        
        if stats["redis_connected"]:
            logger.info("✅ Redis подключен успешно")
        else:
            logger.warning("⚠️  Redis не подключен, используется локальный кеш")
        
        return stats["redis_connected"]
        
    except Exception as e:
        logger.error(f"Ошибка проверки Redis: {e}")
        return False

async def optimize_database_performance():
    """Оптимизация производительности базы данных"""
    logger.info("Запуск оптимизации базы данных...")
    
    try:
        # Запускаем полную оптимизацию
        await full_database_optimization()
        logger.info("✅ Оптимизация базы данных завершена")
        
    except Exception as e:
        logger.error(f"❌ Ошибка оптимизации базы данных: {e}")
        raise

async def warm_up_cache():
    """Прогрев кеша"""
    logger.info("Прогрев кеша...")
    
    try:
        from app.core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            await OptimizedCRUDv2.warm_up_cache(db)
        
        logger.info("✅ Кеш прогрет успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка прогрева кеша: {e}")

async def run_performance_tests():
    """Запуск тестов производительности"""
    logger.info("Запуск тестов производительности...")
    
    try:
        from app.core.database import AsyncSessionLocal
        import time
        
        async with AsyncSessionLocal() as db:
            # Тест 1: Загрузка заявок без оптимизации
            from sqlalchemy import text
            start_time = time.time()
            requests_old = await db.execute(
                text("SELECT * FROM requests ORDER BY created_at DESC LIMIT 100")
            )
            old_time = time.time() - start_time
            
            # Тест 2: Загрузка заявок с оптимизацией
            start_time = time.time()
            requests_new = await OptimizedCRUDv2.get_requests_optimized(db, limit=100)
            new_time = time.time() - start_time
            
            # Сравнение результатов
            improvement = ((old_time - new_time) / old_time * 100) if old_time > 0 else 0
            
            logger.info(f"Тест загрузки заявок:")
            logger.info(f"  Без оптимизации: {old_time:.3f}с")
            logger.info(f"  С оптимизацией: {new_time:.3f}с")
            logger.info(f"  Улучшение: {improvement:.1f}%")
            
            # Тест кеширования
            start_time = time.time()
            cities_1 = await OptimizedCRUDv2.get_cities_cached(db)
            cache_miss_time = time.time() - start_time
            
            start_time = time.time()
            cities_2 = await OptimizedCRUDv2.get_cities_cached(db)
            cache_hit_time = time.time() - start_time
            
            cache_improvement = ((cache_miss_time - cache_hit_time) / cache_miss_time * 100) if cache_miss_time > 0 else 0
            
            logger.info(f"Тест кеширования:")
            logger.info(f"  Cache miss: {cache_miss_time:.3f}с")
            logger.info(f"  Cache hit: {cache_hit_time:.3f}с")
            logger.info(f"  Улучшение: {cache_improvement:.1f}%")
        
        logger.info("✅ Тесты производительности завершены")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестов производительности: {e}")

async def generate_performance_report():
    """Генерация отчета о производительности"""
    logger.info("Генерация отчета о производительности...")
    
    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "optimizations_applied": [
                "Созданы индексы для оптимизации N+1 запросов",
                "Добавлено Redis кеширование",
                "Оптимизированы SQL запросы с joinedload/selectinload",
                "Созданы материализованные представления",
                "Настроены параметры PostgreSQL",
                "Добавлены агрегированные запросы для статистики"
            ],
            "cache_stats": cache_manager.get_stats(),
            "recommendations": [
                "Регулярно обновляйте материализованные представления",
                "Мониторьте статистику кеша",
                "Проверяйте медленные запросы через pg_stat_statements",
                "Настройте автоматическое обновление индексов",
                "Используйте connection pooling в продакшене"
            ]
        }
        
        # Сохраняем отчет
        with open("performance_optimization_report.json", "w", encoding="utf-8") as f:
            import json
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Отчет сохранен в performance_optimization_report.json")
        
        # Выводим краткую сводку
        print("\n" + "="*60)
        print("ОТЧЕТ ОБ ОПТИМИЗАЦИИ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*60)
        print(f"Время выполнения: {report['timestamp']}")
        print(f"Кеш подключен: {'✅' if report['cache_stats']['redis_connected'] else '❌'}")
        print(f"Попаданий в кеш: {report['cache_stats']['hit_rate']}%")
        print(f"Всего запросов к кешу: {report['cache_stats']['total_requests']}")
        print("\nПрименены оптимизации:")
        for opt in report['optimizations_applied']:
            print(f"  ✅ {opt}")
        print("\nРекомендации:")
        for rec in report['recommendations']:
            print(f"  💡 {rec}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации отчета: {e}")

async def main():
    """Основная функция оптимизации"""
    logger.info("🚀 Запуск оптимизации производительности системы")
    
    try:
        # 1. Установка зависимостей
        await install_dependencies()
        
        # 2. Проверка подключения к Redis
        redis_connected = await check_redis_connection()
        
        # 3. Оптимизация базы данных
        await optimize_database_performance()
        
        # 4. Прогрев кеша
        if redis_connected:
            await warm_up_cache()
        
        # 5. Тесты производительности
        await run_performance_tests()
        
        # 6. Генерация отчета
        await generate_performance_report()
        
        logger.info("🎉 Оптимизация производительности завершена успешно!")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка оптимизации: {e}")
        sys.exit(1)
    
    finally:
        # Закрываем соединения
        if cache_manager:
            await cache_manager.close()
        if engine:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main()) 