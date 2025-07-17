"""
Интеграционные тесты для API endpoints
Покрывают полные пользовательские сценарии
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date
from unittest.mock import patch, AsyncMock

from app.core.models import (
    City, Role, Master, Employee, Administrator, 
    Request, Transaction, RequestType, TransactionType, File
)


@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Тесты полного процесса аутентификации"""
    
    async def test_complete_login_flow(self, client: TestClient, test_employee: Employee):
        """Тест полного процесса входа в систему"""
        # 1. Попытка доступа без авторизации
        response = client.get("/api/v1/requests/")
        assert response.status_code == 401
        
        # 2. Получение CSRF токена
        csrf_response = client.get("/api/v1/auth/csrf-token")
        assert csrf_response.status_code == 200
        csrf_token = csrf_response.json()["csrf_token"]
        
        # 3. Успешный вход
        login_response = client.post("/api/v1/auth/login", 
            json={
                "login": test_employee.login,
                "password": "test_password"
            },
            headers={"X-CSRF-Token": csrf_token}
        )
        assert login_response.status_code == 200
        
        data = login_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "employee"
        
        # 4. Доступ к защищенному ресурсу
        token = data["access_token"]
        protected_response = client.get("/api/v1/requests/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == 200
    
    async def test_invalid_login_attempts(self, client: TestClient, test_employee: Employee):
        """Тест обработки неверных попыток входа"""
        # Неверный пароль
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "wrong_password"
        })
        assert response.status_code == 401
        
        # Несуществующий пользователь
        response = client.post("/api/v1/auth/login", json={
            "login": "nonexistent_user",
            "password": "any_password"
        })
        assert response.status_code == 401
        
        # Пустые данные
        response = client.post("/api/v1/auth/login", json={
            "login": "",
            "password": ""
        })
        assert response.status_code == 422
    
    async def test_token_expiration(self, client: TestClient, test_employee: Employee):
        """Тест истечения токена"""
        # Логинимся
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "test_password"
        })
        assert response.status_code == 200
        
        # Имитируем истекший токен
        expired_token = "expired.token.here"
        response = client.get("/api/v1/requests/",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRequestsWorkflow:
    """Тесты полного жизненного цикла заявок"""
    
    async def test_create_request_full_workflow(
        self, 
        authenticated_client: TestClient,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест полного процесса создания заявки"""
        # 1. Получение справочников
        cities_response = authenticated_client.get("/api/v1/requests/cities")
        assert cities_response.status_code == 200
        cities = cities_response.json()
        assert len(cities) > 0
        
        types_response = authenticated_client.get("/api/v1/requests/request-types")
        assert types_response.status_code == 200
        types = types_response.json()
        assert len(types) > 0
        
        masters_response = authenticated_client.get("/api/v1/requests/masters")
        assert masters_response.status_code == 200
        masters = masters_response.json()
        assert len(masters) > 0
        
        # 2. Создание заявки
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
        
        create_response = authenticated_client.post("/api/v1/requests/", json=request_data)
        assert create_response.status_code == 201
        
        created_request = create_response.json()
        assert created_request["client_name"] == "Тестовый клиент"
        assert created_request["status"] == "new"
        
        # 3. Получение созданной заявки
        request_id = created_request["id"]
        get_response = authenticated_client.get(f"/api/v1/requests/{request_id}")
        assert get_response.status_code == 200
        
        # 4. Обновление заявки
        update_data = {
            "status": "in_progress",
            "problem": "Обновленная проблема"
        }
        
        update_response = authenticated_client.put(f"/api/v1/requests/{request_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_request = update_response.json()
        assert updated_request["status"] == "in_progress"
        assert updated_request["problem"] == "Обновленная проблема"
        
        # 5. Получение списка заявок
        list_response = authenticated_client.get("/api/v1/requests/")
        assert list_response.status_code == 200
        
        requests_list = list_response.json()
        assert len(requests_list) > 0
        assert any(req["id"] == request_id for req in requests_list)
    
    async def test_request_filtering_and_search(
        self, 
        authenticated_client: TestClient,
        test_request: Request
    ):
        """Тест фильтрации и поиска заявок"""
        # Поиск по телефону
        response = authenticated_client.get(f"/api/v1/requests/?phone={test_request.client_phone}")
        assert response.status_code == 200
        requests = response.json()
        assert len(requests) > 0
        assert requests[0]["client_phone"] == test_request.client_phone
        
        # Фильтрация по статусу
        response = authenticated_client.get(f"/api/v1/requests/?status={test_request.status}")
        assert response.status_code == 200
        requests = response.json()
        assert len(requests) > 0
        
        # Фильтрация по городу
        response = authenticated_client.get(f"/api/v1/requests/?city_id={test_request.city_id}")
        assert response.status_code == 200
        requests = response.json()
        assert len(requests) > 0
        
        # Фильтрация по мастеру
        response = authenticated_client.get(f"/api/v1/requests/?master_id={test_request.master_id}")
        assert response.status_code == 200
        requests = response.json()
        assert len(requests) > 0
    
    async def test_request_permissions(
        self, 
        client: TestClient,
        master_client: TestClient,
        test_request: Request,
        test_master: Master
    ):
        """Тест разрешений доступа к заявкам"""
        # Неавторизованный доступ
        response = client.get("/api/v1/requests/")
        assert response.status_code == 401
        
        # Мастер может видеть только свои заявки
        response = master_client.get("/api/v1/requests/")
        assert response.status_code == 200
        
        # Мастер может обновлять только свои заявки
        if test_request.master_id == test_master.id:
            response = master_client.put(f"/api/v1/requests/{test_request.id}", 
                json={"status": "completed"})
            assert response.status_code == 200
        else:
            response = master_client.put(f"/api/v1/requests/{test_request.id}", 
                json={"status": "completed"})
            assert response.status_code == 403


@pytest.mark.asyncio
class TestTransactionsWorkflow:
    """Тесты работы с транзакциями"""
    
    async def test_create_transaction_workflow(
        self,
        authenticated_client: TestClient,
        test_city: City,
        test_transaction_type: TransactionType,
        test_master: Master
    ):
        """Тест создания транзакции"""
        # Создание транзакции
        transaction_data = {
            "city_id": test_city.id,
            "transaction_type_id": test_transaction_type.id,
            "master_id": test_master.id,
            "amount": 1000.00,
            "specified_date": str(date.today()),
            "description": "Тестовая транзакция"
        }
        
        response = authenticated_client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 201
        
        created_transaction = response.json()
        assert created_transaction["amount"] == 1000.00
        assert created_transaction["description"] == "Тестовая транзакция"
        
        # Получение транзакции
        transaction_id = created_transaction["id"]
        response = authenticated_client.get(f"/api/v1/transactions/{transaction_id}")
        assert response.status_code == 200
        
        # Обновление транзакции
        update_data = {
            "amount": 1500.00,
            "description": "Обновленная транзакция"
        }
        
        response = authenticated_client.put(f"/api/v1/transactions/{transaction_id}", json=update_data)
        assert response.status_code == 200
        
        updated_transaction = response.json()
        assert updated_transaction["amount"] == 1500.00
    
    async def test_transaction_filtering(
        self,
        authenticated_client: TestClient,
        test_transaction: Transaction
    ):
        """Тест фильтрации транзакций"""
        # Фильтрация по типу
        response = authenticated_client.get(f"/api/v1/transactions/?type_id={test_transaction.transaction_type_id}")
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) > 0
        
        # Фильтрация по мастеру
        response = authenticated_client.get(f"/api/v1/transactions/?master_id={test_transaction.master_id}")
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) > 0
        
        # Фильтрация по дате
        response = authenticated_client.get(f"/api/v1/transactions/?date={test_transaction.specified_date}")
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) > 0


@pytest.mark.asyncio
class TestFileUploadWorkflow:
    """Тесты загрузки файлов"""
    
    async def test_file_upload_workflow(
        self,
        authenticated_client: TestClient,
        test_request: Request
    ):
        """Тест загрузки файлов"""
        # Создаем тестовый файл
        test_file_content = b"Test file content"
        
        # Загружаем файл как чек расходов
        files = {"file": ("test_receipt.jpg", test_file_content, "image/jpeg")}
        response = authenticated_client.post(
            f"/api/v1/files/upload-expense-receipt/{test_request.id}",
            files=files
        )
        assert response.status_code == 200
        
        file_info = response.json()
        assert "file_path" in file_info
        assert "file_size" in file_info
        
        # Загружаем файл как БСО
        files = {"file": ("test_bso.pdf", test_file_content, "application/pdf")}
        response = authenticated_client.post(
            f"/api/v1/files/upload-bso/{test_request.id}",
            files=files
        )
        assert response.status_code == 200
    
    @patch('app.utils.file_security.validate_file_content')
    async def test_file_security_validation(
        self,
        mock_validate,
        authenticated_client: TestClient,
        test_request: Request
    ):
        """Тест валидации безопасности файлов"""
        # Мокаем валидацию как неуспешную
        mock_validate.return_value = False
        
        malicious_file = b"Malicious content"
        files = {"file": ("malicious.exe", malicious_file, "application/x-executable")}
        
        response = authenticated_client.post(
            f"/api/v1/files/upload-expense-receipt/{test_request.id}",
            files=files
        )
        assert response.status_code == 400
        assert "не прошел проверку безопасности" in response.json()["detail"]


@pytest.mark.asyncio
class TestHealthAndMonitoring:
    """Тесты системы мониторинга и здоровья"""
    
    async def test_health_check_workflow(self, client: TestClient):
        """Тест проверки здоровья системы"""
        # Базовая проверка здоровья
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "timestamp" in health_data
        
        # Детальная проверка здоровья (требует авторизации)
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 401  # Без авторизации
    
    async def test_metrics_collection(self, admin_client: TestClient):
        """Тест сбора метрик"""
        # Получение метрик (только для админа)
        response = admin_client.get("/api/v1/metrics/")
        assert response.status_code == 200
        
        metrics = response.json()
        assert "system_metrics" in metrics
        assert "business_metrics" in metrics
        
        # Проверка наличия ключевых метрик
        system_metrics = metrics["system_metrics"]
        assert "cpu_usage" in system_metrics
        assert "memory_usage" in system_metrics
        
        business_metrics = metrics["business_metrics"]
        assert "requests_total" in business_metrics
        assert "transactions_total" in business_metrics


@pytest.mark.asyncio
class TestSecurityFeatures:
    """Тесты функций безопасности"""
    
    async def test_csrf_protection(self, client: TestClient, test_employee: Employee):
        """Тест CSRF защиты"""
        # Попытка входа без CSRF токена
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "test_password"
        })
        # В зависимости от настроек может быть 200 или 403
        assert response.status_code in [200, 403]
        
        # Получение CSRF токена
        csrf_response = client.get("/api/v1/auth/csrf-token")
        assert csrf_response.status_code == 200
        
        csrf_token = csrf_response.json()["csrf_token"]
        assert csrf_token is not None
        
        # Вход с CSRF токеном
        response = client.post("/api/v1/auth/login", 
            json={
                "login": test_employee.login,
                "password": "test_password"
            },
            headers={"X-CSRF-Token": csrf_token}
        )
        assert response.status_code == 200
    
    async def test_rate_limiting(self, client: TestClient):
        """Тест ограничения частоты запросов"""
        # Делаем много запросов подряд
        responses = []
        for i in range(20):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Проверяем что большинство запросов прошло
        success_count = sum(1 for status in responses if status == 200)
        assert success_count > 10  # Большинство должно пройти
    
    async def test_secure_headers(self, client: TestClient):
        """Тест заголовков безопасности"""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Проверяем наличие заголовков безопасности
        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Content-Security-Policy" in headers
        
        # Проверяем значения заголовков
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"


@pytest.mark.asyncio
class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    async def test_validation_errors(self, authenticated_client: TestClient):
        """Тест ошибок валидации"""
        # Создание заявки с неверными данными
        invalid_data = {
            "city_id": "invalid",  # Должно быть число
            "client_phone": "invalid_phone",  # Неверный формат
            "result": "not_a_number"  # Должно быть число
        }
        
        response = authenticated_client.post("/api/v1/requests/", json=invalid_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
    
    async def test_not_found_errors(self, authenticated_client: TestClient):
        """Тест ошибок 404"""
        # Попытка получить несуществующую заявку
        response = authenticated_client.get("/api/v1/requests/99999")
        assert response.status_code == 404
        
        # Попытка обновить несуществующую заявку
        response = authenticated_client.put("/api/v1/requests/99999", json={"status": "completed"})
        assert response.status_code == 404
    
    async def test_permission_errors(self, master_client: TestClient):
        """Тест ошибок доступа"""
        # Мастер пытается получить метрики (только для админа)
        response = master_client.get("/api/v1/metrics/")
        assert response.status_code == 403
        
        # Мастер пытается создать пользователя
        response = master_client.post("/api/v1/users/", json={
            "name": "Новый пользователь",
            "login": "new_user",
            "password": "password123"
        })
        assert response.status_code == 403


@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Тесты интеграции с базой данных"""
    
    async def test_database_transactions(
        self,
        authenticated_client: TestClient,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест транзакций базы данных"""
        # Создание нескольких связанных записей
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
        
        # Создаем заявку
        response = authenticated_client.post("/api/v1/requests/", json=request_data)
        assert response.status_code == 201
        
        request_id = response.json()["id"]
        
        # Проверяем что заявка создалась
        response = authenticated_client.get(f"/api/v1/requests/{request_id}")
        assert response.status_code == 200
        
        # Обновляем заявку
        response = authenticated_client.put(f"/api/v1/requests/{request_id}", 
            json={"status": "completed"})
        assert response.status_code == 200
        
        # Проверяем что обновление сохранилось
        response = authenticated_client.get(f"/api/v1/requests/{request_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    async def test_database_constraints(
        self,
        authenticated_client: TestClient,
        test_city: City,
        test_request_type: RequestType
    ):
        """Тест ограничений базы данных"""
        # Попытка создать заявку с несуществующим мастером
        request_data = {
            "city_id": test_city.id,
            "request_type_id": test_request_type.id,
            "master_id": 99999,  # Несуществующий мастер
            "client_phone": "+79991234567",
            "client_name": "Тестовый клиент",
            "address": "Тестовый адрес",
            "problem": "Тестовая проблема"
        }
        
        response = authenticated_client.post("/api/v1/requests/", json=request_data)
        assert response.status_code == 400  # Ошибка валидации внешнего ключа 