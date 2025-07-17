"""
Утилиты для безопасной обработки файлов
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException
import logging
import io

from app.core.config import settings

# Импорты с обработкой ошибок
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)

# Опасные расширения файлов
DANGEROUS_EXTENSIONS = {
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr', 'vbs', 'js', 'jar', 'app',
    'deb', 'pkg', 'rpm', 'dmg', 'iso', 'msi', 'run', 'bin', 'sh', 'ps1',
    'php', 'py', 'rb', 'pl', 'asp', 'aspx', 'jsp', 'cgi', 'htaccess'
}

# MIME типы для изображений
IMAGE_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

# MIME типы для документов
DOCUMENT_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}

# MIME типы для аудио
AUDIO_MIME_TYPES = {
    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/ogg'
}

# Все разрешенные MIME типы
ALLOWED_MIME_TYPES = IMAGE_MIME_TYPES | DOCUMENT_MIME_TYPES | AUDIO_MIME_TYPES


class FileSecurityError(Exception):
    """Исключение для ошибок безопасности файлов"""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Очистка имени файла от опасных символов
    
    Args:
        filename: Исходное имя файла
        
    Returns:
        Очищенное имя файла
    """
    # Убираем путь, оставляем только имя файла
    filename = os.path.basename(filename)
    
    # Заменяем опасные символы
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Убираем множественные точки (защита от ../)
    while '..' in filename:
        filename = filename.replace('..', '.')
    
    # Убираем пробелы в начале и конце
    filename = filename.strip()
    
    # Если имя файла пустое или состоит только из точек
    if not filename or filename.replace('.', '') == '':
        filename = 'unnamed_file'
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Получение расширения файла
    
    Args:
        filename: Имя файла
        
    Returns:
        Расширение файла в нижнем регистре
    """
    return Path(filename).suffix.lower().lstrip('.')


def validate_file_extension(filename: str) -> bool:
    """
    Проверка расширения файла
    
    Args:
        filename: Имя файла
        
    Returns:
        True если расширение разрешено
        
    Raises:
        FileSecurityError: Если расширение не разрешено
    """
    extension = get_file_extension(filename)
    
    # Проверяем на опасные расширения
    if extension in DANGEROUS_EXTENSIONS:
        raise FileSecurityError(f"Опасное расширение файла: {extension}")
    
    # Проверяем на разрешенные расширения
    allowed_extensions = settings.get_allowed_file_types
    if extension not in allowed_extensions:
        raise FileSecurityError(
            f"Расширение '{extension}' не разрешено. "
            f"Разрешенные расширения: {', '.join(allowed_extensions)}"
        )
    
    return True


def validate_file_size(file_size: int) -> bool:
    """
    Проверка размера файла
    
    Args:
        file_size: Размер файла в байтах
        
    Returns:
        True если размер допустим
        
    Raises:
        FileSecurityError: Если размер превышает лимит
    """
    if file_size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        current_size_mb = file_size / (1024 * 1024)
        raise FileSecurityError(
            f"Размер файла {current_size_mb:.2f}MB превышает лимит {max_size_mb:.2f}MB"
        )
    
    return True


def validate_mime_type(file_content: bytes, filename: str) -> str:
    """
    Проверка MIME типа файла по содержимому
    
    Args:
        file_content: Содержимое файла
        filename: Имя файла
        
    Returns:
        MIME тип файла
        
    Raises:
        FileSecurityError: Если MIME тип не разрешен
    """
    if not HAS_MAGIC:
        # Если magic не доступен, определяем тип по расширению
        extension = get_file_extension(filename)
        if extension in ['jpg', 'jpeg']:
            return 'image/jpeg'
        elif extension == 'png':
            return 'image/png'
        elif extension == 'gif':
            return 'image/gif'
        elif extension == 'pdf':
            return 'application/pdf'
        elif extension in ['doc', 'docx']:
            return 'application/msword'
        elif extension in ['mp3']:
            return 'audio/mpeg'
        elif extension in ['wav']:
            return 'audio/wav'
        else:
            return 'application/octet-stream'
    
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
    except Exception as e:
        logger.error(f"Ошибка определения MIME типа: {e}")
        raise FileSecurityError("Не удалось определить тип файла")
    
    # Проверяем разрешенные MIME типы
    if mime_type not in ALLOWED_MIME_TYPES:
        raise FileSecurityError(
            f"MIME тип '{mime_type}' не разрешен для файла '{filename}'"
        )
    
    return mime_type


def validate_image_file(file_content: bytes, filename: str) -> bool:
    """
    Дополнительная проверка для изображений
    
    Args:
        file_content: Содержимое файла
        filename: Имя файла
        
    Returns:
        True если изображение валидно
        
    Raises:
        FileSecurityError: Если изображение повреждено или подозрительно
    """
    try:
        # Проверяем, что файл действительно является изображением
        with Image.open(io.BytesIO(file_content)) as img:
            # Проверяем основные параметры
            if img.width <= 0 or img.height <= 0:
                raise FileSecurityError("Неверные размеры изображения")
            
            # Проверяем разумные лимиты размера
            if img.width > 10000 or img.height > 10000:
                raise FileSecurityError("Изображение слишком большое")
            
            # Проверяем формат
            if img.format.lower() not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                raise FileSecurityError(f"Неподдерживаемый формат изображения: {img.format}")
            
    except Exception as e:
        if isinstance(e, FileSecurityError):
            raise
        logger.error(f"Ошибка валидации изображения {filename}: {e}")
        raise FileSecurityError("Поврежденное или некорректное изображение")
    
    return True


def generate_safe_filename(original_filename: str) -> str:
    """
    Генерация безопасного имени файла
    
    Args:
        original_filename: Исходное имя файла
        
    Returns:
        Безопасное уникальное имя файла
    """
    # Очищаем исходное имя
    safe_name = sanitize_filename(original_filename)
    
    # Получаем расширение
    extension = get_file_extension(safe_name)
    
    # Генерируем уникальный идентификатор
    unique_id = str(uuid.uuid4())
    
    # Создаем безопасное имя файла
    if extension:
        return f"{unique_id}.{extension}"
    else:
        return unique_id


def get_file_hash(file_content: bytes) -> str:
    """
    Получение хеша файла для проверки дубликатов
    
    Args:
        file_content: Содержимое файла
        
    Returns:
        SHA256 хеш файла
    """
    return hashlib.sha256(file_content).hexdigest()


def create_secure_upload_path(upload_dir: str, subfolder: str = "") -> Path:
    """
    Создание безопасного пути для загрузки файлов
    
    Args:
        upload_dir: Основная директория для загрузок
        subfolder: Подпапка (опционально)
        
    Returns:
        Безопасный путь для загрузки
    """
    # Создаем базовый путь
    base_path = Path(upload_dir).resolve()
    
    if subfolder:
        # Очищаем подпапку от опасных символов
        safe_subfolder = sanitize_filename(subfolder)
        full_path = base_path / safe_subfolder
    else:
        full_path = base_path
    
    # Создаем директорию если не существует
    full_path.mkdir(parents=True, exist_ok=True)
    
    return full_path


async def validate_and_save_file(
    file: UploadFile,
    upload_dir: str,
    subfolder: str = "",
    user_id: Optional[int] = None
) -> Tuple[str, str, str]:
    """
    Полная валидация и сохранение файла
    
    Args:
        file: Загружаемый файл
        upload_dir: Директория для загрузки
        subfolder: Подпапка
        user_id: ID пользователя (для проверки лимитов)
        
    Returns:
        Кортеж (путь к файлу, оригинальное имя, хеш файла)
        
    Raises:
        FileSecurityError: При ошибках валидации
        HTTPException: При критических ошибках
    """
    try:
        # Проверяем, что имя файла не пустое
        if not file.filename:
            raise FileSecurityError("Имя файла не может быть пустым")
        
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Проверяем размер файла
        validate_file_size(len(file_content))
        
        # Проверяем расширение файла
        validate_file_extension(file.filename)
        
        # Проверяем MIME тип
        mime_type = validate_mime_type(file_content, file.filename)
        
        # Дополнительная проверка для изображений
        if mime_type in IMAGE_MIME_TYPES:
            validate_image_file(file_content, file.filename)
        
        # Генерируем безопасное имя файла
        safe_filename = generate_safe_filename(file.filename)
        
        # Создаем безопасный путь
        upload_path = create_secure_upload_path(upload_dir, subfolder)
        file_path = upload_path / safe_filename
        
        # Сохраняем файл
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Получаем хеш файла
        file_hash = get_file_hash(file_content)
        
        logger.info(f"Файл успешно сохранен: {file_path}")
        
        return str(file_path), file.filename, file_hash
        
    except FileSecurityError:
        raise
    except Exception as e:
        logger.error(f"Ошибка сохранения файла {file.filename or 'unknown'}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения файла")


def delete_file_safely(file_path: str) -> bool:
    """
    Безопасное удаление файла
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если файл успешно удален
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            logger.info(f"Файл удален: {file_path}")
            return True
        else:
            logger.warning(f"Файл не найден: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Ошибка удаления файла {file_path}: {e}")
        return False 