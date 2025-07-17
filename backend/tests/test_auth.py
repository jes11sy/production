import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.core.models import Master, Employee, Administrator, Role, City


class TestPasswordHashing:
    """Тесты хеширования паролей"""
    
    def test_password_hashing(self):
        """Тест хеширования и проверки пароля"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Тест что один пароль дает разные хеши"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Тесты JWT токенов"""
    
    def test_create_access_token(self):
        """Тест создания JWT токена"""
        data = {"sub": "testuser", "user_type": "master"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_expiration(self):
        """Тест создания токена с кастомным временем жизни"""
        from datetime import timedelta
        data = {"sub": "testuser", "user_type": "master"}
        token = create_access_token(data, expires_delta=timedelta(minutes=15))
        
        assert token is not None
        assert isinstance(token, str)


@pytest.mark.asyncio
class TestUserAuthentication:
    """Тесты аутентификации пользователей"""
    
    async def test_authenticate_master(self, db_session: AsyncSession):
        """Тест аутентификации мастера"""
        from app.core.auth import authenticate_user
        
        # Создаем тестовый город
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        # Создаем тестового мастера
        password = "test_password_123"
        hashed_password = get_password_hash(password)
        
        master = Master(
            city_id=city.id,
            full_name="Тестовый мастер",
            phone_number="+79991234567",
            login="test_master",
            password_hash=hashed_password
        )
        db_session.add(master)
        await db_session.commit()
        
        # Тестируем аутентификацию
        authenticated_user = await authenticate_user("test_master", password, db_session)
        assert authenticated_user is not None
        assert authenticated_user.login == "test_master"
        assert isinstance(authenticated_user, Master)
        
        # Тестируем неправильный пароль
        wrong_auth = await authenticate_user("test_master", "wrong_password", db_session)
        assert wrong_auth is None
    
    async def test_authenticate_employee(self, db_session: AsyncSession):
        """Тест аутентификации сотрудника"""
        from app.core.auth import authenticate_user
        
        # Создаем тестовую роль
        role = Role(name="callcenter")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)
        
        # Создаем тестового сотрудника
        password = "employee_password_123"
        hashed_password = get_password_hash(password)
        
        employee = Employee(
            name="Тестовый сотрудник",
            role_id=role.id,
            login="test_employee",
            password_hash=hashed_password
        )
        db_session.add(employee)
        await db_session.commit()
        
        # Тестируем аутентификацию
        authenticated_user = await authenticate_user("test_employee", password, db_session)
        assert authenticated_user is not None
        assert authenticated_user.login == "test_employee"
        assert isinstance(authenticated_user, Employee)
    
    async def test_authenticate_nonexistent_user(self, db_session: AsyncSession):
        """Тест аутентификации несуществующего пользователя"""
        from app.core.auth import authenticate_user
        
        result = await authenticate_user("nonexistent_user", "password", db_session)
        assert result is None


@pytest.mark.asyncio
class TestAuthAPI:
    """Тесты API аутентификации"""
    
    async def test_login_endpoint(self, client: TestClient, db_session: AsyncSession):
        """Тест эндпоинта входа"""
        # Создаем тестовый город и мастера
        city = City(name="Тестовый город")
        db_session.add(city)
        await db_session.commit()
        await db_session.refresh(city)
        
        password = "test_password_123"
        hashed_password = get_password_hash(password)
        
        master = Master(
            city_id=city.id,
            full_name="Тестовый мастер",
            phone_number="+79991234567",
            login="test_master",
            password_hash=hashed_password
        )
        db_session.add(master)
        await db_session.commit()
        
        # Тестируем успешный вход
        response = client.post("/api/v1/auth/login", json={
            "login": "test_master",
            "password": password
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "master"
    
    async def test_login_wrong_credentials(self, client: TestClient):
        """Тест входа с неправильными данными"""
        response = client.post("/api/v1/auth/login", json={
            "login": "wrong_user",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    async def test_logout_endpoint(self, client: TestClient):
        """Тест эндпоинта выхода"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Successfully logged out" 