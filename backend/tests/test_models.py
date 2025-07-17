import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    City, Role, Master, Employee, Administrator, 
    Request, Transaction, RequestType, Direction, 
    AdvertisingCampaign, TransactionType, File
)


@pytest.mark.asyncio
class TestCityModel:
    """Тесты модели City"""
    
    async def test_create_city(self, db_session: AsyncSession):
        """Тест создания города"""
        city = City(name="Москва")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        assert city.id is not None
        assert city.name == "Москва"
    
    async def test_city_unique_name(self, db_session: AsyncSession):
        """Тест уникальности имени города"""
        city1 = City(name="Санкт-Петербург")
        city2 = City(name="Санкт-Петербург")
        
        db_session.add(city1)
        await db_session.commit()
        
        db_session.add(city2)
        
        # Должно вызвать ошибку уникальности
        with pytest.raises(Exception):
            await db_session.commit()


@pytest.mark.asyncio
class TestRoleModel:
    """Тесты модели Role"""
    
    async def test_create_role(self, db_session: AsyncSession):
        """Тест создания роли"""
        role = Role(name="manager")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        assert role.id is not None
        assert role.name == "manager"
    
    async def test_role_unique_name(self, db_session: AsyncSession):
        """Тест уникальности имени роли"""
        role1 = Role(name="admin")
        role2 = Role(name="admin")
        
        db_session.add(role1)
        await db_session.commit()
        
        db_session.add(role2)
        
        with pytest.raises(Exception):
            await db_session.commit()


@pytest.mark.asyncio
class TestMasterModel:
    """Тесты модели Master"""
    
    async def test_create_master(self, db_session: AsyncSession):
        """Тест создания мастера"""
        # Создаем город
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        # Создаем мастера
        master = Master(
            city_id=city.id,
            full_name="Иван Иванов",
            phone_number="+79991234567",
            birth_date=date(1990, 1, 1),
            passport="1234567890",
            login="ivan_master",
            password_hash="hashed_password",
            notes="Тестовые заметки"
        )
        db_session.add(master)
        await db_session.commit()
        await db_session.refresh(master)
        
        assert master.id is not None
        assert master.full_name == "Иван Иванов"
        assert master.phone_number == "+79991234567"
        assert master.status == "active"  # Значение по умолчанию
        assert master.city_id == city.id
        assert master.created_at is not None
    
    async def test_master_unique_login(self, db_session: AsyncSession):
        """Тест уникальности логина мастера"""
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        master1 = Master(
            city_id=city.id,
            full_name="Мастер 1",
            phone_number="+79991234567",
            login="unique_login",
            password_hash="hash1"
        )
        
        master2 = Master(
            city_id=city.id,
            full_name="Мастер 2",
            phone_number="+79991234568",
            login="unique_login",
            password_hash="hash2"
        )
        
        db_session.add(master1)
        await db_session.commit()
        
        db_session.add(master2)
        
        with pytest.raises(Exception):
            await db_session.commit()


@pytest.mark.asyncio
class TestEmployeeModel:
    """Тесты модели Employee"""
    
    async def test_create_employee(self, db_session: AsyncSession):
        """Тест создания сотрудника"""
        # Создаем роль
        role = Role(name="callcenter")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        # Создаем город
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        # Создаем сотрудника
        employee = Employee(
            name="Анна Петрова",
            role_id=role.id,
            city_id=city.id,
            login="anna_employee",
            password_hash="hashed_password",
            notes="Тестовые заметки"
        )
        db_session.add(employee)
        await db_session.commit()
        await db_session.refresh(employee)
        
        assert employee.id is not None
        assert employee.name == "Анна Петрова"
        assert employee.role_id == role.id
        assert employee.city_id == city.id
        assert employee.status == "active"
        assert employee.created_at is not None


@pytest.mark.asyncio
class TestRequestModel:
    """Тесты модели Request"""
    
    async def test_create_request(self, db_session: AsyncSession):
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
        
        # Создаем заявку
        request = Request(
            city_id=city.id,
            request_type_id=request_type.id,
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
        assert request.client_phone == "+79991234567"
        assert request.client_name == "Тестовый клиент"
        assert request.status == "new"  # Значение по умолчанию
        assert request.result == Decimal("1500.00")
        assert request.created_at is not None
        assert request.updated_at is None  # Устанавливается только при обновлении


@pytest.mark.asyncio
class TestTransactionModel:
    """Тесты модели Transaction"""
    
    async def test_create_transaction(self, db_session: AsyncSession):
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
        
        # Создаем транзакцию
        transaction = Transaction(
            city_id=city.id,
            transaction_type_id=transaction_type.id,
            amount=Decimal("5000.00"),
            notes="Тестовая транзакция",
            specified_date=date.today(),
            payment_reason="Оплата за услуги"
        )
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.amount == Decimal("5000.00")
        assert transaction.notes == "Тестовая транзакция"
        assert transaction.specified_date == date.today()
        assert transaction.created_at is not None


@pytest.mark.asyncio
class TestFileModel:
    """Тесты модели File"""
    
    async def test_create_file_for_request(self, db_session: AsyncSession):
        """Тест создания файла для заявки"""
        # Создаем заявку
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        request_type = RequestType(name="Ремонт")
        db_session.add(request_type)
        await db_session.commit()
        await db_session.refresh(request_type)
        
        request = Request(
            city_id=city.id,
            request_type_id=request_type.id,
            client_phone="+79991234567"
        )
        db_session.add(request)
        await db_session.commit()
        await db_session.refresh(request)
        
        # Создаем файл для заявки
        file = File(
            request_id=request.id,
            file_type="bso",
            file_path="/media/test/file.jpg"
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)
        
        assert file.id is not None
        assert file.request_id == request.id
        assert file.transaction_id is None
        assert file.file_type == "bso"
        assert file.uploaded_at is not None
    
    async def test_file_constraint_violation(self, db_session: AsyncSession):
        """Тест нарушения ограничения файла (должна быть связь только с одной сущностью)"""
        # Создаем файл с обеими связями - это должно вызвать ошибку
        file = File(
            request_id=1,
            transaction_id=1,
            file_type="bso",
            file_path="/media/test/file.jpg"
        )
        db_session.add(file)
        
        with pytest.raises(Exception):
            await db_session.commit()


# Вспомогательные модели для тестов
@pytest.mark.asyncio
class TestHelperModels:
    """Тесты вспомогательных моделей"""
    
    async def test_create_request_type(self, db_session: AsyncSession):
        """Тест создания типа заявки"""
        request_type = RequestType(name="Установка")
        db_session.add(request_type)
        await db_session.commit()
        await db_session.refresh(request_type)
        
        assert request_type.id is not None
        assert request_type.name == "Установка"
    
    async def test_create_direction(self, db_session: AsyncSession):
        """Тест создания направления"""
        direction = Direction(name="Кондиционеры")
        db_session.add(direction)
        await db_session.commit()
        await db_session.refresh(direction)
        
        assert direction.id is not None
        assert direction.name == "Кондиционеры"
    
    async def test_create_advertising_campaign(self, db_session: AsyncSession):
        """Тест создания рекламной кампании"""
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        campaign = AdvertisingCampaign(
            city_id=city.id,
            name="Тестовая кампания",
            description="Описание кампании",
            budget=Decimal("10000.00"),
            start_date=date.today(),
            end_date=date.today()
        )
        db_session.add(campaign)
        await db_session.commit()
        await db_session.refresh(campaign)
        
        assert campaign.id is not None
        assert campaign.name == "Тестовая кампания"
        assert campaign.budget == Decimal("10000.00")
    
    async def test_create_transaction_type(self, db_session: AsyncSession):
        """Тест создания типа транзакции"""
        transaction_type = TransactionType(name="Расход")
        db_session.add(transaction_type)
        await db_session.commit()
        await db_session.refresh(transaction_type)
        
        assert transaction_type.id is not None
        assert transaction_type.name == "Расход" 