"""
Комплексные тесты производительности и нагрузочные тесты
"""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from decimal import Decimal
from datetime import datetime, date
import psutil
import os
from unittest.mock import patch, AsyncMock
import threading
from contextlib import contextmanager

from app.core.models import (
    City, Role, Master, Employee, Request, Transaction, 
    RequestType, TransactionType
)
from app.core.crud import (
    create_request, get_requests, get_request, update_request,
    create_transaction, get_transactions
)
from app.monitoring.performance import performance_monitor
from app.core.cache import cache_manager


@contextmanager
def measure_time():
    """Context manager для измерения времени выполнения"""
    start = time.time()
    yield lambda: time.time() - start
    

@contextmanager
def measure_memory():
    """Context manager для измерения использования памяти"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    yield lambda: process.memory_info().rss / 1024 / 1024 - start_memory


@pytest.mark.asyncio
class TestAPIPerformance:
    """Тесты производительности API"""
    
    async def test_health_check_performance(self, client: TestClient):
        """Тест производительности health check"""
        times = []
        
        # Делаем несколько запросов для получения средних значений
        for _ in range(10):
            with measure_time() as get_time:
                response = client.get("/health")
                assert response.status_code == 200
            times.append(get_time())
        
        # Проверяем производительность
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Health check должен быть очень быстрым
        assert avg_time < 0.1  # Средняя < 100ms
        assert max_time < 0.5  # Максимальная < 500ms
        
        print(f"Health check - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    async def test_authentication_performance(self, client: TestClient, test_employee):
        """Тест производительности аутентификации"""
        login_data = {
            "login": test_employee.login,
            "password": "test_password"
        }
        
        times = []
        
        # Тестируем несколько попыток входа
        for _ in range(5):
            with measure_time() as get_time:
                response = client.post("/api/v1/auth/login", json=login_data)
                assert response.status_code == 200
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Аутентификация должна быть быстрой
        assert avg_time < 0.5  # Средняя < 500ms
        assert max_time < 1.0  # Максимальная < 1s
        
        print(f"Authentication - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    async def test_requests_list_performance(self, authenticated_client: TestClient):
        """Тест производительности получения списка заявок"""
        times = []
        
        for _ in range(5):
            with measure_time() as get_time:
                response = authenticated_client.get("/api/v1/requests/")
                assert response.status_code == 200
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Получение списка должно быть быстрым
        assert avg_time < 1.0  # Средняя < 1s
        assert max_time < 2.0  # Максимальная < 2s
        
        print(f"Requests list - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    async def test_request_creation_performance(
        self, 
        authenticated_client: TestClient,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности создания заявок"""
        request_data = {
            "city_id": test_city.id,
            "request_type_id": test_request_type.id,
            "master_id": test_master.id,
            "client_phone": "+79991234567",
            "client_name": "Тестовый клиент",
            "address": "Тестовый адрес",
            "problem": "Тестовая проблема",
            "result": 1500.00,
            "expenses": 300.00,
            "net_amount": 1200.00,
            "master_handover": 800.00
        }
        
        times = []
        
        for i in range(5):
            # Изменяем телефон для каждой заявки
            request_data["client_phone"] = f"+7999123456{i}"
            
            with measure_time() as get_time:
                response = authenticated_client.post("/api/v1/requests/", json=request_data)
                assert response.status_code == 201
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Создание заявки должно быть быстрым
        assert avg_time < 0.5  # Средняя < 500ms
        assert max_time < 1.0  # Максимальная < 1s
        
        print(f"Request creation - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Тесты производительности базы данных"""
    
    async def test_simple_query_performance(self, db_session: AsyncSession):
        """Тест производительности простых запросов"""
        times = []
        
        for _ in range(10):
            with measure_time() as get_time:
                result = await db_session.execute(select(City))
                cities = result.scalars().all()
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Простые запросы должны быть очень быстрыми
        assert avg_time < 0.05  # Средняя < 50ms
        assert max_time < 0.1   # Максимальная < 100ms
        
        print(f"Simple query - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    async def test_complex_query_performance(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности сложных запросов"""
        # Создаем тестовые данные
        requests = []
        for i in range(50):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:02d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}",
                result=Decimal(f"{1000 + i * 10}.00")
            )
            requests.append(request)
        
        db_session.add_all(requests)
        await db_session.commit()
        
        # Тестируем сложный запрос с соединениями
        times = []
        
        for _ in range(5):
            with measure_time() as get_time:
                result = await db_session.execute(
                    select(Request, City, RequestType, Master)
                    .join(City, Request.city_id == City.id)
                    .join(RequestType, Request.request_type_id == RequestType.id)
                    .join(Master, Request.master_id == Master.id)
                    .where(Request.city_id == test_city.id)
                    .limit(20)
                )
                joined_data = result.all()
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Сложные запросы должны быть разумно быстрыми
        assert avg_time < 0.2  # Средняя < 200ms
        assert max_time < 0.5  # Максимальная < 500ms
        
        print(f"Complex query - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")
    
    async def test_bulk_insert_performance(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности массовой вставки"""
        # Создаем много записей
        requests = []
        for i in range(100):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:03d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}"
            )
            requests.append(request)
        
        # Измеряем время вставки
        with measure_time() as get_time:
            db_session.add_all(requests)
            await db_session.commit()
        
        insert_time = get_time()
        
        # Массовая вставка должна быть эффективной
        assert insert_time < 2.0  # Меньше 2 секунд для 100 записей
        
        # Проверяем что все записи созданы
        result = await db_session.execute(
            select(func.count(Request.id)).where(Request.city_id == test_city.id)
        )
        count = result.scalar()
        
        assert count >= 100
        
        print(f"Bulk insert (100 records) - Time: {insert_time:.3f}s")
    
    async def test_aggregation_performance(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности агрегационных запросов"""
        # Создаем тестовые данные
        requests = []
        for i in range(100):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:03d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}",
                result=Decimal(f"{1000 + i * 10}.00")
            )
            requests.append(request)
        
        db_session.add_all(requests)
        await db_session.commit()
        
        # Тестируем агрегационные запросы
        times = []
        
        for _ in range(5):
            with measure_time() as get_time:
                result = await db_session.execute(
                    select(
                        func.count(Request.id),
                        func.sum(Request.result),
                        func.avg(Request.result),
                        func.max(Request.result),
                        func.min(Request.result)
                    ).where(Request.city_id == test_city.id)
                )
                stats = result.first()
            times.append(get_time())
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Агрегационные запросы должны быть быстрыми
        assert avg_time < 0.1  # Средняя < 100ms
        assert max_time < 0.2  # Максимальная < 200ms
        
        print(f"Aggregation query - Average: {avg_time:.3f}s, Max: {max_time:.3f}s")


@pytest.mark.asyncio
class TestConcurrencyPerformance:
    """Тесты производительности при конкурентном доступе"""
    
    async def test_concurrent_requests(self, client: TestClient):
        """Тест конкурентных запросов"""
        def make_request():
            response = client.get("/health")
            return response.status_code == 200
        
        # Запускаем 20 конкурентных запросов
        with ThreadPoolExecutor(max_workers=20) as executor:
            with measure_time() as get_time:
                futures = [executor.submit(make_request) for _ in range(20)]
                results = [future.result() for future in as_completed(futures)]
        
        total_time = get_time()
        success_count = sum(results)
        
        # Проверяем результаты
        assert success_count >= 18  # Минимум 90% успешных запросов
        assert total_time < 5.0     # Все запросы должны завершиться за 5 секунд
        
        print(f"Concurrent requests (20) - Success: {success_count}/20, Time: {total_time:.3f}s")
    
    async def test_concurrent_authentication(self, client: TestClient, test_employee):
        """Тест конкурентной аутентификации"""
        login_data = {
            "login": test_employee.login,
            "password": "test_password"
        }
        
        def authenticate():
            response = client.post("/api/v1/auth/login", json=login_data)
            return response.status_code == 200
        
        # Запускаем 10 конкурентных аутентификаций
        with ThreadPoolExecutor(max_workers=10) as executor:
            with measure_time() as get_time:
                futures = [executor.submit(authenticate) for _ in range(10)]
                results = [future.result() for future in as_completed(futures)]
        
        total_time = get_time()
        success_count = sum(results)
        
        # Проверяем результаты
        assert success_count >= 9   # Минимум 90% успешных аутентификаций
        assert total_time < 10.0    # Все аутентификации должны завершиться за 10 секунд
        
        print(f"Concurrent auth (10) - Success: {success_count}/10, Time: {total_time:.3f}s")
    
    async def test_concurrent_database_operations(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест конкурентных операций с базой данных"""
        async def create_request_async(session_id):
            # Создаем новую сессию для каждого потока
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                request = Request(
                    city_id=test_city.id,
                    request_type_id=test_request_type.id,
                    master_id=test_master.id,
                    client_phone=f"+7999123456{session_id:02d}",
                    client_name=f"Клиент {session_id}",
                    address=f"Адрес {session_id}",
                    problem=f"Проблема {session_id}"
                )
                session.add(request)
                await session.commit()
                return True
        
        # Запускаем 10 конкурентных операций
        with measure_time() as get_time:
            tasks = [create_request_async(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = get_time()
        success_count = sum(1 for r in results if r is True)
        
        # Проверяем результаты
        assert success_count >= 8   # Минимум 80% успешных операций
        assert total_time < 5.0     # Все операции должны завершиться за 5 секунд
        
        print(f"Concurrent DB ops (10) - Success: {success_count}/10, Time: {total_time:.3f}s")


@pytest.mark.asyncio
class TestMemoryPerformance:
    """Тесты производительности памяти"""
    
    async def test_memory_usage_normal_operations(self, authenticated_client: TestClient):
        """Тест использования памяти при нормальных операциях"""
        with measure_memory() as get_memory_diff:
            # Выполняем серию операций
            for i in range(50):
                response = authenticated_client.get("/api/v1/requests/")
                assert response.status_code == 200
        
        memory_diff = get_memory_diff()
        
        # Использование памяти должно быть разумным
        assert memory_diff < 50  # Меньше 50MB для 50 запросов
        
        print(f"Memory usage (50 requests) - Diff: {memory_diff:.2f}MB")
    
    async def test_memory_leak_detection(self, authenticated_client: TestClient):
        """Тест обнаружения утечек памяти"""
        memory_measurements = []
        
        for iteration in range(5):
            # Делаем много запросов
            for i in range(100):
                response = authenticated_client.get("/health")
                assert response.status_code == 200
            
            # Измеряем память
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_measurements.append(memory_mb)
            
            # Небольшая пауза между итерациями
            await asyncio.sleep(0.1)
        
        # Проверяем что память не растет постоянно
        for i in range(1, len(memory_measurements)):
            memory_growth = memory_measurements[i] - memory_measurements[i-1]
            assert memory_growth < 20  # Рост не более 20MB между итерациями
        
        print(f"Memory leak test - Measurements: {memory_measurements}")
    
    async def test_large_response_memory(self, authenticated_client: TestClient):
        """Тест использования памяти при больших ответах"""
        with measure_memory() as get_memory_diff:
            # Запрашиваем большой список (если есть данные)
            response = authenticated_client.get("/api/v1/requests/?limit=1000")
            assert response.status_code == 200
            
            data = response.json()
            # Обрабатываем данные
            processed_data = [item for item in data if item]
        
        memory_diff = get_memory_diff()
        
        # Использование памяти должно быть пропорциональным размеру данных
        assert memory_diff < 100  # Меньше 100MB для больших ответов
        
        print(f"Large response memory - Diff: {memory_diff:.2f}MB")


@pytest.mark.asyncio
class TestCachePerformance:
    """Тесты производительности кеширования"""
    
    @patch('app.core.cache.cache_manager')
    async def test_cache_hit_performance(self, mock_cache, authenticated_client: TestClient):
        """Тест производительности попаданий в кеш"""
        # Настраиваем мок кеша
        mock_cache.get.return_value = '{"cached": "data"}'
        mock_cache.set.return_value = True
        
        times_with_cache = []
        
        # Тестируем запросы с кешем
        for _ in range(10):
            with measure_time() as get_time:
                response = authenticated_client.get("/api/v1/requests/")
                assert response.status_code == 200
            times_with_cache.append(get_time())
        
        avg_time_with_cache = sum(times_with_cache) / len(times_with_cache)
        
        # Запросы с кешем должны быть быстрыми
        assert avg_time_with_cache < 0.1  # Средняя < 100ms
        
        print(f"Cache hit performance - Average: {avg_time_with_cache:.3f}s")
    
    @patch('app.core.cache.cache_manager')
    async def test_cache_miss_performance(self, mock_cache, authenticated_client: TestClient):
        """Тест производительности промахов кеша"""
        # Настраиваем мок кеша (промахи)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        times_without_cache = []
        
        # Тестируем запросы без кеша
        for _ in range(5):
            with measure_time() as get_time:
                response = authenticated_client.get("/api/v1/requests/")
                assert response.status_code == 200
            times_without_cache.append(get_time())
        
        avg_time_without_cache = sum(times_without_cache) / len(times_without_cache)
        
        # Запросы без кеша должны быть разумно быстрыми
        assert avg_time_without_cache < 1.0  # Средняя < 1s
        
        print(f"Cache miss performance - Average: {avg_time_without_cache:.3f}s")


@pytest.mark.asyncio
class TestLoadTesting:
    """Нагрузочные тесты"""
    
    async def test_sustained_load(self, client: TestClient):
        """Тест устойчивой нагрузки"""
        def make_sustained_requests():
            success_count = 0
            error_count = 0
            
            for i in range(100):
                try:
                    response = client.get("/health")
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1
                
                # Небольшая задержка между запросами
                time.sleep(0.01)
            
            return success_count, error_count
        
        # Запускаем 5 потоков с устойчивой нагрузкой
        with ThreadPoolExecutor(max_workers=5) as executor:
            with measure_time() as get_time:
                futures = [executor.submit(make_sustained_requests) for _ in range(5)]
                results = [future.result() for future in as_completed(futures)]
        
        total_time = get_time()
        total_success = sum(success for success, _ in results)
        total_errors = sum(errors for _, errors in results)
        
        # Проверяем результаты
        success_rate = total_success / (total_success + total_errors) * 100
        
        assert success_rate >= 95  # Минимум 95% успешных запросов
        assert total_time < 60     # Все запросы должны завершиться за 60 секунд
        
        print(f"Sustained load test - Success rate: {success_rate:.1f}%, Time: {total_time:.1f}s")
    
    async def test_spike_load(self, client: TestClient):
        """Тест пиковой нагрузки"""
        def make_spike_requests():
            success_count = 0
            
            # Быстрые запросы без задержек
            for i in range(50):
                try:
                    response = client.get("/health")
                    if response.status_code == 200:
                        success_count += 1
                except Exception:
                    pass
            
            return success_count
        
        # Запускаем 10 потоков одновременно (пиковая нагрузка)
        with ThreadPoolExecutor(max_workers=10) as executor:
            with measure_time() as get_time:
                futures = [executor.submit(make_spike_requests) for _ in range(10)]
                results = [future.result() for future in as_completed(futures)]
        
        total_time = get_time()
        total_success = sum(results)
        
        # Проверяем результаты
        success_rate = total_success / 500 * 100  # 10 потоков * 50 запросов
        
        assert success_rate >= 80  # Минимум 80% успешных запросов при пиковой нагрузке
        assert total_time < 30     # Все запросы должны завершиться за 30 секунд
        
        print(f"Spike load test - Success rate: {success_rate:.1f}%, Time: {total_time:.1f}s")


@pytest.mark.asyncio
class TestPerformanceRegression:
    """Тесты регрессии производительности"""
    
    async def test_performance_baseline(self, authenticated_client: TestClient):
        """Тест базовой производительности для отслеживания регрессий"""
        # Набор стандартных операций
        operations = [
            ("health_check", lambda: authenticated_client.get("/health")),
            ("requests_list", lambda: authenticated_client.get("/api/v1/requests/")),
            ("cities_list", lambda: authenticated_client.get("/api/v1/requests/cities")),
            ("types_list", lambda: authenticated_client.get("/api/v1/requests/request-types")),
            ("masters_list", lambda: authenticated_client.get("/api/v1/requests/masters")),
        ]
        
        performance_results = {}
        
        for operation_name, operation_func in operations:
            times = []
            
            # Выполняем операцию несколько раз
            for _ in range(5):
                with measure_time() as get_time:
                    response = operation_func()
                    assert response.status_code == 200
                times.append(get_time())
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            performance_results[operation_name] = {
                "average": avg_time,
                "maximum": max_time
            }
        
        # Проверяем что производительность в пределах нормы
        performance_limits = {
            "health_check": {"average": 0.1, "maximum": 0.2},
            "requests_list": {"average": 1.0, "maximum": 2.0},
            "cities_list": {"average": 0.5, "maximum": 1.0},
            "types_list": {"average": 0.5, "maximum": 1.0},
            "masters_list": {"average": 0.5, "maximum": 1.0},
        }
        
        for operation_name, results in performance_results.items():
            limits = performance_limits[operation_name]
            
            assert results["average"] < limits["average"], \
                f"{operation_name} average time {results['average']:.3f}s exceeds limit {limits['average']:.3f}s"
            assert results["maximum"] < limits["maximum"], \
                f"{operation_name} maximum time {results['maximum']:.3f}s exceeds limit {limits['maximum']:.3f}s"
        
        # Выводим результаты для мониторинга
        print("Performance baseline results:")
        for operation_name, results in performance_results.items():
            print(f"  {operation_name}: avg={results['average']:.3f}s, max={results['maximum']:.3f}s")
    
    async def test_database_performance_baseline(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест базовой производительности базы данных"""
        # Создаем тестовые данные
        requests = []
        for i in range(100):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:03d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}"
            )
            requests.append(request)
        
        # Тест вставки
        with measure_time() as get_time:
            db_session.add_all(requests)
            await db_session.commit()
        insert_time = get_time()
        
        # Тест простого запроса
        with measure_time() as get_time:
            result = await db_session.execute(
                select(Request).where(Request.city_id == test_city.id).limit(10)
            )
            simple_results = result.scalars().all()
        simple_query_time = get_time()
        
        # Тест сложного запроса
        with measure_time() as get_time:
            result = await db_session.execute(
                select(Request, City, Master)
                .join(City, Request.city_id == City.id)
                .join(Master, Request.master_id == Master.id)
                .where(Request.city_id == test_city.id)
                .limit(10)
            )
            complex_results = result.all()
        complex_query_time = get_time()
        
        # Проверяем производительность
        assert insert_time < 2.0        # Вставка 100 записей < 2s
        assert simple_query_time < 0.1  # Простой запрос < 100ms
        assert complex_query_time < 0.2 # Сложный запрос < 200ms
        
        print(f"Database baseline - Insert: {insert_time:.3f}s, Simple: {simple_query_time:.3f}s, Complex: {complex_query_time:.3f}s") 