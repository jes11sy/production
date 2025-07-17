"""
E2E тесты для полного тестирования пользовательских сценариев
Тестируют весь жизненный цикл заявок от создания до завершения
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import uuid
import os

from app.main import app
from app.core.database import get_db
from app.core.models import Request, Transaction, Master, Employee, City, RequestType
from app.core.auth import get_current_user


class TestE2EFullRequestLifecycle:
    """Тестирование полного жизненного цикла заявки"""
    
    @pytest.fixture
    async def authenticated_client(self, async_client: AsyncClient, test_db: AsyncSession):
        """Клиент с аутентифицированным пользователем"""
        # Создаем тестового пользователя
        test_user = Employee(
            login="test_employee",
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test Employee",
            role_id=1,
            city_id=1,
            is_active=True
        )
        test_db.add(test_user)
        await test_db.commit()
        
        # Мокаем аутентификацию
        with patch('app.core.auth.get_current_user', return_value=test_user):
            yield async_client
    
    async def test_complete_request_workflow(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Тест полного workflow заявки: создание → обработка → завершение"""
        
        # 1. Создание заявки
        request_data = {
            "client_name": "Иван Петров",
            "client_phone": "+79123456789",
            "client_email": "ivan@example.com",
            "address": "Москва, ул. Тестовая, 1",
            "description": "Требуется ремонт крана",
            "advertising_campaign_id": 1,
            "city_id": 1,
            "request_type_id": 1,
            "direction_id": 1,
            "priority": "medium",
            "status": "new"
        }
        
        response = await authenticated_client.post("/api/v1/requests/", json=request_data)
        assert response.status_code == 201
        created_request = response.json()
        request_id = created_request["id"]
        
        # 2. Назначение мастера
        master_assignment = {"master_id": 1}
        response = await authenticated_client.patch(
            f"/api/v1/requests/{request_id}/assign-master",
            json=master_assignment
        )
        assert response.status_code == 200
        
        # 3. Обновление статуса на "в работе"
        status_update = {"status": "in_progress"}
        response = await authenticated_client.patch(
            f"/api/v1/requests/{request_id}",
            json=status_update
        )
        assert response.status_code == 200
        
        # 4. Добавление файлов к заявке
        test_file_content = b"test file content"
        files = {"file": ("test.jpg", test_file_content, "image/jpeg")}
        response = await authenticated_client.post(
            f"/api/v1/requests/{request_id}/files",
            files=files
        )
        assert response.status_code == 201
        
        # 5. Создание транзакции
        transaction_data = {
            "amount": 5000.0,
            "transaction_type_id": 1,
            "description": "Оплата за ремонт",
            "request_id": request_id,
            "city_id": 1,
            "status": "completed"
        }
        
        response = await authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 201
        
        # 6. Завершение заявки
        completion_data = {
            "status": "completed",
            "completion_notes": "Работа выполнена качественно"
        }
        
        response = await authenticated_client.patch(
            f"/api/v1/requests/{request_id}",
            json=completion_data
        )
        assert response.status_code == 200
        
        # 7. Проверка финального состояния заявки
        response = await authenticated_client.get(f"/api/v1/requests/{request_id}")
        assert response.status_code == 200
        
        final_request = response.json()
        assert final_request["status"] == "completed"
        assert final_request["master_id"] == 1
        assert len(final_request["files"]) > 0
        assert final_request["completion_notes"] == "Работа выполнена качественно"


class TestE2EUserManagement:
    """Тестирование управления пользователями"""
    
    async def test_user_registration_and_authentication_flow(self, async_client: AsyncClient):
        """Тест регистрации и аутентификации пользователя"""
        
        # 1. Регистрация нового пользователя
        user_data = {
            "login": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User",
            "role_id": 2,
            "city_id": 1
        }
        
        response = await async_client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 201
        
        # 2. Аутентификация
        login_data = {
            "login": "newuser",
            "password": "securepassword123"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        # 3. Получение информации о текущем пользователе
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        
        user_info = response.json()
        assert user_info["login"] == "newuser"
        assert user_info["email"] == "newuser@example.com"
        
        # 4. Обновление профиля
        update_data = {
            "full_name": "Updated User Name",
            "email": "updated@example.com"
        }
        
        response = await async_client.patch("/api/v1/auth/me", json=update_data)
        assert response.status_code == 200
        
        # 5. Выход из системы
        response = await async_client.post("/api/v1/auth/logout")
        assert response.status_code == 200


class TestE2EReportingAndAnalytics:
    """Тестирование отчетности и аналитики"""
    
    async def test_comprehensive_reporting_flow(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Тест полного цикла создания отчетов"""
        
        # 1. Создание тестовых данных
        await self._create_test_data(test_db)
        
        # 2. Получение общей статистики
        response = await authenticated_client.get("/api/v1/requests/statistics")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_requests" in stats
        assert "requests_by_status" in stats
        assert "requests_by_city" in stats
        
        # 3. Получение финансовой отчетности
        response = await authenticated_client.get("/api/v1/transactions/financial-report")
        assert response.status_code == 200
        
        financial_report = response.json()
        assert "total_revenue" in financial_report
        assert "transactions_by_type" in financial_report
        
        # 4. Получение отчета по мастерам
        response = await authenticated_client.get("/api/v1/users/masters/performance")
        assert response.status_code == 200
        
        masters_report = response.json()
        assert isinstance(masters_report, list)
        
        # 5. Экспорт данных
        response = await authenticated_client.get("/api/v1/requests/export?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
    
    async def _create_test_data(self, test_db: AsyncSession):
        """Создание тестовых данных для отчетов"""
        # Создаем несколько заявок с разными статусами
        for i in range(5):
            request = Request(
                client_name=f"Client {i}",
                client_phone=f"+7912345678{i}",
                address=f"Address {i}",
                description=f"Description {i}",
                city_id=1,
                request_type_id=1,
                status="completed" if i % 2 == 0 else "in_progress",
                created_at=datetime.now() - timedelta(days=i)
            )
            test_db.add(request)
        
        await test_db.commit()


class TestE2ESystemIntegration:
    """Тестирование интеграции с внешними системами"""
    
    async def test_external_services_integration(self, authenticated_client: AsyncClient):
        """Тест интеграции с внешними сервисами"""
        
        # 1. Тест отправки email уведомлений
        with patch('app.services.email_client.EmailClient.send_email') as mock_email:
            mock_email.return_value = True
            
            email_data = {
                "to": "test@example.com",
                "subject": "Test Subject",
                "body": "Test Body",
                "template": "notification"
            }
            
            response = await authenticated_client.post("/api/v1/notifications/email", json=email_data)
            assert response.status_code == 200
            mock_email.assert_called_once()
        
        # 2. Тест записи звонков
        with patch('app.services.recording_service.RecordingService.save_recording') as mock_recording:
            mock_recording.return_value = {"file_path": "/recordings/test.mp3"}
            
            recording_data = {
                "caller_phone": "+79123456789",
                "duration": 120,
                "request_id": 1
            }
            
            response = await authenticated_client.post("/api/v1/recordings/", json=recording_data)
            assert response.status_code == 201
            mock_recording.assert_called_once()
        
        # 3. Тест интеграции с платежной системой
        with patch('app.api.mango.process_payment') as mock_payment:
            mock_payment.return_value = {"status": "success", "transaction_id": "12345"}
            
            payment_data = {
                "amount": 1000.0,
                "card_number": "1234567890123456",
                "request_id": 1
            }
            
            response = await authenticated_client.post("/api/v1/payments/process", json=payment_data)
            assert response.status_code == 200
            mock_payment.assert_called_once()


class TestE2ESecurityScenarios:
    """Тестирование сценариев безопасности"""
    
    async def test_security_attack_scenarios(self, async_client: AsyncClient):
        """Тест защиты от различных атак"""
        
        # 1. Тест защиты от SQL инъекций
        malicious_data = {
            "client_name": "'; DROP TABLE requests; --",
            "client_phone": "+79123456789",
            "description": "Normal description"
        }
        
        response = await async_client.post("/api/v1/requests/", json=malicious_data)
        # Запрос должен быть обработан безопасно
        assert response.status_code in [400, 401, 422]  # Валидация или аутентификация
        
        # 2. Тест защиты от XSS
        xss_data = {
            "client_name": "<script>alert('XSS')</script>",
            "description": "<img src=x onerror=alert('XSS')>"
        }
        
        response = await async_client.post("/api/v1/requests/", json=xss_data)
        assert response.status_code in [400, 401, 422]
        
        # 3. Тест rate limiting
        for i in range(105):  # Превышаем лимит 100 req/min
            response = await async_client.get("/api/v1/health")
            if i > 100:
                assert response.status_code == 429  # Too Many Requests
        
        # 4. Тест CSRF защиты
        csrf_data = {"malicious": "data"}
        response = await async_client.post("/api/v1/requests/", json=csrf_data)
        # Без CSRF токена запрос должен быть отклонен
        assert response.status_code in [401, 403]


class TestE2EPerformanceScenarios:
    """Тестирование производительности в реальных сценариях"""
    
    async def test_concurrent_request_handling(self, authenticated_client: AsyncClient):
        """Тест обработки конкурентных запросов"""
        
        async def create_request(client_id: int):
            """Создание заявки"""
            data = {
                "client_name": f"Client {client_id}",
                "client_phone": f"+7912345678{client_id % 10}",
                "address": f"Address {client_id}",
                "description": f"Description {client_id}",
                "city_id": 1,
                "request_type_id": 1
            }
            
            response = await authenticated_client.post("/api/v1/requests/", json=data)
            return response.status_code
        
        # Создаем 50 заявок одновременно
        tasks = [create_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Проверяем, что большинство запросов обработано успешно
        successful_requests = sum(1 for result in results if result == 201)
        assert successful_requests >= 40  # Минимум 80% успешных запросов
    
    async def test_large_data_processing(self, authenticated_client: AsyncClient):
        """Тест обработки больших объемов данных"""
        
        # Тест загрузки большого файла
        large_file_content = b"x" * (5 * 1024 * 1024)  # 5MB файл
        files = {"file": ("large_file.txt", large_file_content, "text/plain")}
        
        response = await authenticated_client.post("/api/v1/files/upload", files=files)
        assert response.status_code in [201, 413]  # Успех или превышение лимита
        
        # Тест получения большого количества записей
        response = await authenticated_client.get("/api/v1/requests/?limit=1000")
        assert response.status_code == 200
        
        # Проверяем время ответа (должно быть разумным)
        assert response.elapsed.total_seconds() < 5.0  # Менее 5 секунд


class TestE2EDataConsistency:
    """Тестирование консистентности данных"""
    
    async def test_data_integrity_across_operations(self, authenticated_client: AsyncClient, test_db: AsyncSession):
        """Тест целостности данных при различных операциях"""
        
        # 1. Создание заявки
        request_data = {
            "client_name": "Test Client",
            "client_phone": "+79123456789",
            "address": "Test Address",
            "description": "Test Description",
            "city_id": 1,
            "request_type_id": 1
        }
        
        response = await authenticated_client.post("/api/v1/requests/", json=request_data)
        assert response.status_code == 201
        request_id = response.json()["id"]
        
        # 2. Создание связанной транзакции
        transaction_data = {
            "amount": 1000.0,
            "transaction_type_id": 1,
            "description": "Test Transaction",
            "request_id": request_id,
            "city_id": 1
        }
        
        response = await authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 201
        transaction_id = response.json()["id"]
        
        # 3. Проверка связей
        response = await authenticated_client.get(f"/api/v1/requests/{request_id}")
        request_data = response.json()
        
        response = await authenticated_client.get(f"/api/v1/transactions/{transaction_id}")
        transaction_data = response.json()
        
        assert transaction_data["request_id"] == request_id
        
        # 4. Удаление заявки (должно каскадно удалить связанные данные)
        response = await authenticated_client.delete(f"/api/v1/requests/{request_id}")
        assert response.status_code == 200
        
        # 5. Проверка, что связанные данные тоже удалены
        response = await authenticated_client.get(f"/api/v1/transactions/{transaction_id}")
        assert response.status_code == 404  # Транзакция должна быть удалена


@pytest.mark.asyncio
class TestE2EHealthAndMonitoring:
    """Тестирование системы мониторинга и здоровья"""
    
    async def test_system_health_monitoring(self, async_client: AsyncClient):
        """Тест системы мониторинга здоровья"""
        
        # 1. Проверка общего здоровья системы
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "checks" in health_data
        
        # 2. Проверка детальных метрик
        response = await async_client.get("/api/v1/metrics/business")
        assert response.status_code == 200
        
        # 3. Проверка производительности
        response = await async_client.get("/api/v1/metrics/performance")
        assert response.status_code == 200
        
        # 4. Проверка статуса базы данных
        response = await async_client.get("/api/v1/database/status")
        assert response.status_code == 200
        
        db_status = response.json()
        assert "connection_pool" in db_status
        assert "active_connections" in db_status


# Фикстуры для тестов
@pytest.fixture
async def async_client():
    """Асинхронный клиент для тестирования"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_db():
    """Тестовая база данных"""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 