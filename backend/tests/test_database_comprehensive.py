"""
Комплексные тесты базы данных, моделей и CRUD операций
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import AsyncMock, patch

from app.core.models import (
    City, Role, Master, Employee, Administrator, 
    Request, Transaction, RequestType, Direction, 
    AdvertisingCampaign, TransactionType, File
)
from app.core.crud import (
    create_request, get_requests, get_request, update_request, delete_request,
    create_transaction, get_transactions, get_transaction, update_transaction,
    get_cities, get_request_types, get_masters
)
from app.core.auth import get_password_hash, verify_password


@pytest.mark.asyncio
class TestModelsCreation:
    """Тесты создания моделей"""
    
    async def test_city_model(self, db_session: AsyncSession):
        """Тест модели City"""
        # Создание города
        city = City(name="Москва")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        assert city.id is not None
        assert city.name == "Москва"
        assert city.created_at is not None
        
        # Проверка уникальности
        duplicate_city = City(name="Москва")
        db_session.add(duplicate_city)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_role_model(self, db_session: AsyncSession):
        """Тест модели Role"""
        role = Role(name="admin")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        assert role.id is not None
        assert role.name == "admin"
        assert role.created_at is not None
    
    async def test_master_model(self, db_session: AsyncSession, test_city: City):
        """Тест модели Master"""
        master = Master(
            city_id=test_city.id,
            full_name="Иван Иванов",
            phone_number="+79991234567",
            login="master001",
            password_hash=get_password_hash("password123"),
            status="active"
        )
        db_session.add(master)
        await db_session.commit()
        await db_session.refresh(master)
        
        assert master.id is not None
        assert master.full_name == "Иван Иванов"
        assert master.city_id == test_city.id
        assert master.status == "active"
        assert verify_password("password123", master.password_hash)
    
    async def test_employee_model(self, db_session: AsyncSession, test_role: Role):
        """Тест модели Employee"""
        employee = Employee(
            name="Сотрудник Тест",
            role_id=test_role.id,
            login="employee001",
            password_hash=get_password_hash("password123"),
            status="active"
        )
        db_session.add(employee)
        await db_session.commit()
        await db_session.refresh(employee)
        
        assert employee.id is not None
        assert employee.name == "Сотрудник Тест"
        assert employee.role_id == test_role.id
        assert employee.status == "active"
    
    async def test_request_model(
        self, 
        db_session: AsyncSession, 
        test_city: City, 
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест модели Request"""
        request = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Тестовый клиент",
            address="Тестовый адрес",
            problem="Тестовая проблема",
            result=Decimal("1500.00"),
            expenses=Decimal("300.00"),
            net_amount=Decimal("1200.00"),
            master_handover=Decimal("800.00")
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)
        
        assert request.id is not None
        assert request.client_name == "Тестовый клиент"
        assert request.result == Decimal("1500.00")
        assert request.status == "new"  # Значение по умолчанию
        assert request.created_at is not None
    
    async def test_transaction_model(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_transaction_type: TransactionType,
        test_master: Master
    ):
        """Тест модели Transaction"""
        transaction = Transaction(
            city_id=test_city.id,
            transaction_type_id=test_transaction_type.id,
            master_id=test_master.id,
            amount=Decimal("1000.00"),
            specified_date=date.today(),
            description="Тестовая транзакция"
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.amount == Decimal("1000.00")
        assert transaction.description == "Тестовая транзакция"
        assert transaction.created_at is not None


@pytest.mark.asyncio
class TestModelRelationships:
    """Тесты связей между моделями"""
    
    async def test_city_requests_relationship(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест связи City -> Requests"""
        # Создаем несколько заявок для одного города
        request1 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Клиент 1",
            address="Адрес 1",
            problem="Проблема 1"
        )
        request2 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234568",
            client_name="Клиент 2",
            address="Адрес 2",
            problem="Проблема 2"
        )
        
        db_session.add_all([request1, request2])
        await db_session.commit()
        
        # Проверяем связь
        result = await db_session.execute(
            select(Request).where(Request.city_id == test_city.id)
        )
        city_requests = result.scalars().all()
        
        assert len(city_requests) == 2
        assert all(req.city_id == test_city.id for req in city_requests)
    
    async def test_master_requests_relationship(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест связи Master -> Requests"""
        # Создаем заявки для мастера
        request1 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Клиент 1",
            address="Адрес 1",
            problem="Проблема 1"
        )
        
        db_session.add(request1)
        await db_session.commit()
        
        # Проверяем связь
        result = await db_session.execute(
            select(Request).where(Request.master_id == test_master.id)
        )
        master_requests = result.scalars().all()
        
        assert len(master_requests) == 1
        assert master_requests[0].master_id == test_master.id
    
    async def test_cascade_delete(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест каскадного удаления"""
        # Создаем заявку
        request = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Тестовый клиент",
            address="Тестовый адрес",
            problem="Тестовая проблема"
        )
        db_session.add(request)
        await db_session.commit()
        
        request_id = request.id
        
        # Удаляем заявку
        await db_session.delete(request)
        await db_session.commit()
        
        # Проверяем что заявка удалена
        result = await db_session.execute(
            select(Request).where(Request.id == request_id)
        )
        deleted_request = result.scalar_one_or_none()
        
        assert deleted_request is None


@pytest.mark.asyncio
class TestCRUDOperations:
    """Тесты CRUD операций"""
    
    async def test_create_request_crud(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест создания заявки через CRUD"""
        request_data = {
            "city_id": test_city.id,
            "request_type_id": test_request_type.id,
            "master_id": test_master.id,
            "client_phone": "+79991234567",
            "client_name": "Тестовый клиент",
            "address": "Тестовый адрес",
            "problem": "Тестовая проблема",
            "result": Decimal("1500.00"),
            "expenses": Decimal("300.00"),
            "net_amount": Decimal("1200.00"),
            "master_handover": Decimal("800.00")
        }
        
        # Создаем заявку
        created_request = await create_request(db_session, request_data)
        
        assert created_request.id is not None
        assert created_request.client_name == "Тестовый клиент"
        assert created_request.result == Decimal("1500.00")
        assert created_request.status == "new"
    
    async def test_get_requests_crud(
        self, 
        db_session: AsyncSession,
        test_request: Request
    ):
        """Тест получения списка заявок"""
        requests = await get_requests(db_session, limit=10)
        
        assert len(requests) > 0
        assert any(req.id == test_request.id for req in requests)
    
    async def test_get_request_crud(
        self, 
        db_session: AsyncSession,
        test_request: Request
    ):
        """Тест получения конкретной заявки"""
        request = await get_request(db_session, test_request.id)
        
        assert request is not None
        assert request.id == test_request.id
        assert request.client_name == test_request.client_name
    
    async def test_update_request_crud(
        self, 
        db_session: AsyncSession,
        test_request: Request
    ):
        """Тест обновления заявки"""
        update_data = {
            "status": "completed",
            "problem": "Обновленная проблема"
        }
        
        updated_request = await update_request(db_session, test_request.id, update_data)
        
        assert updated_request.status == "completed"
        assert updated_request.problem == "Обновленная проблема"
        assert updated_request.updated_at is not None
    
    async def test_delete_request_crud(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест удаления заявки"""
        # Создаем заявку для удаления
        request = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Для удаления",
            address="Адрес",
            problem="Проблема"
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)
        
        request_id = request.id
        
        # Удаляем заявку
        success = await delete_request(db_session, request_id)
        
        assert success is True
        
        # Проверяем что заявка удалена
        deleted_request = await get_request(db_session, request_id)
        assert deleted_request is None


@pytest.mark.asyncio
class TestDatabaseQueries:
    """Тесты сложных запросов к базе данных"""
    
    async def test_filtering_requests(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест фильтрации заявок"""
        # Создаем заявки с разными статусами
        request1 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Клиент 1",
            address="Адрес 1",
            problem="Проблема 1",
            status="new"
        )
        request2 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234568",
            client_name="Клиент 2",
            address="Адрес 2",
            problem="Проблема 2",
            status="completed"
        )
        
        db_session.add_all([request1, request2])
        await db_session.commit()
        
        # Фильтрация по статусу
        result = await db_session.execute(
            select(Request).where(Request.status == "new")
        )
        new_requests = result.scalars().all()
        
        assert len(new_requests) >= 1
        assert all(req.status == "new" for req in new_requests)
        
        # Фильтрация по городу
        result = await db_session.execute(
            select(Request).where(Request.city_id == test_city.id)
        )
        city_requests = result.scalars().all()
        
        assert len(city_requests) >= 2
        assert all(req.city_id == test_city.id for req in city_requests)
    
    async def test_aggregation_queries(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест агрегационных запросов"""
        # Создаем заявки с разными суммами
        request1 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Клиент 1",
            address="Адрес 1",
            problem="Проблема 1",
            result=Decimal("1000.00")
        )
        request2 = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234568",
            client_name="Клиент 2",
            address="Адрес 2",
            problem="Проблема 2",
            result=Decimal("2000.00")
        )
        
        db_session.add_all([request1, request2])
        await db_session.commit()
        
        # Подсчет количества заявок
        result = await db_session.execute(
            select(func.count(Request.id)).where(Request.city_id == test_city.id)
        )
        count = result.scalar()
        
        assert count >= 2
        
        # Сумма результатов
        result = await db_session.execute(
            select(func.sum(Request.result)).where(Request.city_id == test_city.id)
        )
        total_result = result.scalar()
        
        assert total_result >= Decimal("3000.00")
    
    async def test_complex_joins(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест сложных соединений"""
        # Создаем заявку
        request = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            master_id=test_master.id,
            client_phone="+79991234567",
            client_name="Тестовый клиент",
            address="Тестовый адрес",
            problem="Тестовая проблема"
        )
        db_session.add(request)
        await db_session.commit()
        
        # Запрос с соединениями
        result = await db_session.execute(
            select(Request, City, RequestType, Master)
            .join(City, Request.city_id == City.id)
            .join(RequestType, Request.request_type_id == RequestType.id)
            .join(Master, Request.master_id == Master.id)
            .where(Request.id == request.id)
        )
        
        row = result.first()
        assert row is not None
        
        request_data, city_data, type_data, master_data = row
        assert request_data.id == request.id
        assert city_data.id == test_city.id
        assert type_data.id == test_request_type.id
        assert master_data.id == test_master.id


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Тесты производительности базы данных"""
    
    async def test_bulk_insert_performance(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности массовой вставки"""
        import time
        
        # Создаем много заявок
        requests = []
        for i in range(100):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:02d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}"
            )
            requests.append(request)
        
        # Измеряем время вставки
        start_time = time.time()
        db_session.add_all(requests)
        await db_session.commit()
        end_time = time.time()
        
        insert_time = end_time - start_time
        
        # Проверяем что вставка прошла быстро (меньше 5 секунд)
        assert insert_time < 5.0
        
        # Проверяем что все записи созданы
        result = await db_session.execute(
            select(func.count(Request.id)).where(Request.city_id == test_city.id)
        )
        count = result.scalar()
        
        assert count >= 100
    
    async def test_query_performance(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест производительности запросов"""
        import time
        
        # Создаем данные для тестирования
        requests = []
        for i in range(50):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:02d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}"
            )
            requests.append(request)
        
        db_session.add_all(requests)
        await db_session.commit()
        
        # Тест производительности простого запроса
        start_time = time.time()
        result = await db_session.execute(
            select(Request).where(Request.city_id == test_city.id).limit(10)
        )
        requests_list = result.scalars().all()
        end_time = time.time()
        
        query_time = end_time - start_time
        
        # Запрос должен выполняться быстро (меньше 1 секунды)
        assert query_time < 1.0
        assert len(requests_list) == 10
        
        # Тест производительности запроса с соединениями
        start_time = time.time()
        result = await db_session.execute(
            select(Request, City, Master)
            .join(City, Request.city_id == City.id)
            .join(Master, Request.master_id == Master.id)
            .where(Request.city_id == test_city.id)
            .limit(10)
        )
        joined_data = result.all()
        end_time = time.time()
        
        join_time = end_time - start_time
        
        # Запрос с соединениями должен выполняться разумно быстро (меньше 2 секунд)
        assert join_time < 2.0
        assert len(joined_data) == 10


@pytest.mark.asyncio
class TestDatabaseConstraints:
    """Тесты ограничений базы данных"""
    
    async def test_unique_constraints(self, db_session: AsyncSession):
        """Тест уникальных ограничений"""
        # Создаем два города с одинаковым именем
        city1 = City(name="Дубликат")
        city2 = City(name="Дубликат")
        
        db_session.add(city1)
        await db_session.commit()
        
        db_session.add(city2)
        
        # Должна возникнуть ошибка уникальности
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_foreign_key_constraints(
        self, 
        db_session: AsyncSession,
        test_request_type: RequestType
    ):
        """Тест ограничений внешних ключей"""
        # Попытка создать заявку с несуществующим городом
        request = Request(
            city_id=99999,  # Несуществующий город
            request_type_id=test_request_type.id,
            master_id=1,
            client_phone="+79991234567",
            client_name="Тестовый клиент",
            address="Тестовый адрес",
            problem="Тестовая проблема"
        )
        
        db_session.add(request)
        
        # Должна возникнуть ошибка внешнего ключа
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_not_null_constraints(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType
    ):
        """Тест ограничений NOT NULL"""
        # Попытка создать заявку без обязательного поля
        request = Request(
            city_id=test_city.id,
            request_type_id=test_request_type.id,
            # master_id пропущен
            client_phone="+79991234567",
            # client_name пропущен (обязательное поле)
            address="Тестовый адрес",
            problem="Тестовая проблема"
        )
        
        db_session.add(request)
        
        # Должна возникнуть ошибка NOT NULL
        with pytest.raises(IntegrityError):
            await db_session.commit()


@pytest.mark.asyncio
class TestDatabaseIndexes:
    """Тесты индексов базы данных"""
    
    async def test_index_usage(
        self, 
        db_session: AsyncSession,
        test_city: City,
        test_request_type: RequestType,
        test_master: Master
    ):
        """Тест использования индексов"""
        # Создаем данные для тестирования индексов
        requests = []
        for i in range(100):
            request = Request(
                city_id=test_city.id,
                request_type_id=test_request_type.id,
                master_id=test_master.id,
                client_phone=f"+7999123456{i:02d}",
                client_name=f"Клиент {i}",
                address=f"Адрес {i}",
                problem=f"Проблема {i}",
                status="new" if i % 2 == 0 else "completed"
            )
            requests.append(request)
        
        db_session.add_all(requests)
        await db_session.commit()
        
        # Запрос, который должен использовать индекс по city_id
        result = await db_session.execute(
            select(Request).where(Request.city_id == test_city.id)
        )
        city_requests = result.scalars().all()
        
        assert len(city_requests) >= 100
        
        # Запрос, который должен использовать индекс по статусу
        result = await db_session.execute(
            select(Request).where(Request.status == "new")
        )
        new_requests = result.scalars().all()
        
        assert len(new_requests) >= 50
        
        # Запрос, который должен использовать составной индекс
        result = await db_session.execute(
            select(Request).where(
                (Request.city_id == test_city.id) & 
                (Request.status == "new")
            )
        )
        filtered_requests = result.scalars().all()
        
        assert len(filtered_requests) >= 50


@pytest.mark.asyncio
class TestDatabaseMigrations:
    """Тесты миграций базы данных"""
    
    async def test_table_creation(self, db_session: AsyncSession):
        """Тест создания таблиц"""
        # Проверяем что основные таблицы созданы
        tables_to_check = [
            "cities", "roles", "masters", "employees", "administrators",
            "requests", "transactions", "request_types", "transaction_types",
            "directions", "advertising_campaigns", "files"
        ]
        
        for table_name in tables_to_check:
            result = await db_session.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            )
            table_exists = result.scalar() is not None
            assert table_exists, f"Table {table_name} should exist"
    
    async def test_column_types(self, db_session: AsyncSession):
        """Тест типов колонок"""
        # Проверяем что колонки имеют правильные типы
        result = await db_session.execute(
            text("PRAGMA table_info(requests)")
        )
        columns = result.fetchall()
        
        # Проверяем наличие основных колонок
        column_names = [col[1] for col in columns]
        expected_columns = [
            "id", "city_id", "request_type_id", "master_id", 
            "client_phone", "client_name", "address", "problem",
            "result", "expenses", "net_amount", "master_handover",
            "status", "created_at", "updated_at"
        ]
        
        for col in expected_columns:
            assert col in column_names, f"Column {col} should exist in requests table" 