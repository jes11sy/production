"""
Комплексные тесты системы безопасности
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, MagicMock, AsyncMock
import time
from datetime import datetime, timedelta
import jwt

from app.core.security import (
    CSRFProtection, LoginAttemptTracker, sanitize_output,
    SecurityHeadersMiddleware, RequestSizeLimitMiddleware
)
from app.core.auth import (
    create_access_token, verify_token, get_password_hash, 
    verify_password, authenticate_user
)
from app.core.models import Employee, Master, Administrator


@pytest.mark.asyncio
class TestCSRFProtection:
    """Тесты CSRF защиты"""
    
    async def test_csrf_token_generation(self):
        """Тест генерации CSRF токенов"""
        csrf_protection = CSRFProtection()
        
        # Генерируем токен
        token = csrf_protection.generate_csrf_token("test_session")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Проверяем что токены разные для разных сессий
        token2 = csrf_protection.generate_csrf_token("test_session2")
        assert token != token2
    
    async def test_csrf_token_validation(self):
        """Тест валидации CSRF токенов"""
        csrf_protection = CSRFProtection()
        
        # Генерируем и валидируем токен
        token = csrf_protection.generate_csrf_token("test_session")
        is_valid = csrf_protection.validate_csrf_token(token, "test_session")
        
        assert is_valid is True
        
        # Проверяем невалидный токен
        is_valid = csrf_protection.validate_csrf_token("invalid_token", "test_session")
        assert is_valid is False
        
        # Проверяем токен для другой сессии
        is_valid = csrf_protection.validate_csrf_token(token, "other_session")
        assert is_valid is False
    
    async def test_csrf_token_expiration(self):
        """Тест истечения CSRF токенов"""
        csrf_protection = CSRFProtection()
        
        # Генерируем токен
        token = csrf_protection.generate_csrf_token("test_session")
        
        # Проверяем что токен валиден
        assert csrf_protection.validate_csrf_token(token, "test_session") is True
        
        # Имитируем истечение времени
        with patch('time.time', return_value=time.time() + 3700):  # +1 час
            assert csrf_protection.validate_csrf_token(token, "test_session") is False
    
    async def test_csrf_endpoint(self, client: TestClient):
        """Тест API эндпоинта для получения CSRF токена"""
        response = client.get("/api/v1/auth/csrf-token")
        
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert isinstance(data["csrf_token"], str)
        assert len(data["csrf_token"]) > 0


@pytest.mark.asyncio
class TestLoginAttemptTracker:
    """Тесты отслеживания попыток входа"""
    
    async def test_record_login_attempt(self):
        """Тест записи попыток входа"""
        tracker = LoginAttemptTracker()
        
        # Записываем успешную попытку
        tracker.record_login_attempt("test_user", "192.168.1.1", True)
        
        # Записываем неуспешную попытку
        tracker.record_login_attempt("test_user", "192.168.1.1", False)
        
        # Проверяем что попытки записаны
        attempts = tracker.get_login_attempts("test_user")
        assert len(attempts) == 2
        
        # Проверяем данные попыток
        assert attempts[0]["success"] is True
        assert attempts[1]["success"] is False
        assert attempts[0]["ip_address"] == "192.168.1.1"
    
    async def test_account_lockout(self):
        """Тест блокировки аккаунта"""
        tracker = LoginAttemptTracker()
        
        # Записываем 5 неуспешных попыток
        for i in range(5):
            tracker.record_login_attempt("test_user", "192.168.1.1", False)
        
        # Проверяем что аккаунт заблокирован
        is_locked = tracker.is_account_locked("test_user")
        assert is_locked is True
        
        # Проверяем что успешный вход разблокирует аккаунт
        tracker.record_login_attempt("test_user", "192.168.1.1", True)
        is_locked = tracker.is_account_locked("test_user")
        assert is_locked is False
    
    async def test_lockout_expiration(self):
        """Тест истечения блокировки"""
        tracker = LoginAttemptTracker()
        
        # Записываем 5 неуспешных попыток
        for i in range(5):
            tracker.record_login_attempt("test_user", "192.168.1.1", False)
        
        assert tracker.is_account_locked("test_user") is True
        
        # Имитируем истечение времени блокировки
        with patch('time.time', return_value=time.time() + 1900):  # +30 минут
            assert tracker.is_account_locked("test_user") is False
    
    async def test_get_failed_attempts_count(self):
        """Тест подсчета неуспешных попыток"""
        tracker = LoginAttemptTracker()
        
        # Записываем смешанные попытки
        tracker.record_login_attempt("test_user", "192.168.1.1", True)
        tracker.record_login_attempt("test_user", "192.168.1.1", False)
        tracker.record_login_attempt("test_user", "192.168.1.1", False)
        tracker.record_login_attempt("test_user", "192.168.1.1", True)
        tracker.record_login_attempt("test_user", "192.168.1.1", False)
        
        # Проверяем подсчет неуспешных попыток (должно быть 1, т.к. после успешного входа счетчик сбрасывается)
        failed_count = tracker.get_failed_attempts_count("test_user")
        assert failed_count == 1


@pytest.mark.asyncio
class TestPasswordSecurity:
    """Тесты безопасности паролей"""
    
    def test_password_hashing(self):
        """Тест хеширования паролей"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Проверяем что пароль хешируется
        assert hashed != password
        assert len(hashed) > 0
        
        # Проверяем что хеш содержит соль
        assert hashed.startswith("$2b$")
        
        # Проверяем что одинаковые пароли дают разные хеши
        hashed2 = get_password_hash(password)
        assert hashed != hashed2
    
    def test_password_verification(self):
        """Тест проверки паролей"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Правильный пароль
        assert verify_password(password, hashed) is True
        
        # Неправильный пароль
        assert verify_password("wrong_password", hashed) is False
        
        # Пустой пароль
        assert verify_password("", hashed) is False
    
    def test_password_strength_requirements(self):
        """Тест требований к сложности пароля"""
        # Слабые пароли
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "qwerty",
            "admin"
        ]
        
        # Сильные пароли
        strong_passwords = [
            "MyStrongPassword123!",
            "Complex@Pass1",
            "Secure#Password456",
            "Strong$Pass789"
        ]
        
        # Все пароли должны хешироваться (логика проверки сложности на уровне валидации)
        for password in weak_passwords + strong_passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed) is True


@pytest.mark.asyncio
class TestJWTSecurity:
    """Тесты безопасности JWT токенов"""
    
    def test_jwt_token_creation(self):
        """Тест создания JWT токенов"""
        data = {"sub": "test_user", "user_type": "employee"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Проверяем что токен содержит правильные данные
        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test_user"
        assert payload["user_type"] == "employee"
    
    def test_jwt_token_expiration(self):
        """Тест истечения JWT токенов"""
        data = {"sub": "test_user", "user_type": "employee"}
        
        # Создаем токен с коротким временем жизни
        token = create_access_token(data, expires_delta=timedelta(seconds=1))
        
        # Токен должен быть валиден сразу после создания
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
        
        # Ждем истечения токена
        time.sleep(2)
        
        # Токен должен быть невалиден
        payload = verify_token(token)
        assert payload is None
    
    def test_jwt_token_tampering(self):
        """Тест защиты от подделки JWT токенов"""
        data = {"sub": "test_user", "user_type": "employee"}
        token = create_access_token(data)
        
        # Пытаемся изменить токен
        tampered_token = token[:-5] + "xxxxx"
        
        # Поддельный токен должен быть отклонен
        payload = verify_token(tampered_token)
        assert payload is None
    
    def test_jwt_additional_claims(self):
        """Тест дополнительных claims в JWT"""
        data = {"sub": "test_user", "user_type": "employee"}
        token = create_access_token(data)
        
        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Проверяем наличие дополнительных claims
        assert "iat" in payload  # issued at
        assert "exp" in payload  # expires
        assert "jti" in payload  # JWT ID
        assert "iss" in payload  # issuer


@pytest.mark.asyncio
class TestXSSProtection:
    """Тесты защиты от XSS атак"""
    
    def test_sanitize_output_basic(self):
        """Тест базовой санитизации вывода"""
        # Опасный HTML
        dangerous_html = "<script>alert('XSS')</script>"
        safe_output = sanitize_output(dangerous_html)
        
        assert "&lt;script&gt;" in safe_output
        assert "&lt;/script&gt;" in safe_output
        assert "<script>" not in safe_output
    
    def test_sanitize_output_complex(self):
        """Тест сложной санитизации"""
        test_cases = [
            ("<img src=x onerror=alert('XSS')>", "&lt;img src=x onerror=alert('XSS')&gt;"),
            ("<div onclick='alert(1)'>Click</div>", "&lt;div onclick='alert(1)'&gt;Click&lt;/div&gt;"),
            ("javascript:alert('XSS')", "javascript:alert('XSS')"),  # Не HTML, но опасно
            ("<iframe src='javascript:alert(1)'></iframe>", "&lt;iframe src='javascript:alert(1)'&gt;&lt;/iframe&gt;")
        ]
        
        for dangerous, expected in test_cases:
            safe_output = sanitize_output(dangerous)
            assert "<" not in safe_output or "&lt;" in safe_output
            assert ">" not in safe_output or "&gt;" in safe_output
    
    def test_sanitize_output_safe_content(self):
        """Тест что безопасный контент не изменяется"""
        safe_content = "Обычный текст без HTML"
        sanitized = sanitize_output(safe_content)
        
        assert sanitized == safe_content
    
    def test_sanitize_output_data_structures(self):
        """Тест санитизации структур данных"""
        # Словарь с опасными данными
        dangerous_dict = {
            "name": "<script>alert('XSS')</script>",
            "description": "Нормальное описание",
            "html": "<div>Контент</div>"
        }
        
        safe_dict = sanitize_output(dangerous_dict)
        
        assert "&lt;script&gt;" in safe_dict["name"]
        assert safe_dict["description"] == "Нормальное описание"
        assert "&lt;div&gt;" in safe_dict["html"]
        
        # Список с опасными данными
        dangerous_list = [
            "<script>alert('XSS')</script>",
            "Безопасный текст",
            "<img src=x onerror=alert(1)>"
        ]
        
        safe_list = sanitize_output(dangerous_list)
        
        assert "&lt;script&gt;" in safe_list[0]
        assert safe_list[1] == "Безопасный текст"
        assert "&lt;img" in safe_list[2]


@pytest.mark.asyncio
class TestSecurityHeaders:
    """Тесты заголовков безопасности"""
    
    async def test_security_headers_middleware(self, client: TestClient):
        """Тест middleware заголовков безопасности"""
        response = client.get("/health")
        
        # Проверяем наличие заголовков безопасности
        headers = response.headers
        
        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers
        
        # Проверяем значения заголовков
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert "strict-origin-when-cross-origin" in headers["Referrer-Policy"]
    
    async def test_csp_header_content(self, client: TestClient):
        """Тест содержимого CSP заголовка"""
        response = client.get("/health")
        
        csp_header = response.headers.get("Content-Security-Policy")
        assert csp_header is not None
        
        # Проверяем основные директивы CSP
        assert "default-src 'self'" in csp_header
        assert "script-src 'self'" in csp_header
        assert "style-src 'self'" in csp_header
        assert "img-src 'self'" in csp_header
        assert "frame-ancestors 'none'" in csp_header
    
    async def test_server_header_removal(self, client: TestClient):
        """Тест удаления заголовка Server"""
        response = client.get("/health")
        
        # Заголовок Server должен быть удален или не содержать информацию о сервере
        server_header = response.headers.get("Server")
        if server_header:
            assert "uvicorn" not in server_header.lower()
            assert "fastapi" not in server_header.lower()


@pytest.mark.asyncio
class TestRateLimiting:
    """Тесты ограничения частоты запросов"""
    
    async def test_rate_limiting_normal_usage(self, client: TestClient):
        """Тест нормального использования без превышения лимитов"""
        # Делаем несколько запросов в пределах лимита
        for i in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            
            # Проверяем наличие заголовков rate limiting
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    async def test_rate_limiting_headers(self, client: TestClient):
        """Тест заголовков rate limiting"""
        response = client.get("/health")
        
        # Проверяем заголовки
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Проверяем значения
        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])
        
        assert limit > 0
        assert remaining <= limit
    
    async def test_rate_limiting_per_ip(self, client: TestClient):
        """Тест rate limiting по IP адресу"""
        # Делаем запросы с разными IP (через заголовки)
        response1 = client.get("/health", headers={"X-Forwarded-For": "192.168.1.1"})
        response2 = client.get("/health", headers={"X-Forwarded-For": "192.168.1.2"})
        
        # Оба запроса должны пройти успешно
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Лимиты должны быть независимыми
        remaining1 = int(response1.headers["X-RateLimit-Remaining"])
        remaining2 = int(response2.headers["X-RateLimit-Remaining"])
        
        # Для разных IP лимиты должны быть одинаковыми (если это первые запросы)
        assert remaining1 == remaining2


@pytest.mark.asyncio
class TestRequestSizeLimiting:
    """Тесты ограничения размера запросов"""
    
    async def test_normal_request_size(self, authenticated_client: TestClient):
        """Тест нормального размера запроса"""
        # Небольшой запрос должен проходить
        small_data = {"test": "data"}
        response = authenticated_client.post("/api/v1/requests/", json=small_data)
        
        # Может быть ошибка валидации, но не ошибка размера
        assert response.status_code != 413
    
    async def test_large_request_rejection(self, authenticated_client: TestClient):
        """Тест отклонения больших запросов"""
        # Создаем очень большой запрос (больше 10MB)
        large_data = {"large_field": "x" * (11 * 1024 * 1024)}  # 11MB
        
        response = authenticated_client.post("/api/v1/requests/", json=large_data)
        
        # Должна быть ошибка размера запроса
        assert response.status_code == 413


@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Тесты безопасности аутентификации"""
    
    async def test_authentication_with_valid_credentials(
        self, 
        client: TestClient, 
        test_employee: Employee
    ):
        """Тест аутентификации с валидными данными"""
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "test_password"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_authentication_with_invalid_credentials(
        self, 
        client: TestClient, 
        test_employee: Employee
    ):
        """Тест аутентификации с невалидными данными"""
        # Неверный пароль
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()
        
        # Несуществующий пользователь
        response = client.post("/api/v1/auth/login", json={
            "login": "nonexistent_user",
            "password": "any_password"
        })
        
        assert response.status_code == 401
    
    async def test_brute_force_protection(
        self, 
        client: TestClient, 
        test_employee: Employee
    ):
        """Тест защиты от брутфорса"""
        # Делаем много неуспешных попыток входа
        for i in range(6):
            response = client.post("/api/v1/auth/login", json={
                "login": test_employee.login,
                "password": "wrong_password"
            })
            
            if i < 5:
                assert response.status_code == 401
            else:
                # После 5 неуспешных попыток аккаунт должен быть заблокирован
                assert response.status_code == 423  # Locked
    
    async def test_session_management(
        self, 
        client: TestClient, 
        test_employee: Employee
    ):
        """Тест управления сессиями"""
        # Логинимся
        response = client.post("/api/v1/auth/login", json={
            "login": test_employee.login,
            "password": "test_password"
        })
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Используем токен для доступа к защищенному ресурсу
        protected_response = client.get("/api/v1/requests/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert protected_response.status_code == 200
        
        # Проверяем информацию о текущем пользователе
        me_response = client.get("/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["login"] == test_employee.login


@pytest.mark.asyncio
class TestFileSecurityValidation:
    """Тесты безопасности файлов"""
    
    async def test_file_type_validation(self, authenticated_client: TestClient, test_request):
        """Тест валидации типов файлов"""
        # Разрешенный тип файла
        allowed_file = b"fake image content"
        files = {"file": ("test.jpg", allowed_file, "image/jpeg")}
        
        response = authenticated_client.post(
            f"/api/v1/files/upload-expense-receipt/{test_request.id}",
            files=files
        )
        
        # Может быть ошибка валидации содержимого, но не типа
        assert response.status_code != 415  # Unsupported Media Type
    
    async def test_file_size_validation(self, authenticated_client: TestClient, test_request):
        """Тест валидации размера файлов"""
        # Большой файл
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("large.jpg", large_file, "image/jpeg")}
        
        response = authenticated_client.post(
            f"/api/v1/files/upload-expense-receipt/{test_request.id}",
            files=files
        )
        
        # Должна быть ошибка размера файла
        assert response.status_code == 413
    
    @patch('app.utils.file_security.validate_file_content')
    async def test_file_content_validation(
        self, 
        mock_validate,
        authenticated_client: TestClient, 
        test_request
    ):
        """Тест валидации содержимого файлов"""
        # Мокаем валидацию как неуспешную
        mock_validate.return_value = False
        
        malicious_file = b"malicious content"
        files = {"file": ("test.jpg", malicious_file, "image/jpeg")}
        
        response = authenticated_client.post(
            f"/api/v1/files/upload-expense-receipt/{test_request.id}",
            files=files
        )
        
        # Должна быть ошибка безопасности
        assert response.status_code == 400
        assert "безопасности" in response.json()["detail"]
    
    async def test_path_traversal_protection(self, authenticated_client: TestClient):
        """Тест защиты от path traversal атак"""
        # Попытка доступа к файлу вне разрешенной директории
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]
        
        for path in dangerous_paths:
            response = authenticated_client.get(f"/api/v1/secure-files/download/{path}")
            
            # Должна быть ошибка доступа
            assert response.status_code in [400, 403, 404] 