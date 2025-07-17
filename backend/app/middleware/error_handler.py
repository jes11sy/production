"""
Улучшенный middleware для обработки ошибок
"""

import logging
import uuid
from typing import Any, Dict, Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import traceback

from ..core.exceptions import (
    BaseAppException,
    ErrorContext,
    create_error_response,
    handle_database_error,
    handle_validation_error,
    ErrorCode,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitExceededError
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Улучшенный middleware для обработки ошибок"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Создаем контекст ошибки
        error_context = ErrorContext()
        error_context.request_id = str(uuid.uuid4())
        error_context.endpoint = request.url.path
        error_context.method = request.method
        error_context.ip_address = request.client.host if request.client else None
        error_context.user_agent = request.headers.get("user-agent")
        
        # Добавляем request_id в headers
        request.state.request_id = error_context.request_id
        
        try:
            response = await self.app(scope, receive, send)
        except Exception as exc:
            response = await self.handle_exception(exc, error_context)
            await response(scope, receive, send)
    
    async def handle_exception(self, exc: Exception, context: ErrorContext) -> JSONResponse:
        """Обработка исключений"""
        
        # Обработка кастомных исключений приложения
        if isinstance(exc, BaseAppException):
            return create_error_response(exc, context)
        
        # Обработка ошибок валидации FastAPI
        elif isinstance(exc, RequestValidationError):
            validation_error = ValidationError(
                message="Validation error",
                field=str(exc.errors()[0].get("loc", [])) if exc.errors() else None
            )
            return create_error_response(validation_error, context)
        
        # Обработка ошибок валидации Pydantic
        elif isinstance(exc, PydanticValidationError):
            validation_error = handle_validation_error(exc)
            return create_error_response(validation_error, context)
        
        # Обработка HTTP исключений
        elif isinstance(exc, (HTTPException, StarletteHTTPException)):
            if exc.status_code == 401:
                auth_error = AuthenticationError(exc.detail)
            elif exc.status_code == 403:
                auth_error = AuthorizationError(exc.detail)
            elif exc.status_code == 429:
                rate_limit_error = RateLimitExceededError(exc.detail)
                return create_error_response(rate_limit_error, context)
            else:
                # Создаем общую ошибку для других HTTP статусов
                app_error = BaseAppException(
                    message=exc.detail,
                    error_code=ErrorCode.INTERNAL_ERROR,
                    status_code=exc.status_code
                )
                return create_error_response(app_error, context)
            
            return create_error_response(auth_error, context)
        
        # Обработка ошибок базы данных
        elif isinstance(exc, SQLAlchemyError):
            db_error = handle_database_error(exc)
            return create_error_response(db_error, context)
        
        # Обработка всех остальных исключений
        else:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            
            internal_error = BaseAppException(
                message="Internal server error",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"exception_type": type(exc).__name__}
            )
            
            return create_error_response(internal_error, context)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Глобальный обработчик исключений для FastAPI"""
    
    # Создаем контекст ошибки
    error_context = ErrorContext()
    error_context.request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    error_context.endpoint = request.url.path
    error_context.method = request.method
    error_context.ip_address = request.client.host if request.client else None
    error_context.user_agent = request.headers.get("user-agent")
    
    # Получаем пользователя из токена если есть
    try:
        from ..core.auth import get_current_user_optional
        user = await get_current_user_optional(request)
        if user:
            error_context.user_id = str(user.id)
    except Exception:
        pass  # Игнорируем ошибки получения пользователя
    
    # Обрабатываем исключение
    middleware = ErrorHandlingMiddleware(None)
    return await middleware.handle_exception(exc, error_context)


def setup_error_handlers(app):
    """Настройка обработчиков ошибок для FastAPI приложения"""
    
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        return await global_exception_handler(request, exc)
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return await global_exception_handler(request, exc)
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return await global_exception_handler(request, exc)
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        return await global_exception_handler(request, exc)
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        return await global_exception_handler(request, exc)
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return await global_exception_handler(request, exc)


class RequestLoggingMiddleware:
    """Middleware для логирования запросов с улучшенной обработкой ошибок"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Логируем входящий запрос
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Обрабатываем запрос
        response = None
        try:
            response = await self.app(scope, receive, send)
        except Exception as exc:
            # Логируем ошибку
            logger.error(
                f"Request {request_id} failed: {exc}",
                extra={
                    "request_id": request_id,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                },
                exc_info=True
            )
            raise
        
        # Логируем успешный ответ
        if response:
            logger.info(
                f"Request {request_id} completed successfully",
                extra={"request_id": request_id}
            )
        
        return response 