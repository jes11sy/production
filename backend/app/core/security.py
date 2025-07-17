"""
Модуль безопасности для защиты от различных атак
"""
import secrets
import hashlib
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Response, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from .config import settings
from .cache import cache_manager

logger = logging.getLogger(__name__)

# Хранилище для CSRF токенов (в продакшене лучше использовать Redis)
csrf_tokens: Dict[str, Dict[str, Any]] = {}

# Хранилище для попыток входа
login_attempts: Dict[str, Dict[str, Any]] = {}

class CSRFProtection:
    """Защита от CSRF атак"""
    
    @staticmethod
    def generate_csrf_token(session_id: str) -> str:
        """Генерация CSRF токена для сессии"""
        token = secrets.token_urlsafe(32)
        csrf_tokens[session_id] = {
            'token': token,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1)
        }
        return token
    
    @staticmethod
    def validate_csrf_token(session_id: str, token: str) -> bool:
        """Валидация CSRF токена"""
        if session_id not in csrf_tokens:
            return False
        
        stored_token = csrf_tokens[session_id]
        
        # Проверяем срок действия
        if datetime.utcnow() > stored_token['expires_at']:
            del csrf_tokens[session_id]
            return False
        
        # Проверяем токен
        if stored_token['token'] != token:
            return False
        
        return True
    
    @staticmethod
    def cleanup_expired_tokens():
        """Очистка просроченных токенов"""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, data in csrf_tokens.items()
            if current_time > data['expires_at']
        ]
        
        for session_id in expired_sessions:
            del csrf_tokens[session_id]

class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware для проверки CSRF токенов"""
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs", "/redoc", "/openapi.json", "/api/v1/auth/login",
            "/api/v1/health", "/api/v1/mango/webhook"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Пропускаем GET запросы и исключенные пути
        if request.method == "GET" or any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Получаем session_id из cookies
        session_id = request.cookies.get("session_id")
        if not session_id:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Missing session ID"}
            )
        
        # Получаем CSRF токен из заголовка
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Missing CSRF token"}
            )
        
        # Валидируем токен
        if not CSRFProtection.validate_csrf_token(session_id, csrf_token):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Invalid CSRF token"}
            )
        
        return await call_next(request)

class LoginAttemptTracker:
    """Отслеживание попыток входа"""
    
    @staticmethod
    def record_login_attempt(ip_address: str, username: str, success: bool, user_agent: Optional[str] = None):
        """Записать попытку входа"""
        attempt_key = f"{ip_address}:{username}"
        current_time = datetime.utcnow()
        
        if attempt_key not in login_attempts:
            login_attempts[attempt_key] = {
                'attempts': [],
                'locked_until': None,
                'total_attempts': 0
            }
        
        # Добавляем попытку
        login_attempts[attempt_key]['attempts'].append({
            'timestamp': current_time,
            'success': success,
            'user_agent': user_agent,
            'ip_address': ip_address
        })
        
        login_attempts[attempt_key]['total_attempts'] += 1
        
        # Логируем попытку
        log_data = {
            'ip_address': ip_address,
            'username': username,
            'success': success,
            'user_agent': user_agent,
            'timestamp': current_time.isoformat()
        }
        
        if success:
            logger.info(f"Successful login attempt", extra=log_data)
        else:
            logger.warning(f"Failed login attempt", extra=log_data)
        
        # Очищаем старые попытки (старше 1 часа)
        one_hour_ago = current_time - timedelta(hours=1)
        login_attempts[attempt_key]['attempts'] = [
            attempt for attempt in login_attempts[attempt_key]['attempts']
            if attempt['timestamp'] > one_hour_ago
        ]
        
        # Проверяем необходимость блокировки
        if not success:
            LoginAttemptTracker._check_and_apply_lockout(attempt_key, current_time)
    
    @staticmethod
    def _check_and_apply_lockout(attempt_key: str, current_time: datetime):
        """Проверить и применить блокировку аккаунта"""
        attempts_data = login_attempts[attempt_key]
        
        # Считаем неудачные попытки за последний час
        failed_attempts = [
            attempt for attempt in attempts_data['attempts']
            if not attempt['success'] and 
            attempt['timestamp'] > current_time - timedelta(hours=1)
        ]
        
        # Блокируем на 30 минут после 5 неудачных попыток
        if len(failed_attempts) >= settings.LOGIN_ATTEMPTS_PER_HOUR:
            attempts_data['locked_until'] = current_time + timedelta(minutes=30)
            logger.warning(f"Account locked due to too many failed attempts: {attempt_key}")
    
    @staticmethod
    def is_account_locked(ip_address: str, username: str) -> bool:
        """Проверить, заблокирован ли аккаунт"""
        attempt_key = f"{ip_address}:{username}"
        
        if attempt_key not in login_attempts:
            return False
        
        locked_until = login_attempts[attempt_key].get('locked_until')
        if not locked_until:
            return False
        
        # Проверяем, не истек ли срок блокировки
        if datetime.utcnow() > locked_until:
            login_attempts[attempt_key]['locked_until'] = None
            return False
        
        return True
    
    @staticmethod
    def get_lockout_time_remaining(ip_address: str, username: str) -> Optional[int]:
        """Получить оставшееся время блокировки в секундах"""
        attempt_key = f"{ip_address}:{username}"
        
        if attempt_key not in login_attempts:
            return None
        
        locked_until = login_attempts[attempt_key].get('locked_until')
        if not locked_until:
            return None
        
        remaining = (locked_until - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления заголовков безопасности"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Добавляем заголовки безопасности
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Удаляем информацию о сервере
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения размера запросов"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB по умолчанию
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        # Проверяем размер тела запроса
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request too large"}
            )
        
        return await call_next(request)

def get_client_ip(request: Request) -> str:
    """Получить IP адрес клиента с учетом прокси"""
    # Проверяем заголовки прокси
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback на стандартный IP
    return request.client.host if request.client else "unknown"

def sanitize_output(data: Any) -> Any:
    """Санитизация выходных данных для защиты от XSS"""
    if isinstance(data, str):
        # Экранируем HTML символы
        return (data.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))
    elif isinstance(data, dict):
        return {key: sanitize_output(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    else:
        return data

async def cleanup_security_data():
    """Периодическая очистка данных безопасности"""
    CSRFProtection.cleanup_expired_tokens()
    
    # Очищаем старые попытки входа
    current_time = datetime.utcnow()
    expired_attempts = []
    
    for attempt_key, data in login_attempts.items():
        # Удаляем записи старше 24 часов
        if data['attempts'] and all(
            attempt['timestamp'] < current_time - timedelta(hours=24)
            for attempt in data['attempts']
        ):
            expired_attempts.append(attempt_key)
    
    for attempt_key in expired_attempts:
        del login_attempts[attempt_key] 