"""
Middleware для обработки ошибок и других функций
"""
import logging
import time
import traceback
import hashlib
import json
from typing import Callable, List, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.exc import SQLAlchemyError
from .core.config import settings
from .core.cache import cache_manager
from .core.exceptions import (
    BaseApplicationError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    handle_database_exception,
    ErrorCode
)
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware для централизованной обработки ошибок с улучшенным error handling"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except BaseApplicationError as e:
            # Обработка наших структурированных исключений
            logger.error(f"Application error: {e.to_dict()}")
            
            status_code = self._get_status_code_for_error(e.error_code)
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": e.error_code.value,
                    "message": e.message,
                    "details": e.details if settings.ENVIRONMENT == "development" else {},
                    "context": e.context if settings.ENVIRONMENT == "development" else {}
                }
            )
        except HTTPException as e:
            # Обработка FastAPI HTTPException
            logger.warning(f"HTTP exception: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "HTTP_ERROR",
                    "message": e.detail,
                    "details": {"status_code": e.status_code}
                }
            )
        except SQLAlchemyError as e:
            # Обработка ошибок SQLAlchemy
            db_error = handle_database_exception(e, "database_operation")
            logger.error(f"Database error: {db_error.to_dict()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "DATABASE_ERROR",
                    "message": "Database operation failed",
                    "details": db_error.details if settings.ENVIRONMENT == "development" else {}
                }
            )
        except ValueError as e:
            # Обработка ошибок валидации
            logger.warning(f"Validation error: {str(e)}")
            logger.warning(f"Request: {request.method} {request.url}")
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {"original_error": str(e)} if settings.ENVIRONMENT == "development" else {}
                }
            )
        except asyncio.TimeoutError as e:
            # Обработка таймаутов
            logger.error(f"Timeout error: {str(e)}")
            logger.error(f"Request: {request.method} {request.url}")
            
            return JSONResponse(
                status_code=504,
                content={
                    "error": "TIMEOUT_ERROR",
                    "message": "Request timeout",
                    "details": {"timeout_type": "request"} if settings.ENVIRONMENT == "development" else {}
                }
            )
        except Exception as e:
            # Обработка всех остальных исключений
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(f"Request: {request.method} {request.url}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    } if settings.ENVIRONMENT == "development" else {}
                }
            )
    
    def _get_status_code_for_error(self, error_code: ErrorCode) -> int:
        """Получение HTTP статус кода для типа ошибки"""
        status_mapping = {
            ErrorCode.VALIDATION_ERROR: 400,
            ErrorCode.INVALID_INPUT: 400,
            ErrorCode.REQUIRED_FIELD_MISSING: 400,
            ErrorCode.AUTHENTICATION_ERROR: 401,
            ErrorCode.TOKEN_EXPIRED: 401,
            ErrorCode.INVALID_TOKEN: 401,
            ErrorCode.AUTHORIZATION_ERROR: 403,
            ErrorCode.INSUFFICIENT_PERMISSIONS: 403,
            ErrorCode.ACCOUNT_LOCKED: 423,
            ErrorCode.RECORD_NOT_FOUND: 404,
            ErrorCode.DUPLICATE_RECORD: 409,
            ErrorCode.CONSTRAINT_VIOLATION: 409,
            ErrorCode.BUSINESS_LOGIC_ERROR: 422,
            ErrorCode.RESOURCE_UNAVAILABLE: 503,
            ErrorCode.FILE_NOT_FOUND: 404,
            ErrorCode.FILE_TOO_LARGE: 413,
            ErrorCode.INVALID_FILE_TYPE: 415,
            ErrorCode.EXTERNAL_SERVICE_ERROR: 502,
            ErrorCode.CACHE_ERROR: 503,
            ErrorCode.EMAIL_SERVICE_ERROR: 503,
            ErrorCode.NETWORK_ERROR: 502,
            ErrorCode.TIMEOUT_ERROR: 504,
            ErrorCode.CONNECTION_ERROR: 502,
            ErrorCode.DATABASE_ERROR: 500,
        }
        return status_mapping.get(error_code, 500)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Получаем IP адрес клиента
        client_ip = request.client.host if request.client else "unknown"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Логируем начало запроса
        logger.info(f"Request started: {request.method} {request.url} from {client_ip}")
        
        try:
            response = await call_next(request)
            
            # Вычисляем время выполнения
            duration = time.time() - start_time
            
            # Логируем завершение запроса
            logger.info(
                f"Request completed: {request.method} {request.url} "
                f"- Status: {response.status_code} "
                f"- Duration: {duration:.3f}s "
                f"- IP: {client_ip}"
            )
            
            return response
            
        except Exception as e:
            # Логируем ошибку
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url} "
                f"- Error: {str(e)} "
                f"- Duration: {duration:.3f}s "
                f"- IP: {client_ip}"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления заголовков безопасности"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения частоты запросов"""
    
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        current_time = time.time()
        
        async with self.lock:
            # Очищаем старые запросы
            window_start = current_time - self.window_seconds
            while self.requests[client_ip] and self.requests[client_ip][0] < window_start:
                self.requests[client_ip].popleft()
            
            # Проверяем лимит
            if len(self.requests[client_ip]) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "details": {
                            "max_requests": self.max_requests,
                            "window_seconds": self.window_seconds
                        }
                    }
                )
            
            # Добавляем текущий запрос
            self.requests[client_ip].append(current_time)
        
        return await call_next(request)


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware для кеширования GET запросов"""
    
    def __init__(self, app: ASGIApp, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Кешируем только GET запросы
        if request.method != "GET":
            return await call_next(request)
        
        # Создаем ключ кеша
        cache_key = f"http_cache:{request.url}"
        
        try:
            # Проверяем кеш
            cached_response = await cache_manager.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.url}")
                return JSONResponse(
                    status_code=cached_response["status_code"],
                    content=cached_response["content"],
                    headers=cached_response.get("headers", {})
                )
            
            # Выполняем запрос
            response = await call_next(request)
            
            # Кешируем только успешные ответы
            if response.status_code == 200:
                # Читаем тело ответа
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                try:
                    content = json.loads(body.decode())
                    cache_data = {
                        "status_code": response.status_code,
                        "content": content,
                        "headers": dict(response.headers)
                    }
                    await cache_manager.set(cache_key, cache_data, ttl=self.cache_ttl)
                    logger.debug(f"Cached response for {request.url}")
                    
                    # Возвращаем новый ответ с прочитанным телом
                    return JSONResponse(
                        status_code=response.status_code,
                        content=content,
                        headers=dict(response.headers)
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Не кешируем если не можем декодировать, возвращаем оригинальный ответ
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.headers.get("content-type", "application/octet-stream")
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Cache middleware error: {e}")
            # При ошибке кеша просто выполняем запрос
            return await call_next(request)