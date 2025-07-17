import imaplib
import email
import email.header
import os
import re
import logging
import socket
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime

from ..core.config import settings


class RamblerEmailClient:
    """Клиент для работы с почтой Rambler для скачивания записей звонков"""
    
    def __init__(self):
        self.host = settings.RAMBLER_IMAP_HOST
        self.port = settings.RAMBLER_IMAP_PORT
        self.username = settings.RAMBLER_IMAP_USERNAME
        self.password = settings.RAMBLER_IMAP_PASSWORD
        self.use_ssl = settings.RAMBLER_IMAP_USE_SSL
        self.connection = None
        
    def connect(self) -> bool:
        """Подключение к IMAP серверу"""
        try:
            if not self.username or not self.password:
                logging.error("RAMBLER: Username or password not configured")
                return False
                
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
                
            self.connection.login(self.username, self.password)
            logging.info(f"RAMBLER: Connected to {self.host}")
            return True
            
        except Exception as e:
            logging.error(f"RAMBLER: Connection error: {e}")
            return False
    
    def disconnect(self):
        """Отключение от IMAP сервера"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                logging.info("RAMBLER: Disconnected")
            except (imaplib.IMAP4.error, socket.error) as e:
                logging.warning(f"Error during IMAP disconnect: {e}")
            self.connection = None
    
    def search_emails(self, days_back: int = 1) -> List[int]:
        """Поиск писем с записями звонков за последние дни"""
        try:
            if not self.connection:
                return []
                
            self.connection.select("INBOX")
            
            # Ищем письма за последние дни
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Поиск писем от Mango Office или с записями звонков
            search_criteria = [
                f'(SINCE "{since_date}")',
                '(FROM "mango")',
                '(SUBJECT "recording")',
                '(SUBJECT "запись")',
                '(SUBJECT "звонок")'
            ]
            
            message_ids = []
            for criteria in search_criteria:
                try:
                    status, messages = self.connection.search(None, criteria)
                    if status == 'OK' and messages and messages[0]:
                        ids = messages[0].split()
                        message_ids.extend([int(id) for id in ids])
                except (imaplib.IMAP4.error, ValueError) as e:
                    logging.warning(f"Error searching emails with criteria '{criteria}': {e}")
                    continue
            
            # Убираем дубликаты
            unique_ids = list(set(message_ids))
            logging.info(f"RAMBLER: Found {len(unique_ids)} emails")
            return unique_ids
            
        except Exception as e:
            logging.error(f"RAMBLER: Search error: {e}")
            return []
    
    def get_email_attachments(self, message_id: int) -> List[Tuple[str, bytes]]:
        """Получение вложений из письма"""
        try:
            if not self.connection:
                return []
                
            status, message_data = self.connection.fetch(str(message_id), '(RFC822)')
            if status != 'OK' or not message_data or len(message_data) == 0:
                return []
            
            raw_email = message_data[0][1] if message_data[0] and len(message_data[0]) > 1 else None
            if not raw_email or not isinstance(raw_email, bytes):
                return []
                
            email_message = email.message_from_bytes(raw_email)
            
            attachments = []
            
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        # Декодируем имя файла если нужно
                        decoded_header = email.header.decode_header(filename)[0][0]
                        if isinstance(decoded_header, bytes):
                            filename = decoded_header.decode('utf-8')
                        else:
                            filename = decoded_header
                        
                        # Проверяем, что это запись звонка по формату имени
                        if self.is_call_recording_filename(filename):
                            file_data = part.get_payload(decode=True)
                            if isinstance(file_data, bytes):
                                attachments.append((filename, file_data))
                                logging.info(f"RAMBLER: Found recording: {filename}")
            
            return attachments
            
        except Exception as e:
            logging.error(f"RAMBLER: Error getting attachments: {e}")
            return []
    
    def is_call_recording_filename(self, filename: str) -> bool:
        """Проверка, что файл - это запись звонка по формату имени"""
        # Формат: 2025.07.15__11-03-07__79173250913__79923298774
        pattern = r'^\d{4}\.\d{2}\.\d{2}__\d{2}-\d{2}-\d{2}__\d+__\d+.*'
        return bool(re.match(pattern, filename))
    
    def parse_recording_filename(self, filename: str) -> Optional[dict]:
        """Парсинг имени файла записи для извлечения данных"""
        try:
            # Удаляем расширение
            name_without_ext = os.path.splitext(filename)[0]
            
            # Разбиваем по двойному подчеркиванию
            parts = name_without_ext.split('__')
            
            if len(parts) >= 4:
                date_str = parts[0]  # 2025.07.15
                time_str = parts[1]  # 11-03-07
                from_number = parts[2]  # 79173250913
                to_number = parts[3]  # 79923298774
                
                # Преобразуем дату и время
                date_obj = datetime.strptime(date_str, '%Y.%m.%d')
                time_obj = datetime.strptime(time_str, '%H-%M-%S').time()
                call_datetime = datetime.combine(date_obj.date(), time_obj)
                
                return {
                    'call_datetime': call_datetime,
                    'from_number': from_number,
                    'to_number': to_number,
                    'filename': filename
                }
        except Exception as e:
            logging.error(f"RAMBLER: Error parsing filename {filename}: {e}")
        
        return None
    
    def download_recordings(self, days_back: int = 1) -> List[dict]:
        """Скачивание записей звонков"""
        downloaded_files = []
        
        try:
            if not self.connect():
                return downloaded_files
            
            # Создаем директорию для записей
            download_path = settings.RECORDINGS_DOWNLOAD_PATH
            os.makedirs(download_path, exist_ok=True)
            
            # Находим корень проекта для правильного вычисления относительного пути
            current = os.path.abspath(os.path.dirname(__file__))
            while not os.path.basename(current).lower() == "project" and current != os.path.dirname(current):
                current = os.path.dirname(current)
            project_root = current
            
            # Ищем письма
            message_ids = self.search_emails(days_back)
            
            for message_id in message_ids:
                attachments = self.get_email_attachments(message_id)
                
                for filename, file_data in attachments:
                    # Парсим имя файла
                    file_info = self.parse_recording_filename(filename)
                    if not file_info:
                        continue
                    
                    # Путь для сохранения
                    file_path = os.path.join(download_path, filename)
                    
                    # Проверяем, не существует ли файл уже
                    if os.path.exists(file_path):
                        logging.info(f"RAMBLER: File already exists: {filename}")
                        continue
                    
                    # Сохраняем файл
                    try:
                        with open(file_path, 'wb') as f:
                            f.write(file_data)
                        
                        # Добавляем информацию о скачанном файле
                        file_info['file_path'] = file_path
                        file_info['relative_path'] = os.path.relpath(file_path, project_root)
                        downloaded_files.append(file_info)
                        
                        logging.info(f"RAMBLER: Downloaded recording: {filename}")
                        
                    except Exception as e:
                        logging.error(f"RAMBLER: Error saving file {filename}: {e}")
            
            return downloaded_files
            
        except Exception as e:
            logging.error(f"RAMBLER: Error downloading recordings: {e}")
            return downloaded_files
        
        finally:
            self.disconnect()


# Глобальный экземпляр клиента
rambler_client = RamblerEmailClient() 