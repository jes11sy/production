from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import re

class APIVersioning:
    """Система версионирования API"""
    
    SUPPORTED_VERSIONS = ["1.0", "2.0"]
    DEFAULT_VERSION = "1.0"
    
    @staticmethod
    def get_version_from_header(request: Request) -> str:
        """Получить версию API из заголовка"""
        version = request.headers.get("API-Version", APIVersioning.DEFAULT_VERSION)
        return version
    
    @staticmethod
    def get_version_from_path(path: str) -> Optional[str]:
        """Получить версию API из пути"""
        # Исправляем регулярное выражение для корректного извлечения версии
        match = re.match(r"^/api/v(\d+(?:\.\d+)?)", path)
        if match:
            version = match.group(1)
            # Преобразуем "1" в "1.0" для совместимости
            if version == "1":
                return "1.0"
            elif version == "2":
                return "2.0"
            return version
        return None
    
    @staticmethod
    def validate_version(version: str) -> bool:
        """Проверить поддерживается ли версия"""
        return version in APIVersioning.SUPPORTED_VERSIONS
    
    @staticmethod
    def get_deprecation_info(version: str) -> Optional[dict]:
        """Получить информацию о deprecation для версии"""
        deprecation_info = {
            "1.0": {
                "deprecated": False,
                "sunset_date": None,
                "migration_guide": None
            },
            "2.0": {
                "deprecated": False,
                "sunset_date": None,
                "migration_guide": None
            }
        }
        return deprecation_info.get(version)


async def version_middleware(request: Request, call_next):
    """Middleware для обработки версионирования API"""
    
    # Получаем версию из пути или заголовка
    path_version = APIVersioning.get_version_from_path(request.url.path)
    header_version = APIVersioning.get_version_from_header(request)
    
    # Приоритет: версия из пути > версия из заголовка > версия по умолчанию
    version = path_version or header_version or APIVersioning.DEFAULT_VERSION
    
    # Проверяем поддерживается ли версия
    if not APIVersioning.validate_version(version):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Unsupported API version",
                "version": version,
                "supported_versions": APIVersioning.SUPPORTED_VERSIONS
            }
        )
    
    # Добавляем информацию о версии в request
    request.state.api_version = version
    
    # Обрабатываем запрос
    response = await call_next(request)
    
    # Добавляем заголовки версионирования в ответ
    response.headers["API-Version"] = version
    
    # Добавляем информацию о deprecation если необходимо
    deprecation_info = APIVersioning.get_deprecation_info(version)
    if deprecation_info and deprecation_info.get("deprecated"):
        response.headers["Deprecation"] = "true"
        if deprecation_info.get("sunset_date"):
            response.headers["Sunset"] = deprecation_info["sunset_date"]
    
    return response


def get_current_version(request: Request) -> str:
    """Получить текущую версию API из request"""
    return getattr(request.state, "api_version", APIVersioning.DEFAULT_VERSION) 