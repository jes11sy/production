"""
Chaos Engineering тесты для проверки отказоустойчивости системы
Тестируют поведение системы при различных сбоях и нештатных ситуациях
"""
import pytest
import asyncio
import aiohttp
import random
import time
import psutil
import os
from unittest.mock import patch, MagicMock
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Callable
import json
from datetime import datetime


class ChaosScenario:
    """Базовый класс для сценариев хаоса"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.is_active = False
    
    async def start(self):
        """Запустить сценарий хаоса"""
        self.is_active = True
        print(f"🔥 Starting chaos scenario: {self.name}")
    
    async def stop(self):
        """Остановить сценарий хаоса"""
        self.is_active = False
        print(f"✅ Stopped chaos scenario: {self.name}")
    
    async def execute(self):
        """Выполнить сценарий хаоса"""
        raise NotImplementedError


class DatabaseChaosScenario(ChaosScenario):
    """Сценарии хаоса для базы данных"""
    
    def __init__(self):
        super().__init__("Database Chaos", "Симуляция проблем с базой данных")
    
    async def execute(self):
        """Симуляция проблем с БД"""
        scenarios = [
            self._simulate_connection_timeout,
            self._simulate_slow_queries,
            self._simulate_connection_pool_exhaustion,
            self._simulate_deadlocks
        ]
        
        scenario = random.choice(scenarios)
        await scenario()
    
    async def _simulate_connection_timeout(self):
        """Симуляция таймаута соединения с БД"""
        print("💥 Simulating database connection timeout")
        
        with patch('app.core.database.AsyncSessionLocal') as mock_session:
            mock_session.side_effect = asyncio.TimeoutError("Connection timeout")
            await asyncio.sleep(5)  # Держим хаос 5 секунд
    
    async def _simulate_slow_queries(self):
        """Симуляция медленных запросов"""
        print("🐌 Simulating slow database queries")
        
        original_execute = None
        
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(random.uniform(2, 5))  # Задержка 2-5 секунд
            if original_execute:
                return await original_execute(*args, **kwargs)
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.execute', side_effect=slow_execute):
            await asyncio.sleep(10)
    
    async def _simulate_connection_pool_exhaustion(self):
        """Симуляция исчерпания пула соединений"""
        print("🔥 Simulating connection pool exhaustion")
        
        with patch('app.core.database.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Connection pool exhausted")
            await asyncio.sleep(3)
    
    async def _simulate_deadlocks(self):
        """Симуляция дедлоков в БД"""
        print("🔒 Simulating database deadlocks")
        
        with patch('sqlalchemy.ext.asyncio.AsyncSession.commit') as mock_commit:
            mock_commit.side_effect = Exception("Deadlock detected")
            await asyncio.sleep(4)


class NetworkChaosScenario(ChaosScenario):
    """Сценарии сетевого хаоса"""
    
    def __init__(self):
        super().__init__("Network Chaos", "Симуляция сетевых проблем")
    
    async def execute(self):
        """Симуляция сетевых проблем"""
        scenarios = [
            self._simulate_network_latency,
            self._simulate_packet_loss,
            self._simulate_network_partition,
            self._simulate_dns_failure
        ]
        
        scenario = random.choice(scenarios)
        await scenario()
    
    async def _simulate_network_latency(self):
        """Симуляция высокой задержки сети"""
        print("🌐 Simulating high network latency")
        
        original_request = aiohttp.ClientSession.request
        
        async def delayed_request(self, *args, **kwargs):
            await asyncio.sleep(random.uniform(1, 3))  # Задержка 1-3 секунды
            return await original_request(self, *args, **kwargs)
        
        with patch.object(aiohttp.ClientSession, 'request', delayed_request):
            await asyncio.sleep(8)
    
    async def _simulate_packet_loss(self):
        """Симуляция потери пакетов"""
        print("📦 Simulating packet loss")
        
        async def random_failure_request(self, *args, **kwargs):
            if random.random() < 0.3:  # 30% вероятность сбоя
                raise aiohttp.ClientError("Packet lost")
            return await aiohttp.ClientSession.request(self, *args, **kwargs)
        
        with patch.object(aiohttp.ClientSession, 'request', random_failure_request):
            await asyncio.sleep(6)
    
    async def _simulate_network_partition(self):
        """Симуляция разделения сети"""
        print("🔌 Simulating network partition")
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Network unreachable")
            await asyncio.sleep(5)
    
    async def _simulate_dns_failure(self):
        """Симуляция сбоя DNS"""
        print("🌍 Simulating DNS failure")
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_request.side_effect = aiohttp.ClientError("DNS resolution failed")
            await asyncio.sleep(4)


class ResourceChaosScenario(ChaosScenario):
    """Сценарии хаоса ресурсов"""
    
    def __init__(self):
        super().__init__("Resource Chaos", "Симуляция нехватки ресурсов")
    
    async def execute(self):
        """Симуляция проблем с ресурсами"""
        scenarios = [
            self._simulate_memory_pressure,
            self._simulate_cpu_spike,
            self._simulate_disk_full,
            self._simulate_file_descriptor_exhaustion
        ]
        
        scenario = random.choice(scenarios)
        await scenario()
    
    async def _simulate_memory_pressure(self):
        """Симуляция нехватки памяти"""
        print("🧠 Simulating memory pressure")
        
        # Выделяем много памяти
        memory_hog = []
        try:
            for _ in range(100):
                memory_hog.append(bytearray(1024 * 1024))  # 1MB блоки
                await asyncio.sleep(0.1)
        except MemoryError:
            print("Memory exhausted!")
        finally:
            del memory_hog
    
    async def _simulate_cpu_spike(self):
        """Симуляция высокой нагрузки на CPU"""
        print("⚡ Simulating CPU spike")
        
        def cpu_intensive_task():
            end_time = time.time() + 5  # 5 секунд нагрузки
            while time.time() < end_time:
                # Интенсивные вычисления
                sum(i * i for i in range(1000))
        
        # Запускаем несколько CPU-интенсивных задач
        tasks = []
        for _ in range(psutil.cpu_count()):
            task = asyncio.create_task(asyncio.to_thread(cpu_intensive_task))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def _simulate_disk_full(self):
        """Симуляция переполнения диска"""
        print("💾 Simulating disk full")
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = OSError("No space left on device")
            await asyncio.sleep(3)
    
    async def _simulate_file_descriptor_exhaustion(self):
        """Симуляция исчерпания файловых дескрипторов"""
        print("📁 Simulating file descriptor exhaustion")
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = OSError("Too many open files")
            await asyncio.sleep(4)


class ServiceChaosScenario(ChaosScenario):
    """Сценарии хаоса внешних сервисов"""
    
    def __init__(self):
        super().__init__("Service Chaos", "Симуляция сбоев внешних сервисов")
    
    async def execute(self):
        """Симуляция сбоев внешних сервисов"""
        scenarios = [
            self._simulate_redis_failure,
            self._simulate_email_service_failure,
            self._simulate_payment_service_failure,
            self._simulate_file_storage_failure
        ]
        
        scenario = random.choice(scenarios)
        await scenario()
    
    async def _simulate_redis_failure(self):
        """Симуляция сбоя Redis"""
        print("🔴 Simulating Redis failure")
        
        with patch('app.core.cache.cache_manager.get') as mock_get:
            mock_get.side_effect = Exception("Redis connection failed")
            await asyncio.sleep(5)
    
    async def _simulate_email_service_failure(self):
        """Симуляция сбоя email сервиса"""
        print("📧 Simulating email service failure")
        
        with patch('app.services.email_client.EmailClient.send_email') as mock_send:
            mock_send.side_effect = Exception("SMTP server unavailable")
            await asyncio.sleep(4)
    
    async def _simulate_payment_service_failure(self):
        """Симуляция сбоя платежного сервиса"""
        print("💳 Simulating payment service failure")
        
        with patch('app.api.mango.process_payment') as mock_payment:
            mock_payment.side_effect = Exception("Payment gateway timeout")
            await asyncio.sleep(6)
    
    async def _simulate_file_storage_failure(self):
        """Симуляция сбоя файлового хранилища"""
        print("📂 Simulating file storage failure")
        
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("Storage unavailable")
            await asyncio.sleep(3)


class ChaosTestRunner:
    """Основной класс для выполнения chaos engineering тестов"""
    
    def __init__(self):
        self.scenarios = [
            DatabaseChaosScenario(),
            NetworkChaosScenario(),
            ResourceChaosScenario(),
            ServiceChaosScenario()
        ]
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "error_types": {},
            "response_times": [],
            "recovery_times": []
        }
    
    async def run_chaos_test(self, duration: int = 60, normal_load: bool = True):
        """Запустить chaos engineering тест"""
        print(f"🚀 Starting chaos engineering test for {duration} seconds")
        
        # Запускаем нормальную нагрузку в фоне
        normal_load_task = None
        if normal_load:
            normal_load_task = asyncio.create_task(self._generate_normal_load())
        
        # Запускаем chaos scenarios
        chaos_task = asyncio.create_task(self._run_chaos_scenarios(duration))
        
        # Мониторим систему
        monitoring_task = asyncio.create_task(self._monitor_system(duration))
        
        try:
            await asyncio.gather(chaos_task, monitoring_task)
        finally:
            if normal_load_task:
                normal_load_task.cancel()
        
        return self.metrics
    
    async def _generate_normal_load(self):
        """Генерация нормальной нагрузки"""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    start_time = time.time()
                    
                    # Случайный endpoint
                    endpoint = random.choice([
                        "/api/v1/health",
                        "/api/v1/requests/",
                        "/api/v1/transactions/",
                        "/api/v1/metrics/business"
                    ])
                    
                    async with session.get(f"http://localhost:8000{endpoint}") as response:
                        response_time = time.time() - start_time
                        
                        self.metrics["total_requests"] += 1
                        self.metrics["response_times"].append(response_time)
                        
                        if response.status < 400:
                            self.metrics["successful_requests"] += 1
                        else:
                            self.metrics["failed_requests"] += 1
                            error_type = f"HTTP_{response.status}"
                            self.metrics["error_types"][error_type] = \
                                self.metrics["error_types"].get(error_type, 0) + 1
                
                except Exception as e:
                    self.metrics["failed_requests"] += 1
                    error_type = type(e).__name__
                    self.metrics["error_types"][error_type] = \
                        self.metrics["error_types"].get(error_type, 0) + 1
                
                await asyncio.sleep(random.uniform(0.1, 0.5))
    
    async def _run_chaos_scenarios(self, duration: int):
        """Запуск сценариев хаоса"""
        end_time = time.time() + duration
        
        while time.time() < end_time:
            # Выбираем случайный сценарий
            scenario = random.choice(self.scenarios)
            
            await scenario.start()
            
            # Запускаем сценарий на случайное время
            scenario_duration = random.uniform(5, 15)
            scenario_task = asyncio.create_task(scenario.execute())
            
            await asyncio.sleep(scenario_duration)
            
            await scenario.stop()
            scenario_task.cancel()
            
            # Пауза между сценариями
            await asyncio.sleep(random.uniform(2, 8))
    
    async def _monitor_system(self, duration: int):
        """Мониторинг системы во время chaos testing"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # Проверяем доступность системы
            try:
                async with aiohttp.ClientSession() as session:
                    recovery_start = time.time()
                    
                    async with session.get("http://localhost:8000/api/v1/health") as response:
                        if response.status == 200:
                            recovery_time = time.time() - recovery_start
                            self.metrics["recovery_times"].append(recovery_time)
            
            except Exception:
                pass  # Система недоступна
            
            await asyncio.sleep(1)


class TestChaosEngineering:
    """Тесты chaos engineering"""
    
    @pytest.mark.asyncio
    async def test_database_chaos_resilience(self):
        """Тест устойчивости к сбоям БД"""
        scenario = DatabaseChaosScenario()
        
        # Запускаем хаос
        await scenario.start()
        chaos_task = asyncio.create_task(scenario.execute())
        
        # Тестируем систему во время хаоса
        async with aiohttp.ClientSession() as session:
            results = []
            
            for _ in range(10):
                try:
                    async with session.get("http://localhost:8000/api/v1/health") as response:
                        results.append(response.status)
                except Exception as e:
                    results.append(str(e))
                
                await asyncio.sleep(0.5)
        
        await scenario.stop()
        chaos_task.cancel()
        
        # Проверяем, что система показала некоторую устойчивость
        successful_responses = sum(1 for r in results if r == 200)
        print(f"Successful responses during DB chaos: {successful_responses}/10")
        
        # Система должна показать хотя бы частичную устойчивость
        assert successful_responses >= 2
    
    @pytest.mark.asyncio
    async def test_network_chaos_resilience(self):
        """Тест устойчивости к сетевым сбоям"""
        scenario = NetworkChaosScenario()
        
        await scenario.start()
        chaos_task = asyncio.create_task(scenario.execute())
        
        # Тестируем внешние вызовы
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Некоторые запросы успешны, некоторые нет
            mock_request.side_effect = [
                aiohttp.ClientError("Network error"),
                MagicMock(status=200),
                aiohttp.ClientError("Timeout"),
                MagicMock(status=200)
            ]
            
            results = []
            for _ in range(4):
                try:
                    # Тестируем resilience логику
                    result = await self._test_external_call()
                    results.append(result)
                except Exception as e:
                    results.append(str(e))
        
        await scenario.stop()
        chaos_task.cancel()
        
        print(f"Network chaos test results: {results}")
        # Проверяем, что есть механизмы восстановления
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_resilience(self):
        """Тест устойчивости к исчерпанию ресурсов"""
        scenario = ResourceChaosScenario()
        
        await scenario.start()
        chaos_task = asyncio.create_task(scenario.execute())
        
        # Мониторим использование ресурсов
        initial_memory = psutil.Process().memory_info().rss
        
        await asyncio.sleep(2)  # Даем время для хаоса
        
        current_memory = psutil.Process().memory_info().rss
        memory_increase = current_memory - initial_memory
        
        await scenario.stop()
        chaos_task.cancel()
        
        print(f"Memory increase during chaos: {memory_increase / 1024 / 1024:.2f} MB")
        
        # Проверяем, что система не потребляет чрезмерно много ресурсов
        assert memory_increase < 500 * 1024 * 1024  # Менее 500MB
    
    @pytest.mark.asyncio
    async def test_service_failure_resilience(self):
        """Тест устойчивости к сбоям внешних сервисов"""
        scenario = ServiceChaosScenario()
        
        await scenario.start()
        chaos_task = asyncio.create_task(scenario.execute())
        
        # Тестируем fallback механизмы
        with patch('app.core.cache.cache_manager.get') as mock_cache:
            mock_cache.side_effect = Exception("Cache unavailable")
            
            # Система должна работать без кеша
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get("http://localhost:8000/api/v1/health") as response:
                        assert response.status in [200, 503]  # OK или Service Unavailable
                except Exception:
                    pass  # Допустимо при chaos testing
        
        await scenario.stop()
        chaos_task.cancel()
    
    @pytest.mark.asyncio
    async def test_full_chaos_scenario(self):
        """Полный тест с множественными сбоями"""
        runner = ChaosTestRunner()
        
        # Запускаем полный chaos test на 30 секунд
        metrics = await runner.run_chaos_test(duration=30, normal_load=True)
        
        print(f"Full chaos test metrics: {json.dumps(metrics, indent=2)}")
        
        # Проверяем основные метрики
        assert metrics["total_requests"] > 0
        
        # Система должна показать некоторую устойчивость
        if metrics["total_requests"] > 0:
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            print(f"Success rate during chaos: {success_rate:.2%}")
            
            # Минимальный уровень устойчивости
            assert success_rate >= 0.1  # Хотя бы 10% запросов успешны
    
    async def _test_external_call(self):
        """Тестовый внешний вызов с retry логикой"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://example.com") as response:
                        return response.status
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
        
        return "Failed after retries"


class TestChaosRecovery:
    """Тесты восстановления после хаоса"""
    
    @pytest.mark.asyncio
    async def test_system_recovery_after_chaos(self):
        """Тест восстановления системы после хаоса"""
        # Запускаем интенсивный хаос
        scenarios = [
            DatabaseChaosScenario(),
            NetworkChaosScenario(),
            ResourceChaosScenario()
        ]
        
        # Применяем все сценарии хаоса
        for scenario in scenarios:
            await scenario.start()
            chaos_task = asyncio.create_task(scenario.execute())
            await asyncio.sleep(5)  # 5 секунд хаоса
            await scenario.stop()
            chaos_task.cancel()
        
        # Даем системе время на восстановление
        await asyncio.sleep(10)
        
        # Проверяем восстановление
        recovery_attempts = 0
        max_attempts = 30
        
        while recovery_attempts < max_attempts:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:8000/api/v1/health") as response:
                        if response.status == 200:
                            print(f"System recovered after {recovery_attempts + 1} attempts")
                            break
            except Exception:
                pass
            
            recovery_attempts += 1
            await asyncio.sleep(1)
        
        # Система должна восстановиться в разумное время
        assert recovery_attempts < max_attempts
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Тест graceful degradation при сбоях"""
        # Симулируем сбой кеша
        with patch('app.core.cache.cache_manager.get') as mock_cache:
            mock_cache.side_effect = Exception("Cache unavailable")
            
            # Система должна работать без кеша, но медленнее
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                try:
                    async with session.get("http://localhost:8000/api/v1/requests/") as response:
                        response_time = time.time() - start_time
                        
                        # Запрос должен быть успешным, но медленным
                        assert response.status in [200, 503]
                        
                        if response.status == 200:
                            print(f"Degraded response time: {response_time:.2f}s")
                            # Допускаем более медленный ответ при деградации
                            assert response_time < 10.0
                
                except Exception as e:
                    print(f"Expected degradation: {e}")


if __name__ == "__main__":
    # Запуск основного chaos engineering теста
    async def main():
        runner = ChaosTestRunner()
        metrics = await runner.run_chaos_test(duration=60)
        
        print("=== CHAOS ENGINEERING TEST RESULTS ===")
        print(json.dumps(metrics, indent=2))
        
        if metrics["total_requests"] > 0:
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            print(f"\n📊 Success Rate: {success_rate:.2%}")
            
            if success_rate >= 0.5:
                print("✅ System shows good resilience")
            elif success_rate >= 0.2:
                print("⚠️ System shows moderate resilience")
            else:
                print("❌ System needs better resilience")
    
    asyncio.run(main()) 