import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text
from unittest.mock import AsyncMock, MagicMock
import os
from decimal import Decimal
from datetime import datetime, date

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.models import (
    City, Role, Master, Employee, Administrator, 
    Request, Transaction, RequestType, Direction, 
    AdvertisingCampaign, TransactionType, File
)
from app.core.auth import get_password_hash
from app.main import app

# Создаем тестовую базу данных в памяти
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False  # Отключаем логирование для тестов
)

TestingSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всей сессии тестирования"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает сессию базы данных для тестирования"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Очищаем базу данных после каждого теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Создает тестового клиента FastAPI"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def authenticated_client(db_session: AsyncSession):
    """Создает аутентифицированного клиента"""
    # Создаем тестового пользователя
    role = Role(name="callcenter")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    
    employee = Employee(
        name="Test User",
        phone="1234567890",
        role_id=role.id,
        password_hash=get_password_hash("testpassword")
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    
    # Переопределяем зависимость базы данных
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        # Получаем токен
        response = test_client.post("/auth/token", data={
            "username": "1234567890",
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        
        # Устанавливаем заголовок авторизации
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_city(db_session: AsyncSession):
    """Создает тестовый город"""
    city = City(name="Тестовый город")
    db_session.add(city)
    await db_session.commit()
    await db_session.refresh(city)
    return city


@pytest.fixture
async def test_role(db_session: AsyncSession):
    """Создает тестовую роль"""
    role = Role(name="callcenter")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_admin_role(db_session: AsyncSession):
    """Создает роль администратора"""
    role = Role(name="admin")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_master_role(db_session: AsyncSession):
    """Создает роль мастера"""
    role = Role(name="master")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_request_type(db_session: AsyncSession):
    """Создает тестовый тип заявки"""
    request_type = RequestType(
        name="Тестовый тип",
        description="Описание тестового типа",
        price=Decimal("100.00")
    )
    db_session.add(request_type)
    await db_session.commit()
    await db_session.refresh(request_type)
    return request_type


@pytest.fixture
async def test_direction(db_session: AsyncSession):
    """Создает тестовое направление"""
    direction = Direction(name="Тестовое направление")
    db_session.add(direction)
    await db_session.commit()
    await db_session.refresh(direction)
    return direction


@pytest.fixture
async def test_advertising_campaign(db_session: AsyncSession):
    """Создает тестовую рекламную кампанию"""
    campaign = AdvertisingCampaign(
        name="Тестовая кампания",
        description="Описание тестовой кампании",
        budget=Decimal("1000.00"),
        start_date=date.today(),
        end_date=date.today()
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


@pytest.fixture
async def test_transaction_type(db_session: AsyncSession):
    """Создает тестовый тип транзакции"""
    transaction_type = TransactionType(
        name="Тестовый тип транзакции",
        description="Описание тестового типа транзакции"
    )
    db_session.add(transaction_type)
    await db_session.commit()
    await db_session.refresh(transaction_type)
    return transaction_type


@pytest.fixture
async def test_employee(db_session: AsyncSession, test_role: Role):
    """Создает тестового сотрудника"""
    employee = Employee(
        name="Тестовый сотрудник",
        phone="1234567890",
        role_id=test_role.id,
        password_hash=get_password_hash("testpassword")
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    return employee


@pytest.fixture
async def test_administrator(db_session: AsyncSession, test_admin_role: Role):
    """Создает тестового администратора"""
    admin = Administrator(
        name="Тестовый администратор",
        phone="0987654321",
        role_id=test_admin_role.id,
        password_hash=get_password_hash("adminpassword")
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def test_master(db_session: AsyncSession, test_master_role: Role, test_city: City):
    """Создает тестового мастера"""
    master = Master(
        name="Тестовый мастер",
        phone="1111111111",
        role_id=test_master_role.id,
        password_hash=get_password_hash("masterpassword"),
        city_id=test_city.id
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)
    return master


@pytest.fixture
async def test_request(
    db_session: AsyncSession,
    test_city: City,
    test_request_type: RequestType,
    test_direction: Direction,
    test_advertising_campaign: AdvertisingCampaign,
    test_employee: Employee
):
    """Создает тестовую заявку"""
    request = Request(
        client_name="Тестовый клиент",
        client_phone="2222222222",
        city_id=test_city.id,
        request_type_id=test_request_type.id,
        direction_id=test_direction.id,
        advertising_campaign_id=test_advertising_campaign.id,
        employee_id=test_employee.id,
        meeting_date=datetime.now(),
        address="Тестовый адрес",
        description="Тестовое описание",
        status="new"
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    return request


@pytest.fixture
async def test_transaction(
    db_session: AsyncSession,
    test_request: Request,
    test_transaction_type: TransactionType
):
    """Создает тестовую транзакцию"""
    transaction = Transaction(
        request_id=test_request.id,
        transaction_type_id=test_transaction_type.id,
        amount=Decimal("100.00"),
        description="Тестовая транзакция"
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


@pytest.fixture
async def test_file(db_session: AsyncSession, test_request: Request):
    """Создает тестовый файл"""
    file = File(
        filename="test.txt",
        file_path="/test/path/test.txt",
        file_type="text/plain",
        file_size=1024,
        request_id=test_request.id
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file


# Моки для внешних сервисов
@pytest.fixture
def mock_redis():
    """Мок для Redis"""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_email_service():
    """Мок для email сервиса"""
    mock = MagicMock()
    mock.send_email = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_file_service():
    """Мок для файлового сервиса"""
    mock = MagicMock()
    mock.save_file = AsyncMock(return_value="/test/path/file.txt")
    mock.delete_file = AsyncMock(return_value=True)
    mock.get_file_info = AsyncMock(return_value={
        "size": 1024,
        "type": "text/plain"
    })
    return mock


# Настройка для отключения логирования в тестах
@pytest.fixture(autouse=True)
def disable_logging():
    """Отключает логирование в тестах"""
    import logging
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# Настройка переменных окружения для тестов
@pytest.fixture(autouse=True)
def setup_test_env():
    """Настраивает переменные окружения для тестов"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["LOG_TO_FILE"] = "false"
    os.environ["ENABLE_MONITORING"] = "false"
    os.environ["CACHE_ENABLED"] = "false"
    yield
    # Очищаем переменные после тестов
    for key in ["ENVIRONMENT", "LOG_TO_FILE", "ENABLE_MONITORING", "CACHE_ENABLED"]:
        if key in os.environ:
            del os.environ[key] 