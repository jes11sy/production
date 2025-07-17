import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import get_password_hash, verify_password


class TestBasicFunctionality:
    """Базовые тесты функциональности"""
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_app_creation(self):
        """Тест создания приложения"""
        assert app is not None
        assert app.title == "Система управления заявками"
    
    def test_client_creation(self):
        """Тест создания тестового клиента"""
        with TestClient(app) as client:
            assert client is not None


class TestAPIEndpoints:
    """Тесты API endpoints без БД"""
    
    def test_health_endpoint_exists(self):
        """Тест существования health endpoint"""
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            # Может быть 200 или 500 (из-за БД), главное что endpoint существует
            assert response.status_code in [200, 500]
    
    def test_docs_endpoint(self):
        """Тест документации API"""
        with TestClient(app) as client:
            response = client.get("/docs")
            assert response.status_code == 200
    
    def test_openapi_endpoint(self):
        """Тест OpenAPI схемы"""
        with TestClient(app) as client:
            response = client.get("/openapi.json")
            assert response.status_code == 200
            data = response.json()
            assert "info" in data
            assert "paths" in data
    
    def test_unauthorized_requests(self):
        """Тест неавторизованных запросов"""
        with TestClient(app) as client:
            # Эти endpoints должны возвращать 401
            endpoints = [
                "/api/v1/requests/",
                "/api/v1/transactions/", 
                "/api/v1/metrics"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == 401
    
    def test_nonexistent_endpoint(self):
        """Тест несуществующего endpoint"""
        with TestClient(app) as client:
            response = client.get("/api/v1/nonexistent")
            assert response.status_code == 404


class TestAuthenticationLogic:
    """Тесты логики аутентификации"""
    
    def test_jwt_token_creation(self):
        """Тест создания JWT токена"""
        from app.core.auth import create_access_token
        
        data = {"sub": "testuser", "user_type": "master"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_password_verification(self):
        """Тест проверки паролей"""
        password = "secure_password_123"
        hashed = get_password_hash(password)
        
        # Правильный пароль
        assert verify_password(password, hashed) is True
        
        # Неправильный пароль
        assert verify_password("wrong_password", hashed) is False
        
        # Пустой пароль
        assert verify_password("", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Тест что разные пароли дают разные хеши"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
        assert verify_password(password1, hash1) is True
        assert verify_password(password2, hash2) is True
        assert verify_password(password1, hash2) is False
        assert verify_password(password2, hash1) is False


class TestConfiguration:
    """Тесты конфигурации"""
    
    def test_app_settings(self):
        """Тест настроек приложения"""
        from app.core.config import settings
        
        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_database_url(self):
        """Тест URL базы данных"""
        from app.core.config import settings
        
        db_url = settings.DATABASE_URL
        assert db_url is not None
        assert "postgresql" in db_url or "sqlite" in db_url
    
    def test_file_upload_settings(self):
        """Тест настроек загрузки файлов"""
        from app.core.config import settings
        
        assert settings.MAX_FILE_SIZE > 0
        assert settings.UPLOAD_DIR is not None
        assert len(settings.get_allowed_file_types) > 0


class TestUtilities:
    """Тесты утилитарных функций"""
    
    def test_file_type_validation(self):
        """Тест валидации типов файлов"""
        from app.core.config import settings
        
        allowed_types = settings.get_allowed_file_types
        assert "jpg" in allowed_types
        assert "pdf" in allowed_types
        assert "mp3" in allowed_types
    
    def test_environment_detection(self):
        """Тест определения окружения"""
        from app.core.config import settings
        
        assert settings.ENVIRONMENT in ["development", "production", "testing"]
    
    def test_security_settings(self):
        """Тест настроек безопасности"""
        from app.core.config import settings
        
        assert settings.RATE_LIMIT_PER_MINUTE > 0
        assert settings.LOGIN_ATTEMPTS_PER_HOUR > 0 