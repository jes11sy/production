from fastapi import APIRouter
from .. import (
    auth, requests, transactions, users, files, file_access, 
    mango, recordings, health, database, metrics, security, monitoring
)

# Создаем роутер для версии v2
v2_router = APIRouter()

# Подключаем все существующие роутеры к v2
v2_router.include_router(auth.router, tags=["auth"])
v2_router.include_router(requests.router, tags=["requests"])
v2_router.include_router(transactions.router, tags=["transactions"])
v2_router.include_router(users.router, tags=["users"])
v2_router.include_router(files.router, prefix="/files", tags=["files"])
v2_router.include_router(file_access.router, prefix="/secure-files", tags=["secure-files"])
v2_router.include_router(mango.router, prefix="/mango", tags=["mango"])
v2_router.include_router(recordings.router, tags=["recordings"])
v2_router.include_router(health.router, tags=["health"])
v2_router.include_router(database.router, tags=["database"])
v2_router.include_router(metrics.router, tags=["metrics"])
v2_router.include_router(security.router, tags=["security"])
v2_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

@v2_router.get("/version")
async def get_version():
    """Получить информацию о версии API"""
    return {
        "version": "2.0.0",
        "status": "beta",
        "deprecated": False,
        "sunset_date": None,
        "features": [
            "Enhanced error handling",
            "Improved pagination",
            "Better validation",
            "Extended monitoring"
        ]
    }

@v2_router.get("/features")
async def get_features():
    """Получить список новых возможностей в v2"""
    return {
        "new_features": [
            {
                "name": "Enhanced Error Handling",
                "description": "Более детальная обработка ошибок с кодами и контекстом"
            },
            {
                "name": "Improved Pagination",
                "description": "Улучшенная пагинация с cursor-based navigation"
            },
            {
                "name": "Better Validation",
                "description": "Расширенная валидация входных данных"
            },
            {
                "name": "Extended Monitoring",
                "description": "Дополнительные метрики и мониторинг"
            }
        ],
        "breaking_changes": [
            {
                "endpoint": "/api/v2/requests",
                "change": "Изменен формат ответа для пагинации"
            }
        ]
    } 