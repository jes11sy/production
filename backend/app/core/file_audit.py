"""
Модуль для аудита доступа к файлам
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, select
from sqlalchemy.sql import func

from .database import Base
from .models import Master, Employee, Administrator

logger = logging.getLogger(__name__)

class FileAccessAction(Enum):
    """Типы действий с файлами"""
    VIEW = "view"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    DELETE = "delete"
    ACCESS_DENIED = "access_denied"

class FileAccessResult(Enum):
    """Результаты доступа к файлам"""
    SUCCESS = "success"
    DENIED = "denied"
    ERROR = "error"
    NOT_FOUND = "not_found"

@dataclass
class FileAccessEvent:
    """Событие доступа к файлу"""
    user_id: int
    user_type: str
    user_login: str
    file_path: str
    action: FileAccessAction
    result: FileAccessResult
    ip_address: str
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    request_id: Optional[int] = None
    transaction_id: Optional[int] = None

class FileAccessLog(Base):
    """Модель для логирования доступа к файлам"""
    __tablename__ = "file_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_type = Column(String(50), nullable=False)
    user_login = Column(String(100), nullable=False, index=True)
    file_path = Column(String(500), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    result = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    error_message = Column(Text)
    file_size = Column(Integer)
    request_id = Column(Integer)
    transaction_id = Column(Integer)

class FileAuditLogger:
    """Логгер для аудита файлов"""
    
    @staticmethod
    async def log_file_access(
        db: AsyncSession,
        event: FileAccessEvent
    ):
        """Записать событие доступа к файлу"""
        try:
            # Создаем запись в базе данных
            log_entry = FileAccessLog(
                user_id=event.user_id,
                user_type=event.user_type,
                user_login=event.user_login,
                file_path=event.file_path,
                action=event.action.value,
                result=event.result.value,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                error_message=event.error_message,
                file_size=event.file_size,
                request_id=event.request_id,
                transaction_id=event.transaction_id
            )
            
            db.add(log_entry)
            await db.commit()
            
            # Логируем в файл
            log_data = {
                'user_id': event.user_id,
                'user_type': event.user_type,
                'user_login': event.user_login,
                'file_path': event.file_path,
                'action': event.action.value,
                'result': event.result.value,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'timestamp': event.timestamp.isoformat() if event.timestamp else datetime.utcnow().isoformat(),
                'error_message': event.error_message,
                'file_size': event.file_size,
                'request_id': event.request_id,
                'transaction_id': event.transaction_id
            }
            
            if event.result == FileAccessResult.SUCCESS:
                logger.info(f"File access successful", extra=log_data)
            elif event.result == FileAccessResult.DENIED:
                logger.warning(f"File access denied", extra=log_data)
            else:
                logger.error(f"File access error", extra=log_data)
                
        except Exception as e:
            logger.error(f"Failed to log file access: {e}")
    
    @staticmethod
    async def get_user_file_access_history(
        db: AsyncSession,
        user_id: int,
        limit: int = 100
    ) -> List[FileAccessLog]:
        """Получить историю доступа к файлам пользователя"""
        try:
            result = await db.execute(
                select(FileAccessLog)
                .where(FileAccessLog.user_id == user_id)
                .order_by(FileAccessLog.timestamp.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get user file access history: {e}")
            return []
    
    @staticmethod
    async def get_file_access_history(
        db: AsyncSession,
        file_path: str,
        limit: int = 100
    ) -> list:
        """Получить историю доступа к конкретному файлу"""
        try:
            result = await db.execute(
                select(FileAccessLog)
                .where(FileAccessLog.file_path == file_path)
                .order_by(FileAccessLog.timestamp.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get file access history: {e}")
            return []
    
    @staticmethod
    async def get_suspicious_activity(
        db: AsyncSession,
        limit: int = 100
    ) -> list:
        """Получить подозрительную активность"""
        try:
            result = await db.execute(
                select(FileAccessLog)
                .where(FileAccessLog.result == FileAccessResult.DENIED.value)
                .order_by(FileAccessLog.timestamp.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get suspicious activity: {e}")
            return []
    
    @staticmethod
    async def get_access_statistics(
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """Получить статистику доступа к файлам"""
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Общее количество обращений
            total_result = await db.execute(
                select(func.count(FileAccessLog.id))
                .where(FileAccessLog.timestamp >= start_date)
            )
            total_accesses = total_result.scalar()
            
            # Успешные обращения
            success_result = await db.execute(
                select(func.count(FileAccessLog.id))
                .where(
                    FileAccessLog.timestamp >= start_date,
                    FileAccessLog.result == FileAccessResult.SUCCESS.value
                )
            )
            successful_accesses = success_result.scalar()
            
            # Заблокированные обращения
            denied_result = await db.execute(
                select(func.count(FileAccessLog.id))
                .where(
                    FileAccessLog.timestamp >= start_date,
                    FileAccessLog.result == FileAccessResult.DENIED.value
                )
            )
            denied_accesses = denied_result.scalar()
            
            # Топ пользователей
            top_users_result = await db.execute(
                select(
                    FileAccessLog.user_login,
                    func.count(FileAccessLog.id).label('access_count')
                )
                .where(FileAccessLog.timestamp >= start_date)
                .group_by(FileAccessLog.user_login)
                .order_by(func.count(FileAccessLog.id).desc())
                .limit(10)
            )
            top_users = [
                {'user_login': row[0], 'access_count': row[1]}
                for row in top_users_result.fetchall()
            ]
            
            # Топ файлов
            top_files_result = await db.execute(
                select(
                    FileAccessLog.file_path,
                    func.count(FileAccessLog.id).label('access_count')
                )
                .where(FileAccessLog.timestamp >= start_date)
                .group_by(FileAccessLog.file_path)
                .order_by(func.count(FileAccessLog.id).desc())
                .limit(10)
            )
            top_files = [
                {'file_path': row[0], 'access_count': row[1]}
                for row in top_files_result.fetchall()
            ]
            
            return {
                'total_accesses': total_accesses,
                'successful_accesses': successful_accesses,
                'denied_accesses': denied_accesses,
                'success_rate': (successful_accesses / total_accesses * 100) if total_accesses > 0 else 0,
                'top_users': top_users,
                'top_files': top_files,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get access statistics: {e}")
            return {}

def create_file_access_event(
    user: Union[Master, Employee, Administrator],
    file_path: str,
    action: FileAccessAction,
    result: FileAccessResult,
    ip_address: str,
    user_agent: Optional[str] = None,
    error_message: Optional[str] = None,
    file_size: Optional[int] = None,
    request_id: Optional[int] = None,
    transaction_id: Optional[int] = None
) -> FileAccessEvent:
    """Создать событие доступа к файлу"""
    
    # Определяем тип пользователя
    if isinstance(user, Master):
        user_type = "master"
    elif isinstance(user, Employee):
        user_type = "employee"
    elif isinstance(user, Administrator):
        user_type = "administrator"
    else:
        user_type = "unknown"
    
    return FileAccessEvent(
        user_id=user.id,
        user_type=user_type,
        user_login=user.login,
        file_path=file_path,
        action=action,
        result=result,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
        error_message=error_message,
        file_size=file_size,
        request_id=request_id,
        transaction_id=transaction_id
    ) 