from fastapi import APIRouter
from .. import (
    auth, requests, transactions, users, files, file_access, 
    mango, recordings, health, database, metrics, security, monitoring
)

# Создаем роутер для версии v1
v1_router = APIRouter()

# Подключаем все существующие роутеры к v1
v1_router.include_router(auth.router, tags=["auth"])
v1_router.include_router(requests.router, tags=["requests"])
v1_router.include_router(transactions.router, tags=["transactions"])
v1_router.include_router(users.router, tags=["users"])
v1_router.include_router(files.router, prefix="/files", tags=["files"])
v1_router.include_router(file_access.router, prefix="/secure-files", tags=["secure-files"])
v1_router.include_router(mango.router, prefix="/mango", tags=["mango"])
v1_router.include_router(recordings.router, tags=["recordings"])
v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(database.router, tags=["database"])
v1_router.include_router(metrics.router, tags=["metrics"])
v1_router.include_router(security.router, tags=["security"])
v1_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

@v1_router.get("/version")
async def get_version():
    """Получить информацию о версии API"""
    return {
        "version": "1.0.0",
        "status": "stable",
        "deprecated": False,
        "sunset_date": None
    } 