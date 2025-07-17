#!/usr/bin/env python3
"""
Интеграция с Prometheus для мониторинга системы управления заявками
Создает метрики и экспортирует их для Prometheus
"""
import asyncio
import logging
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, 
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess
)
from prometheus_client.exposition import start_http_server
import aiohttp
from aiohttp import web
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """Класс для управления метриками Prometheus"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # HTTP метрики
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Бизнес метрики
        self.requests_total = Counter(
            'requests_total',
            'Total number of requests',
            ['status', 'city', 'type'],
            registry=self.registry
        )
        
        self.transactions_total = Counter(
            'transactions_total',
            'Total number of transactions',
            ['type', 'city'],
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            ['role'],
            registry=self.registry
        )
        
        # Системные метрики
        self.database_connections = Gauge(
            'database_connections',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.redis_connections = Gauge(
            'redis_connections',
            'Number of active Redis connections',
            registry=self.registry
        )
        
        self.memory_usage_bytes = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )
        
        self.cpu_usage_percent = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        # Производительность
        self.response_time_seconds = Histogram(
            'response_time_seconds',
            'API response time in seconds',
            ['endpoint'],
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            registry=self.registry
        )
        
        # Ошибки
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['type', 'component'],
            registry=self.registry
        )
        
        # Кеш метрики
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Безопасность
        self.login_attempts_total = Counter(
            'login_attempts_total',
            'Total login attempts',
            ['status', 'ip'],
            registry=self.registry
        )
        
        self.security_violations_total = Counter(
            'security_violations_total',
            'Total security violations',
            ['type'],
            registry=self.registry
        )
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Записать метрику HTTP запроса"""
        self.http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_request_created(self, status: str, city: str, request_type: str):
        """Записать создание заявки"""
        self.requests_total.labels(status=status, city=city, type=request_type).inc()
    
    def record_transaction_created(self, transaction_type: str, city: str):
        """Записать создание транзакции"""
        self.transactions_total.labels(type=transaction_type, city=city).inc()
    
    def set_active_users(self, role: str, count: int):
        """Установить количество активных пользователей"""
        self.active_users.labels(role=role).set(count)
    
    def set_database_connections(self, count: int):
        """Установить количество соединений с БД"""
        self.database_connections.set(count)
    
    def set_redis_connections(self, count: int):
        """Установить количество соединений с Redis"""
        self.redis_connections.set(count)
    
    def record_error(self, error_type: str, component: str):
        """Записать ошибку"""
        self.errors_total.labels(type=error_type, component=component).inc()
    
    def record_cache_hit(self, cache_type: str):
        """Записать попадание в кеш"""
        self.cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Записать промах кеша"""
        self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_login_attempt(self, status: str, ip: str):
        """Записать попытку входа"""
        self.login_attempts_total.labels(status=status, ip=ip).inc()
    
    def record_security_violation(self, violation_type: str):
        """Записать нарушение безопасности"""
        self.security_violations_total.labels(type=violation_type).inc()


class SystemMetricsCollector:
    """Сборщик системных метрик"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
    
    async def collect_system_metrics(self):
        """Собрать системные метрики"""
        try:
            # Использование памяти
            memory = psutil.virtual_memory()
            self.metrics.memory_usage_bytes.set(memory.used)
            
            # Использование CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.cpu_usage_percent.set(cpu_percent)
            
            logger.info(f"System metrics collected: CPU {cpu_percent}%, Memory {memory.used / 1024 / 1024:.1f}MB")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            self.metrics.record_error("system_metrics", "collector")


class DatabaseMetricsCollector:
    """Сборщик метрик базы данных"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
    
    async def collect_database_metrics(self):
        """Собрать метрики базы данных"""
        try:
            # Здесь должна быть логика получения метрик из БД
            # Пока используем моковые данные
            connection_count = 10  # Моковое значение
            self.metrics.set_database_connections(connection_count)
            
            logger.info(f"Database metrics collected: {connection_count} connections")
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            self.metrics.record_error("database_metrics", "collector")


class RedisMetricsCollector:
    """Сборщик метрик Redis"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
    
    async def collect_redis_metrics(self):
        """Собрать метрики Redis"""
        try:
            # Здесь должна быть логика получения метрик из Redis
            # Пока используем моковые данные
            connection_count = 5  # Моковое значение
            self.metrics.set_redis_connections(connection_count)
            
            logger.info(f"Redis metrics collected: {connection_count} connections")
            
        except Exception as e:
            logger.error(f"Error collecting Redis metrics: {e}")
            self.metrics.record_error("redis_metrics", "collector")


class PrometheusExporter:
    """Экспортер метрик для Prometheus"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.metrics = PrometheusMetrics()
        self.system_collector = SystemMetricsCollector(self.metrics)
        self.db_collector = DatabaseMetricsCollector(self.metrics)
        self.redis_collector = RedisMetricsCollector(self.metrics)
    
    async def start_metrics_server(self):
        """Запустить сервер метрик"""
        app = web.Application()
        
        # Endpoint для метрик Prometheus
        app.router.add_get('/metrics', self.metrics_handler)
        
        # Endpoint для проверки здоровья
        app.router.add_get('/health', self.health_handler)
        
        # Endpoint для статистики
        app.router.add_get('/stats', self.stats_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        
        logger.info(f"Prometheus metrics server started on port {self.port}")
        logger.info(f"Metrics available at: http://localhost:{self.port}/metrics")
        logger.info(f"Health check at: http://localhost:{self.port}/health")
        logger.info(f"Stats at: http://localhost:{self.port}/stats")
        
        return runner
    
    async def metrics_handler(self, request):
        """Обработчик для метрик Prometheus"""
        try:
            metrics_data = generate_latest(self.metrics.registry)
            return web.Response(
                body=metrics_data,
                content_type=CONTENT_TYPE_LATEST
            )
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return web.Response(status=500, text="Internal Server Error")
    
    async def health_handler(self, request):
        """Обработчик для проверки здоровья"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        return web.Response(
            body=json.dumps(health_data),
            content_type='application/json'
        )
    
    async def stats_handler(self, request):
        """Обработчик для статистики"""
        stats_data = {
            "metrics_count": len(list(self.metrics.registry.collect())),
            "uptime": "running",
            "last_update": datetime.now().isoformat()
        }
        return web.Response(
            body=json.dumps(stats_data),
            content_type='application/json'
        )
    
    async def collect_metrics_loop(self):
        """Цикл сбора метрик"""
        while True:
            try:
                # Собираем системные метрики
                await self.system_collector.collect_system_metrics()
                
                # Собираем метрики БД
                await self.db_collector.collect_database_metrics()
                
                # Собираем метрики Redis
                await self.redis_collector.collect_redis_metrics()
                
                # Ждем 30 секунд перед следующим сбором
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)  # Ждем дольше при ошибке


async def main():
    """Основная функция"""
    logger.info("Starting Prometheus integration...")
    
    try:
        # Создаем экспортер
        exporter = PrometheusExporter(port=8001)
        
        # Запускаем сервер метрик
        runner = await exporter.start_metrics_server()
        
        # Запускаем цикл сбора метрик
        metrics_task = asyncio.create_task(exporter.collect_metrics_loop())
        
        # Ждем завершения
        await metrics_task
        
    except KeyboardInterrupt:
        logger.info("Shutting down Prometheus integration...")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 