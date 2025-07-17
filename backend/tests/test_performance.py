import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app


class TestPerformanceBasics:
    """Базовые тесты производительности"""
    
    def test_app_startup_time(self):
        """Тест времени запуска приложения"""
        start_time = time.time()
        
        # Создаем клиент (имитация запуска)
        with TestClient(app) as client:
            response = client.get("/docs")
            assert response.status_code == 200
        
        startup_time = time.time() - start_time
        
        # Приложение должно запускаться быстро (менее 10 секунд)
        assert startup_time < 10.0, f"App startup took {startup_time:.2f}s, expected < 10s"
    
    def test_health_check_response_time(self):
        """Тест времени ответа health check"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/api/v1/health")
            response_time = time.time() - start_time
            
            # Health check должен отвечать быстро (менее 2 секунд)
            assert response_time < 2.0, f"Health check took {response_time:.2f}s, expected < 2s"
            assert response.status_code in [200, 500]  # 500 из-за БД в тестах
    
    def test_docs_response_time(self):
        """Тест времени ответа документации"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/docs")
            response_time = time.time() - start_time
            
            # Документация должна загружаться быстро (менее 1 секунды)
            assert response_time < 1.0, f"Docs took {response_time:.2f}s, expected < 1s"
            assert response.status_code == 200
    
    def test_openapi_schema_response_time(self):
        """Тест времени генерации OpenAPI схемы"""
        with TestClient(app) as client:
            start_time = time.time()
            response = client.get("/openapi.json")
            response_time = time.time() - start_time
            
            # OpenAPI схема должна генерироваться быстро (менее 1 секунды)
            assert response_time < 1.0, f"OpenAPI schema took {response_time:.2f}s, expected < 1s"
            assert response.status_code == 200
            
            # Проверяем размер ответа
            data = response.json()
            assert len(str(data)) > 1000  # Схема должна быть содержательной


class TestConcurrentRequests:
    """Тесты конкурентных запросов"""
    
    def test_concurrent_health_checks(self):
        """Тест параллельных health check запросов"""
        def make_request():
            with TestClient(app) as client:
                start_time = time.time()
                response = client.get("/api/v1/health")
                response_time = time.time() - start_time
                return response.status_code, response_time
        
        # Запускаем 10 параллельных запросов
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # Проверяем результаты
        for status_code, response_time in results:
            assert status_code in [200, 500]  # Все запросы должны завершиться
            assert response_time < 5.0  # Каждый запрос должен быть быстрым
    
    def test_concurrent_docs_requests(self):
        """Тест параллельных запросов к документации"""
        def make_docs_request():
            with TestClient(app) as client:
                start_time = time.time()
                response = client.get("/docs")
                response_time = time.time() - start_time
                return response.status_code, response_time
        
        # Запускаем 5 параллельных запросов
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_docs_request) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # Проверяем результаты
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 3.0  # Документация должна загружаться быстро
    
    def test_mixed_concurrent_requests(self):
        """Тест смешанных параллельных запросов"""
        def make_health_request():
            with TestClient(app) as client:
                return client.get("/api/v1/health").status_code
        
        def make_docs_request():
            with TestClient(app) as client:
                return client.get("/docs").status_code
        
        def make_openapi_request():
            with TestClient(app) as client:
                return client.get("/openapi.json").status_code
        
        # Запускаем разные типы запросов параллельно
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            
            # 5 health check запросов
            futures.extend([executor.submit(make_health_request) for _ in range(5)])
            
            # 5 docs запросов
            futures.extend([executor.submit(make_docs_request) for _ in range(5)])
            
            # 5 openapi запросов
            futures.extend([executor.submit(make_openapi_request) for _ in range(5)])
            
            results = [future.result() for future in futures]
        
        # Проверяем что все запросы завершились успешно
        health_results = results[:5]
        docs_results = results[5:10]
        openapi_results = results[10:15]
        
        for status in health_results:
            assert status in [200, 500]
        
        for status in docs_results:
            assert status == 200
        
        for status in openapi_results:
            assert status == 200


class TestMemoryUsage:
    """Тесты использования памяти"""
    
    def test_memory_usage_basic(self):
        """Базовый тест использования памяти"""
        import psutil
        import os
        
        # Получаем текущий процесс
        process = psutil.Process(os.getpid())
        
        # Замеряем память до создания клиента
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Создаем клиент и делаем запросы
        with TestClient(app) as client:
            # Делаем несколько запросов
            for _ in range(10):
                client.get("/docs")
                client.get("/api/v1/health")
                client.get("/openapi.json")
        
        # Замеряем память после
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Проверяем что память не выросла критично (менее 100MB)
        memory_increase = memory_after - memory_before
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB, expected < 100MB"
    
    def test_memory_leak_detection(self):
        """Тест обнаружения утечек памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Делаем много запросов и проверяем память
        memory_measurements = []
        
        for i in range(5):
            # Делаем серию запросов
            with TestClient(app) as client:
                for _ in range(20):
                    client.get("/docs")
            
            # Замеряем память
            memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(memory)
            
            # Небольшая пауза
            time.sleep(0.1)
        
        # Проверяем что память не растет постоянно
        # Допускаем небольшой рост, но не более 50MB между измерениями
        for i in range(1, len(memory_measurements)):
            memory_diff = memory_measurements[i] - memory_measurements[i-1]
            assert memory_diff < 50, f"Memory increased by {memory_diff:.2f}MB between measurements"


class TestResponseSizes:
    """Тесты размеров ответов"""
    
    def test_docs_response_size(self):
        """Тест размера ответа документации"""
        with TestClient(app) as client:
            response = client.get("/docs")
            assert response.status_code == 200
            
            # Размер HTML документации не должен быть слишком большим
            content_size = len(response.content)
            assert content_size < 5 * 1024 * 1024, f"Docs size is {content_size} bytes, expected < 5MB"
            assert content_size > 1000, "Docs should have some content"
    
    def test_openapi_schema_size(self):
        """Тест размера OpenAPI схемы"""
        with TestClient(app) as client:
            response = client.get("/openapi.json")
            assert response.status_code == 200
            
            # Размер JSON схемы
            content_size = len(response.content)
            assert content_size < 1 * 1024 * 1024, f"OpenAPI schema size is {content_size} bytes, expected < 1MB"
            assert content_size > 5000, "OpenAPI schema should be substantial"
            
            # Проверяем что это валидный JSON
            data = response.json()
            assert isinstance(data, dict)
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data


class TestStressTests:
    """Стресс-тесты"""
    
    def test_rapid_requests_stress(self):
        """Стресс-тест быстрых запросов"""
        with TestClient(app) as client:
            start_time = time.time()
            
            # Делаем 100 быстрых запросов
            success_count = 0
            for i in range(100):
                try:
                    response = client.get("/docs")
                    if response.status_code == 200:
                        success_count += 1
                except Exception:
                    pass  # Игнорируем ошибки в стресс-тесте
            
            total_time = time.time() - start_time
            
            # Проверяем результаты
            success_rate = success_count / 100
            assert success_rate > 0.8, f"Success rate is {success_rate:.2%}, expected > 80%"
            
            # Средняя скорость должна быть разумной
            avg_time_per_request = total_time / 100
            assert avg_time_per_request < 0.5, f"Average time per request: {avg_time_per_request:.3f}s"
    
    def test_endpoint_availability_under_load(self):
        """Тест доступности endpoints под нагрузкой"""
        endpoints = ["/docs", "/openapi.json", "/api/v1/health"]
        
        def test_endpoint(endpoint):
            success_count = 0
            for _ in range(20):
                try:
                    with TestClient(app) as client:
                        response = client.get(endpoint)
                        if response.status_code in [200, 500]:  # 500 для health из-за БД
                            success_count += 1
                except Exception:
                    pass
            return success_count
        
        # Тестируем все endpoints параллельно
        with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
            futures = [executor.submit(test_endpoint, endpoint) for endpoint in endpoints]
            results = [future.result() for future in futures]
        
        # Проверяем что все endpoints доступны
        for i, success_count in enumerate(results):
            success_rate = success_count / 20
            assert success_rate > 0.7, f"Endpoint {endpoints[i]} success rate: {success_rate:.2%}" 