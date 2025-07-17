"""
Улучшенная система обработки ошибок
Содержит кастомные исключения и детальную обработку ошибок
"""

from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from enum import Enum
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Коды ошибок для стандартизации"""
    
    # Аутентификация и авторизация
    AUTHENTICATION_FAILED = "AUTH_001"
    AUTHORIZATION_FAILED = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    TOKEN_INVALID = "AUTH_004"
    
    # Валидация данных
    VALIDATION_ERROR = "VAL_001"
    MISSING_REQUIRED_FIELD = "VAL_002"
    INVALID_FORMAT = "VAL_003"
    INVALID_VALUE = "VAL_004"
    
    # База данных
    DATABASE_ERROR = "DB_001"
    RECORD_NOT_FOUND = "DB_002"
    DUPLICATE_RECORD = "DB_003"
    FOREIGN_KEY_CONSTRAINT = "DB_004"
    DATABASE_CONNECTION_ERROR = "DB_005"
    
    # Бизнес-логика
    BUSINESS_RULE_VIOLATION = "BIZ_001"
    INSUFFICIENT_PERMISSIONS = "BIZ_002"
    OPERATION_NOT_ALLOWED = "BIZ_003"
    RESOURCE_CONFLICT = "BIZ_004"
    
    # Файловая система
    FILE_NOT_FOUND = "FILE_001"
    FILE_TOO_LARGE = "FILE_002"
    INVALID_FILE_TYPE = "FILE_003"
    FILE_UPLOAD_ERROR = "FILE_004"
    
    # Внешние сервисы
    EXTERNAL_SERVICE_ERROR = "EXT_001"
    EXTERNAL_SERVICE_TIMEOUT = "EXT_002"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXT_003"
    
    # Система
    INTERNAL_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    RATE_LIMIT_EXCEEDED = "SYS_003"
    MAINTENANCE_MODE = "SYS_004"


class BaseAppException(Exception):
    """Базовое исключение для приложения"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование исключения в словарь для JSON ответа"""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        }


class AuthenticationError(BaseAppException):
    """Ошибка аутентификации"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(BaseAppException):
    """Ошибка авторизации"""
    
    def __init__(self, message: str = "Authorization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHORIZATION_FAILED,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ValidationError(BaseAppException):
    """Ошибка валидации данных"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DatabaseError(BaseAppException):
    """Ошибка базы данных"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class RecordNotFoundError(BaseAppException):
    """Запись не найдена"""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found",
            error_code=ErrorCode.RECORD_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": str(identifier)}
        )


class DuplicateRecordError(BaseAppException):
    """Дублирование записи"""
    
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"Duplicate {resource}: {field} already exists",
            error_code=ErrorCode.DUPLICATE_RECORD,
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": str(value)}
        )


class BusinessRuleViolationError(BaseAppException):
    """Нарушение бизнес-правил"""
    
    def __init__(self, message: str, rule: str, details: Optional[Dict[str, Any]] = None):
        rule_details = {"rule": rule}
        if details:
            rule_details.update(details)
        
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=rule_details
        )


class FileError(BaseAppException):
    """Ошибка работы с файлами"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.FILE_NOT_FOUND, filename: Optional[str] = None):
        details = {}
        if filename:
            details["filename"] = filename
        
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ExternalServiceError(BaseAppException):
    """Ошибка внешнего сервиса"""
    
    def __init__(self, message: str, service: str, error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class RateLimitExceededError(BaseAppException):
    """Превышен лимит запросов"""
    
    def __init__(self, message: str = "Rate limit exceeded", limit: Optional[int] = None, window: Optional[str] = None):
        details = {}
        if limit:
            details["limit"] = limit
        if window:
            details["window"] = window
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ErrorContext:
    """Контекст ошибки для сбора дополнительной информации"""
    
    def __init__(self):
        self.request_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.endpoint: Optional[str] = None
        self.method: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.user_agent: Optional[str] = None
        self.additional_data: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "additional_data": self.additional_data
        }


def log_error(exception: BaseAppException, context: Optional[ErrorContext] = None):
    """Логирование ошибки с контекстом"""
    
    error_data = {
        "error_code": exception.error_code.value,
        "message": exception.message,
        "details": exception.details,
        "timestamp": exception.timestamp.isoformat(),
        "traceback": traceback.format_exc()
    }
    
    if context:
        error_data["context"] = context.to_dict()
    
    logger.error(f"Application error: {exception.error_code.value}", extra=error_data)


def create_error_response(exception: BaseAppException, context: Optional[ErrorContext] = None) -> JSONResponse:
    """Создание JSON ответа с ошибкой"""
    
    # Логируем ошибку
    log_error(exception, context)
    
    # Создаем ответ
    response_data = exception.to_dict()
    
    # Добавляем контекст в debug режиме
    if context and logger.isEnabledFor(logging.DEBUG):
        response_data["error"]["context"] = context.to_dict()
    
    return JSONResponse(
        status_code=exception.status_code,
        content=response_data
    )


def handle_database_error(error: Exception) -> BaseAppException:
    """Обработка ошибок базы данных"""
    
    error_str = str(error).lower()
    
    # Определяем тип ошибки по сообщению
    if "unique constraint" in error_str or "duplicate" in error_str:
        return DuplicateRecordError("Record", "field", "value")
    elif "foreign key constraint" in error_str:
        return DatabaseError("Foreign key constraint violation", ErrorCode.FOREIGN_KEY_CONSTRAINT)
    elif "not found" in error_str:
        return RecordNotFoundError("Record", "unknown")
    elif "connection" in error_str:
        return DatabaseError("Database connection error", ErrorCode.DATABASE_CONNECTION_ERROR)
    else:
        return DatabaseError(f"Database error: {str(error)}")


def handle_validation_error(error: Exception, field: Optional[str] = None) -> ValidationError:
    """Обработка ошибок валидации"""
    
    return ValidationError(
        message=str(error),
        field=field
    ) 


class BaseApplicationError(BaseAppException):
    """Совместимый базовый класс для обработки ошибок (legacy alias)"""
    pass 


def handle_database_exception(error: Exception, context: str = "") -> BaseAppException:
    """Обработка ошибок базы данных (обратная совместимость)"""
    return handle_database_error(error) 