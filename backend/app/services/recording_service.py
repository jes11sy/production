import asyncio
import logging
from datetime import datetime
from typing import List

from .email_client import rambler_client
from ..core.database import get_db
from ..core.crud import link_recording_to_request
from ..core.config import settings


class RecordingService:
    """Сервис для автоматического скачивания записей звонков"""
    
    def __init__(self):
        self.is_running = False
        self.task = None
        
    async def download_and_link_recordings(self) -> int:
        """Скачивание записей и связывание с заявками"""
        linked_count = 0
        
        try:
            # Скачиваем записи за последний день
            recordings = rambler_client.download_recordings(days_back=1)
            
            if not recordings:
                logging.info("RECORDING SERVICE: No new recordings found")
                return 0
            
            # Связываем записи с заявками
            async for db in get_db():
                try:
                    for recording_info in recordings:
                        request = await link_recording_to_request(db, recording_info)
                        if request:
                            linked_count += 1
                            logging.info(f"RECORDING SERVICE: Linked {recording_info['filename']} to request {request.id}")
                        else:
                            logging.warning(f"RECORDING SERVICE: Could not link {recording_info['filename']}")
                    
                    break  # Выходим из цикла после обработки
                    
                except Exception as e:
                    logging.error(f"RECORDING SERVICE: Database error: {e}")
                    
        except Exception as e:
            logging.error(f"RECORDING SERVICE: Error downloading recordings: {e}")
        
        return linked_count
    
    async def run_periodic_check(self):
        """Периодическая проверка новых записей"""
        while self.is_running:
            try:
                logging.info("RECORDING SERVICE: Starting periodic check")
                linked_count = await self.download_and_link_recordings()
                logging.info(f"RECORDING SERVICE: Linked {linked_count} recordings")
                
                # Ждем интервал между проверками
                await asyncio.sleep(settings.RECORDINGS_CHECK_INTERVAL)
                
            except Exception as e:
                logging.error(f"RECORDING SERVICE: Error in periodic check: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке
    
    def start(self):
        """Запуск сервиса"""
        if self.is_running:
            logging.warning("RECORDING SERVICE: Already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self.run_periodic_check())
        logging.info("RECORDING SERVICE: Started")
    
    def stop(self):
        """Остановка сервиса"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            self.task = None
        logging.info("RECORDING SERVICE: Stopped")
    
    async def manual_download(self, days_back: int = 1) -> dict:
        """Ручное скачивание записей"""
        try:
            start_time = datetime.now()
            linked_count = 0
            
            # Скачиваем записи
            recordings = rambler_client.download_recordings(days_back=days_back)
            
            if recordings:
                # Связываем с заявками
                async for db in get_db():
                    try:
                        for recording_info in recordings:
                            request = await link_recording_to_request(db, recording_info)
                            if request:
                                linked_count += 1
                        break
                    except Exception as e:
                        logging.error(f"RECORDING SERVICE: Manual download DB error: {e}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                'success': True,
                'downloaded_count': len(recordings),
                'linked_count': linked_count,
                'duration_seconds': duration,
                'recordings': recordings
            }
            
            logging.info(f"RECORDING SERVICE: Manual download completed - {len(recordings)} downloaded, {linked_count} linked")
            return result
            
        except Exception as e:
            logging.error(f"RECORDING SERVICE: Manual download error: {e}")
            return {
                'success': False,
                'error': str(e),
                'downloaded_count': 0,
                'linked_count': 0
            }


# Глобальный экземпляр сервиса
recording_service = RecordingService()


async def start_recording_service():
    """Запуск сервиса записей при старте приложения"""
    if settings.RAMBLER_IMAP_USERNAME and settings.RAMBLER_IMAP_PASSWORD:
        recording_service.start()
        logging.info("RECORDING SERVICE: Auto-started")
    else:
        logging.warning("RECORDING SERVICE: Not started - email credentials not configured")


async def stop_recording_service():
    """Остановка сервиса при завершении приложения"""
    recording_service.stop()
    logging.info("RECORDING SERVICE: Stopped on shutdown") 