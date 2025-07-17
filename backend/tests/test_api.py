import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from decimal import Decimal

from app.core.models import City, Role, Master, Employee, RequestType, Request, TransactionType, Transaction
from app.core.auth import get_password_hash


@pytest.mark.asyncio
class TestHealthAPI:
    """Тесты API здоровья системы"""
    
    def test_health_check(self, client: TestClient):
        """Тест проверки здоровья системы"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data


@pytest.mark.asyncio
class TestRequestsAPI:
    """Тесты API заявок"""
    
    async def test_get_requests_unauthorized(self, client: TestClient):
        """Тест получения заявок без авторизации"""
        response = client.get("/api/v1/requests")
        assert response.status_code == 401
    
    async def test_create_request(self, client: TestClient, db_session: AsyncSession):
        """Тест создания заявки"""
        # Создаем необходимые зависимости
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        request_type = RequestType(name="Ремонт")
        db_session.add(request_type)
        await db_session.commit()
        await db_session.refresh(request_type)
        
        # Создаем мастера для авторизации
        role = Role(name="callcenter")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        password = "test_password"
        employee = Employee(
            name="Тестовый сотрудник",
            role_id=role.id,
            login="test_employee",
            password_hash=get_password_hash(password)
        )
        db_session.add(employee)
        await db_session.commit()
        
        # Авторизуемся
        login_response = client.post("/api/v1/auth/login", json={
            "login": "test_employee",
            "password": password
        })
        assert login_response.status_code == 200
        
        # Создаем заявку
        request_data = {
            "city_id": city.id,
            "request_type_id": request_type.id,
            "client_phone": "+79991234567",
            "client_name": "Тестовый клиент",
            "address": "Тестовый адрес",
            "problem": "Тестовая проблема"
        }
        
        response = client.post("/api/v1/requests", json=request_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["client_phone"] == "+79991234567"
        assert data["client_name"] == "Тестовый клиент"
        assert data["status"] == "new"


@pytest.mark.asyncio
class TestTransactionsAPI:
    """Тесты API транзакций"""
    
    async def test_get_transactions_unauthorized(self, client: TestClient):
        """Тест получения транзакций без авторизации"""
        response = client.get("/api/v1/transactions")
        assert response.status_code == 401
    
    async def test_create_transaction(self, client: TestClient, db_session: AsyncSession):
        """Тест создания транзакции"""
        # Создаем необходимые зависимости
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        transaction_type = TransactionType(name="Доход")
        db_session.add(transaction_type)
        await db_session.commit()
        await db_session.refresh(transaction_type)
        
        # Создаем сотрудника для авторизации
        role = Role(name="manager")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        password = "test_password"
        employee = Employee(
            name="Тестовый менеджер",
            role_id=role.id,
            login="test_manager",
            password_hash=get_password_hash(password)
        )
        db_session.add(employee)
        await db_session.commit()
        
        # Авторизуемся
        login_response = client.post("/api/v1/auth/login", json={
            "login": "test_manager",
            "password": password
        })
        assert login_response.status_code == 200
        
        # Создаем транзакцию
        transaction_data = {
            "city_id": city.id,
            "transaction_type_id": transaction_type.id,
            "amount": "5000.00",
            "notes": "Тестовая транзакция",
            "specified_date": str(date.today()),
            "payment_reason": "Оплата за услуги"
        }
        
        response = client.post("/api/v1/transactions", json=transaction_data)
        assert response.status_code == 201
        
        data = response.json()
        assert float(data["amount"]) == 5000.00
        assert data["notes"] == "Тестовая транзакция"


@pytest.mark.asyncio
class TestUsersAPI:
    """Тесты API пользователей"""
    
    async def test_get_users_unauthorized(self, client: TestClient):
        """Тест получения пользователей без авторизации"""
        response = client.get("/api/v1/users")
        assert response.status_code == 401
    
    async def test_create_master(self, client: TestClient, db_session: AsyncSession):
        """Тест создания мастера"""
        # Создаем город
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        # Создаем администратора для авторизации
        role = Role(name="admin")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        password = "admin_password"
        admin = Employee(
            name="Тестовый админ",
            role_id=role.id,
            login="test_admin",
            password_hash=get_password_hash(password)
        )
        db_session.add(admin)
        await db_session.commit()
        
        # Авторизуемся
        login_response = client.post("/api/v1/auth/login", json={
            "login": "test_admin",
            "password": password
        })
        assert login_response.status_code == 200
        
        # Создаем мастера
        master_data = {
            "city_id": city.id,
            "full_name": "Новый мастер",
            "phone_number": "+79991234567",
            "birth_date": "1990-01-01",
            "passport": "1234567890",
            "login": "new_master",
            "password": "master_password",
            "notes": "Тестовые заметки"
        }
        
        response = client.post("/api/v1/users/masters", json=master_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["full_name"] == "Новый мастер"
        assert data["phone_number"] == "+79991234567"
        assert data["login"] == "new_master"


@pytest.mark.asyncio
class TestMetricsAPI:
    """Тесты API метрик"""
    
    async def test_get_metrics_unauthorized(self, client: TestClient):
        """Тест получения метрик без авторизации"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 401
    
    async def test_get_metrics_authorized(self, client: TestClient, db_session: AsyncSession):
        """Тест получения метрик с авторизацией"""
        # Создаем администратора
        role = Role(name="admin")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        password = "admin_password"
        admin = Employee(
            name="Тестовый админ",
            role_id=role.id,
            login="test_admin",
            password_hash=get_password_hash(password)
        )
        db_session.add(admin)
        await db_session.commit()
        
        # Авторизуемся
        login_response = client.post("/api/v1/auth/login", json={
            "login": "test_admin",
            "password": password
        })
        assert login_response.status_code == 200
        
        # Получаем метрики
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "system_metrics" in data
        assert "business_metrics" in data


@pytest.mark.asyncio
class TestDatabaseAPI:
    """Тесты API базы данных"""
    
    async def test_database_status(self, client: TestClient):
        """Тест статуса базы данных"""
        response = client.get("/api/v1/database/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "connection_pool" in data
    
    async def test_database_statistics_unauthorized(self, client: TestClient):
        """Тест получения статистики БД без авторизации"""
        response = client.get("/api/v1/database/statistics")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestFilesAPI:
    """Тесты API файлов"""
    
    async def test_upload_file_unauthorized(self, client: TestClient):
        """Тест загрузки файла без авторизации"""
        response = client.post("/api/v1/files/upload")
        assert response.status_code == 401
    
    async def test_get_files_unauthorized(self, client: TestClient):
        """Тест получения файлов без авторизации"""
        response = client.get("/api/v1/files/")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestErrorHandling:
    """Тесты обработки ошибок"""
    
    async def test_404_error(self, client: TestClient):
        """Тест обработки 404 ошибки"""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
    
    async def test_422_validation_error(self, client: TestClient):
        """Тест обработки ошибки валидации"""
        response = client.post("/api/v1/auth/login", json={
            "login": "",  # Пустой логин
            "password": "password"
        })
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    async def test_method_not_allowed(self, client: TestClient):
        """Тест обработки неразрешенного HTTP метода"""
        response = client.delete("/api/v1/auth/login")
        assert response.status_code == 405


@pytest.mark.asyncio
class TestPagination:
    """Тесты пагинации"""
    
    async def test_requests_pagination(self, client: TestClient, db_session: AsyncSession):
        """Тест пагинации заявок"""
        # Создаем необходимые зависимости
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        request_type = RequestType(name="Ремонт")
        db_session.add(request_type)
        await db_session.commit()
        await db_session.refresh(request_type)
        
        # Создаем несколько заявок
        for i in range(5):
            request = Request(
                city_id=city.id,
                request_type_id=request_type.id,
                client_phone=f"+7999123456{i}",
                client_name=f"Клиент {i}"
            )
            db_session.add(request)
        
        await db_session.commit()
        
        # Создаем сотрудника для авторизации
        role = Role(name="callcenter")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        password = "test_password"
        employee = Employee(
            name="Тестовый сотрудник",
            role_id=role.id,
            login="test_employee",
            password_hash=get_password_hash(password)
        )
        db_session.add(employee)
        await db_session.commit()
        
        # Авторизуемся
        login_response = client.post("/api/v1/auth/login", json={
            "login": "test_employee",
            "password": password
        })
        assert login_response.status_code == 200
        
        # Тестируем пагинацию
        response = client.get("/api/v1/requests?page=1&per_page=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["pages"] == 3 