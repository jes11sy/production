"""
API endpoints для управления миграциями базы данных
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from ..core.auth import require_admin
from ..core.models import Administrator
from ..migrations import (
    check_migration_status,
    apply_pending_migrations,
    create_new_migration,
    validate_schema,
    initialize_migration_system,
    migration_manager
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migrations", tags=["migrations"])


@router.get("/status")
async def get_migration_status(
    current_user: Administrator = Depends(require_admin)
):
    """Получение статуса миграций"""
    try:
        status = await check_migration_status()
        return {
            "status": "success",
            "data": status,
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get migration status: {str(e)}"
        )


@router.post("/apply")
async def apply_migrations(
    current_user: Administrator = Depends(require_admin)
):
    """Применение неприменённых миграций"""
    try:
        result = await apply_pending_migrations()
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result,
                "timestamp": "2025-01-15T15:00:00Z"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply migrations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply migrations: {str(e)}"
        )


@router.post("/create")
async def create_migration(
    message: str = Query(..., description="Описание миграции"),
    autogenerate: bool = Query(True, description="Автоматическое создание миграции"),
    current_user: Administrator = Depends(require_admin)
):
    """Создание новой миграции"""
    try:
        result = await create_new_migration(message, autogenerate)
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result,
                "timestamp": "2025-01-15T15:00:00Z"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create migration: {str(e)}"
        )


@router.get("/validate")
async def validate_database_schema(
    current_user: Administrator = Depends(require_admin)
):
    """Валидация схемы базы данных"""
    try:
        validation_result = await validate_schema()
        return {
            "status": "success",
            "data": validation_result,
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to validate schema: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate schema: {str(e)}"
        )


@router.post("/initialize")
async def initialize_migrations(
    current_user: Administrator = Depends(require_admin)
):
    """Инициализация системы миграций"""
    try:
        result = await initialize_migration_system()
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "data": result,
                "timestamp": "2025-01-15T15:00:00Z"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize migrations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize migrations: {str(e)}"
        )


@router.get("/history")
async def get_migration_history(
    limit: int = Query(10, ge=1, le=100, description="Количество миграций"),
    current_user: Administrator = Depends(require_admin)
):
    """Получение истории миграций"""
    try:
        history = migration_manager.get_migration_history()
        
        # Ограничиваем количество записей
        limited_history = history[:limit]
        
        return {
            "status": "success",
            "data": {
                "history": limited_history,
                "total_count": len(history),
                "showing_count": len(limited_history)
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get migration history: {str(e)}"
        )


@router.post("/rollback")
async def rollback_migration(
    revision: str = Query(..., description="Ревизия для отката"),
    current_user: Administrator = Depends(require_admin)
):
    """Откат миграции"""
    try:
        # Создаем резервную копию перед откатом
        backup_file = migration_manager.backup_database()
        
        # Выполняем откат
        result = migration_manager.rollback_migration(revision)
        
        return {
            "status": "success",
            "message": f"Миграция откачена до ревизии: {revision}",
            "data": {
                "rollback_output": result,
                "backup_file": backup_file,
                "target_revision": revision
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Failed to rollback migration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rollback migration: {str(e)}"
        )


@router.get("/pending")
async def get_pending_migrations(
    current_user: Administrator = Depends(require_admin)
):
    """Получение списка неприменённых миграций"""
    try:
        pending = migration_manager.get_pending_migrations()
        
        return {
            "status": "success",
            "data": {
                "pending_migrations": pending,
                "count": len(pending),
                "has_pending": len(pending) > 0
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get pending migrations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pending migrations: {str(e)}"
        )


@router.get("/current")
async def get_current_revision(
    current_user: Administrator = Depends(require_admin)
):
    """Получение текущей ревизии базы данных"""
    try:
        current = migration_manager.get_current_revision()
        head = migration_manager.get_head_revision()
        
        return {
            "status": "success",
            "data": {
                "current_revision": current,
                "head_revision": head,
                "is_up_to_date": current == head
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to get current revision: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current revision: {str(e)}"
        )


@router.post("/backup")
async def create_database_backup(
    current_user: Administrator = Depends(require_admin)
):
    """Создание резервной копии базы данных"""
    try:
        backup_file = migration_manager.backup_database()
        
        return {
            "status": "success",
            "message": "Резервная копия успешно создана",
            "data": {
                "backup_file": backup_file,
                "created_at": "2025-01-15T15:00:00Z"
            },
            "timestamp": "2025-01-15T15:00:00Z"
        }
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup: {str(e)}"
        ) 