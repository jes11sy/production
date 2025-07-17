#!/usr/bin/env python3
"""
Скрипт для запуска тестов с различными опциями
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from app.utils.subprocess_security import safe_subprocess_run, SubprocessSecurityError


def run_command(cmd, description=""):
    """Выполняет команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Команда: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = safe_subprocess_run(cmd, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка выполнения команды: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов для backend")
    parser.add_argument("--unit", action="store_true", help="Запустить только unit тесты")
    parser.add_argument("--integration", action="store_true", help="Запустить только integration тесты")
    parser.add_argument("--auth", action="store_true", help="Запустить только тесты аутентификации")
    parser.add_argument("--api", action="store_true", help="Запустить только тесты API")
    parser.add_argument("--models", action="store_true", help="Запустить только тесты моделей")
    parser.add_argument("--coverage", action="store_true", help="Запустить с покрытием кода")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    parser.add_argument("--parallel", "-p", action="store_true", help="Параллельный запуск тестов")
    parser.add_argument("--file", "-f", help="Запустить конкретный файл тестов")
    parser.add_argument("--install-deps", action="store_true", help="Установить зависимости перед запуском")
    
    args = parser.parse_args()
    
    # Переходим в директорию backend
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Устанавливаем зависимости если нужно
    if args.install_deps:
        print("📦 Установка зависимостей...")
        if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          "Установка зависимостей"):
            return 1
    
    # Базовая команда pytest
    cmd = [sys.executable, "-m", "pytest"]
    
    # Добавляем опции в зависимости от аргументов
    if args.coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--cov-fail-under=70"
        ])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])  # Требует pytest-xdist
    
    # Фильтры по типам тестов
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.auth:
        cmd.extend(["-m", "auth"])
    elif args.api:
        cmd.extend(["-m", "api"])
    elif args.models:
        cmd.extend(["-m", "models"])
    
    # Конкретный файл
    if args.file:
        cmd.append(f"tests/{args.file}")
    
    # Запускаем тесты
    success = run_command(cmd, "Запуск тестов")
    
    if success:
        print("\n✅ Все тесты прошли успешно!")
        
        # Показываем отчет о покрытии если был запрошен
        if args.coverage and os.path.exists("htmlcov/index.html"):
            print(f"\n📊 Отчет о покрытии кода: {os.path.abspath('htmlcov/index.html')}")
        
        return 0
    else:
        print("\n❌ Некоторые тесты не прошли!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 