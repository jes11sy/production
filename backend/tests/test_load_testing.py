"""
Load Testing тесты для проверки производительности системы под нагрузкой
Используется для определения пределов производительности и стабильности
"""
import pytest
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta
import random
import string


class LoadTestConfig:
    """Конфигурация для нагрузочных тестов"""
    BASE_URL = "http://localhost:8000"
    CONCURRENT_USERS = 50
    REQUESTS_PER_USER = 20
    RAMP_UP_TIME = 10  # секунд
    TEST_DURATION = 60  # секунд
    ACCEPTABLE_RESPONSE_TIME = 2.0  # секунд
    ACCEPTABLE_ERROR_RATE = 0.05  # 5%


class LoadTestMetrics:
    """Метрики для нагрузочного тестирования"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.status_codes: Dict[int, int] = {}
    
    def add_response(self, response_time: float, status_code: int):
        """Добавить результат запроса"""
        self.response_times.append(response_time)
        
        if status_code >= 400:
            self.error_count += 1
        else:
            self.success_count += 1
        
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику тестирования"""
        total_requests = len(self.response_times)
        
        if not self.response_times:
            return {"error": "No requests completed"}
        
        return {
            "total_requests": total_requests,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "error_rate": self.error_count / total_requests if total_requests > 0 else 0,
            "average_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "95th_percentile": self._percentile(self.response_times, 95),
            "99th_percentile": self._percentile(self.response_times, 99),
            "requests_per_second": total_requests / (self.end_time - self.start_time) if self.end_time and self.start_time else 0,
            "status_codes": self.status_codes,
            "test_duration": self.end_time - self.start_time if self.end_time and self.start_time else 0
        }
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Вычислить percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class LoadTestRunner:
    """Основной класс для выполнения нагрузочных тестов"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics = LoadTestMetrics()
        self.session = None
    
    async def setup_session(self):
        """Настройка HTTP сессии"""
        connector = aiohttp.TCPConnector(
            limit=self.config.CONCURRENT_USERS * 2,
            limit_per_host=self.config.CONCURRENT_USERS * 2
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def cleanup_session(self):
        """Очистка HTTP сессии"""
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнить HTTP запрос с измерением времени"""
        start_time = time.time()
        
        try:
            async with self.session.request(
                method, 
                f"{self.config.BASE_URL}{endpoint}",
                **kwargs
            ) as response:
                response_time = time.time() - start_time
                
                # Читаем содержимое ответа
                try:
                    content = await response.text()
                except:
                    content = ""
                
                self.metrics.add_response(response_time, response.status)
                
                return {
                    "status_code": response.status,
                    "response_time": response_time,
                    "content": content,
                    "headers": dict(response.headers)
                }
        
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.add_response(response_time, 500)
            
            return {
                "status_code": 500,
                "response_time": response_time,
                "error": str(e)
            }
    
    async def simulate_user_session(self, user_id: int) -> List[Dict[str, Any]]:
        """Симуляция пользовательской сессии"""
        results = []
        
        # Случайная задержка для имитации ramp-up
        await asyncio.sleep(random.uniform(0, self.config.RAMP_UP_TIME))
        
        for request_num in range(self.config.REQUESTS_PER_USER):
            # Случайный выбор endpoint для тестирования
            endpoint = random.choice([
                "/api/v1/health",
                "/api/v1/requests/",
                "/api/v1/transactions/",
                "/api/v1/users/",
                "/api/v1/metrics/business"
            ])
            
            result = await self.make_request("GET", endpoint)
            results.append(result)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        return results
    
    async def run_load_test(self) -> Dict[str, Any]:
        """Запустить нагрузочный тест"""
        await self.setup_session()
        
        try:
            self.metrics.start_time = time.time()
            
            # Создаем задачи для всех пользователей
            tasks = [
                self.simulate_user_session(user_id) 
                for user_id in range(self.config.CONCURRENT_USERS)
            ]
            
            # Выполняем все задачи параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            self.metrics.end_time = time.time()
            
            return self.metrics.get_statistics()
        
        finally:
            await self.cleanup_session()


class TestLoadTesting:
    """Тесты нагрузочного тестирования"""
    
    @pytest.mark.asyncio
    async def test_basic_load_test(self):
        """Базовый нагрузочный тест"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 10
        config.REQUESTS_PER_USER = 5
        
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        # Проверяем основные метрики
        assert stats["total_requests"] > 0
        assert stats["error_rate"] < config.ACCEPTABLE_ERROR_RATE
        assert stats["average_response_time"] < config.ACCEPTABLE_RESPONSE_TIME
        
        print(f"Load Test Results: {json.dumps(stats, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_stress_test(self):
        """Стресс-тест с высокой нагрузкой"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 100
        config.REQUESTS_PER_USER = 10
        
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        # В стресс-тесте допускается более высокий error rate
        assert stats["total_requests"] > 0
        assert stats["error_rate"] < 0.2  # 20%
        
        print(f"Stress Test Results: {json.dumps(stats, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_spike_test(self):
        """Тест пиковой нагрузки"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 200
        config.REQUESTS_PER_USER = 3
        config.RAMP_UP_TIME = 1  # Быстрый ramp-up
        
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        # Проверяем, что система выдерживает пиковую нагрузку
        assert stats["total_requests"] > 0
        print(f"Spike Test Results: {json.dumps(stats, indent=2)}")
    
    @pytest.mark.asyncio
    async def test_endurance_test(self):
        """Тест на выносливость (длительная нагрузка)"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 20
        config.REQUESTS_PER_USER = 50
        config.TEST_DURATION = 120  # 2 минуты
        
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        # Проверяем стабильность при длительной нагрузке
        assert stats["total_requests"] > 0
        assert stats["error_rate"] < 0.1  # 10%
        
        print(f"Endurance Test Results: {json.dumps(stats, indent=2)}")


class TestSpecificEndpointLoad:
    """Тесты нагрузки на конкретные endpoints"""
    
    @pytest.mark.asyncio
    async def test_requests_endpoint_load(self):
        """Нагрузочный тест для endpoint заявок"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 30
        config.REQUESTS_PER_USER = 10
        
        runner = LoadTestRunner(config)
        await runner.setup_session()
        
        try:
            runner.metrics.start_time = time.time()
            
            # Тестируем только endpoint заявок
            tasks = []
            for _ in range(config.CONCURRENT_USERS):
                for _ in range(config.REQUESTS_PER_USER):
                    tasks.append(runner.make_request("GET", "/api/v1/requests/"))
            
            await asyncio.gather(*tasks)
            runner.metrics.end_time = time.time()
            
            stats = runner.metrics.get_statistics()
            
            # Проверяем производительность endpoint заявок
            assert stats["average_response_time"] < 1.0  # Менее 1 секунды
            assert stats["error_rate"] < 0.05  # Менее 5%
            
            print(f"Requests Endpoint Load Test: {json.dumps(stats, indent=2)}")
        
        finally:
            await runner.cleanup_session()
    
    @pytest.mark.asyncio
    async def test_database_intensive_load(self):
        """Тест нагрузки на БД-интенсивные операции"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 25
        config.REQUESTS_PER_USER = 8
        
        runner = LoadTestRunner(config)
        await runner.setup_session()
        
        try:
            runner.metrics.start_time = time.time()
            
            # Тестируем БД-интенсивные endpoints
            db_endpoints = [
                "/api/v1/requests/statistics",
                "/api/v1/transactions/financial-report",
                "/api/v1/users/masters/performance",
                "/api/v1/metrics/business"
            ]
            
            tasks = []
            for _ in range(config.CONCURRENT_USERS):
                for _ in range(config.REQUESTS_PER_USER):
                    endpoint = random.choice(db_endpoints)
                    tasks.append(runner.make_request("GET", endpoint))
            
            await asyncio.gather(*tasks)
            runner.metrics.end_time = time.time()
            
            stats = runner.metrics.get_statistics()
            
            # БД операции могут быть медленнее
            assert stats["average_response_time"] < 3.0  # Менее 3 секунд
            assert stats["error_rate"] < 0.1  # Менее 10%
            
            print(f"Database Intensive Load Test: {json.dumps(stats, indent=2)}")
        
        finally:
            await runner.cleanup_session()


class TestMemoryAndResourceLoad:
    """Тесты нагрузки на память и ресурсы"""
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Тест на обнаружение утечек памяти"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 50
        config.REQUESTS_PER_USER = 20
        
        # Выполняем несколько циклов тестирования
        for cycle in range(3):
            runner = LoadTestRunner(config)
            await runner.run_load_test()
            
            # Принудительная сборка мусора
            import gc
            gc.collect()
            
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            print(f"Cycle {cycle + 1}: Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
            
            # Проверяем, что увеличение памяти не критично
            assert memory_increase < 100 * 1024 * 1024  # Менее 100MB
    
    @pytest.mark.asyncio
    async def test_concurrent_connections_limit(self):
        """Тест лимита одновременных соединений"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 500  # Очень высокая нагрузка
        config.REQUESTS_PER_USER = 1
        
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        # Проверяем, что система не падает при большом количестве соединений
        assert stats["total_requests"] > 0
        
        # Высокий error rate допустим при таком количестве соединений
        print(f"Connection Limit Test: {json.dumps(stats, indent=2)}")


class TestRealisticUserScenarios:
    """Тесты реалистичных пользовательских сценариев"""
    
    @pytest.mark.asyncio
    async def test_realistic_user_behavior(self):
        """Тест реалистичного поведения пользователей"""
        config = LoadTestConfig()
        config.CONCURRENT_USERS = 20
        
        runner = LoadTestRunner(config)
        await runner.setup_session()
        
        try:
            runner.metrics.start_time = time.time()
            
            # Симулируем реалистичное поведение пользователей
            tasks = [
                self._simulate_callcenter_user(runner),
                self._simulate_manager_user(runner),
                self._simulate_master_user(runner),
                self._simulate_admin_user(runner)
            ]
            
            # Запускаем несколько экземпляров каждого типа пользователя
            all_tasks = []
            for _ in range(5):  # 5 пользователей каждого типа
                all_tasks.extend(tasks)
            
            await asyncio.gather(*all_tasks)
            runner.metrics.end_time = time.time()
            
            stats = runner.metrics.get_statistics()
            
            # Проверяем реалистичную производительность
            assert stats["average_response_time"] < 2.0
            assert stats["error_rate"] < 0.1
            
            print(f"Realistic User Behavior Test: {json.dumps(stats, indent=2)}")
        
        finally:
            await runner.cleanup_session()
    
    async def _simulate_callcenter_user(self, runner: LoadTestRunner):
        """Симуляция пользователя колл-центра"""
        # Типичный workflow колл-центра
        await runner.make_request("GET", "/api/v1/requests/")
        await asyncio.sleep(2)
        
        await runner.make_request("POST", "/api/v1/requests/", json={
            "client_name": "Test Client",
            "client_phone": "+79123456789",
            "description": "Test request"
        })
        await asyncio.sleep(1)
        
        await runner.make_request("GET", "/api/v1/requests/statistics")
        await asyncio.sleep(3)
    
    async def _simulate_manager_user(self, runner: LoadTestRunner):
        """Симуляция пользователя-менеджера"""
        # Типичный workflow менеджера
        await runner.make_request("GET", "/api/v1/users/masters/performance")
        await asyncio.sleep(2)
        
        await runner.make_request("GET", "/api/v1/transactions/financial-report")
        await asyncio.sleep(3)
        
        await runner.make_request("GET", "/api/v1/requests/statistics")
        await asyncio.sleep(1)
    
    async def _simulate_master_user(self, runner: LoadTestRunner):
        """Симуляция пользователя-мастера"""
        # Типичный workflow мастера
        await runner.make_request("GET", "/api/v1/requests/?assigned_to_me=true")
        await asyncio.sleep(1)
        
        await runner.make_request("PATCH", "/api/v1/requests/1", json={
            "status": "in_progress"
        })
        await asyncio.sleep(2)
        
        await runner.make_request("GET", "/api/v1/requests/1")
        await asyncio.sleep(1)
    
    async def _simulate_admin_user(self, runner: LoadTestRunner):
        """Симуляция пользователя-администратора"""
        # Типичный workflow администратора
        await runner.make_request("GET", "/api/v1/health")
        await asyncio.sleep(1)
        
        await runner.make_request("GET", "/api/v1/metrics/performance")
        await asyncio.sleep(2)
        
        await runner.make_request("GET", "/api/v1/database/status")
        await asyncio.sleep(1)


# Утилиты для генерации тестовых данных
def generate_random_request_data() -> Dict[str, Any]:
    """Генерация случайных данных для заявки"""
    return {
        "client_name": f"Client {''.join(random.choices(string.ascii_letters, k=10))}",
        "client_phone": f"+7912345{random.randint(1000, 9999)}",
        "client_email": f"client{random.randint(1, 1000)}@example.com",
        "address": f"Address {random.randint(1, 100)}",
        "description": f"Description {''.join(random.choices(string.ascii_letters, k=50))}",
        "city_id": random.randint(1, 5),
        "request_type_id": random.randint(1, 3),
        "priority": random.choice(["low", "medium", "high"])
    }


def generate_random_transaction_data() -> Dict[str, Any]:
    """Генерация случайных данных для транзакции"""
    return {
        "amount": round(random.uniform(100, 10000), 2),
        "transaction_type_id": random.randint(1, 3),
        "description": f"Transaction {''.join(random.choices(string.ascii_letters, k=30))}",
        "city_id": random.randint(1, 5),
        "status": random.choice(["pending", "completed", "failed"])
    }


if __name__ == "__main__":
    # Запуск основного нагрузочного теста
    async def main():
        config = LoadTestConfig()
        runner = LoadTestRunner(config)
        stats = await runner.run_load_test()
        
        print("=== LOAD TEST RESULTS ===")
        print(json.dumps(stats, indent=2))
        
        # Проверка соответствия требованиям
        if stats["error_rate"] > config.ACCEPTABLE_ERROR_RATE:
            print(f"❌ ERROR RATE TOO HIGH: {stats['error_rate']:.2%}")
        else:
            print(f"✅ ERROR RATE OK: {stats['error_rate']:.2%}")
        
        if stats["average_response_time"] > config.ACCEPTABLE_RESPONSE_TIME:
            print(f"❌ RESPONSE TIME TOO HIGH: {stats['average_response_time']:.2f}s")
        else:
            print(f"✅ RESPONSE TIME OK: {stats['average_response_time']:.2f}s")
    
    asyncio.run(main()) 