"""
E2E тесты для системы управления заявками
Тестируют полные сценарии использования API
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from decimal import Decimal
import json

from app.main import app
from app.core.models import City, Role, Master, Employee, Request, Transaction, RequestType, Direction, AdvertisingCampaign, TransactionType


class TestE2EUserManagement:
    """E2E тесты для управления пользователями"""
    
    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, client: TestClient, db_session: AsyncSession, admin_token: str):
        """Тест полного workflow создания и управления пользователем"""
        
        # 1. Создаем город
        city_data = {"name": "Тестовый город"}
        response = client.post("/api/v1/cities", json=city_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        city_id = response.json()["id"]
        
        # 2. Создаем роль
        role_data = {"name": "Тестовая роль"}
        response = client.post("/api/v1/roles", json=role_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        role_id = response.json()["id"]
        
        # 3. Создаем мастера
        master_data = {
            "city_id": city_id,
            "full_name": "Тестовый Мастер",
            "phone_number": "+7999123456",
            "birth_date": "1990-01-01",
            "passport": "1234567890",
            "login": "test_master",
            "password": "test_password123"
        }
        response = client.post("/api/v1/masters", json=master_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        master_id = response.json()["id"]
        
        # 4. Создаем сотрудника
        employee_data = {
            "name": "Тестовый Сотрудник",
            "role_id": role_id,
            "city_id": city_id,
            "login": "test_employee",
            "password": "test_password123"
        }
        response = client.post("/api/v1/employees", json=employee_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        employee_id = response.json()["id"]
        
        # 5. Проверяем список пользователей
        response = client.get("/api/v1/masters", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        masters = response.json()
        assert len(masters) >= 1
        assert any(m["id"] == master_id for m in masters)
        
        # 6. Обновляем мастера
        update_data = {"full_name": "Обновленный Мастер"}
        response = client.put(f"/api/v1/masters/{master_id}", json=update_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json()["full_name"] == "Обновленный Мастер"
        
        # 7. Деактивируем мастера
        response = client.patch(f"/api/v1/masters/{master_id}/deactivate", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 8. Проверяем статус
        response = client.get(f"/api/v1/masters/{master_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        assert response.json()["status"] == "inactive"


class TestE2ERequestManagement:
    """E2E тесты для управления заявками"""
    
    @pytest.mark.asyncio
    async def test_complete_request_workflow(self, client: TestClient, db_session: AsyncSession, admin_token: str):
        """Тест полного workflow обработки заявки"""
        
        # Подготовка данных
        city_data = {"name": "Город для заявки"}
        response = client.post("/api/v1/cities", json=city_data, headers={"Authorization": f"Bearer {admin_token}"})
        city_id = response.json()["id"]
        
        request_type_data = {"name": "Тип заявки"}
        response = client.post("/api/v1/request_types", json=request_type_data, headers={"Authorization": f"Bearer {admin_token}"})
        request_type_id = response.json()["id"]
        
        direction_data = {"name": "Направление"}
        response = client.post("/api/v1/directions", json=direction_data, headers={"Authorization": f"Bearer {admin_token}"})
        direction_id = response.json()["id"]
        
        campaign_data = {
            "city_id": city_id,
            "name": "Тестовая кампания",
            "phone_number": "+7999111222"
        }
        response = client.post("/api/v1/advertising_campaigns", json=campaign_data, headers={"Authorization": f"Bearer {admin_token}"})
        campaign_id = response.json()["id"]
        
        master_data = {
            "city_id": city_id,
            "full_name": "Мастер для заявки",
            "phone_number": "+7999333444",
            "login": "master_request",
            "password": "password123"
        }
        response = client.post("/api/v1/masters", json=master_data, headers={"Authorization": f"Bearer {admin_token}"})
        master_id = response.json()["id"]
        
        # 1. Создаем заявку
        request_data = {
            "advertising_campaign_id": campaign_id,
            "city_id": city_id,
            "request_type_id": request_type_id,
            "client_phone": "+7999555666",
            "client_name": "Тестовый Клиент",
            "address": "Тестовый адрес",
            "direction_id": direction_id,
            "problem": "Тестовая проблема"
        }
        response = client.post("/api/v1/requests", json=request_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        request_id = response.json()["id"]
        
        # 2. Назначаем мастера
        assign_data = {"master_id": master_id}
        response = client.patch(f"/api/v1/requests/{request_id}/assign", json=assign_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 3. Обновляем статус заявки
        status_data = {"status": "in_progress"}
        response = client.patch(f"/api/v1/requests/{request_id}/status", json=status_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 4. Добавляем заметки мастера
        notes_data = {"master_notes": "Работа выполнена"}
        response = client.patch(f"/api/v1/requests/{request_id}/notes", json=notes_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 5. Добавляем финансовые данные
        financial_data = {
            "result": "5000.00",
            "expenses": "1000.00",
            "net_amount": "4000.00",
            "master_handover": "2000.00"
        }
        response = client.patch(f"/api/v1/requests/{request_id}/financial", json=financial_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 6. Завершаем заявку
        complete_data = {"status": "completed"}
        response = client.patch(f"/api/v1/requests/{request_id}/status", json=complete_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 7. Проверяем итоговое состояние заявки
        response = client.get(f"/api/v1/requests/{request_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        final_request = response.json()
        assert final_request["status"] == "completed"
        assert final_request["master_id"] == master_id
        assert final_request["master_notes"] == "Работа выполнена"
        assert float(final_request["result"]) == 5000.00
        
        # 8. Проверяем статистику
        response = client.get("/api/v1/requests/stats", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        stats = response.json()
        assert stats["total_requests"] >= 1
        assert stats["completed_requests"] >= 1


class TestE2ETransactionManagement:
    """E2E тесты для управления транзакциями"""
    
    @pytest.mark.asyncio
    async def test_complete_transaction_workflow(self, client: TestClient, db_session: AsyncSession, admin_token: str):
        """Тест полного workflow обработки транзакций"""
        
        # Подготовка данных
        city_data = {"name": "Город для транзакции"}
        response = client.post("/api/v1/cities", json=city_data, headers={"Authorization": f"Bearer {admin_token}"})
        city_id = response.json()["id"]
        
        transaction_type_data = {"name": "Тип транзакции"}
        response = client.post("/api/v1/transaction_types", json=transaction_type_data, headers={"Authorization": f"Bearer {admin_token}"})
        transaction_type_id = response.json()["id"]
        
        # 1. Создаем транзакцию
        transaction_data = {
            "city_id": city_id,
            "transaction_type_id": transaction_type_id,
            "amount": "1500.00",
            "notes": "Тестовая транзакция",
            "specified_date": "2024-01-15",
            "payment_reason": "Тестовая причина"
        }
        response = client.post("/api/v1/transactions", json=transaction_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 201
        transaction_id = response.json()["id"]
        
        # 2. Проверяем создание
        response = client.get(f"/api/v1/transactions/{transaction_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        transaction = response.json()
        assert float(transaction["amount"]) == 1500.00
        assert transaction["notes"] == "Тестовая транзакция"
        
        # 3. Обновляем транзакцию
        update_data = {
            "amount": "2000.00",
            "notes": "Обновленная транзакция"
        }
        response = client.put(f"/api/v1/transactions/{transaction_id}", json=update_data, headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        
        # 4. Проверяем обновление
        response = client.get(f"/api/v1/transactions/{transaction_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        updated_transaction = response.json()
        assert float(updated_transaction["amount"]) == 2000.00
        assert updated_transaction["notes"] == "Обновленная транзакция"
        
        # 5. Получаем список транзакций
        response = client.get("/api/v1/transactions", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) >= 1
        assert any(t["id"] == transaction_id for t in transactions)
        
        # 6. Проверяем фильтрацию по городу
        response = client.get(f"/api/v1/transactions?city_id={city_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        filtered_transactions = response.json()
        assert all(t["city_id"] == city_id for t in filtered_transactions)


class TestE2EAPIVersioning:
    """E2E тесты для версионирования API"""
    
    def test_api_v1_endpoints(self, client: TestClient, admin_token: str):
        """Тест доступности эндпоинтов v1"""
        
        # Проверяем информацию о версии v1
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        version_info = response.json()
        assert version_info["version"] == "1.0.0"
        assert version_info["status"] == "stable"
        
        # Проверяем заголовки версионирования
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "API-Version" in response.headers
        assert response.headers["API-Version"] == "1.0"
    
    def test_api_v2_endpoints(self, client: TestClient, admin_token: str):
        """Тест доступности эндпоинтов v2"""
        
        # Проверяем информацию о версии v2
        response = client.get("/api/v2/version")
        assert response.status_code == 200
        version_info = response.json()
        assert version_info["version"] == "2.0.0"
        assert version_info["status"] == "beta"
        
        # Проверяем новые возможности v2
        response = client.get("/api/v2/features")
        assert response.status_code == 200
        features = response.json()
        assert "new_features" in features
        assert "breaking_changes" in features
    
    def test_version_header_support(self, client: TestClient):
        """Тест поддержки версионирования через заголовки"""
        
        # Запрос с заголовком версии 1.0
        response = client.get("/api/health", headers={"API-Version": "1.0"})
        assert response.status_code == 200
        assert response.headers["API-Version"] == "1.0"
        
        # Запрос с заголовком версии 2.0
        response = client.get("/api/health", headers={"API-Version": "2.0"})
        assert response.status_code == 200
        assert response.headers["API-Version"] == "2.0"
        
        # Запрос с неподдерживаемой версией
        response = client.get("/api/health", headers={"API-Version": "3.0"})
        assert response.status_code == 400
        error = response.json()
        assert "Unsupported API version" in error["error"]


class TestE2ESecurityAndAuth:
    """E2E тесты для безопасности и аутентификации"""
    
    def test_authentication_flow(self, client: TestClient):
        """Тест полного flow аутентификации"""
        
        # 1. Попытка доступа без токена
        response = client.get("/api/v1/users")
        assert response.status_code == 401
        
        # 2. Логин с неверными данными
        login_data = {"username": "wrong_user", "password": "wrong_password"}
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        
        # 3. Логин с правильными данными (используем админа из фикстур)
        login_data = {"username": "admin", "password": "admin_password"}
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        
        # 4. Использование токена для доступа к защищенному ресурсу
        token = token_data["access_token"]
        response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        
        # 5. Проверка информации о текущем пользователе
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user_info = response.json()
        assert user_info["username"] == "admin"
    
    def test_rate_limiting(self, client: TestClient):
        """Тест ограничения скорости запросов"""
        
        # Делаем много запросов подряд
        responses = []
        for i in range(100):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Проверяем, что есть ограничения (429 Too Many Requests)
        assert any(status == 429 for status in responses[-10:])  # В последних 10 запросах


class TestE2EPerformanceAndMonitoring:
    """E2E тесты для производительности и мониторинга"""
    
    def test_health_checks(self, client: TestClient):
        """Тест системы health checks"""
        
        # Основной health check
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # Детальный health check
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        detailed_health = response.json()
        assert "database" in detailed_health
        assert "redis" in detailed_health
        assert "disk_space" in detailed_health
    
    def test_metrics_collection(self, client: TestClient, admin_token: str):
        """Тест сбора метрик"""
        
        # Делаем несколько запросов для генерации метрик
        client.get("/api/v1/health")
        client.get("/api/v1/health")
        client.get("/api/v1/health")
        
        # Проверяем метрики
        response = client.get("/api/v1/metrics", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        metrics = response.json()
        assert "request_count" in metrics
        assert "response_time" in metrics
        assert "error_rate" in metrics
    
    def test_monitoring_alerts(self, client: TestClient, admin_token: str):
        """Тест системы мониторинга и алертов"""
        
        # Получаем статус мониторинга
        response = client.get("/api/v1/monitoring/status", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        monitoring_status = response.json()
        assert "alerts" in monitoring_status
        assert "system_health" in monitoring_status


class TestE2EDataIntegrity:
    """E2E тесты для целостности данных"""
    
    @pytest.mark.asyncio
    async def test_data_consistency(self, client: TestClient, db_session: AsyncSession, admin_token: str):
        """Тест консистентности данных при сложных операциях"""
        
        # Создаем связанные данные
        city_data = {"name": "Город для консистентности"}
        response = client.post("/api/v1/cities", json=city_data, headers={"Authorization": f"Bearer {admin_token}"})
        city_id = response.json()["id"]
        
        # Создаем несколько связанных записей
        for i in range(5):
            master_data = {
                "city_id": city_id,
                "full_name": f"Мастер {i}",
                "phone_number": f"+799900000{i}",
                "login": f"master_{i}",
                "password": "password123"
            }
            response = client.post("/api/v1/masters", json=master_data, headers={"Authorization": f"Bearer {admin_token}"})
            assert response.status_code == 201
        
        # Проверяем, что все мастера связаны с городом
        response = client.get(f"/api/v1/masters?city_id={city_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200
        masters = response.json()
        assert len(masters) == 5
        assert all(m["city_id"] == city_id for m in masters)
        
        # Попытка удалить город с связанными данными должна быть заблокирована
        response = client.delete(f"/api/v1/cities/{city_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code in [400, 409]  # Конфликт или Bad Request
        
        # Удаляем всех мастеров
        for master in masters:
            response = client.delete(f"/api/v1/masters/{master['id']}", headers={"Authorization": f"Bearer {admin_token}"})
            assert response.status_code == 200
        
        # Теперь можем удалить город
        response = client.delete(f"/api/v1/cities/{city_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == 200 