from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.auth import require_admin
from ..services.recording_service import recording_service
from ..core.models import Master, Employee, Administrator

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("/download")
async def manual_download_recordings(
    days_back: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Ручное скачивание записей звонков"""
    try:
        result = await recording_service.manual_download(days_back)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading recordings: {str(e)}"
        )


@router.get("/status")
async def get_recording_service_status(
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Получение статуса сервиса записей"""
    return {
        "is_running": recording_service.is_running,
        "task_active": recording_service.task is not None and not recording_service.task.done()
    }


@router.post("/start")
async def start_recording_service(
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Запуск сервиса записей"""
    try:
        recording_service.start()
        return {"message": "Recording service started", "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting recording service: {str(e)}"
        )


@router.post("/stop")
async def stop_recording_service(
    current_user: Master | Employee | Administrator = Depends(require_admin)
):
    """Остановка сервиса записей"""
    try:
        recording_service.stop()
        return {"message": "Recording service stopped", "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping recording service: {str(e)}"
        ) 