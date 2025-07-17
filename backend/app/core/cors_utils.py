"""
CORS utilities для динамического управления CORS headers
"""
from typing import Dict, List
from fastapi.responses import JSONResponse
from .config import Settings

def get_cors_headers(allowed_methods: str = "GET, POST, PUT, DELETE, OPTIONS", 
                    additional_headers: str = "Content-Type, Authorization") -> Dict[str, str]:
    """
    Получить CORS headers на основе текущих настроек
    
    Args:
        allowed_methods: Разрешенные HTTP методы
        additional_headers: Дополнительные разрешенные заголовки
    
    Returns:
        Словарь с CORS headers
    """
    settings = Settings()
    allowed_origins = settings.get_allowed_origins
    
    # Берем первый разрешенный origin для заголовка
    # В реальном production FastAPI middleware будет обрабатывать это корректно
    origin = allowed_origins[0] if allowed_origins else "*"
    
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": allowed_methods,
        "Access-Control-Allow-Headers": additional_headers,
        "Access-Control-Allow-Credentials": "true",
    }

def create_cors_response(content: dict = {}, 
                        status_code: int = 200,
                        allowed_methods: str = "GET, POST, PUT, DELETE, OPTIONS") -> JSONResponse:
    """
    Создать JSONResponse с корректными CORS headers
    
    Args:
        content: Содержимое ответа
        status_code: HTTP статус код
        allowed_methods: Разрешенные HTTP методы
    
    Returns:
        JSONResponse с CORS headers
    """
    if not content:
        content = {}
        
    headers = get_cors_headers(allowed_methods)
    
    return JSONResponse(
        content=content,
        status_code=status_code,
        headers=headers
    )

def get_allowed_origins() -> List[str]:
    """
    Получить список разрешенных origins
    
    Returns:
        Список разрешенных origins
    """
    settings = Settings()
    return settings.get_allowed_origins 