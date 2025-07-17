"""
Конфигурация логирования для приложения с продвинутой ротацией
"""
import logging
import logging.config
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict
from .core.config import settings


class JSONFormatter(logging.Formatter):
    """Форматтер для JSON логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем дополнительные поля если они есть
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = getattr(record, 'user_id')
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = getattr(record, 'request_id')
        if hasattr(record, 'client_ip'):
            log_entry["client_ip"] = getattr(record, 'client_ip')
        if hasattr(record, 'method'):
            log_entry["method"] = getattr(record, 'method')
        if hasattr(record, 'url'):
            log_entry["url"] = getattr(record, 'url')
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = getattr(record, 'status_code')
        if hasattr(record, 'response_time'):
            log_entry["response_time"] = getattr(record, 'response_time')
        
        # Добавляем traceback для ошибок
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    """Настройка логирования с продвинутой ротацией"""
    
    # Определяем уровень логирования
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Проверяем, нужно ли логировать в файл
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    
    # Создаем директории для логов если их нет
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Конфигурация для разработки (читаемые логи)
    if settings.ENVIRONMENT == "development":
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "default",
                    "stream": sys.stdout,
                },
                **({"app_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "formatter": "detailed",
                    "filename": settings.LOG_FILE,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                }} if log_to_file else {}),
                **({"error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": logging.ERROR,
                    "formatter": "detailed",
                    "filename": settings.LOG_FILE.replace(".log", "_error.log"),
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 10,
                }} if log_to_file else {}),
                **({"security_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": logging.INFO,
                    "formatter": "detailed",
                    "filename": settings.LOG_FILE.replace(".log", "_security.log"),
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 10,
                }} if log_to_file else {}),
            },
            "loggers": {
                "": {  # root logger
                    "level": log_level,
                    "handlers": ["console"] + (["app_file"] if log_to_file else []),
                },
                "app.security": {
                    "level": logging.INFO,
                    "handlers": ["console"] + (["security_file"] if log_to_file else []),
                    "propagate": False,
                },
                "app.performance": {
                    "level": logging.INFO,
                    "handlers": ["console"] + (["app_file"] if log_to_file else []),
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": logging.INFO,
                    "handlers": ["console"] + (["app_file"] if log_to_file else []),
                    "propagate": False,
                },
                "uvicorn": {
                    "level": logging.INFO,
                    "handlers": ["console"] + (["app_file"] if log_to_file else []),
                    "propagate": False,
                },
            },
        }
    else:
        # Конфигурация для продакшена (JSON логи с продвинутой ротацией)
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JSONFormatter,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "json",
                    "stream": sys.stdout,
                },
                "app_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": log_level,
                    "formatter": "json",
                    "filename": settings.LOG_FILE,
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 30,  # Хранить 30 дней
                    "encoding": "utf-8",
                },
                "error_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": logging.ERROR,
                    "formatter": "json",
                    "filename": settings.LOG_FILE.replace(".log", "_error.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 90,  # Хранить 90 дней для ошибок
                    "encoding": "utf-8",
                },
                "security_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": logging.INFO,
                    "formatter": "json",
                    "filename": settings.LOG_FILE.replace(".log", "_security.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 365,  # Хранить 1 год для безопасности
                    "encoding": "utf-8",
                },
                "performance_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": logging.INFO,
                    "formatter": "json",
                    "filename": settings.LOG_FILE.replace(".log", "_performance.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 30,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "": {  # root logger
                    "level": log_level,
                    "handlers": ["console", "app_file"],
                },
                "app.security": {
                    "level": logging.INFO,
                    "handlers": ["console", "security_file"],
                    "propagate": False,
                },
                "app.performance": {
                    "level": logging.INFO,
                    "handlers": ["console", "performance_file"],
                    "propagate": False,
                },
                "app.request": {
                    "level": logging.INFO,
                    "handlers": ["console", "app_file"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": logging.WARNING,  # Меньше SQL логов в продакшене
                    "handlers": ["console", "app_file"],
                    "propagate": False,
                },
                "uvicorn": {
                    "level": logging.INFO,
                    "handlers": ["console", "app_file"],
                    "propagate": False,
                },
            },
        }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с дополнительными возможностями"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Адаптер для добавления контекстной информации в логи"""
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any] | None = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Добавляем extra информацию в каждый лог
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        if isinstance(self.extra, dict):
            kwargs['extra'].update(self.extra)
        return msg, kwargs


def get_request_logger(request_id: str | None = None, user_id: int | None = None, 
                      client_ip: str | None = None) -> LoggerAdapter:
    """Получить логгер с контекстом запроса"""
    logger = get_logger("app.request")
    extra: Dict[str, Any] = {}
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    if client_ip:
        extra["client_ip"] = client_ip
    
    return LoggerAdapter(logger, extra)


def log_performance(func_name: str, execution_time: float, 
                   additional_info: Dict[str, Any] | None = None) -> None:
    """Логирование производительности"""
    logger = get_logger("app.performance")
    extra: Dict[str, Any] = {
        "function": func_name,
        "execution_time": execution_time,
        "performance_log": True
    }
    if additional_info:
        extra.update(additional_info)
    
    logger.info(f"Performance: {func_name} executed in {execution_time:.3f}s", extra=extra) 