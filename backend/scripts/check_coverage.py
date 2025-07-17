#!/usr/bin/env python3
import subprocess
import sys
from app.utils.subprocess_security import safe_subprocess_run, SubprocessSecurityError

def run_coverage():
    """Запускает тесты с покрытием и выводит результат"""
    try:
        # Запуск тестов с покрытием
        result = safe_subprocess_run([
            sys.executable, "-m", "pytest", 
            "--cov=app", 
            "--cov-report=term-missing",
            "--tb=short",
            "-q"
        ], cwd=".", check=False)
        
        print("=== РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ ===")
        print(result.stdout)
        if result.stderr:
            print("ОШИБКИ:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Ошибка при запуске тестов: {e}")
        return False

if __name__ == "__main__":
    success = run_coverage()
    sys.exit(0 if success else 1) 