"""
API для безопасного доступа к файлам с проверкой прав доступа
"""
import os
import mimetypes
from pathlib import Path
from typing import Union
from fastapi import APIRouter, HTTPException, Depends, status, Path as FastAPIPath, Request as FastAPIRequest
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.models import Master, Employee, Administrator, Request, Transaction, File
from ..core.config import settings
from ..core.security import get_client_ip
import logging
# from ..utils.file_security import validate_file_access  # Пока не используется

router = APIRouter(prefix="/secure-files", tags=["secure-files"])

# Базовая директория для медиа файлов
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MEDIA_DIR = os.path.join(BASE_DIR, "media")

async def check_file_access_permission(
    file_path: str,
    user: Union[Master, Employee, Administrator],
    db: AsyncSession
) -> bool:
    """
    Проверка прав доступа к файлу
    
    Args:
        file_path: Путь к файлу
        user: Текущий пользователь
        db: Сессия базы данных
        
    Returns:
        True если доступ разрешен
    """
    # Администраторы имеют доступ ко всем файлам
    if isinstance(user, Administrator):
        return True
    
    # Получаем информацию о файле из базы данных
    file_record = await db.execute(
        select(File).where(File.file_path == file_path)
    )
    file_obj = file_record.scalar_one_or_none()
    
    if not file_obj:
        # Если файл не найден в базе, проверяем по пути
        # Файлы заявок доступны всем авторизованным пользователям
        if "zayvka" in file_path:
            return True
        # Файлы транзакций доступны только мастерам и администраторам
        elif "gorod" in file_path and isinstance(user, Master):
            return True
        return False
    
    # Проверяем доступ к файлам заявок
    if file_obj.request_id is not None:
        request_record = await db.execute(
            select(Request).where(Request.id == file_obj.request_id)
        )
        request_obj = request_record.scalar_one_or_none()
        
        if not request_obj:
            return False
        
        # Мастера могут видеть только свои заявки
        if isinstance(user, Master):
            return bool(request_obj.master_id == user.id)
        
        # Сотрудники могут видеть все заявки
        return isinstance(user, Employee)
    
    # Проверяем доступ к файлам транзакций
    if file_obj.transaction_id is not None:
        transaction_record = await db.execute(
            select(Transaction).where(Transaction.id == file_obj.transaction_id)
        )
        transaction_obj = transaction_record.scalar_one_or_none()
        
        if not transaction_obj:
            return False
        
        # Мастера могут видеть только свои транзакции
        if isinstance(user, Master):
            return transaction_obj.master_id == user.id
        
        # Сотрудники могут видеть все транзакции
        return isinstance(user, Employee)
    
    return False

@router.get("/download/{file_path:path}")
async def download_file(
    request: FastAPIRequest,
    file_path: str = FastAPIPath(..., description="Path to the file to download"),
    db: AsyncSession = Depends(get_db),
    current_user: Union[Master, Employee, Administrator] = Depends(get_current_user)
):
    """
    Безопасная загрузка файла с проверкой прав доступа
    
    Args:
        file_path: Путь к файлу относительно media директории
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        FileResponse с файлом
        
    Raises:
        HTTPException: При отсутствии прав доступа или файла
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    
    try:
        # Проверяем права доступа
        has_access = await check_file_access_permission(file_path, current_user, db)
        if not has_access:
            # Логируем отказ в доступе
            logging.warning(f"File access denied: {file_path} for user {current_user.login} from {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для доступа к файлу"
            )
        
        # Формируем полный путь к файлу
        full_path = os.path.join(MEDIA_DIR, file_path)
        
        # Проверяем, что файл существует
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден"
            )
        
        # Проверяем, что путь не выходит за пределы media директории (защита от path traversal)
        full_path = os.path.abspath(full_path)
        media_dir = os.path.abspath(MEDIA_DIR)
        
        if not full_path.startswith(media_dir):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недопустимый путь к файлу"
            )
        
        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Получаем имя файла для заголовка
        filename = os.path.basename(full_path)
        
        # Возвращаем файл
        return FileResponse(
            path=full_path,
            media_type=mime_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )

@router.get("/view/{file_path:path}")
async def view_file(
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: Union[Master, Employee, Administrator] = Depends(get_current_user)
):
    """
    Безопасный просмотр файла в браузере с проверкой прав доступа
    
    Args:
        file_path: Путь к файлу относительно media директории
        db: Сессия базы данных
        current_user: Текущий пользователь
        
    Returns:
        FileResponse с файлом для просмотра
        
    Raises:
        HTTPException: При отсутствии прав доступа или файла
    """
    try:
        # Проверяем права доступа
        has_access = await check_file_access_permission(file_path, current_user, db)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра файла"
            )
        
        # Формируем полный путь к файлу
        full_path = os.path.join(MEDIA_DIR, file_path)
        
        # Проверяем, что файл существует
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Файл не найден"
            )
        
        # Проверяем, что путь не выходит за пределы media директории
        full_path = os.path.abspath(full_path)
        media_dir = os.path.abspath(MEDIA_DIR)
        
        if not full_path.startswith(media_dir):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недопустимый путь к файлу"
            )
        
        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Проверяем, что файл можно безопасно отображать в браузере
        safe_mime_types = {
            "image/jpeg", "image/png", "image/gif", "image/webp",
            "application/pdf", "text/plain", "audio/mpeg", "audio/wav"
        }
        
        if mime_type not in safe_mime_types:
            # Для небезопасных типов принудительно скачиваем
            filename = os.path.basename(full_path)
            return FileResponse(
                path=full_path,
                media_type=mime_type,
                filename=filename,
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Content-Type-Options": "nosniff"
                }
            )
        
        # Возвращаем файл для просмотра
        return FileResponse(
            path=full_path,
            media_type=mime_type,
            headers={
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "Content-Security-Policy": "default-src 'self'"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при просмотре файла: {str(e)}"
        ) 