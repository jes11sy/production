"""
Утилиты для безопасного выполнения subprocess команд
"""
import subprocess
import shlex
import logging
from typing import List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Белый список разрешенных команд
ALLOWED_COMMANDS = {
    'python', 'python3', 'pip', 'alembic', 'pytest', 'coverage',
    'git', 'docker', 'docker-compose', 'npm', 'yarn'
}

# Опасные символы и паттерны
DANGEROUS_PATTERNS = [
    ';', '&&', '||', '|', '>', '<', '`', '$(',
    'rm -rf', 'del', 'format', 'shutdown', 'reboot',
    'curl', 'wget', 'nc', 'netcat', 'telnet'
]

class SubprocessSecurityError(Exception):
    """Исключение для ошибок безопасности subprocess"""
    pass

def validate_command(command: Union[str, List[str]]) -> List[str]:
    """
    Валидация команды перед выполнением
    
    Args:
        command: Команда в виде строки или списка
        
    Returns:
        Список валидированных аргументов команды
        
    Raises:
        SubprocessSecurityError: При обнаружении опасных паттернов
    """
    if isinstance(command, str):
        # Безопасное разделение строки на аргументы
        try:
            args = shlex.split(command)
        except ValueError as e:
            raise SubprocessSecurityError(f"Invalid command syntax: {e}")
    else:
        args = command
    
    if not args:
        raise SubprocessSecurityError("Empty command")
    
    # Проверяем основную команду
    main_command = Path(args[0]).name
    if main_command not in ALLOWED_COMMANDS:
        raise SubprocessSecurityError(f"Command '{main_command}' is not allowed")
    
    # Проверяем на опасные паттерны
    full_command = ' '.join(args)
    for pattern in DANGEROUS_PATTERNS:
        if pattern in full_command:
            raise SubprocessSecurityError(f"Dangerous pattern '{pattern}' detected in command")
    
    # Проверяем пути
    for arg in args:
        if arg.startswith('/') or arg.startswith('\\'):
            # Абсолютный путь - проверяем, что он безопасный
            path = Path(arg)
            try:
                path.resolve()
            except (OSError, ValueError):
                raise SubprocessSecurityError(f"Invalid path: {arg}")
        
        # Проверяем на попытки выхода за пределы директории
        if '..' in arg:
            raise SubprocessSecurityError(f"Path traversal attempt detected: {arg}")
    
    return args

def safe_subprocess_run(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    timeout: int = 300,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Безопасное выполнение subprocess команды
    
    Args:
        command: Команда для выполнения
        cwd: Рабочая директория
        timeout: Таймаут выполнения в секундах
        check: Проверять код возврата
        capture_output: Захватывать вывод
        text: Текстовый режим
        **kwargs: Дополнительные аргументы для subprocess.run
        
    Returns:
        Результат выполнения команды
        
    Raises:
        SubprocessSecurityError: При нарушении безопасности
        subprocess.CalledProcessError: При ошибке выполнения
        subprocess.TimeoutExpired: При превышении таймаута
    """
    # Валидируем команду
    validated_args = validate_command(command)
    
    # Валидируем рабочую директорию
    if cwd:
        cwd_path = Path(cwd).resolve()
        if not cwd_path.exists():
            raise SubprocessSecurityError(f"Working directory does not exist: {cwd}")
        if not cwd_path.is_dir():
            raise SubprocessSecurityError(f"Working directory is not a directory: {cwd}")
    
    # Логируем выполнение команды
    logger.info(f"Executing command: {' '.join(validated_args)}")
    if cwd:
        logger.info(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(
            validated_args,
            cwd=cwd,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=text,
            **kwargs
        )
        
        logger.info(f"Command completed successfully with return code: {result.returncode}")
        return result
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {e}")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}: {e}")
        if e.stderr:
            logger.error(f"Command stderr: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing command: {e}")
        raise SubprocessSecurityError(f"Unexpected error: {e}")

def safe_subprocess_check_output(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    timeout: int = 300,
    **kwargs
) -> str:
    """
    Безопасное выполнение команды с получением вывода
    
    Args:
        command: Команда для выполнения
        cwd: Рабочая директория
        timeout: Таймаут выполнения
        **kwargs: Дополнительные аргументы
        
    Returns:
        Вывод команды
    """
    result = safe_subprocess_run(
        command=command,
        cwd=cwd,
        timeout=timeout,
        check=True,
        capture_output=True,
        text=True,
        **kwargs
    )
    return result.stdout

def is_command_allowed(command: str) -> bool:
    """
    Проверка, разрешена ли команда
    
    Args:
        command: Имя команды
        
    Returns:
        True если команда разрешена
    """
    return Path(command).name in ALLOWED_COMMANDS 